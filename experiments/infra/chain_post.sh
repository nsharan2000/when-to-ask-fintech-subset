#!/bin/bash
# chain_post.sh — after GRPO run1: evaluate the trained LoRA, capability retention (base + trained), then re-run the two
# thinking-mode open models with a completion budget large enough for their reasoning (6144 tokens).
set -u
export FLASHINFER_DISABLE_VERSION_CHECK=1 VLLM_USE_FLASHINFER_SAMPLER=0
LORA=${LORA:-/workspace/experiments/grpo/run1/final}
echo "=== chain_post start $(date)"
bash /workspace/experiments/evals/eval_checkpoint.sh "$LORA" trained-run1
bash /workspace/experiments/evals/capability.sh base
bash /workspace/experiments/evals/capability.sh trained-run1 "$LORA"
cd /workspace/environment
for spec in "Qwen/Qwen3-4B|qwen3-4b-thinking" "Qwen/Qwen3-8B|qwen3-8b"; do
  M="${spec%%|*}"; T="${spec##*|}"
  rm -rf /workspace/experiments/probe-open/$T
  bash /workspace/experiments/infra/serve.sh "$M" "$T" --tool-call-parser hermes --reasoning-parser qwen3 --max-model-len 12288 || { echo "SKIP $T"; continue; }
  python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model "$T" --tag "$T" --scenarios /workspace/data/probe/probe.jsonl --out /workspace/experiments/probe-open/$T --concurrency 12 --temperature 0.0 --max-tokens 6144 2>&1 | tail -3
  echo "PROBE_DONE $T"
done
pkill -f 'vllm serve'
echo "=== chain_post end $(date)"
