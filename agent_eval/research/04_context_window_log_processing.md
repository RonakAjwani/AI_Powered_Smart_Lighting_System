# Context Window Management for Real-Time Log Stream Processing

## The Challenge

Smart lighting grids generate 60-120 events/second. LLM context windows range 8K-128K tokens. Raw log ingestion overflows even the largest context windows in seconds.

## Research-Backed Solutions (2024-2025)

| Approach | Source | Description |
|---|---|---|
| **Sliding Window Chunking** | RAG research (2024) | 30-sec rolling windows with overlap for context continuity |
| **Semantic Compression** | LLM log analysis (brightcoding.dev, 2025) | Raw events → statistical aggregates (rates, distributions) |
| **Context Condensation** | RLM research (2025) | Summarize previous window, feed into next analysis |
| **CEF Normalization** | SIEM industry standard | Common Event Format reduces token waste |
| **Agentic Chunking** | RAG chunking research (firecrawl.dev, 2024) | LLM-based dynamic chunking by semantic meaning |

## Our 3-Stage Pipeline

1. **Buffer**: 30-sec sliding window captures ~3000 raw events
2. **Compress**: Statistical aggregation → ~500-800 token summary
3. **Analyze**: Compressed summary fits any model's context window

## Context Window Comparison

| Model | Window | Strategy |
|---|---|---|
| Llama 3.1 8B | 8,192 tokens | Compressed stats only |
| Gemma 2 9B | 8,192 tokens | Compressed stats only |
| Mixtral 8x7B | 32,768 tokens | Stats + raw suspicious events |
| Qwen3 32B | 64,000 tokens | Stats + raw events + history |
| DeepSeek-V2 | 128,000 tokens | All data + multi-window context |

> **Novel finding for paper**: Do larger context windows improve detection accuracy? This creates a natural independent variable.

## Stateless Inference — Why Provider Switching Has No Context Loss

LLM APIs are inherently **stateless**. Each API call is independent — no conversation history is maintained server-side. Our pipeline design ensures:

1. Each analysis window is self-contained (compressed summary + system prompt)
2. Previous findings are stored in Redis, not in LLM memory
3. Switching providers mid-evaluation is seamless — same prompt → same model weights → equivalent output
4. **Key guarantee**: Same model (e.g., Llama 3.1 8B) produces equivalent results whether served by Cerebras or Groq

## References
- RAG Chunking Strategies (2024): https://dev.to/
- LLM Log Analysis (2025): https://brightcoding.dev/
- Recursive Language Models: https://llmsresearch.com/
- SIEM CEF Format: https://www.microfocus.com/documentation/arcsight
