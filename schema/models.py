from enum import Enum
from typing import Hashable, Optional, OrderedDict

from pydantic import BaseModel


# https://github.com/temporalio/api/blob/master/temporal/api/enums/v1/event_type.proto#L35
class HistoryEventType(Enum):
    WF_STARTED = 1
    WF_COMPLETED = 2
    WF_FAILED = 3
    WFT_SCHEDULED = 5
    WFT_STARTED = 6
    WFT_COMPLETED = 7
    WFT_FAILED = 9
    ACTIVITY_TASK_SCHEDULED = 10
    ACTIVITY_TASK_STARTED = 11
    ACTIVITY_TASK_COMPLETED = 12
    ACTIVITY_TASK_FAILED = 13
    TIMER_STARTED = 17
    TIMER_FIRED = 18
    WF_SIGNALED = 26
    WF_UPDATE_ACCEPTED = 41
    WF_UPDATE_REJECTED = 42
    WF_UPDATE_COMPLETED = 43


class ApplicationRequestType(Enum):
    StartWorkflow = 1
    ExecuteWorkflow = 2
    ExecuteUpdate = 3
    SignalWorkflow = 4
    GetWorkflowResult = 5


NamespaceId = str
WorkflowId = str
ProtocolInstanceId = str


class UpdateInfo(BaseModel):
    update_id: ProtocolInstanceId
    update_name: str


class RequestResponseStage(Enum):
    Request = 1
    Response = 2


class Entity(BaseModel):
    id: int
    time: int


class RequestResponse(Entity):
    stage: RequestResponseStage
    token: Optional[int]


class Response(Entity):
    stage: RequestResponseStage


class HistoryEvent(Entity):
    event_type: HistoryEventType
    seen_by_worker: bool
    data: dict[str, Hashable]


class History(Entity):
    workflow_id: str
    events: list[HistoryEvent]


class WorkflowTask(BaseModel):
    workflow_id: WorkflowId
    events: list[HistoryEvent]
    pending_updates: list[UpdateInfo]


class ActivityTask(BaseModel):
    workflow_id: WorkflowId
    events: list[HistoryEvent]


class WorkerPollRequest(RequestResponse):
    task: WorkflowTask | ActivityTask


class WorkerRequest(Response):
    workflow_id: WorkflowId


class Workflow(Entity):
    code: str
    language: str
    blocked_lines: set[int]


class WorkflowWorker(Entity):
    workflows: list[Workflow]


class ActivityWorker(Entity):
    code: str
    language: str
    blocked_lines: set[int]


class WorkflowData(BaseModel):
    history: History
    pending_updates: list[UpdateInfo]


Namespace = OrderedDict[WorkflowId, WorkflowData]
Shard = dict[NamespaceId, Namespace]


class Server(Entity):
    shards: list[Shard]


class ApplicationRequest(RequestResponse):
    request_type: ApplicationRequestType


class WorkflowTaskCompleted(WorkerRequest):
    pass


class Application(Entity):
    code: str
    language: str
    blocked_lines: set[int]


class ActivityTaskCompleted(WorkerRequest):
    pass


class StateChangeEvent(BaseModel):
    entity: Entity


class MessageEvent(BaseModel):
    sender: Entity
    receiver: Entity
    message: RequestResponse
