import json

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.metrics import dp

from datetime import datetime

from ui.category_select_popup import CategorySelectPopup

class AddTransactionPopup(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        self.input_box = TextInput(
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )

        self.category_btn = Button(text="Select Category", size_hint=(1, 0.3))
        self.category_btn.bind(on_release=lambda x: self.open_category_window())

        save_btn = Button(text="Save", size_hint=(1, 0.3))
        save_btn.bind(on_release=lambda x: self.save_text())

        layout.add_widget(self.input_box)
        layout.add_widget(self.category_btn)
        layout.add_widget(save_btn)

        self.title="Add Transaction"
        self.content=layout
        self.size_hint=(0.8, 0.3)

    def open_category_window(self):
        CategorySelectPopup(self.app, self.category_btn).open()

    def save_text(self):
        value = self.input_box.text.strip()

        try:
            amount = float(value)
        except ValueError:
            self.app.show_error("Please enter a valid number.")
            return

        entry = {
            "amount": amount,
            "timestamp": datetime.now(),
            "category": getattr(self.app, "selected_category", None)
        }

        self.app.saved_amounts.append(entry)

        with open(self.app.transactions_file, "w") as f:
            json.dump(self.app.saved_amounts, f, default=str)

        self.app.update_display()
        self.dismiss()