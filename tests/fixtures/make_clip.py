"""Synthetic basketball clip generator (Pillow to draw, PyAV to encode).

Spec: 640x360, 30 fps, 600 frames. A stick-figure player dribbles (ball goes
hand -> floor -> hand every 20 frames, a deliberate distractor), gathers the
ball overhead over ~14 frames, releases at `release_frame`, the ball arcs to
the hoop over ~34 frames, then drops and bounces. Clips are generated into a
temp dir at runtime and never committed.
"""

from __future__ import annotations

from pathlib import Path

WIDTH = 640
HEIGHT = 360
FPS = 30
FRAME_COUNT = 600
DRIBBLE_PERIOD = 20
GATHER_FRAMES = 14
ARC_FRAMES = 34


def make_basketball_clip(
    out_dir: Path,
    *,
    release_frame: int | None = None,
    seed: int = 0,
) -> tuple[Path, int]:
    """Render the clip into `out_dir`; return (video path, true release frame).

    A `release_frame` of None picks a random release (seeded) for blind tests.
    """
    raise NotImplementedError("make_basketball_clip is not implemented yet (v0.1 scaffolding)")
