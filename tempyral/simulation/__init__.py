"""
A pure python simulation of Temporal without any visualization.
"""
import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict

from tempyral.event_bus import EventBus, MessageEvent, StateChangeEvent

DEFAULT_NAMESPACE = "default"
DEFAULT_WORKFLOW_ID = "wid"

NamespaceId = str
WorkflowId = str
TaskQueueId = str
ActivityTask = str


class ApplicationRequestType(Enum):
    START_WORKFLOW = "StartWorkflow"


class HistoryEventType(Enum):
    WORKFLOW_EXECUTION_STARTED = "WORKFLOW_EXECUTION_STARTED"
    WORKFLOW_EXECUTION_COMPLETED = "WORKFLOW_EXECUTION_COMPLETED"
    WORKFLOW_TASK_SCHEDULED = "WORKFLOW_TASK_SCHEDULED"
    WORKFLOW_TASK_STARTED = "WORKFLOW_TASK_STARTED"
    WORKFLOW_TASK_COMPLETED = "WORKFLOW_TASK_COMPLETED"


class PublishingEntity:
    def __init__(self, event_bus: EventBus, proxy: Any):
        self.event_bus = event_bus
        self.proxy = proxy

    async def publish_change_event(self):
        await self.event_bus.publish(StateChangeEvent(self.proxy))

    async def publish_message_event(
        self, sender: "PublishingEntity", receiver: "PublishingEntity"
    ):
        await self.event_bus.publish(MessageEvent(sender.proxy, receiver.proxy))


@dataclass
class HistoryEvent:
    event_type: HistoryEventType
    seen_by_sticky_worker: bool = False


class HistoryEvents:
    """A slice of history events"""

    def __init__(self, events: List[HistoryEvent]) -> None:
        self.events = events


WorkflowTask = HistoryEvents


Shard = Dict[NamespaceId, Dict[WorkflowId, HistoryEvents]]


class TaskQueue(TypedDict):
    workflow_task_queue: List[WorkflowTask]
    activity_task_queue: List[ActivityTask]


class WorkflowWorker(PublishingEntity):
    async def poll(self, server: "Server"):
        while True:
            # Currently we're not actually simulating the long-poll; just the
            # dispatch from server to worker.
            server.dispatch_wft_if_pending_events(self)
            await asyncio.sleep(0)

    def handle_wft(self, wft: WorkflowTask, server: "Server"):
        pass


class Server(PublishingEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shards: List[Shard] = [
            {DEFAULT_NAMESPACE: {DEFAULT_WORKFLOW_ID: HistoryEvents([])}}
        ]
        self.task_queues: Dict[TaskQueueId, TaskQueue] = {}

    def handle(self, request: ApplicationRequestType):
        match request:
            case ApplicationRequestType.START_WORKFLOW:
                self.history.events.extend(
                    [
                        HistoryEvent(HistoryEventType.WORKFLOW_EXECUTION_STARTED),
                        HistoryEvent(HistoryEventType.WORKFLOW_TASK_SCHEDULED),
                    ]
                )

    def dispatch_wft_if_pending_events(
        self, worker: WorkflowWorker
    ) -> Tuple[Optional[WorkflowTask], List[Callable], List[Callable]]:
        new_events = []
        for e in self.history.events:
            if not e.seen_by_sticky_worker:
                e.seen_by_sticky_worker = True
                new_events.append(e)
        self.publish(ChangeState(self))
        if new_events:
            wft = WorkflowTask(new_events)
            return wft, [], [lambda: worker.handle_wft(wft, self)]
        else:
            return None, [], []

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


class Application(PublishingEntity):
    def start_workflow(
        self, server: Server
    ) -> Tuple[None, List[Callable], List[Callable]]:
        """
        The sending of a request is represented by a list of pre-send functions,
        and a list of post-receive functions. These will typically mutate the
        state of the sender and receiver respectively.
        """
        return (
            None,
            [],
            [lambda: server.handle(ApplicationRequestType.START_WORKFLOW)],
        )


def drain(source: List, sink: List):
    while source:
        sink.append(source.pop())


if __name__ == "__main__":

    def simulation():
        server = Server()
        app = Application()
        wworker = WorkflowWorker()
