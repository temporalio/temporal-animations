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
        requested_updates: Iterable[schema.UpdateInfo],
    ) -> Mobject:
        eventsm = HistoryEvents.render(events)
        if requested_updates:
            eventsm = VGroup(
                eventsm, RequestedUpdates.render(requested_updates)
            ).arrange(DOWN, buff=SMALL_BUFF, aligned_edge=LEFT)
        rect = SurroundingRectangle(
            eventsm,
            color=WHITE,
            stroke_width=1,
            fill_opacity=1,
            fill_color=style.COLOR_SCENE_BACKGROUND,
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
                entity.task.events, task.requested_updates
            )
            return VGroup(request, eventsm).arrange()


class RequestedUpdate(VisualElement):
    @staticmethod
    def render(_: schema.UpdateInfo) -> Mobject:
        return style.requested_update(
            "[update requested]",
        )


class RequestedUpdates(VisualElement):
    @staticmethod
    def render(updates: Iterable[schema.UpdateInfo]) -> Mobject:
        return VGroup(*map(RequestedUpdate.render, updates)).arrange(
            DOWN, buff=SMALL_BUFF, aligned_edge=LEFT
        )
