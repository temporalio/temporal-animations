from dataclasses import dataclass
from typing import Dict, List, TypedDict, Union

from tempyral.simulation.api import (
    ApplicationRequestType,
    HistoryEventType,
    WorkerRequestType,
)
from tempyral.simulation.entity import Entity
from tempyral.simulation.worker import WorkflowWorker

NamespaceId = str
WorkflowId = str
TaskQueueId = str

DEFAULT_NAMESPACE = "default"
DEFAULT_WORKFLOW_ID = "wid"


@dataclass
class HistoryEvent:
    event_type: HistoryEventType
    seen_by_sticky_worker: bool = False


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

    async def handle_request(
        self, request: Union[ApplicationRequestType, WorkerRequestType]
    ):
        match request:
            case ApplicationRequestType.StartWorkflow:
                self.history.events.extend(
                    [
                        HistoryEvent(HistoryEventType.WORKFLOW_EXECUTION_STARTED),
                        HistoryEvent(HistoryEventType.WORKFLOW_TASK_SCHEDULED),
                    ]
                )
                await self.publish_change_event()
            case WorkerRequestType.RespondWorkflowTaskCompleted:
                self.history.events.append(
                    HistoryEvent(
                        HistoryEventType.WORKFLOW_TASK_COMPLETED,
                        seen_by_sticky_worker=True,
                    )
                )
                await self.publish_change_event(new_history_events=1)
            case _:
                raise ValueError(f"Server does not support request of type: {request}")

    async def dispatch_wft_if_new_events(self, worker: WorkflowWorker) -> None:
        if all(e.seen_by_sticky_worker for e in self.history.events):
            return

        self.history.events.append(HistoryEvent(HistoryEventType.WORKFLOW_TASK_STARTED))
        await self.publish_change_event()
        wft = WorkflowTask(
            [e for e in self.history.events if not e.seen_by_sticky_worker]
        )
        for e in self.history.events:
            e.seen_by_sticky_worker |= True
        await self.publish_change_event()
        await self.publish_message_event(self, worker, events=wft.events)
        await worker.handle_wft(wft, self)

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
