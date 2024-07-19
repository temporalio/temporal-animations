from enum import Enum


class CommandType(Enum):
    SCHEDULE_ACTIVITY_TASK = 1
    START_TIMER = 2
    COMPLETE_WORKFLOW_EXECUTION = 3
