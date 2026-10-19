# kairoscope

> Your video agent is watching every frame. It doesn't need to.

**kairoscope** makes AI video agents faster and cheaper. It decides which frames, at
what resolution, a vision model actually needs to see, and finds key moments without
watching the whole video.

> **Status: v0.1 scaffolding.** APIs are stubs and not yet implemented.

```bash
pip install kairoscope           # core (av, numpy, pillow)
pip install "kairoscope[claude]" # + Anthropic judge
```

```python
import kairoscope as ks
from kairoscope.judges.claude import ClaudeJudge

video = ks.Video("game.mp4")
judge = ClaudeJudge()  # default model: claude-sonnet-5-5
result = ks.find_event(video, judge)
print(result.seconds, result.calls, result.cost)
```

## Development

```bash
uv sync --all-extras
uv run ruff format .
uv run ruff check . --fix
uv run mypy src --strict
uv run pytest -q
```

Benchmark numbers in this README come only from `benchmarks/`.
