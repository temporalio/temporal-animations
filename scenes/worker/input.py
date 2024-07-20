from dataclasses import dataclass
from typing import Iterable

import esv
from scenes.worker.commands import Command
from scenes.worker.history import HistoryEvent, HistoryEventType


@dataclass
class Event(esv.Event):
    history_event: HistoryEvent

    def __str__(self) -> str:
        return f"{self.__class__.__name__} {self.history_event}"


history_events = [
    HistoryEvent(id=1, event_type=HistoryEventType.WF_STARTED),
    HistoryEvent(id=2, event_type=HistoryEventType.WFT_SCHEDULED),
    HistoryEvent(id=3, event_type=HistoryEventType.WFT_STARTED, initiating_event_id=2),
    HistoryEvent(
        id=4, event_type=HistoryEventType.WFT_COMPLETED, initiating_event_id=2
    ),
    HistoryEvent(id=5, event_type=HistoryEventType.ACTIVITY_TASK_SCHEDULED),
    HistoryEvent(id=6, event_type=HistoryEventType.TIMER_STARTED),
]


def infer_commands(events: Iterable[HistoryEvent]) -> list[list["Command"]]:
    commands = []
    wft_commands: list["Command"] = []
    # TODO: We want to use 0 to mean main wf coroutine. But if another coroutine gets scheduled
    # before the main wf coroutine, then we're going to end up incorrectly assigning the coroutine
    # IDs here. Maybe we should not be inferring the commands from history.
    coroutine_id = 0
    for event in events:
        if event.event_type == HistoryEventType.WFT_STARTED:
            if wft_commands:
                commands.append(wft_commands)
                wft_commands = []
                coroutine_id = 0
        elif command_type := event.event_type.matching_command_type():
            wft_commands.append(Command(command_type, coroutine_id))
            coroutine_id += 1
    commands.append(wft_commands)
    return commands


commands = infer_commands(history_events)
