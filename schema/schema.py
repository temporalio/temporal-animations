import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, Hashable, OrderedDict


@dataclass
class Model:
    _type: str


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
    GetWorkflowResult = 2
    StartUpdate = 3
    GetUpdateResult = 4
    ExecuteUpdate = 5
    StartWorkflowAndExecuteUpdate = 6
    SignalWithStartWorkflow = 7
    SignalWorkflow = 8
    NexusRequest = 9


NamespaceId = str
WorkflowId = str
ProtocolInstanceId = str


@dataclass
class UpdateInfo(Model):
    update_id: ProtocolInstanceId
    update_name: str


class RequestResponseStage(Enum):
    Request = 1
    Response = 2


@dataclass
class Entity(Model):
    """
    An entity in the simulation. Instances of the same type with the same id are
    equal from the point of view of hashing and object equality. This allows a
    renderer to map entity instances referenced in events to a fixed set of
    graphical components in the animation.
    """

    id: int
    time: int

    # TODO: Python bug?? Didn't seem possible to override __hash__.
    # See https://github.com/python/cpython/blob/3.12/Lib/dataclasses.py#L136
    def hash_key(self) -> int:
        return hash((type(self).__name__, self.id))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and hash(self) == hash(other)


@dataclass
class RequestResponse(Entity):
    stage: RequestResponseStage
    token: int | None
    response_payload: Hashable | None


# TODO: unnecessary
@dataclass
class Response(RequestResponse):
    pass


@dataclass
class HistoryEvent(Entity):
    event_type: HistoryEventType
    seen_by_worker: bool
    data: dict[str, Hashable]


@dataclass
class History(Entity):
    workflow_id: str
    events: list[HistoryEvent]


@dataclass
class WorkflowTask(Model):
    workflow_id: WorkflowId
    events: list[HistoryEvent]
    requested_updates: list[UpdateInfo]


@dataclass
class ActivityTask(Model):
    workflow_id: WorkflowId
    events: list[HistoryEvent]


@dataclass
class WorkerPollRequest(RequestResponse):
    task: WorkflowTask | ActivityTask


@dataclass
class WorkerRequest(Response):
    pass


@dataclass
class EntityWithCode(Entity):
    code: str
    language: str
    blocked_lines: set[int]
    active: bool


@dataclass
class Workflow(EntityWithCode):
    pass


@dataclass
class WorkflowWorker(Entity):
    workflows: list[Workflow]


@dataclass
class ActivityWorker(EntityWithCode):
    pass


@dataclass
class WorkflowData(Model):
    history: History
    update_registry: list[UpdateInfo]


Namespace = OrderedDict[WorkflowId, WorkflowData]
Shard = dict[NamespaceId, Namespace]


@dataclass
class Server(Entity):
    shards: list[Shard]


@dataclass
class ApplicationRequest(RequestResponse):
    request_type: ApplicationRequestType


@dataclass
class WorkflowTaskCompleted(WorkerRequest):
    pass


@dataclass
class Application(EntityWithCode):
    pass


@dataclass
class ActivityTaskCompleted(WorkerRequest):
    pass


@dataclass
class InitEvent(Model):
    """
    The first event emitted by a simulation must be of this type. Its purpose is
    to declare the identities of the actor instances that will be involved in
    the simulation. A renderer will typically use this event to position the
    actors in the scene, and establish a mapping between these graphical
    components and the actor ids, so that actors referenced in subsequent
    StateChange and Message events can be mapped to their graphical components
    in the animation.
    """

    server: Server
    apps: list[Application]
    workflow_workers: list[WorkflowWorker]
    activity_workers: list[ActivityWorker]
    title: str


@dataclass
class StateChangeEvent(Model):
    """
    An event indicating that the internal state of `entity` has changed. A
    renderer will typically re-render the graphical component corresponding to
    the entity.
    """

    entity: Entity


@dataclass
class MessageEvent(Model):
    """
    An event indicating that `sender` has sent `message` to `receiver`. A
    renderer will typically display an animation of the message.
    """

    sender: Entity
    receiver: Entity
    message: RequestResponse


@dataclass
class NexusServer(Entity):
    pass


@dataclass
class NexusWorker(Entity):
    pass


@dataclass
class NexusInitEvent(InitEvent):
    nexus_server: NexusServer
    nexus_workers: list[NexusWorker]


type Event = StateChangeEvent | MessageEvent | InitEvent


def from_serializable(data: Any) -> Any:
    if isinstance(data, dict):
        data = {k: from_serializable(v) for k, v in data.items()}
        if "_type" in data:
            cls = getattr(sys.modules[__name__], data["_type"])
            if issubclass(cls, Enum):
                return cls(data["value"])
            else:
                return cls(**data)
        else:
            return data
    elif isinstance(data, list):
        return [from_serializable(v) for v in data]
    else:
        return data
