from typing import Iterable, List

from manim import LEFT, WHITE, Mobject, SurroundingRectangle, Text, VGroup

import tempyral
from manim_renderer import mobject
from manim_renderer.code import ProxyEntityWithCode
from manim_renderer.entity import (
    Message,
    MessageStage,
    ProxyEntity,
    ProxyEntityMessage,
    ProxyEntityWithChildren,
)
from manim_renderer.history import HistoryEvents


class ActivityTask(ProxyEntityMessage[tempyral.ActivityTask]):
    message_stage = MessageStage.Response

    def render(self, _: tempyral.ActivityTask) -> Mobject:
        return mobject.message("Activity Task")


class ActivityTaskCompleted(Message):
    message_stage = MessageStage.Response

    def render(self) -> Mobject:
        return mobject.message("ActivityTaskCompleted")


class ActivityWorker(ProxyEntity[tempyral.ActivityWorker]):
    def render(self, _: tempyral.ActivityWorker) -> Mobject:
        return mobject.actor("Activity Worker")


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


class WorkflowTask(ProxyEntityMessage[tempyral.WorkflowTask]):
    message_stage = MessageStage.Response

    def render(self, entity: tempyral.WorkflowTask) -> Mobject:
        eventsm = BoxedHistoryEvents.render(entity.events)
        task = mobject.message("WFT")
        return VGroup(task, eventsm).arrange()


class WorkerRequest(Message):
    # For example RespondWorkflowTaskCompleted. It's really a Request, but the
    # response isn't interesting, so we model the request as a response and do
    # not visualize the true response.
    message_stage = MessageStage.Response

    def render(self, name: str) -> Mobject:
        return mobject.message(name)


class Workflow(ProxyEntityWithCode[tempyral.Workflow]):
    pass


class WorkflowWorker(
    ProxyEntityWithChildren[tempyral.WorkflowWorker, tempyral.Workflow, Workflow]
):
    child_cls = Workflow
    child_align_direction = LEFT

    def render(self, _: tempyral.WorkflowWorker) -> Mobject:
        return mobject.actor("Workflow Worker")

    @staticmethod
    def get_child_entities(
        entity: tempyral.WorkflowWorker,
    ) -> List[tempyral.Workflow]:
        return entity.workflows
