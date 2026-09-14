"""Generate the scenario splits. Run from repo root: python3 data/gen_splits.py
  train.jsonl        train domains (payments, orders, database), all triggers, seed 1  → GRPO prompts
  test_indist.jsonl  train domains, seed 2 (disjoint worlds/ids/phrasings)            → in-distribution paired eval
  heldout.jsonl      held-out domains (files, email, cloud, git), seed 3               → cross-domain generalisation
  probe.jsonl        (separate, seed 20260911, all domains) is the hypothesis-test set used for the Claude + open-model arms
"""
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "environment"))
from askbc.scenarios import generate_pairs, save_jsonl, TRIGGERS
from askbc.domains import TRAIN_DOMAINS, HELDOUT_DOMAINS
here = os.path.dirname(os.path.abspath(__file__))
splits = {
    "train": generate_pairs(TRAIN_DOMAINS, TRIGGERS, 40, seed=1, split="train"),
    "test_indist": generate_pairs(TRAIN_DOMAINS, TRIGGERS, 4, seed=2, split="test"),
    "heldout": generate_pairs(HELDOUT_DOMAINS, TRIGGERS, 5, seed=3, split="heldout"),
}
probe = [json.loads(l) for l in open(os.path.join(here, "probe", "probe.jsonl"))]
held = {r["user_message"] for r in splits["test_indist"]} | {r["user_message"] for r in probe} | {r["user_message"] for r in splits["heldout"]}
bad_pairs = {r["pair_id"] for r in splits["train"] if r["user_message"] in held}
splits["train"] = [r for r in splits["train"] if r["pair_id"] not in bad_pairs]
print(f"dropped {len(bad_pairs)} train pairs whose user message collides with an eval set")
for name, rows in splits.items():
    save_jsonl(rows, os.path.join(here, f"{name}.jsonl"))
    print(f"{name}: {len(rows)} episodes / {len({r['pair_id'] for r in rows})} pairs; triggers={dict(collections.Counter(r['trigger'] for r in rows))}")
# contamination check: exact user-message overlap between train and every other set
train_msgs = {r["user_message"] for r in splits["train"]}
for name, rows in list(splits.items())[1:] + [("probe", probe)]:
    dup = sum(1 for r in rows if r["user_message"] in train_msgs)
    print(f"overlap train↔{name}: {dup}/{len(rows)} identical user messages")
