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
    Rectangle,
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
from tempyral.simulation.api import WorkflowId


class ActivityTask(ProxyEntity[simulation.ActivityTask]):
    def newm(self, entity: simulation.ActivityTask) -> Mobject:
        return Text(f"Activity Task({entity.workflow_id})", font_size=FONT_SIZE_MEDIUM)


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
        font_size = FONT_SIZE_MEDIUM
        width = Text("_" * 30, font_size=font_size).width
        eventsm = HistoryEvents.newm(events)
        rect = Rectangle(
            width=max(width, eventsm.width) + 0.5,
            height=eventsm.height + 0.5,
            color=WHITE,
        )
        if events:
            rect.surround(eventsm)

        return VGroup(rect, eventsm)


class WorkflowTask(ProxyEntity[simulation.WorkflowTask]):
    def newm(self, entity: simulation.WorkflowTask) -> Mobject:
        eventsm = BoxedHistoryEvents.newm(entity.events)
        task = Text(f"WFT({entity.workflow_id})", font_size=FONT_SIZE_MEDIUM)
        return VGroup(task, eventsm).arrange()


class WorkerRequest(VisualElement):
    def newm(self, name: str) -> Mobject:
        return Text(name, font_size=FONT_SIZE_MEDIUM, font=MONOSPACE_FONT)


class Workflow(ProxyEntity[simulation.Workflow]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.highlighted_line = None

    def newm(self, entity: simulation.Workflow) -> Mobject:
        text = Text(entity.workflow_id, font_size=FONT_SIZE_MEDIUM)
        code = Code(
            code=entity.code,
            insert_line_no=False,
            language=entity.language,
            font_size=FONT_SIZE_SMALL,
            line_spacing=1,
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
        return VGroup(text, VGroup(code, arrows)).arrange(DOWN)

    def highlight_line(self, line_num: int):
        arrows = self.m[1][1]
        if self.highlighted_line is not None:
            arrows[self.highlighted_line].set_color(BLACK)
        self.highlighted_line = line_num
        arrows[self.highlighted_line].set_color(PINK)


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
        return list(entity.workflows.values())
