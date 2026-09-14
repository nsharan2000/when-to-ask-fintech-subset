"""TRL GRPOTrainer `environment_factory` adapter.

One environment class per domain (dict factory form). Each class exposes the domain's tools as methods whose
signatures/docstrings match the OpenAI schemas in domains.tool_schemas (TRL renders them via transformers'
get_json_schema), a `reset(**row)` that builds an Episode from the dataset row's `scenario` JSON column, and a
`get_reward()` that returns the programmatic reward. Grades are appended to ASKBC_GRADE_LOG (JSONL) for curves.
"""
from __future__ import annotations
import json, os, threading, time
from ..episode import Episode
from ..domains import tool_schemas, ALL_DOMAINS

_JSON2PY = {"string": "str", "number": "float", "integer": "int", "boolean": "bool"}
_LOCK = threading.Lock()

def _method_source(schema: dict) -> str:
    f = schema["function"]; props = f["parameters"]["properties"]; req = set(f["parameters"].get("required", []))
    params, doc_args = [], []
    for name, p in sorted(props.items(), key=lambda kv: kv[0] not in req):   # required params first
        ty = _JSON2PY.get(p.get("type", "string"), "str")
        if name in req:
            params.append(f"{name}: {ty}")
        else:
            params.append(f"{name}: {ty} = {'0.0' if ty == 'float' else '\"\"'}")
        doc_args.append(f"        {name}: {p.get('description', name)}")
    body = ", ".join(f'"{n}": {n}' for n in props)
    return (f"def {f['name']}(self, {', '.join(params)}) -> str:\n"
            f'    """{f["description"]}\n\n    Args:\n' + "\n".join(doc_args) + '\n\n    Returns:\n        The tool result.\n    """\n'
            f"    return self._step('{f['name']}', {{{body}}})\n")

class _AskBCEnvBase:
    def __init__(self):
        self.ep: Episode | None = None
        self.grade_log = os.environ.get("ASKBC_GRADE_LOG")

    def reset(self, **kwargs):
        scn = kwargs.get("scenario")
        if isinstance(scn, str):
            scn = json.loads(scn)
        self.ep = Episode(scn)
        return None

    def _step(self, name: str, args: dict) -> str:
        if self.ep is None:
            return "ERROR: environment not reset"
        args = {k: v for k, v in args.items() if v not in ("", None)}
        return self.ep.step(name, args)["result"]

    def get_reward(self) -> float:
        if self.ep is not None and not self.ep.finished and not self.ep.done:
            # generation ended without a finish call (model stopped or hit the tool-iteration cap): score it as ended
            self.ep.trajectory.append({"tool": "__text_only__", "args": {}, "raw": "", "result": "", "cls": "invalid", "meta": {}})
        g = self.ep.grade() if self.ep else {"reward": -3.0, "label": "no_episode"}
        if self.grade_log:
            with _LOCK, open(self.grade_log, "a") as fh:
                g2 = {k: g.get(k) for k in ("id", "domain", "trigger", "should_ask", "label", "success", "harm", "n_asks", "n_named", "n_commits", "steps", "reward")}
                g2["t"] = time.time()
                fh.write(json.dumps(g2) + "\n")
        return float(g["reward"])

def make_env_class(domain: str):
    ns = {}
    src = "\n".join(_method_source(s) for s in tool_schemas(domain))
    exec(src, ns)
    methods = {k: v for k, v in ns.items() if callable(v) and not k.startswith("_")}
    return type(f"AskBC_{domain}", (_AskBCEnvBase,), methods)

ENV_CLASSES = {d: make_env_class(d) for d in ALL_DOMAINS}
ENV_FACTORIES = {d: (lambda d=d: ENV_CLASSES[d]()) for d in ALL_DOMAINS}

def dataset_rows(scenarios: list[dict]) -> list[dict]:
    """rows for GRPOTrainer: prompt (chat), environment (domain), scenario (JSON)"""
    return [{"prompt": [{"role": "system", "content": s["system_prompt"]}, {"role": "user", "content": s["user_message"]}],
             "environment": s["domain"], "scenario": json.dumps(s, ensure_ascii=False)} for s in scenarios]
