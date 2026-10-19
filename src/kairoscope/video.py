"""Video access: PyAV decoding, keyframe seeking, bounded frame caching, context strips.

The container stays open between reads. Seeks go to the nearest keyframe and decode
forward; frames are scaled during decode and LRU-cached with bounded memory. Never
reopen or re-decode the video per frame.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from PIL import Image

logger = logging.getLogger("kairoscope")


class Video:
    """A video file opened once, read many times.

    Example:
        >>> video = Video("game.mp4")
        >>> frame = video.frame(437, size=(640, 360))
        >>> strip = video.strip(437, offsets=(-6, -3, 0, 3, 6))
    """

    def __init__(self, path: str | Path, *, max_cached_frames: int = 256) -> None:
        self._path = Path(path)
        self._max_cached_frames = max_cached_frames
        raise NotImplementedError("Video is not implemented yet (v0.1 scaffolding)")

    @property
    def fps(self) -> float:
        """Average frames per second."""
        raise NotImplementedError

    @property
    def frame_count(self) -> int:
        """Total number of frames."""
        raise NotImplementedError

    @property
    def duration(self) -> float:
        """Duration in seconds."""
        raise NotImplementedError

    def frame(self, i: int, *, size: tuple[int, int] | None = None) -> Image.Image:
        """Decode frame `i`, scaled to `size` (width, height) during decode."""
        raise NotImplementedError

    def frames(
        self, indices: Sequence[int], *, size: tuple[int, int] | None = None
    ) -> list[Image.Image]:
        """Decode several frames in one forward pass where possible."""
        raise NotImplementedError

    def strip(
        self, center: int, offsets: Sequence[int], *, size: tuple[int, int] | None = None
    ) -> list[Image.Image]:
        """Frames at `center + offset` for each offset, clamped to the video bounds."""
        raise NotImplementedError
