from scenes.Signal import SignalHandlerWorkflow
from tempyral.application import Application
from tempyral.simulation import Simulation, run_simulation


class SignalWithStartApplication(Application):
    """
    An application that starts a workflow via SignalWithStart.
    """

    typescript = """
const wfHandle = await client.signalWithStart(myWorkflow, {                // tempyral: ApplicationRequestType.SignalWithStartWorkflow "my-workflow-id"
    workflowId: 'my-workflow-id',
    signal: myIncrementer,
    signalArgs: [1],
    taskQueue: 'my-tast-queue',
});
await wfHandle.result()                                                    // tempyral: ApplicationRequestType.GetWorkflowResult "my-workflow-id"
"""


class SignalWithStart(Simulation):
    application_classes = [SignalWithStartApplication]
    workflow_classes = [SignalHandlerWorkflow]


if __name__ == "__main__":
    run_simulation(SignalWithStart())
