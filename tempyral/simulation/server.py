import os
from asyncio import Queue
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Hashable, List, Optional, TypedDict, Union

from tempyral import log
from tempyral.simulation.api import (
    ApplicationRequest,
    ApplicationRequestType,
    Command,
    CommandType,
    HistoryEventType,
    NamespaceId,
    RespondActivityTaskCompleted,
    RespondWorkflowTaskCompleted,
    TaskQueueId,
    WorkerRequest,
    WorkflowId,
)
from tempyral.simulation.entity import Entity

if TYPE_CHECKING:
    from tempyral.simulation.worker import ActivityWorker, WorkflowWorker

DEFAULT_NAMESPACE: NamespaceId = "default"
NOOP_WORKFLOW_ID: WorkflowId = "noop-workflow"
CALL_ACTIVITY_WORKFLOW_ID: WorkflowId = "call-activity-workflow"


class HistoryEvent(Entity):
    def __init__(
        self,
        event_type: HistoryEventType,
        seen_by_sticky_worker=False,
        **kwargs: Hashable,
    ):
        super().__init__()
        self.event_type = event_type
        self.seen_by_sticky_worker = seen_by_sticky_worker
        self.data = kwargs

    def __repr__(self) -> str:
        star = "*" if self.seen_by_sticky_worker else ""
        data = f"({self.data})" if self.data else ""
        return f"{self.event_type.name}{star}{data}"


class History(Entity):
    """A workflow execution history"""

    def __init__(self, workflow_id: WorkflowId, events: List[HistoryEvent]) -> None:
        self.workflow_id = workflow_id
        self.events = events
        super().__init__()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(workflow_id={self.workflow_id},id={self.id}: events={self.events})"


class WorkflowTask(Entity):
    """A slice of history events"""

    def __init__(self, worklow_id: WorkflowId, events: List[HistoryEvent]) -> None:
        self.workflow_id = worklow_id
        self.events = events
        super().__init__()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id}: events={self.events})"


Namespace = OrderedDict[WorkflowId, History]
Shard = Dict[NamespaceId, Namespace]


@dataclass
class ActivityTask:
    workflow_id: WorkflowId


class TaskQueue(TypedDict):
    workflow_task_queue: List[WorkflowTask]
    activity_task_queue: List[ActivityTask]


class Server(Entity):
    def __init__(self):
        super().__init__()
        self.shards: List[Shard] = [
            {
                DEFAULT_NAMESPACE: OrderedDict(
                    {
                        NOOP_WORKFLOW_ID: History(NOOP_WORKFLOW_ID, []),
                        CALL_ACTIVITY_WORKFLOW_ID: History(
                            CALL_ACTIVITY_WORKFLOW_ID, []
                        ),
                    }
                )
            }
        ]
        self.task_queues: Dict[TaskQueueId, TaskQueue] = {}
        self.workflow_worker_long_poll_connections: Dict[
            WorkflowWorker, Queue[WorkflowTask]
        ] = {}
        self.activity_worker_long_poll_connections: Dict[
            ActivityWorker, Queue[ActivityTask]
        ] = {}

    def clone(self) -> "Server":
        cloned = Server()
        cloned.shards = deepcopy(self.shards)
        cloned.id = self.id
        return cloned

    def __repr__(self) -> str:
        namespace = {
            w: ", ".join(repr(e) for e in h.events)
            for w, h in self.namespace.items()
            if h.events
        }
        return f"{type(self).__name__}(id={self.id}: namespace={namespace})"

    async def handle_request(self, request: Union[ApplicationRequest, WorkerRequest]):
        workflow_id: WorkflowId
        match request:
            case ApplicationRequest(
                workflow_id, ApplicationRequestType.StartWorkflowExecution
            ):
                workflow_id = workflow_id
                await self.start_workflow_execution(workflow_id)
            case RespondWorkflowTaskCompleted(workflow_id, commands):
                workflow_id = workflow_id
                await self.handle_commands(workflow_id, commands)
            case RespondActivityTaskCompleted(workflow_id, result):
                workflow_id = workflow_id
                await self.handle_activity_task_completed(workflow_id, result)
            case _:
                raise ValueError(f"Server does not support request of type: {request}")

        # If this request resulted in new WFTs or ATs then dispatch them.
        await self.dispatch_activity_task(workflow_id)
        await self.dispatch_workflow_task(workflow_id)

        if os.path.exists("/tmp/flag"):
            self.terminate_simulation()

    async def start_workflow_execution(self, workflow_id: WorkflowId):
        await self.write_history_events(
            workflow_id,
            HistoryEventType.WF_STARTED,
            HistoryEventType.WFT_SCHEDULED,
            seen_by_sticky_worker=False,
        )

    # https://github.com/temporalio/temporal/blob/569a306daa2aef8e221712ae19d72219db4a4712/service/history/workflow_task_handler_callbacks.go#L386
    # https://github.com/temporalio/temporal/blob/569a306daa2aef8e221712ae19d72219db4a4712/service/history/workflow_task_handler.go#L166
    async def handle_commands(self, workflow_id, commands: List[Command]):
        for command in commands:
            match command.command_type:
                case CommandType.SCHEDULE_ACTIVITY_TASK:
                    await self.write_history_events(
                        workflow_id,
                        HistoryEventType.ACTIVITY_TASK_SCHEDULED,
                        seen_by_sticky_worker=False,
                    )
                case CommandType.COMPLETE_WORKFLOW_EXECUTION:
                    log(
                        "",
                        "S: Handling RespondWorkflowTaskCompleted([COMPLETE_WORKFLOW_EXECUTION])",
                    )
                    await self.write_history_events(
                        workflow_id,
                        HistoryEventType.WFT_COMPLETED,
                        HistoryEventType.WF_COMPLETED,
                        seen_by_sticky_worker=True,
                    )
                    self.terminate_simulation()
                case _:
                    raise ValueError(
                        f"Server does not support command of type: {command.command_type}"
                    )

    async def handle_activity_task_completed(
        self, workflow_id: WorkflowId, result: Any
    ):
        await self.write_history_events(
            workflow_id,
            HistoryEventType.ACTIVITY_TASK_COMPLETED,
            HistoryEventType.WFT_SCHEDULED,
            seen_by_sticky_worker=False,
            result=result,
        )

    async def write_history_events(
        self,
        workflow_id: WorkflowId,
        *events: HistoryEventType,
        seen_by_sticky_worker: bool,
        **kwargs: Hashable,
    ):
        self.namespace[workflow_id].events.extend(
            HistoryEvent(e, seen_by_sticky_worker=seen_by_sticky_worker, **kwargs)
            for e in events
        )
        await self.publish_change_event()

    def establish_workflow_worker_long_poll_connection(
        self, worker: "WorkflowWorker"
    ) -> None:
        self.workflow_worker_long_poll_connections[worker] = Queue()

    def establish_activity_worker_long_poll_connection(
        self, worker: "ActivityWorker"
    ) -> None:
        self.activity_worker_long_poll_connections[worker] = Queue()

    async def dispatch_workflow_task(self, workflow_id: WorkflowId):
        events = self.namespace[workflow_id].events
        if all(e.seen_by_sticky_worker for e in events):
            return

        await self.write_history_events(
            workflow_id, HistoryEventType.WFT_STARTED, seen_by_sticky_worker=False
        )
        wft = WorkflowTask(
            workflow_id,
            [e for e in events if not e.seen_by_sticky_worker],
        )
        for e in events:
            e.seen_by_sticky_worker |= True
        await self.publish_change_event()
        assert (
            len(self.workflow_worker_long_poll_connections) == 1
        ), "Multiple workflow workers not supported"
        [queue] = self.workflow_worker_long_poll_connections.values()
        await queue.put(wft)
        log(queue, "S: dispatch_workflow_task")

    async def dispatch_activity_task(
        self, workflow_id: WorkflowId
    ) -> Optional[ActivityTask]:
        # TODO: "sticky" should not apply to Activity Workers.
        undispatched = [
            e
            for e in self.namespace[workflow_id].events
            if e.event_type == HistoryEventType.ACTIVITY_TASK_SCHEDULED
            and not e.seen_by_sticky_worker
        ]
        if not undispatched:
            return
        assert len(undispatched) == 1, "Multiple undispatched activities not supported"

        await self.write_history_events(
            workflow_id,
            HistoryEventType.ACTIVITY_TASK_STARTED,
            seen_by_sticky_worker=False,
        )
        for e in undispatched:
            e.seen_by_sticky_worker |= True
        await self.publish_change_event()
        assert (
            len(self.activity_worker_long_poll_connections) == 1
        ), "Multiple activity workers not supported"
        [queue] = self.activity_worker_long_poll_connections.values()
        await queue.put(ActivityTask(workflow_id))
        log(queue, "S: dispatch_activity_task")

    @property
    def namespace(self) -> OrderedDict[WorkflowId, History]:
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
