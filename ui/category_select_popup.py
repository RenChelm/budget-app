import json

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

from ui.category_edit_popup import CategoryEditPopup

DEFAULT_CATEGORIES = [
    {"name": "Food",    "color": [1, 0.6, 0.2, 1]},
    {"name": "Bills",   "color": [0.9, 0.3, 0.3, 1]},
    {"name": "Rent",    "color": [0.6, 0.4, 0.9, 1]},
    {"name": "Savings", "color": [0.3, 0.8, 0.4, 1]},
    {"name": "Other",   "color": [0.6, 0.6, 0.6, 1]},
]

class CategorySelectPopup(Popup):
    def __init__(self, app, category_btn=None, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.category_btn = category_btn

        outer_layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        self.list_layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))

        self._populate_list()

        new_btn = Button(
            text="New Category",
            size_hint_y=None,
            height=dp(40),
            background_normal="",
            background_color=(0.51765, 0.878, 0.737, 1),
            color=(1, 1, 1, 1),
            outline_color=(0, 0, 0, 1),
            outline_width=1
        )
        new_btn.bind(on_release=lambda x: self._open_add_popup())

        scroll = ScrollView()
        scroll.add_widget(self.list_layout)
        outer_layout.add_widget(scroll)
        outer_layout.add_widget(new_btn)

        self.title = "Manage Categories" if category_btn is None else "Select Category"
        self.title_color = (1, 1, 1, 1)
        self.content = outer_layout
        self.size_hint = (0.8, 0.84)

    def _populate_list(self):
        self.list_layout.clear_widgets()

        for cat in self.app.saved_categories:
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))

            cat_btn = Button(
                text=cat["name"],
                background_normal="",
                background_color=cat["color"],
                color=(1, 1, 1, 1),
                outline_color=(0, 0, 0, 1),
                outline_width=1
            )
            cat_btn.bind(on_release=lambda inst, c=cat: self.app.select_category(c, self.category_btn, self))

            delete_btn = Button(
                text="X",
                background_normal="",
                background_color=(0.8, 0.3, 0.3, 1),
                color=(1, 1, 1, 1),
                outline_color=(0, 0, 0, 1),
                outline_width=1,
                size_hint_x=None,
                width=dp(36)
            )
            delete_btn.bind(on_release=lambda inst, c=cat: self._delete_category(c))

            edit_btn = Button(
                text="Edit",
                background_normal="",
                background_color=(0.3, 0.5, 0.8, 1),
                color=(1, 1, 1, 1),
                outline_color=(0, 0, 0, 1),
                outline_width=1,
                size_hint_x=None,
                width=dp(50)
            )
            edit_btn.bind(on_release=lambda inst, c=cat: self._open_edit_popup(c))

            row.add_widget(cat_btn)
            row.add_widget(delete_btn)
            row.add_widget(edit_btn)
            self.list_layout.add_widget(row)

        for cat in DEFAULT_CATEGORIES:
            btn = Button(
                text=cat["name"],
                background_normal="",
                background_color=cat["color"],
                color=(1, 1, 1, 1),
                outline_color=(0, 0, 0, 1),
                outline_width=1,
                size_hint_y=None,
                height=dp(40)
            )
            btn.bind(on_release=lambda inst, c=cat: self.app.select_category(c, self.category_btn, self))
            self.list_layout.add_widget(btn)

    def _open_add_popup(self):
        CategoryEditPopup(self.app, on_save=self._on_add_save).open()

    def _on_add_save(self, new_category, _):
        self.app.saved_categories.insert(0, new_category)
        self.app.select_category(new_category, self.category_btn, self)
        with open(self.app.categories_file, "w") as f:
            json.dump(self.app.saved_categories, f, default=str)

    def _delete_category(self, cat):
        self.app.saved_categories = [c for c in self.app.saved_categories if c["name"] != cat["name"]]
        with open(self.app.categories_file, "w") as f:
            json.dump(self.app.saved_categories, f, default=str)
        self._populate_list()

    def _open_edit_popup(self, cat):
        CategoryEditPopup(self.app, on_save=self._on_edit_save, existing_category=cat).open()

    def _on_edit_save(self, new_category, old_category):
        idx = next((i for i, c in enumerate(self.app.saved_categories) if c["name"] == old_category["name"]), None)
        if idx is not None:
            self.app.saved_categories[idx] = new_category

        for entry in self.app.saved_amounts:
            if entry.get("category") and entry["category"]["name"] == old_category["name"]:
                entry["category"] = new_category

        with open(self.app.categories_file, "w") as f:
            json.dump(self.app.saved_categories, f, default=str)

        with open(self.app.transactions_file, "w") as f:
            json.dump(self.app.saved_amounts, f, default=str)

        self._populate_list()
        self.app.update_display()
