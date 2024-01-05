from typing import Iterable

from manim import BLACK, DOWN
from manim import GREEN_D as GREEN
from manim import LEFT
from manim import RED_D as RED
from manim import SMALL_BUFF, Mobject, Point, VGroup

from manim_renderer import style
from manim_renderer.entity import ProxyEntity, ProxyEntityWithChildren, VisualElement
from schema import schema


class HistoryEvent(ProxyEntity[schema.HistoryEvent]):
    @staticmethod
    def render(event: schema.HistoryEvent) -> Mobject:
        return style.history_event(
            event.event_type.name,
            color=GREEN if event.seen_by_worker else RED,
        )


class HistoryEvents(VisualElement):
    @staticmethod
    def render(events: Iterable[schema.HistoryEvent]) -> Mobject:
        return VGroup(*map(HistoryEvent.render, events)).arrange(
            DOWN, buff=SMALL_BUFF, aligned_edge=LEFT
        )


class History(
    ProxyEntityWithChildren[schema.History, schema.HistoryEvent, HistoryEvent]
):
    child_cls = HistoryEvent
    child_align_direction = LEFT

    @staticmethod
    def render(_: schema.History) -> Mobject:
        m = Point(color=BLACK)
        m.set_stroke_width(0)
        return m

    @staticmethod
    def get_child_entities(entity: schema.History) -> list[schema.HistoryEvent]:
        return entity.events
