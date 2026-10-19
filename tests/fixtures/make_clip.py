"""Synthetic test clips, generated at runtime (Pillow to draw, PyAV to encode).

Two generators:

- :func:`make_counter_clip` — every frame is a solid color encoding its own index,
  so Video tests can assert exact frame identity through seeks, scaling, and caching.
- :func:`make_basketball_clip` — the find_event scenario (still a stub). Spec:
  640x360, 30 fps, 600 frames. A stick-figure player dribbles (ball goes
  hand -> floor -> hand every 20 frames, a deliberate distractor), gathers the
  ball overhead over ~14 frames, releases at `release_frame`, the ball arcs to
  the hoop over ~34 frames, then drops and bounces.
"""

from __future__ import annotations

from pathlib import Path

import av
from PIL import Image

WIDTH = 640
HEIGHT = 360
FPS = 30
FRAME_COUNT = 600
DRIBBLE_PERIOD = 20
GATHER_FRAMES = 14
ARC_FRAMES = 34

# Counter-clip colors quantize each channel to 16 levels (step 16, centered in the
# bucket) so indices survive RGB -> yuv420p -> RGB round-trips.
_COLOR_STEP = 16
_LEVELS = 256 // _COLOR_STEP
MAX_COUNTER_INDEX = _LEVELS**3


def index_color(i: int) -> tuple[int, int, int]:
    """Solid RGB color encoding frame index `i`."""
    if not 0 <= i < MAX_COUNTER_INDEX:
        raise ValueError(f"index {i} out of range [0, {MAX_COUNTER_INDEX})")

    def channel(level: int) -> int:
        return level * _COLOR_STEP + _COLOR_STEP // 2

    return (
        channel(i % _LEVELS),
        channel((i // _LEVELS) % _LEVELS),
        channel(i // (_LEVELS * _LEVELS)),
    )


def color_index(color: tuple[int, int, int]) -> int:
    """Inverse of :func:`index_color`, tolerant of lossy encoding."""

    def level(c: int) -> int:
        return min(_LEVELS - 1, max(0, round((c - _COLOR_STEP // 2) / _COLOR_STEP)))

    r, g, b = color
    return level(r) + _LEVELS * level(g) + _LEVELS * _LEVELS * level(b)


def make_counter_clip(
    out_dir: Path,
    *,
    frames: int = 120,
    fps: int = 30,
    size: tuple[int, int] = (320, 180),
    gop: int = 30,
) -> Path:
    """Encode a clip whose every frame is a solid color encoding its own index.

    `gop` fixes the keyframe interval (scene-cut detection off) so seeking tests
    exercise real keyframe-then-decode-forward behavior.
    """
    path = Path(out_dir) / f"counter_{frames}f_{fps}fps.mp4"
    container = av.open(str(path), mode="w")
    stream = container.add_stream("libx264", rate=fps)
    stream.width, stream.height = size
    stream.pix_fmt = "yuv420p"
    stream.options = {
        "x264opts": f"keyint={gop}:min-keyint={gop}:scenecut=0",
        "crf": "18",
    }
    for i in range(frames):
        image = Image.new("RGB", size, index_color(i))
        for packet in stream.encode(av.VideoFrame.from_image(image)):
            container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
    container.close()
    return path


def make_basketball_clip(
    out_dir: Path,
    *,
    release_frame: int | None = None,
    seed: int = 0,
) -> tuple[Path, int]:
    """Render the basketball clip into `out_dir`; return (video path, true release frame).

    A `release_frame` of None picks a random release (seeded) for blind tests.
    """
    raise NotImplementedError("make_basketball_clip is not implemented yet (v0.1 scaffolding)")
