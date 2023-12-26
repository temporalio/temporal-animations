import os
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


class HistoryEvent(Entity):
    def __init__(self, event_type: HistoryEventType, seen_by_sticky_worker=False):
        super().__init__()
        self.event_type = event_type
        self.seen_by_sticky_worker = seen_by_sticky_worker

    def __repr__(self) -> str:
        return f"{self.event_type.name}{'*' if self.seen_by_sticky_worker else ''}"


class History(Entity):
    """A workflow execution history"""

    def __init__(self, workflow_id: WorkflowId, events: List[HistoryEvent]) -> None:
        self.workflow_id = workflow_id
        self.events = events
        super().__init__()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(workflow_id={self.workflow_id},id={self.id},{id(self)}: events={self.events})"


class WorkflowTask(Entity):
    """A slice of history events"""

    def __init__(self, events: List[HistoryEvent]) -> None:
        self.events = events
        super().__init__()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id},{id(self)}: events={self.events})"


Namespace = List[History]
Shard = Dict[NamespaceId, Namespace]
ActivityTask = str


class TaskQueue(TypedDict):
    workflow_task_queue: List[WorkflowTask]
    activity_task_queue: List[ActivityTask]


class Server(Entity):
    def __init__(self):
        self.shards: List[Shard] = [
            {DEFAULT_NAMESPACE: [History(DEFAULT_WORKFLOW_ID, [])]}
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
                    HistoryEventType.WF_STARTED,
                    HistoryEventType.WFT_SCHEDULED,
                    seen_by_sticky_worker=False,
                )
                if os.path.exists("/tmp/flag"):
                    await self.terminate_simulation()
            case RespondWorkflowTaskCompleted([Command.COMPLETE_WORKFLOW_EXECUTION]):
                log(
                    "",
                    "S: Handling RespondWorkflowTaskCompleted([COMPLETE_WORKFLOW_EXECUTION])",
                )
                await self.write_history_events(
                    HistoryEventType.WFT_COMPLETED,
                    HistoryEventType.WF_COMPLETED,
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
        await self.publish_change_event()

    async def dispatch_workflow_task(self) -> Optional[WorkflowTask]:
        if all(e.seen_by_sticky_worker for e in self.history.events):
            return

        await self.write_history_events(
            HistoryEventType.WFT_STARTED, seen_by_sticky_worker=False
        )
        wft = WorkflowTask(
            [e for e in self.history.events if not e.seen_by_sticky_worker]
        )
        for e in self.history.events:
            e.seen_by_sticky_worker |= True
        await self.publish_change_event()
        return wft

    @property
    def history(self) -> History:
        """
        Return the history of the sole workflow execution.
        """
        try:
            [history] = self.namespace
        except ValueError:
            raise ValueError("Multiple workflow executions are not supported")
        return history

    @property
    def namespace(self) -> List[History]:
        """
        Return the sole namespace.

        The simulation currently supports one namespace only.
        """
        try:
            [shard] = self.shards
        except ValueError:
            raise ValueError("Multiple history shards are not supported")
        try:
            [namespace] = shard.values()
        except ValueError:
            raise ValueError("Multiple namespaces are not supported")
        return namespace
