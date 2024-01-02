import subprocess
import sys
from pathlib import Path

SCENES = [
    "ExecuteWorkflow",
    "CallActivity",
    "ExecuteUpdate",
]


def create_animation(scene):
    scenes_dir = Path(__file__).parent
    scene_file = scenes_dir / f"{scene}.py"
    assert scene_file.exists(), scene_file
    subprocess.run(["manim", "-qh", scene_file, scene], cwd=scenes_dir)


def create_animations(scenes: list[str]):
    for scene in scenes:
        create_animation(scene)


if __name__ == "__main__":
    scenes = sys.argv[1:] or SCENES
    create_animations(scenes)
