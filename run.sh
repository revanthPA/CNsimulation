#!/usr/bin/env bash
# =============================================================================
# run.sh - Convenience wrapper for the Energy-Aware Routing Protocol simulator
#
# Usage:
#   ./run.sh <command> [options]
#
# Commands:
#   run [config]          Run a single simulation (default: configs/base.yaml)
#   experiment [name]     Run a routing comparison experiment
#   list                  List available experiments
#   test                  Run the full test suite
#   sensitivity [scenario] Run a sensitivity study scenario
#   help                  Show this help message
# =============================================================================

set -euo pipefail

# Repository root (directory containing this script)
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

# Activate virtual environment if it exists
if [[ -d .venv ]]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

PYTHON="python"

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
show_help() {
    cat <<EOF
Usage: ./run.sh <command> [options]

Commands:
  run [config]            Run a single simulation
                          Default config: configs/base.yaml
  experiment [name]       Run a routing comparison experiment
                          Default name: routing_comparison
  list                    List available experiments
  test                    Run the full test suite (pytest)
  gui                     Launch the interactive Streamlit GUI
  sensitivity [scenario]  Run a sensitivity study scenario
                          Use 'all' for all scenarios (slow)
  help                    Show this help message

Examples:
  ./run.sh gui                              # Launch interactive web GUI
  ./run.sh run                              # Single simulation with base config
  ./run.sh run configs/small.yaml           # Small network (20 nodes)
  ./run.sh experiment                       # Routing comparison (5 seeds)
  ./run.sh experiment routing_comparison    # Named experiment
  ./run.sh list                             # List experiments
  ./run.sh test                             # Run all tests
  ./run.sh sensitivity net_size_20          # One sensitivity scenario
  ./run.sh sensitivity all                  # All sensitivity scenarios

Output is written to the results/ directory.
EOF
}

# ---------------------------------------------------------------------------
# Command dispatch
# ---------------------------------------------------------------------------
COMMAND="${1:-help}"
shift || true

case "$COMMAND" in
    run)
        CONFIG="${1:-configs/base.yaml}"
        echo "=== Running single simulation: $CONFIG ==="
        $PYTHON -m energy_routing.main run --config "$CONFIG"
        ;;

    experiment)
        NAME="${1:-routing_comparison}"
        echo "=== Running experiment: $NAME ==="
        $PYTHON -m energy_routing.main experiment --name "$NAME" --base-config configs/base.yaml
        ;;

    list)
        echo "=== Available experiments ==="
        $PYTHON -m energy_routing.main list-experiments
        ;;

    test)
        echo "=== Running test suite ==="
        $PYTHON -m pytest tests/ -q
        ;;

    sensitivity)
        SCENARIO="${1:-all}"
        echo "=== Sensitivity study: $SCENARIO ==="
        if [[ "$SCENARIO" == "all" ]]; then
            $PYTHON scripts/sensitivity_study.py
        else
            $PYTHON scripts/sensitivity_study.py "$SCENARIO"
        fi
        ;;

    gui)
        echo "=== Launching Streamlit GUI ==="
        $PYTHON -m streamlit run src/energy_routing/dashboard.py
        ;;

    help|--help|-h|*)
        show_help
        ;;
esac