from scenes.ExecuteWorkflow import NoOpWorkflow
from tempyral.application import Application
from tempyral.nexus import NexusServer, NexusSimulation, NexusWorker
from tempyral.simulation import run_simulation


class NexusRequestApplication(Application):
    """
    An application that makes a Nexus request.
    """

    typescript = """
const handle = await nexusClient.request(nexusEndpoint, {        // tempyral: ApplicationRequestType.NexusRequest "my-request-id"
});
"""


class NexusRequest(NexusSimulation):
    application_classes = [NexusRequestApplication]
    nexus_server_classes = [NexusServer]
    nexus_worker_classes = [NexusWorker]
    workflow_classes = [NoOpWorkflow]


if __name__ == "__main__":
    run_simulation(NexusRequest())
