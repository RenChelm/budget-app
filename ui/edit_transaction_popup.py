import json

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.metrics import dp

from datetime import datetime

from ui.category_select_popup import CategorySelectPopup
from ui.date_input import DateInput
from ui.number_input import NumberInput
from ui.color_utils import contrast_color

class EditTransactionPopup(Popup):
    def __init__(self, app, index, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        entry = self.app.saved_amounts[index]
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        self.app.selected_category = entry.get("category")

        self.amount_input_box = amount_input_box = NumberInput(
            text=str(entry["amount"]),
            hint_text="Enter Amount",
            size_hint_y=None,
            height=dp(40)
        )

        self.date_input_box = DateInput(
            day=entry["timestamp"].date(),
            hint_text="Enter Date",
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
            color=contrast_color(existing_cat["color"]) if isinstance(existing_cat, dict) else (1, 1, 1, 1),
            size_hint=(1, None),
            height=dp(44)
        )

        category_btn.bind(on_release=lambda inst: self.open_category_window_for_edit(index, category_btn))

        save_btn = Button(text="Save", color=(1, 1, 1, 1))
        save_btn.bind(
            on_release=lambda inst: self.save_edit(index, amount_input_box.text, note_input_box.text)
        )

        delete_btn = Button(
            text="Delete",
            background_normal="",
            background_color=(0.8, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        delete_btn.bind(on_release=lambda inst: self.delete(index))

        btn_row = BoxLayout(size_hint=(1, None), height=dp(44), spacing=dp(10))
        btn_row.add_widget(save_btn)
        btn_row.add_widget(delete_btn)

        layout.add_widget(amount_input_box)
        layout.add_widget(self.date_input_box)
        layout.add_widget(category_btn)
        layout.add_widget(note_input_box)
        layout.add_widget(btn_row)

        self.title = "Edit Transaction"
        self.title_color = (1, 1, 1, 1)
        self.content = layout
        self.size_hint = (0.8, None)
        self.height = dp(330)

    def save_edit(self, index, new_amount, new_note):
        try:
            new_amount = float(new_amount)
        except ValueError:
            return

        try:
            new_day = self.date_input_box.parse_day()
        except ValueError as error:
            self.app.show_error(str(error))
            return

        new_note = new_note.strip()

        # A new date keeps the original time of day; blank leaves the date unchanged #
        if new_day:
            self.app.saved_amounts[index]["timestamp"] = datetime.combine(new_day, self.app.saved_amounts[index]["timestamp"].time())
        self.app.saved_amounts[index]["amount"] = new_amount
        self.app.saved_amounts[index]["category"] = getattr(self.app, "selected_category", self.app.saved_amounts[index]["category"])
        self.app.saved_amounts[index]["note"] = new_note if new_note else None

        with open(self.app.transactions_file, "w") as f:
            json.dump(self.app.saved_amounts, f, default=str)

        self.app.update_display()
        self.dismiss()  

    def delete(self, index):
        self.app.delete_entry(index)
        self.dismiss()

    def open_category_window_for_edit(self, index, category_btn):
        CategorySelectPopup(self.app, category_btn).open()