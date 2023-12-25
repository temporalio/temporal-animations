from typing import TYPE_CHECKING, List

from manim import DOWN
from manim import GREEN_D as GREEN
from manim import LEFT
from manim import RED_D as RED
from manim import RIGHT, UL, Mobject, Text, VGroup

from tempyral import log, simulation
from tempyral.animation.entity import FONT_SIZE_MEDIUM, ProxyEntity, VisualElement

if TYPE_CHECKING:
    from tempyral.animation.server import Server


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


class History:
    def __init__(self, entities: List[simulation.HistoryEvent], server: "Server"):
        self.events: List[HistoryEvent] = []
        self.server = server
        for e in entities:
            self.append(e)

    def render(self, events: List[simulation.HistoryEvent]):
        assert len(events) >= len(self.events)
        for e in events[len(self.events) :]:
            self.append(e)
        for e, entity in zip(self.events, events):
            e.render(entity)

    def append(self, entity: simulation.HistoryEvent):
        event = HistoryEvent(entity=entity)
        self.move_event_into_position(event.m)
        self.events.append(event)

    def move_event_into_position(self, newm: Mobject) -> Mobject:
        if not self.events:
            return newm.next_to(self.server.m, DOWN).align_to(self.server.m, RIGHT)
        else:
            last = self.events[-1].m
            return newm.next_to(last, DOWN).align_to(last, RIGHT)
