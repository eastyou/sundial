"""水平日晷制作卡生成器。"""

from __future__ import annotations

from .model import (
    DEFAULT_END_HOUR,
    DEFAULT_LATITUDE,
    DEFAULT_START_HOUR,
    DEFAULT_TITLE,
    HourLine,
    Sundial,
    SundialError,
    angle_table,
    format_angle,
    gnomon_dimensions,
    hour_angle,
    hour_line_endpoint,
    hour_lines,
)
from .render import render_html, render_sundial

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_END_HOUR",
    "DEFAULT_LATITUDE",
    "DEFAULT_START_HOUR",
    "DEFAULT_TITLE",
    "HourLine",
    "Sundial",
    "SundialError",
    "__version__",
    "angle_table",
    "format_angle",
    "gnomon_dimensions",
    "hour_angle",
    "hour_line_endpoint",
    "hour_lines",
    "render_html",
    "render_sundial",
]
