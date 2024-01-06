from collections import defaultdict
from typing import Callable


class Entity:
    """
    An entity in the simulation.

    It can publish two types of events to a renderer:
    - a change to its internal state
    - a message between two entities
    """

    next_id = defaultdict(int)
    terminate_simulation: Callable

    def __init__(self, time=0):
        key = type(self).__name__
        self.next_id[key] += 1
        self.id = self.next_id[key]
        self.time = time

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self.id})"

    __publish__ = {"id", "time"}

    def tick(self, message: "Entity"):
        message.time = self.time = max(self.time, message.time) + 1
