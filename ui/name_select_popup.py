import json

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

from ui.name_edit_popup import NameEditPopup
from ui.text_box import TextBox

# Optional transaction details picked from a saved list; there are no defaults, the user adds every one #
NAME_KINDS = {"retailer": "Retailer", "brand": "Brand"}

## SAVED NAME LISTS (KEPT A-Z, MATCHED IGNORING CASE) ##

def _sorted(names):
    return sorted(names, key=str.casefold)

def find_name(names, name):
    # The saved spelling of `name` ignoring case, or None #
    key = name.casefold()
    return next((saved for saved in names if saved.casefold() == key), None)

def matching_names(names, query):
    key = query.strip().casefold()
    return _sorted(name for name in names if key in name.casefold())

def add_name(names, name):
    # Returns the new list and the name to use; one already saved in a different case is reused instead #
    existing = find_name(names, name)
    if existing is not None:
        return names, existing
    return _sorted(names + [name]), name

def rename_name(names, old, new):
    # Renaming onto another saved name merges the two #
    others = [name for name in names if name != old]
    existing = find_name(others, new)
    if existing is not None:
        return others, existing
    return _sorted(others + [new]), new

## PICK, ADD, RENAME OR REMOVE A RETAILER OR BRAND ##

class NameSelectPopup(Popup):
    def __init__(self, app, kind, on_select, on_rename=None, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.kind = kind
        self.label = NAME_KINDS[kind]
        self.on_select = on_select
        self.on_rename = on_rename

        outer_layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        # At the very top so the keyboard never covers what's being typed or the closest matches under it #
        self.search_input = TextBox(
            hint_text=f"Search or add {self.label.lower()}",
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        self.search_input.bind(text=lambda inst, val: self._populate_list())
        self.search_input.bind(on_text_validate=lambda inst: self._submit())

        self.list_layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))

        self.clear_btn = Button(
            text=f"No {self.label}",
            size_hint_y=None,
            height=dp(40),
            color=(1, 1, 1, 1)
        )
        self.clear_btn.bind(on_release=lambda x: self._select(None))

        self._populate_list()

        scroll = ScrollView()
        scroll.add_widget(self.list_layout)
        outer_layout.add_widget(self.search_input)
        outer_layout.add_widget(scroll)
        outer_layout.add_widget(self.clear_btn)

        self.title = f"Select {self.label}"
        self.title_color = (1, 1, 1, 1)
        self.content = outer_layout
        self.size_hint = (0.8, 0.84)

    @property
    def names(self):
        return self.app.saved_names[self.kind]

    def _populate_list(self):
        self.list_layout.clear_widgets()
        query = self.search_input.text.strip()

        # A typed name that isn't saved yet is added straight from the search, first in the list so it's in view #
        self.add_btn = None
        if query and find_name(self.names, query) is None:
            self.add_btn = fit_text(Button(
                text=f'+ Add "{query}"',
                size_hint_y=None,
                height=dp(40),
                background_normal="",
                background_color=(0.51765, 0.878, 0.737, 1),
                color=(0, 0, 0, 1)
            ))
            self.add_btn.bind(on_release=lambda inst: self._add(query))
            self.list_layout.add_widget(self.add_btn)

        for name in matching_names(self.names, query):
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))

            name_btn = fit_text(Button(text=name, color=(1, 1, 1, 1)))
            name_btn.bind(on_release=lambda inst, n=name: self._select(n))

            delete_btn = Button(
                text="X",
                background_normal="",
                background_color=(0.8, 0.3, 0.3, 1),
                color=(1, 1, 1, 1),
                size_hint_x=None,
                width=dp(36)
            )
            delete_btn.bind(on_release=lambda inst, n=name: self._delete(n))

            edit_btn = Button(
                text="Edit",
                background_normal="",
                background_color=(0.3, 0.5, 0.8, 1),
                color=(1, 1, 1, 1),
                size_hint_x=None,
                width=dp(50)
            )
            edit_btn.bind(on_release=lambda inst, n=name: self._open_edit_popup(n))

            row.add_widget(name_btn)
            row.add_widget(delete_btn)
            row.add_widget(edit_btn)
            self.list_layout.add_widget(row)

        if not self.names and not query:
            empty_label = Label(
                text=f"No {self.label.lower()}s yet. Type one above to add it.",
                size_hint_y=None,
                height=dp(40),
                halign="center",
                valign="middle",
                color=(1, 1, 1, 0.6)
            )
            empty_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
            self.list_layout.add_widget(empty_label)

    def _submit(self):
        # The keyboard's Enter picks the typed name, adding it if it's new #
        query = self.search_input.text.strip()
        if not query:
            return
        existing = find_name(self.names, query)
        if existing is not None:
            self._select(existing)
        else:
            self._add(query)

    def _select(self, name):
        self.on_select(name)
        self.dismiss()

    def _add(self, name):
        names, name = add_name(self.names, name)
        self.app.saved_names[self.kind] = names
        self._save_names()
        self._select(name)

    def _delete(self, name):
        # Only removes it from the list; transactions that used it keep it #
        self.app.saved_names[self.kind] = [n for n in self.names if n != name]
        self._save_names()
        self._populate_list()

    def _open_edit_popup(self, name):
        NameEditPopup(self.label, name, on_save=lambda new_name: self._on_edit_save(name, new_name)).open()

    def _on_edit_save(self, old_name, new_name):
        names, new_name = rename_name(self.names, old_name, new_name)
        self.app.saved_names[self.kind] = names

        for entry in self.app.saved_amounts:
            if entry.get(self.kind) == old_name:
                entry[self.kind] = new_name

        self._save_names()
        with open(self.app.transactions_file, "w") as f:
            json.dump(self.app.saved_amounts, f, default=str)

        if self.on_rename is not None:
            self.on_rename(old_name, new_name)
        self._populate_list()
        self.app.update_display()

    def _save_names(self):
        with open(self.app.names_files[self.kind], "w") as f:
            json.dump(self.names, f)

def fit_text(btn):
    # Long names end in "..." instead of running past the button #
    btn.shorten = True
    btn.shorten_from = "right"
    btn.halign = "center"
    btn.valign = "middle"
    btn.bind(size=lambda inst, val: setattr(inst, "text_size", (inst.width - dp(12), inst.height)))
    return btn
