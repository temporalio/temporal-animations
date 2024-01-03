from manim_renderer.scene import TemporalScene, run_simulation
from tempyral import Application, Workflow


class SignalWorkflowApplication(Application):
    """
    An application that starts a workflow and then sends it a signal
    """

    typescript = """
const wfHandle = await client.start(myWorkflow, {               // tempyral: ApplicationRequestType.StartWorkflow "my-workflow-id"
    workflowId: 'my-workflow-id',
    taskQueue: 'my-task-queue',
});
await wfHandle.signal(mySignal)                                 // tempyral: ApplicationRequestType.SignalWorkflow "my-workflow-id"
await wfHandle.result()                                         // tempyral: ApplicationRequestType.GetWorkflowResult "my-workflow-id"
"""


class SignalHandlerWorkflow(Workflow):
    """
    A workflow that handles an Signal.
    """

    typescript = """
const mySignal = wf.defineSignal<[number]>('mySignal');

export async function myWorkflow(): Promise<number> {
  let total = 0;
  wf.setHandler(
    mySignal,
    async (arg: number) => {
      total += arg;
    },
  );
  await wf.condition(() => total > 0);                          // tempyral: DirectiveType.WAIT_FOR_SIGNAL
  return total;                                                 // tempyral: CommandType.COMPLETE_WORKFLOW_EXECUTION
}
"""


class SignalWorkflow(TemporalScene):
    application_classes = [SignalWorkflowApplication]
    workflow_classes = [SignalHandlerWorkflow]


if __name__ == "__main__":
    run_simulation(SignalWorkflow())
