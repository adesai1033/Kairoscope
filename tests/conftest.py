"""Shared test configuration: --live gating and synthetic clip fixtures.

The default suite never calls real model APIs and must stay under 30 seconds.
Live tests are marked ``@pytest.mark.live`` and run only with ``--live`` plus
``ANTHROPIC_API_KEY`` set.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="run tests that call real model APIs (costs money; needs ANTHROPIC_API_KEY)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--live") and os.environ.get("ANTHROPIC_API_KEY"):
        return
    skip_live = pytest.mark.skip(reason="needs --live and ANTHROPIC_API_KEY")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture(scope="session")
def counter_clip(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, int, int]:
    """(path, frame_count, fps) for a clip whose every frame encodes its own index."""
    from tests.fixtures.make_clip import make_counter_clip

    frames, fps = 120, 30
    path = make_counter_clip(tmp_path_factory.mktemp("clips"), frames=frames, fps=fps)
    return path, frames, fps


@pytest.fixture
def basketball_clip(tmp_path: Path) -> Callable[..., tuple[Path, int]]:
    """Factory: generate a synthetic basketball clip, return (path, true release frame)."""
    from tests.fixtures.make_clip import make_basketball_clip

    def _make(*, release_frame: int | None = None, seed: int = 0) -> tuple[Path, int]:
        return make_basketball_clip(tmp_path, release_frame=release_frame, seed=seed)

    return _make
