"""
Utility module for normalizing and validating API endpoint URLs.

This module handles URL validation for various LLM providers, ensuring
the correct completions endpoint is used while respecting user configuration.
"""

from typing import Optional, Dict, Tuple
from urllib.parse import urlparse
import os


# Known OpenAI-compatible API providers and their FULL correct endpoints
# Format: "detection_string": "full_correct_endpoint"
KNOWN_PROVIDERS = {
    # Major cloud providers
    "openrouter.ai": "https://openrouter.ai/api/v1/chat/completions",
    "api.openai.com": "https://api.openai.com/v1/chat/completions",
    "api.anthropic.com": "https://api.anthropic.com/v1/messages",  # Note: Anthropic has different format
    "generativelanguage.googleapis.com": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",  # Google uses different format
    
    # Chinese/Asian providers
    "api.deepseek.com": "https://api.deepseek.com/v1/chat/completions",
    "dashscope.aliyuncs.com": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",  # Alibaba Cloud (Qwen)
    "api.qwen.ai": "https://api.qwen.ai/compatible-mode/v1/chat/completions",  # Qwen direct
    "api.moonshot.cn": "https://api.moonshot.cn/v1/chat/completions",  # MoonshotAI (Kimi)
    "api.minimax.chat": "https://api.minimax.chat/v1/text/chatcompletion_pro",  # MiniMax (may not be OpenAI-compatible)
    "open.bigmodel.cn": "https://open.bigmodel.cn/api/paas/v4/chat/completions",  # Z.ai (ZhipuAI)
    "api.xiaomi.com": "https://api.xiaomi.com/v1/chat/completions",  # Xiaomi (MiLM)
    
    # Western AI providers
    "api.mistral.ai": "https://api.mistral.ai/v1/chat/completions",
    "api.x.ai": "https://api.x.ai/v1/chat/completions",  # xAI (Grok)
    "integrate.api.nvidia.com": "https://integrate.api.nvidia.com/v1/chat/completions",  # NVIDIA NIM
    "api.poolside.ai": "https://api.poolside.ai/v1/chat/completions",  # Poolside
    
    # Local/self-hosted (common default ports)
    "localhost:8080": "http://localhost:8080/v1/chat/completions",  # llama.cpp default
    "localhost:11434": "http://localhost:11434/v1/chat/completions",  # Ollama with OpenAI compatibility mode
    "127.0.0.1:8080": "http://127.0.0.1:8080/v1/chat/completions",  # llama.cpp alternative
    "127.0.0.1:11434": "http://127.0.0.1:11434/v1/chat/completions",  # Ollama alternative
}


def detect_provider(url: str) -> Optional[str]:
    """
    Detect if the URL belongs to a known provider.
    
    Args:
        url: The API endpoint URL to check
        
    Returns:
        The detection string (provider key) if recognized, None otherwise
    """
    parsed = urlparse(url)
    netloc = parsed.netloc
    
    for provider in KNOWN_PROVIDERS.keys():
        if provider in netloc:
            return provider
    return None


def validate_endpoint(url: str, verbose: int = 0) -> Tuple[bool, Optional[str]]:
    """
    Validate that the endpoint URL is properly formatted.
    
    Args:
        url: The API endpoint URL to validate
        verbose: Verbosity level for warnings
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url:
        msg = "Empty endpoint URL"
        if verbose > 0:
            print(f"[API ERROR] {msg}")
        return False, msg
    
    parsed = urlparse(url)
    
    if not parsed.scheme or not parsed.netloc:
        msg = f"Invalid URL format: {url}"
        if verbose > 0:
            print(f"[API ERROR] {msg}")
        return False, msg
    
    if parsed.scheme not in ("http", "https"):
        if verbose > 0:
            print(f"[API WARNING] Unexpected scheme: {parsed.scheme}")
    
    return True, None


def normalize_endpoint(url: str, verbose: int = 0, no_confirm: bool = False) -> str:
    """
    Normalize API endpoint URL.
    
    For known providers, compares the given URL to the full correct endpoint.
    - If they match: use as-is
    - If they don't match: raise ValueError (normal mode) or substitute (no_confirm mode)
    For unknown providers: use as-is.
    
    Args:
        url: The API endpoint URL from config
        verbose: Verbosity level for warnings
        no_confirm: If True, substitute malformed endpoint instead of raising exception
        
    Returns:
        Normalized URL (may be corrected to the full endpoint)
        
    Raises:
        ValueError: If provider detected but URL doesn't match full endpoint (and no_confirm=False)
    """
    if not url:
        return url
    
    # Check basic URL validity
    is_valid, _ = validate_endpoint(url, verbose)
    if not is_valid:
        return url
    
    # Detect provider
    provider = detect_provider(url)
    
    # If not a known provider, use as-is
    if not provider:
        if verbose > 1:
            print(f"[API INFO] Unknown provider, using URL as-is: {url}")
        return url
    
    # Get the full correct endpoint for this provider
    correct_endpoint = KNOWN_PROVIDERS[provider]
    
    # Check if user URL matches the correct endpoint
    if url.rstrip("/") == correct_endpoint.rstrip("/"):
        # URL is correct
        if verbose > 1:
            print(f"[API INFO] Endpoint URL is correct for {provider}: {url}")
        return url
    
    # URL doesn't match - it's likely a base URL or incorrect path
    error_msg = f"Endpoint mismatch for {provider}. Given: {url}, Expected: {correct_endpoint}"
    
    if no_confirm:
        # Substitute with correct endpoint
        if verbose > 0:
            print(f"[API WARNING] {error_msg}")
            print(f"[API WARNING] Substituting with correct endpoint: {correct_endpoint}")
        return correct_endpoint
    else:
        # Raise exception
        raise ValueError(
            f"{error_msg}\n"
            f"Use --no-confirm to automatically substitute with the correct endpoint, "
            f"or update your config to use: {correct_endpoint}"
        )


def get_provider_info(url: str) -> Dict[str, str]:
    """
    Get information about the detected provider.
    
    Args:
        url: The API endpoint URL
        
    Returns:
        Dictionary with provider info
    """
    provider = detect_provider(url)
    
    if not provider:
        return {"provider": "unknown", "full_endpoint": "unknown", "is_known": False}
    
    return {
        "provider": provider,
        "full_endpoint": KNOWN_PROVIDERS[provider],
        "is_known": True,
    }
