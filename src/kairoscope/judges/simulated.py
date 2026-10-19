"""SimulatedJudge: a noisy ground-truth judge for tests and benchmarks.

Answers ground truth (``frame >= truth``) but flips with probability
``base_error + near_error * exp(-abs(frame - truth) / near_scale)``, seeded.
This mirrors real models, which are most confused right at the event.
"""

from __future__ import annotations

from collections.abc import Sequence

from PIL import Image

from kairoscope.judges.base import Answer


class SimulatedJudge:
    """Deterministic (seeded) noisy judge; never calls a real API.

    Example:
        >>> judge = SimulatedJudge(truth=437, base_error=0.05, near_error=0.25, seed=7)
    """

    def __init__(
        self,
        truth: int,
        *,
        base_error: float = 0.05,
        near_error: float = 0.25,
        near_scale: float = 10.0,
        seed: int = 0,
    ) -> None:
        self.truth = truth
        self.base_error = base_error
        self.near_error = near_error
        self.near_scale = near_scale
        self.seed = seed

    def ask(self, images: Sequence[Image.Image], prompt: str) -> Answer:
        """Answer from ground truth with distance-dependent noise."""
        raise NotImplementedError

    def ask_frame(self, frame: int) -> Answer:
        """Answer for a bare frame index (used by simulations without decoding)."""
        raise NotImplementedError
