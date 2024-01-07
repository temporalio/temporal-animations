from scenes.ExecuteWorkflow import NoOpWorkflow
from tempyral.application import Application
from tempyral.simulation import Simulation, run_simulation


class StartWorkflowApplication(Application):
    """
    An application that starts a workflow.
    """

    typescript = """
const wfHandle = await client.start(myWorkflow, {        // tempyral: ApplicationRequestType.StartWorkflow "my-workflow-id"
    workflowId: 'my-workflow-id',
    taskQueue: 'my-task-queue',
});
"""


class StartWorkflow(Simulation):
    application_classes = [StartWorkflowApplication]
    workflow_classes = [NoOpWorkflow]


if __name__ == "__main__":
    run_simulation(StartWorkflow())
