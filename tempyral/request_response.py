from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from tempyral.entity import Entity

if TYPE_CHECKING:
    from tempyral.api import ApplicationRequestType, Command, WorkflowId
    from tempyral.server import HistoryEvent, UpdateInfo


class RequestResponseStage(Enum):
    Request = 1
    Response = 2


class RequestResponse(Entity):
    def __init__(self, time=0):
        super().__init__(time)
        self.stage = RequestResponseStage.Request
        self.token: int | None = None
        self.response_payload: Any | None = None

    __publish__ = Entity.__publish__ | {"stage", "token", "response_payload"}


class Response(RequestResponse):
    """
    A communication between two actors which we model as a response only,
    without a corresponding request.
    """

    def __init__(self, time=0):
        super().__init__(time)
        self.stage = RequestResponseStage.Response


class ApplicationRequest(RequestResponse):
    def __init__(
        self,
        request_type: "ApplicationRequestType",
        workflow_id: "WorkflowId",
        time: int,
        token: int | None,
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


class WorkflowTask(Entity):
    def __init__(
        self,
        workflow_id: "WorkflowId",
        events: list["HistoryEvent"],
        requested_updates: list["UpdateInfo"],
    ):
        super().__init__()
        self.workflow_id = workflow_id
        self.events = events
        self.requested_updates = requested_updates

    __publish__ = {"workflow_id", "events", "requested_updates"}

    def __repr__(self) -> str:
        return f"WFT(wid={self.workflow_id}, events={self.events}, updates={self.requested_updates})"


class ActivityTask(Entity):
    def __init__(self, workflow_id: "WorkflowId", events: list["HistoryEvent"]):
        super().__init__()
        self.workflow_id = workflow_id
        self.events = events

    __publish__ = {"workflow_id", "events"}

    @property
    def scheduled_event(self) -> "HistoryEvent":
        [event] = self.events
        return event

    def __repr__(self) -> str:
        return f"AT(wid={self.workflow_id}, events={self.events})"


T = TypeVar("T", bound=WorkflowTask | ActivityTask)


class WorkerPollRequest(RequestResponse, Generic[T]):
    """A Workflow or Activity Task dispatched by the server in response to a long-poll request."""

    def __init__(
        self,
        workflow_id: "WorkflowId",
        task: T,
        time: int,
        token: int,
    ):
        super().__init__(time)
        self.workflow_id = workflow_id
        self.task = task
        self.token = token

    __publish__ = RequestResponse.__publish__ | {"task"}

    def __repr__(self) -> str:
        return f"{type(self).__name__}[{self.time}](id={self.id}: {self.task})"


class WorkerRequest(Response):
    # Although these are technically requests, we model them as responses. We do
    # not model the true response of these at all. In other words, we think of
    # them as responses to tasks dispatched to the worker by the server.
    def __init__(self, workflow_id: "WorkflowId", time: int):
        super().__init__(time)
        self.workflow_id = workflow_id


class WorkflowTaskCompleted(WorkerRequest):
    __match_args__ = ("workflow_id", "commands")

    def __init__(self, workflow_id: "WorkflowId", time: int, commands: list["Command"]):
        super().__init__(workflow_id, time)
        self.commands = commands


class ActivityTaskCompleted(WorkerRequest):
    __match_args__ = ("workflow_id", "result", "token")
    token: int

    def __init__(self, workflow_id: "WorkflowId", time: int, result: Any, token: int):
        super().__init__(workflow_id, time)
        self.result = result
        self.token = token
