#!/bin/bash
# serve.sh <hf-model> <served-name> [extra vllm args...] — start vLLM in the background (inside ir-exp) and wait until ready.
# Env fixes for vllm 0.29 on GB10: flashinfer cubin mismatch + sampler kernel mismatch.
MODEL="$1"; NAME="$2"; shift 2
export FLASHINFER_DISABLE_VERSION_CHECK=1 VLLM_USE_FLASHINFER_SAMPLER=0
pkill -f 'vllm serve' 2>/dev/null; sleep 3
nohup vllm serve "$MODEL" --port 8001 --host 0.0.0.0 --enable-auto-tool-choice --max-model-len 8192 --gpu-memory-utilization 0.45 \
  --max-num-seqs 32 --served-model-name "$NAME" "$@" > /workspace/logs/vllm-$NAME.log 2>&1 &
for i in $(seq 1 120); do
  if curl -s -m 3 localhost:8001/v1/models | grep -q "$NAME"; then echo "SERVER_UP $NAME"; return 0 2>/dev/null || exit 0; fi
  if grep -q "Engine core initialization failed" /workspace/logs/vllm-$NAME.log 2>/dev/null; then echo "SERVER_FAILED $NAME"; return 1 2>/dev/null || exit 1; fi
  sleep 10
done
echo "SERVER_TIMEOUT $NAME"; exit 1
