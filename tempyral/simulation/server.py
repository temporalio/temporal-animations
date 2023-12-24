from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, TypedDict, Union

from tempyral import log
from tempyral.simulation.api import (
    ApplicationRequestType,
    Command,
    HistoryEventType,
    RespondWorkflowTaskCompleted,
    WorkerRequestType,
)
from tempyral.simulation.entity import Entity

NamespaceId = str
WorkflowId = str
TaskQueueId = str

DEFAULT_NAMESPACE = "default"
DEFAULT_WORKFLOW_ID = "wid"


@dataclass
class HistoryEvent:
    event_type: HistoryEventType
    seen_by_sticky_worker: bool = False

    def __repr__(self) -> str:
        return f"{self.event_type.name}{'*' if self.seen_by_sticky_worker else ''}"


class HistoryEvents(Entity):
    """A slice of history events"""

    def __init__(self, events: List[HistoryEvent]) -> None:
        self.events = events


WorkflowTask = HistoryEvents
ActivityTask = str

Shard = Dict[NamespaceId, Dict[WorkflowId, HistoryEvents]]


class TaskQueue(TypedDict):
    workflow_task_queue: List[WorkflowTask]
    activity_task_queue: List[ActivityTask]


class Server(Entity):
    def __init__(self):
        self.shards: List[Shard] = [
            {DEFAULT_NAMESPACE: {DEFAULT_WORKFLOW_ID: HistoryEvents([])}}
        ]
        self.task_queues: Dict[TaskQueueId, TaskQueue] = {}
        super().__init__()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id},{id(self)}: events={self.history.events})"

    async def handle_request(
        self, request: Union[ApplicationRequestType, WorkerRequestType]
    ):
        match request:
            case ApplicationRequestType.StartWorkflowExecution:
                log("", "S: handling StartWorkflowExecution")
                await self.write_history_events(
                    HistoryEventType.WORKFLOW_EXECUTION_STARTED,
                    HistoryEventType.WORKFLOW_TASK_SCHEDULED,
                    seen_by_sticky_worker=False,
                )
            case RespondWorkflowTaskCompleted([Command.COMPLETE_WORKFLOW_EXECUTION]):
                log(
                    "",
                    "S: Handling RespondWorkflowTaskCompleted([COMPLETE_WORKFLOW_EXECUTION])",
                )
                await self.write_history_events(
                    HistoryEventType.WORKFLOW_TASK_COMPLETED,
                    HistoryEventType.WORKFLOW_EXECUTION_COMPLETED,
                    seen_by_sticky_worker=True,
                )
                await self.terminate_simulation()
            case _:
                raise ValueError(f"Server does not support request of type: {request}")

    async def write_history_events(
        self, *events: HistoryEventType, seen_by_sticky_worker: bool
    ):
        self.history.events.extend(
            HistoryEvent(
                e,
                seen_by_sticky_worker=seen_by_sticky_worker,
            )
            for e in events
        )
        await self.publish_change_event(new_history_events=len(events))

    async def dispatch_workflow_task(self) -> Optional[WorkflowTask]:
        if all(e.seen_by_sticky_worker for e in self.history.events):
            return

        await self.write_history_events(
            HistoryEventType.WORKFLOW_TASK_STARTED, seen_by_sticky_worker=False
        )
        wft = WorkflowTask(
            [e for e in self.history.events if not e.seen_by_sticky_worker]
        )
        for e in self.history.events:
            e.seen_by_sticky_worker |= True
        await self.publish_change_event()
        return wft

    @property
    def history(self) -> HistoryEvents:
        """
        Currently, the simulation only supports a single workflow execution.
        Return its history.
        """
        try:
            [shard] = self.shards
        except ValueError:
            raise ValueError("Multiple history shards are not supported")
        try:
            [namespace] = shard.values()
        except ValueError:
            raise ValueError("Multiple namespaces are not supported")
        try:
            [history] = namespace.values()
        except ValueError:
            raise ValueError("Multiple workflow executions are not supported")
        return history
