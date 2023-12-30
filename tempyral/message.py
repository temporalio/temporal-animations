from typing import Any, Optional

from tempyral.api import ApplicationRequestType, WorkflowId
from tempyral.entity import Entity


class ApplicationRequest(Entity):
    def __init__(
        self,
        request_type: ApplicationRequestType,
        workflow_id: WorkflowId,
        token: Optional[int] = None,
        response_payload: Any = None,
    ):
        self.workflow_id = workflow_id
        self.request_type = request_type
        self.token = token
        self.response_payload = response_payload
        super().__init__()

    __publish__ = {"id", "request_type"}
