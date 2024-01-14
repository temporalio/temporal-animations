from tempyral.application import Application
from tempyral.simulation import Simulation, run_simulation
from tempyral.worker import Workflow


class ExecuteUpdateApplication(Application):
    """
    An application that starts a workflow and executes an update
    """

    typescript = """
const wfHandle = await client.start(myWorkflow, {               // tempyral: ApplicationRequestType.StartWorkflow "my-workflow-id"
    workflowId: 'my-workflow-id',
    taskQueue: 'my-task-queue',
});
const updateResult = await wfHandle.executeUpdate(myIncrementer, {args: [1]})     // tempyral: ApplicationRequestType.ExecuteUpdate "my-workflow-id"
"""


class UpdateHandlerWorkflow(Workflow):
    """
    A workflow that handles an Update.
    """

    typescript = """
const myIncrementer = wf.defineUpdate<number, [number]>('myIncrementer');

export async function myWorkflow(): Promise<number> {
  let total = 1;
  wf.setHandler(
    myIncrementer,
    async (arg: number) => {
      total += arg;
      return total;
    },
    { validator: (arg: number) => arg > 0 }
  );
  await wf.condition(() => total > 1);                          // tempyral: DirectiveType.WAIT_FOR_UPDATE 2
  return total;                                                 // tempyral: CommandType.COMPLETE_WORKFLOW_EXECUTION 2
}
"""


class ExecuteUpdate(Simulation):
    application_classes = [ExecuteUpdateApplication]
    workflow_classes = [UpdateHandlerWorkflow]


if __name__ == "__main__":
    run_simulation(ExecuteUpdate())
