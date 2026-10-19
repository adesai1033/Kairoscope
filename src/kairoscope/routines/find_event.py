"""find_event: bisection with context strips, optional voting, verify-and-repair.

The caller asserts the answer flips exactly once in the window: NO at ``lo`` and
YES at ``hi`` (no calls are spent there). The judge sees a strip of frames around
each midpoint (offsets -6, -3, 0, +3, +6 at 30 fps), tiled in time order with the
judged frame outlined in red.

Verify-and-repair (on by default): after bisection converges on frame ``f``,
re-check ``f - 1`` (expect NO) and ``f`` (expect YES), each with a 3-vote majority
that stops early once decided. On a failed check, step away by doubling distances
until the answer flips, then bisect that bracket; repeat up to ``max_repairs``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from kairoscope.cost import Cost
from kairoscope.judges.base import Judge
from kairoscope.video import Video

logger = logging.getLogger("kairoscope")

DEFAULT_OFFSETS = (-6, -3, 0, 3, 6)
MAX_REPAIRS = 4


@dataclass(frozen=True)
class EventResult:
    """Where the answer flips from NO to YES, and what it cost to find."""

    frame: int
    seconds: float
    calls: int
    cost: Cost


def find_event(
    video: Video,
    judge: Judge,
    *,
    lo: int = 0,
    hi: int | None = None,
    votes: int = 1,
    verify: bool = True,
    max_repairs: int = MAX_REPAIRS,
) -> EventResult:
    """Find the first frame where `judge` answers YES.

    Example:
        >>> result = ks.find_event(video, judge)
        >>> result.seconds, result.calls
    """
    hi = video.frame_count - 1 if hi is None else hi
    if not 0 <= lo < hi < video.frame_count:
        raise ValueError(f"invalid window: lo={lo}, hi={hi}, frames={video.frame_count}")
    logger.debug("find_event window=[%d, %d] votes=%d verify=%s", lo, hi, votes, verify)
    raise NotImplementedError("find_event is not implemented yet (v0.1 scaffolding)")
