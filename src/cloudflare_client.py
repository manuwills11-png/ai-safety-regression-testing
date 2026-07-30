"""
Cloudflare Workers AI client — same interface as gemini_client.py
(get_client, generate_text, call_function_with_retry) so attacker.py,
target.py, and judge.py can run against either provider unchanged; the
active one is picked by model_client.py via MODEL_PROVIDER.

Calls the Cloudflare Workers AI REST API directly:

    POST https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}
    Authorization: Bearer {api_token}

Cloudflare's generic Workers AI docs describe tools as a flat
{"name", "description", "parameters"} shape with a simplified
{"result": {"response", "tool_calls"}} response. That does NOT match reality
for this model: @cf/google/gemma-4-26b-a4b-it-external is served through an
OpenAI-compatible /v1/chat/completions backend (confirmed via a live 400
error naming the sglang OpenAI entrypoint), so it requires OpenAI's exact
wrapped tool format and returns a full OpenAI chat-completion object nested
under "result" — verified against this account's live responses:

  request:  "tools": [{"type": "function", "function": {name, description, parameters}}]
  response: result.choices[0].message.content            (plain text)
            result.choices[0].message.tool_calls[]        (when a tool is called)
              -> {"id", "type": "function",
                  "function": {"name": ..., "arguments": "<JSON string>"}}

No forced/constrained tool-choice mode is used here — Cloudflare's API
doesn't expose one, and forcing it via Gemini's API was what caused the 504s
that led to this client existing, so this is the AUTO-equivalent by default.
"""
import json
import os
import time

import requests
from dotenv import load_dotenv

from .utils import QuotaExceededError

TIMEOUT_S = 60  # requests' timeout is in seconds, not milliseconds; matches
# gemini_client.py's TIMEOUT_MS=60_000 after the same content-dependent
# latency was observed on both providers
MAX_TRANSIENT_RETRIES = 3
BACKOFF_BASE_SECONDS = 2
TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}

MODEL_NAME = os.environ.get("CLOUDFLARE_MODEL_ID", "@cf/google/gemma-4-26b-a4b-it")

_config = None


def get_client():
    """Cloudflare's REST API is stateless, so there's no persistent client
    object — this validates and caches the request config the way
    gemini_client.get_client() caches a genai.Client()."""
    global _config
    if _config is None:
        load_dotenv()
        account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
        if not account_id or not api_token:
            raise RuntimeError(
                "CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN must both be set "
                "in .env to use MODEL_PROVIDER=cloudflare."
            )
        base_url = (
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}"
            f"/ai/run/{MODEL_NAME}"
        )
        _config = {
            "base_url": base_url,
            "headers": {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            },
        }
    return _config


def _post_with_backoff(config, payload):
    """POST to Workers AI, retrying transient 429/5xx and network errors."""
    last_exc = None
    for attempt in range(MAX_TRANSIENT_RETRIES):
        response = None
        try:
            response = requests.post(
                config["base_url"],
                headers=config["headers"],
                json=payload,
                timeout=TIMEOUT_S,
            )
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_exc = exc

        if response is not None:
            if response.status_code not in TRANSIENT_STATUS_CODES:
                response.raise_for_status()
                data = response.json()
                if data.get("success") is False:
                    raise RuntimeError(
                        f"Cloudflare Workers AI request failed: {data.get('errors')}"
                    )
                return data
            if response.status_code == 429:
                last_exc = QuotaExceededError(
                    f"Cloudflare Workers AI returned 429 (quota exceeded): "
                    f"{response.text[:500]}"
                )
            else:
                last_exc = RuntimeError(
                    f"Cloudflare Workers AI returned transient status "
                    f"{response.status_code}: {response.text[:500]}"
                )

        if attempt < MAX_TRANSIENT_RETRIES - 1:
            sleep_seconds = BACKOFF_BASE_SECONDS * (2**attempt)
            print(
                f"  Transient error ({last_exc!r}), retrying in {sleep_seconds}s "
                f"(attempt {attempt + 1}/{MAX_TRANSIENT_RETRIES})..."
            )
            time.sleep(sleep_seconds)

    raise last_exc


def _message(data):
    return data["result"]["choices"][0]["message"]


def _extract_tool_call(data, expected_name):
    for call in _message(data).get("tool_calls") or []:
        fn = call.get("function") or {}
        if fn.get("name") != expected_name:
            continue
        args = fn.get("arguments")
        if isinstance(args, str):
            args = json.loads(args)
        return args
    return None


def generate_text(system_prompt: str, user_prompt: str) -> str:
    """Plain (no-tools) call, used by target.py."""
    config = get_client()
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    }
    data = _post_with_backoff(config, payload)
    return _message(data)["content"]


def call_function_with_retry(system_prompt, user_prompt, function_schema, expected_name):
    """Call Gemma 4 (via Cloudflare Workers AI) with a single tool.

    If the model responds with free text instead of calling the expected
    function, retry once with an explicit instruction to call it. Raises
    RuntimeError if it still doesn't call the function on the second try.
    """
    config = get_client()
    tool = {"type": "function", "function": function_schema}

    def _call(prompt_text):
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text},
            ],
            "tools": [tool],
        }
        return _post_with_backoff(config, payload)

    data = _call(user_prompt)
    args = _extract_tool_call(data, expected_name)
    if args is not None:
        return args

    print(f"  Model did not call {expected_name}; retrying with explicit instruction...")
    retry_prompt = (
        f"{user_prompt}\n\nYou must call the {expected_name} function with your response."
    )
    data = _call(retry_prompt)
    args = _extract_tool_call(data, expected_name)
    if args is not None:
        return args

    raise RuntimeError(
        f"Model did not return a {expected_name} function call after retry. "
        f"Last response: {_message(data).get('content')!r}"
    )
