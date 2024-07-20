from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Optional

from manim import (
    DOWN,
    DR,
    LEFT,
    ORANGE,
    SMALL_BUFF,
    SurroundingRectangle,
    Text,
    VGroup,
    VMobject,
)

import esv
from scenes.worker import style

if TYPE_CHECKING:
    from scenes.worker.state_machines import StateMachine


class CommandType(Enum):
    SCHEDULE_ACTIVITY_TASK = 1
    START_TIMER = 2
    COMPLETE_WORKFLOW_EXECUTION = 3
    FAKE = 4


@dataclass
class Command(esv.Entity):
    command_type: CommandType
    coroutine_id: int
    machine: Optional["StateMachine"] = None

    @property
    def name(self) -> str:
        return self.command_type.name

    def render(self) -> VMobject:
        return Text(
            self.command_type.name,
            font=style.FONT_COMMAND,
            font_size=style.FONT_SIZE_COMMAND,
            color=ORANGE,
        )


@dataclass
class Commands(esv.Entity):
    commands: deque[Command]

    def __post_init__(self) -> None:
        super().__post_init__()
        for e in self.commands:
            self.children[e.name] = e

    def handle(self, event: "input.Event") -> bool:
        return False

    def render(self) -> VMobject:
        events = VGroup(*(e.mobj for e in self.commands)).arrange(
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
        return VGroup(rect, events).align_on_border(DR)
