# AI Safety Regression Testing — Complete Product & Build Guide
### CI for AI Safety: Regression Testing for Model Vulnerabilities

*(Working title only — swap the placeholder name in once you've decided on one.)*

---

## 0. The Pitch, Locked

**One sentence:**
> [Your Product] is GitHub Actions for AI safety — it automatically discovers safety regressions every time your LLM changes.

**Target user:**
> ML engineers deploying fine-tuned open-source LLMs.

Not "AI developers," not "enterprises," not "security teams." Every slide, every feature, every demo beat gets built for this one person. If a feature doesn't help this person ship a fine-tune more safely, it doesn't belong in the product.

---

## 1. The Problem

Every time a team fine-tunes or redeploys an open model, its safety guardrails can silently degrade. Nobody finds out until:
- A user posts a screenshot of a jailbreak that worked, or
- A security researcher discloses it, or
- It's too late.

There is no equivalent of `git diff` or a broken CI test for model safety. Teams ship blind.

---

## 2. Why Current Tools Don't Solve This

| Tool | What it does | What it's missing |
|---|---|---|
| Garak / PyRIT | Run a fixed or semi-fixed battery of known jailbreak probes | Static — only catches attacks someone already wrote down |
| PAIR / TAP / AutoDAN-Turbo / Rainbow Teaming (research) | Use an attacker LLM to *discover new* jailbreaks automatically | Research methods, not packaged products — no versioning, no CI, no "did this get worse" tracking |
| DeepTeam / Promptfoo | Package red-teaming into a dev-facing eval report | One-time audit — a snapshot, not a trend |

**The gap: every one of these tells you a model is vulnerable *right now*. None of them tell you whether your last deployment made it *more* vulnerable, or vulnerable in a *new* way.** That's a versioning/regression problem — the same problem code testing solved a decade ago — and nobody has wired it into a CI product for model safety yet.

---

## 3. The Product

**This is a GitHub Action.** You drop it into your model's deploy pipeline. On every commit or fine-tune, it:

1. **Discovers** — an attacker LLM automatically generates and refines jailbreak attempts against your model (not a static list — it iterates, using a judge model's feedback, the way a real attacker would).
2. **Maps** — every successful attack is filed into an archive by risk category × attack style, building a live picture of *where* your model is weak.
3. **Diffs** — every run is compared against your last one. New weak spots, and any rise in attack success rate, are surfaced explicitly.
4. **Gates** — if safety regresses, the build fails. Same as a broken unit test.

```
git push  →  runs  →  new vulnerability found?  →  ❌ build fails, report attached
                    →  no regression?            →  ✅ build passes
```

---

## 4. What Makes This Different

We are **not** claiming a new attack-generation algorithm — the generation techniques (attacker-LLM refinement, diversity search) are proven research methods, and we say so upfront rather than overselling it.

What's missing from the landscape isn't a better way to *find* a jailbreak. It's a way to know, automatically, on every deploy, whether you introduced a new one — the same reflex every engineering team already has for broken code, just missing for broken safety.

**That reframes the category:** not "another red-teaming tool" (crowded), but **"regression testing infrastructure for AI safety"** (essentially unoccupied as a packaged product).

---

## 5. The Signature Idea: The Safety Diff

Every safety demo tends to show a raw percentage: *"attack success rate went from 12% to 26%."* Numbers don't stick in someone's memory across ten other things they've seen that day. A **diff** does — everyone already has the mental model for it from `git diff`.

This is the one screen you want people to still remember afterward:

```
Safety Diff

Model v1                      Model v2
✓ Prompt Injection      →      ✗ Prompt Injection
✓ Roleplay              →      ✗ Roleplay
✓ Tool Misuse           →      ✓ Tool Misuse

Regression: +2 vulnerabilities
```

`✓` = defended, `✗` = broke. Nothing else needs explaining — the moment someone sees checkmarks flip to X's, they understand the entire product without a word of explanation. This view is the product's homepage, its CI report, and the centerpiece of any demo. Everything else exists to feed this one screen or let someone drill into one line of it.

---

## 6. The User Journey

```
Fine-tune model
      ↓
Push to GitHub
      ↓
Discovery runs (attacker LLM vs. target, judged)
      ↓
Safety Diff shows categories flipping from ✓ to ✗
      ↓
Blocks the deployment (CI check fails)
      ↓
Developer clicks a flipped line, replays the exact attack, sees the root cause
      ↓
Developer fixes it, re-runs → Safety Diff shows all ✓ again → deployment succeeds
```

---

## 7. Architecture: Three Engines

### 7.1 Discovery Engine
| Component | Role |
|---|---|
| Seed prompts | A small set of known jailbreak styles (roleplay, prompt injection, multi-turn escalation, obfuscation) — bootstraps the attacker, doesn't limit it |
| Attacker LLM | Iteratively rewrites the attack using judge feedback — this is what makes it "not a static list" |
| Target model | The model under test (base checkpoint or fine-tune) |
| Judge model | Scores each response: did the target comply with something it shouldn't have |
| Success detector | Converts judge scores into a pass/fail verdict per attempt |

Use a known iterative-refinement technique (PAIR/TAP-style) rather than inventing a new attack algorithm — the innovation here is the regression layer, not the attack search, and saying so builds trust rather than doubt.

### 7.2 Vulnerability Archive
Every attack attempt is stored as a structured record — this is what makes the diff and replay features possible.

```
Attack record:
  - attack_id
  - category        (roleplay bypass, prompt injection, multi-turn escalation, tool misuse)
  - prompt          (full attacker turn, including refinement history)
  - response         (target model's output)
  - verdict          (success / fail)
  - model_version    (which checkpoint was tested)
  - timestamp
```
Flat JSON files or SQLite are enough — no need for a real database. The archive is what turns "we ran some attacks" into a queryable history.

### 7.3 Regression Engine → Safety Diff
Given archive(version A) and archive(version B), for each risk category: was it defended (no successful attack) or broken (at least one successful attack) in each run? The Safety Diff is exactly this table, rendered with `✓`/`✗`. "Regression: +N vulnerabilities" is a simple count of categories that flipped from `✓` to `✗`. This is pure data comparison over two archive files — no model calls involved, so it stays fast and doesn't depend on a live API to render.

---

## 8. Product Surface

### 8.1 GitHub Action
```yaml
# .github/workflows/safety-check.yml
name: Safety Regression Check
on: [push, pull_request]
jobs:
  safety:
    runs-on: ubuntu-latest
    steps:
      - uses: your-org/your-action@v1
        with:
          target_model: ${{ secrets.MODEL_ENDPOINT }}
          config: config.yaml
```
One file, dropped into a real repo. This is the artifact that makes the product feel installable, not just demoable.

### 8.2 CLI
```
run       # execute a discovery run against a target
diff       # compare two archived runs → Safety Diff
report      # render the Safety Diff as markdown
replay <id>  # re-run a specific stored attack and show the trace
```

### 8.3 Config file (internal use — not a feature to showcase)
```yaml
target_model: your-model-endpoint
judge_model: your-judge-model
risk_categories: [roleplay_bypass, prompt_injection, multi_turn_escalation, tool_misuse]
```
Keep this for your own convenience; it doesn't need to be part of what you show people.

---

## 9. Feature Set — What to Build vs. What to Cut

### ✅ Build (the full product, in priority order)

1. **Discovery loop** — attacker ↔ target ↔ judge, iterating per seed category.
2. **Vulnerability archive** — every attempt logged.
3. **Regression engine** — category-level ✓/✗ diff between two runs.
4. **The Safety Diff view (§5)** — the product's signature screen; the best design effort goes here.
5. **Replay attack** — click a flipped `✗` line, see prompt → response → judge explanation in sequence.
6. **Root cause label** — one short tag at the end of the replay:
   ```
   Root Cause
        ↓
   Roleplay Bypass
   ```
   That's the whole feature — a label, not a paragraph of remediation advice. A label is something people remember; advice text is not.
7. **GitHub Action** — a real `.yml` in a real repo, wired to your CLI, that actually fails a real build and shows the Safety Diff in the check output.

### 🧩 Add only once 1–7 are solid, with time and appetite to spare

- **CI markdown report + auto PR comment** — render the Safety Diff itself as the PR comment body. Reuses a view you've already built; reads as very polished because it mimics tools people already trust (Codecov, Dependabot).
- **Replay against a fixed/patched model** — same attack, old model shows `✗`, patched model shows `✓`, in the same Safety Diff format. The single highest-impact addition, and it costs nothing new since it's the same view already built.
- **Heatmap** — category × attack-style grid, color-coded. Only worth adding if the Safety Diff and replay flow are already finished; it's a secondary view, not a replacement for the Safety Diff.

### ❌ Deliberately left out

| Cut | Why |
|---|---|
| Suggested Fix as a shown feature | Even a simple lookup table of remediation text doesn't stick the way a clean label does; a Root Cause tag replaces it |
| Attack tree visualization | Visually interesting, doesn't add to the product story |
| Vulnerability cards (CVE-style) | Adds polish, not functionality |
| Severity weighting (Critical/High/Medium/Low) | Plain **Success/Fail** per category is all the Safety Diff needs — weighting adds a whole judgment call (how much is "Critical" worth?) without adding clarity |
| Configuration file as a demo moment | Useful internally, not worth screen time |
| Multiple simultaneous visualizations (timeline, cards, charts, attack tree, heatmap all at once) | Pick one signature screen. Everything else is a secondary, optional add |

A product with one sharp, memorable screen and a working end-to-end loop reads as more credible than one juggling five half-built visuals.

---

## 10. The Realistic Shortcut: Don't Necessarily Fine-Tune a Model Yourself

Training a real checkpoint and waiting on a fine-tuning job is one of the biggest time risks in building this. Two honest ways around it:

- **Option A:** use two *existing* models as "v1" and "v2" — e.g. a base instruction-tuned model vs. the same model wrapped with a weaker system prompt, or a smaller/older checkpoint with known weaker refusal behavior. You're genuinely diffing two real models; you're just not the one who trained the weaker one.
- **Option B:** do a small, fast fine-tune on a tiny dataset (a few hundred roleplay examples) against a small open model, with Option A ready as a fallback if the run doesn't behave as expected.

State plainly which one you did. It doesn't weaken the pitch — the product is about the *regression check*, not about how the vulnerability got introduced.

---

## 11. How to Build It — Tech Stack

Keep the stack boring. The interesting part of this product is the regression/diff logic, not the infrastructure around it.

| Layer | Choice | Why |
|---|---|---|
| Attacker + judge model calls | One LLM API, two different system prompts | Reuse one client for both roles |
| Target model | A small open-weight model, local or hosted | Fast to iterate against, cheap to produce a "weaker" variant of |
| Discovery loop | Plain Python, no agent framework | The loop is simple: generate → query → judge → refine; a framework adds risk without adding speed |
| Archive | JSON files or SQLite | Zero setup, still gives you diff, replay, and reporting for free |
| Regression engine | Pure Python over the archive | No model calls needed — fast and doesn't depend on a live API to render |
| GitHub Action | A `Dockerfile` + `action.yml` wrapping the CLI | The Action shells out to the CLI and parses its exit code |
| CLI | `click` or `argparse` | Thin wrapper over the same functions the Action calls |
| Report / PR comment | Markdown generation + the GitHub REST API | No custom UI needed — GitHub renders the markdown |
| Safety Diff / heatmap | A minimal static HTML page (or a single React component) reading the archive JSON directly | No backend needed for the visual layer |

### Implementation order
1. Discovery loop in isolation — one seed prompt, attacker → target → judge, print pass/fail.
2. Wrap it to run a full battery across seed categories, storing every attempt in the archive.
3. Build the regression engine as pure archive math — load two run files, produce the category ✓/✗ table. This one function is the actual product.
4. Wrap the CLI (`run`, `diff`, `report`, `replay`).
5. Wrap the GitHub Action — a `Dockerfile` + `action.yml` that calls `run` then `diff`, exiting non-zero on regression.
6. Add the PR comment step — POST the Safety Diff markdown to the PR via the GitHub API.
7. Only once 1–6 work end-to-end, consider the optional adds from §9 (replay-against-fixed-model, heatmap).

---

## 12. Build Phases

**Phase 1 — Validate**
Lock the one-sentence pitch, the single target user, and the user journey (§6). Don't start building until these three fit on an index card.

**Phase 2 — Core Engine**
Discovery loop working end-to-end against a real target → vulnerability archive → regression engine producing a correct Safety Diff between two real runs.

**Phase 3 — Productize**
CLI wrapper → GitHub Action that actually fails a real build on a real `git push` → Safety Diff rendered in the check output.

**Phase 4 — Differentiators**
Replay view + root cause label. If time and appetite remain: PR comment, replay-against-fixed-model, heatmap — in that order, since each reuses work already done.

**Phase 5 — Polish and Rehearse**
Consistent presentation of the Safety Diff view (this is the screen carrying the whole pitch), a README with an architecture diagram, an example repo pre-loaded with a real "v1 vs v2" pair so a live run never depends on something training correctly on the spot, and a full rehearsal of the demo flow with a cached fallback run in case a live API call is slow or fails.

---

## 13. Demo Flow

| Beat | What happens | Why it lands |
|---|---|---|
| Hook | "Every team fine-tuning an open model can silently break its own safety guardrails. Nobody finds out until it's public. This is the CI check that catches it first." | Frames the gap before any tech is shown |
| Setup | Show the real `.yml` in a real repo | Proves installability, not just capability |
| Push | `git push` → Action triggers | The "just like real CI" moment |
| Discovery, live | Loop runs against the target, building the archive in real time | Visual and genuinely happening, not a mockup |
| The gate | Safety Diff renders: checkmarks flip to X's, `Regression: +N vulnerabilities`, CI shows ❌ FAILED | The money shot — looks exactly like a failed unit test |
| Replay + fix | Click a flipped line → replay the exact attack → Root Cause label → fix applied | Demonstrates the full loop, not just detection |
| Green build | Re-run → Safety Diff shows all ✓ again → ✅ PASSED | Satisfying close, reinforces the CI mental model on the way out |

---

## 14. Honest Limitations (state these before anyone asks)

- Detection quality is bounded by the judge model — its verdicts are treated as a strong signal, not ground truth.
- A category counts as "broken" if any attack within it succeeds — a simple, defensible rule, not a formal severity model.
- This tests the model/checkpoint itself; a team running a separate runtime safety layer would use this alongside it, not instead of it.
- The "v1 vs v2" pair used in any demo should be described plainly — whether it's a real fine-tune or two existing models chosen to show a real behavior gap.

---

## 15. Readiness Checklist

- [ ] One-sentence pitch, no hedging
- [ ] One named target user, everything built for them
- [ ] The Safety Diff view works, looks clean, and is the first thing shown after the gate fails
- [ ] Real GitHub Action, real repo, real pass/fail
- [ ] Discovery loop actually running, not canned
- [ ] Regression comparison between two real model behaviors
- [ ] Replay view: prompt → response → judge → Root Cause label (no remediation text shown)
- [ ] A fallback cached run ready in case a live API call fails during a demo
- [ ] Full demo flow rehearsed end to end

---

## 16. The Close

> "We're not pitching a smarter jailbreak generator. We're pitching the missing regression test — the thing that turns 'we hope this fine-tune didn't break anything' into a Safety Diff you can read in two seconds."
