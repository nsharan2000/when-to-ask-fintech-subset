#!/bin/bash
# chain_llama.sh — after chain_post_auto prints ALL_DONE and the Llama download finished: probe Llama-3.1-8B-Instruct.
set -u; export FLASHINFER_DISABLE_VERSION_CHECK=1 VLLM_USE_FLASHINFER_SAMPLER=0
until grep -q ALL_DONE /workspace/logs/chain-post-auto.log 2>/dev/null && grep -q LLAMA_DOWNLOAD_DONE /workspace/logs/hf-download-llama.log 2>/dev/null; do sleep 60; done
grep -q LLAMA_OK /workspace/logs/hf-download-llama.log || { echo "LLAMA_NOT_DOWNLOADED"; exit 1; }
cd /workspace/environment
bash /workspace/experiments/infra/serve.sh meta-llama/Llama-3.1-8B-Instruct llama-3.1-8b-instruct --tool-call-parser llama3_json --chat-template /vllm-workspace/examples/tool_chat_template_llama3.1_json.jinja || { echo "SERVER_FAILED llama"; exit 1; }
python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model llama-3.1-8b-instruct --tag llama-3.1-8b-instruct --scenarios /workspace/data/probe/probe.jsonl --out /workspace/experiments/probe-open/llama-3.1-8b-instruct --concurrency 12 --temperature 0.0 2>&1 | tail -2
pkill -f 'vllm serve'; echo "PROBE_DONE llama-3.1-8b-instruct"; echo LLAMA_ALL_DONE
