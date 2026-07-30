"""
Shared Gemini API client + the validated function-calling pattern from
test_gemma_api.py: default AUTO mode only (forced/constrained mode causes a
504 on Gemma 4), with a retry-once-then-error fallback for when the model
returns free text instead of a function call.

Some prompts also cause the backend itself to exceed its own deadline and
return a transient 504 DEADLINE_EXCEEDED (observed independent of tool use,
content-dependent, not a client-side bug) — generate_content_with_backoff
retries those a few times before giving up.
"""
import os
import time

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

from .utils import QuotaExceededError

MODEL_NAME = "gemma-4-26b-a4b-it"
TIMEOUT_MS = 60_000  # HttpOptions.timeout is in milliseconds
MAX_TRANSIENT_RETRIES = 3
BACKOFF_BASE_SECONDS = 2

TRANSIENT_EXCEPTIONS = (errors.ServerError, httpx.TimeoutException)

_client = None


def get_client():
    global _client
    if _client is None:
        load_dotenv()
        if not os.environ.get("GEMINI_API_KEY"):
            raise RuntimeError(
                "GEMINI_API_KEY not set. Add a real key to .env before running."
            )
        _client = genai.Client()
    return _client


def generate_content_with_backoff(client, **kwargs):
    """client.models.generate_content, retrying transient 504s/timeouts/429s.

    A 429 is a ClientError (4xx), not a ServerError, so it's handled
    separately: retried the same as other transient failures, but raised as
    QuotaExceededError once retries are exhausted, so model_client.py can
    fail over to another provider specifically on this. Other ClientErrors
    (400, 401, ...) are real bugs, not transient — raised immediately.
    """
    last_exc = None
    for attempt in range(MAX_TRANSIENT_RETRIES):
        try:
            return client.models.generate_content(**kwargs)
        except errors.ClientError as exc:
            if exc.code != 429:
                raise
            last_exc = QuotaExceededError(f"Gemini quota exceeded (429): {exc}")
        except TRANSIENT_EXCEPTIONS as exc:
            last_exc = exc

        if attempt < MAX_TRANSIENT_RETRIES - 1:
            sleep_seconds = BACKOFF_BASE_SECONDS * (2**attempt)
            print(
                f"  Transient error ({last_exc!r}), retrying in {sleep_seconds}s "
                f"(attempt {attempt + 1}/{MAX_TRANSIENT_RETRIES})..."
            )
            time.sleep(sleep_seconds)
    raise last_exc


def generate_text(system_prompt, user_prompt):
    """Plain (no-tools) call, used by target.py. Provider-agnostic name shared
    with cloudflare_client.py so callers don't need to know which is active."""
    client = get_client()
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        http_options=types.HttpOptions(timeout=TIMEOUT_MS),
    )
    response = generate_content_with_backoff(
        client,
        model=MODEL_NAME,
        contents=user_prompt,
        config=config,
    )
    return response.text


def call_function_with_retry(system_prompt, user_prompt, function_schema, expected_name):
    """Call Gemma 4 with a single tool in default AUTO mode.

    If the model responds with free text instead of calling the expected
    function, retry once with an explicit instruction to call it. Raises
    RuntimeError if it still doesn't call the function on the second try.
    """
    client = get_client()
    tools = types.Tool(function_declarations=[function_schema])

    def _call(prompt_text):
        config = types.GenerateContentConfig(
            tools=[tools],
            system_instruction=system_prompt,
            http_options=types.HttpOptions(timeout=TIMEOUT_MS),
        )
        return generate_content_with_backoff(
            client,
            model=MODEL_NAME,
            contents=prompt_text,
            config=config,
        )

    def _extract(response):
        if not response.function_calls:
            return None
        for fc in response.function_calls:
            if fc.name == expected_name:
                return fc.args
        return None

    response = _call(user_prompt)
    args = _extract(response)
    if args is not None:
        return args

    print(f"  Model did not call {expected_name}; retrying with explicit instruction...")
    retry_prompt = (
        f"{user_prompt}\n\nYou must call the {expected_name} function with your response."
    )
    response = _call(retry_prompt)
    args = _extract(response)
    if args is not None:
        return args

    raise RuntimeError(
        f"Model did not return a {expected_name} function call after retry. "
        f"Last text response: {getattr(response, 'text', None)!r}"
    )
