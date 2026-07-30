"""HTML rendering for the Safety Diff and attack replay views — the
product's signature screens (ai-safety-regression-testing-guide.md §5, §9).
Inline CSS only, no external dependencies, so these render as static files
with nothing else to fetch.
"""
from html import escape

ROOT_CAUSES = {
    "roleplay_bypass": "Roleplay Bypass",
    "prompt_injection": "Prompt Injection",
    "multi_turn_escalation": "Multi-turn Escalation",
    "tool_misuse": "Tool Misuse",
}


def render_safety_diff_html(diff_result: dict, output_file: str = "safety_diff.html") -> str:
    """Render the Safety Diff as a clean, static HTML page."""
    diff = diff_result["diff"]
    regression_count = diff_result["regression_count"]

    rows = []
    for category, row in diff.items():
        v1_class = "check" if row["v1"] == "✓" else "cross"
        v2_class = "check" if row["v2"] == "✓" else "cross"
        tr_class = "regression" if row["regression"] else ""
        marker = " &larr; REGRESSION" if row["regression"] else ""
        rows.append(
            f"""
            <tr class="{tr_class}">
                <td class="category">{escape(category)}</td>
                <td class="{v1_class}">{row['v1']}</td>
                <td class="{v2_class}">{row['v2']}{marker}</td>
            </tr>"""
        )

    if regression_count == 0:
        summary = '<div class="summary passed">&#10003; PASSED: No regressions detected</div>'
    else:
        summary = (
            f'<div class="summary failed">&#10007; REGRESSION: '
            f"+{regression_count} vulnerabilities</div>"
        )

    html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Safety Diff</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 40px; background: #f5f5f5; }}
    .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    h1 {{ margin: 0 0 30px 0; font-size: 28px; font-weight: 600; }}
    .diff-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
    .diff-table th {{ text-align: left; padding: 12px; background: #f0f0f0; font-weight: 600; font-size: 13px; text-transform: uppercase; }}
    .diff-table td {{ padding: 12px; border-bottom: 1px solid #eee; font-family: Consolas, Monaco, monospace; font-size: 14px; }}
    .category {{ font-weight: 500; }}
    .check {{ color: #10b981; font-weight: bold; }}
    .cross {{ color: #ef4444; font-weight: bold; }}
    .regression {{ background: #fef2f2; }}
    .summary {{ margin-top: 20px; padding: 16px; border-radius: 4px; font-weight: 600; }}
    .passed {{ background: #ecfdf5; color: #047857; border-left: 4px solid #10b981; }}
    .failed {{ background: #fef2f2; color: #dc2626; border-left: 4px solid #ef4444; }}
</style>
</head>
<body>
<div class="container">
<h1>Safety Diff</h1>
<table class="diff-table">
<tr><th>Category</th><th>v1</th><th>v2</th></tr>
{"".join(rows)}
</table>
{summary}
</div>
</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_doc)

    return output_file


def render_replay_html(record: dict, output_file: str = "replay.html") -> str:
    """Render a single attack replay (prompt, response, verdict, Root Cause) as HTML."""
    verdict = record["verdict"]
    verdict_color = "#ef4444" if verdict == "fail" else "#10b981"
    verdict_bg = "#fef2f2" if verdict == "fail" else "#ecfdf5"
    root_cause = ROOT_CAUSES.get(record["category"], "Unknown")

    html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Attack Replay</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; padding: 40px; background: #f5f5f5; }}
    .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    h1 {{ margin: 0 0 30px 0; font-size: 24px; font-weight: 600; }}
    .section {{ margin-bottom: 30px; }}
    .section h2 {{ font-size: 16px; font-weight: 600; margin-bottom: 12px; text-transform: uppercase; color: #6b7280; }}
    pre {{ background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; font-family: Consolas, Monaco, monospace; font-size: 13px; }}
    .verdict {{ padding: 16px; border-radius: 4px; background: {verdict_bg}; color: {verdict_color}; font-weight: 600; margin-bottom: 20px; }}
    .root-cause {{ padding: 12px; background: #fef3c7; border-left: 4px solid #f59e0b; font-weight: 500; }}
</style>
</head>
<body>
<div class="container">
<h1>Attack Replay: {escape(record['category'])}</h1>
<div class="verdict">{escape(verdict.upper())} (confidence: {escape(record['confidence'])})</div>
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
</div>
</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_doc)

    return output_file
