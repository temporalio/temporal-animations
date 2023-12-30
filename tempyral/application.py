from typing import Coroutine, Iterable

from tempyral.api import ApplicationRequestType
from tempyral.code import EntityWithCode
from tempyral.message import ApplicationRequest
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
                request_type, workflow_id = map(eval, directive.split())
                if not isinstance(request_type, ApplicationRequestType):
                    raise ValueError
                requests.append(ApplicationRequest(request_type, workflow_id, line_num))
            except ValueError:
                raise ValueError(f"Unsupported application directive: {directive}")
        self.requests = requests
        self.blocked_expressions = set()
        super().__init__()

    def get_coroutines(self, server: Server) -> Iterable[Coroutine]:
        """
        Return a coroutine that issues each application requests, waiting for its reponse.
        """

        async def coro():
            for request in self.requests:
                if request.token is not None:
                    self.blocked_expressions.add(request.token)
                    await self.publish_change_event()
                await self.publish_message_event(self, server, request)
                await server.handle_application_request(request)
                if request.token is not None:
                    self.blocked_expressions.remove(request.token)
                await self.publish_message_event(server, self, request)
            server.terminate_simulation()

        yield coro()
