from tempyral.simulation.api import (
    ApplicationRequest,
    ApplicationRequestType,
    WorkflowId,
)
from tempyral.simulation.entity import Entity
from tempyral.simulation.server import Server


class Application(Entity):
    async def start_workflow(self, workflow_id: WorkflowId, server: Server) -> None:
        request = ApplicationRequest(
            workflow_id, ApplicationRequestType.StartWorkflowExecution
        )
        await self.publish_message_event(self, server, request=request)
        await server.handle_request(request)
