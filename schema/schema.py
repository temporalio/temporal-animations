import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Hashable, Optional, OrderedDict, Self


@dataclass
class Model:
    type: str = field(init=False)

    def __post_init__(self):
        self.type = self.__class__.__name__

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        this_module = sys.modules[__name__]
        field_data = {}
        for k, v in data.items():
            if isinstance(v, dict) and "_type" in v:
                cls = getattr(this_module, v.pop("_type"))
                field_data[k] = cls.from_dict(v)
            else:
                field_data[k] = v
        return cls(**field_data)


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


class UpdateInfo(Model):
    update_id: ProtocolInstanceId
    update_name: str


class RequestResponseStage(Enum):
    Request = 1
    Response = 2


class Entity(Model):
    """
    An entity in the simulation. Instances of the same type with the same id are
    equal from the point of view of hashing and object equality. This allows a
    renderer to map entity instances referenced in events to a fixed set of
    graphical components in the animation.
    """

    id: int
    time: int

    def __hash__(self) -> int:
        return hash((type(self).__name__, self.id))

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and hash(self) == hash(other)


class RequestResponse(Entity):
    stage: RequestResponseStage
    token: Optional[int]


# TODO: unnecessary
class Response(RequestResponse):
    pass


class HistoryEvent(Entity):
    event_type: HistoryEventType
    seen_by_worker: bool
    data: dict[str, Hashable]


class History(Entity):
    workflow_id: str
    events: list[HistoryEvent]


class WorkflowTask(Model):
    workflow_id: WorkflowId
    events: list[HistoryEvent]
    pending_updates: list[UpdateInfo]


class ActivityTask(Model):
    workflow_id: WorkflowId
    events: list[HistoryEvent]


class WorkerPollRequest(RequestResponse):
    task: WorkflowTask | ActivityTask


class WorkerRequest(Response):
    pass


class EntityWithCode(Entity):
    code: str
    language: str
    blocked_lines: set[int]


class Workflow(EntityWithCode):
    pass


class WorkflowWorker(Entity):
    workflows: list[Workflow]


class ActivityWorker(EntityWithCode):
    pass


class WorkflowData(Model):
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


class Application(EntityWithCode):
    pass


class ActivityTaskCompleted(WorkerRequest):
    pass


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


class StateChangeEvent(Model):
    """
    An event indicating that the internal state of `entity` has changed. A
    renderer will typically re-render the graphical component corresponding to
    the entity.
    """

    entity: Entity


class MessageEvent(Model):
    """
    An event indicating that `sender` has sent `message` to `receiver`. A
    renderer will typically display an animation of the message.
    """

    sender: Entity
    receiver: Entity
    message: RequestResponse


type Event = StateChangeEvent | MessageEvent | InitEvent
