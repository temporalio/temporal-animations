from typing import Iterable, List

from manim import (
    DOWN,
    LEFT,
    SMALL_BUFF,
    WHITE,
    Mobject,
    SurroundingRectangle,
    VDict,
    VGroup,
)

import tempyral
from manim_renderer import style
from manim_renderer.code import ProxyEntityWithCode
from manim_renderer.entity import ProxyEntity, ProxyEntityWithChildren
from manim_renderer.history import HistoryEvents


class ActivityTaskRequest(ProxyEntity[tempyral.WorkerPollRequest]):
    def render(self, entity: tempyral.WorkerPollRequest) -> Mobject:
        if entity.stage == tempyral.RequestResponseStage.Request:
            return style.invisible_message()
        else:
            return style.message("Activity Task")


class ActivityTaskCompleted(ProxyEntity[tempyral.ActivityTaskCompleted]):
    def render(self, _: tempyral.ActivityTaskCompleted) -> Mobject:
        return style.message("Activity Task Completed")


class ActivityWorker(ProxyEntityWithCode[tempyral.ActivityWorker]):
    def render(self, entity: tempyral.ActivityWorker) -> Mobject:
        code = super().render(entity)
        text = self.with_time(style.actor("Activity Worker"), entity)
        return VDict({"text": text, "code": code}).arrange(
            DOWN, buff=SMALL_BUFF, aligned_edge=LEFT
        )


class BoxedHistoryEvents(HistoryEvents):
    @staticmethod
    def render(events: Iterable[tempyral.HistoryEvent]) -> Mobject:
        eventsm = HistoryEvents.render(events)
        rect = SurroundingRectangle(
            eventsm,
            color=WHITE,
            stroke_width=1,
        )
        return VGroup(rect, eventsm)


class WorkflowTaskRequest(ProxyEntity[tempyral.WorkerPollRequest]):
    def render(self, entity: tempyral.WorkerPollRequest) -> Mobject:
        if entity.stage == tempyral.RequestResponseStage.Request:
            return style.invisible_message()
        else:
            request = self.with_time(style.message("WFT"), entity)
            eventsm = BoxedHistoryEvents.render(entity.task.events)
            return VGroup(request, eventsm).arrange()


class WorkflowTaskCompleted(ProxyEntity[tempyral.WorkflowTaskCompleted]):
    def render(self, _: tempyral.WorkflowTaskCompleted) -> Mobject:
        return style.message("WFT Completed")


class WorkerRequest(ProxyEntity[tempyral.WorkerRequest]):
    def render(self, entity: tempyral.WorkerRequest) -> Mobject:
        return style.message(f"WorkerRequest[{entity.__class__.__name__}]")


class Workflow(ProxyEntityWithCode[tempyral.Workflow]):
    pass


class WorkflowWorker(
    ProxyEntityWithChildren[tempyral.WorkflowWorker, tempyral.Workflow, Workflow]
):
    child_cls = Workflow
    child_align_direction = LEFT

    def render(self, entity: tempyral.WorkflowWorker) -> Mobject:
        return self.with_time(style.actor("Workflow Worker"), entity)

    def render_to_scene(self, entity: tempyral.WorkflowWorker):
        super().render_to_scene(entity)
        self.scene.wait()

    @staticmethod
    def get_child_entities(
        entity: tempyral.WorkflowWorker,
    ) -> List[tempyral.Workflow]:
        return entity.workflows
