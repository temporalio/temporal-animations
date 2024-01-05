from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncGenerator, Generic, List, Type, TypeVar, cast

from common.logger import log
from schema import models
from tempyral.api import (
    Command,
    CommandType,
    HistoryEventType,
    ProtocolMessage,
    ProtocolMessageType,
    WorkflowId,
)
from tempyral.code import WithCode
from tempyral.entity import Entity
from tempyral.request_response import (
    ActivityTask,
    WorkerPollRequest,
    WorkerRequest,
    WorkflowTask,
)
from tempyral.server import ActivityTaskCompleted, Server, WorkflowTaskCompleted

T = TypeVar("T", bound=ActivityTask | WorkflowTask)


class DirectiveType(Enum):
    WAIT_FOR_SIGNAL = 1
    WAIT_FOR_UPDATE = 1


class Worker(Entity, ABC, Generic[T]):
    async def poll(self, server: Server):
        while True:
            request = WorkerPollRequest("", self.task_factory(), 0, 0)
            await self.publish_message_event(self, server, request)
            response = await server.handle_worker_poll_request(request)
            task = response.task
            log(f"got task: {task} {task.__dict__}", "W:")
            await self.publish_message_event(server, self, response)
            self.tick(request)
            # TODO: token nullability
            await self.handle_task(task, response.token or 0, server)

    @abstractmethod
    def task_factory(self) -> T:
        ...

    @abstractmethod
    async def handle_task(self, task: T, token: int, server: Server):
        ...

    async def send_request(self, request: WorkerRequest, server: Server):
        await self.publish_message_event(self, server, request)
        await server.handle_worker_request(request)
        request.time = server.time
        self.tick(request)
        await self.publish_change_event()


class ActivityWorker(Worker[ActivityTask], WithCode):
    typescript = """
fn myActivity() {
  return doAnything()
}
"""

    def __init__(self):
        if not hasattr(self, "language"):
            self.language = self._get_language()
        self.code, _ = self.parse_code(self.language)
        self.blocked_lines = set()
        super().__init__()

    __publish__ = Worker.__publish__ | {
        "code",
        "language",
        "blocked_lines",
    }

    def task_factory(self) -> ActivityTask:
        return ActivityTask("", [])

    async def handle_task(
        self,
        at: ActivityTask,
        token: int,
        server: Server,
    ):
        await self.send_request(
            ActivityTaskCompleted(at.workflow_id, self.time, None, token), server
        )


class Workflow(Entity, WithCode, ABC):
    """
    A Workflow Definition, together with fake handling of the workflow by an SDK worker.
    """

    workflow_id: WorkflowId

    def __init__(self, worker: "WorkflowWorker"):
        if not hasattr(self, "language"):
            self.language = self._get_language()
        self.worker = worker
        self.code, raw_directives = self.parse_code(self.language)
        self.raw_directives = iter(raw_directives)
        self.blocked_lines = set()
        self.blocked_lines_waiting_for_signal = set()
        self.blocked_lines_waiting_for_update = set()
        super().__init__()

    __publish__ = Entity.__publish__ | {
        "code",
        "language",
        "blocked_lines",
    }

    def _advance_to_next_command_or_fake_sdk_directive(self) -> Command | None:
        """
        Lazily honor each command or directive annotation in the workflow code.
        """
        raw, line_num = next(self.raw_directives)

        log(f"{line_num}:{raw}", "W: _advance_to_next_command_or_fake_sdk_directive")

        # Each command or directive causes the workflow to block at that line
        self.blocked_lines.add(line_num)
        match cmd := eval(raw):
            case DirectiveType.WAIT_FOR_SIGNAL:
                # This line will be unblocked on acceptance of any signal
                # TODO: support multiple signals
                self.blocked_lines_waiting_for_signal.add(line_num)
            case DirectiveType.WAIT_FOR_UPDATE:
                # This line will be unblocked on acceptance of any update
                # TODO: support multiple updates
                self.blocked_lines_waiting_for_update.add(line_num)
            case _ if isinstance(cmd, CommandType):
                # This line will be unblocked when a WFT is received
                # containing an event with the line_num token.
                return Command(cmd, None, line_num)
            case _:
                raise ValueError(f"{cmd}")

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.blocked_lines})"

    async def handle_wft(self, task: WorkflowTask) -> List[Command]:
        commands = []

        if not self.blocked_lines:
            commands.extend([cmd async for cmd in self.advance()])

        # If the WFT contains history events that unblock futures, then unblock them.
        for e in task.events:
            if (token := e.data.get("token")) != None:
                line_num = cast(int, token)
                self.blocked_lines.remove(line_num)
            if e.event_type == HistoryEventType.WF_SIGNALED:
                # TODO: Currently, any signal unblocks all waiting_for_signal lines.
                while self.blocked_lines_waiting_for_signal:
                    self.blocked_lines.remove(
                        self.blocked_lines_waiting_for_signal.pop()
                    )
            await self.worker.publish_change_event()

        update_commands = []
        for u in task.pending_updates:
            # TODO: Currently, any update unblocks all waiting_for_update lines.
            while self.blocked_lines_waiting_for_update:
                self.blocked_lines.remove(self.blocked_lines_waiting_for_update.pop())
            await self.worker.publish_change_event()
            update_commands.extend(
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

        if not self.blocked_lines:
            commands.extend([cmd async for cmd in self.advance()])

        # Commands last, since they may include a WF_COMPLETED
        return update_commands + commands

    async def advance(self) -> AsyncGenerator[Command, None]:
        # Advance to the workflow state corresponding to the next command or
        # directive emitted by this workflow
        if cmd := self._advance_to_next_command_or_fake_sdk_directive():
            yield cmd
        await self.worker.publish_change_event()


class WorkflowWorker(Worker[WorkflowTask]):
    def __init__(self, workflow_classes: List[Type[Workflow]]):
        super().__init__()
        self.workflows = [cls(self) for cls in workflow_classes]

    __publish__ = Worker.__publish__ | {"workflows"}

    def as_serializable(self) -> models.Entity:
        data = self.get_serializable_data()
        data["workflows"] = [wf.as_serializable() for wf in self.workflows]
        cls = self.get_serializable_cls()
        return cls(**data)

    def task_factory(self) -> WorkflowTask:
        return WorkflowTask("", [], [])

    @property
    def workflow(self) -> Workflow:
        assert (
            len(self.workflows) == 1
        ), "Workflow worker with multiple workflows is not supported"
        [workflow] = self.workflows
        return workflow

    async def handle_task(self, wft: WorkflowTask, _: int, server: Server):
        commands = await self.workflow.handle_wft(wft)
        await self.send_request(
            WorkflowTaskCompleted(wft.workflow_id, self.time, commands), server
        )
