from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Iterable, Optional

from manim import (
    DL,
    DOWN,
    GREEN,
    LEFT,
    RED,
    SMALL_BUFF,
    SurroundingRectangle,
    Text,
    VGroup,
    VMobject,
)

import esv
from scenes.worker import style
from scenes.worker.commands import CommandType

if TYPE_CHECKING:
    from scenes.worker import input
    from scenes.worker.worker_scene import WorkerScene


HistoryEventId = int


# https://github.com/temporalio/api/blob/master/temporal/api/enums/v1/event_type.proto#L35
class HistoryEventType(Enum):
    WF_STARTED = 1
    WF_COMPLETED = 2
    WF_FAILED = 3
    WFT_SCHEDULED = 5
    WFT_STARTED = 6
    WFT_COMPLETED = 7
    WFT_FAILED = 9
    ACTIVITY_TASK_SCHEDULED = 10
    ACTIVITY_TASK_STARTED = 11
    ACTIVITY_TASK_COMPLETED = 12
    ACTIVITY_TASK_FAILED = 13
    TIMER_STARTED = 17
    TIMER_FIRED = 18
    WF_SIGNALED = 26
    WF_UPDATE_ACCEPTED = 41
    WF_UPDATE_REJECTED = 42
    WF_UPDATE_COMPLETED = 43

    def matching_command_type(self) -> Optional[CommandType]:
        return _event_type_to_command_type.get(self)

    def is_command_event(self) -> bool:
        return self.matching_command_type() is not None

    def matches_command_type(self, command_type: CommandType):
        return self.matching_command_type() == command_type


_event_type_to_command_type = {
    HistoryEventType.ACTIVITY_TASK_SCHEDULED: CommandType.SCHEDULE_ACTIVITY_TASK,
    HistoryEventType.TIMER_STARTED: CommandType.START_TIMER,
    HistoryEventType.WF_COMPLETED: CommandType.COMPLETE_WORKFLOW_EXECUTION,
}


@dataclass
class HistoryEvent(esv.Entity):
    id: int
    event_type: HistoryEventType
    seen_by_worker: bool = False
    initiating_event_id: HistoryEventId = -1

    @property
    def _name(self) -> str:
        return f"{self.id} {self.event_type.name}"

    def render(self) -> VMobject:
        return Text(
            self.event_type.name,
            font=style.FONT_HISTORY_EVENT,
            font_size=style.FONT_SIZE_HISTORY_EVENT,
            color=GREEN if self.seen_by_worker else RED,
        )

    def handle(self, event: "input.Event") -> bool:
        if event.history_event != self:
            return False
        self.explain()
        scene: WorkerScene = self.scene  # type: ignore # TODO
        self.move_to(scene.state_machines)
        self.seen_by_worker = True
        return True

    def explain(self):
        match self.event_type:
            case HistoryEventType.WFT_SCHEDULED:
                super().explain(
                    r"""
                    WORKFLOW\_TASK\_SCHEDULED is the first event in a sequence of
                    workflow task events. When the state machines encounter this
                    event, they create a new instance of WorkflowTaskStateMachine. 
                    """
                )
            case HistoryEventType.WFT_STARTED:
                super().explain(
                    r"""
                    WORKFLOW\_TASK\_STARTED is handled by the instance of
                    WorkflowTaskStateMachine that was created previously. It runs
                    all coroutines until blocked. This is the first time we're
                    executing user code, so you'll see the main workflow coroutine
                    come into existence, along with a child coroutine that it
                    creates.
                    """
                )
            case HistoryEventType.TIMER_STARTED:
                super().explain(
                    r"""We're seeing TIMER\_STARTED because in a previous workflow task, some user code
                    made a call to `sleep(duration)`."""
                )

    def __str__(self) -> str:
        return self._name


@dataclass
class History(esv.Entity):
    events: Iterable[HistoryEvent]

    def __post_init__(self) -> None:
        super().__post_init__()
        for e in self.events:
            self.children[e._name] = e

    def handle(self, event: "input.Event") -> bool:
        return False

    def render(self) -> VMobject:
        events = VGroup(*(e.mobj for e in self.events)).arrange(
            DOWN, buff=SMALL_BUFF, aligned_edge=LEFT
        )
        rect = SurroundingRectangle(
            events,
            color=style.COLOR_HISTORY_EVENT_GROUP_RECT,
            stroke_width=style.STROKE_WIDTH_HISTORY_EVENT_GROUP_RECT,
            fill_color=style.COLOR_SCENE_BACKGROUND,
            fill_opacity=1,
            corner_radius=style.RECT_CORNER_RADIUS,
        )
        return VGroup(rect, events).align_on_border(DL)
