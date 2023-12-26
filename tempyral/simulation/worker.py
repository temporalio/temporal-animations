import asyncio
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import List, Tuple, TypedDict

from tempyral.simulation.api import (
    Command,
    CommandType,
    RespondActivityTaskCompleted,
    RespondWorkflowTaskCompleted,
)
from tempyral.simulation.entity import Entity
from tempyral.simulation.server import (
    CALL_ACTIVITY_WORKFLOW_ID,
    NOOP_WORKFLOW_ID,
    ActivityTask,
    Server,
    WorkflowId,
    WorkflowTask,
)


class ActivityWorker(Entity):
    async def poll(self, server: "Server"):
        while True:
            # Currently we're not actually simulating the long-poll; just the
            # dispatch from server to worker.
            at = await server.dispatch_activity_task()
            if at:
                await self.publish_message_event(server, self)
                await self.handle_at(at, server)
            await asyncio.sleep(0)

    async def handle_at(self, at: "ActivityTask", server: "Server"):
        await self.publish_message_event(self, server)
        await server.handle_request(RespondActivityTaskCompleted(None))


class CommentMarkers(TypedDict):
    go: str


COMMENT_MARKERS: CommentMarkers = {"go": "//"}


class Workflow(Entity, ABC):
    """
    A Workflow Definition, together with fake handling of the workflow by an SDK worker.
    """

    go: str
    workflow_id: WorkflowId

    def __init__(self):
        super().__init__()
        self.code, commands = self.parse_code("go")
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
        assert language == "go"
        comment_marker = COMMENT_MARKERS[language]
        i = 0
        for i, line in enumerate(self.go.splitlines()):
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
    go = """
func MyWorkflow(ctx workflow.Context) error {
    return nil
}
"""


class CallActivityWorkflow(Workflow):
    """
    A workflow that calls an activity.
    """

    workflow_id = CALL_ACTIVITY_WORKFLOW_ID
    go = """
func MyWorkflow(ctx workflow.Context) (int, error) {
    var activityResult int
    workflow.ExecuteActivity(MyActivity).Get(ctx, &result) // tempyral: CommandType.SCHEDULE_ACTIVITY_TASK
    return activityResult, nil
}
"""


Workflows = OrderedDict[WorkflowId, Workflow]


class WorkflowWorker(Entity, ABC):
    workflows: Workflows

    def __init__(self):
        super().__init__()

    async def poll(self, server: "Server"):
        while True:
            # Currently we're not actually simulating the long-poll; just the
            # dispatch from server to worker.
            assert (
                len(self.workflows) == 1
            ), "Workflow worker with multiple workflows is not supported"
            [workflow] = self.workflows.values()
            wft = await server.dispatch_workflow_task(workflow.workflow_id)
            if wft:
                await self.publish_message_event(server, self, events=tuple(wft.events))
                await self.handle_wft(wft, server)
            await asyncio.sleep(0)

    async def handle_wft(self, wft: "WorkflowTask", server: "Server"):
        wf = self.workflows[wft.workflow_id]
        await self.publish_message_event(
            self, server, name="RespondWorkflowTaskCompleted"
        )
        await server.handle_request(RespondWorkflowTaskCompleted(wf.handle_wft(wft)))


class NoOpWorkflowWorker(WorkflowWorker):
    workflows = OrderedDict([(NOOP_WORKFLOW_ID, NoOpWorkflow())])


class CallActivityWorkflowWorker(WorkflowWorker):
    workflows = OrderedDict([(CALL_ACTIVITY_WORKFLOW_ID, CallActivityWorkflow())])
