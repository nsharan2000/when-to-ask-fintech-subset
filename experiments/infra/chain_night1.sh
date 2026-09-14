#!/bin/bash
# chain_night1.sh — Fri-night GPU chain (one job at a time): extra open-model baselines on the probe, the base model on the
# in-dist test + held-out sets, then the full GRPO run. Idempotent: the driver skips finished episodes.
set -u
export FLASHINFER_DISABLE_VERSION_CHECK=1 VLLM_USE_FLASHINFER_SAMPLER=0
cd /workspace/environment
probe() {  # probe <tag> <served-name> <scenarios> <outdir>
  python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model "$2" --tag "$1" --scenarios "$3" --out "$4" --concurrency 12 --temperature 0.0 2>&1 | tail -3
}
run_model() {  # run_model <hf-model> <tag> <extra vllm args...>
  local M="$1" T="$2"; shift 2
  bash /workspace/experiments/infra/serve.sh "$M" "$T" "$@" || { echo "SKIP $T (server failed)"; return; }
  probe "$T" "$T" /workspace/data/probe/probe.jsonl /workspace/experiments/probe-open/$T
  echo "PROBE_DONE $T"
}
echo "=== chain_night1 start $(date)"
run_model Qwen/Qwen3-4B qwen3-4b-thinking --tool-call-parser hermes --reasoning-parser qwen3
if [ -d /root/.cache/huggingface/hub/models--Qwen--Qwen3-8B ]; then run_model Qwen/Qwen3-8B qwen3-8b --tool-call-parser hermes --reasoning-parser qwen3; fi
if [ -d /root/.cache/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct ]; then run_model meta-llama/Llama-3.1-8B-Instruct llama-3.1-8b-instruct --tool-call-parser llama3_json; fi
# base Qwen3-4B-Instruct on the larger eval sets (the "before" numbers for the trained model)
bash /workspace/experiments/infra/serve.sh Qwen/Qwen3-4B-Instruct-2507 qwen3-4b-instruct --tool-call-parser hermes && {
  probe qwen3-4b-instruct-2507 qwen3-4b-instruct /workspace/data/test_indist.jsonl /workspace/experiments/evals/base/test_indist
  probe qwen3-4b-instruct-2507 qwen3-4b-instruct /workspace/data/heldout.jsonl /workspace/experiments/evals/base/heldout
  echo "BASE_EVALS_DONE"; }
pkill -f 'vllm serve'; sleep 5
echo "=== training start $(date)"
cd /workspace && TRL_EXPERIMENTAL_SILENCE=1 python3 experiments/grpo/train_grpo.py --out /workspace/experiments/grpo/run1 --max-steps ${MAX_STEPS:-300} 2>&1 | grep -vE "Warning|warn\("
echo "=== chain_night1 end $(date)"
