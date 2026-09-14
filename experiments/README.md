# experiments/ — everything that produced the reported numbers

| Directory | What it holds |
|---|---|
| `probe-claude/` | Claude arm of the probe: `prompt.py` (the task prompt given to one fresh Claude Code agent per episode), `aggregate.py` (grader), `runs/<model>/<id>/episode.json` (every transcript), `grades_*.jsonl`, `summary_*.json` for Haiku 4.5, Sonnet 5, Opus 5, Fable 5.1 |
| `probe-open/` | Open-weight arm of the probe via vLLM (`askbc.drivers.openai_chat`): one directory per model or checkpoint with `runs/`, `grades.jsonl`, `summary.json` |
| `grpo/` | `train_grpo.py` (the training script) and, for run1 (v1 data) and run3 (audited v2 data), `episode_grades.jsonl` (every training rollout's grade) and `trainer_state.json`. Adapter weights are not versioned; retrain with the script |
| `evals/` | Post-training evaluations: `base/` and `trained-<run>ck<step>/`, each with `test_indist/`, `heldout/`, `metr/`, `test_v2/`, `heldout_v2/` (runs + grades + summary) and `capability/` (lm-evaluation-harness IFEval + GSM8K results and samples). `eval_checkpoint.sh`, `capability.sh` are the drivers |
| `infra/` | The exact shell chains that ran on the GPU box: `serve.sh` (vLLM flags per model: tool-call parser, chat template, LoRA modules), `setup_ir_exp.sh` (container setup), `chain_*.sh` (job sequences), `chain-eval-final.log.txt` (log of the final evaluation pass) |
| `figures/` | `build_report_data.py` (collects every summary/grade/trainer_state into `report_data.json`), `results_table.py` (→ `RESULTS.md`), `frontier_filtered.{json,md}` (probe restricted to pairs both frontier models got right) |

Paths inside `infra/*.sh` and `evals/*.sh` use `/workspace`, which was this repository mounted at the container root
(`setup_ir_exp.sh`). Replace with the repository path to run elsewhere. Hardware for every reported run: one NVIDIA GB10
(DGX Spark); a run of 300 GRPO steps took about nine hours.

Evaluation protocol (identical for every model and checkpoint): greedy decoding (temperature 0), same grader, same scenario
files, one pass. The selected checkpoint (run3 step 300) was chosen on `test_v2` only, before any other set was looked at.
