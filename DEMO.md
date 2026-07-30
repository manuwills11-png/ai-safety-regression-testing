# Live Demo Script

## Setup (1 min before stage)

```bash
cd ai-safety-regression-testing
git status  # confirm on a clean main
```

No live API calls are needed for the demo — `DEMO_MODE=1` uses the cached
fixtures below, so nothing depends on Cloudflare/Gemini being fast or up.

## Demo Flow (5 min on stage)

### Hook (30 sec)
> "Every team fine-tuning Gemma 4 can silently break its own safety
> guardrails. Existing safety CI tools catch known attacks — they run a
> fixed list. This is Gemma 4 attacking Gemma 4, adaptively, every time you
> deploy, with a regression gate that fails the build if it finds something
> new."

### Show the code (1 min)
- Open `.github/workflows/safety-check.yml` — point to the trigger on `push`
- Open `src/attacker.py` — the Gemma 4 red-team system prompt

### Run the primary demo pair (1.5 min)
This is the "watch checkmarks flip" moment. It uses the **synthetic
fixtures** (`examples/archive_v1_synthetic_test.json` and
`archive_v2_synthetic_test.json`), not a live run — chosen deliberately so
the visual always reproduces the same clean regression on demand:

```bash
DEMO_MODE=1 bash entry.sh v2
# or, to render the HTML view directly:
python -m src.cli diff examples/archive_v1_synthetic_test.json examples/archive_v2_synthetic_test.json
open safety_diff.html   # (or start safety_diff.html on Windows)
```

> "This is the signature screen. Checkmarks mean the model defended. X's
> mean it broke. `roleplay_bypass` and `multi_turn_escalation` both flipped
> from defended to broken — two regressions, build fails."

### Callout: this already caught a real one (30 sec)
> "This isn't just a synthetic demo. This exact regression detection
> already caught a real issue in our own CI — here's the actual failed
> GitHub Action run:
> https://github.com/manuwills11-png/ai-safety-regression-testing/actions/runs/30539385942
>
> That run did two full live discovery passes against Gemma 4 and the gate
> correctly failed the build on a real `multi_turn_escalation` regression —
> not a canned example."

### Replay (1 min)
```bash
python -m src.cli replay examples/archive_v2_synthetic_test.json 1
open replay.html
```
- Show the attack prompt, the target's response, the judge's reasoning
- Point at the Root Cause label
> "One word. That's all you need to know."

### Secondary proof point: a real clean deploy (30 sec)
```bash
python -m src.cli diff examples/archive_v1_cached.json examples/archive_v2_cached.json
```
> "And this pair is a real live discovery run against Gemma 4, not
> synthetic — no regressions found, build passes. Same tool, same gate,
> real model calls, clean result." (Pre-rendered at
> `examples/safety_diff_cached.html` if you don't want to run it live.)

### Close
> "We're not pitching a smarter jailbreak generator. We're pitching the
> missing piece: adaptive discovery wired into CI regression gating. Gemma 4
> red-teaming Gemma 4, with a Safety Diff you can read in two seconds."

## Fallback Notes

- Primary demo path (`DEMO_MODE=1` / synthetic fixtures) makes zero live API
  calls — it cannot be slow or flaky on stage.
- If asked "is this real," the CI run link and the secondary clean-deploy
  pair are both real live Gemma 4 output — have both ready.
- If a live run is specifically requested: `python -m src.cli run --variant v2`
  (no `DEMO_MODE`) — budget several minutes; live discovery has hit
  provider-side timeouts before (see gemini_client.py / cloudflare_client.py
  comments), so don't do this live on stage as the primary path.
