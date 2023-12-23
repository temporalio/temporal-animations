from tempyral.scene import TemporalScene
from tempyral.simulation import Application, NoOpWorkflowWorkflowWorker, Server


class ExecuteWorkflow(TemporalScene):
    def simulation(
        self,
        server: Server,
        app: Application,
        workflow_worker: NoOpWorkflowWorkflowWorker,
    ):
        yield app.start_workflow(server)
        yield workflow_worker.poll(server)
