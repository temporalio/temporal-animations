from scenes.ExecuteUpdate import UpdateHandlerWorkflow
from tempyral.application import Application
from tempyral.simulation import Simulation, run_simulation


class StartWorkflowAndExecuteUpdateApplication(Application):
    """
    An application that starts a workflow.
    """

    typescript = """
const myUpdate = client.newUpdate(myIncrementer, {args: [1]})
const wfHandle = await client.start(myWorkflow, {        // tempyral: ApplicationRequestType.StartWorkflowAndExecuteUpdate "my-workflow-id"
    workflowId: 'my-workflow-id',
    startOperations: [myUpdate],
    taskQueue: 'my-task-queue',
});
const updateResult = myUpdate.result()  // => 2 (no RPC)
"""


class StartWorkflowAndExecuteUpdate(Simulation):
    application_classes = [StartWorkflowAndExecuteUpdateApplication]
    workflow_classes = [UpdateHandlerWorkflow]


if __name__ == "__main__":
    run_simulation(StartWorkflowAndExecuteUpdate())
