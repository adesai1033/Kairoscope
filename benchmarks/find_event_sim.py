"""Simulate find_event strategies over long videos with a noisy judge.

Reproduces the plain / vote / verify-and-repair comparison; README numbers for
find_event come only from this script (no real API calls, no decoding).

Usage:
    uv run python benchmarks/find_event_sim.py --trials 2000
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials", type=int, default=2000, help="simulated searches per strategy")
    parser.add_argument("--frames", type=int, default=108_000, help="frames in the simulated video")
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    raise SystemExit(
        f"not implemented yet (v0.1 scaffolding); would run {args.trials} trials "
        f"over {args.frames} frames"
    )


if __name__ == "__main__":
    main()
