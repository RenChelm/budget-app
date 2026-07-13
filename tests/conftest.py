import os

# Must be set before kivy is imported anywhere: prevents Kivy from trying to
# parse pytest's own command-line args as its own (-d, -a, etc.).
os.environ.setdefault("KIVY_NO_ARGS", "1")
os.environ.setdefault("KIVY_NO_CONSOLELOG", "1")

import pytest

from kivy.config import Config
Config.set("graphics", "width", "360")
Config.set("graphics", "height", "800")

from kivy.app import App
from kivy.base import EventLoop


@pytest.fixture(scope="session")
def kivy_window():
    """Widgets that draw (Label, Button, canvas instructions, ...) need a
    real GL context to exist before they can be instantiated. Create it once
    for the whole test session and hand back the Window."""
    EventLoop.ensure_window()
    return EventLoop.window


@pytest.fixture(autouse=True)
def _clear_running_app():
    yield
    App._running_app = None
