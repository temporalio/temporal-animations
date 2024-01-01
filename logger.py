from typing import Any


def log(msg: Any, prefix: str):
    with open("/tmp/log", "a") as f:
        print(f"{prefix:30s}{msg}", file=f)
