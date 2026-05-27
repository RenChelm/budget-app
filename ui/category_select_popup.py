import json

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

class CategorySelectPopup(Popup):
    def __init__(self, app, category_btn, **kwargs):
        super().__init__(**kwargs)
        self.app = app 
        self.category_btn = category_btn

        outer_layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))

        categories = self.app.saved_categories + [
            {"name": "Food",    "color": (1, 0.6, 0.2, 1)},
            {"name": "Bills",   "color": (0.9, 0.3, 0.3, 1)},
            {"name": "Rent",    "color": (0.6, 0.4, 0.9, 1)},
            {"name": "Savings", "color": (0.3, 0.8, 0.4, 1)},
            {"name": "Other",   "color": (0.6, 0.6, 0.6, 1)},
]

        popup = self

        for cat in categories:
            btn = Button(text=cat["name"], background_normal="", background_color=cat["color"], size_hint_y=None, height=dp(40))
            btn.bind(on_release=lambda instance, c=cat: self.app.select_category(c, self.category_btn, popup))
            layout.add_widget(btn)

        self.input_box = TextInput(
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )

        add_btn = Button(text="Add", size_hint_y=None, height=dp(40))
        add_btn.bind(on_release=lambda x: self.save_text())

        scroll = ScrollView()

        scroll.add_widget(layout)
        outer_layout.add_widget(scroll)
        outer_layout.add_widget(self.input_box)
        outer_layout.add_widget(add_btn)

        self.title="Select Category"
        self.content=outer_layout
        self.size_hint=(0.8, 0.84)

    def save_text(self):
        value = self.input_box.text.strip()

        if not value:
            return

        new_category = {"name": value, "color": (0.4, 0.7, 1, 1)}
        self.app.saved_categories.insert(0, new_category)
        self.app.select_category(new_category, self.category_btn, self)

        with open(self.app.categories_file, "w") as f:
            json.dump(self.app.saved_categories, f, default=str)
