# AGENTS.md — kairoscope

> Your video agent is watching every frame. It doesn't need to.

**kairoscope** is an open-source Python library that makes AI video agents faster and cheaper. The two numbers that matter most are **model calls** and **dollars per answer**: model calls take seconds while local frame work takes milliseconds, so the library wins by making fewer and smaller model calls, not by micro-optimizing local code. Every cost or accuracy claim must be backed by a benchmark.

## Commands

Run these often. Every task ends with format, lint, types, and tests passing.

```bash
uv sync --all-extras                          # install everything (core + claude + dev)
uv run ruff format .                          # format
uv run ruff check . --fix                     # lint, auto-fix safe issues
uv run mypy src --strict                      # type-check the library
uv run pytest -q                              # offline test suite (must stay < 30 s)
uv run pytest -v -k find_event                # run one area verbosely
uv run pytest --cov=kairoscope --cov-report=term-missing
uv run pytest --live -m live                  # real API calls: costs money, needs ANTHROPIC_API_KEY
uv run python benchmarks/find_event_sim.py --trials 2000
uv build                                      # build sdist + wheel into dist/
```

## Project knowledge

### What it does

Kairos is the Greek word for the right moment. kairoscope decides which frames, at what resolution, a vision model actually needs to see, and finds key moments without watching the whole video. Because the right settings depend on the task (dense low-res frames often beat sparse high-res frames at equal token budgets, but some tasks are resolution-sensitive), kairoscope **measures** what each task needs instead of guessing.

### Names

- PyPI distribution and import name: `kairoscope` (used as `import kairoscope as ks`).
- `kairos` is taken: `kairos-ai` and `kairos-agent` (active AI-agent packages) both install as `import kairos`.

### Tech stack

| Area | Choice | Version |
|---|---|---|
| Language | Python | ≥ 3.12 (required by current `av` and `numpy`) |
| Video decoding | PyAV (`av`) | ≥ 19.0 |
| Arrays | NumPy | ≥ 2.5 |
| Images | Pillow | ≥ 13.0 |
| Model SDK | `anthropic` (optional extra `kairoscope[claude]`) | ≥ 1.15 |
| Build backend | hatchling | ≥ 1.32 |
| Env / runner | uv | ≥ 0.13 |
| Lint / format | ruff | ≥ 0.17 |
| Types | mypy (`--strict`) | ≥ 2.4 |
| Tests | pytest, pytest-cov | pytest ≥ 9.1 |
| CI | GitHub Actions | Python 3.12, 3.13, 3.14 |

Core runtime dependencies are exactly `av`, `numpy`, `pillow`. The core package must import without any provider SDK installed.

### File structure

```
src/kairoscope/
  __init__.py          # public API: Video, find_event, calibrate, Profile, CostLedger
  video.py             # Video: PyAV decoding, seeking, caching, context strips
  sampling.py          # uniform, scene-aware, dedupe
  cost.py              # CostLedger, pricing loading, token estimates
  pricing.json         # per-provider/model prices, each with source URL and date
  judges/
    base.py            # Judge protocol, Answer dataclass
    claude.py          # ClaudeJudge (extra: kairoscope[claude])
    simulated.py       # SimulatedJudge for tests and benchmarks
  routines/
    find_event.py      # bisection + voting + verify-and-repair
    calibrate.py       # cheapest-profile search
tests/                 # offline tests
  conftest.py          # synthetic clip fixtures
  fixtures/make_clip.py
benchmarks/            # reproducible cost/accuracy scripts; README numbers come only from here
examples/              # notebooks
docs/                  # user docs (later)
```

## v0.1 scope

Build in this order:

1. **`Video`** — keep the PyAV container open between reads; seek to the nearest keyframe, then decode forward; scale during decode; LRU-cache decoded frames with bounded memory. API: `fps`, `frame_count`, `duration`, `frame(i, size=None)`, `frames(indices, size=None)`, `strip(center, offsets)`.
2. **Judges** — `Judge` protocol with `ask(images, prompt) -> Answer`. `ClaudeJudge` first (default model `claude-sonnet-5-5`, configurable). Gemini and OpenAI after v0.1.
3. **Cost tracking** — every call records images, image dimensions, input/output tokens (from the API response when available), latency, and estimated dollars. `CostLedger` aggregates per routine.
4. **`find_event`** — bisection with context strips, optional voting, and verify-and-repair (see findings below).
5. **`calibrate`** — reference answers at full quality, then progressively cheaper configs (fps, resolution, crop, dedupe); return the cheapest `Profile` whose answers agree at or above a target rate (default 0.95). Profiles serialize to JSON.
6. **Smart sampling** — drop near-duplicate frames (perceptual hash or downscaled pixel difference); spend more frames where scenes change.

**Out of scope for v0.1:** own models, web UI, a second provider, plugins, streaming video, Rust extensions, an MCP server.

## Code style

**Naming:**
- Functions and variables: `snake_case` (`find_event`, `frame_count`)
- Classes: `PascalCase` (`Video`, `CostLedger`, `ClaudeJudge`)
- Constants: `UPPER_SNAKE_CASE` (`DEFAULT_MODEL`, `MAX_REPAIRS`)
- Private helpers: leading underscore (`_bisect`, `_gallop_left`)

**Rules:** type hints everywhere; keyword-only arguments for options; frozen dataclasses for results; every routine result includes `calls` and `cost`; public functions get a docstring with a short example; logging via `logging.getLogger("kairoscope")`; bounded retries with exponential backoff on API calls.

**Example:**

```python
# ✅ Good — typed, validated, keyword-only options, result carries calls and cost
logger = logging.getLogger("kairoscope")


@dataclass(frozen=True)
class EventResult:
    frame: int
    seconds: float
    calls: int
    cost: Cost


def find_event(
    video: Video,
    judge: Judge,
    *,
    lo: int = 0,
    hi: int | None = None,
    votes: int = 1,
    verify: bool = True,
) -> EventResult:
    """Find the first frame where `judge` answers YES.

    Example:
        >>> result = ks.find_event(video, judge)
        >>> result.seconds, result.calls
    """
    hi = video.frame_count - 1 if hi is None else hi
    if not 0 <= lo < hi < video.frame_count:
        raise ValueError(f"invalid window: lo={lo}, hi={hi}, frames={video.frame_count}")
    logger.debug("find_event window=[%d, %d] votes=%d verify=%s", lo, hi, votes, verify)
    ...


# ❌ Bad — reopens the file every step, swallows errors, prints, untyped
def find(path, j, lo=0, hi=None):
    while hi - lo > 1:
        mid = (lo + hi) // 2
        cap = cv2.VideoCapture(path)  # reopens and re-seeks every call
        cap.set(cv2.CAP_PROP_POS_FRAMES, mid)
        try:
            ans = j(cap.read()[1])
        except Exception:  # hides API failures as "no"
            ans = False
        print("asked", mid, ans)  # prints from library code
        lo, hi = (lo, mid) if ans else (mid, hi)
    return hi
```

## Testing

- **Never call real model APIs in the default suite.** Use `SimulatedJudge`: it answers ground truth (`frame >= truth`) but flips with probability `base_error + near_error * exp(-|frame - truth| / near_scale)`, seeded. This mirrors real models, which are most confused right at the event.
- **Synthetic clips** come from `tests/fixtures/make_clip.py` (Pillow to draw, PyAV to encode), generated into a temp dir. Spec: 640×360, 30 fps, 600 frames; a stick-figure player dribbles (ball goes hand → floor → hand every 20 frames, a deliberate distractor), gathers the ball overhead over ~14 frames, releases at a configurable `release_frame`, the ball arcs to the hoop over ~34 frames, then drops and bounces. Returns the video path and the true release frame; supports a random release for blind tests.
- **Adapters** are tested with a mocked client: request shape, base64 image encoding, response parsing, token and cost recording.
- **Live tests** are marked `@pytest.mark.live` and skipped unless `--live` is passed and `ANTHROPIC_API_KEY` is set.

**Example:**

```python
def test_find_event_recovers_from_noisy_judge(basketball_clip):
    video, truth = basketball_clip(release_frame=437)
    judge = SimulatedJudge(truth, base_error=0.05, near_error=0.25, seed=7)

    result = ks.find_event(video, judge, verify=True)

    assert abs(result.frame - truth) <= 3
    assert result.calls < 60
    assert result.cost.images == result.calls
```

## Git workflow

- Branch from `main`: `feat/<short-name>`, `fix/<short-name>`, `bench/<short-name>`, `docs/<short-name>`.
- Conventional commits: `feat: add verify-and-repair to find_event`, `fix: reuse open container in Video.frame`, `bench: add 1h simulation`, `test:`, `docs:`, `chore:`.
- One logical change per commit; keep PRs small and reviewable.
- Before every commit: `ruff format`, `ruff check`, `mypy src --strict`, `pytest -q` all pass.
- PR descriptions say what changed and why; if cost or accuracy changed, include before/after numbers from `benchmarks/`.
- Never force-push to `main`; never rewrite published history.

## Findings from the prototype

An earlier single-file prototype (not in this repo) proved the bisection idea. Build on these findings:

- **Context strips beat single frames.** The judge sees 5 frames around the midpoint (offsets −6, −3, 0, +3, +6 at 30 fps, about ±0.2 s), tiled left to right with relative time labels and the judged frame outlined in red. A single still can't tell a dribble from a shot. The prompt says the frames are in time order and which one is judged, and asks for JSON `{"answer": "yes" | "no", "reason": "..."}`.
- **Plain bisection is fragile; verify-and-repair fixes it.** Simulation on 1 hour of video (108,000 frames), judge wrong 5% of the time plus 25% extra right at the event:

  | strategy | exact | ±3 frames | ±1 s | calls |
  |---|---|---|---|---|
  | plain | 18% | 44% | 59% | 17 |
  | vote of 3 | 52% | 88% | 93% | 36 |
  | verify-and-repair | 70% | 98% | 100% | 51 |
  | vote of 3 + verify | 80% | 100% | 100% | 57 |

  A perfect judge needs ~9 calls on 600 frames. Above ~20% judge error, nothing is reliable. Verify-and-repair is on by default.
- **Verify-and-repair algorithm:** after bisection converges on frame `f`, re-check `f−1` (expect NO) and `f` (expect YES), each with a 3-vote majority that stops early once decided. If `f−1` says YES, step left by doubling distances (2, 4, 8, …) until a frame says NO, then bisect that bracket; if `f` says NO, mirror to the right. Repeat up to `max_repairs` (default 4).
- **Models aren't frame-precise.** Errors cluster at the exact boundary (ball touching the fingertips). A blind live test landed 2 frames (67 ms) late. Keep a `refine=` hook for a post-v0.1 local refinement step (tracking or frame differencing).
- **The answer must flip exactly once in the window.** The caller asserts NO at `lo` and YES at `hi` (no calls spent there). Multi-event videos need a coarse pass first (`find_all_events`, post-v0.1).
- **The prototype's worst bug** was reopening the video for every frame.

## Facts to respect

- Hosted APIs generally price images by pixel dimensions, not color channels or JPEG quality. Greyscale and compression don't reduce tokens. Real levers: frame count, resolution, cropping, dedupe, scene-aware sampling, transcript-first, cascades, search.
- Decoding dominates local cost on long videos: decode only needed frames, at reduced size, with seeking.

## Boundaries

- ✅ **Always:**
  - Write code in `src/kairoscope/`, tests in `tests/`, benchmarks in `benchmarks/`
  - Run format, lint, types, and tests before declaring a task done or committing
  - Add or update a benchmark when a change affects cost or accuracy, and report before/after numbers
  - Keep `pricing.json` entries sourced (URL + date)
  - Generate test videos at runtime
- ⚠️ **Ask first:**
  - Adding or upgrading a dependency
  - Changing public API names or signatures
  - Changing defaults that affect cost or accuracy (`verify`, `votes`, strip offsets, default model)
  - Modifying CI config, `pyproject.toml` build settings, or this file
  - Starting anything listed as out of scope
  - Running live API tests (they cost money)
- 🚫 **Never:**
  - Commit secrets, API keys, or `.env` files
  - Commit large binaries (videos over ~1 MB) or anything in `dist/`, `.venv/`, caches
  - Call real model APIs in the default test suite or CI
  - Use `kairos` as a module, package, or import name
  - Reopen or re-decode the video per frame, or decode a whole video to get a few frames
  - Add heavy dependencies (torch, transformers, opencv, langchain, llama-index) to core
  - Invent prices, model behavior, or benchmark numbers
  - Claim greyscale or JPEG quality saves tokens
  - Send frames anywhere except the user's configured provider; no telemetry or import-time network calls
  - Print from library code, keep global mutable state, or swallow API errors
  - Delete or skip a failing test to make the suite pass
  - Force-push to `main`

## Launch checklist (v0.1)

- [x] Reserve `kairoscope` on PyPI with a placeholder release (0.1.0.dev0, 2026-10-18)
- [ ] README: tagline, demo GIF, one-line install, five-line example, headline benchmark number
- [ ] Benchmark on a public video dataset: accuracy vs. cost against naive uniform sampling
- [ ] Two or three example notebooks
- [ ] License (MIT or Apache-2.0)