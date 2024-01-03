from dataclasses import dataclass
from enum import Enum
from typing import Optional

NamespaceId = str
WorkflowId = str
TaskQueueId = str
ProtocolInstanceId = str


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


# https://github.com/temporalio/api/blob/master/temporal/api/enums/v1/command_type.proto#L35
class CommandType(Enum):
    SCHEDULE_ACTIVITY_TASK = 1
    REQUEST_CANCEL_ACTIVITY_TASK = 2
    START_TIMER = 3
    COMPLETE_WORKFLOW_EXECUTION = 4
    FAIL_WORKFLOW_EXECUTION = 5
    CANCEL_TIMER = 6
    CANCEL_WORKFLOW_EXECUTION = 7
    REQUEST_CANCEL_EXTERNAL_WORKFLOW_EXECUTION = 8
    RECORD_MARKER = 9
    CONTINUE_AS_NEW_WORKFLOW_EXECUTION = 10
    START_CHILD_WORKFLOW_EXECUTION = 11
    SIGNAL_EXTERNAL_WORKFLOW_EXECUTION = 12
    UPSERT_WORKFLOW_SEARCH_ATTRIBUTES = 13
    PROTOCOL_MESSAGE = 14
    MODIFY_WORKFLOW_PROPERTIES = 16


@dataclass
class UpdateInfo:
    update_id: ProtocolInstanceId
    update_name: str


class ProtocolMessageType(Enum):
    UPDATE_ACCEPTED = 1
    UPDATE_REJECTED = 2
    UPDATE_COMPLETED = 3


@dataclass
class ProtocolMessage:
    message_type: ProtocolMessageType
    instance_id: ProtocolInstanceId


@dataclass(frozen=True)
class Command:
    command_type: CommandType
    protocol_message: Optional[ProtocolMessage] = None
    token: Optional[int] = None
