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

    __publish__ = Entity.__publish__ | {"stage"}


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
        token: Optional[int] = None,
        response_payload: Any = None,
    ):
        self.workflow_id = workflow_id
        self.request_type = request_type
        self.token = token
        self.response_payload = response_payload
        super().__init__(time)

    __publish__ = RequestResponse.__publish__ | {"request_type"}


class WorkflowTask(Response):
    """A Workflow Task dispatched by the server in response to a long-poll request."""

    def __init__(
        self,
        worklow_id: "WorkflowId",
        time: int,
        events: List["HistoryEvent"],
        pending_updates: List["UpdateInfo"],
    ) -> None:
        super().__init__(time)
        self.workflow_id = worklow_id
        self.events = tuple(events)
        self.pending_updates = tuple(pending_updates)

    __publish__ = RequestResponse.__publish__ | {"events", "pending_updates"}

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id}: events={self.events}, updates={self.pending_updates})"


class ActivityTask(RequestResponse):
    """An Activity Task dispatched by the server in response to a long-poll request."""

    def __init__(self, workflow_id: "WorkflowId", time: int, token: int):
        super().__init__(time)
        self.workflow_id = workflow_id
        self.token = token


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
