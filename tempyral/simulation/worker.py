import asyncio
from abc import ABC, abstractmethod
from asyncio import Queue
from typing import Dict, Generic, List, Literal, Set, Tuple, Type, TypeVar, Union, cast

from tempyral import log
from tempyral.simulation.api import (
    Command,
    CommandType,
    RespondActivityTaskCompleted,
    RespondWorkflowTaskCompleted,
    WorkflowId,
)
from tempyral.simulation.entity import Entity
from tempyral.simulation.server import ActivityTask, Server, WorkflowTask

T = TypeVar("T", bound=Union[ActivityTask, WorkflowTask])


class Worker(Entity, ABC, Generic[T]):
    long_poll_connection: Queue[T]

    async def poll(self, server: Server):
        while True:
            task = await self.long_poll_connection.get()
            # TODO: Move this into server.dispatch method?
            await self.publish_message_event(server, self, entity=task)
            await self.handle_task(task, server)
            await asyncio.sleep(0)

    @abstractmethod
    async def handle_task(self, task: T, server: Server):
        ...

    def __getstate__(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "long_poll_connection"}


class ActivityWorker(Worker[ActivityTask]):
    def __init__(self, server: Server):
        super().__init__()
        self.long_poll_connection = (
            server.establish_activity_worker_long_poll_connection(self)
        )

    async def handle_task(self, at: ActivityTask, server: Server):
        await self.publish_message_event(self, server)
        await server.handle_request(
            RespondActivityTaskCompleted(at.workflow_id, None, at.token)
        )


Language = Literal["go", "python", "typescript", "java", "dotnet"]


COMMENT_MARKERS: Dict[Language, str] = {
    "go": "//",
    "java": "//",
    "python": "#",
    "dotnet": "//",
}


class Workflow(Entity, ABC):
    """
    A Workflow Definition, together with fake handling of the workflow by an SDK worker.
    """

    language: Language
    go: str
    workflow_id: WorkflowId

    def __init__(self):
        super().__init__()
        if not hasattr(self, "language"):
            self.language = self._get_language()
        self.code, commands = self.parse_code(self.language)
        self.commands = iter(commands)
        self.blocked_expressions: Set[int] = set()

    def _get_language(self) -> Language:
        available_languages = list(COMMENT_MARKERS)
        languages: List[Language] = [l for l in available_languages if hasattr(self, l)]
        assert (
            languages
        ), f"You must define the workflow code as a class attribute named one of {', '.join(available_languages)}"
        assert (
            len(languages) == 1
        ), "You must set the 'language' class attribute when supplying workflow code in multiple languages"
        [language] = languages
        return language

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.blocked_expressions})"

    def handle_wft(self, _: WorkflowTask) -> List[Command]:
        """
        Currently, we assume that each WFT is handled by emitting a single command.
        """
        command = next(self.commands)
        if command.token is not None:
            self.blocked_expressions.add(command.token)
        return [command]

    def parse_code(self, language: Language) -> Tuple[str, List[Command]]:
        """
        Return code, and list of commands.

        Strip out special WFT-handling directives, and convert these into the
        corresponding Command, together with line number.
        """
        lines: List[str] = []
        commands: List[Command] = []
        comment_marker = COMMENT_MARKERS[language]
        code = getattr(self, language)
        line_num = 1
        for line_num, line in enumerate(code.strip().splitlines(), line_num):
            code, _, command = line.partition(f"{comment_marker} tempyral:")
            if command:
                commands.append(Command(eval(command.strip()), line_num))
            lines.append(code)
        commands.append(Command(CommandType.COMPLETE_WORKFLOW_EXECUTION, line_num))
        return "\n".join(lines), commands


class WorkflowWorker(Worker[WorkflowTask]):
    def __init__(self, workflow_classes: List[Type[Workflow]], server: Server):
        super().__init__()
        self.workflows = [cls() for cls in workflow_classes]
        self.long_poll_connection = (
            server.establish_workflow_worker_long_poll_connection(self)
        )

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
        await self.publish_message_event(
            self, server, name="RespondWorkflowTaskCompleted"
        )
        await server.handle_request(
            RespondWorkflowTaskCompleted(wft.workflow_id, commands)
        )
