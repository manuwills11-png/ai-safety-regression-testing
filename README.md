# AI Safety Regression Testing

CI for AI safety: this is the missing piece between static jailbreak scanners and adaptive red-teaming research. Every deploy, **Gemma 4 red-teams Gemma 4** — an attacker model iteratively refines jailbreak attempts against a target model, a judge model scores each attempt, and a regression engine diffs the result against the last known-good run. If a risk category that used to be defended flips to broken, the build fails, the same way a broken unit test would. The signature output is the **Safety Diff**: a category-by-category ✓/✗ table that makes "did this deploy make the model less safe?" answerable in two seconds instead of a full manual audit.

## Architecture

```
Gemma 4 Attacker (adversarial prompt)
  ↓
Target Model (v1 safe, v2 weaker)
  ↓
Gemma 4 Judge (evaluator)
  ↓
Vulnerability Archive (JSON records)
  ↓
Regression Engine (✓/✗ diff)
  ↓
Safety Diff (the signature screen)
  ↓
GitHub Action (fails build on regression)
```

## Quick Start

```bash
pip install -r requirements.txt

# Run discovery against a target variant, save the results as an archive
python -m src.cli run --variant v2

# Compare two archives, produce the Safety Diff (exits 1 on regression)
python -m src.cli diff archive_v1.json archive_v2.json

# Replay a specific attack: prompt, response, verdict, Root Cause label
python -m src.cli replay archive_v2.json 0
```

## Why This, Not [Existing Tool]

| What exists | What it actually does | The gap that remains |
|---|---|---|
| Garak, PyRIT | Fixed or semi-fixed probe battery | Static — misses anything not already written down |
| FutureAGI `fi` CLI and similar eval-gate tools | CI/CD-integrated safety scanners with statistical regression gating | Still a fixed/classifier-based test battery underneath — the *gate* is real, the *discovery* isn't adaptive |
| GitHub repos tagged `regression-testing` + `jailbreak` + `ai-safety` | Automate a fixed attack suite in CI, produce regression evidence | Same limitation — regression tracking exists, but against a static list |
| PAIR / TAP / AutoDAN-Turbo (research) | An attacker LLM iteratively refines attacks using judge feedback — genuinely adaptive discovery | Research code, not wired into CI, no regression tracking, no versioning |
| **This project** | **Adaptive discovery (attacker LLM + judge feedback loop) wired into a CI regression gate** | — |

## Limitations

- **Judge verdicts are a strong signal, not ground truth.** The judge is itself an LLM call; its pass/fail calls are treated as reliable but not infallible.
- **The v1/v2 target pair is two system-prompt configurations of the same model (a strong safety prompt vs. a weak one), not a real fine-tune.** This is disclosed plainly rather than implied — it's a real, honest behavior gap, just not one produced by training a checkpoint.
- **This tests the model itself.** A team running a separate runtime safety layer (input/output filtering, etc.) should use this alongside it, not instead of it.

## Setup

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Notes |
|---|---|---|
| `MODEL_PROVIDER` | No | `cloudflare` (default) or `gemini` |
| `FALLBACK_PROVIDER` | No | `gemini` (default) — see Resilience below |
| `CLOUDFLARE_ACCOUNT_ID` | Yes, if using `cloudflare` | From the Cloudflare dashboard |
| `CLOUDFLARE_API_TOKEN` | Yes, if using `cloudflare` | Workers AI-scoped API token |
| `GEMINI_API_KEY` | Yes, if using `gemini` | Fallback provider, kept working alongside Cloudflare |

For the GitHub Action, set `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` as repo secrets.

### Resilience: automatic provider failover

If `MODEL_PROVIDER` returns a 429 (quota exceeded) even after its own
retries are exhausted, that single call transparently fails over to
`FALLBACK_PROVIDER` and logs a warning — one provider hitting a rate limit
mid-run doesn't crash the whole discovery loop. This is invisible to
`discovery.py`; it just gets a valid response either way.
