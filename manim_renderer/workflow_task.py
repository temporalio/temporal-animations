from typing import Iterable, cast

from manim import DOWN, LEFT, SMALL_BUFF, WHITE, Mobject, SurroundingRectangle, VGroup

from manim_renderer import style
from manim_renderer.entity import ProxyEntity, VisualElement
from manim_renderer.history import HistoryEvents
from schema import schema


class BoxedHistoryEvents(HistoryEvents):
    @staticmethod
    def render(
        events: Iterable[schema.HistoryEvent],
        pending_updates: Iterable[schema.UpdateInfo],
    ) -> Mobject:
        eventsm = HistoryEvents.render(events)
        if pending_updates:
            eventsm = VGroup(eventsm, PendingUpdates.render(pending_updates)).arrange(
                DOWN, buff=SMALL_BUFF, aligned_edge=LEFT
            )
        rect = SurroundingRectangle(
            eventsm,
            color=WHITE,
            stroke_width=1,
        )
        return VGroup(rect, eventsm)


class WorkflowTaskRequest(ProxyEntity[schema.WorkerPollRequest]):
    def render(self, entity: schema.WorkerPollRequest) -> Mobject:
        if entity.stage == schema.RequestResponseStage.Request:
            return style.invisible_message()
        else:
            request = self.with_time(style.message("WFT"), entity)
            task = cast(schema.WorkflowTask, entity.task)
            eventsm = BoxedHistoryEvents.render(
                entity.task.events, task.pending_updates
            )
            return VGroup(request, eventsm).arrange()


class PendingUpdate(VisualElement):
    @staticmethod
    def render(_: schema.UpdateInfo) -> Mobject:
        return style.pending_update(
            "[update requested]",
        )


class PendingUpdates(VisualElement):
    @staticmethod
    def render(updates: Iterable[schema.UpdateInfo]) -> Mobject:
        return VGroup(*map(PendingUpdate.render, updates)).arrange(
            DOWN, buff=SMALL_BUFF, aligned_edge=LEFT
        )
