from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

from manim import DR, RIGHT, VDict, VMobject

import esv
from manim_renderer.workflow_task import BoxedHistoryEvents
from schema import schema

if TYPE_CHECKING:
    from scenes.worker import input


HistoryEventId = int


HistoryEventType = schema.HistoryEventType


@dataclass
class HistoryEvent(schema.HistoryEvent):
    initiating_event_id: HistoryEventId = -1

    def __str__(self) -> str:
        return self.event_type.name


@dataclass
class History(esv.Entity):
    events: Iterable[HistoryEvent]

    def __post_init__(self):
        self.unapplied_events = deque(self.events)
        self.applied_events = deque([])
        super().__post_init__()

    def handle(self, event: "input.Event") -> bool:
        event.history_event.seen_by_worker = True
        self.applied_events.append(event.history_event)
        return True

    def render(self) -> VMobject:
        return VDict(
            {"unapplied": self._render_unapplied(), "applied": self._render_applied()}
        )

    def _render_unapplied(self) -> VMobject:
        return self._render_events(self.unapplied_events).align_on_border(DR)

    def _render_applied(self) -> VMobject:
        return self._render_events(self.applied_events).align_on_border(RIGHT)

    @staticmethod
    def _render_events(events: Iterable[HistoryEvent]) -> VMobject:
        return BoxedHistoryEvents.render(events, [])
