from asyncio import Queue
from typing import Coroutine, Iterable

from tempyral.api import ApplicationRequest, ApplicationRequestType
from tempyral.code import EntityWithCode
from tempyral.server import Server


class Application(EntityWithCode):
    __publish__ = {"id", "code", "language", "blocked_expressions"}

    def __init__(self):
        if not hasattr(self, "language"):
            self.language = self._get_language()
        self.code, raw_requests = self.parse_code(self.language)
        requests = []
        for directive, line_num in raw_requests:
            try:
                code, workflow_id = directive.split()
                match req := eval(code):
                    case ApplicationRequestType.StartWorkflow | ApplicationRequestType.ExecuteWorkflow:
                        requests.append(
                            ApplicationRequest(req, eval(workflow_id), line_num)
                        )
                    case _:
                        raise ValueError
            except ValueError:
                raise ValueError(f"Unsupported application directive: {directive}")
        self.requests = iter(requests)
        self.blocked_expressions = set()
        self.requests_queue: Queue[ApplicationRequest] = Queue()
        super().__init__()

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
                if request.token is not None:
                    self.blocked_expressions.add(request.token)
                    await self.publish_change_event()
                await self.publish_message_event(self, server, request=request)
                response = await server.handle_request(request)
                await self.publish_message_event(server, self, response=response)
                assert response
                if response.request.token:
                    self.blocked_expressions.remove(response.request.token)
                    await self.publish_change_event()
            server.terminate_simulation()

        yield coro()
