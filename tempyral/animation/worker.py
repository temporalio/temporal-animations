from typing import Iterable, List

from manim import (
    BLACK,
    DOWN,
    LEFT,
    PINK,
    WHITE,
    Arrow,
    Code,
    Mobject,
    SurroundingRectangle,
    Text,
    VGroup,
)

from tempyral import simulation
from tempyral.animation.entity import (
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    MONOSPACE_FONT,
    ProxyEntity,
    ProxyEntityWithChildren,
    VisualElement,
)
from tempyral.animation.history import HistoryEvents


class ActivityTask(ProxyEntity[simulation.ActivityTask]):
    def newm(self, entity: simulation.ActivityTask) -> Mobject:
        return Text("Activity Task", font_size=FONT_SIZE_MEDIUM)


class ActivityTaskCompleted(VisualElement):
    def newm(self) -> Mobject:
        return Text(
            "ActivityTaskCompleted", font_size=FONT_SIZE_MEDIUM, font=MONOSPACE_FONT
        )


class ActivityWorker(ProxyEntity[simulation.ActivityWorker]):
    @staticmethod
    def newm(_: simulation.ActivityWorker) -> Mobject:
        return Text("Activity Worker", font_size=FONT_SIZE_LARGE)


class BoxedHistoryEvents(HistoryEvents):
    @staticmethod
    def newm(events: Iterable[simulation.HistoryEvent]) -> Mobject:
        eventsm = HistoryEvents.newm(events)
        rect = SurroundingRectangle(
            eventsm,
            color=WHITE,
            stroke_width=1,
        )
        return VGroup(rect, eventsm)


class WorkflowTask(ProxyEntity[simulation.WorkflowTask]):
    def newm(self, entity: simulation.WorkflowTask) -> Mobject:
        eventsm = BoxedHistoryEvents.newm(entity.events)
        task = Text("WFT", font_size=FONT_SIZE_MEDIUM)
        return VGroup(task, eventsm).arrange()


class WorkerRequest(VisualElement):
    def newm(self, name: str) -> Mobject:
        return Text(name, font_size=FONT_SIZE_MEDIUM, font=MONOSPACE_FONT)


class Workflow(ProxyEntity[simulation.Workflow]):
    def newm(self, entity: simulation.Workflow) -> Mobject:
        code = Code(
            code=entity.code,
            language=entity.language,
            insert_line_no=False,
            font_size=FONT_SIZE_SMALL,
            line_spacing=1,
            background_stroke_width=0,
        ).to_edge(LEFT, buff=1.0)
        lines = code[2]
        arrows = VGroup(
            *(
                Arrow(
                    start=line.get_edge_center(LEFT) + LEFT,
                    end=line.get_edge_center(LEFT),
                    color=BLACK,
                )
                .next_to(line, LEFT, buff=0.1)
                .shift(DOWN * 0.075)
                for line in lines
            )
        )
        for line_num in entity.blocked_expressions:
            arrows[line_num - 1].set_color(PINK)
        return VGroup(code, arrows)


class WorkflowWorker(
    ProxyEntityWithChildren[simulation.WorkflowWorker, simulation.Workflow, Workflow]
):
    child_cls = Workflow
    child_align_direction = LEFT

    @staticmethod
    def newm(_: simulation.WorkflowWorker) -> Mobject:
        return Text("Workflow Worker", font_size=FONT_SIZE_LARGE)

    @staticmethod
    def get_child_entities(
        entity: simulation.WorkflowWorker,
    ) -> List[simulation.Workflow]:
        return entity.workflows
