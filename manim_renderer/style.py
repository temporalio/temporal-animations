from manim import ORANGE, Mobject, Text

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
COLOR_SCENE_BACKGROUND = "#1D1D1D"  # GRAY_E is #222222


def message(name: str, **kwargs) -> Mobject:
    return Text(
        name, font=FONT_MESSAGE, font_size=FONT_SIZE_MESSAGE, color=ORANGE, **kwargs
    )


def actor(name: str, **kwargs) -> Mobject:
    return Text(name, font=FONT_ACTOR, font_size=FONT_SIZE_ACTOR, **kwargs)


def history_event(name: str, **kwargs) -> Mobject:
    return Text(
        name, font=FONT_HISTORY_EVENT, font_size=FONT_SIZE_HISTORY_EVENT, **kwargs
    )
