"""Cost tracking: per-call records, pricing, token estimates, and ledger aggregation.

Every model call records images, image dimensions, input/output tokens (from the API
response when available), latency, and estimated dollars. Prices come from
``pricing.json``; each entry carries a source URL and date, never invented.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("kairoscope")


@dataclass(frozen=True)
class Cost:
    """Aggregate cost of one or more model calls."""

    images: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    dollars: float = 0.0


@dataclass(frozen=True)
class CallRecord:
    """One model call, as recorded by a judge."""

    routine: str
    model: str
    images: int
    image_dims: tuple[tuple[int, int], ...]
    input_tokens: int | None
    output_tokens: int | None
    latency_s: float
    dollars: float


class CostLedger:
    """Aggregates call records per routine.

    Example:
        >>> ledger = CostLedger()
        >>> ledger.total().dollars
    """

    def __init__(self) -> None:
        self._records: list[CallRecord] = []

    def record(self, rec: CallRecord) -> None:
        """Append one call record."""
        raise NotImplementedError

    def total(self, routine: str | None = None) -> Cost:
        """Aggregate cost, optionally filtered to one routine."""
        raise NotImplementedError


def load_pricing() -> dict[str, object]:
    """Load per-provider/model prices bundled as ``pricing.json``."""
    raise NotImplementedError


def estimate_tokens(width: int, height: int) -> int:
    """Estimate input tokens for one image; hosted APIs price by pixel dimensions."""
    raise NotImplementedError
