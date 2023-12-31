import os
from asyncio import Queue
from collections import OrderedDict
from typing import TYPE_CHECKING, Any, Dict, Hashable, List, Tuple, TypedDict
from uuid import uuid4

from attr import dataclass

from log import log
from manim_renderer.utils import drain
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
from tempyral.message import ApplicationRequest

if TYPE_CHECKING:
    from tempyral.worker import ActivityWorker, WorkflowWorker

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
class UpdateInfo:
    update_id: ProtocolInstanceId
    update_name: str


@dataclass
class WorkflowData:
    history: History
    pending_updates: List[UpdateInfo]


class WorkflowTask(Entity):
    """A slice of history events"""

    def __init__(
        self,
        worklow_id: WorkflowId,
        time: int,
        events: List[HistoryEvent],
        pending_updates: List[UpdateInfo],
    ) -> None:
        super().__init__(time)
        self.workflow_id = worklow_id
        self.events = tuple(events)
        self.pending_updates = tuple(pending_updates)

    __publish__ = Entity.__publish__ | {"events", "pending_updates"}

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id}: events={self.events}, updates={self.pending_updates})"


Namespace = OrderedDict[WorkflowId, WorkflowData]
Shard = Dict[NamespaceId, Namespace]


class ActivityTask(Entity):
    def __init__(self, workflow_id: WorkflowId, time: int, token: int):
        super().__init__(time)
        self.workflow_id = workflow_id
        self.token = token


class WorkerRequest(Entity):
    def __init__(self, workflow_id: WorkflowId, time: int):
        super().__init__(time)
        self.workflow_id = workflow_id


class WorkflowTaskCompleted(WorkerRequest):
    __match_args__ = ("workflow_id", "commands")

    def __init__(self, workflow_id: WorkflowId, time: int, commands: List[Command]):
        super().__init__(workflow_id, time)
        self.commands = commands


class ActivityTaskCompleted(WorkerRequest):
    __match_args__ = ("workflow_id", "result", "token")

    def __init__(self, workflow_id: WorkflowId, time: int, result: Any, token: int):
        super().__init__(workflow_id, time)
        self.result = result
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
        self.in_flight_application_request_channels: Dict[
            NamespaceId,
            OrderedDict[Tuple[ApplicationRequestType, WorkflowId], Queue[HistoryEvent]],
        ] = {DEFAULT_NAMESPACE: OrderedDict()}

    __publish__ = Entity.__publish__ | {"shards", "in_flight_application_request_types"}

    # Computed property published to event bus without the underscore prefix.
    in_flight_application_request_types: List[str]

    @property
    def _in_flight_application_request_types(self) -> List[str]:
        return [
            req.name
            for req, _ in self.in_flight_application_request_channels[
                DEFAULT_NAMESPACE
            ].keys()
        ]

    def __repr__(self) -> str:
        namespace = {
            w: ", ".join(repr(e) for e in wd.history.events)
            for w, wd in self.namespace.items()
            if wd.history.events
        }
        return f"{type(self).__name__}(id={self.id}: namespace={namespace})"

    async def handle_application_request(self, request: ApplicationRequest):
        self.time = max(self.time, request.time) + 1
        request.time = self.time
        await self.publish_change_event()
        await request.publish_change_event()
        match request.request_type:
            case ApplicationRequestType.StartWorkflow:
                return await self.start_workflow(request)
            case ApplicationRequestType.ExecuteWorkflow:
                return await self.execute_workflow(request)
            case ApplicationRequestType.ExecuteUpdate:
                return await self.execute_update(request)
            case _:
                raise ValueError(f"Server does not support request of type: {request}")

    async def handle_worker_request(self, request: WorkerRequest):
        self.time = max(self.time, request.time) + 1
        request.time = self.time
        await self.publish_change_event()
        await request.publish_change_event()
        match request:
            case WorkflowTaskCompleted(workflow_id, commands):
                await self.handle_commands(workflow_id, commands)
            case ActivityTaskCompleted(workflow_id, result, token):
                await self.handle_activity_task_completed(workflow_id, result, token)
            case _:
                raise ValueError(f"Server does not support request of type: {request}")

    async def start_workflow(self, request: ApplicationRequest):
        # This is a non-blocking request; we don't need to wait for a
        # HistoryEvent to be written, beyond those we write synchronously on
        # handling the request. As a result we do not use
        # _get_application_request_response.
        chans = self.in_flight_application_request_channels[DEFAULT_NAMESPACE]
        key = request.request_type, request.workflow_id
        chans[key] = Queue(maxsize=1)
        await self.publish_change_event()
        wf_started, _ = await self.write_history_events(
            request.workflow_id,
            [HistoryEventType.WF_STARTED, HistoryEventType.WFT_SCHEDULED],
            seen_by_sticky_worker=False,
        )
        del chans[key]
        await self.publish_change_event()
        request.response_payload = wf_started.data.get("payload")

    async def execute_workflow(self, request: ApplicationRequest):
        event = await self._get_application_request_response(
            request, [HistoryEventType.WF_STARTED, HistoryEventType.WFT_SCHEDULED]
        )
        request.response_payload = event.data.get("payload")

    async def execute_update(self, request: ApplicationRequest):
        self.get_workflow_data(request.workflow_id).pending_updates.append(
            UpdateInfo(uuid4().hex, "fake-update-name")
        )
        event = await self._get_application_request_response(
            request, [HistoryEventType.WF_STARTED, HistoryEventType.WFT_SCHEDULED]
        )
        request.response_payload = event.data.get("payload")

    async def _get_application_request_response(
        self, request: ApplicationRequest, events_to_be_written: List[HistoryEventType]
    ) -> HistoryEvent:
        """
        Handle request by writing history events, and return response.

        When handling an application request, we create a new channel
        (maxsize=1) and block, waiting for the response to be pushed to the
        channel. The value pushed to the channel is a HistoryEvent that contains
        within it information needed to unblock the corresponding client-side
        awaitable. The handler deletes the channel when it receives the response
        from it.

        Note that the set of in-flight application requests (which is published
        to the event bus to be visualized) is defined to be the current set of
        channels. Therefore we publish a change event after creating/deleting a
        channel.
        """

        chans = self.in_flight_application_request_channels[DEFAULT_NAMESPACE]
        key = request.request_type, request.workflow_id
        assert (
            key not in chans
        ), "Multiple concurrent requests of same type for same workflow ID are not supported"
        chan: Queue[HistoryEvent] = Queue(maxsize=1)
        chans[key] = chan
        await self.publish_change_event()

        await self.write_history_events(
            request.workflow_id,
            events_to_be_written,
            seen_by_sticky_worker=False,
        )

        event = await chan.get()
        del chans[key]
        await self.publish_change_event()
        return event

    # https://github.com/temporalio/temporal/blob/569a306daa2aef8e221712ae19d72219db4a4712/service/history/workflow_task_handler_callbacks.go#L386
    # https://github.com/temporalio/temporal/blob/569a306daa2aef8e221712ae19d72219db4a4712/service/history/workflow_task_handler.go#L166
    async def handle_commands(self, workflow_id, commands: List[Command]):
        chans = self.in_flight_application_request_channels[DEFAULT_NAMESPACE]

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
                    key = ApplicationRequestType.ExecuteWorkflow, workflow_id
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
            await self.publish_change_event()
        await self.dispatch_workflow_or_activity_task(workflow_id)
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
            [at_scheduled_event] = events
            events.extend(
                await self.write_history_events(
                    workflow_id,
                    [HistoryEventType.ACTIVITY_TASK_STARTED],
                    seen_by_sticky_worker=True,
                )
            )
            [queue] = self.activity_worker_long_poll_connections.values()
            await queue.put(
                ActivityTask(
                    workflow_id, self.time, token=int(at_scheduled_event.data["token"])  # type: ignore
                )
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
            [queue] = self.workflow_worker_long_poll_connections.values()
            await queue.put(
                WorkflowTask(workflow_id, self.time, events, pending_updates)
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
