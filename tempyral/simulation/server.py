import os
from typing import Any, Dict, Hashable, List, Optional, TypedDict, Union

from tempyral import log
from tempyral.simulation.api import (
    ApplicationRequestType,
    Command,
    CommandType,
    HistoryEventType,
    RespondActivityTaskCompleted,
    RespondWorkflowTaskCompleted,
    WorkerRequestType,
)
from tempyral.simulation.entity import Entity

NamespaceId = str
WorkflowId = str
TaskQueueId = str

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
        return f"{self.event_type.name}{'*' if self.seen_by_sticky_worker else ''}({self.data if self.data else ''})"


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

    def __init__(self, worklow_id: WorkflowId, events: List[HistoryEvent]) -> None:
        self.workflow_id = worklow_id
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
        super().__init__()
        self.shards: List[Shard] = [
            {DEFAULT_NAMESPACE: [History(NOOP_WORKFLOW_ID, [])]}
        ]
        self.task_queues: Dict[TaskQueueId, TaskQueue] = {}

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id},{id(self)}: events={self.history.events})"

    async def handle_request(
        self, request: Union[ApplicationRequestType, WorkerRequestType]
    ):
        match request:
            case ApplicationRequestType.StartWorkflowExecution:
                await self.start_workflow_execution()
            case RespondWorkflowTaskCompleted(commands):
                await self.handle_commands(commands)
            case RespondActivityTaskCompleted(result):
                await self.handle_activity_task_completed(result)
            case _:
                raise ValueError(f"Server does not support request of type: {request}")

        if os.path.exists("/tmp/flag"):
            await self.terminate_simulation()

    async def start_workflow_execution(self):
        await self.write_history_events(
            HistoryEventType.WF_STARTED,
            HistoryEventType.WFT_SCHEDULED,
            seen_by_sticky_worker=False,
        )

    # https://github.com/temporalio/temporal/blob/569a306daa2aef8e221712ae19d72219db4a4712/service/history/workflow_task_handler_callbacks.go#L386
    # https://github.com/temporalio/temporal/blob/569a306daa2aef8e221712ae19d72219db4a4712/service/history/workflow_task_handler.go#L166
    async def handle_commands(self, commands: List[Command]):
        for command in commands:
            match command.command_type:
                case CommandType.SCHEDULE_ACTIVITY_TASK:
                    await self.write_history_events(
                        HistoryEventType.ACTIVITY_TASK_SCHEDULED,
                        seen_by_sticky_worker=False,
                    )
                case CommandType.COMPLETE_WORKFLOW_EXECUTION:
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
                    raise ValueError(
                        f"Server does not support command of type: {command.command_type}"
                    )

    async def handle_activity_task_completed(self, result: Any):
        await self.write_history_events(
            HistoryEventType.ACTIVITY_TASK_COMPLETED,
            HistoryEventType.WFT_SCHEDULED,
            seen_by_sticky_worker=False,
            result=result,
        )

    async def write_history_events(
        self, *events: HistoryEventType, seen_by_sticky_worker: bool, **kwargs: Hashable
    ):
        self.history.events.extend(
            HistoryEvent(
                e,
                seen_by_sticky_worker=seen_by_sticky_worker,
            )
            for e in events
        )
        await self.publish_change_event()

    async def dispatch_workflow_task(
        self, workflow_id: WorkflowId
    ) -> Optional[WorkflowTask]:
        if all(e.seen_by_sticky_worker for e in self.history.events):
            return

        await self.write_history_events(
            HistoryEventType.WFT_STARTED, seen_by_sticky_worker=False
        )
        wft = WorkflowTask(
            workflow_id,
            [e for e in self.history.events if not e.seen_by_sticky_worker],
        )
        for e in self.history.events:
            e.seen_by_sticky_worker |= True
        await self.publish_change_event()
        return wft

    async def dispatch_activity_task(self) -> Optional[ActivityTask]:
        # TODO: "sticky" should not apply to Activity Workers.
        undispatched = [
            e
            for e in self.history.events
            if e.event_type == HistoryEventType.ACTIVITY_TASK_SCHEDULED
            and not e.seen_by_sticky_worker
        ]
        if not undispatched:
            return
        assert len(undispatched) == 1, "Multiple undispatched activities not supported"

        await self.write_history_events(
            HistoryEventType.ACTIVITY_TASK_STARTED, seen_by_sticky_worker=False
        )
        for e in undispatched:
            e.seen_by_sticky_worker |= True
        await self.publish_change_event()
        return "fake-activity-task"

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
