#!/bin/bash
# chain_mistral_fix.sh — Mistral probe re-run from scratch. The final pass kept 95 stale run files (tool-call id "call_1" from
# before the 9-char id fix; the resumable driver skipped them). Old files are moved to probe-open/_invalid/mistral-stale-callid/.
set -u; export FLASHINFER_DISABLE_VERSION_CHECK=1 VLLM_USE_FLASHINFER_SAMPLER=0
cd /workspace/environment; echo "=== mistral fix start $(date)"
T=mistral-7b-instruct-v0.3; D=/workspace/experiments/probe-open/$T
mkdir -p /workspace/experiments/probe-open/_invalid && mv $D /workspace/experiments/probe-open/_invalid/mistral-stale-callid && mkdir -p $D
bash /workspace/experiments/infra/serve.sh mistralai/Mistral-7B-Instruct-v0.3 $T --tool-call-parser mistral --chat-template /vllm-workspace/examples/tool_chat_template_mistral.jinja || { echo SERVER_FAILED; exit 1; }
python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model $T --tag $T --scenarios /workspace/data/probe/probe.jsonl --out $D --concurrency 12 --temperature 0.0 --max-tokens 4096 2>&1 | tail -1
pkill -f 'vllm serve'; echo "MISTRAL_FIX_DONE $(date)"
