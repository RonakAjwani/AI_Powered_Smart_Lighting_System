# LLM Provider Matrix for Multi-Model Evaluation

## Provider Comparison

| Provider | Models Available | Free Tier | Rate Limit | Speed | Sign-Up URL |
|---|---|---|---|---|---|
| **Cerebras** | Llama 3.1 8B/70B, Qwen3 32B/235B | 1M tokens/day | 30 RPM | 1,800 tok/sec (8B) | https://cloud.cerebras.ai/ |
| **Groq** | Llama 3.1 8B/70B, Mixtral 8x7B, Gemma 2 9B, Qwen3 32B | Free tier | 30 RPM (free) | ~500 tok/sec | https://console.groq.com/ |
| **Together AI** | Llama 3.1, Mistral 7B, Qwen 2.5, DeepSeek-V2 | Limited free | Dynamic RPM | ~275 tok/sec | https://api.together.ai/ |
| **Fireworks AI** | Llama 3, Mixtral, Mistral | Free ($1 credit) | 600 RPM | Fast multimodal | https://fireworks.ai/ |
| **DeepSeek** | DeepSeek-V2, DeepSeek-R1 | Pay-per-token (cheap) | Moderate | Variable | https://platform.deepseek.com/ |
| **Mistral** | Mistral 7B, Mistral Large | Free tier | ~6 RPM | Moderate | https://console.mistral.ai/ |

## Models to Evaluate (Same Model Across Providers)

| Model | Primary Provider | Fallback Provider | Context Window |
|---|---|---|---|
| **Llama 3.1 8B** | Cerebras | Groq | 8,192 |
| **Llama 3.1 70B** | Cerebras | Groq | 8,192 |
| **Qwen3 32B** | Cerebras | Groq | 64,000 |
| **Mixtral 8x7B** | Groq | Fireworks AI | 32,768 |
| **Gemma 2 9B** | Groq | — | 8,192 |
| **Mistral 7B** | Mistral API | Together AI | 32,768 |
| **DeepSeek-V2** | DeepSeek API | Together AI | 128,000 |

## API Keys Needed (User Action Required)

### Step 1: Cerebras (Primary — fastest inference)
1. Go to https://cloud.cerebras.ai/
2. Sign up with email/Google
3. Navigate to API Keys → Create new key
4. Copy the API key

### Step 2: Groq (Fallback — free tier)
1. Go to https://console.groq.com/
2. Sign up with email/Google/GitHub
3. Navigate to API Keys → Create API Key
4. Copy the API key

### Step 3: Together AI (Mistral, Qwen, DeepSeek models)
1. Go to https://api.together.ai/
2. Sign up with email/Google/GitHub
3. Navigate to Settings → API Keys
4. Copy the API key

### Step 4: DeepSeek (DeepSeek-V2 model)
1. Go to https://platform.deepseek.com/
2. Sign up with email
3. Navigate to API Keys
4. Copy the API key

### Step 5: Mistral (Mistral 7B model)
1. Go to https://console.mistral.ai/
2. Sign up with email/Google/GitHub
3. Navigate to API Keys
4. Copy the API key

## Environment Variables to Set

```bash
# In .env file
CEREBRAS_API_KEY=your_cerebras_key
GROQ_API_KEY=your_groq_key
TOGETHER_API_KEY=your_together_key
DEEPSEEK_API_KEY=your_deepseek_key
MISTRAL_API_KEY=your_mistral_key
```

## Provider Switching Design — No Context Loss

Since LLM APIs are **stateless** (each call is independent), switching providers for the same model has **zero context loss**:

- Same model weights → same analysis capability
- Our pipeline sends self-contained prompts (compressed log summary + system prompt)
- Previous window findings stored in Redis, not in LLM memory
- Provider failover is transparent to the agent

## Rate Limit Management Strategy

With ~33 LLM calls per model evaluation (11 scenarios × Pass@3), across 7 models = ~231 total calls:

| Provider | RPM | Total calls handled | Time needed |
|---|---|---|---|
| Cerebras | 30 RPM | ~99 calls (3 models) | ~3.3 min |
| Groq | 30 RPM | ~99 calls (3 models) | ~3.3 min |
| Together AI | Dynamic | ~33 calls (1 model) | ~1-2 min |
| DeepSeek | Moderate | ~33 calls (1 model) | ~1-2 min |
| Mistral | 6 RPM | ~33 calls (1 model) | ~5.5 min |
| **Total** | — | **231 calls** | **~15-16 min** |

Full evaluation across all 7 models completes in under 20 minutes.
