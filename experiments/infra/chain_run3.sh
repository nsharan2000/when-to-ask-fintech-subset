#!/bin/bash
# chain_run3.sh — corrected data & grader (audit fixes: strict keywords, typo corruption, buried decoys, categorical beliefs,
# +tool_injection, +batch_scope). Train run3 on train_v2, then ONE evaluation pass: base + run1 checkpoints + run3 checkpoints on
# probe / test_indist / heldout / test_v2 / heldout_v2 / metr. Stale episodes (old keyword lists) are deleted first so the
# resumable driver regenerates only those. Then other open models' stale re-runs + Mistral, then capability for run3's best.
set -u; export FLASHINFER_DISABLE_VERSION_CHECK=1 VLLM_USE_FLASHINFER_SAMPLER=0 TRL_EXPERIMENTAL_SILENCE=1
cd /workspace/environment
echo "=== run3 training start $(date)"
cd /workspace && python3 experiments/grpo/train_grpo.py --train /workspace/data/train_v2.jsonl --out /workspace/experiments/grpo/run3 --max-steps ${MAX_STEPS:-300} 2>&1 | grep -vE "Warning|warn\("
echo "=== run3 training end $(date)"
cd /workspace/environment
SETS="probe:/workspace/data/probe/probe.jsonl test_indist:/workspace/data/test_indist.jsonl heldout:/workspace/data/heldout.jsonl test_v2:/workspace/data/test_v2.jsonl heldout_v2:/workspace/data/heldout_v2.jsonl metr:/workspace/data/metr_derived/metr_derived.jsonl"
# stale cleanup for everything already evaluated under the old keyword lists
for d in /workspace/experiments/probe-open/* /workspace/experiments/evals/*/*; do
  [ -d "$d/runs" ] || continue
  case "$d" in *probe-open*) F=/workspace/data/probe/probe.jsonl;; *test_indist*) F=/workspace/data/test_indist.jsonl;; *heldout*) F=/workspace/data/heldout.jsonl;; *) continue;; esac
  echo "stale $d: $(python3 tools/regrade_stale.py "$d" "$F")"
done
probe() { python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model "$1" --tag "$2" --scenarios "$3" --out "$4" --concurrency 20 --temperature 0.0 2>&1 | tail -1; }
outdir() { [ "$1" = probe ] && echo /workspace/experiments/probe-open/$2 || echo /workspace/experiments/evals/$2/$1; }
MODS=""; for spec in run1:150 run1:200 run3:150 run3:200 run3:250 run3:300; do R=${spec%%:*}; K=${spec##*:}; D=/workspace/experiments/grpo/$R/checkpoint-$K; [ -d "$D" ] && MODS="$MODS ${R}ck$K=$D"; done
echo "adapters:$MODS"
bash /workspace/experiments/infra/serve.sh Qwen/Qwen3-4B-Instruct-2507 qwen3-4b-instruct --tool-call-parser hermes --enable-lora --lora-modules $MODS --max-lora-rank 32 --max-loras 4 --gpu-memory-utilization 0.5 || { echo SERVER_FAILED; exit 1; }
for S in $SETS; do NAME=${S%%:*}; F=${S##*:}
  probe qwen3-4b-instruct $( [ $NAME = probe ] && echo qwen3-4b-instruct-2507 || echo base ) "$F" "$(outdir $NAME $( [ $NAME = probe ] && echo qwen3-4b-instruct-2507 || echo base ))"
  for spec in $MODS; do A=${spec%%=*}; probe $A trained-$A "$F" "$(outdir $NAME trained-$A)"; done
  echo "SET_DONE $NAME"
done
pkill -f 'vllm serve'; sleep 5
# other open models: stale re-runs (only if any) + Mistral fresh
for spec in "Qwen/Qwen3-8B|qwen3-8b|--tool-call-parser hermes --reasoning-parser qwen3 --max-model-len 12288|6144" "Qwen/Qwen3-4B|qwen3-4b-thinking|--tool-call-parser hermes --reasoning-parser qwen3 --max-model-len 12288|6144" "meta-llama/Llama-3.1-8B-Instruct|llama-3.1-8b-instruct|--tool-call-parser llama3_json --chat-template /vllm-workspace/examples/tool_chat_template_llama3.1_json.jinja|4096" "mistralai/Mistral-7B-Instruct-v0.3|mistral-7b-instruct-v0.3|--tool-call-parser mistral --chat-template /vllm-workspace/examples/tool_chat_template_mistral.jinja|4096"; do
  IFS='|' read -r M T ARGS MT <<< "$spec"
  N=$(ls /workspace/experiments/probe-open/$T/runs 2>/dev/null | wc -l)
  [ "$N" -ge 96 ] && { echo "SKIP $T (complete)"; continue; }
  bash /workspace/experiments/infra/serve.sh "$M" "$T" $ARGS || { echo "SERVER_FAILED $T"; continue; }
  python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model "$T" --tag "$T" --scenarios /workspace/data/probe/probe.jsonl --out /workspace/experiments/probe-open/$T --concurrency 12 --temperature 0.0 --max-tokens $MT 2>&1 | tail -1
  echo "PROBE_DONE $T"; pkill -f 'vllm serve'; sleep 5
done
BEST=$(python3 - <<'PY'
import json,glob,os
best=None
for p in glob.glob('/workspace/experiments/evals/trained-run3ck*/test_indist/summary.json'):
    a=json.load(open(p))['overall']['paired_acc']; tag=p.split('/')[-3]
    if best is None or a>best[0]: best=(a,tag)
print(best[1].replace('trained-run3ck','') if best else '300')
PY
)
echo "BEST_RUN3_CKPT $BEST"
bash /workspace/experiments/evals/capability.sh trained-run3ck$BEST /workspace/experiments/grpo/run3/checkpoint-$BEST
echo RUN3_ALL_DONE
