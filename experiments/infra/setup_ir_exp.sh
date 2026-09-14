#!/bin/bash
# setup_ir_exp.sh — bring the fresh ir-exp container to the TRL-compatible stack.
# Idempotent. Runs INSIDE the container. Log: /workspace/logs/setup-vllm.log
# Rules (research-documents/training-methods.md): vLLM must be in [0.19.1, 0.29.0] for TRL; never install flash-attn;
# cu130 nightly wheels for aarch64/sm_121.
set -x
export PIP_DISABLE_PIP_VERSION_CHECK=1
python3 -m pip install -U "peft>=0.17" 2>&1 | tail -2
python3 -m pip install -U --pre "vllm>=0.19.1,<0.30" --extra-index-url https://wheels.vllm.ai/nightly/cu130 2>&1 | tail -15
python3 -m pip install -U "trl>=1.13" "openai>=1.50" "datasets" "accelerate" 2>&1 | tail -2
python3 - <<'PY'
import torch, transformers
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
import vllm, trl, peft
print("vllm", vllm.__version__, "trl", trl.__version__, "peft", peft.__version__, "transformers", transformers.__version__)
PY
echo SETUP_VLLM_DONE
