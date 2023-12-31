from typing import Any


def log(msg: Any, prefix: str):
    if prefix.startswith("W:"):
        with open("/tmp/log", "a") as f:
            print(f"{prefix:30s}{msg}", file=f)
