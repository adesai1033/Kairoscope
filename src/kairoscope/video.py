"""Video access: PyAV decoding, keyframe seeking, bounded frame caching, context strips.

The container stays open between reads. Seeks go to the nearest keyframe and decode
forward; frames are scaled during decode and LRU-cached with a bounded count. Assumes
constant-frame-rate video: frame indices map linearly to timestamps.
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from collections.abc import Iterator, Sequence
from fractions import Fraction
from pathlib import Path
from types import TracebackType
from typing import cast

import av
from PIL import Image

logger = logging.getLogger("kairoscope")

# Within this many frames ahead of the decoder, decoding forward beats seeking
# back to a keyframe and re-decoding the gap.
_FORWARD_WINDOW = 64

_Size = tuple[int, int]
_CacheKey = tuple[int, _Size | None]


class Video:
    """A video file opened once, read many times.

    Not thread-safe. Use as a context manager or call :meth:`close` to release
    the decoder.

    Example:
        >>> with Video("game.mp4") as video:
        ...     frame = video.frame(437, size=(640, 360))
        ...     strip = video.strip(437, offsets=(-6, -3, 0, 3, 6))
    """

    def __init__(self, path: str | Path, *, max_cached_frames: int = 256) -> None:
        if max_cached_frames < 1:
            raise ValueError(f"max_cached_frames must be >= 1, got {max_cached_frames}")
        self._path = Path(path)
        if not self._path.is_file():
            raise FileNotFoundError(f"no such video file: {self._path}")
        self._max_cached_frames = max_cached_frames
        self._container = av.open(str(self._path), mode="r")
        try:
            if not self._container.streams.video:
                raise ValueError(f"no video stream in {self._path}")
            self._stream = self._container.streams.video[0]
            self._stream.thread_type = "AUTO"
            rate = self._stream.average_rate
            time_base = self._stream.time_base
            if rate is None or rate <= 0 or time_base is None:
                raise ValueError(f"cannot determine frame rate for {self._path}")
            self._rate = Fraction(rate.numerator, rate.denominator)
            self._time_base = Fraction(time_base.numerator, time_base.denominator)
            self._start_time: int = self._stream.start_time or 0
            if self._stream.duration is not None:
                self._duration = float(self._stream.duration * time_base)
            elif self._container.duration is not None:
                self._duration = self._container.duration / av.time_base
            else:
                raise ValueError(f"cannot determine duration for {self._path}")
            frames = self._stream.frames
            self._frame_count = frames if frames > 0 else round(self._duration * float(rate))
            if self._frame_count <= 0:
                raise ValueError(f"empty video: {self._path}")
        except Exception:
            self._container.close()
            raise
        self._frame_iter: Iterator[av.VideoFrame] | None = None
        self._last_index: int | None = None  # index of the most recently decoded frame
        self._cache: OrderedDict[_CacheKey, Image.Image] = OrderedDict()
        self._decoded_frames = 0  # decode statistic; tests assert on it
        self._closed = False
        logger.debug(
            "opened %s: %d frames, %.3f fps, %.2f s",
            self._path,
            self._frame_count,
            float(self._rate),
            self._duration,
        )

    @property
    def fps(self) -> float:
        """Average frames per second."""
        return float(self._rate)

    @property
    def frame_count(self) -> int:
        """Total number of frames."""
        return self._frame_count

    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return self._duration

    def frame(self, i: int, *, size: _Size | None = None) -> Image.Image:
        """Decode frame `i`, scaled to `size` (width, height) during decode."""
        return self.frames([i], size=size)[0]

    def frames(self, indices: Sequence[int], *, size: _Size | None = None) -> list[Image.Image]:
        """Decode several frames, one forward decode pass per cluster of indices.

        Returns images in the order requested; duplicates are allowed.
        """
        self._check_open()
        for i in indices:
            if not 0 <= i < self._frame_count:
                raise IndexError(f"frame {i} out of range [0, {self._frame_count})")
        size_key = (int(size[0]), int(size[1])) if size is not None else None
        images: dict[int, Image.Image] = {}
        misses: list[int] = []
        for i in dict.fromkeys(indices):
            cached = self._cache_get((i, size_key))
            if cached is not None:
                images[i] = cached
            else:
                misses.append(i)
        if misses:
            for i, img in self._decode_missing(sorted(misses), size_key).items():
                self._cache_put((i, size_key), img)
                images[i] = img
        return [images[i] for i in indices]

    def strip(
        self, center: int, offsets: Sequence[int], *, size: _Size | None = None
    ) -> list[Image.Image]:
        """Frames at `center + offset` for each offset, clamped to the video bounds."""
        self._check_open()
        last = self._frame_count - 1
        indices = [min(max(center + offset, 0), last) for offset in offsets]
        return self.frames(indices, size=size)

    def close(self) -> None:
        """Release the container and drop the cache. Safe to call twice."""
        if self._closed:
            return
        self._closed = True
        self._frame_iter = None
        self._cache.clear()
        self._container.close()

    def __enter__(self) -> Video:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def _check_open(self) -> None:
        if self._closed:
            raise ValueError(f"Video is closed: {self._path}")

    def _decode_missing(self, misses: list[int], size_key: _Size | None) -> dict[int, Image.Image]:
        """Decode sorted, unique frame indices, grouped into runs decoded in one pass."""
        out: dict[int, Image.Image] = {}
        run: list[int] = []
        for i in misses:
            if run and i - run[-1] > _FORWARD_WINDOW:
                self._decode_run(run, size_key, out)
                run = []
            run.append(i)
        if run:
            self._decode_run(run, size_key, out)
        return out

    def _decode_run(
        self, run: list[int], size_key: _Size | None, out: dict[int, Image.Image]
    ) -> None:
        first, last = run[0], run[-1]
        want = set(run)
        can_roll_forward = (
            self._last_index is not None
            and self._last_index < first <= self._last_index + _FORWARD_WINDOW
        )
        if not can_roll_forward:
            index, decoded = self._start_run(first)
            self._take(index, decoded, want, size_key, out)
        while want:
            got = self._decode_next()
            if got is None:
                raise IndexError(f"stream ended before frame {min(want)} in {self._path}")
            index, decoded = got
            self._take(index, decoded, want, size_key, out)
            if index >= last and want:
                raise IndexError(f"could not decode frame(s) {sorted(want)} in {self._path}")

    def _take(
        self,
        index: int,
        decoded: av.VideoFrame,
        want: set[int],
        size_key: _Size | None,
        out: dict[int, Image.Image],
    ) -> None:
        if index in want:
            out[index] = self._to_image(decoded, size_key)
            want.discard(index)

    def _start_run(self, target: int) -> tuple[int, av.VideoFrame]:
        """Seek so decoding resumes at or before `target`; return the first decoded frame.

        `backward=True` seeks to the keyframe at or before the requested timestamp,
        but timestamp rounding can land one frame late, so retry with growing slack.
        """
        slack = 0
        while True:
            seek_index = max(0, target - slack)
            self._seek_to(seek_index)
            got = self._decode_next()
            if got is not None and got[0] <= target:
                return got
            if seek_index == 0:
                raise IndexError(f"cannot decode frame {target} in {self._path}")
            slack = 16 if slack == 0 else slack * 4

    def _seek_to(self, index: int) -> None:
        seconds = Fraction(index) / self._rate
        offset = self._start_time + int(seconds / self._time_base)
        logger.debug("seek to frame %d (pts %d)", index, offset)
        self._container.seek(offset, stream=self._stream, backward=True)
        self._frame_iter = None
        self._last_index = None

    def _decode_next(self) -> tuple[int, av.VideoFrame] | None:
        if self._frame_iter is None:
            self._frame_iter = self._container.decode(self._stream)
        try:
            decoded = next(self._frame_iter)
        except StopIteration:
            self._frame_iter = None
            self._last_index = None
            return None
        self._decoded_frames += 1
        index = self._index_of(decoded)
        self._last_index = index
        return index, decoded

    def _index_of(self, decoded: av.VideoFrame) -> int:
        pts = decoded.pts
        if pts is None:
            return self._last_index + 1 if self._last_index is not None else 0
        return round(float((pts - self._start_time) * self._time_base * self._rate))

    @staticmethod
    def _to_image(decoded: av.VideoFrame, size_key: _Size | None) -> Image.Image:
        if size_key is None:
            img = decoded.to_image()  # type: ignore[no-untyped-call]
        else:
            img = decoded.to_image(width=size_key[0], height=size_key[1])  # type: ignore[no-untyped-call]
        return cast(Image.Image, img)

    def _cache_get(self, key: _CacheKey) -> Image.Image | None:
        img = self._cache.get(key)
        if img is not None:
            self._cache.move_to_end(key)
        return img

    def _cache_put(self, key: _CacheKey, img: Image.Image) -> None:
        self._cache[key] = img
        self._cache.move_to_end(key)
        while len(self._cache) > self._max_cached_frames:
            self._cache.popitem(last=False)
