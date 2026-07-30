"""
Picks the active model-provider module based on MODEL_PROVIDER (default
"cloudflare", chosen after a head-to-head comparison showed no meaningful
reliability/latency difference vs. gemini) and FALLBACK_PROVIDER (default
"gemini"). Every provider module exposes the same interface —
get_client(), generate_text(), call_function_with_retry() — so attacker.py,
target.py, judge.py, and discovery.py don't need to know which one is
active, or whether a call failed over, just that they get a valid response.

If the primary provider raises QuotaExceededError (HTTP 429, even after its
own internal retries are exhausted), that one call transparently fails over
to FALLBACK_PROVIDER instead of crashing the whole discovery run.
"""
import logging
import os

from dotenv import load_dotenv

from . import cloudflare_client, gemini_client
from .utils import QuotaExceededError

load_dotenv()  # so MODEL_PROVIDER/FALLBACK_PROVIDER can be set in .env, not just the shell env

logger = logging.getLogger(__name__)

_PROVIDERS = {
    "gemini": gemini_client,
    "cloudflare": cloudflare_client,
}


def _resolve_provider(env_var: str, default: str) -> str:
    name = os.environ.get(env_var, default).strip().lower()
    if name not in _PROVIDERS:
        raise RuntimeError(f"Unknown {env_var}: {name!r}. Expected one of {list(_PROVIDERS)}.")
    return name


PROVIDER = _resolve_provider("MODEL_PROVIDER", "cloudflare")
FALLBACK_PROVIDER = _resolve_provider("FALLBACK_PROVIDER", "gemini")

_active = _PROVIDERS[PROVIDER]
_fallback = _PROVIDERS[FALLBACK_PROVIDER]

get_client = _active.get_client
MODEL_NAME = _active.MODEL_NAME


def _with_failover(fn_name, *args, **kwargs):
    primary_fn = getattr(_active, fn_name)

    if PROVIDER == FALLBACK_PROVIDER:
        return primary_fn(*args, **kwargs)

    try:
        return primary_fn(*args, **kwargs)
    except QuotaExceededError as exc:
        warning = (
            f"WARNING: {PROVIDER} hit a quota limit ({exc}); "
            f"failing over to {FALLBACK_PROVIDER} for this call."
        )
        logger.warning(warning)
        print(warning)
        fallback_fn = getattr(_fallback, fn_name)
        return fallback_fn(*args, **kwargs)


def generate_text(system_prompt, user_prompt):
    return _with_failover("generate_text", system_prompt, user_prompt)


def call_function_with_retry(system_prompt, user_prompt, function_schema, expected_name):
    return _with_failover(
        "call_function_with_retry", system_prompt, user_prompt, function_schema, expected_name
    )
