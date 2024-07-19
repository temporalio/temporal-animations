from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterator, Optional

from manim import VGroup, VMobject

import esv
from scenes.worker.constants import CONTAINER_HEIGHT, CONTAINER_WIDTH
from scenes.worker.history import HistoryEvent, HistoryEventId, HistoryEventType
from scenes.worker.utils import ContainerRectangle, labeled_rectangle
from schema import schema

if TYPE_CHECKING:
    from scenes.worker import input
    from scenes.worker.scheduler import Scheduler

MACHINE_RADIUS = 0.3


@dataclass
class StateMachine(esv.Entity):
    workflow_machines: "WorkflowStateMachines"

    def handle(self, event: "input.Event") -> bool:
        # WorkflowStateMachines dispatch history events to state machines; they
        # do not handle raw events as they are passed down the tree.
        return False

    def render(self) -> VMobject:
        label = self.__class__.__name__.replace("StateMachine", "\nStateMachine")
        return labeled_rectangle(label)

    def handle_history_event(self, event: HistoryEvent): ...


@dataclass
class Command:
    command_type: schema.CommandType
    coroutine_id: str
    machine: Optional[StateMachine] = None


class WorkflowTaskStateMachine(StateMachine):
    def __init__(
        self,
        workflow_machines: "WorkflowStateMachines",
        commands_that_will_be_generated_in_this_wft: list[Command],
    ):
        super().__init__(
            name="WorkflowTaskStateMachine", workflow_machines=workflow_machines
        )
        self.commands_that_will_be_generated_in_this_wft = (
            commands_that_will_be_generated_in_this_wft
        )

    def handle_history_event(self, event: HistoryEvent):
        match event.event_type:
            case HistoryEventType.WFT_SCHEDULED:
                print("WFT_SCHEDULED")
            case HistoryEventType.WFT_STARTED:
                print("WFT_STARTED")
                self.workflow_machines.scheduler.run_all_coroutines_until_blocked(
                    self.commands_that_will_be_generated_in_this_wft,
                    self.workflow_machines,
                )
            case HistoryEventType.WFT_COMPLETED:
                print("WFT_COMPLETED")
            case _:
                raise ValueError(event)


class ActivityTaskStateMachine(StateMachine):
    def handle_history_event(self, event: HistoryEvent):
        match event.event_type:
            case HistoryEventType.ACTIVITY_TASK_SCHEDULED:
                print("AT_SCHEDULED")
            case HistoryEventType.ACTIVITY_TASK_STARTED:
                print("AT_STARTED")
            case HistoryEventType.ACTIVITY_TASK_COMPLETED:
                print("AT_COMPLETED")
            case _:
                raise ValueError(event)


class TimerStateMachine(StateMachine):
    def handle_history_event(self, event: HistoryEvent):
        match event.event_type:
            case HistoryEventType.TIMER_STARTED:
                print("TIMER_STARTED")
            case HistoryEventType.TIMER_FIRED:
                print("TIMER_FIRED")
            case _:
                raise ValueError(event)


@dataclass
class WorkflowStateMachines(esv.Entity):
    scheduler: "Scheduler"
    # User workflow code is represented by a stream of batches of commands generated in each WFT.
    user_workflow_code: Iterator[list[Command]]
    commands_generated_by_user_workflow_code: deque[Command] = field(
        default_factory=deque
    )
    state_machines: dict[HistoryEventId, StateMachine] = field(default_factory=dict)

    def handle(self, event: "input.Event") -> bool:
        self.handle_history_event(event.history_event)
        return True

    def handle_history_event(self, event: HistoryEvent) -> None:
        # TODO: self.is_replaying

        if event.event_type == HistoryEventType.WF_STARTED:
            # Non-stateful event
            # Create a DeterministicRunner ready to run the main workflow method
            # Java: see SyncWorkflow.start()
            ...

        elif event.event_type == HistoryEventType.WFT_SCHEDULED:
            # Non-stateful event
            # Create an instance of WorkflowTaskStateMachine.
            machine = self.add_machine(
                event,
                WorkflowTaskStateMachine(self, next(self.user_workflow_code)),
            )
            self.explain(
                r"""
                WORKFLOW\_TASK\_SCHEDULED is the first event in a sequence of
                workflow task events. When the state machines encounter this
                event, they create a new instance of WorkflowTaskStateMachine. 
                """,
                target=machine,
            )

        elif event.event_type == HistoryEventType.WFT_STARTED:
            # Look up WorkflowTaskStateMachine instance and handle the event.
            # The state machine transition calls runAllUntilBlocked() if this is the last
            # WFT_STARTED event in history (i.e. no WFT_COMPLETED for it yet).
            machine = self.state_machines[event.initiating_event_id]
            machine.handle_history_event(event)
            self.explain(
                r"""
                WORKFLOW\_TASK\_STARTED is handled by the instance of
                WorkflowTaskStateMachine that was created previously. It runs
                all coroutines until blocked. This is the first time we're
                executing user code, so you'll see the main workflow coroutine
                come into existence, along with a child coroutine that it
                creates.
                """,
                target=machine,
            )

        elif event.event_type == HistoryEventType.WFT_COMPLETED:
            # Look up WorkflowTaskStateMachine instance and handle the event.
            # The state machine transition calls runAllUntilBlocked().
            self.state_machines[event.initiating_event_id].handle_history_event(event)

        elif event.event_type == HistoryEventType.TIMER_STARTED:
            # Command event: see below
            #
            # We see this event because user code called `sleep(duration)`, which is implemented as
            # `newTimer(duration).get()`. `newTimer` returns a workflow.Promise backed by a new
            # TimerStateMachine instance (i.e. a promise-completing callback is passed into the
            # state machine). The state machine emits the START_TIMER command on creation and, when
            # later transitioning to complete, will complete the promise.

            # TODO: should be created by command and set promise-completing callback
            machine = self.add_machine(
                event, TimerStateMachine("TimerStateMachine", workflow_machines=self)
            )
            self.explain(
                r"""We're seeing TIMER\_STARTED because in a previous workflow task, some user code
            made a call to `sleep(duration)`.""",
                target=machine,
            )

        elif event.event_type == HistoryEventType.TIMER_FIRED:
            # Look up TimerStateMachine instance and handle the event by calling the promise completion
            # callback that was provided when the state machine was created.
            # see TimerStateMachine.java
            self.state_machines[event.initiating_event_id].handle_history_event(event)

        elif event.event_type == HistoryEventType.ACTIVITY_TASK_SCHEDULED:
            # Command event: see below
            #
            # Same pattern as TIMER_STARTED: we see this event because the user's code called
            # WorkflowInternal.executeActivity, which emits the SCHEDULE_ACTIVITY_TASK command that
            # creates this event, and creates a workflow.Promise backed by an ActivityStateMachine,
            # such that the promise is completed when the activity is completed.

            # TODO: should be created by command and set promise-completing callback
            self.add_machine(
                event,
                ActivityTaskStateMachine(
                    "ActivityTaskStateMachine", workflow_machines=self
                ),
            )

        elif event.event_type == HistoryEventType.ACTIVITY_TASK_STARTED:
            self.state_machines[event.initiating_event_id].handle_history_event(event)

        elif event.event_type == HistoryEventType.ACTIVITY_TASK_COMPLETED:
            self.state_machines[event.initiating_event_id].handle_history_event(event)

        # Command events
        # --------------
        if event.event_type.is_command_event():
            # Events corresponding to a command issued by user workflow code
            # E.g. ACTIVITY_TASK_SCHEDULED, TIMER_STARTED, WORKFLOW_EXECUTION_COMPLETED

            # At some point, we executed some user code in one of the workflow coroutines and it
            # generated the command corresponding to this event. (If we are replaying from the
            # beginning then that just happened in this WFT; but if we are a sticky worker with this
            # workflow execution in cache, then that happened in a previous WFT.) When that
            # happened, we created an instance of the state machine corresponding to the event, and
            # enqueued a Command object containing the state machine instance.

            # Now, we have encountered the corresponding event in history. It should be at the front
            # of the queue.
            command = self.commands_generated_by_user_workflow_code.popleft()
            assert event.event_type.matches_command_type(command.command_type)
            assert command.machine
            command.machine.handle_history_event(event)

    def add_machine(
        self, initiating_event: HistoryEvent, machine: StateMachine
    ) -> StateMachine:
        self.state_machines[initiating_event.id] = machine
        # TODO: Are we going to "mark" or "register" self.state_machines as the
        # "official" children?
        self.add_child(machine)
        return machine

    def render(self) -> VMobject:
        container = ContainerRectangle(width=CONTAINER_WIDTH, height=CONTAINER_HEIGHT)
        state_machines = VGroup(
            *(c.mobj for _, c in sorted(self.state_machines.items()))
        ).move_to(container)
        if self.state_machines:
            state_machines.arrange_in_grid()
        return VGroup(container, state_machines)
