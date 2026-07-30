"""CLI wrapper: run, diff, report, replay — thin wrappers over discovery.py
and regression.py, per complete-build-roadmap.md Phase 3."""
from .utils import ensure_utf8_stdout

ensure_utf8_stdout()  # must run before any print() that might emit ✓/✗

import json  # noqa: E402
import sys  # noqa: E402

import click  # noqa: E402

from .discovery import run_full_discovery  # noqa: E402
from .models.schemas import RiskCategory  # noqa: E402
from .regression import print_safety_diff, produce_safety_diff  # noqa: E402

ROOT_CAUSES = {
    "roleplay_bypass": "Roleplay Bypass",
    "prompt_injection": "Prompt Injection",
    "multi_turn_escalation": "Multi-turn Escalation",
    "tool_misuse": "Tool Misuse",
}


@click.group()
def cli():
    pass


@cli.command()
@click.option(
    "--variant",
    type=click.Choice(["v1", "v2"]),
    default="v2",
    help="Target model variant (v1 = strong safety prompt, v2 = weak).",
)
@click.option("--output", default=None, help="Archive output file")
def run(variant, output):
    """Execute a full discovery run across all 4 risk categories."""
    print(f"Running discovery against {variant}...")
    archive = run_full_discovery(model_variant=variant, output_file=output)
    print(f"Archive saved: {output or archive['run_id']}")


@cli.command()
@click.argument("archive_v1", type=click.Path(exists=True))
@click.argument("archive_v2", type=click.Path(exists=True))
def diff(archive_v1, archive_v2):
    """Compare two archives, produce the Safety Diff."""
    with open(archive_v1, encoding="utf-8") as f:
        a1 = json.load(f)
    with open(archive_v2, encoding="utf-8") as f:
        a2 = json.load(f)

    result = produce_safety_diff(a1, a2)
    print_safety_diff(result)
    sys.exit(0 if result["passed"] else 1)


@cli.command()
@click.argument("archive", type=click.Path(exists=True))
def report(archive):
    """Render an archive as a markdown summary: attacks and success rate per category."""
    with open(archive, encoding="utf-8") as f:
        data = json.load(f)

    print("# Safety Report\n")
    print(f"Run ID: {data['run_id']}")
    print(f"Timestamp: {data['timestamp']}")
    print(f"Model: {data['model_variant']}\n")

    by_category = {}
    for record in data["records"]:
        by_category.setdefault(record["category"], []).append(record)

    for category in [c.value for c in RiskCategory]:
        records = by_category.get(category, [])
        total = len(records)
        succeeded = sum(1 for r in records if r["verdict"] == "fail")
        rate = f"{succeeded / total:.0%}" if total else "n/a"
        print(f"## {category}\n")
        print(f"Attacks: {total}, Successful: {succeeded}, Success rate: {rate}\n")


@cli.command()
@click.argument("archive", type=click.Path(exists=True))
@click.argument("attack_index", type=int)
def replay(archive, attack_index):
    """Replay a specific attack: prompt, response, verdict, and Root Cause label."""
    with open(archive, encoding="utf-8") as f:
        data = json.load(f)

    record = data["records"][attack_index]
    print(f"\n=== REPLAY: {record['category']} (iteration {record['iteration']}) ===\n")
    print(f"Attack:\n{record['attack_prompt']}\n")
    print(f"Response:\n{record['target_response']}\n")
    print(f"Verdict: {record['verdict'].upper()}")
    print(f"Confidence: {record['confidence']}")
    print(f"Judge reasoning: {record['reasoning']}\n")
    print(f"Root Cause: {ROOT_CAUSES.get(record['category'], 'Unknown')}")


if __name__ == "__main__":
    cli()
