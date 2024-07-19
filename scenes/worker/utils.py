from manim import (
    Rectangle,
    SurroundingRectangle,
    Text,
    VGroup,
    VMobject,
)

from manim_renderer import style


class ContainerRectangle(Rectangle):
    def __init__(self, **kwargs):
        super().__init__(
            color=style.COLOR_SCENE_BACKGROUND,
            stroke_width=style.STROKE_WIDTH_HISTORY_EVENT_GROUP_RECT,
            fill_color=style.COLOR_SCENE_BACKGROUND,
            fill_opacity=1,
            **kwargs,
        )


def labeled_rectangle(label: str, **kwargs) -> VMobject:
    text = label_text(label, **kwargs)
    rect = SurroundingRectangle(
        text,
        color=style.COLOR_HISTORY_EVENT_GROUP_RECT,
        stroke_width=style.STROKE_WIDTH_HISTORY_EVENT_GROUP_RECT,
        fill_color=style.COLOR_SCENE_BACKGROUND,
        fill_opacity=1,
    )
    return VGroup(rect, text)


def label_text(text: str, **kwargs) -> Text:
    return Text(text, font_size=16, font=style.FONT_MONOSPACE, **kwargs)
