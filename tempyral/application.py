from asyncio import Queue
from typing import Coroutine, Iterable

from tempyral.api import ApplicationRequest, ApplicationRequestType
from tempyral.code import EntityWithCode
from tempyral.server import Server


class Application(EntityWithCode):
    def __init__(self):
        super().__init__()
        self.code, raw_requests = self.parse_code(self.language)
        requests = []
        for directive, line_num in raw_requests:
            try:
                code, workflow_id = directive.split()
                match eval(code):
                    case ApplicationRequestType.StartWorkflowExecution as req:
                        requests.append(ApplicationRequest(workflow_id, req, line_num))
                    case _:
                        raise ValueError
            except ValueError:
                raise ValueError(f"Unsupported application directive: {directive}")
        self.requests = iter(requests)
        self.blocked_expressions = set()
        self.requests_queue: Queue[ApplicationRequest] = Queue()

    def get_coroutines(self, server: Server) -> Iterable[Coroutine]:
        """
        Return a coroutine that issues the application requests as they become unblocked.
        """

        async def coro():
            request = next(self.requests, None)
            assert request, "Application code does not contain any request directives"
            await self.requests_queue.put(request)
            while not self.requests_queue.empty():
                request = await self.requests_queue.get()
                await self.publish_message_event(self, server, request=request)
                await server.handle_request(request)

        yield coro()
