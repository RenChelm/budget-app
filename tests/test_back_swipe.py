import sys
import types

from kivy.core.window import Window

import main
import ui.back_swipe as back_swipe
from ui.back_swipe import filter_back_swipes


def test_does_nothing_off_android(monkeypatch):
    monkeypatch.setattr(back_swipe, "platform", "linux")
    monkeypatch.setitem(sys.modules, "jnius", None)  # Importing it would raise #

    filter_back_swipes()


def test_installs_the_java_filter_on_the_apps_activity(monkeypatch):
    installed = []
    activity = object()
    java_class = types.SimpleNamespace(install=installed.append)
    looked_up = []

    def autoclass(name):
        looked_up.append(name)
        return java_class

    monkeypatch.setitem(sys.modules, "jnius", types.SimpleNamespace(autoclass=autoclass))
    monkeypatch.setitem(sys.modules, "android", types.SimpleNamespace(mActivity=activity))
    monkeypatch.setattr(back_swipe, "platform", "android")

    filter_back_swipes()

    assert looked_up == ["org.ren.budgetapp.BackSwipeFilter"]
    assert installed == [activity]


def test_app_start_filters_back_swipes(tmp_path, kivy_window, monkeypatch):
    calls = []
    monkeypatch.setattr(main, "filter_back_swipes", lambda: calls.append(True))

    app = main.BudgetApp()
    app._user_data_dir = str(tmp_path)
    app.build()
    app.on_start()
    Window.unbind(on_keyboard=app.on_back_key)

    assert calls == [True]
