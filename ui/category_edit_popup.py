import json

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.metrics import dp

from ui.color_utils import contrast_color
from ui.color_wheel_popup import ColorWheelPopup
from ui.expanding_popup import ExpandingPopup
from ui.text_box import TextBox

PALETTE = [
    (0.9, 0.3, 0.3, 1),   # Red
    (1.0, 0.6, 0.2, 1),   # Orange
    (0.9, 0.8, 0.2, 1),   # Yellow
    (0.3, 0.8, 0.4, 1),   # Green
    (0.3, 0.7, 0.5, 1),   # Teal
    (0.3, 0.6, 0.9, 1),   # Sky Blue
    (0.3, 0.5, 0.8, 1),   # Blue
    (0.6, 0.4, 0.9, 1),   # Purple
    (0.9, 0.4, 0.7, 1),   # Pink
    (0.7, 0.5, 0.3, 1),   # Brown
    (0.6, 0.6, 0.6, 1),   # Gray
    (0.4, 0.6, 0.45, 1),  # Muted Green
]

SWATCH_COLUMNS = 4
SWATCH_HEIGHT = dp(50)
SWATCH_SPACING = dp(4)
MAX_SAVED_ROWS = 2          # Past this, the saved colors scroll so the popup stays on screen

def _normalize(color):
    return tuple(round(c, 2) for c in color [:4])

def _grid_height(count):
    rows = (count + SWATCH_COLUMNS - 1) // SWATCH_COLUMNS
    return SWATCH_HEIGHT * rows + SWATCH_SPACING * max(rows - 1, 0)

## NAME AND COLOR FOR A CATEGORY, OR A RETAILER/PLATFORM OR BRAND/CREATOR (`label`) ##

class CategoryEditPopup(ExpandingPopup):
    def __init__(self, app, on_save, existing_category=None, initial_name="", label="Category", color_optional=False, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.on_save_callback =  on_save
        self.existing_category = existing_category

        # A color picked from the wheel isn't in the palette, so it's kept as is rather than swapped for a default #
        existing_color = existing_category["color"] if existing_category else None
        # Retailers and brands don't need a color, so nothing starts picked for them #
        if existing_color:
            self.selected_color = self._known_color(existing_color) or tuple(existing_color)
        else:
            self.selected_color = None if color_optional else PALETTE[5]

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))

        self.name_input = TextBox(
            text=existing_category["name"] if existing_category else initial_name,
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            hint_text=f"{label} name"
        )
        layout.add_widget(self.name_input)

        layout.add_widget(Label(
            text="Select Color:",
            size_hint_y=None,
            height=dp(24),
            color=(1, 1, 1, 1),
        ))

        self.swatch_buttons = {}
        color_grid = GridLayout(cols=SWATCH_COLUMNS, size_hint_y=None, height=_grid_height(len(PALETTE)), spacing=SWATCH_SPACING)
        for color in PALETTE:
            color_grid.add_widget(self._swatch(color))
        layout.add_widget(color_grid)

        # Colors saved from the wheel, newest first, beneath the defaults; only added to the layout once there's one #
        self.saved_grid = GridLayout(cols=SWATCH_COLUMNS, size_hint_y=None, spacing=SWATCH_SPACING)
        self.saved_scroll = ScrollView(size_hint_y=None, do_scroll_x=False)
        self.saved_scroll.add_widget(self.saved_grid)

        self.custom_color_btn = Button(
            text="Custom Color",
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1)
        )
        self.custom_color_btn.bind(on_release=lambda x: self._open_color_wheel())
        layout.add_widget(self.custom_color_btn)

        save_btn = Button(
            text="Save",
            size_hint_y=None,
            height=dp(44),
            background_normal="",
            background_color=(0.51765, 0.878, 0.737, 1),
            color=(0, 0, 0, 1)
        )
        save_btn.bind(on_release=lambda x: self._save())
        layout.add_widget(save_btn)

        self.form = layout
        self._show_saved_colors()
        self._update_swatch_indicator()

        self.title = f"Edit {label}" if existing_category else f"Add {label}"
        self.title_color = (1, 1, 1, 1)
        self.content = layout
        self.size_hint_x = 0.85
        self.fit_to(layout)

    @property
    def saved_colors(self):
        return getattr(self.app, "saved_colors", [])

    def _known_color(self, color):
        # The palette or saved color matching `color`, or None #
        key = _normalize(color)
        return next((c for c in PALETTE + [tuple(c) for c in self.saved_colors] if _normalize(c) == key), None)

    def _swatch(self, color):
        btn = Button(
            background_normal="",
            background_color=color,
            size_hint_y=None,
            height=SWATCH_HEIGHT,
            font_size=dp(18),
            color=contrast_color(color)
        )
        btn.bind(on_release=lambda inst, c=color: self._select_color(c))
        self.swatch_buttons[color] = btn
        return btn

    def _show_saved_colors(self):
        self.swatch_buttons = {c: b for c, b in self.swatch_buttons.items() if b.parent is not self.saved_grid}
        self.saved_grid.clear_widgets()

        colors = [tuple(c) for c in self.saved_colors]
        for color in colors:
            self.saved_grid.add_widget(self._swatch(color))

        # Empty spots fill out the last row; with fewer swatches than columns the grid would stretch them wide #
        for _ in range(-len(colors) % SWATCH_COLUMNS):
            self.saved_grid.add_widget(Widget(size_hint_y=None, height=SWATCH_HEIGHT))
        self.saved_grid.height = _grid_height(len(colors))
        self.saved_scroll.height = min(self.saved_grid.height, _grid_height(MAX_SAVED_ROWS * SWATCH_COLUMNS))

        # Sits right under the defaults, above Custom Color and Save #
        if colors and self.saved_scroll.parent is None:
            self.form.add_widget(self.saved_scroll, index=2)

    def _open_color_wheel(self):
        ColorWheelPopup(self.selected_color or PALETTE[5], on_save=self._on_color_wheel_save).open()

    def _on_color_wheel_save(self, color):
        # A color that's already a swatch is just picked; a new one is saved for every category to use #
        known = self._known_color(color)
        if known is None:
            self.app.saved_colors.insert(0, list(color))
            with open(self.app.colors_file, "w") as f:
                json.dump(self.app.saved_colors, f)
            self._show_saved_colors()
            known = tuple(color)
        self._select_color(known)

    def _select_color(self, color):
        self.selected_color = color
        self._update_swatch_indicator()

    def _update_swatch_indicator(self):
        sel = _normalize(self.selected_color) if self.selected_color else None
        for color, btn in self.swatch_buttons.items():
            btn.text = "X" if _normalize(color) == sel else ""

    def _save(self):
        name = self.name_input.text.strip()
        if not name:
            return

        color = list(self.selected_color) if self.selected_color else None
        self.on_save_callback({"name": name, "color": color}, self.existing_category)
        self.dismiss()
