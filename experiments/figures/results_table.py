"""Print the headline results as Markdown tables from report_data.json (for README/report; never retype numbers)."""
import json, os
d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "report_data.json")))
pct = lambda v: "—" if v is None else f"{100*v:.0f} %"
NICE = {"claude-haiku":"Claude Haiku 4.5 (Claude Code)","claude-sonnet":"Claude Sonnet 5 (Claude Code)","claude-opus":"Claude Opus 5 (Claude Code)","claude-fable":"Claude Fable 5.1 (Claude Code)",
        "qwen3-4b-instruct-2507":"Qwen3-4B-Instruct-2507 (base)","qwen3-4b-thinking":"Qwen3-4B thinking","qwen3-8b":"Qwen3-8B","llama-3.1-8b-instruct":"Llama-3.1-8B-Instruct","mistral-7b-instruct-v0.3":"Mistral-7B-Instruct-v0.3"}
nice = lambda m: NICE.get(m, m.replace("trained-", "Qwen3-4B-Instruct after ").replace("ck", " step ").replace("run1", "run1 (final, step 300)") if m == "trained-run1" else NICE.get(m, m.replace("trained-", "Qwen3-4B-Instruct after ").replace("ck", " step ")))
print("## Probe: 48 twin pairs / 96 episodes, 8 triggers × 7 domains (identical for every model)\n")
print("| Model | Both twins right | Tricky twin handled | Dangerous action | Silent | Act-side ok | Needless questions |\n|---|---|---|---|---|---|---|")
HIDE = {"trained-ck100", "trained-ck200", "trained-run1"}  # earlier evaluation pass (old keyword lists); not comparable with the final pass
order = sorted([m for m in d["models"] if m not in HIDE], key=lambda m: (0 if m.startswith("claude") else 2 if m.startswith("trained") else 1, -(d["models"][m]["overall"]["paired_acc"] or 0)))
for m in order:
    o = d["models"][m]["overall"]
    print(f"| {nice(m)} | **{pct(o['paired_acc'])}** | {pct(o['ask_side_success'])} | {pct(o['harm_rate'])} | {pct(o['silent_rate'])} | {pct(o['act_side_success'])} | {pct(o['over_ask_rate'])} |")
print("\n_Three run-1 checkpoints measured only in the earlier pass (old keyword lists) are omitted; the keyword groups were tightened after the data audit._")
print("\n## Before / after (base Qwen3-4B-Instruct-2507 vs trained checkpoints)\n")
for suite, s in d["evals"].items():
    print(f"**{suite}**\n")
    for r in sorted(s["rows"], key=lambda r: (r["tag"] != "base", r["tag"])):
        print(f"- {r['model']}: **{r['score']}** — {r.get('note','')}")
    print()
print(f"_Built {d['built_at']} from experiments/figures/report_data.json._")
