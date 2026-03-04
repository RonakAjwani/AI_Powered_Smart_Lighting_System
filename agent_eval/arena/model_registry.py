"""
Model Registry — Multi-provider LLM router with automatic failover.

Provides a unified interface to access the same open-source models across
free inference providers (Cerebras, Groq, Mistral).

Design guarantees:
  - Same model weights across providers → equivalent outputs
  - Stateless inference → zero context loss on provider switch
  - Automatic failover → if primary provider rate-limited, try next
  - Configurable per-model → provider order, context window, temperature
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Provider(str, Enum):
    """Supported LLM inference providers (free tier only)."""
    CEREBRAS = "cerebras"
    GROQ = "groq"
    MISTRAL = "mistral"


@dataclass
class ModelConfig:
    """Configuration for a single model across providers."""
    model_id: str                          # Internal ID (e.g., "llama-3.1-8b")
    display_name: str                      # Human-readable name
    context_window: int                    # Max tokens
    providers: List[Dict[str, str]]        # [{provider, model_name}] in failover order
    description: str = ""
    family: str = ""                       # Model family (llama, mistral, qwen, etc.)
    parameters: str = ""                   # Parameter count string


@dataclass
class ProviderConfig:
    """Configuration for a single inference provider."""
    name: Provider
    api_key_env: str                       # Environment variable name for API key
    base_url: Optional[str] = None         # Custom base URL (if needed)
    rpm_limit: int = 30                    # Requests per minute
    tpm_limit: int = 30000                 # Tokens per minute
    last_request_time: float = 0.0
    request_count_minute: int = 0
    minute_start: float = 0.0


# ── Provider Configurations ────────────────────────────────

PROVIDER_CONFIGS: Dict[Provider, ProviderConfig] = {
    Provider.CEREBRAS: ProviderConfig(
        name=Provider.CEREBRAS,
        api_key_env="CEREBRAS_API_KEY",
        rpm_limit=30,
        tpm_limit=60000,
    ),
    Provider.GROQ: ProviderConfig(
        name=Provider.GROQ,
        api_key_env="GROQ_API_KEY",
        rpm_limit=30,
        tpm_limit=30000,
    ),
    Provider.MISTRAL: ProviderConfig(
        name=Provider.MISTRAL,
        api_key_env="MISTRAL_API_KEY",
        rpm_limit=6,
        tpm_limit=500000,
    ),
}

# ── Model Registry ─────────────────────────────────────────

MODEL_REGISTRY: Dict[str, ModelConfig] = {
    "llama-3.1-8b": ModelConfig(
        model_id="llama-3.1-8b",
        display_name="Llama 3.1 8B",
        context_window=8192,
        family="llama",
        parameters="8B",
        description="Meta's Llama 3.1 8B — strong cybersecurity analysis (94% score)",
        providers=[
            {"provider": "cerebras", "model_name": "llama3.1-8b"},
            {"provider": "groq", "model_name": "llama-3.1-8b-instant"},
        ],
    ),
    "llama-3.1-70b": ModelConfig(
        model_id="llama-3.1-70b",
        display_name="Llama 3.1 70B",
        context_window=8192,
        family="llama",
        parameters="70B",
        description="Meta's Llama 3.1 70B — highest overall accuracy",
        providers=[
            {"provider": "cerebras", "model_name": "llama3.1-70b"},
            {"provider": "groq", "model_name": "llama-3.1-70b-versatile"},
        ],
    ),
    "qwen-2.5-32b": ModelConfig(
        model_id="qwen-2.5-32b",
        display_name="Qwen 2.5 32B",
        context_window=32768,
        family="qwen",
        parameters="32B",
        description="Alibaba's Qwen 2.5 32B — strong multilingual + coding",
        providers=[
            {"provider": "cerebras", "model_name": "qwen-2.5-32b"},
            {"provider": "groq", "model_name": "qwen-2.5-32b"},
        ],
    ),
    "mixtral-8x7b": ModelConfig(
        model_id="mixtral-8x7b",
        display_name="Mixtral 8x7B",
        context_window=32768,
        family="mistral",
        parameters="46.7B MoE",
        description="Mistral's MoE model — efficient multi-expert architecture",
        providers=[
            {"provider": "groq", "model_name": "mixtral-8x7b-32768"},
        ],
    ),
    "gemma-2-9b": ModelConfig(
        model_id="gemma-2-9b",
        display_name="Gemma 2 9B",
        context_window=8192,
        family="gemma",
        parameters="9B",
        description="Google's Gemma 2 9B — balanced open model",
        providers=[
            {"provider": "groq", "model_name": "gemma2-9b-it"},
        ],
    ),
    "mistral-7b": ModelConfig(
        model_id="mistral-7b",
        display_name="Mistral 7B",
        context_window=32768,
        family="mistral",
        parameters="7B",
        description="Mistral 7B — European compliance focus",
        providers=[
            {"provider": "mistral", "model_name": "mistral-small-latest"},
        ],
    ),
}


class ModelRegistry:
    """
    Manages LLM model selection and provider routing.

    Usage:
        registry = ModelRegistry()
        llm = registry.get_llm("llama-3.1-8b")
        response = llm.invoke("Analyze this traffic...")
    """

    def __init__(self):
        self.models = MODEL_REGISTRY
        self.providers = PROVIDER_CONFIGS
        self._available_providers: Dict[Provider, bool] = {}
        self._check_api_keys()

    def _check_api_keys(self):
        """Check which providers have API keys configured."""
        for provider, config in self.providers.items():
            key = os.getenv(config.api_key_env, "")
            self._available_providers[provider] = bool(key and key != f"your_{provider.value}_api_key_here")
            if self._available_providers[provider]:
                logger.info(f"Provider {provider.value}: API key found ✓")
            else:
                logger.warning(f"Provider {provider.value}: No API key configured")

    def _check_rate_limit(self, provider: Provider) -> bool:
        """Check if provider is within rate limits."""
        config = self.providers[provider]
        now = time.time()

        # Reset counter every minute
        if now - config.minute_start >= 60:
            config.request_count_minute = 0
            config.minute_start = now

        if config.request_count_minute >= config.rpm_limit:
            logger.warning(f"Provider {provider.value}: Rate limit reached ({config.rpm_limit} RPM)")
            return False

        return True

    def _record_request(self, provider: Provider):
        """Record a request for rate limiting."""
        config = self.providers[provider]
        config.request_count_minute += 1
        config.last_request_time = time.time()

    def get_model_info(self, model_id: str) -> Optional[ModelConfig]:
        """Get model configuration by ID."""
        return self.models.get(model_id)

    def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models with availability status."""
        result = []
        for model_id, config in self.models.items():
            available_providers = []
            for p in config.providers:
                provider = Provider(p["provider"])
                if self._available_providers.get(provider, False):
                    available_providers.append(p["provider"])

            result.append({
                "model_id": model_id,
                "display_name": config.display_name,
                "family": config.family,
                "parameters": config.parameters,
                "context_window": config.context_window,
                "available_providers": available_providers,
                "is_available": len(available_providers) > 0,
            })
        return result

    def get_llm(self, model_id: str, temperature: float = 0.0, provider_override: Optional[str] = None):
        """
        Get a LangChain-compatible LLM instance for the specified model.

        Args:
            model_id: Model identifier from registry
            temperature: LLM temperature (default 0 for deterministic)
            provider_override: Force a specific provider (bypasses failover)

        Returns:
            LangChain BaseChatModel instance

        Raises:
            ValueError: If model not found or no providers available
        """
        model_config = self.models.get(model_id)
        if not model_config:
            available = ", ".join(self.models.keys())
            raise ValueError(f"Model '{model_id}' not found. Available: {available}")

        # Determine provider order
        if provider_override:
            provider_entries = [p for p in model_config.providers if p["provider"] == provider_override]
            if not provider_entries:
                raise ValueError(f"Provider '{provider_override}' not available for model '{model_id}'")
        else:
            provider_entries = model_config.providers

        # Try providers in order (failover)
        last_error = None
        for entry in provider_entries:
            provider = Provider(entry["provider"])
            model_name = entry["model_name"]

            # Check availability
            if not self._available_providers.get(provider, False):
                logger.debug(f"Skipping {provider.value}: no API key")
                continue

            # Check rate limits
            if not self._check_rate_limit(provider):
                logger.debug(f"Skipping {provider.value}: rate limited")
                continue

            try:
                llm = self._create_llm(provider, model_name, temperature)
                self._record_request(provider)
                logger.info(f"Using {model_config.display_name} via {provider.value} ({model_name})")
                return llm
            except Exception as e:
                last_error = e
                logger.warning(f"Failed to create LLM via {provider.value}: {e}")
                continue

        raise ValueError(
            f"No available provider for model '{model_id}'. "
            f"Last error: {last_error}. "
            f"Check API keys in .env file."
        )

    def _create_llm(self, provider: Provider, model_name: str, temperature: float):
        """Create a LangChain chat model for the given provider."""

        if provider == Provider.CEREBRAS:
            from langchain_cerebras import ChatCerebras
            return ChatCerebras(
                model=model_name,
                api_key=os.getenv("CEREBRAS_API_KEY"),
                temperature=temperature,
            )

        elif provider == Provider.GROQ:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model_name=model_name,
                groq_api_key=os.getenv("GROQ_API_KEY"),
                temperature=temperature,
            )

        elif provider == Provider.MISTRAL:
            from langchain_mistralai import ChatMistralAI
            return ChatMistralAI(
                model=model_name,
                mistral_api_key=os.getenv("MISTRAL_API_KEY"),
                temperature=temperature,
            )

        else:
            raise ValueError(f"Unknown provider: {provider}")


# ── Singleton Instance ─────────────────────────────────────
_registry: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    """Get or create the singleton ModelRegistry instance."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
    return _registry
