from manim import Mobject, Text

FONT_MESSAGE = "Monospace"
FONT_ACTOR = "Noto Sans Kannada"
FONT_HISTORY_EVENT = "Monospace"
FONT_SIZE_HISTORY_EVENT = 12
FONT_SIZE_ACTOR = 20
FONT_SIZE_MESSAGE = 16
FONT_SIZE_CODE = 12


def message(name: str, **kwargs) -> Mobject:
    return Text(name, font=FONT_MESSAGE, font_size=FONT_SIZE_MESSAGE, **kwargs)


def actor(name: str, **kwargs) -> Mobject:
    return Text(name, font=FONT_ACTOR, font_size=FONT_SIZE_ACTOR, **kwargs)


def history_event(name: str, **kwargs) -> Mobject:
    return Text(
        name, font=FONT_HISTORY_EVENT, font_size=FONT_SIZE_HISTORY_EVENT, **kwargs
    )
