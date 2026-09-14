#!/bin/bash
# chain_run2.sh — after the post-training chains finish: GRPO run2 on the v2 data (realistic phrasing bank, larger worlds, extra
# triggers), then evaluate run1 and run2 side by side on: v1 probe (run2), v2 test, v2 held-out domains, METR-derived (both).
set -u; export FLASHINFER_DISABLE_VERSION_CHECK=1 VLLM_USE_FLASHINFER_SAMPLER=0 TRL_EXPERIMENTAL_SILENCE=1
until grep -q EXTRA_ALL_DONE /workspace/logs/chain-extra.log 2>/dev/null || grep -q ALL_DONE /workspace/logs/chain-post-auto.log 2>/dev/null && ! pgrep -f chain_extra.sh >/dev/null; do sleep 60; done
pkill -f 'vllm serve'; sleep 5
echo "=== run2 training start $(date)"
cd /workspace && python3 experiments/grpo/train_grpo.py --train /workspace/data/train_v2.jsonl --out /workspace/experiments/grpo/run2 --max-steps ${MAX_STEPS:-300} 2>&1 | grep -vE "Warning|warn\("
echo "=== run2 training end $(date)"
R1=/workspace/experiments/grpo/run1/final; R2=/workspace/experiments/grpo/run2/final; [ -d "$R2" ] || R2=$(ls -d /workspace/experiments/grpo/run2/checkpoint-* | sort -t- -k2 -n | tail -1)
cd /workspace/environment
bash /workspace/experiments/infra/serve.sh Qwen/Qwen3-4B-Instruct-2507 qwen3-4b-instruct --tool-call-parser hermes --enable-lora --lora-modules run1=$R1 run2=$R2 --max-lora-rank 32 --gpu-memory-utilization 0.45 || { echo SERVER_FAILED; exit 1; }
probe() { python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model "$1" --tag "$2" --scenarios "$3" --out "$4" --concurrency 12 --temperature 0.0 2>&1 | tail -2; }
for S in test_v2 heldout_v2; do
  probe qwen3-4b-instruct base /workspace/data/$S.jsonl /workspace/experiments/evals/base/$S
  probe run1 trained-run1 /workspace/data/$S.jsonl /workspace/experiments/evals/trained-run1/$S
  probe run2 trained-run2 /workspace/data/$S.jsonl /workspace/experiments/evals/trained-run2/$S
  echo "V2EVAL_DONE $S"
done
if [ -f /workspace/data/metr_derived/metr_derived.jsonl ]; then
  probe qwen3-4b-instruct base /workspace/data/metr_derived/metr_derived.jsonl /workspace/experiments/evals/base/metr
  probe run1 trained-run1 /workspace/data/metr_derived/metr_derived.jsonl /workspace/experiments/evals/trained-run1/metr
  probe run2 trained-run2 /workspace/data/metr_derived/metr_derived.jsonl /workspace/experiments/evals/trained-run2/metr
  echo "METR_EVAL_DONE"
fi
probe run2 trained-run2 /workspace/data/probe/probe.jsonl /workspace/experiments/probe-open/trained-run2; echo "PROBE_DONE trained-run2"
pkill -f 'vllm serve'
bash /workspace/experiments/evals/capability.sh trained-run2 "$R2"
echo RUN2_ALL_DONE
