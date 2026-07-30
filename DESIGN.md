# Design

<!-- impeccable:design-schema 1 -->

## World

Security-scanner artifact — GitHub Security tab / terminal output / Snyk-Sentry severity-dashboard lineage. Brief-pinned by the user; executed at full fidelity, not its softest rendition. Explicitly rejects: purple-blue gradients, glassmorphism, one-font-does-everything, rounded-2xl soft-shadow cards, centered single-card-on-dark-void landing-page layout.

## Layout

Full-width, left-aligned, information-dense — a log/dashboard, not a hero card. No centered floating card with drop shadow. A terminal-style chrome bar (prompt-style breadcrumb) opens each page to read as tool output, not a marketing surface. Regions are separated by 1px hairline borders, not shadow or blur.

## Color Strategy

Restrained: near-black terminal ground + muted neutrals, with exactly one saturated signal color reserved for regression/fail states (a hot vermillion, not a generic Tailwind red-500). Pass states stay quiet/desaturated so the one alarm color carries all the meaning. Color is a severity signal, not decoration.

## Type

Two-family contrast, both system stacks (zero external font requests, per the offline-artifact constraint):
- Headers/labels: system sans, treated with weight/tracking for character (not the same stack used for data).
- Data (category names, IDs, timestamps, code/log content): monospace stack (Consolas/SF Mono/Menlo/Cascadia Code/Courier New).

## Shape

Sharp — 0-2px border-radius throughout. No soft/glow shadows. Severity badges are rectangular tags (solid fill or left-border accent), not pills.

## Motion

Entrance/stagger animations on rows and sections, disabled under `prefers-reduced-motion: reduce`. Motion supports scanning (draws the eye to what changed), never decorative.

## Constraints

Inline CSS only, no external fonts/scripts/CDNs — must render identically as an offline CI artifact. All model-generated content (attack prompts, responses, judge reasoning) is HTML-escaped before display; this is a security requirement and is never traded for a visual effect.
