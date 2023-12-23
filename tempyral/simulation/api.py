from dataclasses import dataclass
from enum import Enum
from typing import List


# https://github.com/temporalio/api/blob/master/temporal/api/enums/v1/event_type.proto#L35
class HistoryEventType(Enum):
    WORKFLOW_EXECUTION_STARTED = 1
    WORKFLOW_EXECUTION_COMPLETED = 2
    WORKFLOW_EXECUTION_FAILED = 3
    WORKFLOW_TASK_SCHEDULED = 5
    WORKFLOW_TASK_STARTED = 6
    WORKFLOW_TASK_COMPLETED = 7
    WORKFLOW_TASK_FAILED = 9
    ACTIVITY_TASK_SCHEDULED = 10
    ACTIVITY_TASK_STARTED = 11
    ACTIVITY_TASK_COMPLETED = 12
    ACTIVITY_TASK_FAILED = 13
    TIMER_STARTED = 17
    TIMER_FIRED = 18
    WORKFLOW_EXECUTION_SIGNALED = 26
    WORKFLOW_EXECUTION_UPDATE_ACCEPTED = 41
    WORKFLOW_EXECUTION_UPDATE_REJECTED = 42
    WORKFLOW_EXECUTION_UPDATE_COMPLETED = 43


class ApplicationRequestType(Enum):
    StartWorkflowExecution = 1


class WorkerRequestType:
    pass


# https://github.com/temporalio/api/blob/master/temporal/api/enums/v1/command_type.proto#L35
class Command(Enum):
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
class RespondWorkflowTaskCompleted(WorkerRequestType):
    commands: List[Command]
