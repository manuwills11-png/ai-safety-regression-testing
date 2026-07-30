"""Small shared helpers used across CLI-facing entry points and provider clients."""
import sys


class QuotaExceededError(RuntimeError):
    """Raised by a provider client when a request is rejected for quota/rate-limit
    reasons (HTTP 429), even after that provider's own retries are exhausted.

    Kept distinct from other transient failures (5xx, network timeouts) so
    model_client.py can trigger provider failover specifically on this, and
    only this — a genuine 4xx bug elsewhere shouldn't be silently masked by
    switching providers.
    """


def ensure_utf8_stdout() -> None:
    """Make stdout safe for unicode output (e.g. the ✓/✗ symbols in the
    Safety Diff). Windows consoles default to a codepage like cp1252, which
    raises UnicodeEncodeError on those characters; reconfigure() fixes that.
    No-op if reconfigure isn't available (Python <3.7) or stdout has already
    been redirected to something that doesn't support it.
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass
