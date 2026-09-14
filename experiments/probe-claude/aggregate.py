"""Aggregate Claude-arm episode runs (experiments/probe-claude/runs/<model>/<id>/episode.json) into grades + summary.
  python3 aggregate.py [--scenarios ../../data/probe/probe.jsonl] [--models haiku,sonnet,opus]
Also prints which scenario ids are still missing (or unfinished) per model, for the next batch.
"""
import argparse, collections, glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "environment"))
from askbc.episode import Episode, pair_metrics
from askbc.scenarios import load_jsonl
from askbc.user_sim import names_divergence

ap = argparse.ArgumentParser(); ap.add_argument("--scenarios", default=os.path.join(os.path.dirname(__file__), "..", "..", "data", "probe", "probe.jsonl"))
ap.add_argument("--models", default=None); ap.add_argument("--quiet", action="store_true")
ns = ap.parse_args()
SCN = {r["id"]: r for r in load_jsonl(ns.scenarios)}
ids = list(SCN)
models = ns.models.split(",") if ns.models else sorted(os.path.basename(p) for p in glob.glob(os.path.join(os.path.dirname(__file__), "runs", "*")))
out = {}
for m in models:
    grades, missing, unfinished = [], [], []
    for sid in ids:
        p = os.path.join(os.path.dirname(__file__), "runs", m, sid, "episode.json")
        if not os.path.exists(p):
            missing.append(sid); continue
        ep = Episode.from_json(json.load(open(p)))
        # regrade with the CURRENT keyword sets: if a should-ask episode's question is now recognised as naming the
        # divergence but the scripted user replied as if it did not (or vice versa), the episode must be re-run.
        stale = False
        kw = SCN[sid]["hidden"]["keywords"]
        for e in ep.trajectory:
            if e["cls"] == "ask_user":
                new_named = bool(kw) and names_divergence(e["args"].get("question", ""), kw)
                if SCN[sid]["should_ask"] and new_named != bool(e["meta"].get("named")):
                    stale = True
        if stale:
            unfinished.append(sid + " (stale-keywords)"); continue
        g = ep.grade(); g["model"] = m
        if not ep.finished:
            unfinished.append(sid)
        grades.append(g)
    with open(os.path.join(os.path.dirname(__file__), f"grades_{m}.jsonl"), "w") as f:
        for g in grades: f.write(json.dumps(g) + "\n")
    summ = {"model": m, "n": len(grades), "overall": pair_metrics(grades), "labels": dict(collections.Counter(g["label"] for g in grades)),
            "by_trigger": {t: pair_metrics([g for g in grades if g["trigger"] == t]) for t in sorted({g["trigger"] for g in grades})},
            "by_domain": {d: pair_metrics([g for g in grades if g["domain"] == d]) for d in sorted({g["domain"] for g in grades})},
            "missing": missing, "unfinished": unfinished}
    json.dump(summ, open(os.path.join(os.path.dirname(__file__), f"summary_{m}.json"), "w"), indent=1)
    out[m] = summ
    if not ns.quiet:
        o = summ["overall"]
        print(f"== {m}: n={len(grades)} pairs={o['n_pairs']} paired={o['paired_acc']} ask_ok={o['ask_side_success']} harm={o['harm_rate']} act_ok={o['act_side_success']} overask={o['over_ask_rate']} R={o['mean_reward']}")
        print("   labels:", summ["labels"])
        print("   missing:", len(missing), "unfinished:", unfinished)
print(json.dumps({m: s["overall"] for m, s in out.items()}))
