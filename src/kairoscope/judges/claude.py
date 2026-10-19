"""ClaudeJudge: judges frames with the Anthropic API.

Requires the ``claude`` extra: ``pip install "kairoscope[claude]"``.
Calls use bounded retries with exponential backoff; API errors are never swallowed.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from PIL import Image

from kairoscope.judges.base import Answer

try:
    import anthropic  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "ClaudeJudge requires the 'claude' extra: pip install 'kairoscope[claude]'"
    ) from exc

logger = logging.getLogger("kairoscope")

DEFAULT_MODEL = "claude-sonnet-5-5"
MAX_RETRIES = 4


class ClaudeJudge:
    """A judge backed by an Anthropic vision model.

    Example:
        >>> judge = ClaudeJudge(model="claude-sonnet-5-5")
        >>> answer = judge.ask(frames, "Has the ball left the shooter's hands?")
    """

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        raise NotImplementedError("ClaudeJudge is not implemented yet (v0.1 scaffolding)")

    def ask(self, images: Sequence[Image.Image], prompt: str) -> Answer:
        """Send base64-encoded frames and parse a JSON yes/no answer."""
        raise NotImplementedError
