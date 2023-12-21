"""
A pure python simulation of Temporal without any visualization.
"""
from typing import Dict, List, TypedDict

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
    def __init__(self, events: List[Event]):
        self.events = events


class Application:
    pass
