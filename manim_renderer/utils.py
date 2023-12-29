from typing import Iterable


def only[T](it: Iterable[T], msg="") -> T:
    it = iter(it)
    try:
        t = next(it)
    except StopIteration:
        raise ValueError(f"Iterable is empty{msg and f': {msg}'}")
    try:
        next(it)
        raise ValueError(f"Iterable had more than one item{msg and f': {msg}'}")
    except StopIteration:
        return t
