# Training recipe — feasibility on one DGX Spark (GB10) in a weekend
Compiled 2026-09-11. **VERIFIED** = fetched, quoted · **CAVEATED** / **ESTIMATE** as marked.

## A. Framework: TRL `GRPOTrainer` + PEFT LoRA + vLLM colocate
- TRL is pure Python over torch/vllm/peft (no custom CUDA kernels → survives aarch64/sm_121). VERIFIED: `GRPOTrainer` supports
  `rollout_func` (custom multi-turn, "experimental") and `environment_factory` (stateful env with `reset()`/`get_reward()`/tool
  methods, `max_tool_calling_iterations`) — a direct fit for a gym. https://huggingface.co/docs/trl/main/en/grpo_trainer
- Colocate = default single-GPU mode; use weight-transfer backend `"ipc"`; vLLM sleep mode to save memory.
  https://huggingface.co/docs/trl/main/en/vllm_integration
- **BLOCKER (VERIFIED):** "TRL currently only supports vLLM versions from 0.19.1 to 0.29.0". Container has 0.16 → upgrade with
  `uv pip install -U vllm --extra-index-url https://wheels.vllm.ai/nightly/cu130` (AI2's dgx-spark-setup; vLLM's own 2026-06-01
  DGX Spark post runs cu130-nightly on sm_121).
- aarch64/CUDA-13 rules (VERIFIED, https://github.com/natolambert/dgx-spark-setup): **never install flash-attn** (slower than
  SDPA on Blackwell, breaks on libcudart.so.12) → `attn_implementation="sdpa"`; `export TRITON_PTXAS_PATH=/usr/local/cuda/bin/ptxas`;
  `--vllm_enforce_eager` (CAVEATED −20–30 % speed); unified memory means GPU OOM = host OOM → `swapoff -a` +
  `systemd-run --scope -p MemoryMax=100G -p MemorySwapMax=0`; rule of thumb GRPO memory ≈ SFT + vllm_gpu_memory_utilization × 119 GB.

## B. Throughput (ESTIMATE, anchors VERIFIED)
Anchors: Unsloth ran 1,000 RL steps in 4 h on Spark (gpt-oss-20b MoE, short episodes); vLLM decode on Spark ≈ 23 tok/s single-stream.
Bandwidth 273 GB/s bounds a 4B bf16 model at ~34 tok/s per stream; ~350–400 tok/s aggregate at concurrency 16.
One GRPO step = 8 prompts × 8 generations × ~600 tokens ≈ 38 k tokens → ~2 min generation + 1–2 min LoRA backward
→ **~3–4 min/step ⇒ ~400 steps ≈ 25 k episodes in 24 GPU-h.** ToolRL used ~50–100× this budget on 2×A100 → keep the env narrow.

## C. Forgetting — why RL + LoRA + KL (VERIFIED)
- RL's Razor (arXiv 2509.04259, ICLR 2026): "RL preserves prior knowledge and capabilities significantly better"; forgetting is
  predicted by "the KL-divergence between the fine-tuned and base policy evaluated on the new task"; on-policy RL "is implicitly
  biased towards KL-minimal solutions". → stay on-policy; **log KL(π‖π_ref) on our task every step as the forgetting proxy.**
- Retaining by Doing (arXiv 2510.18874): "RL leads to less forgetting than SFT"; "approximately on-policy data" suffices. No mixing
  ratio is prescribed — do not cite one.
- TRL defaults: `beta=0.0` (no reference), `num_generations=8`, `loss_type="dapo"`, `scale_rewards="group"`. **Set beta > 0**
  (start 0.01–0.04, CAVEATED); with LoRA the reference is the adapter-disabled model (free).

## D. Programmatic reward precedent (VERIFIED)
ToolRL (arXiv 2504.13958): 100 % rule-based, no judge — `R_format ∈ {0,1}` + `R_correct ∈ [−3,3]` from tool-name / parameter-name
Jaccard and value match; Qwen2.5-1.5B/3B/7B, GRPO, lr 1e-6; "17% improvement over base models and a 15% gain over SFT".
→ Keep format and outcome as separate additive terms; make outcome graded (state-diff overlap), not binary. No paper verified this
session that RL-trains ask-vs-act with a purely programmatic reward — our scripted user simulator is the novelty and must be
validated with planted-signal policies (always-act / always-ask / oracle).

## E. Recipe
- Qwen3-4B-Instruct-2507 (cached), LoRA r=16 (CAVEATED start), GRPO G=8, dapo loss, group scaling, beta 0.02, sdpa, vLLM colocate
  0.3–0.4 GPU memory, enforce-eager, MemoryMax rail, checkpoints every 50 steps → in-dist paired eval + BFCL canary.
- Reward: `R = R_format + R_outcome + R_gate` with `|R_gate| < |R_outcome|` overall; R_gate: commit-before-confirm on should-ask −3,
  ask on should-act −1, silent finish on should-ask −2, correct ask naming the hidden divergence slot +1 (episode continues).
- Every batch mixes should-ask and should-act twins; resample zero-variance groups; alarm if ask-rate leaves 20–60 %.
- Judging by Claude Code subagents happens offline on saved transcripts only.

## F. Pitfalls (VERIFIED mechanism unless marked)
1. **Always-ask / never-ask collapse**: with group-scaled advantages, a prompt whose 8 rollouts all take the same branch yields zero
   gradient, so collapse is self-sustaining. Mitigate with the paired batch mix and resampling (DAPO dynamic sampling, CAVEATED).
2. **Hacking the ask signal**: grade question content against the env's hidden divergence slot, never a surface string.
3. **Timid-everywhere generalisation / capability loss**: held-out tool families + BFCL + IFEval/GSM8K each checkpoint; rising KL is the alarm.
