# Intent-vs-instruction: the flaw, its mechanism, and the spec lines that condemn it
Compiled 2026-09-11. `[VERIFIED]` = fetched, quoted · `[CAVEAT]` = partial.

## 1. The flaw, stated precisely
> Current LLM agents are optimised for autonomous execution rather than intent verification. When a syntactically clear instruction's
> *evident intent* diverges from its *literal content* — the user holds a false belief about consequences, mistyped, or buried a
> consequential sub-request in a long benign message — the agent executes the literal instruction, even though it is independently
> capable of recognising the divergence. Because the action is often irreversible the cost is asymmetric; because deference is
> reinforced by preference training the gap is maintained rather than merely unaddressed.

## 2. Evidence for each clause (VERIFIED)
| Clause | Source | Quote / number |
|---|---|---|
| Agents are trained to execute, not verify | Ask or Assume? arXiv 2603.26233 (Mar 2026) | "current agents are largely optimized for autonomous execution"; decoupling detection from execution lifts underspecified SWE-bench resolve rate to 69.40 % |
| Recognition exists but doesn't drive action | SimpleToM arXiv 2410.13648 | models "reliably infer mental state (a), but fail at applying knowledge about the mental state" for behaviour prediction/judgement |
| Even pure recognition is weak | R-Judge arXiv 2401.10019 | best model 74.42 %; "no other models significantly exceed the random" |
| Prompting does not fix it | Agent-SafetyBench arXiv 2412.14470 | no agent > 60 %; "reliance on defense prompts alone may be insufficient" |
| Live and regressing at the frontier | GPT-5.6 System Card, 2026-07-09, https://deploymentsafety.openai.com/gpt-5-6 | "a greater tendency than GPT-5.5 to go beyond the user's intent, including by taking or attempting actions that the user had not asked for"; severity-3 example "deleting data from cloud storage without requesting user approval"; mitigation is scaffold-level confirmation policy, not learned intent inference |
| Deference is a trained-in bias | Sharma et al. ICLR 2024 arXiv 2310.13548; Price of Agreement arXiv 2604.24668 (Apr 2026) | preference models "prefer convincingly-written sycophantic responses over correct ones"; in 2026 sycophancy survives via *stated preferences* even where blunt contradiction is defended |

## 3. The spec says it should have asked — OpenAI Model Spec 2026-08-18 (VERIFIED, https://model-spec.openai.com/2026-08-18.html)
- "The assistant should consider not just the literal wording of instructions, but also the underlying intent and context."
- Triggers: "If an instruction seems misaligned or orthogonal to what the assistant otherwise believes to be the user's intent"; "If the
  user may have made a mistake in their message. For example, the user might forget a 'not'…" → "err on the side of asking the user
  for confirmation or clarification before taking any potentially costly actions."
- Buried sub-request: "especially important when it's plausible that the user might not have noticed the instructions (e.g., the
  message is long, and the instructions are embedded inside otherwise innocuous content), or carrying out the instructions could
  cause irreversible side effects. In such cases, the assistant should ask for clarification before proceeding if possible."
- "For actions that go beyond what the request clearly implies, the assistant should seek confirmation before proceeding."
- Informed consent: "clearly outline what information will be sent, who will receive it … This context helps the user provide informed consent."
- **Counter-pressure (must be in the reward):** "avoiding unnecessary or trivial clarifying questions"; narrow scopes "could
  habituate the user to automatically confirming all requests"; "Trivial questions may waste the user's time."
- Push-back: "it may politely push back when asked to do something that … runs counter to the user's best interests as reasonably
  inferred from the context, while remaining respectful of the user's final decisions."
Anthropic's constitution `[CAVEAT]`: text behind HTTP 403; nothing quoted.

## 4. Design takeaways
- **Construct divergence, not ambiguity.** Three generators matching the spec's triggers: false belief about consequence (truth
  discoverable by a read-only call, so "didn't check" is distinguishable from "couldn't know"); mistake in message (dropped "not",
  wrong amount/recipient/table); buried sub-request (vary position and benign-clause count).
- **Score the action, not the statement**; run a separate "does the user understand what X does?" probe to measure the know-vs-act gap.
- **Penalise over-asking as hard as under-asking**; paired scenarios differing only in reversibility force conditioning on consequence.
- **Expertise** = evidence in the transcript (fluency, jargon), never a label. **Attention** = consent validity: a one-token "ok just
  do it" after an unread warning does not discharge the obligation; an assent naming the specific risk does.
- **Encode wrong intent as a confident aside or preference**, not as an argument (that failure mode is already partly fixed).
- **Why RL, not a prompt**: Agent-SafetyBench and Ask-or-Assume both show single-pass prompting is insufficient.
- Missing number we will produce: the rate at which a dangerous sub-request buried among benign ones is executed unnoticed.
