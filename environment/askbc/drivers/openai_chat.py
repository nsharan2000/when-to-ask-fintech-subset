"""Run episodes against any OpenAI-compatible chat endpoint with native tool calling (vLLM, LiteLLM, ...).

  python3 -m askbc.drivers.openai_chat --base-url http://localhost:8001/v1 --model qwen3-4b-instruct \
      --scenarios /workspace/data/probe/probe.jsonl --out /workspace/experiments/probe-open/qwen3-4b-instruct \
      [--ids id1,id2] [--concurrency 8] [--temperature 0.0] [--n 1]

Writes one JSON per episode (full transcript + grade) into --out/runs/, plus grades.jsonl and summary.json.
Resumable: episodes with an existing run file are skipped.
"""
from __future__ import annotations
import argparse, asyncio, json, os, sys, time
from ..episode import Episode, pair_metrics
from ..scenarios import load_jsonl

NO_TOOL_CALL_MSG = ("Please respond with a tool call. If you are done, call finish; if you need the user's input, call ask_user.")

async def run_episode(client, model: str, scn: dict, temperature: float, max_tokens: int, tag: str) -> dict:
    ep = Episode(scn)
    obs = ep.reset()
    n_no_call = 0
    t0 = time.time()
    while not ep.done:
        try:
            resp = await client.chat.completions.create(model=model, messages=ep.messages, tools=obs["tools"], tool_choice="auto",
                                                        temperature=temperature, max_tokens=max_tokens)
        except Exception as e:  # noqa
            ep.trajectory.append({"tool": "__api_error__", "args": {}, "raw": str(e)[:500], "result": "", "cls": "invalid", "meta": {}})
            break
        msg = resp.choices[0].message
        content = msg.content or ""
        calls = msg.tool_calls or []
        if not calls:
            n_no_call += 1
            # a bare text answer: treat a clear question as ask_user? No — score actions only. Nudge once, then end.
            ep.messages.append({"role": "assistant", "content": content})
            if n_no_call >= 2:
                ep.trajectory.append({"tool": "__text_only__", "args": {}, "raw": content, "result": "", "cls": "invalid", "meta": {}})
                break
            ep.messages.append({"role": "user", "content": NO_TOOL_CALL_MSG})
            continue
        # execute the first call only (sequential tools keep grading unambiguous); extra calls are dropped with a note
        call = calls[0]
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {"__unparseable__": call.function.arguments}
        ep.step(call.function.name, args if isinstance(args, dict) else {}, raw=content)
        if len(calls) > 1:
            ep.messages.append({"role": "user", "content": f"(note: only the first of your {len(calls)} tool calls was executed; issue one tool call per turn)"})
    g = ep.grade()
    g["model"] = tag; g["seconds"] = round(time.time() - t0, 1)
    return {"grade": g, "episode": ep.to_json()}

async def main_async(ns):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(base_url=ns.base_url, api_key=ns.api_key)
    rows = load_jsonl(ns.scenarios)
    if ns.ids:
        keep = set(ns.ids.split(",")); rows = [r for r in rows if r["id"] in keep]
    if ns.limit:
        rows = rows[: ns.limit]
    run_dir = os.path.join(ns.out, "runs"); os.makedirs(run_dir, exist_ok=True)
    sem = asyncio.Semaphore(ns.concurrency)
    tag = ns.tag or ns.model

    async def one(scn, rep):
        path = os.path.join(run_dir, f"{scn['id']}_r{rep}.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)["grade"]
        async with sem:
            res = await run_episode(client, ns.model, scn, ns.temperature, ns.max_tokens, tag)
        res["grade"]["rep"] = rep
        with open(path, "w") as f:
            json.dump(res, f, ensure_ascii=False)
        g = res["grade"]
        print(f"[{tag}] {scn['id']:24s} {g['label']:24s} R={g['reward']:+.2f} steps={g['steps']}", flush=True)
        return g

    grades = await asyncio.gather(*[one(s, rep) for s in rows for rep in range(ns.n)])
    with open(os.path.join(ns.out, "grades.jsonl"), "w") as f:
        for g in grades:
            f.write(json.dumps(g) + "\n")
    summary = {"model": tag, "n": len(grades), "overall": pair_metrics(grades)}
    for key in ("trigger", "domain", "split"):
        summary[f"by_{key}"] = {}
        for v in sorted({g[key] for g in grades}):
            summary[f"by_{key}"][v] = pair_metrics([g for g in grades if g[key] == v])
    import collections
    summary["labels"] = dict(collections.Counter(g["label"] for g in grades))
    with open(os.path.join(ns.out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps(summary["overall"], indent=1))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8001/v1"); ap.add_argument("--api-key", default="EMPTY")
    ap.add_argument("--model", required=True); ap.add_argument("--tag", default=None)
    ap.add_argument("--scenarios", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--ids", default=None); ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=8); ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=4096); ap.add_argument("--n", type=int, default=1)
    asyncio.run(main_async(ap.parse_args()))

if __name__ == "__main__":
    main()
