import asyncio
from abc import ABC, abstractmethod

from tempyral.simulation.api import Command, RespondWorkflowTaskCompleted
from tempyral.simulation.entity import Entity
from tempyral.simulation.server import Server, WorkflowTask


class WorkflowWorker(Entity, ABC):
    go = ""

    async def poll(self, server: "Server"):
        while True:
            # Currently we're not actually simulating the long-poll; just the
            # dispatch from server to worker.
            wft = await server.dispatch_workflow_task()
            if wft:
                await self.publish_message_event(server, self, events=tuple(wft.events))
                await self.handle_wft(wft, server)
            await asyncio.sleep(0)

    @abstractmethod
    async def handle_wft(self, wft: "WorkflowTask", server: "Server"):
        ...


class NoOpWorkflowWorker(WorkflowWorker):
    """
    A Workflow Worker with a single workflow that does nothing (completes immediately).
    """

    go = """
func Workflow(ctx workflow.Context) error {
    return nil
}
"""

    async def handle_wft(self, wft: "WorkflowTask", server: "Server"):
        await self.publish_message_event(
            self, server, name="RespondWorkflowTaskCompleted"
        )
        await server.handle_request(
            RespondWorkflowTaskCompleted([Command.COMPLETE_WORKFLOW_EXECUTION])
        )
