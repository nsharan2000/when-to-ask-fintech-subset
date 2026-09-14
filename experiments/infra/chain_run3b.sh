#!/bin/bash
# chain_run3b.sh — run3 training could not start while run2 still held the GPU; this waits for chain_run3's evaluation pass to
# finish (RUN3_ALL_DONE), then trains run3 on the corrected v2 data and evaluates its checkpoints on every set + capability.
set -u; export FLASHINFER_DISABLE_VERSION_CHECK=1 VLLM_USE_FLASHINFER_SAMPLER=0 TRL_EXPERIMENTAL_SILENCE=1
until grep -q RUN3_ALL_DONE /workspace/logs/chain-run3.log 2>/dev/null; do sleep 60; done
pkill -f 'vllm serve'; pkill -f lm_eval; sleep 10
echo "=== run3 training start $(date)"; free -g | head -2 | tail -1
cd /workspace && python3 experiments/grpo/train_grpo.py --train /workspace/data/train_v2.jsonl --out /workspace/experiments/grpo/run3 --max-steps ${MAX_STEPS:-300} 2>&1 | grep -vE "Warning|warn\("
echo "=== run3 training end $(date)"
cd /workspace/environment
SETS="probe:/workspace/data/probe/probe.jsonl test_indist:/workspace/data/test_indist.jsonl heldout:/workspace/data/heldout.jsonl test_v2:/workspace/data/test_v2.jsonl heldout_v2:/workspace/data/heldout_v2.jsonl metr:/workspace/data/metr_derived/metr_derived.jsonl"
probe() { python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model "$1" --tag "$2" --scenarios "$3" --out "$4" --concurrency 20 --temperature 0.0 2>&1 | tail -1; }
outdir() { [ "$1" = probe ] && echo /workspace/experiments/probe-open/$2 || echo /workspace/experiments/evals/$2/$1; }
MODS=""; for K in 100 150 200 250 300; do D=/workspace/experiments/grpo/run3/checkpoint-$K; [ -d "$D" ] && MODS="$MODS run3ck$K=$D"; done
echo "adapters:$MODS"
bash /workspace/experiments/infra/serve.sh Qwen/Qwen3-4B-Instruct-2507 qwen3-4b-instruct --tool-call-parser hermes --enable-lora --lora-modules $MODS --max-lora-rank 32 --max-loras 4 --gpu-memory-utilization 0.5 || { echo SERVER_FAILED; exit 1; }
for S in $SETS; do NAME=${S%%:*}; F=${S##*:}
  for spec in $MODS; do A=${spec%%=*}; probe $A trained-$A "$F" "$(outdir $NAME trained-$A)"; done
  echo "SET_DONE run3 $NAME"
done
pkill -f 'vllm serve'; sleep 5
BEST=$(python3 - <<'PY'
import json,glob
best=None
for p in glob.glob('/workspace/experiments/evals/trained-run3ck*/test_indist/summary.json'):
    a=json.load(open(p))['overall']['paired_acc']; tag=p.split('/')[-3]
    if best is None or a>best[0]: best=(a,tag)
print(best[1].replace('trained-run3ck','') if best else '300')
PY
)
echo "BEST_RUN3_CKPT $BEST"
bash /workspace/experiments/evals/capability.sh trained-run3ck$BEST /workspace/experiments/grpo/run3/checkpoint-$BEST
echo RUN3B_ALL_DONE
