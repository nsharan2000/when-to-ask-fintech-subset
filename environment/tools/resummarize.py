"""Re-grade saved open-arm runs with the CURRENT grader and rewrite grades.jsonl + summary.json.  python3 resummarize.py <run_dir>"""
import glob, json, os, sys, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from askbc.episode import Episode, pair_metrics
run_dir = sys.argv[1]; grades = []
for p in sorted(glob.glob(os.path.join(run_dir, "runs", "*.json"))):
    d = json.load(open(p)); ep = Episode.from_json(d["episode"]); g = ep.grade()
    g.update({k: d["grade"][k] for k in ("model", "seconds", "rep") if k in d["grade"]}); d["grade"] = g
    json.dump(d, open(p, "w"), ensure_ascii=False); grades.append(g)
with open(os.path.join(run_dir, "grades.jsonl"), "w") as f:
    for g in grades: f.write(json.dumps(g) + "\n")
tag = grades[0]["model"] if grades else os.path.basename(run_dir)
summary = {"model": tag, "n": len(grades), "overall": pair_metrics(grades), "labels": dict(collections.Counter(g["label"] for g in grades))}
for key in ("trigger", "domain", "split"):
    summary[f"by_{key}"] = {v: pair_metrics([g for g in grades if g[key] == v]) for v in sorted({g[key] for g in grades})}
json.dump(summary, open(os.path.join(run_dir, "summary.json"), "w"), indent=1)
print(tag, summary["overall"], summary["labels"])
