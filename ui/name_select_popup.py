import json

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

from ui.category_edit_popup import CategoryEditPopup
from ui.color_utils import contrast_color
from ui.text_box import TextBox

# Optional transaction details picked from a saved list; there are no defaults, the user adds every one #
NAME_KINDS = {"retailer": "Retailer/Platform", "brand": "Brand/Creator"}
NAME_KIND_PLURALS = {"retailer": "Retailers/Platforms", "brand": "Brands/Creators"}

## SAVED NAME LISTS (KEPT A-Z, MATCHED IGNORING CASE) ##
# Each entry is {"name": ..., "color": [r, g, b, a] or None}; picking a color is optional #
# Transactions store just the name, so a color change shows everywhere at once #

def _sorted(entries):
    return sorted(entries, key=lambda entry: entry["name"].casefold())

def find_entry(entries, name):
    # The saved entry for `name` ignoring case, or None #
    key = name.casefold()
    return next((entry for entry in entries if entry["name"].casefold() == key), None)

def name_color(entries, name):
    # The color picked for `name`, or None if it has none or is no longer in the list #
    entry = find_entry(entries, name) if name else None
    return entry["color"] if entry else None

def matching_entries(entries, query):
    key = query.strip().casefold()
    return _sorted(entry for entry in entries if key in entry["name"].casefold())

def add_entry(entries, name, color=None):
    # Returns the new list and the name to use; one already saved in a different case is reused as it is #
    existing = find_entry(entries, name)
    if existing is not None:
        return entries, existing["name"]
    return _sorted(entries + [{"name": name, "color": color}]), name

def edit_entry(entries, old, new, color):
    # Renaming onto another saved name merges the two, keeping the color just picked #
    others = [entry for entry in entries if entry["name"] != old]
    existing = find_entry(others, new)
    if existing is not None:
        others.remove(existing)
        new = existing["name"]
    return _sorted(others + [{"name": new, "color": color}]), new

## PICK, ADD, RENAME OR REMOVE A RETAILER OR BRAND ##

class NameSelectPopup(Popup):
    def __init__(self, app, kind, on_select=None, on_rename=None, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.kind = kind
        self.label = NAME_KINDS[kind]
        self.plural = NAME_KIND_PLURALS[kind]
        self.on_select = on_select
        self.on_rename = on_rename

        # Without `on_select` it only manages the list (opened from Custom on the main page) instead of picking from it #
        self.picking = on_select is not None

        outer_layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        # At the very top so the keyboard never covers what's being typed or the closest matches under it #
        self.search_input = search_box(f"Search {self.plural.lower()}")
        self.search_input.bind(text=lambda inst, val: self._populate_list())

        self.list_layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10), size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))

        self.clear_btn = None
        if self.picking:
            self.clear_btn = Button(
                text=f"No {self.label}",
                size_hint_y=None,
                height=dp(40),
                color=(1, 1, 1, 1)
            )
            self.clear_btn.bind(on_release=lambda x: self._select(None))

        # At the bottom like New Category, so it sits in the same spot in every list #
        self.new_btn = Button(
            text=f"New {self.label}",
            size_hint_y=None,
            height=dp(40),
            background_normal="",
            background_color=(0.51765, 0.878, 0.737, 1),
            color=(0, 0, 0, 1)
        )
        self.new_btn.bind(on_release=lambda x: self._open_add_popup())

        self._populate_list()

        scroll = ScrollView()
        scroll.add_widget(self.list_layout)
        outer_layout.add_widget(self.search_input)
        outer_layout.add_widget(scroll)
        if self.clear_btn is not None:
            outer_layout.add_widget(self.clear_btn)
        outer_layout.add_widget(self.new_btn)

        self.title = f"Select {self.label}" if self.picking else f"Manage {self.plural}"
        self.title_color = (1, 1, 1, 1)
        self.content = outer_layout
        self.size_hint = (0.8, 0.84)

    @property
    def names(self):
        return self.app.saved_names[self.kind]

    def _populate_list(self):
        self.list_layout.clear_widgets()
        query = self.search_input.text.strip()

        matches = matching_entries(self.names, query)
        for entry in matches:
            name = entry["name"]
            row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(4))

            name_btn = fit_text(Button(text=name, color=(1, 1, 1, 1)))
            show_color(name_btn, entry["color"])
            name_btn.bind(on_release=lambda inst, n=name: self._tap_name(n))

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

        if query and not matches:
            self.list_layout.add_widget(hint_label("No matches"))

    def _tap_name(self, name):
        # There's nothing to pick a name for when managing the list, so tapping it renames it like Edit does #
        if self.picking:
            self._select(name)
        else:
            self._open_edit_popup(name)

    def _select(self, name):
        self.on_select(name)
        self.dismiss()

    def _open_add_popup(self):
        # Same name and color popup as a category; starts with whatever was searched for, #
        # so a search that found nothing is one tap from being added #
        CategoryEditPopup(
            self.app,
            on_save=lambda entry, _: self._add(entry["name"], entry["color"]),
            initial_name=self.search_input.text.strip(),
            label=self.label,
            color_optional=True
        ).open()

    def _add(self, name, color=None):
        names, name = add_entry(self.names, name, color)
        self.app.saved_names[self.kind] = names
        self._save_names()
        if self.picking:
            self._select(name)
        else:
            # Stays open for adding more; clearing the search shows the whole list, the new name included #
            self.search_input.text = ""
            self._populate_list()

    def _delete(self, name):
        # Only removes it from the list; transactions that used it keep it #
        self.app.saved_names[self.kind] = [entry for entry in self.names if entry["name"] != name]
        self._save_names()
        self._populate_list()

    def _open_edit_popup(self, name):
        CategoryEditPopup(
            self.app,
            on_save=lambda entry, _: self._on_edit_save(name, entry["name"], entry["color"]),
            existing_category=find_entry(self.names, name),
            label=self.label,
            color_optional=True
        ).open()

    def _on_edit_save(self, old_name, new_name, color=None):
        names, new_name = edit_entry(self.names, old_name, new_name, color)
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

def search_box(hint_text):
    # Only filters the list; new entries are added with the New button #
    return TextBox(hint_text=hint_text, multiline=False, size_hint_y=None, height=dp(40))

def hint_label(text):
    # Dimmed note in place of the list when there's nothing to show #
    label = Label(
        text=text,
        size_hint_y=None,
        height=dp(40),
        halign="center",
        valign="middle",
        color=(1, 1, 1, 0.6)
    )
    label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
    return label

def show_color(btn, color):
    # Fills the button with a picked color like a category's, or puts back the plain button look #
    if color:
        btn.background_normal = ""
        btn.background_color = color
        btn.color = contrast_color(color)
    else:
        btn.background_normal = "atlas://data/images/defaulttheme/button"
        btn.background_color = (1, 1, 1, 1)
        btn.color = (1, 1, 1, 1)
    return btn

def fit_text(btn):
    # Long names end in "..." instead of running past the button #
    btn.shorten = True
    btn.shorten_from = "right"
    btn.halign = "center"
    btn.valign = "middle"
    btn.bind(size=lambda inst, val: setattr(inst, "text_size", (inst.width - dp(12), inst.height)))
    return btn
