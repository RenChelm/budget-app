from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.metrics import dp

from ui.expanding_popup import ExpandingPopup
from ui.text_box import TextBox

## RENAME A SAVED RETAILER OR BRAND ##

class NameEditPopup(ExpandingPopup):
    def __init__(self, label, name, on_save, **kwargs):
        super().__init__(**kwargs)
        self.on_save_callback = on_save

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        self.name_input = TextBox(
            text=name,
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            hint_text=f"{label} name"
        )
        self.name_input.bind(on_text_validate=lambda inst: self._save())

        save_btn = Button(
            text="Save",
            size_hint_y=None,
            height=dp(44),
            background_normal="",
            background_color=(0.51765, 0.878, 0.737, 1),
            color=(0, 0, 0, 1)
        )
        save_btn.bind(on_release=lambda x: self._save())

        layout.add_widget(self.name_input)
        layout.add_widget(save_btn)

        self.title = f"Edit {label}"
        self.title_color = (1, 1, 1, 1)
        self.content = layout
        self.size_hint_x = 0.85

        # Sits high on the screen so the keyboard never covers the name being typed or Save #
        self.top_hint = 0.88
        self.fit_to(layout)

    def _save(self):
        name = self.name_input.text.strip()
        if not name:
            return

        self.on_save_callback(name)
        self.dismiss()
