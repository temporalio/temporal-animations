from typing import Iterable, List

from manim import BLACK, DOWN
from manim import GREEN_D as GREEN
from manim import LEFT
from manim import RED_D as RED
from manim import SMALL_BUFF, Mobject, Point, Text, VGroup

from tempyral import simulation
from tempyral.animation.entity import (
    FONT_SIZE_SMALL,
    ProxyEntity,
    ProxyEntityWithChildren,
    VisualElement,
)


class HistoryEvent(ProxyEntity[simulation.HistoryEvent]):
    @staticmethod
    def newm(event: simulation.HistoryEvent) -> Mobject:
        return Text(
            event.event_type.name,
            font_size=FONT_SIZE_SMALL,
            color=GREEN if event.seen_by_worker else RED,
        )


class HistoryEvents(VisualElement):
    @staticmethod
    def newm(events: Iterable[simulation.HistoryEvent]) -> Mobject:
        return VGroup(*map(HistoryEvent.newm, events)).arrange(
            DOWN, buff=SMALL_BUFF, aligned_edge=LEFT
        )


class History(
    ProxyEntityWithChildren[simulation.History, simulation.HistoryEvent, HistoryEvent]
):
    child_cls = HistoryEvent
    child_align_direction = LEFT

    @staticmethod
    def newm(_: simulation.History) -> Mobject:
        m = Point(color=BLACK)
        m.set_stroke_width(0)
        return m

    @staticmethod
    def get_child_entities(entity: simulation.History) -> List[simulation.HistoryEvent]:
        return entity.events
