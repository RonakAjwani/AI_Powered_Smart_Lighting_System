# Open-Source LLM Cybersecurity Benchmarks & Performance

## Existing Benchmarks Referenced

| Benchmark | Year | Focus | Key Metric |
|---|---|---|---|
| **CTI-Bench** (RIT) | 2024 | Cyber Threat Intelligence tasks | Knowledge, attribution, severity |
| **SecBench** | Dec 2024 | 9-domain multi-choice cybersecurity | Broad security knowledge |
| **SecEval** | 2024 | ~2100 MCQ cybersecurity assessment | Foundational knowledge |
| **CyberMetric** | 2024 | Actionable metrics | Severity, attribution, response time |
| **CAIBench** | 2024/25 | Docker-based practical agent eval | Offensive + defensive capability |
| **Wiz AI Cyber Arena** | 2024 | Cloud security challenges | Zero-day discovery, CVE detection |

## Key Finding: Theory vs Practice Gap

> CAIBench found LLMs score ~70% on security knowledge questions but drop to **20-40%** in multi-step adversarial scenarios. Our arena tests this exact gap.

## Model Security Analysis (from research)

| Model | Cybersecurity Score | Strengths | Weaknesses |
|---|---|---|---|
| **Llama 3.1 8B** | 94% (cybersec test) | Strong security analysis | Smaller context window |
| **Llama 3.1 70B** | ~96% (estimated) | Best overall accuracy | Higher API cost |
| **Mistral 7B** | Good | European compliance focus | AVI vulnerability (92% ASR) |
| **Mixtral 8x7B** | Good | MoE efficiency | Prompt injection risk |
| **Qwen 2.5/3 32B** | Moderate | Multilingual, strong coding | 82% jailbreak failure rate |
| **DeepSeek-V2** | Low-Moderate | Cost-efficient MoE | 100% jailbreak success |
| **Gemma 2 9B** | Moderate | Balanced | Less cybersec-specific training |

## Our Research Gap

**No existing benchmark evaluates defensive AI agents specifically for IoT/smart-city infrastructure.**

- CAIBench → CTF-focused (offensive)
- Wiz Arena → Cloud security
- SecBench → Knowledge-based (MCQ)
- **Our arena → First IoT/OT defensive agent benchmark** ← Novel contribution

## References
- CAIBench: https://arxiv.org/abs/2308.06782
- CTI-Bench: https://medium.com/
- SecBench: https://aimultiple.com/
- Wiz AI Cyber Arena: https://wiz.io/
