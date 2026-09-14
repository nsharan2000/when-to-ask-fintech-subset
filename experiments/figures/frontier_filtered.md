# Probe results restricted by what the frontier models got right

Pairs are counted only if both twins were run without a harness error. 'Frontier' = Claude Opus 5 and Claude Fable 5.1 (through Claude Code).

## all 48 pairs (n = 48 pairs)

| model | both twins right | tricky twin handled | dangerous action | needless questions |
|---|---|---|---|---|
| Claude Opus 5 | **58 %** | 95 % | 4 % | 37 % |
| Claude Fable 5.1 | **48 %** | 87 % | 5 % | 29 % |
| Claude Sonnet 5 | **38 %** | 75 % | 4 % | 41 % |
| Claude Haiku 4.5 | **19 %** | 73 % | 9 % | 71 % |
| Qwen3-8B | **30 %** | 60 % | 32 % | 31 % |
| Qwen3-4B-Instruct (base, before training) | **27 %** | 44 % | 24 % | 32 % |
| Qwen3-4B thinking | **15 %** | 33 % | 38 % | 35 % |
| Llama 3.1 8B | **4 %** | 20 % | 49 % | 44 % |
| Mistral 7B v0.3 | **0 %** | 11 % | 2 % | 3 % |
| Qwen3-4B-Instruct after training (run3 step 300, selected) | **52 %** | 69 % | 16 % | 24 % |
| Qwen3-4B-Instruct after training (run3 step 250) | **44 %** | 55 % | 24 % | 20 % |
| Qwen3-4B-Instruct after training (run1 step 200) | **40 %** | 65 % | 20 % | 37 % |

## pairs Opus AND Fable both got right (n = 20 pairs)

| model | both twins right | tricky twin handled | dangerous action | needless questions |
|---|---|---|---|---|
| Claude Opus 5 | **100 %** | 100 % | 0 % | 0 % |
| Claude Fable 5.1 | **100 %** | 100 % | 0 % | 0 % |
| Claude Sonnet 5 | **75 %** | 90 % | 0 % | 15 % |
| Claude Haiku 4.5 | **20 %** | 75 % | 0 % | 75 % |
| Qwen3-8B | **50 %** | 65 % | 25 % | 15 % |
| Qwen3-4B-Instruct (base, before training) | **45 %** | 55 % | 10 % | 15 % |
| Qwen3-4B thinking | **20 %** | 40 % | 25 % | 25 % |
| Llama 3.1 8B | **5 %** | 35 % | 35 % | 30 % |
| Mistral 7B v0.3 | **0 %** | 11 % | 0 % | 5 % |
| Qwen3-4B-Instruct after training (run3 step 300, selected) | **70 %** | 75 % | 5 % | 5 % |
| Qwen3-4B-Instruct after training (run3 step 250) | **65 %** | 70 % | 10 % | 5 % |
| Qwen3-4B-Instruct after training (run1 step 200) | **60 %** | 75 % | 0 % | 20 % |

## pairs Opus OR Fable got wrong (n = 28 pairs)

| model | both twins right | tricky twin handled | dangerous action | needless questions |
|---|---|---|---|---|
| Claude Opus 5 | **29 %** | 91 % | 6 % | 71 % |
| Claude Fable 5.1 | **11 %** | 80 % | 9 % | 57 % |
| Claude Sonnet 5 | **11 %** | 66 % | 6 % | 67 % |
| Claude Haiku 4.5 | **18 %** | 71 % | 14 % | 67 % |
| Qwen3-8B | **15 %** | 58 % | 36 % | 47 % |
| Qwen3-4B-Instruct (base, before training) | **14 %** | 37 % | 31 % | 48 % |
| Qwen3-4B thinking | **12 %** | 28 % | 47 % | 45 % |
| Llama 3.1 8B | **4 %** | 11 % | 57 % | 57 % |
| Mistral 7B v0.3 | **0 %** | 12 % | 3 % | 0 % |
| Qwen3-4B-Instruct after training (run3 step 300, selected) | **39 %** | 66 % | 23 % | 43 % |
| Qwen3-4B-Instruct after training (run3 step 250) | **29 %** | 46 % | 31 % | 33 % |
| Qwen3-4B-Instruct after training (run1 step 200) | **25 %** | 60 % | 31 % | 52 % |
