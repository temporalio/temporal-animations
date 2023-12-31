from typing import Iterable, List

from manim import BLACK, DOWN
from manim import GREEN_D as GREEN
from manim import LEFT
from manim import RED_D as RED
from manim import SMALL_BUFF, Mobject, Point, VGroup

import tempyral
from manim_renderer import mobject
from manim_renderer.entity import ProxyEntity, ProxyEntityWithChildren, VisualElement


class HistoryEvent(ProxyEntity[tempyral.HistoryEvent]):
    @staticmethod
    def render(event: tempyral.HistoryEvent) -> Mobject:
        return mobject.history_event(
            event.event_type.name,
            color=GREEN if event.seen_by_worker else RED,
        )


class HistoryEvents(VisualElement):
    @staticmethod
    def render(events: Iterable[tempyral.HistoryEvent]) -> Mobject:
        return VGroup(*map(HistoryEvent.render, events)).arrange(
            DOWN, buff=SMALL_BUFF, aligned_edge=LEFT
        )


class History(
    ProxyEntityWithChildren[tempyral.History, tempyral.HistoryEvent, HistoryEvent]
):
    child_cls = HistoryEvent
    child_align_direction = LEFT

    @staticmethod
    def render(_: tempyral.History) -> Mobject:
        m = Point(color=BLACK)
        m.set_stroke_width(0)
        return m

    @staticmethod
    def get_child_entities(entity: tempyral.History) -> List[tempyral.HistoryEvent]:
        return entity.events
