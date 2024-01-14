from dataclasses import dataclass
from enum import Enum
from typing import Any

TaskQueueId = str

# pyright: reportUnusedImport=false
from schema.schema import (
    ApplicationRequestType,
    HistoryEventType,
    NamespaceId,
    ProtocolInstanceId,
    WorkflowId,
)


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


class ProtocolMessageType(Enum):
    UPDATE_ACCEPTED = 1
    UPDATE_REJECTED = 2
    UPDATE_COMPLETED = 3


@dataclass
class ProtocolMessage:
    message_type: ProtocolMessageType
    instance_id: ProtocolInstanceId
    payload: Any = None


@dataclass(frozen=True)
class Command:
    command_type: CommandType
    protocol_message: ProtocolMessage | None = None
    token: int | None = None
    payload: Any = None
