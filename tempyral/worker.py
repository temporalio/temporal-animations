from abc import ABC, abstractmethod
from asyncio import Queue
from enum import Enum
from typing import Generic, List, Tuple, Type, TypeVar, Union, cast

from logger import log
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


class DirectiveType(Enum):
    WAIT_FOR_UPDATE = 1


class Worker(Entity, ABC, Generic[T]):
    long_poll_connection: Queue[T]

    async def poll(self, server: Server):
        while True:
            task = await self.long_poll_connection.get()
            log(f"got task: {task} {task.__dict__}", "W:")
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

        self.iter_commands_and_fake_sdk_directives = (
            self._iter_commands_and_fake_sdk_directives(directives)
        )
        self.blocked_lines = set()
        self.waiting_for_update_lines = set()
        super().__init__()

    __publish__ = EntityWithCode.__publish__ | {
        "code",
        "language",
        "blocked_lines",
    }

    def _iter_commands_and_fake_sdk_directives(
        self, raw_directives: List[Tuple[str, int]]
    ):
        """
        Lazily honor each command or directive annotation in the workflow code.
        """
        for raw, line_num in raw_directives:
            log(f"{line_num}:{raw}", "W: _iter_commands_and_fake_sdk_directives")
            # Each command or directive causes the workflow to block at that line
            self.blocked_lines.add(line_num)
            match cmd := eval(raw):
                case DirectiveType.WAIT_FOR_UPDATE:
                    # This line will be unblocked on acceptance of any update
                    # TODO: support multiple updates
                    self.waiting_for_update_lines.add(line_num)
                    log(
                        f"{line_num} WAIT_FOR_UPDATE: {self.blocked_lines} {self.waiting_for_update_lines}",
                        "W: process directive",
                    )
                case _ if isinstance(cmd, CommandType):
                    # This line will be unblocked when a WFT is received
                    # containing an event with the line_num token.
                    log(
                        f"{line_num} {cmd}: {self.blocked_lines} {self.waiting_for_update_lines}",
                        "W: process directive",
                    )
                    yield Command(cmd, None, line_num)
                case _:
                    raise ValueError(f"{cmd}")

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.blocked_lines})"

    def handle_wft(self, wft: WorkflowTask) -> List[Command]:
        log(f"{self.blocked_lines}", "W: handle_wft")
        # If the WFT contains history events that unblock futures, then unblock them.
        for e in wft.events:
            if (token := e.data.get("token")) != None:
                self.blocked_lines.remove(cast(int, token))

        commands = []

        # Obtain the next command or directive emitted by this workflow
        if not self.blocked_lines:
            match cmd := next(self.iter_commands_and_fake_sdk_directives, None):
                case Command():
                    commands.append(cmd)
        for u in wft.pending_updates:
            # TODO: Currently, any update unblocks all `waiting_for_update_lines`.
            while self.waiting_for_update_lines:
                self.blocked_lines.remove(self.waiting_for_update_lines.pop())
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
        commands = self.workflow.handle_wft(wft)
        log(
            f"{self.workflow.blocked_lines} {self.workflow.waiting_for_update_lines}",
            "W: handled wft",
        )
        await self.publish_change_event()
        msg = WorkflowTaskCompleted(wft.workflow_id, self.time, commands)
        await self.publish_message_event(self, server, msg)
        await server.handle_worker_request(msg)
        self.time = max(self.time, msg.time) + 1
        await self.publish_change_event()
