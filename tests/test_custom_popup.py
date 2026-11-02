import time

import pytest

from kivy.clock import Clock
from kivy.uix.modalview import ModalView

import main
import ui.custom_popup as custom_popup
from ui.custom_popup import CustomPopup
from ui.rounded_button import RoundedButton


class FakeApp:
    def __init__(self):
        self.saved_categories = []
        self.saved_names = {"retailer": [], "brand": []}


@pytest.fixture(autouse=True)
def close_popups(kivy_window):
    yield
    for widget in list(kivy_window.children):
        if isinstance(widget, ModalView):
            widget.dismiss(animation=False)


@pytest.fixture
def opened_menus(monkeypatch):
    # Records which list would open (and how) instead of opening it #
    opened = []

    class FakeMenu:
        def __init__(self, *args, **kwargs):
            self.args, self.kwargs = args, kwargs

        def open(self):
            opened.append(self)

    class FakeCategories(FakeMenu):
        pass

    class FakeNames(FakeMenu):
        pass

    monkeypatch.setattr(custom_popup, "CategorySelectPopup", FakeCategories)
    monkeypatch.setattr(custom_popup, "NameSelectPopup", FakeNames)
    return opened


def opened_custom_popup(app):
    popup = CustomPopup(app)
    popup.open(animation=False)
    for _ in range(5):
        Clock.tick()
    return popup


def test_lists_categories_retailers_and_brands_in_that_order(kivy_window):
    popup = CustomPopup(FakeApp())

    buttons = [w for w in reversed(popup.content.children)]
    assert [b.text for b in buttons] == ["Categories", "Retailers", "Brands"]
    assert all(isinstance(b, RoundedButton) for b in buttons)
    assert popup.title == "Custom"


@pytest.mark.parametrize("key, menu, args", [
    ("categories", "FakeCategories", ()),
    ("retailers", "FakeNames", ("retailer",)),
    ("brands", "FakeNames", ("brand",)),
])
def test_each_choice_opens_its_list_for_managing(kivy_window, opened_menus, key, menu, args):
    app = FakeApp()
    popup = CustomPopup(app)

    popup.buttons[key].dispatch("on_release")

    assert len(opened_menus) == 1
    assert type(opened_menus[0]).__name__ == menu
    assert opened_menus[0].args == (app, *args)
    assert opened_menus[0].kwargs == {}     # No category button or on_select, so it manages instead of picks #


def test_choosing_closes_it_so_closing_the_list_goes_back_to_the_main_page(kivy_window, opened_menus):
    popup = opened_custom_popup(FakeApp())

    assert popup._is_open

    popup.buttons["retailers"].dispatch("on_release")
    end = time.monotonic() + 0.5     # Lets it finish fading out #
    while time.monotonic() < end:
        Clock.tick()
        time.sleep(0.01)

    assert not popup._is_open
    assert popup not in kivy_window.children


def test_fits_its_three_buttons(kivy_window):
    popup = opened_custom_popup(FakeApp())

    assert popup.height < kivy_window.height / 2
    for btn in popup.buttons.values():
        assert popup.y < btn.y and btn.top < popup.top


def test_main_page_custom_button_opens_it(tmp_path, kivy_window, monkeypatch):
    opened = []
    monkeypatch.setattr(main, "CustomPopup", lambda app: type("Stub", (), {"open": lambda self: opened.append(app)})())
    app = main.BudgetApp()
    app._user_data_dir = str(tmp_path)
    root = app.build()

    texts = [getattr(w, "text", None) for w in root.walk()]
    assert "Custom" in texts and "Categories" not in texts

    next(w for w in root.walk() if getattr(w, "text", None) == "Custom").dispatch("on_release")

    assert opened == [app]
