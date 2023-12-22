"""
A pure python simulation of Temporal without any visualization.
"""
from typing import Callable, Dict, List, Tuple, TypedDict

DEFAULT_NAMESPACE = "default"
DEFAULT_WORKFLOW_ID = "wid"

NamespaceId = str
WorkflowId = str
TaskQueueId = str
Event = str
WorkflowTask = List[Event]
ActivityTask = str


class HistoryEvents:
    """A slice of history events"""

    def __init__(self, events: List[Event]) -> None:
        self.events = events


WorkflowTask = HistoryEvents


Shard = Dict[NamespaceId, Dict[WorkflowId, HistoryEvents]]


class TaskQueue(TypedDict):
    workflow_task_queue: List[WorkflowTask]
    activity_task_queue: List[ActivityTask]


class Server:
    def __init__(self) -> None:
        self.shards: List[Shard] = [
            {DEFAULT_NAMESPACE: {DEFAULT_WORKFLOW_ID: HistoryEvents([])}}
        ]
        self.task_queues: Dict[TaskQueueId, TaskQueue] = {}

    @property
    def history(self) -> HistoryEvents:
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


class WorkflowWorker:
    pass


class ApplicationRequest:
    # For now, an ApplicationRequest is a list of events that the application
    # wants to be appended to server-side history. For example
    # WORKFLOW_EXECUTION_STARTED, WORKFLOW_EXECUTION_SIGNALED.
    # TODO: generalize to support requests such as update that don't append history events.

    def __init__(self, events: List[Event]):
        self.events = events
        self.pre_send_hook = []
        self.post_receive_hook = []


class Application:
    def send_request(
        self, request: ApplicationRequest, server: Server
    ) -> Tuple[List[Callable], List[Callable]]:
        """
        The sending of a request is represented by a list of pre-send functions,
        and a list of post-receive functions. These will typically mutate the
        state of the sender and receiver respectively.
        """
        return [], [lambda: drain(request.events, server.history.events)]


def drain(source: List, sink: List):
    while source:
        sink.append(source.pop())
