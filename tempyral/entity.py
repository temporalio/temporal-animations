from collections import defaultdict
from enum import Enum
from types import NoneType
from typing import Any, Callable, Iterable, Mapping

from schema import schema


class Entity:
    """
    An entity in the simulation.
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

    def update(self, **kwargs):
        self.__dict__.update(kwargs)
        # TODO: circular
        from tempyral.event import emit_change_event

        emit_change_event(self)


def to_serializable(obj: Any) -> dict | list | int | bool | str | None:
    if isinstance(obj, Entity):
        data = {k: to_serializable(getattr(obj, k)) for k in obj.__publish__}
        schema_cls = next(
            filter(
                None,
                (getattr(schema, cls.__name__, None) for cls in obj.__class__.mro()),
            )
        )
        data["_type"] = schema_cls.__name__
        return data
    elif isinstance(obj, Enum):
        return {"_type": obj.__class__.__name__, "value": obj.value, "name": obj.name}
    elif isinstance(obj, Mapping):
        return {k: to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, str):
        return obj
    elif isinstance(obj, Iterable):
        return [to_serializable(v) for v in obj]
    elif hasattr(obj, "__dict__"):
        return to_serializable(obj.__dict__)
    elif isinstance(obj, (int, bool, NoneType)):
        return obj
    else:
        raise TypeError(f"Unexpected type: {type(obj)}")
