"""Smoke tests: the scaffolded package imports and exposes its public API."""

from __future__ import annotations

import kairoscope as ks


def test_public_api() -> None:
    for name in ("Video", "find_event", "calibrate", "Profile", "CostLedger"):
        assert hasattr(ks, name), f"missing public API: {name}"


def test_judges_import_without_provider_sdk() -> None:
    from kairoscope.judges import Answer, Judge, SimulatedJudge

    judge = SimulatedJudge(truth=437, seed=7)
    assert isinstance(judge, Judge)
    assert Answer(yes=True, reason="scaffold").yes
