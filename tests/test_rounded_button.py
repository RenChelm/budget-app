import pytest

from kivy.graphics import RoundedRectangle

from ui.entry_row import BORDER_RADIUS
from ui.rounded_button import PRESSED_SHADE, RoundedButton

MINT = (0.51765, 0.878, 0.737, 1)


def test_corners_are_rounded_as_much_as_the_entry_rows(kivy_window):
    button = RoundedButton(fill_color=MINT)

    assert [tuple(corner) for corner in button.bg_rect.radius] == [(BORDER_RADIUS, BORDER_RADIUS)] * 4


def test_buttons_own_square_background_is_hidden(kivy_window):
    button = RoundedButton(fill_color=MINT)

    assert tuple(button.background_color) == (0, 0, 0, 0)
    assert button.background_normal == "" and button.background_down == ""


def test_rounded_background_follows_the_button(kivy_window):
    button = RoundedButton(fill_color=MINT)

    button.pos = (12, 30)
    button.size = (90, 91)

    assert tuple(button.bg_rect.pos) == (12, 30)
    assert tuple(button.bg_rect.size) == (90, 91)


def test_fills_with_its_color_and_darkens_while_pressed(kivy_window):
    button = RoundedButton(fill_color=MINT)
    assert tuple(button.fill_instruction.rgba) == pytest.approx(MINT)

    button.state = "down"
    r, g, b, a = MINT
    assert tuple(button.fill_instruction.rgba) == pytest.approx((r * PRESSED_SHADE, g * PRESSED_SHADE, b * PRESSED_SHADE, a))

    button.state = "normal"
    assert tuple(button.fill_instruction.rgba) == pytest.approx(MINT)


def test_main_pages_four_buttons_are_rounded(tmp_path, kivy_window):
    import main

    app = main.BudgetApp()
    app._user_data_dir = str(tmp_path)
    root = app.build()

    labels = {"Spending\nHistory", "Budget", "Add", "Custom"}
    buttons = [w for w in root.walk() if getattr(w, "text", None) in labels]
    assert len(buttons) == 4
    assert all(isinstance(button, RoundedButton) for button in buttons)
    assert all(tuple(button.fill_color) == pytest.approx(MINT) for button in buttons)
    assert all(any(isinstance(i, RoundedRectangle) for i in button.canvas.before.children) for button in buttons)
