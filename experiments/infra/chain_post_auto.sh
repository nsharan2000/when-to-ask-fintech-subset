#!/bin/bash
# chain_post_auto.sh — waits for run1 to finish, then runs everything that remains, parallelised where memory allows:
#   [A] vLLM (base + 3 LoRA adapters: final, checkpoint-100, checkpoint-200) → trained-final on probe/test_indist/heldout,
#       checkpoint-100/200 on probe (checkpoint curve)          ‖  [B] lm_eval IFEval+GSM8K on the trained adapter (HF backend)
#   then [C] thinking-model re-runs at a 6144-token budget (Qwen3-4B-thinking, Qwen3-8B), sequential on the same port.
# Every stage writes a marker line; the whole log is /workspace/logs/chain-post-auto.log. Idempotent (driver skips finished episodes).
set -u
export FLASHINFER_DISABLE_VERSION_CHECK=1 VLLM_USE_FLASHINFER_SAMPLER=0
RUN=/workspace/experiments/grpo/run1
until grep -qE "TRAIN_DONE|chain_night1 end" /workspace/logs/chain-night1.log 2>/dev/null; do sleep 60; done
echo "=== chain_post_auto start $(date)"
pkill -f train_grpo; pkill -f 'vllm serve'; sleep 5
FINAL=$RUN/final; [ -d "$FINAL" ] || FINAL=$(ls -d $RUN/checkpoint-* | sort -t- -k2 -n | tail -1)
CK100=$RUN/checkpoint-100; CK200=$RUN/checkpoint-200
echo "adapters: final=$FINAL"
cd /workspace/environment
# ---- [B] capability on the trained adapter, in the background (HF backend, ~15 GB)
( bash /workspace/experiments/evals/capability.sh trained-run1 "$FINAL" > /workspace/logs/capability-trained.log 2>&1; echo "CAP_TRAINED_DONE $(date)" ) &
# ---- [A] vLLM with three adapters
MODS="askbc=$FINAL"; [ -d "$CK100" ] && MODS="$MODS ck100=$CK100"; [ -d "$CK200" ] && MODS="$MODS ck200=$CK200"
bash /workspace/experiments/infra/serve.sh Qwen/Qwen3-4B-Instruct-2507 qwen3-4b-instruct --tool-call-parser hermes --enable-lora --lora-modules $MODS --max-lora-rank 32 --gpu-memory-utilization 0.40 || echo "SERVER_FAILED trained"
probe() { python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model "$1" --tag "$2" --scenarios "$3" --out "$4" --concurrency 12 --temperature 0.0 2>&1 | tail -2; }
probe askbc trained-run1 /workspace/data/probe/probe.jsonl /workspace/experiments/probe-open/trained-run1 ; echo "PROBE_DONE trained-run1"
probe askbc trained-run1 /workspace/data/test_indist.jsonl /workspace/experiments/evals/trained-run1/test_indist ; echo "TEST_DONE trained-run1"
probe askbc trained-run1 /workspace/data/heldout.jsonl /workspace/experiments/evals/trained-run1/heldout ; echo "HELDOUT_DONE trained-run1"
[ -d "$CK100" ] && { probe ck100 trained-ck100 /workspace/data/probe/probe.jsonl /workspace/experiments/probe-open/trained-ck100; echo "PROBE_DONE trained-ck100"; }
[ -d "$CK200" ] && { probe ck200 trained-ck200 /workspace/data/probe/probe.jsonl /workspace/experiments/probe-open/trained-ck200; echo "PROBE_DONE trained-ck200"; }
pkill -f 'vllm serve'; sleep 5
echo "ASKBC_EVALS_DONE $(date)"
# ---- [C] thinking-model re-runs with a large reasoning budget
for spec in "Qwen/Qwen3-4B|qwen3-4b-thinking" "Qwen/Qwen3-8B|qwen3-8b"; do
  M="${spec%%|*}"; T="${spec##*|}"
  rm -rf /workspace/experiments/probe-open/$T
  bash /workspace/experiments/infra/serve.sh "$M" "$T" --tool-call-parser hermes --reasoning-parser qwen3 --max-model-len 12288 || { echo "SKIP $T"; continue; }
  python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model "$T" --tag "$T" --scenarios /workspace/data/probe/probe.jsonl --out /workspace/experiments/probe-open/$T --concurrency 12 --temperature 0.0 --max-tokens 6144 2>&1 | tail -2
  echo "PROBE_DONE $T"
done
pkill -f 'vllm serve'
wait
echo "=== chain_post_auto end $(date)"
echo ALL_DONE
