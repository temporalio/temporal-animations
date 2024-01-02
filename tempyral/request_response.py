from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, List, Optional

from tempyral.entity import Entity

if TYPE_CHECKING:
    from tempyral.api import ApplicationRequestType, Command, UpdateInfo, WorkflowId
    from tempyral.server import HistoryEvent


class RequestResponseStage(Enum):
    Request = 1
    Response = 2


class RequestResponse(Entity):
    def __init__(self, time=0):
        super().__init__(time)
        self.stage = RequestResponseStage.Request
        self.token: Optional[int] = None

    __publish__ = Entity.__publish__ | {"stage", "token"}


class Response(Entity):
    """
    A communication between two actors which we model as a response only,
    without a corresponding request.
    """

    def __init__(self, time=0):
        super().__init__(time)
        self.stage = RequestResponseStage.Response

    __publish__ = Entity.__publish__ | {"stage"}


class ApplicationRequest(RequestResponse):
    def __init__(
        self,
        request_type: "ApplicationRequestType",
        workflow_id: "WorkflowId",
        time: int,
        token: Optional[int],
        response_payload: Any = None,
    ):
        super().__init__(time)
        self.workflow_id = workflow_id
        self.request_type = request_type
        self.token = token
        self.response_payload = response_payload

    def __repr__(self) -> str:
        return f"{self.request_type.name}[{self.time}]"

    __publish__ = RequestResponse.__publish__ | {"request_type"}


@dataclass
class WorkflowTask:
    events: list["HistoryEvent"]
    pending_updates: list["UpdateInfo"]

    def __repr__(self) -> str:
        return f"WFT(events={self.events}, updates={self.pending_updates})"


class WorkflowTaskRequest(Response):
    """A Workflow Task dispatched by the server in response to a long-poll request."""

    def __init__(self, worklow_id: "WorkflowId", time: int, task: WorkflowTask) -> None:
        super().__init__(time)
        self.workflow_id = worklow_id
        self.task = task

    __publish__ = Response.__publish__ | {"task"}

    def __repr__(self) -> str:
        return f"{type(self).__name__}[{self.time}](id={self.id}: {self.task})"


@dataclass
class ActivityTask:
    pass


class ActivityTaskRequest(Response):
    """An Activity Task dispatched by the server in response to a long-poll request."""

    def __init__(
        self,
        workflow_id: "WorkflowId",
        time: int,
        token: int,
        task: ActivityTask,
    ):
        super().__init__(time)
        self.workflow_id = workflow_id
        self.token = token
        self.task = task

    __publish__ = Response.__publish__ | {"task"}


class WorkerRequest(Response):
    # Although these are technically requests, we model them as responses. We do
    # not model the true response of these at all. In other words, we think of
    # them as responses to tasks dispatched to the worker by the server.
    def __init__(self, workflow_id: "WorkflowId", time: int):
        super().__init__(time)
        self.workflow_id = workflow_id


class WorkflowTaskCompleted(WorkerRequest):
    __match_args__ = ("workflow_id", "commands")

    def __init__(self, workflow_id: "WorkflowId", time: int, commands: List["Command"]):
        super().__init__(workflow_id, time)
        self.commands = commands


class ActivityTaskCompleted(WorkerRequest):
    __match_args__ = ("workflow_id", "result", "token")

    def __init__(self, workflow_id: "WorkflowId", time: int, result: Any, token: int):
        super().__init__(workflow_id, time)
        self.result = result
        self.token = token
