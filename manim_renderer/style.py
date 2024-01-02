from manim import ORANGE, Line, Mobject, Text
from manim.typing import Point3D

FONT_MONOSPACE = "Monaco"  # Monaco, Menlo, PT Mono
FONT_SANS = "Noto Sans Kannada"
FONT_MESSAGE = FONT_MONOSPACE
FONT_ACTOR = FONT_SANS
FONT_HISTORY_EVENT = FONT_MONOSPACE
FONT_CODE = FONT_MONOSPACE
FONT_SIZE_HISTORY_EVENT = 12
FONT_SIZE_ACTOR = 20
FONT_SIZE_MESSAGE = 16
FONT_SIZE_CODE = 10
COLOR_MESSAGE = ORANGE
COLOR_SCENE_BACKGROUND = "#1D1D1D"  # GRAY_E is #222222
STROKE_WIDTH_PENDING_REQUEST_RAY = 1
STROKE_OPACITY_PENDING_REQUEST_RAY = 0.7
BUFF_PENDING_REQUEST = 0.5


def message(name: str, **kwargs) -> Mobject:
    return Text(
        name,
        font=FONT_MESSAGE,
        font_size=FONT_SIZE_MESSAGE,
        color=COLOR_MESSAGE,
        **kwargs
    )


def pending_request_ray(start: Point3D, end: Point3D) -> Mobject:
    return Line(
        start=start,
        end=end,
        stroke_color=COLOR_MESSAGE,
        stroke_width=STROKE_WIDTH_PENDING_REQUEST_RAY,
        buff=BUFF_PENDING_REQUEST,
        stroke_opacity=STROKE_OPACITY_PENDING_REQUEST_RAY,
    )


def invisible_message() -> Mobject:
    return Text(".").set_opacity(0)


def actor(name: str, **kwargs) -> Mobject:
    return Text(name, font=FONT_ACTOR, font_size=FONT_SIZE_ACTOR, **kwargs)


def history_event(name: str, **kwargs) -> Mobject:
    return Text(
        name, font=FONT_HISTORY_EVENT, font_size=FONT_SIZE_HISTORY_EVENT, **kwargs
    )
