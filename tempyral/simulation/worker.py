import asyncio
from abc import ABC
from collections import OrderedDict
from typing import List, Tuple, TypedDict

from tempyral import log
from tempyral.simulation.api import (
    Command,
    CommandType,
    RespondActivityTaskCompleted,
    RespondWorkflowTaskCompleted,
    WorkflowId,
)
from tempyral.simulation.entity import Entity
from tempyral.simulation.server import (
    CALL_ACTIVITY_WORKFLOW_ID,
    NOOP_WORKFLOW_ID,
    ActivityTask,
    Server,
    WorkflowTask,
)


class ActivityWorker(Entity):
    def __init__(self, server: Server):
        super().__init__()
        server.establish_activity_worker_long_poll_connection(self)

    async def poll(self, server: Server):
        while True:
            log(
                server.activity_worker_long_poll_connections[self]._queue,  # type: ignore (non-public attribute)
                "S: ActivityWorker.poll",
            )
            at = await server.activity_worker_long_poll_connections[self].get()
            await self.publish_message_event(server, self, entity=at)
            await self.handle_at(at, server)
            await asyncio.sleep(0)

    async def handle_at(self, at: "ActivityTask", server: "Server"):
        await self.publish_message_event(self, server)
        await server.handle_request(RespondActivityTaskCompleted(at.workflow_id, None))


class CommentMarkers(TypedDict):
    go: str


COMMENT_MARKERS: CommentMarkers = {"go": "//"}


class Workflow(Entity, ABC):
    """
    A Workflow Definition, together with fake handling of the workflow by an SDK worker.
    """

    code: str
    language: str
    workflow_id: WorkflowId

    def __init__(self):
        super().__init__()
        self.code, commands = self.parse_code(self.language)
        self.commands = iter(commands)

    def handle_wft(self, _: WorkflowTask) -> List[Command]:
        """
        Currently, we assume that each WFT is handled by emitting a single command.
        """
        return [next(self.commands)]

    def parse_code(self, language: str) -> Tuple[str, List[Command]]:
        """
        Return code, and list of commands.

        Strip out special WFT-handling directives, and convert these into the
        corresponding Command, together with line number.
        """
        lines: List[str] = []
        commands: List[Command] = []
        comment_marker = COMMENT_MARKERS[language]
        i = 0
        for i, line in enumerate(self.code.splitlines()):
            code, _, command = line.partition(f"{comment_marker} tempyral:")
            if command:
                commands.append(Command(eval(command.strip()), i))
            lines.append(code)
        commands.append(Command(CommandType.COMPLETE_WORKFLOW_EXECUTION, i))
        return "\n".join(lines), commands


class NoOpWorkflow(Workflow):
    """
    A workflow that does nothing (completes immediately).
    """

    workflow_id = NOOP_WORKFLOW_ID
    code = """
func MyWorkflow(ctx workflow.Context) error {
    return nil
}
"""
    language = "go"


class CallActivityWorkflow(Workflow):
    """
    A workflow that calls an activity.
    """

    workflow_id = CALL_ACTIVITY_WORKFLOW_ID
    code = """
func MyWorkflow(ctx workflow.Context) (int, error) {
    var activityResult int
    workflow.ExecuteActivity(MyActivity).Get(ctx, &result) // tempyral: CommandType.SCHEDULE_ACTIVITY_TASK
    return activityResult, nil
}
"""
    language = "go"


Workflows = OrderedDict[WorkflowId, Workflow]


class WorkflowWorker(Entity, ABC):
    workflows: Workflows

    def __init__(self, server: Server):
        super().__init__()
        server.establish_workflow_worker_long_poll_connection(self)

    @property
    def workflow(self) -> Workflow:
        assert (
            len(self.workflows) == 1
        ), "Workflow worker with multiple workflows is not supported"
        [workflow] = self.workflows.values()
        return workflow

    async def poll(self, server: "Server"):
        while True:
            log(
                server.workflow_worker_long_poll_connections[self]._queue,  # type: ignore (non-public attribute)
                "S: WorkflowWorker.poll",
            )
            wft = await server.workflow_worker_long_poll_connections[self].get()
            await self.publish_message_event(server, self, entity=wft)
            await self.handle_wft(wft, server)
            await asyncio.sleep(0)

    async def handle_wft(self, wft: "WorkflowTask", server: "Server"):
        wf = self.workflows[wft.workflow_id]
        await self.publish_message_event(
            self, server, name="RespondWorkflowTaskCompleted"
        )
        await server.handle_request(
            RespondWorkflowTaskCompleted(wft.workflow_id, wf.handle_wft(wft))
        )


class NoOpWorkflowWorker(WorkflowWorker):
    workflows = OrderedDict([(NOOP_WORKFLOW_ID, NoOpWorkflow())])


class CallActivityWorkflowWorker(WorkflowWorker):
    workflows = OrderedDict([(CALL_ACTIVITY_WORKFLOW_ID, CallActivityWorkflow())])
