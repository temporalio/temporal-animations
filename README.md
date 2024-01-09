A toolkit for creating animations explaining Temporal.

- [`schema/`](schema/) defines a schema describing actor state changes and messages passing between actors.

- [`manim_renderer/`](manim_renderer/) uses [manim](https://github.com/ManimCommunity/manim) to render JSONL data conforming to the schema as an animation.

- [`tempyral/`](tempyral/) is a simulation of Temporal and Nexus that outputs the JSONL format.

## Example usage:

```
python scenes/CallActivity.py | manim render --quality h manim_renderer/scene.py TemporalScene
```

[Example output](https://reimagined-chainsaw-qkmjre7.pages.github.io/).

## Installation

This project uses typing features requiring Python >= 3.12. Use
[pyenv](https://github.com/pyenv/pyenv) to install the required Python
interpreter version, and use [poetry](https://python-poetry.org/docs/) to manage
the Python virtualenv:

```
# install poetry
brew install pyenv
pyenv install 3.12
pyenv shell 3.12
poetry install
poetry shell
```

To use the command-line utilities in [`bin/`](bin/), install [fzf](https://github.com/junegunn/fzf).
