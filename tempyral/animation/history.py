from typing import TYPE_CHECKING, List

from manim import DL, DOWN, DR
from manim import GREEN_D as GREEN
from manim import LEFT
from manim import RED_D as RED
from manim import RIGHT, UL, Line, Mobject, Point, Text, VGroup

from tempyral import log, simulation
from tempyral.animation.entity import (
    FONT_SIZE_MEDIUM,
    ProxyEntity,
    ProxyEntityWithChildren,
    VisualElement,
)

if TYPE_CHECKING:
    from tempyral.animation.server import Server

InvisibleMobject = Point


class HistoryEvent(ProxyEntity[simulation.HistoryEvent]):
    @staticmethod
    def newm(event: simulation.HistoryEvent, font_size=FONT_SIZE_MEDIUM) -> Mobject:
        log(event, "A: HistoryEvent.newm")
        return Text(
            event.event_type.name,
            font_size=font_size,
            color=GREEN if event.seen_by_sticky_worker else RED,
        )


class HistoryEvents(VisualElement):
    @staticmethod
    def newm(
        events: List[simulation.HistoryEvent], font_size=FONT_SIZE_MEDIUM
    ) -> Mobject:
        log(events, "A: HistoryEvents.newm")
        return VGroup(*map(HistoryEvent.newm, events)).arrange(DOWN)


class History(
    ProxyEntityWithChildren[simulation.History, simulation.HistoryEvent, HistoryEvent]
):
    child_cls = HistoryEvent

    @staticmethod
    def newm(_: simulation.History) -> Mobject:
        return InvisibleMobject()

    @staticmethod
    def get_child_entities(entity: simulation.History) -> List[simulation.HistoryEvent]:
        return entity.events
