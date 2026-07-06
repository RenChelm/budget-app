import json

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.metrics import dp

from ui.category_select_popup import CategorySelectPopup
from ui.color_utils import contrast_color

class EditTransactionPopup(Popup):
    def __init__(self, app, index, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        entry = self.app.saved_amounts[index]
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        self.app.selected_category = entry.get("category")

        amount_input_box = TextInput(
            text=str(entry["amount"]),
            hint_text="Enter Amount",
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height=dp(40)
        )

        existing_cat = entry.get("category")

        note_input_box = TextInput(
            hint_text="Enter Note (Optional)",
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        note_input_box.text = entry.get("note") or ""

        category_btn = Button(
            text=existing_cat["name"] if isinstance(existing_cat, dict) else "Uncategorized",
            background_normal="",
            background_color=existing_cat["color"] if isinstance(existing_cat, dict) else (0.6, 0.6, 0.6, 1),
            color=contrast_color(existing_cat["color"]),
            size_hint=(1, 0.3)
        )

        category_btn.bind(on_release=lambda inst: self.open_category_window_for_edit(index, category_btn))

        save_btn = Button(text="Save", size_hint=(1, 0.3), color=(1, 1, 1, 1))
        save_btn.bind(
            on_release=lambda inst: self.save_edit(index, amount_input_box.text, note_input_box.text)
        )

        layout.add_widget(amount_input_box)
        layout.add_widget(category_btn)
        layout.add_widget(note_input_box)
        layout.add_widget(save_btn)

        self.title = "Edit Transaction"
        self.title_color = (1, 1, 1, 1)
        self.content = layout
        self.size_hint = (0.8, 0.3)

    def save_edit(self, index, new_amount, new_note):
        try:
            new_amount = float(new_amount)
        except ValueError:
            return

        new_note = new_note.strip()

        self.app.saved_amounts[index]["amount"] = new_amount
        self.app.saved_amounts[index]["category"] = getattr(self.app, "selected_category", self.app.saved_amounts[index]["category"])
        self.app.saved_amounts[index]["note"] = new_note if new_note else None

        with open(self.app.transactions_file, "w") as f:
            json.dump(self.app.saved_amounts, f, default=str)

        self.app.update_display()
        self.dismiss()  

    def open_category_window_for_edit(self, index, category_btn):
        CategorySelectPopup(self.app, category_btn).open()