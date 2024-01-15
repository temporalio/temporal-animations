from tempyral.application import Application
from tempyral.simulation import Simulation, run_simulation
from tempyral.worker import Workflow


class SignalApplication(Application):
    """
    An application that starts a workflow and then sends it a signal
    """

    typescript = """
const wfHandle = await client.start(myWorkflow, {               // tempyral: ApplicationRequestType.StartWorkflow "my-workflow-id"
    workflowId: 'my-workflow-id',
    taskQueue: 'my-task-queue',
});
await wfHandle.signal(myIncrementer, 1)                         // tempyral: ApplicationRequestType.SignalWorkflow "my-workflow-id"
await wfHandle.result()                                         // tempyral: ApplicationRequestType.GetWorkflowResult "my-workflow-id"
"""


class SignalHandlerWorkflow(Workflow):
    """
    A workflow that handles an Signal.
    """

    typescript = """
const myIncrementer = wf.defineSignal<[number]>('myIncrementer');

export async function myWorkflow(): Promise<number> {
  let total = 0;
  wf.setHandler(
    myIncrementer,
    async (arg: number) => {
      total += arg;
    },
  );
  await wf.condition(() => total > 0);                          // tempyral: DirectiveType.WAIT_FOR_SIGNAL
  return total;                                                 // tempyral: CommandType.COMPLETE_WORKFLOW_EXECUTION 2
}
"""


class Signal(Simulation):
    application_classes = [SignalApplication]
    workflow_classes = [SignalHandlerWorkflow]


if __name__ == "__main__":
    run_simulation(Signal())
