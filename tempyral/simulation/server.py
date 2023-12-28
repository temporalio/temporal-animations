import os
from asyncio import Queue
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Dict, Hashable, List, TypedDict, Union

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


class HistoryEvent(Entity):
    def __init__(
        self,
        event_type: HistoryEventType,
        seen_by_sticky_worker=False,
        **kwargs: Hashable,
    ):
        super().__init__()
        self.event_type = event_type
        self.seen_by_worker = seen_by_sticky_worker
        self.data = kwargs

    __publish__ = ["id", "seen_by_worker", "data", "event_type"]

    def __repr__(self) -> str:
        star = "*" if self.seen_by_worker else ""
        data = f"({self.data})" if self.data else ""
        return f"{self.event_type.name}{star}{data}"


class History(Entity):
    """A workflow execution history"""

    def __init__(self, workflow_id: WorkflowId, events: List[HistoryEvent]) -> None:
        self.workflow_id = workflow_id
        self.events = events
        super().__init__()

    __publish__ = ["id", "events"]

    def __repr__(self) -> str:
        return f"{type(self).__name__}(workflow_id={self.workflow_id},id={self.id}: events={self.events})"


class WorkflowTask(Entity):
    """A slice of history events"""

    def __init__(self, worklow_id: WorkflowId, events: List[HistoryEvent]) -> None:
        super().__init__()
        self.workflow_id = worklow_id
        self.events = tuple(events)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id}: events={self.events})"


Namespace = OrderedDict[WorkflowId, History]
Shard = Dict[NamespaceId, Namespace]


class ActivityTask(Entity):
    def __init__(self, workflow_id: WorkflowId, token: int):
        super().__init__()
        self.workflow_id = workflow_id
        self.token = token


class TaskQueue(TypedDict):
    workflow_task_queue: List[WorkflowTask]
    activity_task_queue: List[ActivityTask]


class Server(Entity):
    def __init__(self):
        super().__init__()
        self.shards: List[Shard] = [{DEFAULT_NAMESPACE: OrderedDict()}]
        self.task_queues: Dict[TaskQueueId, TaskQueue] = {}
        self.workflow_worker_long_poll_connections: Dict[
            WorkflowWorker, Queue[WorkflowTask]
        ] = {}
        self.activity_worker_long_poll_connections: Dict[
            ActivityWorker, Queue[ActivityTask]
        ] = {}

    __publish__ = ["id", "shards"]

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
            case RespondActivityTaskCompleted(workflow_id, result, token):
                workflow_id = workflow_id
                await self.handle_activity_task_completed(workflow_id, result, token)
            case _:
                raise ValueError(f"Server does not support request of type: {request}")

        # If this request resulted in new WFTs or ATs then dispatch them.
        await self.dispatch_workflow_or_activity_task(workflow_id)

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
                        token=command.token,
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
        self, workflow_id: WorkflowId, result: Any, token: int
    ):
        await self.write_history_events(
            workflow_id,
            HistoryEventType.ACTIVITY_TASK_COMPLETED,
            seen_by_sticky_worker=False,
            publish=False,
            result=result,
            token=token,
        )
        await self.write_history_events(
            workflow_id,
            HistoryEventType.WFT_SCHEDULED,
            seen_by_sticky_worker=False,
        )

    async def write_history_events(
        self,
        workflow_id: WorkflowId,
        *event_types: HistoryEventType,
        seen_by_sticky_worker: bool,
        publish=True,
        **kwargs: Hashable,
    ) -> List[HistoryEvent]:
        events = [
            HistoryEvent(e, seen_by_sticky_worker=seen_by_sticky_worker, **kwargs)
            for e in event_types
        ]
        self.namespace.setdefault(workflow_id, History(workflow_id, [])).events.extend(
            events
        )
        if publish:
            await self.publish_change_event()
        return events

    def establish_workflow_worker_long_poll_connection(
        self, worker: "WorkflowWorker"
    ) -> Queue[WorkflowTask]:
        connection = Queue()
        self.workflow_worker_long_poll_connections[worker] = connection
        return connection

    def establish_activity_worker_long_poll_connection(
        self, worker: "ActivityWorker"
    ) -> Queue[ActivityTask]:
        connection = Queue()
        self.activity_worker_long_poll_connections[worker] = connection
        return connection

    async def dispatch_workflow_or_activity_task(self, workflow_id: WorkflowId):
        events = iter(self.namespace[workflow_id].events)
        event = next((e for e in events if not e.seen_by_worker), None)
        if event is None:
            return
        events = [event] + list(events)
        assert all(
            not e.seen_by_worker for e in events
        ), "Expected seen_by_sticky_worker to define a unique high watermark"
        for e in events:
            e.seen_by_worker = True
        if any(
            e.event_type == HistoryEventType.ACTIVITY_TASK_SCHEDULED for e in events
        ):
            assert (
                len(events) == 1
            ), "Expected ACTIVITY_TASK_SCHEDULED event to be sole unseen event"
            [at_scheduled_event] = events
            events.extend(
                await self.write_history_events(
                    workflow_id,
                    HistoryEventType.ACTIVITY_TASK_STARTED,
                    seen_by_sticky_worker=True,
                )
            )
            [queue] = self.activity_worker_long_poll_connections.values()
            await queue.put(
                ActivityTask(workflow_id, token=int(at_scheduled_event.data["token"]))  # type: ignore
            )
        else:
            events.extend(
                await self.write_history_events(
                    workflow_id,
                    HistoryEventType.WFT_STARTED,
                    seen_by_sticky_worker=True,
                )
            )
            [queue] = self.workflow_worker_long_poll_connections.values()
            await queue.put(WorkflowTask(workflow_id, events))

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
