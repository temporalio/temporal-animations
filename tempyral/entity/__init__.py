"""
A pure python simulation of Temporal without any visualization.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, List, Tuple, TypedDict

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


class WorkflowWorker:
    pass


class Server:
    def __init__(self) -> None:
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

    def dispatch_wft(
        self, worker: WorkflowWorker
    ) -> Tuple[WorkflowTask, List[Callable], List[Callable]]:
        # TODO: Sticky optimisation: send all unseen events to the workflow
        # worker, and mark them as seen.
        return WorkflowTask(self.history.events), [], []

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


class Application:
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
