import asyncio
import sys
import traceback
from typing import Coroutine, Iterable, cast


def notnull[T](t: T | None) -> T:
    return cast(T, t)


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


def drain[T](source: list[T]) -> list[T]:
    vals = []
    while source:
        vals.append(source.pop())
    return vals


async def debug(coro: Coroutine):
    try:
        await coro
    except asyncio.exceptions.CancelledError:
        pass
    except:
        traceback.print_exc(file=sys.stderr)
        import pdb

        pdb.post_mortem()
