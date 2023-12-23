from enum import Enum


class HistoryEventType(Enum):
    WORKFLOW_EXECUTION_STARTED = "WORKFLOW_EXECUTION_STARTED"
    WORKFLOW_EXECUTION_COMPLETED = "WORKFLOW_EXECUTION_COMPLETED"
    WORKFLOW_TASK_SCHEDULED = "WORKFLOW_TASK_SCHEDULED"
    WORKFLOW_TASK_STARTED = "WORKFLOW_TASK_STARTED"
    WORKFLOW_TASK_COMPLETED = "WORKFLOW_TASK_COMPLETED"


class ApplicationRequestType(Enum):
    StartWorkflow = "StartWorkflow"


class WorkerRequestType(Enum):
    RespondWorkflowTaskCompleted = "RespondWorkflowTaskCompleted"
