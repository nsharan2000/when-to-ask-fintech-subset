# data/ — the Ask First scenario dataset (CC-BY-4.0, see `LICENSE`)

One JSON object per line, one line per episode; twins share `pair_id`, ids end in `a` (should-ask) or `b` (should-act).
Format: [`SCENARIO_FORMAT.md`](SCENARIO_FORMAT.md). Generators: `environment/askbc/scenarios.py`.

| File | Episodes | Settings | Situation types | Used for |
|---|---|---|---|---|
| `probe/probe.jsonl` | 96 (48 pairs) | all 7 | 8 | the identical cross-model probe every reported model ran |
| `train_v2.jsonl` | 2,340 | payments, orders, database | 10 | training run3 (audited phrasing bank, larger worlds) |
| `test_v2.jsonl` | 208 | payments, orders, database | 10 | fresh twins in trained settings; checkpoint selection used **only** this set |
| `heldout_v2.jsonl` | 300 | files, email, cloud, git | 10 | never-trained settings |
| `train.jsonl` | 1,726 | payments, orders, database | 8 | v1 template data, training run1 (kept for reproducibility) |
| `test_indist.jsonl` | 176 | payments, orders, database | 8 | v1 fresh twins |
| `heldout.jsonl` | 260 | files, email, cloud, git | 8 | v1 never-trained settings |
| `metr_derived/metr_derived.jsonl` | 40 (20 pairs) | mixed | mixed | twins re-cast from real incidents; never trained on (see `metr_derived/README.md`) |

Zero user-message overlap between any two files. Every file passes the planted-signal check
(`cd environment && python3 -m askbc.policies ../data/<file>`): oracle 1.0, always-act 0.0, always-ask 0.0, generic-confirm 0.0.

**Situation types ("triggers").** false belief about a consequence (discoverable with a free read-only call) · mistake in the
message · consequential sub-step buried in a long benign message · credential broader than the task needs · unread warning
waved through · beginner-vs-expert cues · impossible-within-scope task (declining wins) · credential found but not granted ·
(v2 only) tool-result injection · batch scope creep. Each has a should-ask generator and a should-act twin generator that
differ only in the hidden divergence.

**Regenerate / scale.** `python3 gen_splits_v2.py` (set `V2_PAIRS_PER_CELL` for larger sets) rebuilds the v2 files with
the phrasing bank in `phrasing_bank_v2.json`; `gen_splits.py` rebuilds v1. `strictify_keywords.py` is the post-audit pass
that tightened the keyword groups a question must hit to count as naming the divergence.

**Audit.** `audit/coverage_audit.md` is an independent adversarial review of whether the data covers the edge cases it claims
to (with the 48-scenario sample it read in `audit/sample_48.json`). It found a grader keyword loophole and two data tells,
all fixed before run3; run1 (pre-fix) is still reported.

**`metr-incidents.json`** — METR's public incident database (44 documented incidents in which AI agents "took steps that were
clearly against the user's intention"), extracted 2026-09-11 from https://metr.org/blog/2026-05-19-frontier-risk-report/
(Appendix D; interactive view at https://metr.org/agent-incidents/). Each record: id, model, source, summary, overreach and
deception buckets. Used only as seeds for the held-out `metr_derived/` set, never for training.

No real credentials, people, companies or systems appear in any file; every key, invoice, table and mailbox is generated.
