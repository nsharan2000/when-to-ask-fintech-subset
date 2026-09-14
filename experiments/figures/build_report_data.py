"""Collect every result file into one JSON for the visual guide. Run from repo root:
   python3 experiments/figures/build_report_data.py  →  experiments/figures/report_data.json
Sources: experiments/probe-claude/summary_<model>.json + grades; experiments/probe-open/<tag>/summary.json + grades.jsonl;
         experiments/grpo/<run>/episode_grades.jsonl (training curves); experiments/evals/**/summary.json (post-training).
Never retype numbers: the artifact embeds this file.
"""
import glob, json, os, collections, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
out = {"models": {}, "examples": {}, "training": {}, "evals": {}}

def load_jsonl(p):
    return [json.loads(l) for l in open(p) if l.strip()]

# --- probe: Claude arm
for p in sorted(glob.glob(os.path.join(ROOT, "experiments/probe-claude/summary_*.json"))):
    s = json.load(open(p)); m = s["model"]
    out["models"][f"claude-{m}"] = {"arm": "claude-code", "n": s["n"], "overall": s["overall"], "labels": s["labels"],
                                    "by_trigger": s["by_trigger"], "by_domain": s["by_domain"]}
# --- probe: open-weight arm (+ trained checkpoints evaluated with the same driver)
for p in sorted(glob.glob(os.path.join(ROOT, "experiments/probe-open/*/summary.json"))):
    s = json.load(open(p)); tag = s["model"]
    out["models"][tag] = {"arm": "vllm", "n": s["n"], "overall": s["overall"], "labels": s["labels"],
                          "by_trigger": s["by_trigger"], "by_domain": s["by_domain"]}
# --- example transcripts for the "here's the problem" section (harmful episodes, one per label)
ex = {}
for p in glob.glob(os.path.join(ROOT, "experiments/probe-claude/runs/*/*/episode.json")) + glob.glob(os.path.join(ROOT, "experiments/probe-open/*/runs/*.json")):
    d = json.load(open(p))
    ep = d.get("episode", d); scn = ep["scenario"]
    model = ("claude-" + p.split("/runs/")[1].split("/")[0]) if "/probe-claude/" in p else p.split("/runs/")[0].split("/")[-1]
    g = d.get("grade")
    if g is None:
        import sys; sys.path.insert(0, os.path.join(ROOT, "environment"))
        from askbc.episode import Episode
        g = Episode.from_json(ep).grade()
    if g["label"] in ("commit_before_confirm", "objection_collapse", "uninformed_commit", "act_then_ask", "commit_after_abort", "named_ask_hold", "over_ask", "silent"):
        key = g["label"]
        ex.setdefault(key, [])
        if len(ex[key]) < 8:
            from askbc.domains import Backend, record_name, DOMAINS
            h = scn["hidden"]; be = Backend(scn["domain"], scn["world"])
            tgt = be._rec(h["literal"]["target"])
            fact = be._fmt(tgt) if tgt else f"{DOMAINS[scn['domain']]['record_kind']} '{h['literal']['target']}' does not exist"
            near = [record_name(scn["domain"], r) for r in scn["world"]["records"]]
            ex[key].append({"model": model, "id": scn["id"], "trigger": scn["trigger"], "domain": scn["domain"], "should_ask": scn["should_ask"],
                            "user_message": scn["user_message"], "target_fact": fact, "known_records": near,
                            "divergence": h["divergence"], "pushback": (h.get("pushback") or {}).get("first"), "pushback_kind": h.get("pushback_kind"),
                            "granted": [f"{k['id']} ({k['scope']}, {k['env']})" for k in scn["world"]["granted"]],
                            "steps": [{"tool": e["tool"], "args": e["args"], "result": e["result"][:400]} for e in ep["trajectory"]], "reward": g["reward"], "label": g["label"]})
out["examples"] = ex
# --- training curves
for run in sorted(glob.glob(os.path.join(ROOT, "experiments/grpo/*/episode_grades.jsonl"))):
    rows = load_jsonl(run); name = run.split("/")[-2]
    # bucket by 64 episodes (= one generation batch of 8 prompts × 8)
    B = 64; curve = []
    for i in range(0, len(rows), B):
        chunk = rows[i:i + B]; ask = [r for r in chunk if r["should_ask"]]; act = [r for r in chunk if not r["should_ask"]]
        curve.append({"episodes": i + len(chunk), "mean_reward": sum(r["reward"] for r in chunk) / len(chunk),
                      "ask_success": sum(r["success"] for r in ask) / max(1, len(ask)), "harm": sum(r["harm"] for r in ask) / max(1, len(ask)),
                      "act_success": sum(r["success"] for r in act) / max(1, len(act)), "over_ask": sum(r["n_asks"] > 0 for r in act) / max(1, len(act))})
    out["training"][name] = {"n_episodes": len(rows), "curve": curve}
    ts = os.path.join(os.path.dirname(run), "trainer_state.json")
    if os.path.exists(ts):
        lh = [e for e in json.load(open(ts))["log_history"] if "reward" in e]
        out["training"][name]["steps"] = [{"step": e["step"], "reward": e["reward"], "kl": e.get("kl"), "len": e.get("completions/mean_length")} for e in lh]
# --- post-training evals: experiments/evals/<tag>/{test_indist,heldout}/summary.json and <tag>/capability/**/results_*.json
NICE_TAG = {"base": "Qwen3-4B-Instruct (before)", "trained-run1": "after run1, step 300 (final; earlier pass)"}
def nice_tag(tag):
    if tag in NICE_TAG: return NICE_TAG[tag]
    m = re.match(r"trained-(run\d)ck(\d+)", tag)
    return f"after {m.group(1)}, step {m.group(2)}" if m else tag
rows_by_suite = {}
for tag_dir in sorted(glob.glob(os.path.join(ROOT, "experiments/evals/*"))):
    tag = os.path.basename(tag_dir); name = nice_tag(tag)
    if not os.path.isdir(tag_dir): continue
    # trained-run1 (run1 final adapter) was only measured on the twin sets in the earlier pass (old keyword lists, partially
    # invalidated by the stale re-grade) and was not re-run in the final pass; only its general-ability rows are comparable.
    STALE_TWIN_TAGS = {"trained-run1"}
    for split, label in (("test_indist", "Fresh twin pairs, training settings (176 episodes)"), ("heldout", "Never-trained settings: files, email, cloud, git (260 episodes)"), ("metr", "Real-incident-derived twin pairs (held out, METR database)"),
                         ("test_v2", "Fresh twin pairs, v2 data: 10 situation types incl. tool-injection and batch scope (208 episodes)"), ("heldout_v2", "Never-trained settings, v2 data: 10 situation types (300 episodes)")):
        sp = os.path.join(tag_dir, split, "summary.json")
        if os.path.exists(sp) and tag not in STALE_TWIN_TAGS:
            S = json.load(open(sp)); o = S["overall"]
            rows_by_suite.setdefault(label, {"rows": [], "kind": "askbc"})["rows"].append({"model": name, "tag": tag, "score": f"{100*o['paired_acc']:.0f} % both twins right",
                "note": f"handled tricky twin {100*o['ask_side_success']:.0f} % · dangerous action {100*o['harm_rate']:.0f} % · asked needlessly {100*o['over_ask_rate']:.0f} % · silent {100*o['silent_rate']:.0f} %", "overall": o,
                "by_trigger": {k: {"paired_acc": v.get("paired_acc"), "n_pairs": v.get("n_pairs"), "harm_rate": v.get("harm_rate")} for k, v in S.get("by_trigger", {}).items()}})
    for rp in glob.glob(os.path.join(tag_dir, "capability", "**", "results_*.json"), recursive=True):
        res = json.load(open(rp)).get("results", {})
        if "ifeval" in res:
            v = res["ifeval"].get("prompt_level_strict_acc,none"); rows_by_suite.setdefault("General ability: instruction following (IFEval, 250 prompts)", {"rows": [], "kind": "capability"})["rows"].append({"model": name, "tag": tag, "score": f"{100*v:.1f} %", "note": "prompt-level strict accuracy; higher is better", "value": v})
        if "gsm8k" in res:
            v = res["gsm8k"].get("exact_match,flexible-extract", res["gsm8k"].get("exact_match,strict-match")); rows_by_suite.setdefault("General ability: grade-school maths (GSM8K, 250 problems)", {"rows": [], "kind": "capability"})["rows"].append({"model": name, "tag": tag, "score": f"{100*v:.1f} %", "note": "exact match; higher is better", "value": v})
out["evals"] = rows_by_suite
# --- planted-signal self-test (deterministic) + probe scenario examples per trigger
import sys; sys.path.insert(0, os.path.join(ROOT, "environment"))
from askbc.scenarios import generate_pairs, TRIGGERS
from askbc.domains import ALL_DOMAINS
from askbc.policies import run_policy
from askbc.episode import pair_metrics
rows = generate_pairs(ALL_DOMAINS, TRIGGERS, 3, seed=7, split="selftest")
out["selftest"] = {pol: pair_metrics([run_policy(s, pol).grade() for s in rows]) for pol in ("always_act", "always_ask", "generic_ask_then_act", "oracle")}
out["selftest"]["n_scenarios"] = len(rows)
probe = load_jsonl(os.path.join(ROOT, "data/probe/probe.jsonl"))
out["trigger_examples"] = {}
for r in probe:
    if r["should_ask"] and r["trigger"] not in out["trigger_examples"] and r["domain"] in ("payments", "orders", "database"):
        out["trigger_examples"][r["trigger"]] = {"domain": r["domain"], "user_message": r["user_message"], "id": r["id"],
                                                  "twin_message": next(x["user_message"] for x in probe if x["pair_id"] == r["pair_id"] and x["id"] != r["id"])}
out["probe_size"] = {"episodes": len(probe), "pairs": len({r["pair_id"] for r in probe}), "domains": sorted({r["domain"] for r in probe}), "triggers": TRIGGERS}
ffp = os.path.join(ROOT, "experiments/figures/frontier_filtered.json")
if os.path.exists(ffp): out["frontier_filtered"] = json.load(open(ffp))
import datetime; out["built_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M PDT")
json.dump(out, open(os.path.join(ROOT, "experiments/figures/report_data.json"), "w"), indent=1)
print("models:", list(out["models"]), "| examples:", {k: len(v) for k, v in out["examples"].items()}, "| training runs:", list(out["training"]), "| evals:", list(out["evals"]))
