from typing import Iterable

from manim import DOWN
from manim import GREEN_D as GREEN
from manim import LEFT
from manim import RED_D as RED
from manim import SMALL_BUFF, Mobject, SurroundingRectangle, VGroup

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.history_event_group_mobjs: list[Mobject] = []

    @staticmethod
    def render(_: schema.History) -> Mobject:
        return style.invisible_point()

    def render_to_scene(self, entity: schema.History):
        super().render_to_scene(entity)
        self.history_event_groups_render_to_scene(entity)

    def history_event_groups_render_to_scene(self, entity: schema.History):
        child_entities = self.get_child_entities(entity)
        assert len(self.children) == len(child_entities)
        wfts: list[list[Mobject]] = []
        wft: list[Mobject] = []
        for c, e in zip(self.children, child_entities):
            if e.event_type == schema.HistoryEventType.WFT_SCHEDULED:
                assert not wft
                wft.append(c.mobj)
            elif e.event_type == schema.HistoryEventType.WFT_COMPLETED:
                wft.append(c.mobj)
                wfts.append(wft)
                wft = []
            elif wft:
                wft.append(c.mobj)
        self.scene.remove(*self.history_event_group_mobjs)
        self.history_event_group_mobjs = [
            SurroundingRectangle(
                VGroup(*wft),
                color=style.COLOR_HISTORY_EVENT_GROUP_RECT,
                stroke_width=style.STROKE_WIDTH_HISTORY_EVENT_GROUP_RECT,
                buff=0.05,
            )
            for wft in wfts
        ]
        self.scene.add(*self.history_event_group_mobjs)

    @staticmethod
    def get_child_entities(entity: schema.History) -> list[schema.HistoryEvent]:
        return entity.events
