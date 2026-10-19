"""Judges: vision models that answer yes/no questions about frames.

``ClaudeJudge`` lives in :mod:`kairoscope.judges.claude` and requires the
``kairoscope[claude]`` extra; it is not imported here so the core package
imports without any provider SDK installed.
"""

from kairoscope.judges.base import Answer, Judge
from kairoscope.judges.simulated import SimulatedJudge

__all__ = ["Answer", "Judge", "SimulatedJudge"]
