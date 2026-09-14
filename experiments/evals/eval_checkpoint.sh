#!/bin/bash
# eval_checkpoint.sh <lora-dir> <tag> — serve base + LoRA via vLLM, run probe / in-dist test / held-out; then IFEval+GSM8K subsets via lm_eval.
set -u
LORA="$1"; TAG="$2"
cd /workspace/environment
export FLASHINFER_DISABLE_VERSION_CHECK=1 VLLM_USE_FLASHINFER_SAMPLER=0
bash /workspace/experiments/infra/serve.sh Qwen/Qwen3-4B-Instruct-2507 qwen3-4b-instruct --tool-call-parser hermes --enable-lora --lora-modules "askbc=$LORA" --max-lora-rank 32 || exit 1
for S in probe test_indist heldout; do
  F=/workspace/data/$S.jsonl; [ "$S" = probe ] && F=/workspace/data/probe/probe.jsonl
  OUT=/workspace/experiments/evals/$TAG/$S; [ "$S" = probe ] && OUT=/workspace/experiments/probe-open/$TAG
  python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model askbc --tag "$TAG" --scenarios "$F" --out "$OUT" --concurrency 12 --temperature 0.0 2>&1 | tail -2
done
pkill -f 'vllm serve'; sleep 5
echo "ASKBC_EVALS_DONE $TAG"
