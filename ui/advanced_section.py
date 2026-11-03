from kivy.animation import Animation
from kivy.graphics import Color, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.stencilview import StencilView
from kivy.metrics import dp

from ui.name_select_popup import NAME_KINDS, NameSelectPopup, fit_text, name_color, show_color

ROW_HEIGHT = dp(44)
ROW_SPACING = dp(10)
SAVE_GAP = dp(8)          # Extra room under the section so Advanced and the Save below it are hard to mix up
OPEN_DURATION = 0.15

## "ADVANCED" BUTTON (CHEVRON POINTS DOWN WHEN CLOSED, UP WHEN OPEN) ##

class AdvancedToggle(Button):
    def __init__(self, **kwargs):
        super().__init__(
            text="Advanced",
            background_normal="",
            background_color=(1, 1, 1, 0.08),
            color=(1, 1, 1, 1),
            padding=[0, 0, dp(22), 0],      # Room for the chevron right of the text #
            **kwargs
        )
        self.expanded = False

        with self.canvas.after:
            Color(1, 1, 1, 1)
            self.chevron = Line(width=dp(1.5), cap="round", joint="round")

        self.bind(pos=self.update_icon, size=self.update_icon, texture_size=self.update_icon)

    def update_icon(self, *args):
        x, cy = self.center_x + self.texture_size[0] / 2 - dp(11), self.center_y
        half = dp(5)
        tip = half / 2 if self.expanded else -half / 2

        self.chevron.points = [x - half, cy - tip, x, cy + tip, x + half, cy - tip]

## CLIPS THE ROWS WHILE THEY SLIDE OPEN ##

class Reveal(StencilView):
    def __init__(self, inner, **kwargs):
        super().__init__(**kwargs)
        self.inner = inner
        self.add_widget(inner)
        self.bind(pos=self._place, size=self._place)

    def _place(self, *args):
        self.inner.x, self.inner.width = self.x, self.width
        self.inner.top = self.top

    def on_touch_down(self, touch):
        # Only the part that's showing takes touches, so the hidden rows can't be tapped #
        return self.collide_point(*touch.pos) and super().on_touch_down(touch)

## ADVANCED SECTION (OPTIONAL RETAILER AND BRAND) ##

class AdvancedSection(BoxLayout):
    def __init__(self, app, retailer=None, brand=None, **kwargs):
        super().__init__(orientation="vertical", size_hint_y=None, padding=[0, 0, 0, SAVE_GAP], **kwargs)
        self.app = app
        self.choices = {"retailer": retailer, "brand": brand}
        self.expanded = False

        self.toggle_btn = AdvancedToggle(size_hint_y=None, height=ROW_HEIGHT)
        self.toggle_btn.bind(on_release=lambda inst: self.set_expanded(not self.expanded))

        # The top padding is the gap under the Advanced button, so a closed section takes no extra room #
        fields = BoxLayout(orientation="vertical", size_hint_y=None, spacing=ROW_SPACING, padding=[0, ROW_SPACING, 0, 0])
        self.choice_btns = {}
        for kind in NAME_KINDS:
            btn = fit_text(Button(size_hint_y=None, height=ROW_HEIGHT, color=(1, 1, 1, 1)))
            btn.bind(on_release=lambda inst, k=kind: self.open_picker(k))
            self.choice_btns[kind] = btn
            fields.add_widget(btn)
            self._show_choice(kind)
        fields.height = len(NAME_KINDS) * (ROW_HEIGHT + ROW_SPACING)

        self.open_height = fields.height
        self.reveal = Reveal(fields, size_hint_y=None, height=0)

        self.add_widget(self.toggle_btn)
        self.add_widget(self.reveal)
        self.bind(minimum_height=self.setter("height"))

        # A transaction that already has a retailer or brand opens with them showing #
        if retailer or brand:
            self.set_expanded(True, animate=False)

    def set_expanded(self, expanded, animate=True):
        self.expanded = expanded
        self.toggle_btn.expanded = expanded
        self.toggle_btn.update_icon()

        height = self.open_height if expanded else 0
        Animation.cancel_all(self.reveal)
        if animate:
            Animation(height=height, d=OPEN_DURATION, t="out_quad").start(self.reveal)
        else:
            self.reveal.height = height

    def open_picker(self, kind):
        picker = NameSelectPopup(
            self.app, kind,
            on_select=lambda name: self.set_choice(kind, name),
            on_rename=lambda old, new: self._on_rename(kind, old, new)
        )
        # The picked name's color may have been changed or removed in the list #
        picker.bind(on_dismiss=lambda inst: self._show_choice(kind))
        picker.open()

    def set_choice(self, kind, name):
        self.choices[kind] = name
        self._show_choice(kind)

    def _on_rename(self, kind, old, new):
        # Renaming the picked name in the list keeps it picked, so saving doesn't write the old name back #
        if self.choices[kind] == old:
            self.set_choice(kind, new)

    def _show_choice(self, kind):
        label, name = NAME_KINDS[kind], self.choices[kind]
        self.choice_btns[kind].text = f"{label}: {name}" if name else f"Select {label}"

        # Takes the name's color like the category button does #
        saved = getattr(self.app, "saved_names", {}).get(kind, [])
        show_color(self.choice_btns[kind], name_color(saved, name))
