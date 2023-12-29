import asyncio
import sys
import traceback
from typing import Coroutine, Iterable


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


async def debug(coro: Coroutine):
    try:
        await coro
    except asyncio.exceptions.CancelledError:
        pass
    except:
        traceback.print_exc(file=sys.stderr)
        import pdb

        pdb.post_mortem()
