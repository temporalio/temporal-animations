from typing import Coroutine

from tempyral.application import AbstractApplication
from tempyral.request_response import RequestResponse
from tempyral.server import Server
from tempyral.simulation import Simulation, emit_init_event, run_coroutines
from tempyral.worker import WorkflowWorker


class NexusServer:
    pass


class NexusWorker:
    pass


class NexusApplicationRequest(RequestResponse):
    pass


class NexusApplication(AbstractApplication):
    application_request_cls = NexusApplicationRequest


class NexusSimulation(Simulation):
    application_classes = [NexusApplication]
    nexus_worker_classes = [NexusWorker]

    async def do_simulation(self):
        """
        Instantiate simulation entities, emit initial event, and run coroutines
        that will emit subsequent events.
        """
        server, apps, wworkers, aworkers, nexus_server, nexus_workers = (
            Server(),
            [cls() for cls in self.application_classes],
            [WorkflowWorker(self.workflow_classes)],
            [cls() for cls in self.activity_worker_classes],
            NexusServer(),
            [cls() for cls in self.nexus_worker_classes],
        )
        emit_init_event(server, apps, wworkers, aworkers)

        coros: list[Coroutine] = [w.poll(server) for w in wworkers + aworkers]
        for app in apps:
            coros.extend(app.get_coroutines(server))

        await run_coroutines(coros)
