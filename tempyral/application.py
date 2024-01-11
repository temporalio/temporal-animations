from typing import Coroutine, Iterable, Type

from tempyral.code import WithCode
from tempyral.entity import Entity
from tempyral.event import emit_change_event, emit_message_event
from tempyral.request_response import ApplicationRequest, RequestResponse
from tempyral.server import AbstractServer


class AbstractApplication(Entity, WithCode):
    application_request_cls: Type[RequestResponse]
    __publish__ = Entity.__publish__ | WithCode.__publish__

    def __init__(self):
        super().__init__()
        if not hasattr(self, "language"):
            self.language = self._get_language()
        self.code, raw_requests = self.parse_code(self.language)
        requests: list[ApplicationRequest] = []
        for directive, line_num in raw_requests:
            try:
                from schema.schema import (
                    ApplicationRequestType,  # pyright: ignore[reportUnusedImport]
                )

                request_type, arg = map(eval, directive)
                requests.append(
                    ApplicationRequest(request_type, arg, self.time, line_num)
                )
            except ValueError:
                raise ValueError(f"Unsupported application directive: {directive}")
        self.requests = requests
        self.blocked_lines = set()

    def __repr__(self) -> str:
        return f"App[{self.time}]"

    def get_coroutines(self, server: AbstractServer) -> Iterable[Coroutine]:
        """
        Return a coroutine that issues each application request, waiting for its reponse.
        """

        async def coro():
            for request in self.requests:
                request.time = self.time
                if request.token is not None:
                    self.blocked_lines.add(request.token)
                    emit_change_event(self)
                emit_message_event(self, server, request)
                await server.handle_application_request(request)
                request.time = server.time
                self.tick(request)
                if request.token is not None:
                    self.blocked_lines.remove(request.token)
                    emit_change_event(self)
                emit_message_event(server, self, request)
            server.terminate_simulation()

        yield coro()


class Application(AbstractApplication):
    application_request_cls = ApplicationRequest
