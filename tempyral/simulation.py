"""
A pure python simulation of Temporal without any visualization.
"""
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, TypedDict

from tempyral.event_bus import MessageEvent, StateChangeEvent, event_bus

DEFAULT_NAMESPACE = "default"
DEFAULT_WORKFLOW_ID = "wid"

NamespaceId = str
WorkflowId = str
TaskQueueId = str
ActivityTask = str


class ApplicationRequestType(Enum):
    StartWorkflow = "StartWorkflow"


class HistoryEventType(Enum):
    WORKFLOW_EXECUTION_STARTED = "WORKFLOW_EXECUTION_STARTED"
    WORKFLOW_EXECUTION_COMPLETED = "WORKFLOW_EXECUTION_COMPLETED"
    WORKFLOW_TASK_SCHEDULED = "WORKFLOW_TASK_SCHEDULED"
    WORKFLOW_TASK_STARTED = "WORKFLOW_TASK_STARTED"
    WORKFLOW_TASK_COMPLETED = "WORKFLOW_TASK_COMPLETED"


class Entity:
    async def publish_change_event(self):
        await event_bus.publish(StateChangeEvent(self))
        await asyncio.sleep(0)

    async def publish_message_event(
        self, sender: "Entity", receiver: "Entity", **kwargs
    ):
        if event_bus is not None:
            await event_bus.publish(MessageEvent(sender, receiver, kwargs))
            await asyncio.sleep(0)


@dataclass
class HistoryEvent:
    event_type: HistoryEventType
    seen_by_sticky_worker: bool = False


class HistoryEvents(Entity):
    """A slice of history events"""

    def __init__(self, events: List[HistoryEvent]) -> None:
        self.events = events


WorkflowTask = HistoryEvents


Shard = Dict[NamespaceId, Dict[WorkflowId, HistoryEvents]]


class TaskQueue(TypedDict):
    workflow_task_queue: List[WorkflowTask]
    activity_task_queue: List[ActivityTask]


class WorkflowWorker(Entity):
    async def poll(self, server: "Server"):
        while True:
            # Currently we're not actually simulating the long-poll; just the
            # dispatch from server to worker.
            await server.dispatch_wft_if_pending_events(self)
            await asyncio.sleep(0)

    def handle_wft(self, wft: WorkflowTask, server: "Server"):
        pass


class Server(Entity):
    def __init__(self):
        self.shards: List[Shard] = [
            {DEFAULT_NAMESPACE: {DEFAULT_WORKFLOW_ID: HistoryEvents([])}}
        ]
        self.task_queues: Dict[TaskQueueId, TaskQueue] = {}

    async def handle_request(self, request: ApplicationRequestType):
        match request:
            case ApplicationRequestType.StartWorkflow:
                self.history.events.extend(
                    [
                        HistoryEvent(HistoryEventType.WORKFLOW_EXECUTION_STARTED),
                        HistoryEvent(HistoryEventType.WORKFLOW_TASK_SCHEDULED),
                    ]
                )
                await self.publish_change_event()

    async def dispatch_wft_if_pending_events(self, worker: WorkflowWorker) -> None:
        new_events = []
        for e in self.history.events:
            if not e.seen_by_sticky_worker:
                e.seen_by_sticky_worker = True
                new_events.append(e)
        if new_events:
            await self.publish_change_event()
            wft = WorkflowTask(new_events)
            await self.publish_message_event(self, worker, events=new_events)
            worker.handle_wft(wft, self)
            await worker.publish_change_event()

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


class Application(Entity):
    async def start_workflow(self, server: Server) -> None:
        request = ApplicationRequestType.StartWorkflow
        await self.publish_message_event(self, server, request_type=request)
        await server.handle_request(request)


def drain(source: List, sink: List):
    while source:
        sink.append(source.pop())
