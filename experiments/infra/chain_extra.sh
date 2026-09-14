#!/bin/bash
# chain_extra.sh — after chain_post_auto prints ALL_DONE: probe extra open models that the HF token can access.
# Mistral-7B-Instruct-v0.3 (accessible) now; Llama-3.1-8B-Instruct is retried at run time in case access was granted meanwhile.
set -u; export FLASHINFER_DISABLE_VERSION_CHECK=1 VLLM_USE_FLASHINFER_SAMPLER=0
until grep -q ALL_DONE /workspace/logs/chain-post-auto.log 2>/dev/null; do sleep 60; done
cd /workspace/environment
probe() { python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model "$1" --tag "$1" --scenarios /workspace/data/probe/probe.jsonl --out /workspace/experiments/probe-open/$1 --concurrency 12 --temperature 0.0 2>&1 | tail -2; }
if python3 -c "from huggingface_hub import snapshot_download as s; s('mistralai/Mistral-7B-Instruct-v0.3', allow_patterns=['*.json','*.safetensors','tokenizer*'])" >/dev/null 2>&1; then
  bash /workspace/experiments/infra/serve.sh mistralai/Mistral-7B-Instruct-v0.3 mistral-7b-instruct-v0.3 --tool-call-parser mistral --chat-template /vllm-workspace/examples/tool_chat_template_mistral.jinja \
    && { probe mistral-7b-instruct-v0.3; echo "PROBE_DONE mistral-7b-instruct-v0.3"; } || echo "SERVER_FAILED mistral"
fi
if python3 -c "from huggingface_hub import snapshot_download as s; s('meta-llama/Llama-3.1-8B-Instruct', allow_patterns=['*.json','*.safetensors','tokenizer*'])" >/dev/null 2>&1; then
  bash /workspace/experiments/infra/serve.sh meta-llama/Llama-3.1-8B-Instruct llama-3.1-8b-instruct --tool-call-parser llama3_json --chat-template /vllm-workspace/examples/tool_chat_template_llama3.1_json.jinja \
    && { probe llama-3.1-8b-instruct; echo "PROBE_DONE llama-3.1-8b-instruct"; } || echo "SERVER_FAILED llama"
else echo "LLAMA_STILL_GATED"; fi
pkill -f 'vllm serve'; echo EXTRA_ALL_DONE
