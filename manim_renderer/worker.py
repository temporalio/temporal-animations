from typing import Iterable, List

from manim import LEFT, WHITE, Mobject, SurroundingRectangle, Text, VGroup

import tempyral
from manim_renderer import mobject
from manim_renderer.code import ProxyEntityWithCode
from manim_renderer.entity import ProxyEntity, ProxyEntityWithChildren, VisualElement
from manim_renderer.history import HistoryEvents


class ActivityTask(ProxyEntity[tempyral.ActivityTask]):
    def render(self, _: tempyral.ActivityTask) -> Mobject:
        return mobject.message("Activity Task")


class ActivityTaskCompleted(ProxyEntity[tempyral.ActivityTaskCompleted]):
    def render(self, _: tempyral.ActivityTaskCompleted) -> Mobject:
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


class WorkflowTask(ProxyEntity[tempyral.WorkflowTask]):
    def render(self, entity: tempyral.WorkflowTask) -> Mobject:
        eventsm = BoxedHistoryEvents.render(entity.events)
        task = mobject.message("WFT")
        return VGroup(task, eventsm).arrange()


class WorkerRequest(ProxyEntity[tempyral.WorkerRequest]):
    def render(self, entity: tempyral.WorkerRequest) -> Mobject:
        return mobject.message(entity.__class__.__name__)


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
