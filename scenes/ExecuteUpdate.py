from manim_renderer.scene import TemporalScene, run_simulation
from tempyral import Application, Workflow


class ExecuteUpdateApplication(Application):
    """
    An application that starts a workflow and executes an update
    """

    typescript = """
const wfHandle = await client.start(myWorkflow, {               // tempyral: ApplicationRequestType.StartWorkflow "my-workflow-id"
    workflowId: 'my-workflow-id',
    taskQueue: 'my-task-queue',
});
const updateResult = wfHandle.executeUpdate(myUpdate)           // tempyral: ApplicationRequestType.ExecuteUpdate "my-workflow-id"
"""


class UpdateHandlerWorkflow(Workflow):
    """
    A workflow that handles an Update.
    """

    typescript = """
const myUpdate = wf.defineUpdate<number, [number]>('myUpdate');

export async function myWorkflow(): Promise<number> {
  let total = 0;
  wf.setHandler(
    myUpdate,
    async (arg: number) => {
      total += arg;
      return total;
    },
    { validator: (arg: number) => arg > 0 }
  );
  await wf.condition(() => total > 0);                          // tempyral: DirectiveType.WAIT_FOR_UPDATE
  return total;                                                 // tempyral: CommandType.COMPLETE_WORKFLOW_EXECUTION
}
"""


class ExecuteUpdate(TemporalScene):
    application_classes = [ExecuteUpdateApplication]
    workflow_classes = [UpdateHandlerWorkflow]


if __name__ == "__main__":
    run_simulation(ExecuteUpdate())
