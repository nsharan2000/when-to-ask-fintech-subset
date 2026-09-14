"""GRPO + LoRA + vLLM-colocate training of Qwen3-4B-Instruct-2507 in the Critical API Understanding for AI Agents environment (TRL 1.13).
Usage:  python3 experiments/grpo/train_grpo.py --out experiments/grpo/run1 [--train data/train_v2.jsonl] [--max-steps 400] [--smoke]
Recipe: research-documents/training-methods.md §E. Reward = environment's programmatic get_reward (format+outcome+gate).
"""
import argparse, json, os, random, sys, time
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "environment"))
os.environ.setdefault("TRL_EXPERIMENTAL_SILENCE", "1")
os.environ.setdefault("TRITON_PTXAS_PATH", "/usr/local/cuda/bin/ptxas")
os.environ.setdefault("FLASHINFER_DISABLE_VERSION_CHECK", "1")   # cubin 0.6.4 vs flashinfer 0.6.18 in this image
os.environ.setdefault("VLLM_USE_FLASHINFER_SAMPLER", "0")        # top_p kernel signature mismatch on sm_121

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="Qwen/Qwen3-4B-Instruct-2507")
ap.add_argument("--train", default=os.path.join(REPO, "data", "train.jsonl"))
ap.add_argument("--out", required=True)
ap.add_argument("--max-steps", type=int, default=400)
ap.add_argument("--num-generations", type=int, default=8)
ap.add_argument("--batch", type=int, default=8, help="prompts per generation batch (× num_generations rollouts)")
ap.add_argument("--grad-accum", type=int, default=2)
ap.add_argument("--lr", type=float, default=1e-5)
ap.add_argument("--beta", type=float, default=0.02)
ap.add_argument("--lora-r", type=int, default=16)
ap.add_argument("--max-completion", type=int, default=640)
ap.add_argument("--vllm-mem", type=float, default=0.35)
ap.add_argument("--save-steps", type=int, default=25)
ap.add_argument("--smoke", action="store_true")
ap.add_argument("--resume", default=None)
ns = ap.parse_args()

import torch
from datasets import Dataset
from peft import LoraConfig
from trl import GRPOConfig, GRPOTrainer
from askbc.drivers.trl_env import ENV_FACTORIES, dataset_rows
from askbc.scenarios import load_jsonl

os.makedirs(ns.out, exist_ok=True)
os.environ["ASKBC_GRADE_LOG"] = os.path.join(ns.out, "episode_grades.jsonl")
rows = load_jsonl(ns.train)
random.Random(0).shuffle(rows)   # twins stay in the same file but are shuffled; every batch mixes should-ask / should-act
if ns.smoke:
    rows = rows[:16]; ns.max_steps = 2; ns.batch = 4; ns.num_generations = 4; ns.save_steps = 1
ds = Dataset.from_list(dataset_rows(rows))
print(f"train rows: {len(ds)}; domains: {sorted(set(ds['environment']))}", flush=True)

cfg = GRPOConfig(
    output_dir=ns.out, max_steps=ns.max_steps, logging_steps=1, save_steps=ns.save_steps, save_total_limit=20,
    per_device_train_batch_size=ns.batch, gradient_accumulation_steps=ns.grad_accum,
    generation_batch_size=ns.batch * ns.num_generations, num_generations=ns.num_generations,
    max_completion_length=ns.max_completion, max_tool_calling_iterations=10,
    learning_rate=ns.lr, lr_scheduler_type="constant_with_warmup", warmup_steps=10, weight_decay=0.0,
    beta=ns.beta, loss_type="dapo", scale_rewards="group", mask_truncated_completions=True,
    use_vllm=True, vllm_mode="colocate", vllm_gpu_memory_utilization=ns.vllm_mem, vllm_max_model_length=6144,
    vllm_enable_sleep_mode=False, temperature=1.0, top_p=1.0,
    bf16=True, gradient_checkpointing=True, report_to="none", log_completions=False,
    model_init_kwargs={"attn_implementation": "sdpa", "dtype": torch.bfloat16},
    seed=0,
)
peft_cfg = LoraConfig(r=ns.lora_r, lora_alpha=2 * ns.lora_r, lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
trainer = GRPOTrainer(model=ns.model, args=cfg, train_dataset=ds, peft_config=peft_cfg, environment_factory=ENV_FACTORIES)
json.dump(vars(ns), open(os.path.join(ns.out, "args.json"), "w"), indent=1)
t0 = time.time()
trainer.train(resume_from_checkpoint=ns.resume)
trainer.save_model(os.path.join(ns.out, "final"))
print(f"TRAIN_DONE in {(time.time()-t0)/60:.1f} min", flush=True)
