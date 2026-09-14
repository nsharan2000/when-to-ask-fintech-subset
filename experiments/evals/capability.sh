#!/bin/bash
# capability.sh <tag> [lora-dir] — IFEval + GSM8K (fixed 250-item subsets, identical for base and trained) with lm-evaluation-harness, HF backend.
set -u
TAG="$1"; LORA="${2:-}"
ARGS="pretrained=Qwen/Qwen3-4B-Instruct-2507,dtype=bfloat16,attn_implementation=sdpa"
[ -n "$LORA" ] && ARGS="$ARGS,peft=$LORA"
mkdir -p /workspace/experiments/evals/$TAG/capability
python3 -m lm_eval --model hf --model_args "$ARGS" --tasks ifeval,gsm8k --limit 250 --batch_size 8 --apply_chat_template --fewshot_as_multiturn \
  --output_path /workspace/experiments/evals/$TAG/capability --log_samples 2>&1 | grep -vE "Warning|warn" | tail -25
echo "CAPABILITY_DONE $TAG"
