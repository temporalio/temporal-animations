worker-scene:
	pkill 'QuickTime Player' || true
	python -m manim -p -qm scenes/worker/worker_scene.py WorkerScene
