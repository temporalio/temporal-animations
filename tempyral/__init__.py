import os


def log(msg: str, prefix: str):
    if os.getenv("TEMPYRAL_DEBUG"):
        with open("/tmp/log", "a") as f:
            print(f"{prefix:30s}{msg}", file=f)
