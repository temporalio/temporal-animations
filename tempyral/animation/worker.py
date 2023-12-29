from typing import Iterable, List

from manim import LEFT, WHITE, Mobject, SurroundingRectangle, Text, VGroup

from tempyral import simulation
from tempyral.animation import mobject
from tempyral.animation.code import ProxyEntityWithCode
from tempyral.animation.entity import (
    ProxyEntity,
    ProxyEntityWithChildren,
    VisualElement,
)
from tempyral.animation.history import HistoryEvents


class ActivityTask(ProxyEntity[simulation.ActivityTask]):
    def render(self, _: simulation.ActivityTask) -> Mobject:
        return mobject.message("Activity Task")


class ActivityTaskCompleted(VisualElement):
    def render(self) -> Mobject:
        return mobject.message("ActivityTaskCompleted")


class ActivityWorker(ProxyEntity[simulation.ActivityWorker]):
    def render(self, _: simulation.ActivityWorker) -> Mobject:
        return mobject.actor("Activity Worker")


class BoxedHistoryEvents(HistoryEvents):
    @staticmethod
    def render(events: Iterable[simulation.HistoryEvent]) -> Mobject:
        eventsm = HistoryEvents.render(events)
        rect = SurroundingRectangle(
            eventsm,
            color=WHITE,
            stroke_width=1,
        )
        return VGroup(rect, eventsm)


class WorkflowTask(ProxyEntity[simulation.WorkflowTask]):
    def render(self, entity: simulation.WorkflowTask) -> Mobject:
        eventsm = BoxedHistoryEvents.render(entity.events)
        task = mobject.message("WFT")
        return VGroup(task, eventsm).arrange()


class WorkerRequest(VisualElement):
    def render(self, name: str) -> Mobject:
        return mobject.message(name)


class Workflow(ProxyEntityWithCode[simulation.Workflow]):
    pass


class WorkflowWorker(
    ProxyEntityWithChildren[simulation.WorkflowWorker, simulation.Workflow, Workflow]
):
    child_cls = Workflow
    child_align_direction = LEFT

    def render(self, _: simulation.WorkflowWorker) -> Mobject:
        return mobject.actor("Workflow Worker")

    @staticmethod
    def get_child_entities(
        entity: simulation.WorkflowWorker,
    ) -> List[simulation.Workflow]:
        return entity.workflows
