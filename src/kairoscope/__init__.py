"""kairoscope — decide which frames a vision model actually needs to see.

Usage:
    >>> import kairoscope as ks
    >>> video = ks.Video("game.mp4")
    >>> result = ks.find_event(video, judge)
"""

from kairoscope.cost import Cost, CostLedger
from kairoscope.routines.calibrate import CalibrateResult, Profile, calibrate
from kairoscope.routines.find_event import EventResult, find_event
from kairoscope.video import Video

__version__ = "0.1.0.dev0"

__all__ = [
    "CalibrateResult",
    "Cost",
    "CostLedger",
    "EventResult",
    "Profile",
    "Video",
    "__version__",
    "calibrate",
    "find_event",
]
