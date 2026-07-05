from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.metrics import dp

from ui.color_utils import contrast_color

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

def _normalize(color):
    return tuple(round(c, 2) for c in color [:4])

class CategoryEditPopup(Popup):
    def __init__(self, app, on_save, existing_category=None, initial_name="", **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.on_save_callback =  on_save
        self.existing_category = existing_category

        existing_color = existing_category["color"] if existing_category else None
        matched = next((c for c in PALETTE if _normalize(c) == _normalize(existing_color)), None) if existing_color else None
        self.selected_color = matched if matched else PALETTE[5]

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))

        self.name_input = TextInput(
            text=existing_category["name"] if existing_category else initial_name,
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            hint_text="Category name"
        )
        layout.add_widget(self.name_input)

        layout.add_widget(Label(
            text="Select Color:",
            size_hint_y=None,
            height=dp(24),
            color=(1, 1, 1, 1),
        ))

        rows = (len(PALETTE) + 3) // 4
        color_grid = GridLayout(
            cols=4,
            size_hint_y=None,
            height=dp(50) * rows + dp(4) * (rows - 1),
            spacing=dp(4)
        )
        self.swatch_buttons = {}
        for color in PALETTE:
            btn = Button(
                background_normal="",
                background_color=color,
                size_hint_y=None,
                height=dp(50),
                font_size=dp(18),
                color=contrast_color(color)
            )
            btn.bind(on_release=lambda inst, c=color: self._select_color(c))
            self.swatch_buttons[color] = btn
            color_grid.add_widget(btn)

        layout.add_widget(color_grid)
        self._update_swatch_indicator()

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

        self.title = "Edit Category" if existing_category else "Add Category"
        self.title_color = (1, 1, 1, 1)
        self.content = layout
        self.size_hint = (0.85, 0.50)

    def _select_color(self, color):
        self.selected_color = color
        self._update_swatch_indicator()

    def _update_swatch_indicator(self):
        sel = _normalize(self.selected_color)
        for color, btn in self.swatch_buttons.items():
            btn.text = "X" if _normalize(color) == sel else ""

    def _save(self):
        name = self.name_input.text.strip()
        if not name:
            return
            
        self.on_save_callback({"name": name, "color": list(self.selected_color)}, self.existing_category)
        self.dismiss()