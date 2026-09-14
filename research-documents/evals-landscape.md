# Evals — evidence of the flaw, what we hold out, what we reuse
Compiled 2026-09-11. **[VERIFIED]** = page fetched, URL given, numbers quoted · **[CAVEATED]** = not confirmed against the primary.

## 1. The gap in one paragraph
Under-asking is documented, but always as a by-product of harm/misuse benchmarks. Nothing scores the case we target: a **benign,
authorised user whose literal request diverges from evident intent while the agent holds a live destructive credential**.
AgentHarm, Agent-SafetyBench, OS-Harm, AgentDojo all presuppose a malicious user or environment. We must build that data ourselves.

## 2. Evidence that models act when they should ask (all VERIFIED)
| Benchmark | What it shows | Number | Link |
|---|---|---|---|
| BLIND-ACT (arXiv 2510.01670, Oct 2025, CC-BY-4.0) | "blind goal-directedness … regardless of feasibility, safety, reliability, or context"; named pattern "assumptions and decisions under ambiguity" | **80.8 %** avg across 9 frontier CUAs (90 OSWorld tasks) | https://arxiv.org/abs/2510.01670 |
| AgentAbstain (arXiv 2607.10059, Jul 2026, CC-BY-4.0 data / MIT code) | 263 **paired** should-act/should-abstain tasks, 42 executable sandboxes, tools tagged lookup/verify/commit | best of 17 models **59.5 %** paired (Gemini 3.1 Pro), GPT-4o 33.0 %; on should-abstain: **19.7 %** no abstention, **17.8 %** silent abstention, **2.6 %** act-then-refuse | https://arxiv.org/abs/2607.10059 · https://huggingface.co/datasets/antiquality/agentabstain |
| Agent-SafetyBench (arXiv 2412.14470, MIT) | 2,000 cases, 16 agents; "lack of risk awareness"; defensive prompting insufficient | no agent > **60 %**; failure mode "ignores implicit risks, incorrectly calls tools" 48 % | https://arxiv.org/abs/2412.14470 |
| LPS-Bench (arXiv 2602.03255, Feb 2026, MIT) | benign ambiguity-induced risks vs adversarial ones | best model **5.88 %** safe on ambiguity-induced (CAVEATED cell); Claude-4.5-Sonnet 58.6 % benign vs 95.8 % adversarial | https://arxiv.org/abs/2602.03255 |
| UnderSpecBench (arXiv 2607.02294, Jul 2026) | DevOps prompts varied by intent clarity × target certainty × blast radius | **55.8–67.8 %** of runs violate a boundary; "blast-radius cues barely reduce action propensity" | https://arxiv.org/abs/2607.02294 |
| SteerBench-Work (arXiv 2608.12654, Aug 2026, CC-BY-4.0) | the pre-commit "proceed or hold" decision, 106 scenarios ~50/50 | **false-hold 28.1 %** vs **false-allow 1.0 %** → over-holding is the larger error | https://arxiv.org/abs/2608.12654 |
| ToolEmu (arXiv 2309.15817, Apache-2.0) | 144 cases, 36 high-stakes toolkits, LM-emulated | safest agent fails **23.9 %** | https://arxiv.org/abs/2309.15817 |
| τ-bench (arXiv 2406.12045) | policy/confirmation compliance | pass^8 < 25 % retail | https://arxiv.org/abs/2406.12045 |

## 3. Held-out tests (never train on these)
- **AgentAbstain** — construct-identical, paired; judge is an OpenAI-compatible endpoint set in `eval/configs/default.yaml`
  (VERIFIED from README) → local vLLM judge works, no external key. Agent harness: OpenAI SDK pointed at local vLLM.
- **SteerBench-Work** — 106 binary gate decisions, programmatic scoring, runner MIT.
- **METR incident DB** — 45 real incidents (`data/metr-incidents.json`), re-cast as scenarios by Claude subagents.
- **Our cross-domain pairs** — files / email / cloud / git (train only on payments, purchase history, transactional DB).

## 4. Over-asking canary — BFCL (Berkeley Function Calling Leaderboard) [VERIFIED]
Irrelevance (875 cases, gold = no call) · Relevance (41, gold = call) · Missing Parameters (200, gold = ask a follow-up).
AST/programmatic scoring, `pip install bfcl-eval`, runs locally against vLLM. Two-sided trap: over-asking tanks relevance,
over-acting tanks irrelevance. Run every checkpoint. https://gorilla.cs.berkeley.edu/leaderboard.html
Metric to copy for the ask term: HiL-Bench Ask-F1 = harmonic mean of question precision and blocker recall (arXiv 2604.09408).
Cost reference: info-gain clarification on τ-Bench gives +3.7 % success for +0.3 interaction steps (arXiv 2606.03135, ICML 2026).

## 5. Reusable for training data (open, not construct-identical)
ToolEmu tool schemas (Apache-2.0) · Agent-SafetyBench environments (MIT) · AskToAct's trick: remove key parameters from a query
while keeping them as ground truth → programmatic "missing slot" divergence (arXiv 2503.01940).

## 6. Design rules extracted
1. Pair every scenario (always-ask and always-act cap at 50 %).
2. Score the action: commit-before-confirm = fail; act-then-ask = fail; silent non-action = fail.
3. Gate on reversibility (only `commit`-class calls may trigger a question); read-only calls never ask.
4. Penalise over-asking as hard as under-asking (SteerBench-Work 28:1).
5. Randomise where in the episode the risky request appears (cold-start effect: safety improves 9–52 % from turn 0 to 20, arXiv 2606.07867).
6. Decompose the ask reward into task relevance + user answerability (CLARITI, arXiv 2604.14624: same resolution as GPT-5 with 41 % fewer questions).
7. Fallback if scalar GRPO reward collapses: pairwise trajectory preferences (MOSAIC, arXiv 2603.03205, ICML 2026, Qwen3-4B).

## Corrections recorded
ToolEmu does not show a helpfulness drop from safety prompting; "selective quitting" (arXiv 2510.16492) hides a 27 % helpfulness
drop for GPT-4o and does not measure over-quitting; PARTNR and "IntentGuard" are unrelated to ask-vs-act.
