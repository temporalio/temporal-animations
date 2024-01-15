from manim import (
    BLUE_E,
    LIGHTER_GRAY,
    ORANGE,
    Line,
    ManimColor,
    Mobject,
    Point,
    SurroundingRectangle,
    Text,
    VGroup,
)
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
COLOR_REQUESTED_UPDATE = BLUE_E
COLOR_MESSAGE = ORANGE
COLOR_ACTIVE_CODE = "#3CB043"
COLOR_INACTIVE_CODE = LIGHTER_GRAY
COLOR_SCENE_BACKGROUND = "#1D1D1D"
COLOR_HISTORY_EVENT_GROUP_RECT = LIGHTER_GRAY
STROKE_WIDTH_HISTORY_EVENT_GROUP_RECT = 1
STROKE_WIDTH_PENDING_REQUEST_RAY = 1
STROKE_OPACITY_PENDING_REQUEST_RAY = 0.7
BUFF_PENDING_REQUEST = 0.5


def message(name: str) -> Mobject:
    text = Text(
        name,
        font=FONT_MESSAGE,
        font_size=FONT_SIZE_MESSAGE,
        color=COLOR_MESSAGE,
    )
    rect = SurroundingRectangle(
        text,
        stroke_width=0,
        fill_opacity=1,
        fill_color=COLOR_SCENE_BACKGROUND,
    )
    return VGroup(rect, text)


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


def invisible_point() -> Mobject:
    return Point().set_stroke_width(0)


def actor(name: str) -> Mobject:
    return Text(name, font=FONT_ACTOR, font_size=FONT_SIZE_ACTOR)


def history_event(name: str, color: ManimColor) -> Mobject:
    return Text(
        name, font=FONT_HISTORY_EVENT, font_size=FONT_SIZE_HISTORY_EVENT, color=color
    )


def requested_update(name: str) -> Mobject:
    return Text(
        name,
        font=FONT_HISTORY_EVENT,
        font_size=FONT_SIZE_HISTORY_EVENT,
        color=COLOR_REQUESTED_UPDATE,
    )
