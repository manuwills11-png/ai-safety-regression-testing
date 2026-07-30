"""
Picks the active model-provider module based on MODEL_PROVIDER (default
"cloudflare", chosen after a head-to-head comparison showed no meaningful
reliability/latency difference vs. gemini; set MODEL_PROVIDER=gemini to fall
back to it — gemini_client.py is kept intact for exactly that). Every
provider module exposes the same interface — get_client(), generate_text(),
call_function_with_retry() — so attacker.py, target.py, judge.py, and
discovery.py don't need to know which one is active.
"""
import os

from dotenv import load_dotenv

from . import cloudflare_client, gemini_client

load_dotenv()  # so MODEL_PROVIDER can be set in .env, not just the shell env

PROVIDER = os.environ.get("MODEL_PROVIDER", "cloudflare").strip().lower()

_PROVIDERS = {
    "gemini": gemini_client,
    "cloudflare": cloudflare_client,
}

if PROVIDER not in _PROVIDERS:
    raise RuntimeError(
        f"Unknown MODEL_PROVIDER: {PROVIDER!r}. Expected one of {list(_PROVIDERS)}."
    )

_active = _PROVIDERS[PROVIDER]

get_client = _active.get_client
generate_text = _active.generate_text
call_function_with_retry = _active.call_function_with_retry
MODEL_NAME = _active.MODEL_NAME
