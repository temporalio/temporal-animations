from typing import Any, Optional

from tempyral.api import ApplicationRequestType, WorkflowId
from tempyral.entity import Entity


class ApplicationRequest(Entity):
    def __init__(
        self,
        workflow_id: WorkflowId,
        request_type: ApplicationRequestType,
        token: Optional[int] = None,
    ):
        self.workflow_id = workflow_id
        self.request_type = request_type
        self.token = token
        super().__init__()


class ApplicationResponse(Entity):
    def __init__(self, request: ApplicationRequest, payload: Any):
        self.request = request
        self.payload = payload
        super().__init__()
