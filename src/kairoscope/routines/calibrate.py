"""calibrate: find the cheapest sampling profile whose answers still agree.

Takes reference answers at full quality, then tries progressively cheaper configs
(fps, resolution, crop, dedupe) and returns the cheapest :class:`Profile` whose
answers agree with the reference at or above a target rate (default 0.95).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from kairoscope.cost import Cost
from kairoscope.judges.base import Judge
from kairoscope.video import Video

logger = logging.getLogger("kairoscope")

DEFAULT_AGREEMENT = 0.95


@dataclass(frozen=True)
class Profile:
    """A sampling configuration measured to be good enough for a task."""

    fps: float
    size: tuple[int, int] | None
    crop: tuple[int, int, int, int] | None
    dedupe: bool
    agreement: float

    def to_json(self) -> str:
        """Serialize to JSON."""
        raise NotImplementedError

    @classmethod
    def from_json(cls, data: str) -> Profile:
        """Deserialize from JSON produced by :meth:`to_json`."""
        raise NotImplementedError


@dataclass(frozen=True)
class CalibrateResult:
    """The cheapest acceptable profile, and what the search cost."""

    profile: Profile
    calls: int
    cost: Cost


def calibrate(
    video: Video,
    judge: Judge,
    prompts: list[str],
    *,
    target_agreement: float = DEFAULT_AGREEMENT,
) -> CalibrateResult:
    """Measure the cheapest profile that still answers `prompts` correctly.

    Example:
        >>> result = ks.calibrate(video, judge, ["Is the ball in the air?"])
        >>> result.profile.to_json()
    """
    raise NotImplementedError("calibrate is not implemented yet (v0.1 scaffolding)")
