"""Routines: model-call-efficient search and calibration over videos."""

from kairoscope.routines.calibrate import CalibrateResult, Profile, calibrate
from kairoscope.routines.find_event import EventResult, find_event

__all__ = ["CalibrateResult", "EventResult", "Profile", "calibrate", "find_event"]
