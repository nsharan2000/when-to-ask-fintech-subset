"""v2 splits: phrasing bank + larger worlds (+ any new triggers registered in scenarios.GENERATORS). Run from repo root or /workspace.
  train_v2.jsonl (train domains, seed 21), test_v2.jsonl (train domains, seed 22), heldout_v2.jsonl (held-out domains, seed 23).
Dedupes against v1 eval sets and the probe. Never touches v1 files."""
import sys, os, json, collections
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
sys.path.insert(0, os.path.join(root, "environment"))
from askbc import scenarios as S
from askbc.scenarios import generate_pairs, save_jsonl, load_jsonl, TRIGGERS
from askbc.domains import TRAIN_DOMAINS, HELDOUT_DOMAINS
S.set_bank(os.path.join(here, "phrasing_bank_v2.json"))
triggers = list(S.GENERATORS)   # includes any v2 triggers registered after the audit
n_train = int(os.environ.get("V2_PAIRS_PER_CELL", "45"))
splits = {"train_v2": generate_pairs(TRAIN_DOMAINS, triggers, n_train, seed=21, split="train"),
          "test_v2": generate_pairs(TRAIN_DOMAINS, triggers, 4, seed=22, split="test"),
          "heldout_v2": generate_pairs(HELDOUT_DOMAINS, triggers, 5, seed=23, split="heldout")}
held = set()
for f in ("test_indist.jsonl", "heldout.jsonl", os.path.join("probe", "probe.jsonl")):
    p = os.path.join(here, f)
    if os.path.exists(p): held |= {r["user_message"] for r in load_jsonl(p)}
held |= {r["user_message"] for r in splits["test_v2"]} | {r["user_message"] for r in splits["heldout_v2"]}
bad = {r["pair_id"] for r in splits["train_v2"] if r["user_message"] in held}
splits["train_v2"] = [r for r in splits["train_v2"] if r["pair_id"] not in bad]
print(f"dropped {len(bad)} colliding train pairs; triggers={triggers}")
for name, rows in splits.items():
    save_jsonl(rows, os.path.join(here, f"{name}.jsonl"))
    msgs = [r["user_message"] for r in rows]
    print(f"{name}: {len(rows)} episodes / {len({r['pair_id'] for r in rows})} pairs; unique messages {len(set(msgs))}; triggers={dict(collections.Counter(r['trigger'] for r in rows))}")
