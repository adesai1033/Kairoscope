"""Frame sampling: uniform, scene-aware, and near-duplicate dedupe."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from PIL import Image

logger = logging.getLogger("kairoscope")


def uniform(frame_count: int, n: int) -> list[int]:
    """`n` frame indices spread evenly across `[0, frame_count)`."""
    raise NotImplementedError


def dedupe(images: Sequence[Image.Image], *, threshold: float = 0.02) -> list[int]:
    """Indices of frames to keep after dropping near-duplicates.

    Uses downscaled pixel difference (or perceptual hash); greyscale and JPEG
    quality do not reduce tokens, dropping frames does.
    """
    raise NotImplementedError


def scene_aware(frame_count: int, n: int) -> list[int]:
    """`n` frame indices, spending more frames where scenes change."""
    raise NotImplementedError
