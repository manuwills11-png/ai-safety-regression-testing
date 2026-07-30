"""HTML rendering for the Safety Diff and attack replay views — the
product's signature screens (ai-safety-regression-testing-guide.md §5, §9).

DIRECTION CONTRACT (see DESIGN.md for the durable rules)
THESIS: this is a CI security-finding artifact, not a demo card — it refuses
  the centered-hero-on-dark-void "AI tool" template.
OWN-WORLD: GitHub Security tab / terminal output / Snyk-Sentry severity
  dashboard. Near-black ground, one reserved signal color (vermillion) for
  regressions, everything else quiet. Sharp edges, hairline borders, no
  soft shadows or glass. Left-aligned, full-width log layout, not a
  floating card.
STORY: an engineer who just got paged by a red CI check scans this in
  seconds and knows exactly what broke and why.
FIRST VIEWPORT: a terminal-style chrome bar, then an eyebrow + h1, then the
  full-width category table with the regressions immediately visible via
  the one reserved color; summary verdict anchors the bottom.
FORM: brief-pinned (GitHub Security / terminal / Snyk-Sentry), executed at
  full fidelity per the user's explicit creative brief.

Inline CSS only, no external dependencies, so these render as static files
with nothing else to fetch. Entrance/stagger animations, disabled under
prefers-reduced-motion. All model-generated content is HTML-escaped before
display — a security requirement, never traded for a visual effect.
"""
from html import escape

ROOT_CAUSES = {
    "roleplay_bypass": "Roleplay Bypass",
    "prompt_injection": "Prompt Injection",
    "multi_turn_escalation": "Multi-turn Escalation",
    "tool_misuse": "Tool Misuse",
}

# Shared system so the two pages read as one tool, not two demos. Three
# distinct type roles for real contrast: a grotesk sans for headers, the
# native UI sans for labels/body, monospace for all data. System stacks
# only — no external font requests, per the offline-artifact constraint.
_BASE_STYLE = """
    * { box-sizing: border-box; }
    :root {
        --bg: #0a0e14;
        --surface: #0d1117;
        --surface-raised: #11161d;
        --border: #21262d;
        --border-strong: #30363d;
        --text: #c9d1d9;
        --text-bright: #e6edf3;
        --text-muted: #6e7681;
        --pass: #5a8f6e;
        --signal: #ff4d2e;
        --signal-dim: rgba(255, 77, 46, 0.1);
        --amber: #d29922;
        --font-head: Arial, Helvetica, sans-serif;
        --font-ui: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        --font-mono: ui-monospace, 'Cascadia Code', 'SF Mono', Consolas, 'Courier New', monospace;
    }
    body {
        font-family: var(--font-ui);
        margin: 0; padding: 0;
        background: var(--bg); color: var(--text);
        font-size: 14px;
    }
    .term-bar {
        display: flex; align-items: center; gap: 10px;
        padding: 8px 20px; background: var(--surface);
        border-bottom: 1px solid var(--border);
    }
    .term-dot { width: 9px; height: 9px; border-radius: 50%; background: var(--border-strong); }
    .term-dot.r { background: #ff5f57; } .term-dot.y { background: #ffbd2e; } .term-dot.g { background: #28c840; }
    .term-prompt { font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); margin-left: 6px; }
    .term-prompt .cmd { color: var(--text); }
    main.report {
        max-width: 980px; margin: 0; padding: 36px 40px 60px;
        opacity: 0; animation: pageIn 0.3s ease-out forwards;
    }
    .eyebrow {
        font-family: var(--font-ui); font-size: 11px; font-weight: 700;
        letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-muted);
        margin-bottom: 8px;
    }
    h1 {
        font-family: var(--font-head); font-weight: 800; letter-spacing: -0.01em;
        font-size: 28px; margin: 0 0 10px 0; color: var(--text-bright);
    }
    .meta-row {
        font-family: var(--font-mono); font-size: 12px; color: var(--text-muted);
        margin-bottom: 28px; padding-bottom: 20px; border-bottom: 1px solid var(--border);
    }
    .meta-row b { color: var(--text); font-weight: 600; }
    .tag {
        display: inline-block; padding: 1px 7px; border-radius: 2px;
        font-family: var(--font-mono); font-size: 10px; font-weight: 700;
        letter-spacing: 0.06em; text-transform: uppercase; vertical-align: middle;
        border: 1px solid currentColor;
    }
    .tag-fail { color: var(--signal); background: var(--signal-dim); }
    .tag-pass { color: var(--pass); background: rgba(90, 143, 110, 0.1); }
    @keyframes pageIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes rowIn { from { opacity: 0; transform: translateX(-4px); } to { opacity: 1; transform: translateX(0); } }
    @keyframes flashSignal {
        0%, 100% { background: var(--signal-dim); }
        50% { background: rgba(255, 77, 46, 0.22); }
    }
    @media (prefers-reduced-motion: reduce) {
        main.report, .diff-table tr, .summary, .section, .verdict-row, .root-cause {
            animation: none !important; opacity: 1 !important;
        }
    }
"""


def render_safety_diff_html(diff_result: dict, output_file: str = "safety_diff.html") -> str:
    """Render the Safety Diff as a dark, dense, security-scanner-style HTML page."""
    diff = diff_result["diff"]
    regression_count = diff_result["regression_count"]
    total = len(diff)

    rows = []
    for i, (category, row) in enumerate(diff.items()):
        v1_class = "check" if row["v1"] == "✓" else "cross"
        v2_class = "check" if row["v2"] == "✓" else "cross"
        delay = i * 70
        if row["regression"]:
            tr_class = "regression"
            style = f"animation-delay:{delay}ms, {550 + delay}ms"
        else:
            tr_class = ""
            style = f"animation-delay:{delay}ms"
        badge = ' <span class="tag tag-fail">Regression</span>' if row["regression"] else ""
        rows.append(
            f"""
            <tr class="{tr_class}" style="{style}">
                <td class="cell-category">{escape(category)}</td>
                <td class="cell-mark {v1_class}">{row['v1']}</td>
                <td class="cell-mark {v2_class}">{row['v2']}{badge}</td>
            </tr>"""
        )

    if regression_count == 0:
        summary = '<div class="summary passed"><span class="tag tag-pass">Pass</span> No regressions detected across %d categories</div>' % total
    else:
        summary = (
            '<div class="summary failed">'
            f'<span class="tag tag-fail">Fail</span> +{regression_count} regression'
            f'{"s" if regression_count != 1 else ""} detected — build blocked'
            "</div>"
        )

    html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Safety Diff</title>
<style>
{_BASE_STYLE}
    .diff-table {{ width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 13px; }}
    .diff-table th {{
        font-family: var(--font-ui);
        text-align: left; padding: 8px 12px; background: var(--surface);
        color: var(--text-muted); font-weight: 700; font-size: 10px;
        text-transform: uppercase; letter-spacing: 0.08em;
        border-top: 1px solid var(--border-strong); border-bottom: 1px solid var(--border-strong);
    }}
    .diff-table td {{ padding: 11px 12px; border-bottom: 1px solid var(--border); }}
    .diff-table tr {{ opacity: 0; animation: rowIn 0.3s ease-out forwards; }}
    .diff-table tr:hover td {{ background: var(--surface); }}
    .cell-category {{ color: var(--text-bright); }}
    .cell-mark {{ font-weight: 700; width: 90px; }}
    .check {{ color: var(--pass); }}
    .cross {{ color: var(--signal); }}
    .regression td {{ border-left: 2px solid var(--signal); }}
    .regression {{ animation: rowIn 0.3s ease-out forwards, flashSignal 1.1s ease-in-out 2; }}
    .summary {{
        margin-top: 22px; padding: 14px 16px; font-family: var(--font-mono); font-size: 13px;
        border: 1px solid var(--border-strong); border-radius: 2px;
        opacity: 0; animation: pageIn 0.3s ease-out 0.3s forwards;
    }}
    .passed {{ color: var(--text); background: var(--surface); }}
    .failed {{ color: var(--text-bright); background: var(--surface); border-color: var(--signal); }}
</style>
</head>
<body>
<div class="term-bar">
    <span class="term-dot r"></span><span class="term-dot y"></span><span class="term-dot g"></span>
    <span class="term-prompt">$ <span class="cmd">safety-diff</span> archive_v1.json archive_v2.json</span>
</div>
<main class="report">
    <div class="eyebrow">Safety Regression Report</div>
    <h1>Safety Diff</h1>
    <div class="meta-row"><b>{total}</b> categories checked &middot; <b>{regression_count}</b> regression{"s" if regression_count != 1 else ""}</div>
    <table class="diff-table">
    <tr><th>Category</th><th>v1</th><th>v2</th></tr>
    {"".join(rows)}
    </table>
    {summary}
</main>
</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_doc)

    return output_file


def render_replay_html(record: dict, output_file: str = "replay.html") -> str:
    """Render a single attack replay (prompt, response, verdict, Root Cause) as HTML."""
    verdict = record["verdict"]
    verdict_tag_class = "tag-fail" if verdict == "fail" else "tag-pass"
    root_cause = ROOT_CAUSES.get(record["category"], "Unknown")

    html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Attack Replay</title>
<style>
{_BASE_STYLE}
    .section {{ margin-bottom: 24px; opacity: 0; animation: rowIn 0.3s ease-out forwards; }}
    .section:nth-of-type(1) {{ animation-delay: 70ms; }}
    .section:nth-of-type(2) {{ animation-delay: 140ms; }}
    .section:nth-of-type(3) {{ animation-delay: 210ms; }}
    .section h2 {{
        font-family: var(--font-ui); font-size: 11px; font-weight: 700;
        margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted);
    }}
    pre {{
        background: var(--surface); border: 1px solid var(--border); border-radius: 2px;
        padding: 12px 14px; margin: 0; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;
        font-family: var(--font-mono); font-size: 13px; line-height: 1.5; color: var(--text-bright);
    }}
    p {{ font-family: var(--font-mono); font-size: 13px; line-height: 1.6; color: var(--text); margin: 0; }}
    .verdict-row {{
        display: flex; align-items: center; gap: 10px;
        padding: 12px 14px; border: 1px solid var(--border-strong); border-radius: 2px;
        font-family: var(--font-mono); font-size: 13px; margin-bottom: 24px; color: var(--text);
        opacity: 0; animation: rowIn 0.3s ease-out forwards;
    }}
    .root-cause {{
        padding: 12px 14px; background: var(--surface); border-left: 2px solid var(--amber);
        font-family: var(--font-mono); font-size: 13px; color: var(--text);
        opacity: 0; animation: rowIn 0.3s ease-out 0.28s forwards;
    }}
    .root-cause strong {{ color: var(--text-bright); }}
</style>
</head>
<body>
<div class="term-bar">
    <span class="term-dot r"></span><span class="term-dot y"></span><span class="term-dot g"></span>
    <span class="term-prompt">$ <span class="cmd">safety-diff replay</span> archive.json --index N</span>
</div>
<main class="report">
    <div class="eyebrow">Attack Replay</div>
    <h1>{escape(record['category'])}</h1>
    <div class="verdict-row">
        <span class="tag {verdict_tag_class}">{escape(verdict.upper())}</span>
        confidence: {escape(record['confidence'])}
    </div>
    <div class="section">
        <h2>Attack</h2>
        <pre>{escape(record['attack_prompt'])}</pre>
    </div>
    <div class="section">
        <h2>Target Response</h2>
        <pre>{escape(record['target_response'])}</pre>
    </div>
    <div class="section">
        <h2>Judge Reasoning</h2>
        <p>{escape(record['reasoning'])}</p>
    </div>
    <div class="root-cause">Root Cause: <strong>{escape(root_cause)}</strong></div>
</main>
</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_doc)

    return output_file
