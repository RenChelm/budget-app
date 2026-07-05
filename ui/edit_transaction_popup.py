import json

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.metrics import dp

from ui.category_select_popup import CategorySelectPopup

class EditTransactionPopup(Popup):
    def __init__(self, app, index, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        entry = self.app.saved_amounts[index]
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        amount_input = TextInput(
            text=str(entry["amount"]),
            multiline=False,
            input_filter="float",
            size_hint_y=None,
            height=dp(40)
        )

        existing_cat = entry.get("category")
        category_btn = Button(
            text=existing_cat["name"] if isinstance(existing_cat, dict) else "Uncategorized",
            background_normal="",
            background_color=existing_cat["color"] if isinstance(existing_cat, dict) else (0.6, 0.6, 0.6, 1),
            color=(1, 1, 1, 1),
            size_hint=(1, 0.3)
        )
        category_btn.bind(on_release=lambda inst: self.open_category_window_for_edit(index, category_btn))

        save_btn = Button(text="Save", size_hint=(1, 0.3), color=(1, 1, 1, 1))
        save_btn.bind(
            on_release=lambda inst: self.save_edit(index, amount_input.text)
        )

        layout.add_widget(amount_input)
        layout.add_widget(category_btn)
        layout.add_widget(save_btn)

        self.title = "Edit Transaction"
        self.title_color = (1, 1, 1, 1)
        self.content = layout
        self.size_hint = (0.8, 0.3)

    def save_edit(self, index, new_amount):
        try:
            new_amount = float(new_amount)
        except ValueError:
            return

        self.app.saved_amounts[index]["amount"] = new_amount
        self.app.saved_amounts[index]["category"] = getattr(self.app, "selected_category", self.app.saved_amounts[index]["category"])

        with open(self.app.transactions_file, "w") as f:
            json.dump(self.app.saved_amounts, f, default=str)

        self.app.update_display()
        self.dismiss()  

    def open_category_window_for_edit(self, index, category_btn):
        CategorySelectPopup(self.app, category_btn).open()