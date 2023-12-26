from tempyral.scene import TemporalScene
from tempyral.simulation import Application, Server, WorkflowWorker


class ExecuteWorkflow(TemporalScene):
    def simulation(
        self,
        server: Server,
        app: Application,
        workflow_worker: WorkflowWorker,
    ):
        yield app.start_workflow(server)
        yield workflow_worker.poll(server)
