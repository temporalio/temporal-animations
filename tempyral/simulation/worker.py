import asyncio
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import List

from tempyral.simulation.api import Command, RespondWorkflowTaskCompleted
from tempyral.simulation.entity import Entity
from tempyral.simulation.server import (
    NOOP_WORKFLOW_ID,
    Server,
    WorkflowId,
    WorkflowTask,
)


class WorkflowWorker(Entity):
    def __init__(self):
        super().__init__()
        self.workflows = OrderedDict([(NOOP_WORKFLOW_ID, NoOpWorkflow())])

    async def poll(self, server: "Server"):
        while True:
            # Currently we're not actually simulating the long-poll; just the
            # dispatch from server to worker.
            wft = await server.dispatch_workflow_task()
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


class Workflow(Entity, ABC):
    go: str
    workflow_id: WorkflowId

    @abstractmethod
    async def handle_wft(self, wft: "WorkflowTask", server: "Server"):
        ...


class NoOpWorkflow(Workflow):
    """
    A workflow that does nothing (completes immediately).
    """

    workflow_id = NOOP_WORKFLOW_ID
    go = """
func Workflow(ctx workflow.Context) error {
    return nil
}
"""

    def handle_wft(self, _: WorkflowTask) -> List[Command]:
        return [Command.COMPLETE_WORKFLOW_EXECUTION]
