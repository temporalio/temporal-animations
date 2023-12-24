from typing import List

from manim import DOWN, WHITE, Code, Mobject, Rectangle, Text, VGroup

from tempyral import simulation
from tempyral.animation.entity import (
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    MONOSPACE_FONT,
    ProxyEntity,
    VisualElement,
)
from tempyral.animation.history import HistoryEvents


class BoxedHistoryEvents(HistoryEvents):
    @staticmethod
    def newm(events: List[simulation.HistoryEvent]) -> Mobject:
        font_size = 16
        width = Text("_" * 30, font_size=font_size).width
        eventsm = HistoryEvents.newm(events, font_size)
        rect = Rectangle(
            width=max(width, eventsm.width) + 0.5,
            height=eventsm.height + 0.5,
            color=WHITE,
        )
        if events:
            rect.surround(eventsm)

        return VGroup(rect, eventsm)


class WorkflowTask(BoxedHistoryEvents):
    @staticmethod
    def newm(events: List[simulation.HistoryEvent]) -> Mobject:
        eventsm = BoxedHistoryEvents.newm(events)
        task = Text("WFT", font_size=16)
        return VGroup(task, eventsm).arrange()


class WorkerRequest(VisualElement):
    def newm(self, name: str) -> Mobject:
        return Text(name, font_size=FONT_SIZE_MEDIUM, font=MONOSPACE_FONT)


class WorkflowWorker(ProxyEntity[simulation.WorkflowWorker]):
    def newm(self, entity: simulation.WorkflowWorker) -> Mobject:
        text = Text("Workflow Worker", font_size=24)
        code = Code(code=entity.go, language="go", font_size=FONT_SIZE_SMALL)
        return VGroup(text, code).arrange(DOWN)
