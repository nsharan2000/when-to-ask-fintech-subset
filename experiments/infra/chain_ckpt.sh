#!/bin/bash
# chain_ckpt.sh — after RUN2_ALL_DONE: evaluate intermediate checkpoints of run1 and run2 (final checkpoints over-ask; select by the
# in-distribution validation set, never by the held-out set), re-run Mistral with the fixed tool-call ids, and METR-derived evals
# for base / run1 / run2 if the set exists. Then CKPT_ALL_DONE.
set -u; export FLASHINFER_DISABLE_VERSION_CHECK=1 VLLM_USE_FLASHINFER_SAMPLER=0
until grep -q RUN2_ALL_DONE /workspace/logs/chain-run2.log 2>/dev/null; do sleep 60; done
pkill -f 'vllm serve'; sleep 5
cd /workspace/environment
probe() { python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model "$1" --tag "$2" --scenarios "$3" --out "$4" --concurrency 12 --temperature 0.0 2>&1 | tail -1; }
MODS=""
for spec in run1:150 run1:200 run1:250 run2:100 run2:150 run2:200 run2:250; do R=${spec%%:*}; K=${spec##*:}; D=/workspace/experiments/grpo/$R/checkpoint-$K; [ -d "$D" ] && MODS="$MODS ${R}ck$K=$D"; done
echo "adapters:$MODS"
bash /workspace/experiments/infra/serve.sh Qwen/Qwen3-4B-Instruct-2507 qwen3-4b-instruct --tool-call-parser hermes --enable-lora --lora-modules $MODS --max-lora-rank 32 --max-loras 4 --gpu-memory-utilization 0.45 || { echo SERVER_FAILED; exit 1; }
for spec in $MODS; do NAME=${spec%%=*}; TAG=trained-$NAME
  probe $NAME $TAG /workspace/data/probe/probe.jsonl /workspace/experiments/probe-open/$TAG
  probe $NAME $TAG /workspace/data/test_indist.jsonl /workspace/experiments/evals/$TAG/test_indist
  probe $NAME $TAG /workspace/data/heldout.jsonl /workspace/experiments/evals/$TAG/heldout
  [ -f /workspace/data/metr_derived/metr_derived.jsonl ] && probe $NAME $TAG /workspace/data/metr_derived/metr_derived.jsonl /workspace/experiments/evals/$TAG/metr
  echo "CKPT_DONE $TAG"
done
if [ -f /workspace/data/metr_derived/metr_derived.jsonl ]; then
  for spec in "qwen3-4b-instruct:base" "run1ck200:trained-run1-final"; do :; done
  probe qwen3-4b-instruct base /workspace/data/metr_derived/metr_derived.jsonl /workspace/experiments/evals/base/metr; echo "METR_DONE base"
fi
pkill -f 'vllm serve'; sleep 5
bash /workspace/experiments/infra/serve.sh mistralai/Mistral-7B-Instruct-v0.3 mistral-7b-instruct-v0.3 --tool-call-parser mistral --chat-template /vllm-workspace/examples/tool_chat_template_mistral.jinja \
  && { rm -rf /workspace/experiments/probe-open/mistral-7b-instruct-v0.3; probe mistral-7b-instruct-v0.3 mistral-7b-instruct-v0.3 /workspace/data/probe/probe.jsonl /workspace/experiments/probe-open/mistral-7b-instruct-v0.3; echo "PROBE_DONE mistral-7b-instruct-v0.3"; } || echo "SERVER_FAILED mistral"
pkill -f 'vllm serve'
echo CKPT_ALL_DONE
