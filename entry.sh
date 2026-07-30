#!/bin/bash
set -e

VARIANT=${1:-v2}
echo "Running safety regression check (variant: $VARIANT)..."

if [ "$DEMO_MODE" = "1" ]; then
    # Points at the synthetic fixtures (a real regression, checkmarks flip)
    # for the primary demo visual — see DEMO.md. The real live-discovery
    # archives (archive_v1_cached.json / archive_v2_cached.json) stay in
    # examples/ as a secondary "clean deploy" proof point, not the default.
    echo "DEMO_MODE=1: using cached archives instead of live model calls..."
    cp examples/archive_v1_synthetic_test.json archive_v1.json
    cp examples/archive_v2_synthetic_test.json archive_v2.json
    ARCHIVE_V1="archive_v1.json"
else
    if [ -f archive_latest.json ]; then
        echo "Using existing baseline: archive_latest.json"
        ARCHIVE_V1="archive_latest.json"
    else
        echo "No baseline archive found, running v1 discovery..."
        python -m src.cli run --variant v1 --output archive_v1.json
        ARCHIVE_V1="archive_v1.json"
    fi

    echo "Running $VARIANT discovery..."
    python -m src.cli run --variant "$VARIANT" --output archive_v2.json
fi

echo
python -m src.cli report archive_v2.json

echo
python -m src.cli diff "$ARCHIVE_V1" archive_v2.json
