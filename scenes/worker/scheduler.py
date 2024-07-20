from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from manim import DOWN, UL, UP, FadeIn, Line, Mobject, Wait

import esv
from scenes.worker.commands import Command, Commands, CommandType
from scenes.worker.coroutines import Coroutines
from scenes.worker.state_machines import (
    ActivityTaskStateMachine,
    TimerStateMachine,
    WorkflowStateMachines,
)
from scenes.worker.utils import labeled_rectangle

if TYPE_CHECKING:
    from scenes.worker.worker_scene import WorkerScene


@dataclass
class Scheduler(esv.Entity):
    coroutines: Coroutines
    def handle(self, event: esv.Event) -> bool:
        return True

    def run_all_coroutines_until_blocked(
        self,
        commands_that_will_be_generated_in_this_wft: list["Command"],
        machines: WorkflowStateMachines,
    ):
        """
        In Java, when user code calls a command-generating API (e.g. executeActivity, startTimer) it
        receives a promise, which it blocks on, and it emits a Command object containing an instance
        of a state machine, within which is a callback that will complete the promise.

        In Python, the user code emits a command, and this results in the creation of a state
        machine in Rust; that state machine has the ability to later emit an activation job (e.g.
        resolve_activity, fire_timer) that, when received by lang, will complete the promise.
        See handle_driven_results
        https://github.com/temporalio/sdk-core/blob/master/core/src/worker/workflow/machines/workflow_machines.rs
        """
        for command in commands_that_will_be_generated_in_this_wft:
            match command.command_type:
                case CommandType.SCHEDULE_ACTIVITY_TASK:
                    command.machine = ActivityTaskStateMachine(
                        workflow_machines=machines
                    )
                case CommandType.START_TIMER:
                    command.machine = TimerStateMachine(workflow_machines=machines)
                case _:
                    raise ValueError(command.command_type)
            machines.commands_generated_by_user_workflow_code.append(command)

            scene: "WorkerScene" = self.scene  # type: ignore

            if command.coroutine_id not in scene.coroutines.coroutines:
                scene.coroutines.add_coroutine(command.coroutine_id)

            coroutine = scene.coroutines.coroutines[command.coroutine_id]
            # command.mobj.move_to(coroutine.mobj.get_boundary_point(UP))
            coroutine.add_child(command)
            self.scene.add(command.mobj)
            commands = cast(Commands, self.scene.entities["commands"])
            command.move_to(commands)
            self.scene.play(Wait(1))
            # commands.commands.append(command)

            print(f"🟠 added animations to {command}: {command.animations}")

            def create_smbp_anim():
                assert command.machine
                return FadeIn(
                    Line(
                        start=coroutine.mobj.get_center(),
                        end=command.machine.mobj.get_center(),
                    )
                )

            # coroutine.animations.append(create_smbp_anim)
            # self.animations.append(create_smbp_anim)

    def render(self) -> Mobject:
        return labeled_rectangle("Scheduler")
