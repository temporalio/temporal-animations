from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

from manim import (
    DOWN,
    DR,
    GREEN,
    LEFT,
    RED,
    SMALL_BUFF,
    SurroundingRectangle,
    Text,
    VGroup,
    VMobject,
)

import esv
from manim_renderer import style
from schema import schema

if TYPE_CHECKING:
    from scenes.worker import input


HistoryEventId = int


HistoryEventType = schema.HistoryEventType


@dataclass
class HistoryEvent(esv.Entity):
    id: int
    event_type: HistoryEventType
    seen_by_worker: bool
    initiating_event_id: HistoryEventId = -1

    def render(self) -> VMobject:
        return Text(
            self.event_type.name,
            font=style.FONT_HISTORY_EVENT,
            font_size=style.FONT_SIZE_HISTORY_EVENT,
            color=GREEN if self.seen_by_worker else RED,
        )

    def handle(self, event: esv.Event) -> bool:
        return False

    def __str__(self) -> str:
        return self.event_type.name


@dataclass
class History(esv.Entity):
    events: Iterable[HistoryEvent]

    def handle(self, event: "input.Event") -> bool:
        event.history_event.seen_by_worker = True
        return True

    def render(self) -> VMobject:
        events = VGroup(*map(HistoryEvent.render, self.events)).arrange(
            DOWN, buff=SMALL_BUFF, aligned_edge=LEFT
        )
        rect = SurroundingRectangle(
            events,
            color=style.COLOR_HISTORY_EVENT_GROUP_RECT,
            stroke_width=style.STROKE_WIDTH_HISTORY_EVENT_GROUP_RECT,
            fill_color=style.COLOR_SCENE_BACKGROUND,
            fill_opacity=1,
            corner_radius=style.RECT_CORNER_RADIUS,
        )
        return VGroup(rect, events).align_on_border(DR)
