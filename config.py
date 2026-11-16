"""Central configuration for the transport demand intelligence prototype."""

from __future__ import annotations

import warnings

from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

AVAILABLE_BUSES = 120
RESERVE_BUSES = 12
BUS_CAPACITY = 50
TARGET_LOAD_FACTOR = 0.80
FORECAST_HORIZON_HOURS = 24

if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    warnings.warn(
        "GEMINI_API_KEY is not configured. Gemini features will remain unavailable.",
        UserWarning,
        stacklevel=2,
    )
