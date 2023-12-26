import os
from typing import Any


def log(msg: Any, prefix: str):
    if True or os.getenv("TEMPYRAL_DEBUG"):
        with open("/tmp/log", "a") as f:
            print(f"{prefix:30s}{msg}", file=f)
