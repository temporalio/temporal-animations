from tempyral.simulation.api import ApplicationRequestType
from tempyral.simulation.entity import Entity
from tempyral.simulation.server import Server


class Application(Entity):
    async def start_workflow(self, server: Server) -> None:
        request = ApplicationRequestType.StartWorkflowExecution
        await self.publish_message_event(self, server, request_type=request)
        await server.handle_request(request)
