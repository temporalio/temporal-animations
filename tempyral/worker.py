from abc import ABC, abstractmethod
from asyncio import Queue
from typing import Generic, List, Type, TypeVar, Union, cast

from log import log
from tempyral.api import (
    Command,
    CommandType,
    ProtocolMessage,
    ProtocolMessageType,
    WorkflowId,
)
from tempyral.code import EntityWithCode
from tempyral.entity import Entity
from tempyral.server import (
    ActivityTask,
    ActivityTaskCompleted,
    Server,
    WorkflowTask,
    WorkflowTaskCompleted,
)

T = TypeVar("T", bound=Union[ActivityTask, WorkflowTask])


class WorkflowPollRequest(Entity):
    pass


class Worker(Entity, ABC, Generic[T]):
    long_poll_connection: Queue[T]

    async def poll(self, server: Server):
        while True:
            await self.publish_message_event(
                self, server, WorkflowPollRequest(self.time)
            )
            task = await self.long_poll_connection.get()
            # TODO: Move this into server.dispatch method?
            await self.publish_message_event(server, self, task)
            self.time = max(self.time, task.time) + 1
            await self.handle_task(task, server)

    @abstractmethod
    async def handle_task(self, task: T, server: Server):
        ...


class ActivityWorker(Worker[ActivityTask]):
    def __init__(self, server: Server):
        super().__init__()
        self.long_poll_connection = (
            server.establish_activity_worker_long_poll_connection(self)
        )

    async def handle_task(self, at: ActivityTask, server: Server):
        await self.publish_message_event(self, server, at)
        await server.handle_worker_request(
            ActivityTaskCompleted(at.workflow_id, self.time, None, at.token)
        )


class Workflow(EntityWithCode, ABC):
    """
    A Workflow Definition, together with fake handling of the workflow by an SDK worker.
    """

    workflow_id: WorkflowId

    def __init__(self):
        if not hasattr(self, "language"):
            self.language = self._get_language()
        self.code, directives = self.parse_code(self.language)
        self.commands = (
            Command(eval(code), None, line_num) for code, line_num in directives
        )
        self.blocked_expressions = set()
        super().__init__()

    __publish__ = EntityWithCode.__publish__ | {
        "code",
        "language",
        "blocked_expressions",
    }

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.blocked_expressions})"

    def handle_wft(self, wft: WorkflowTask) -> List[Command]:
        """
        Currently, we assume that each WFT is handled by emitting a single command.
        """
        commands = []
        command = next(self.commands, None)
        if command and command.token is not None:
            self.blocked_expressions.add(command.token)
            commands.append(command)
        for u in wft.pending_updates:
            commands.extend(
                Command(
                    CommandType.PROTOCOL_MESSAGE,
                    ProtocolMessage(m, u.update_id),
                    None,
                )
                for m in [
                    ProtocolMessageType.UPDATE_ACCEPTED,
                    ProtocolMessageType.UPDATE_COMPLETED,
                ]
            )
        return commands


class WorkflowWorker(Worker[WorkflowTask]):
    def __init__(self, workflow_classes: List[Type[Workflow]], server: Server):
        super().__init__()
        self.workflows = [cls() for cls in workflow_classes]
        self.long_poll_connection = (
            server.establish_workflow_worker_long_poll_connection(self)
        )

    __publish__ = Worker.__publish__ | {"workflows"}

    @property
    def workflow(self) -> Workflow:
        assert (
            len(self.workflows) == 1
        ), "Workflow worker with multiple workflows is not supported"
        [workflow] = self.workflows
        return workflow

    async def handle_task(self, wft: WorkflowTask, server: Server):
        wf = self.workflow
        log(f"wf={wf} wft={wft}", "S: handle_wft")
        for e in wft.events:
            if (token := e.data.get("token")) != None:
                token = cast(int, token)
                if token in wf.blocked_expressions:
                    wf.blocked_expressions.remove(token)
                else:
                    log(
                        f"ERROR: expected {token} in {wf.blocked_expressions}",
                        "S: handle_wft",
                    )
        commands = wf.handle_wft(wft)
        for c in commands:
            if c.token is not None:
                wf.blocked_expressions.add(c.token)
        await self.publish_change_event()
        msg = WorkflowTaskCompleted(wft.workflow_id, self.time, commands)
        await self.publish_message_event(self, server, msg)
        await server.handle_worker_request(msg)
        self.time = max(self.time, msg.time) + 1
        await self.publish_change_event()
