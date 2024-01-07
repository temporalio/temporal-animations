from asyncio import Queue
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, Hashable, List, Tuple, TypedDict, cast
from uuid import uuid4

from common.logger import log
from common.utils import drain
from tempyral.api import (
    ApplicationRequestType,
    Command,
    CommandType,
    HistoryEventType,
    NamespaceId,
    ProtocolInstanceId,
    ProtocolMessage,
    ProtocolMessageType,
    TaskQueueId,
    WorkflowId,
)
from tempyral.entity import Entity
from tempyral.event import emit_change_event
from tempyral.request_response import (
    ActivityTask,
    ActivityTaskCompleted,
    ApplicationRequest,
    RequestResponseStage,
    WorkerPollRequest,
    WorkerRequest,
    WorkflowTask,
    WorkflowTaskCompleted,
)

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

    __publish__ = Entity.__publish__ | {"seen_by_worker", "data", "event_type"}

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

    __publish__ = Entity.__publish__ | {"events", "workflow_id"}

    def __repr__(self) -> str:
        return f"{type(self).__name__}(workflow_id={self.workflow_id},id={self.id}: events={self.events})"


@dataclass
class UpdateInfo(Entity):
    update_id: ProtocolInstanceId
    update_name: str

    __publish__ = {"update_id", "update_name"}


@dataclass
class WorkflowData(Entity):
    history: History
    pending_updates: List[UpdateInfo]

    __publish__ = {"history", "pending_updates"}


Namespace = OrderedDict[WorkflowId, WorkflowData]
Shard = Dict[NamespaceId, Namespace]


class TaskQueue(TypedDict):
    workflow_task_queue: Queue[WorkflowTask]
    activity_task_queue: Queue[ActivityTask]


class Server(Entity):
    def __init__(self):
        super().__init__()
        self.shards: List[Shard] = [{DEFAULT_NAMESPACE: OrderedDict()}]
        self.task_queues: Dict[TaskQueueId, TaskQueue] = {}
        self.pending_application_requests: Dict[
            NamespaceId,
            OrderedDict[Tuple[ApplicationRequestType, WorkflowId], Queue[HistoryEvent]],
        ] = {DEFAULT_NAMESPACE: OrderedDict()}
        self.workflow_task_queue: Dict[
            NamespaceId,
            Queue[WorkflowTask],
        ] = {DEFAULT_NAMESPACE: Queue()}
        self.activity_task_queue: Dict[
            NamespaceId,
            Queue[ActivityTask],
        ] = {DEFAULT_NAMESPACE: Queue()}

    __publish__ = Entity.__publish__ | {"shards"}

    def __repr__(self) -> str:
        namespace = {
            w: ", ".join(repr(e) for e in wd.history.events)
            for w, wd in self.namespace.items()
            if wd.history.events
        }
        return (
            f"{type(self).__name__}[{self.time}](id={self.id}: namespace={namespace})"
        )

    def should_schedule_wft(self, workflow_id: WorkflowId) -> bool:
        """
        A WFT should be scheduled if there is not one already pending, and any
        of the following are true:

        - There are unseen history events that could advance workflow history
        - There are pending updates
        """
        wf_data = self.get_workflow_data(workflow_id)

        events_might_advance_workflow_execution = False
        for e in wf_data.history.events:
            if e.seen_by_worker:
                continue
            if e.event_type == HistoryEventType.WFT_SCHEDULED:
                return False
            if e.event_type in [
                HistoryEventType.WF_STARTED,
                HistoryEventType.ACTIVITY_TASK_COMPLETED,
                HistoryEventType.TIMER_FIRED,
                HistoryEventType.WF_SIGNALED,
            ]:
                events_might_advance_workflow_execution = True

        return events_might_advance_workflow_execution or bool(wf_data.pending_updates)

    async def handle_application_request(self, request: ApplicationRequest):
        """
        In general, an application request is handled as follows:

        1. Mutate the received RequestResponse object so that it is now marked as a Response
        2. Create a new channel representing the request being handled
        3. Append some history events or pending updates/queries etc
        4. Append a WFT_SCHEDULED event if there is not one already
        5. Block until a value is written to the channel
        6. Return the same RequestResponse object that was received
        """
        self.tick(request)
        request.stage = RequestResponseStage.Response
        emit_change_event(self)
        match request.request_type:
            case ApplicationRequestType.StartWorkflow:
                await self.start_workflow(request)
            case ApplicationRequestType.GetWorkflowResult:
                await self.get_workflow_result(request)
            case ApplicationRequestType.ExecuteUpdate:
                await self.execute_update(request)
            case ApplicationRequestType.SignalWorkflow:
                await self.signal_workflow(request)
            case _:
                raise ValueError(f"Server does not support request of type: {request}")

    async def handle_worker_poll_request[
        T: WorkflowTask | ActivityTask
    ](self, request: WorkerPollRequest[T]) -> WorkerPollRequest[T]:
        self.tick(request)
        request.stage = RequestResponseStage.Response
        # TODO:
        queue = cast(
            Queue[T],
            (
                self.workflow_task_queue
                if isinstance(request.task, WorkflowTask)
                else self.activity_task_queue
            )[DEFAULT_NAMESPACE],
        )

        task = await queue.get()
        request.time = self.time
        request.task = task
        # TODO: Do not copy tokens to request
        request.token = cast(int, next(e.data.get("token", 0) for e in task.events))
        return request

    async def handle_worker_request(self, request: WorkerRequest):
        self.tick(request)
        request.stage = RequestResponseStage.Response
        emit_change_event(self)
        match request:
            case WorkflowTaskCompleted(workflow_id, commands):
                await self.handle_commands(workflow_id, commands)
            case ActivityTaskCompleted(workflow_id, result, token):
                await self.handle_activity_task_completed(workflow_id, result, token)
            case _:
                raise ValueError(f"Server does not support request of type: {request}")

    # The following are non-blocking requests; we don't need to wait for a
    # HistoryEvent to be written, beyond those we write synchronously on
    # handling the request.

    async def start_workflow(self, request: ApplicationRequest):
        await self._handle_non_blocking_application_request(
            request, HistoryEventType.WF_STARTED
        )

    async def signal_workflow(self, request: ApplicationRequest):
        await self._handle_non_blocking_application_request(
            request, HistoryEventType.WF_SIGNALED
        )

    async def _handle_non_blocking_application_request(
        self, request: ApplicationRequest, event_to_be_written: HistoryEventType
    ):
        [event] = await self.write_history_events(
            request.workflow_id,
            [event_to_be_written],
            seen_by_sticky_worker=False,
        )
        request.response_payload = event.data.get("payload")
        emit_change_event(self)

    # The following are blocking requests; they use
    # _handle_blocking_application_request to wait for a certain
    # HistoryEvent to be written that indicates that the application request has
    # been fulfilled.

    async def get_workflow_result(self, request: ApplicationRequest):
        event = await self._handle_blocking_application_request(request, None)
        request.response_payload = event.data.get("payload")

    async def execute_update(self, request: ApplicationRequest):
        self.get_workflow_data(request.workflow_id).pending_updates.append(
            UpdateInfo(update_id=uuid4().hex, update_name="fake-update-name")
        )
        event = await self._handle_blocking_application_request(request, None)
        request.response_payload = event.data.get("payload")

    async def _handle_blocking_application_request(
        self, request: ApplicationRequest, event_to_be_written: HistoryEventType | None
    ) -> HistoryEvent:
        """
        Handle request by writing history events, and return response.

        When handling an application request, we create a new channel
        (maxsize=1) and block, waiting for the response to be pushed to the
        channel. The value pushed to the channel is a HistoryEvent that contains
        within it information needed to unblock the corresponding client-side
        awaitable.
        """

        chans = self.pending_application_requests[DEFAULT_NAMESPACE]
        key = request.request_type, request.workflow_id
        assert (
            key not in chans
        ), "Multiple concurrent requests of same type for same workflow ID are not supported"
        chan: Queue[HistoryEvent] = Queue(maxsize=1)
        chans[key] = chan
        emit_change_event(self)

        if event_to_be_written:
            await self.write_history_events(
                request.workflow_id,
                [event_to_be_written],
                seen_by_sticky_worker=False,
            )
        if self.should_schedule_wft(request.workflow_id):
            await self.write_history_events(
                request.workflow_id,
                [HistoryEventType.WFT_SCHEDULED],
                seen_by_sticky_worker=False,
            )

        event = await chan.get()
        del chans[key]
        emit_change_event(self)
        return event

    # https://github.com/temporalio/temporal/blob/569a306daa2aef8e221712ae19d72219db4a4712/service/history/workflow_task_handler_callbacks.go#L386
    # https://github.com/temporalio/temporal/blob/569a306daa2aef8e221712ae19d72219db4a4712/service/history/workflow_task_handler.go#L166
    async def handle_commands(self, workflow_id, commands: List[Command]):
        chans = self.pending_application_requests[DEFAULT_NAMESPACE]

        await self.write_history_events(
            workflow_id,
            [HistoryEventType.WFT_COMPLETED],
            seen_by_sticky_worker=True,
        )

        for command in commands:
            match command.command_type:
                case CommandType.SCHEDULE_ACTIVITY_TASK:
                    await self.write_history_events(
                        workflow_id,
                        [HistoryEventType.ACTIVITY_TASK_SCHEDULED],
                        seen_by_sticky_worker=False,
                        token=command.token,
                    )
                case CommandType.COMPLETE_WORKFLOW_EXECUTION:
                    log(
                        "",
                        "S: Handling RespondWorkflowTaskCompleted([COMPLETE_WORKFLOW_EXECUTION])",
                    )
                    [event] = await self.write_history_events(
                        workflow_id,
                        [HistoryEventType.WF_COMPLETED],
                        seen_by_sticky_worker=True,
                    )
                    for request_type in [
                        ApplicationRequestType.GetWorkflowResult,
                        ApplicationRequestType.GetWorkflowResult,
                    ]:
                        key = request_type, workflow_id
                        if key in chans:
                            await chans[key].put(event)
                case CommandType.PROTOCOL_MESSAGE:
                    assert command.protocol_message
                    match command.protocol_message:
                        # TODO: Make Accepted and Rejected do something; use update_id
                        case ProtocolMessage(
                            ProtocolMessageType.UPDATE_ACCEPTED, update_id
                        ):
                            await self.write_history_events(
                                workflow_id,
                                [HistoryEventType.WF_UPDATE_ACCEPTED],
                                seen_by_sticky_worker=True,
                            )
                        case ProtocolMessage(
                            ProtocolMessageType.UPDATE_REJECTED, update_id
                        ):
                            await self.write_history_events(
                                workflow_id,
                                [HistoryEventType.WF_UPDATE_REJECTED],
                                seen_by_sticky_worker=True,
                            )
                        case ProtocolMessage(
                            ProtocolMessageType.UPDATE_COMPLETED, update_id
                        ):
                            [event] = await self.write_history_events(
                                workflow_id,
                                [HistoryEventType.WF_UPDATE_COMPLETED],
                                seen_by_sticky_worker=True,
                            )
                            key = ApplicationRequestType.ExecuteUpdate, workflow_id
                            await chans[key].put(event)
                case _:
                    raise ValueError(
                        f"Server does not support command of type: {command.command_type}"
                    )

    async def handle_activity_task_completed(
        self, workflow_id: WorkflowId, result: Any, token: int
    ):
        await self.write_history_events(
            workflow_id,
            [HistoryEventType.ACTIVITY_TASK_COMPLETED],
            seen_by_sticky_worker=False,
            publish=False,
            result=result,
            token=token,
        )
        if self.should_schedule_wft(workflow_id):
            await self.write_history_events(
                workflow_id,
                [HistoryEventType.WFT_SCHEDULED],
                seen_by_sticky_worker=False,
            )

    async def write_history_events(
        self,
        workflow_id: WorkflowId,
        event_types: List[HistoryEventType],
        seen_by_sticky_worker: bool,
        publish=True,
        **kwargs: Hashable,
    ) -> List[HistoryEvent]:
        events = [
            HistoryEvent(e, seen_by_sticky_worker=seen_by_sticky_worker, **kwargs)
            for e in event_types
        ]
        self.get_workflow_data(workflow_id).history.events.extend(events)
        if publish:
            emit_change_event(self)
        await self.dispatch_workflow_or_activity_task(workflow_id)
        return events

    async def dispatch_workflow_or_activity_task(self, workflow_id: WorkflowId):
        events = iter(self.namespace[workflow_id].history.events)
        event = next((e for e in events if not e.seen_by_worker), None)
        if event is None:
            return
        events = [event] + list(events)
        assert all(
            not e.seen_by_worker for e in events
        ), "Expected seen_by_sticky_worker to define a unique high watermark"
        if any(
            e.event_type == HistoryEventType.ACTIVITY_TASK_SCHEDULED for e in events
        ):
            assert (
                len(events) == 1
            ), "Expected ACTIVITY_TASK_SCHEDULED event to be sole unseen event"
            for e in events:
                e.seen_by_worker = True
            [scheduled_event] = events
            events.extend(
                await self.write_history_events(
                    workflow_id,
                    [HistoryEventType.ACTIVITY_TASK_STARTED],
                    seen_by_sticky_worker=True,
                )
            )
            await self.activity_task_queue[DEFAULT_NAMESPACE].put(
                ActivityTask(workflow_id, [scheduled_event])
            )
        elif any(e.event_type == HistoryEventType.WFT_SCHEDULED for e in events):
            for e in events:
                e.seen_by_worker = True
            events.extend(
                await self.write_history_events(
                    workflow_id,
                    [HistoryEventType.WFT_STARTED],
                    seen_by_sticky_worker=True,
                )
            )
            pending_updates = drain(self.namespace[workflow_id].pending_updates)
            await self.workflow_task_queue[DEFAULT_NAMESPACE].put(
                WorkflowTask(workflow_id, events, pending_updates)
            )

    @property
    def namespace(self) -> OrderedDict[WorkflowId, WorkflowData]:
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

    def get_workflow_data(self, workflow_id: WorkflowId) -> WorkflowData:
        return self.namespace.setdefault(
            workflow_id, WorkflowData(History(workflow_id, []), [])
        )
