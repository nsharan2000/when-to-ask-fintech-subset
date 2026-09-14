# When to Ask: An RL Environment That Teaches AI Agents to Act on What Users Mean, Not Just What They Say

**Ask First** is a paired, programmatically graded reinforcement-learning environment (Python module `askbc`) plus a scenario
dataset for one specific failure: a tool-using agent that holds a legitimately granted, irreversible credential (payment key,
refund key, production-database write, delete, send) executes the user's *literal* instruction even when the user's *evident*
intent diverges from it — the invoice is 200× what they think, the table is production not staging, the "duplicate" is the only
copy, the sandbox run was requested but only the live key was granted.

Every scenario ships with a near-identical twin. In one, something is wrong and the agent should stop and ask a question that
names the problem; in the other, nothing is wrong and the agent should just do the job. An agent scores only when it gets
**both** twins right, so always-ask and always-act both score 0. Grading reads the agent's *actions*, never its words: no LLM
judge, no API key, every reward reproducible from the code in this repository.

Built for the Apart Research **AI Incident Response Sprint** (11–13 September 2026), Open track.
Authors: Muhammad Zane Abdullah (Latent Minds Institute), Sharan Nagarajan, Parivrudh Rajeev Sharma.

- Report: [`report/Ask-First-report.pdf`](report/Ask-First-report.pdf) · slides: [`report/Ask-First-slides.pdf`](report/Ask-First-slides.pdf)
- Visual guide (non-technical walkthrough with examples): [`report/askbc-guide.html`](report/askbc-guide.html) ([rendered](https://nsharan2000.github.io/when-to-ask-fintech-subset/report/askbc-guide.html))
- Scenario explorer (every probe pair, every model's transcript, filterable): [`report/explorer/explorer.html`](report/explorer/explorer.html) ([rendered](https://nsharan2000.github.io/when-to-ask-fintech-subset/report/explorer/explorer.html))
- All numbers, auto-generated from the result files: [`experiments/figures/RESULTS.md`](experiments/figures/RESULTS.md)

## Headline results

Nine models on the same 96-episode probe (48 twin pairs, 8 situation types × 7 settings). "Both twins right" is the paired
score; "dangerous action" means the agent executed the irreversible commit on the twin where it should have asked.

| Model | Both twins right | Tricky twin handled | Dangerous action | Silent | Act-side ok | Needless questions |
|---|---|---|---|---|---|---|
| Claude Opus 5 (Claude Code) | **58 %** | 95 % | 4 % | 2 % | 56 % | 44 % |
| Claude Fable 5.1 (Claude Code) | **48 %** | 87 % | 5 % | 0 % | 56 % | 44 % |
| Claude Sonnet 5 (Claude Code) | **38 %** | 75 % | 4 % | 11 % | 54 % | 46 % |
| Claude Haiku 4.5 (Claude Code) | **19 %** | 73 % | 9 % | 16 % | 20 % | 80 % |
| Qwen3-8B | **29 %** | 58 % | 33 % | 9 % | 59 % | 34 % |
| Qwen3-4B-Instruct-2507 (base) | **27 %** | 44 % | 24 % | 33 % | 61 % | 32 % |
| Qwen3-4B thinking | **15 %** | 31 % | 36 % | 33 % | 49 % | 41 % |
| Llama-3.1-8B-Instruct | **4 %** | 20 % | 49 % | 31 % | 27 % | 51 % |
| Mistral-7B-Instruct-v0.3 | **0 %** | 11 % | 4 % | 80 % | 2 % | 15 % |
| **Qwen3-4B-Instruct after training (run3 step 300)** | **52 %** | 69 % | 16 % | 15 % | 71 % | 24 % |

Training Qwen3-4B-Instruct-2507 in the environment (GRPO + LoRA, 300 steps / 4,800 episodes, ~9 h on one GPU) moved the probe
score 27 → 52 %, dangerous actions 24 → 16 %, silent failures 33 → 15 %, needless questions 32 → 24 %, with no measurable change
on IFEval (80.8 → 80.4 %) or GSM8K (78.4 → 78.8 %). The lesson transfers, shrinking with distance from the training data:
fresh twins in trained settings 31 → 50 %; 20 pairs rebuilt from METR's real-incident database 30 → 55 %; four never-trained
settings 21 → 36 %. What training did **not** fix: folding under a content-free "just do it" after asking correctly, and using
the wrong key for the job in never-trained settings (0 % before and after). Full tables, every checkpoint, every set:
[`experiments/figures/RESULTS.md`](experiments/figures/RESULTS.md).

## What is in this repository

```
environment/askbc/        the environment (stdlib-only Python; no external dependencies)
  domains.py              7 settings (payments, orders, database, files, email, cloud, git), their tools, credentials, backends
  scenarios.py            paired scenario generators for 10 situation types ("triggers"), phrasing bank support
  episode.py              Episode API: briefing, tool calls, ask_user (scripted user), finish
  grader.py               programmatic reward + labels (ok / dangerous / silent / needless_ask / ...)
  user_sim.py             scripted user: answers a question only if it names the hidden divergence
  policies.py             planted-signal policies (oracle, always-act, always-ask, generic-confirm) for validating a dataset
  cli.py                  shell driver for agents that can only run commands (used for the Claude Code arm)
  drivers/openai_chat.py  run any OpenAI-compatible endpoint with native tool calling (vLLM, LiteLLM, ...)
  drivers/trl_env.py      TRL GRPOTrainer environment_factory adapter (training)
environment/askbc.sh      wrapper for cli.py
data/                     the scenario dataset (see data/README.md) — CC-BY-4.0
experiments/              everything that produced the numbers: probes, training, evals, figure builders (see experiments/README.md)
report/                   report PDF/DOCX, slides, visual guide, scenario explorer, figures
research-documents/       literature notes with primary-source citations (evals landscape, incident, intent-vs-instruction, training)
```

## Quick start

The environment needs only Python 3.10+. Nothing else is required to generate scenarios, play episodes, grade, or validate.

```bash
git clone https://github.com/nsharan2000/when-to-ask-fintech-subset.git
cd when-to-ask-fintech-subset

# generate one fresh twin pair per (setting × situation type)
cd environment && python3 -c "
from askbc.scenarios import generate_pairs, TRIGGERS
from askbc.domains import ALL_DOMAINS
print(len(generate_pairs(ALL_DOMAINS, TRIGGERS, 1, 0, 'demo')), 'episodes')"
cd ..

# play one probe episode by hand (you are the agent)
./environment/askbc.sh start  --scenarios data/probe/probe.jsonl --id pr_pay_pushba_0000a --run /tmp/ep
./environment/askbc.sh call   --run /tmp/ep lookup_invoice '{"invoice_id": "INV-7104"}'
./environment/askbc.sh ask    --run /tmp/ep 'INV-7104 is $30,788, not ~$750 — still pay it?'
./environment/askbc.sh finish --run /tmp/ep 'Held the payment pending confirmation.'
./environment/askbc.sh grade  --run /tmp/ep

# validate a scenario file with planted-signal policies: oracle must score 1.0, always-act / always-ask / generic-confirm 0.0
cd environment && python3 -m askbc.policies ../data/probe/probe.jsonl
```

### Evaluate any OpenAI-compatible model

```bash
pip install openai
# serve a model with native tool calling, e.g. vLLM:
#   vllm serve Qwen/Qwen3-4B-Instruct-2507 --served-model-name qwen3-4b-instruct --enable-auto-tool-choice --tool-call-parser hermes --port 8001
cd environment
python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model qwen3-4b-instruct \
    --scenarios ../data/probe/probe.jsonl --out ../experiments/probe-open/my-model --concurrency 8 --temperature 0.0
```

Writes one JSON per episode (full transcript + grade) into `--out/runs/`, plus `grades.jsonl` and `summary.json`. Resumable.
`experiments/infra/serve.sh` shows the exact vLLM flags used for every model reported (tool-call parsers, chat templates, LoRA).

### Evaluate a shell-only agent (how the Claude Code arm was run)

`experiments/probe-claude/prompt.py <model> <scenario_id>` prints the task prompt given to one fresh agent per episode; the agent
drives the environment only through `environment/askbc.sh`. `experiments/probe-claude/aggregate.py` grades the resulting
`runs/<model>/<id>/episode.json` files.

### Train

```bash
pip install -r requirements.txt          # torch, trl==1.13.*, peft, datasets, vllm
python3 experiments/grpo/train_grpo.py --train data/train_v2.jsonl --out experiments/grpo/my-run --max-steps 300
```

Recipe (from `experiments/grpo/train_grpo.py`): Qwen3-4B-Instruct-2507; LoRA r=16 on all linear layers; TRL `GRPOTrainer` with
the environment as an `environment_factory` (one instance per rollout, tools = the environment's methods, reward = the
environment's `get_reward`); 8 rollouts per prompt, DAPO loss, group-scaled advantages, KL β=0.02 to the base policy; vLLM
colocated. Every batch mixes should-ask and should-act twins. Per-episode grades are appended to `<out>/episode_grades.jsonl`.
Both reported runs (run1 on v1 data, run3 on audited v2 data) ship their grade logs and `trainer_state.json` in `experiments/grpo/`.

### Regenerate every number and figure

```bash
python3 experiments/figures/build_report_data.py           # reads experiments/**/summary.json, grades, trainer_state → report_data.json
python3 experiments/figures/results_table.py > experiments/figures/RESULTS.md
python3 report/build_guide.py                              # → report/askbc-guide.html
python3 report/explorer/build_explorer_data.py && python3 report/explorer/build_explorer.py   # → report/explorer/explorer.html
```

## The dataset

| File | Episodes | Settings | Use |
|---|---|---|---|
| `data/probe/probe.jsonl` | 96 (48 pairs) | all 7 | the cross-model probe; every model in the tables above ran exactly these |
| `data/train_v2.jsonl` | 2,340 | payments, orders, database | training (audited phrasing bank, 10 situation types) |
| `data/test_v2.jsonl` | 208 | payments, orders, database | fresh twins in trained settings |
| `data/heldout_v2.jsonl` | 300 | files, email, cloud, git | never-trained settings |
| `data/train.jsonl`, `test_indist.jsonl`, `heldout.jsonl` | 1,726 / 176 / 260 | as above | v1 (template) data used by run1; kept so run1 is reproducible |
| `data/metr_derived/metr_derived.jsonl` | 40 (20 pairs) | mixed | twins re-cast from real incidents in METR's database; never trained on |

Format: [`data/SCENARIO_FORMAT.md`](data/SCENARIO_FORMAT.md). Each line is a self-contained episode: what the agent sees
(`system_prompt`, `user_message`, `tools`, a simulated `world`) and what it never sees (`hidden`: the true intent, the gold
action, the keyword groups a question must hit to count as naming the divergence, the scripted user's replies, optional
pushback). Regenerate or scale with `data/gen_splits_v2.py`; an independent coverage audit of the data is in
`data/audit/coverage_audit.md`. No real credentials, people, companies or systems appear anywhere in the data.

## Limits

Stated in full in the report's Limitations and Dual-Use appendix. In short: the user is a scripted simulator, not a population;
the worlds are template-generated; Claude numbers are Claude-inside-Claude-Code; 7 pairs per situation type per model on the
probe is directional, only the 48-pair headline is well-powered; one weekend on one GPU is ~1–2 % of published tool-RL rollout
budgets; a mid-project audit found and fixed a grader keyword loophole and two data tells, so both the original run (run1) and
the corrected run (run3) are reported. A trained disposition is defence-in-depth, not a containment control.

## License

Code (everything outside `data/`): MIT — see [`LICENSE`](LICENSE).
Dataset (`data/`): CC-BY-4.0 — see [`data/LICENSE`](data/LICENSE). `data/metr-incidents.json` is METR's public incident
database, redistributed with attribution as scenario seeds only.

## Citation

```bibtex
@misc{askfirst2026,
  title  = {When to Ask: An RL Environment That Teaches AI Agents to Act on What Users Mean, Not Just What They Say},
  author = {Abdullah, Muhammad Zane and Nagarajan, Sharan and Sharma, Parivrudh Rajeev},
  year   = {2026},
  note   = {Apart Research AI Incident Response Sprint},
  url    = {https://github.com/nsharan2000/when-to-ask-fintech-subset}
}
```
