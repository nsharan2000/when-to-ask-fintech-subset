"""CLI driver so an LLM agent that can only run shell commands (e.g. a Claude Code subagent) can play an episode.

  python3 -m askbc.cli start  --scenarios FILE --id ID --run DIR     → prints the briefing (system prompt, tools, user message)
  python3 -m askbc.cli call   --run DIR TOOL '{"json": "args"}'      → executes a tool, prints the result
  python3 -m askbc.cli ask    --run DIR "question"                    → asks the user, prints their reply
  python3 -m askbc.cli finish --run DIR "summary"                     → ends the episode
  python3 -m askbc.cli grade  --run DIR                               → prints the grade (hidden from the agent by convention)
State lives in DIR/episode.json. The briefing never reveals hidden fields.
"""
from __future__ import annotations
import argparse, json, os, sys
from .episode import Episode
from .scenarios import load_jsonl

CLI = os.environ.get("ASKBC_CLI", "python3 -m askbc.cli")

def _load(run: str) -> Episode:
    with open(os.path.join(run, "episode.json")) as f:
        return Episode.from_json(json.load(f))

def _save(run: str, ep: Episode):
    os.makedirs(run, exist_ok=True)
    with open(os.path.join(run, "episode.json"), "w") as f:
        json.dump(ep.to_json(), f, ensure_ascii=False, indent=1)

def _briefing(ep: Episode, run: str) -> str:
    s = ep.s
    tools = []
    for t in s["tools"]:
        f = t["function"]; props = f["parameters"]["properties"]
        sig = ", ".join(f"{k}: {v.get('type','string')}" + ("" if k in f["parameters"].get("required", []) else "?") for k, v in props.items())
        tools.append(f"  - {f['name']}({sig})\n      {f['description']}")
    return ("=== SYSTEM PROMPT ===\n" + s["system_prompt"] +
            "\n\n=== TOOLS (call each with: " + CLI + " call --run " + run + " <tool> '<json args>') ===\n" + "\n".join(tools) +
            "\n  (ask_user and finish have shortcuts: " + CLI + " ask --run " + run + " 'question' · " + CLI + " finish --run " + run + " 'summary')" +
            "\n  SHELL NOTE: wrap every argument in SINGLE quotes ('...'), never double quotes — a dollar sign inside double quotes is eaten by the shell." +
            "\n\n=== USER MESSAGE ===\n" + s["user_message"] + "\n")

def main(argv=None):
    ap = argparse.ArgumentParser(prog="askbc.cli")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("start"); a.add_argument("--scenarios", required=True); a.add_argument("--id", required=True); a.add_argument("--run", required=True)
    a = sub.add_parser("call"); a.add_argument("--run", required=True); a.add_argument("tool"); a.add_argument("args", nargs="?", default="{}")
    a = sub.add_parser("ask"); a.add_argument("--run", required=True); a.add_argument("question")
    a = sub.add_parser("finish"); a.add_argument("--run", required=True); a.add_argument("summary")
    a = sub.add_parser("grade"); a.add_argument("--run", required=True)
    a = sub.add_parser("briefing"); a.add_argument("--run", required=True)
    ns = ap.parse_args(argv)

    if ns.cmd == "start":
        scn = next((r for r in load_jsonl(ns.scenarios) if r["id"] == ns.id), None)
        if scn is None:
            print(f"ERROR: scenario {ns.id} not found", file=sys.stderr); sys.exit(2)
        ep = Episode(scn); _save(ns.run, ep); print(_briefing(ep, ns.run)); return
    ep = _load(ns.run)
    if ns.cmd == "briefing":
        print(_briefing(ep, ns.run)); return
    if ns.cmd == "grade":
        print(json.dumps(ep.grade(), indent=1)); return
    if ns.cmd == "call":
        try:
            args = json.loads(ns.args) if ns.args.strip() else {}
        except json.JSONDecodeError as e:
            print(f"ERROR: args must be a JSON object ({e})"); return
        r = ep.step(ns.tool, args)
    elif ns.cmd == "ask":
        r = ep.step("ask_user", {"question": ns.question})
    else:
        r = ep.step("finish", {"summary": ns.summary})
    _save(ns.run, ep)
    print(r["result"])
    if r["done"] and ns.cmd != "finish":
        print("(episode over: step budget exhausted)")

if __name__ == "__main__":
    main()
