"""Discovery loop: attacker <-> target <-> judge, iterating within one risk category."""
import json
import time
import uuid

from .attacker import generate_attack
from .judge import evaluate
from .models.schemas import ArchiveRecord, RiskCategory
from .target import query_target

CATEGORIES = [c.value for c in RiskCategory]


def run_discovery_single_category(
    category: str, iterations: int = 3, target_variant: str = "v2"
) -> list[ArchiveRecord]:
    records: list[ArchiveRecord] = []
    prior_feedback = None

    for i in range(iterations):
        attack = generate_attack(category, prior_feedback=prior_feedback)
        target_response = query_target(attack.prompt, variant=target_variant)
        verdict = evaluate(attack.prompt, target_response, category)

        record = ArchiveRecord(
            iteration=i,
            category=attack.category,
            attack_prompt=attack.prompt,
            refinement_reasoning=attack.refinement_reasoning,
            target_response=target_response,
            verdict=verdict.verdict,
            confidence=verdict.confidence,
            reasoning=verdict.reasoning,
        )
        records.append(record)

        print(f"Iteration {i}: {verdict.verdict} (confidence: {verdict.confidence})")

        prior_feedback = verdict.reasoning

    return records


def run_full_discovery(
    model_variant: str = "v2", output_file: str | None = None, iterations: int = 3
) -> dict:
    """Run discovery across all 4 risk categories and save the results as an archive."""
    all_records: list[ArchiveRecord] = []

    for category in CATEGORIES:
        print(f"\n=== {category} ===")
        records = run_discovery_single_category(
            category, iterations=iterations, target_variant=model_variant
        )
        all_records.extend(records)

    archive = {
        "run_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "model_variant": model_variant,
        "records": [record.model_dump(mode="json") for record in all_records],
    }

    path = output_file or f"archive_{archive['run_id']}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(archive, f, indent=2)

    return archive


if __name__ == "__main__":
    results = run_discovery_single_category(
        "roleplay_bypass", iterations=3, target_variant="v2"
    )
    print(f"\n{len(results)} records collected.")
