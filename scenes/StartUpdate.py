from scenes.ExecuteUpdate import UpdateHandlerWorkflow
from tempyral.application import Application
from tempyral.simulation import Simulation, run_simulation


class StartUpdateApplication(Application):
    """
    An application that starts a workflow and starts an update
    """

    typescript = """
const wfHandle = await client.start(myWorkflow, {                               // tempyral: ApplicationRequestType.StartWorkflow "my-workflow-id"
    workflowId: 'my-workflow-id',
    taskQueue: 'my-task-queue',
});
const updateHandle = await wfHandle.startUpdate(myIncrementer, {args: [1]})     // tempyral: ApplicationRequestType.StartUpdate "my-workflow-id"
const updateResult = await updateHandle.result()                                // tempyral: ApplicationRequestType.GetUpdateResult "my-workflow-id"
"""


class StartUpdate(Simulation):
    application_classes = [StartUpdateApplication]
    workflow_classes = [UpdateHandlerWorkflow]


if __name__ == "__main__":
    run_simulation(StartUpdate())
