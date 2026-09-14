## Probe: 48 twin pairs / 96 episodes, 8 triggers × 7 domains (identical for every model)

| Model | Both twins right | Tricky twin handled | Dangerous action | Silent | Act-side ok | Needless questions |
|---|---|---|---|---|---|---|
| Claude Opus 5 (Claude Code) | **58 %** | 95 % | 4 % | 2 % | 56 % | 44 % |
| Claude Fable 5.1 (Claude Code) | **48 %** | 87 % | 5 % | 0 % | 56 % | 44 % |
| Claude Sonnet 5 (Claude Code) | **38 %** | 75 % | 4 % | 11 % | 54 % | 46 % |
| Claude Haiku 4.5 (Claude Code) | **19 %** | 73 % | 9 % | 16 % | 20 % | 80 % |
| Qwen3-8B | **29 %** | 58 % | 33 % | 9 % | 59 % | 34 % |
| Qwen3-4B-Instruct-2507 (base) | **27 %** | 44 % | 24 % | 33 % | 61 % | 32 % |
| Qwen3-4B thinking | **15 %** | 31 % | 36 % | 33 % | 49 % | 41 % |
| Llama-3.1-8B-Instruct | **4 %** | 20 % | 49 % | 31 % | 27 % | 51 % |
| Mistral-7B-Instruct-v0.3 | **0 %** | 11 % | 4 % | 80 % | 2 % | 15 % |
| Qwen3-4B-Instruct after run3 step 300 | **52 %** | 69 % | 16 % | 15 % | 71 % | 24 % |
| Qwen3-4B-Instruct after run3 step 200 | **44 %** | 62 % | 20 % | 18 % | 59 % | 37 % |
| Qwen3-4B-Instruct after run3 step 250 | **44 %** | 55 % | 24 % | 22 % | 76 % | 20 % |
| Qwen3-4B-Instruct after run1 step 200 | **40 %** | 65 % | 20 % | 15 % | 56 % | 37 % |
| Qwen3-4B-Instruct after run1 step 150 | **38 %** | 60 % | 24 % | 16 % | 56 % | 39 % |
| Qwen3-4B-Instruct after run3 step 150 | **33 %** | 64 % | 20 % | 16 % | 44 % | 51 % |

_Three run-1 checkpoints measured only in the earlier pass (old keyword lists) are omitted; the keyword groups were tightened after the data audit._

## Before / after (base Qwen3-4B-Instruct-2507 vs trained checkpoints)

**Fresh twin pairs, training settings (176 episodes)**

- Qwen3-4B-Instruct (before): **31 % both twins right** — handled tricky twin 46 % · dangerous action 22 % · asked needlessly 24 % · silent 32 %
- after run1, step 150: **47 % both twins right** — handled tricky twin 61 % · dangerous action 19 % · asked needlessly 28 % · silent 20 %
- after run1, step 200: **45 % both twins right** — handled tricky twin 64 % · dangerous action 17 % · asked needlessly 36 % · silent 19 %
- after run3, step 150: **42 % both twins right** — handled tricky twin 61 % · dangerous action 19 % · asked needlessly 46 % · silent 20 %
- after run3, step 200: **49 % both twins right** — handled tricky twin 63 % · dangerous action 17 % · asked needlessly 29 % · silent 20 %
- after run3, step 250: **49 % both twins right** — handled tricky twin 58 % · dangerous action 17 % · asked needlessly 12 % · silent 25 %
- after run3, step 300: **50 % both twins right** — handled tricky twin 63 % · dangerous action 20 % · asked needlessly 26 % · silent 17 %

**Never-trained settings: files, email, cloud, git (260 episodes)**

- Qwen3-4B-Instruct (before): **21 % both twins right** — handled tricky twin 42 % · dangerous action 19 % · asked needlessly 42 % · silent 39 %
- after run1, step 150: **29 % both twins right** — handled tricky twin 59 % · dangerous action 20 % · asked needlessly 50 % · silent 21 %
- after run1, step 200: **25 % both twins right** — handled tricky twin 57 % · dangerous action 19 % · asked needlessly 55 % · silent 24 %
- after run3, step 150: **20 % both twins right** — handled tricky twin 57 % · dangerous action 17 % · asked needlessly 67 % · silent 26 %
- after run3, step 200: **32 % both twins right** — handled tricky twin 53 % · dangerous action 21 % · asked needlessly 43 % · silent 25 %
- after run3, step 250: **35 % both twins right** — handled tricky twin 47 % · dangerous action 25 % · asked needlessly 27 % · silent 28 %
- after run3, step 300: **36 % both twins right** — handled tricky twin 55 % · dangerous action 21 % · asked needlessly 37 % · silent 23 %

**Real-incident-derived twin pairs (held out, METR database)**

- Qwen3-4B-Instruct (before): **30 % both twins right** — handled tricky twin 38 % · dangerous action 24 % · asked needlessly 37 % · silent 38 %
- after run1, step 150: **55 % both twins right** — handled tricky twin 71 % · dangerous action 14 % · asked needlessly 26 % · silent 14 %
- after run1, step 200: **55 % both twins right** — handled tricky twin 76 % · dangerous action 14 % · asked needlessly 32 % · silent 10 %
- after run3, step 150: **20 % both twins right** — handled tricky twin 67 % · dangerous action 10 % · asked needlessly 63 % · silent 24 %
- after run3, step 200: **55 % both twins right** — handled tricky twin 67 % · dangerous action 10 % · asked needlessly 16 % · silent 24 %
- after run3, step 250: **60 % both twins right** — handled tricky twin 67 % · dangerous action 14 % · asked needlessly 11 % · silent 19 %
- after run3, step 300: **55 % both twins right** — handled tricky twin 67 % · dangerous action 10 % · asked needlessly 16 % · silent 24 %

**Fresh twin pairs, v2 data: 10 situation types incl. tool-injection and batch scope (208 episodes)**

- Qwen3-4B-Instruct (before): **21 % both twins right** — handled tricky twin 34 % · dangerous action 19 % · asked needlessly 28 % · silent 47 %
- after run1, step 200: **33 % both twins right** — handled tricky twin 48 % · dangerous action 19 % · asked needlessly 33 % · silent 32 %
- after run3, step 150: **23 % both twins right** — handled tricky twin 47 % · dangerous action 21 % · asked needlessly 52 % · silent 32 %
- after run3, step 200: **32 % both twins right** — handled tricky twin 43 % · dangerous action 24 % · asked needlessly 25 % · silent 32 %
- after run3, step 250: **39 % both twins right** — handled tricky twin 46 % · dangerous action 21 % · asked needlessly 18 % · silent 33 %
- after run3, step 300: **36 % both twins right** — handled tricky twin 49 % · dangerous action 19 % · asked needlessly 24 % · silent 31 %

**Never-trained settings, v2 data: 10 situation types (300 episodes)**

- Qwen3-4B-Instruct (before): **20 % both twins right** — handled tricky twin 38 % · dangerous action 23 % · asked needlessly 37 % · silent 39 %
- after run1, step 200: **23 % both twins right** — handled tricky twin 51 % · dangerous action 21 % · asked needlessly 55 % · silent 28 %
- after run3, step 150: **13 % both twins right** — handled tricky twin 51 % · dangerous action 22 % · asked needlessly 65 % · silent 28 %
- after run3, step 200: **24 % both twins right** — handled tricky twin 48 % · dangerous action 24 % · asked needlessly 51 % · silent 28 %
- after run3, step 250: **28 % both twins right** — handled tricky twin 41 % · dangerous action 27 % · asked needlessly 28 % · silent 32 %
- after run3, step 300: **25 % both twins right** — handled tricky twin 47 % · dangerous action 24 % · asked needlessly 46 % · silent 29 %

**General ability: instruction following (IFEval, 250 prompts)**

- Qwen3-4B-Instruct (before): **80.8 %** — prompt-level strict accuracy; higher is better
- after run1, step 300 (final; earlier pass): **81.6 %** — prompt-level strict accuracy; higher is better
- after run3, step 300: **80.4 %** — prompt-level strict accuracy; higher is better

**General ability: grade-school maths (GSM8K, 250 problems)**

- Qwen3-4B-Instruct (before): **78.4 %** — exact match; higher is better
- after run1, step 300 (final; earlier pass): **79.6 %** — exact match; higher is better
- after run3, step 300: **78.8 %** — exact match; higher is better

_Built 2026-09-13 21:56 PDT from experiments/figures/report_data.json._
