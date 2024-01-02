import subprocess
from pathlib import Path

SCENES = [
    "ExecuteWorkflow",
    "ExecuteUpdate",
    "CallActivity",
]


def create_animation(scene):
    scenes_dir = Path(__file__).parent
    scene_file = scenes_dir / f"{scene}.py"
    assert scene_file.exists(), scene_file
    subprocess.run(["manim", "-qh", scene_file, scene], cwd=scenes_dir)


def create_animations():
    for scene in SCENES:
        create_animation(scene)


if __name__ == "__main__":
    create_animations()
