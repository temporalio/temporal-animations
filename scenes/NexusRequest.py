from scenes.ExecuteWorkflow import NoOpWorkflow
from tempyral.application import Application
from tempyral.nexus import NexusServer, NexusSimulation, NexusWorker
from tempyral.simulation import run_simulation


class NexusRequestApplication(Application):
    """
    An application that starts a workflow.
    """

    typescript = """
const wfHandle = await client.start(myWorkflow, {        // tempyral: ApplicationRequestType.StartWorkflow "my-workflow-id"
    workflowId: 'my-workflow-id',
    taskQueue: 'my-task-queue',
});
"""


class NexusRequest(NexusSimulation):
    application_classes = [NexusRequestApplication]
    nexus_server_classes = [NexusServer]
    nexus_worker_classes = [NexusWorker]
    workflow_classes = [NoOpWorkflow]


if __name__ == "__main__":
    run_simulation(NexusRequest())
