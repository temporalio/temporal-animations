import subprocess
import sys
from pathlib import Path
from threading import Thread

SCENES = [
    "ExecuteWorkflow",
    "CallActivity",
    "ExecuteUpdate",
]


def create_animation(scene, output_to_file=False):
    scenes_dir = Path(__file__).parent
    scene_file = scenes_dir / f"{scene}.py"
    assert scene_file.exists(), scene_file
    cmd = ["manim", "-qh", scene_file, scene]
    if output_to_file:
        with open(f"/tmp/{scene}.out", "w") as out_file, open(
            f"/tmp/{scene}.err", "w"
        ) as err_file:
            subprocess.run(cmd, cwd=scenes_dir, stdout=out_file, stderr=err_file)
    else:
        subprocess.run(cmd, cwd=scenes_dir)


def create_animations_parallel(scenes: list[str]):
    threads = [Thread(target=create_animation, args=[s, True]) for s in scenes]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    scenes = sys.argv[1:] or SCENES
    if False:
        create_animations_parallel(scenes)
    else:
        for scene in scenes:
            create_animation(scene, output_to_file=False)
