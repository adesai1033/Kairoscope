"""Video: metadata, exact frame identity, seeking, caching, strips, lifecycle."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from PIL import Image

from kairoscope.video import Video
from tests.fixtures.make_clip import color_index

Clip = tuple[Path, int, int]


def frame_index(img: Image.Image) -> int:
    """Recover the frame index encoded in the image's color."""
    w, h = img.size
    pixel = img.getpixel((w // 2, h // 2))
    assert isinstance(pixel, tuple)
    r, g, b = pixel[:3]
    return color_index((r, g, b))


@pytest.fixture
def video(counter_clip: Clip) -> Iterator[Video]:
    path, _, _ = counter_clip
    with Video(path) as v:
        yield v


def test_metadata(counter_clip: Clip, video: Video) -> None:
    _, frames, fps = counter_clip
    assert video.fps == pytest.approx(fps)
    assert video.frame_count == frames
    assert video.duration == pytest.approx(frames / fps, abs=0.2)


@pytest.mark.parametrize("index", [0, 1, 29, 30, 59, 119])
def test_frame_identity(video: Video, index: int) -> None:
    assert frame_index(video.frame(index)) == index


def test_backward_then_forward_access(video: Video) -> None:
    assert frame_index(video.frame(100)) == 100
    assert frame_index(video.frame(10)) == 10
    assert frame_index(video.frame(50)) == 50


def test_sequential_reads_decode_each_frame_once(video: Video) -> None:
    video.frame(30)
    before = video._decoded_frames
    for i in range(31, 41):
        assert frame_index(video.frame(i)) == i
    assert video._decoded_frames - before == 10


def test_scaled_decode(video: Video) -> None:
    img = video.frame(42, size=(160, 90))
    assert img.size == (160, 90)
    assert frame_index(img) == 42


def test_cache_hit_does_not_decode(video: Video) -> None:
    video.frame(50)
    before = video._decoded_frames
    assert frame_index(video.frame(50)) == 50
    assert video._decoded_frames == before


def test_cache_is_bounded_and_evicts(counter_clip: Clip) -> None:
    path, _, _ = counter_clip
    with Video(path, max_cached_frames=2) as v:
        for i in (0, 1, 2):
            v.frame(i)
        assert len(v._cache) <= 2
        before = v._decoded_frames
        v.frame(0)  # evicted, must decode again
        assert v._decoded_frames > before


def test_frames_preserves_order_and_duplicates(video: Video) -> None:
    indices = [5, 3, 5, 100]
    images = video.frames(indices)
    assert [frame_index(img) for img in images] == indices


def test_strip_clamps_at_edges(video: Video) -> None:
    offsets = (-6, -3, 0, 3, 6)
    start = video.strip(0, offsets)
    assert [frame_index(img) for img in start] == [0, 0, 0, 3, 6]
    end = video.strip(119, offsets)
    assert [frame_index(img) for img in end] == [113, 116, 119, 119, 119]


def test_out_of_range_raises(video: Video) -> None:
    with pytest.raises(IndexError):
        video.frame(-1)
    with pytest.raises(IndexError):
        video.frame(video.frame_count)


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Video(tmp_path / "nope.mp4")


def test_closed_video_raises(counter_clip: Clip) -> None:
    path, _, _ = counter_clip
    v = Video(path)
    v.close()
    with pytest.raises(ValueError):
        v.frame(0)
    v.close()  # idempotent
