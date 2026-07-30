"""Small shared helpers used across CLI-facing entry points."""
import sys


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
