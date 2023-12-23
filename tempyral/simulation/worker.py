import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from tempyral.simulation.api import WorkerRequestType
from tempyral.simulation.entity import Entity

if TYPE_CHECKING:
    from tempyral.simulation.server import Server, WorkflowTask


class WorkflowWorker(Entity, ABC):
    async def poll(self, server: "Server"):
        while True:
            # Currently we're not actually simulating the long-poll; just the
            # dispatch from server to worker.
            await server.dispatch_wft_if_new_events(self)
            await asyncio.sleep(0)

    @abstractmethod
    async def handle_wft(self, wft: "WorkflowTask", server: "Server"):
        ...


class NoOpWorkflowWorkflowWorker(WorkflowWorker):
    """
    A Workflow Worker with a single workflow that does nothing (completes immediately).
    """

    async def handle_wft(self, wft: "WorkflowTask", server: "Server"):
        await self.publish_message_event(
            self, server, name="RespondWorkflowTaskCompleted"
        )
        await server.handle_request(WorkerRequestType.RespondWorkflowTaskCompleted)
