"""Judge protocol and Answer result."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from PIL import Image


@dataclass(frozen=True)
class Answer:
    """One judge reply to one question about a set of frames."""

    yes: bool
    reason: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_s: float = 0.0


@runtime_checkable
class Judge(Protocol):
    """Anything that can answer a yes/no prompt about a sequence of images."""

    def ask(self, images: Sequence[Image.Image], prompt: str) -> Answer:
        """Answer `prompt` about `images` (in time order, left to right)."""
        ...
