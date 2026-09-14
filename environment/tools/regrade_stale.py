"""Find open-arm run files whose scripted-user reply is stale under the CURRENT probe keywords, delete them (the driver is
resumable and will regenerate them), and print the ids.  python3 regrade_stale.py <run_dir> <scenarios.jsonl>"""
import glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from askbc.user_sim import names_divergence
from askbc.scenarios import load_jsonl
run_dir, scn_path = sys.argv[1], sys.argv[2]
SCN = {r["id"]: r for r in load_jsonl(scn_path)}
stale = []
for p in glob.glob(os.path.join(run_dir, "runs", "*.json")):
    d = json.load(open(p)); ep = d["episode"]; sid = ep["scenario"]["id"]
    kw = SCN[sid]["hidden"]["keywords"]
    for e in ep["trajectory"]:
        if e["cls"] == "ask_user" and SCN[sid]["should_ask"]:
            if (bool(kw) and names_divergence(e["args"].get("question", ""), kw)) != bool(e["meta"].get("named")):
                stale.append(sid); os.remove(p); break
print(json.dumps(sorted(set(stale))))
