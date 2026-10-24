from kivy.app import App
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.metrics import dp

from ui.color_utils import contrast_color

BORDER_WIDTH = dp(1.1)
BORDER_RADIUS = dp(10)

## TRANSACTION ROW (TAP TO EDIT; SIDEWAYS SWIPES BELONG TO THE WEEK CAROUSEL) ##

class EntryRow(ButtonBehavior, FloatLayout):
    timestamp_text = StringProperty("")
    category_text = StringProperty("")
    amount_text = StringProperty("")
    note_text = StringProperty("")
    index = NumericProperty(0)
    category_color = ListProperty([0.30, 0.45, 0.32, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(70)

        with self.canvas.before:
            self.bg_color_instruction = Color(*self.category_color)
            self.bg_rect = RoundedRectangle(
                radius=[BORDER_RADIUS],
                pos=self.pos,
                size=self.size
            )
            Color(0, 0, 0, 1)
            self.border_line = Line(
                rounded_rectangle=(self.x, self.y, self.width, self.height, BORDER_RADIUS),
                width=BORDER_WIDTH,
            )

        ## TIMESTAMP (TOP-LEFT) ##

        self.timestamp_label = Label(
            text="",
            size_hint=(None, None),
            size=(dp(180), dp(30)),
            pos_hint={"x": 0.00, "y": 0.50},
            halign="left",
            valign="middle",
            color=contrast_color(self.category_color)
        )
        self.timestamp_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))

        ## CATEGORY (BOTTOM-LEFT) ##

        self.category_label = Label(
            text="",
            size_hint=(None, None),
            size=(dp(180), dp(30)),
            pos_hint={"x": 0.00, "y": 0.10},
            halign="left",
            valign="middle",
            color=contrast_color(self.category_color)
        )
        self.category_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))

        ## NOTE (BOTTOM-RIGHT) ##

        self.note_label = Label(
            text="",
            size_hint=(None, None),
            size=(dp(130), dp(30)),
            pos_hint={"right": 0.95, "y": 0.10},
            halign="right",
            valign="middle",
            color=contrast_color(self.category_color)
        )
        self.note_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))

        ## AMOUNT (TOP-RIGHT) ##

        self.amount_label = Label(
            text="",
            size_hint=(None, None),
            size=(dp(130), dp(30)),
            pos_hint={"right": 0.95, "y": 0.50},
            halign="right",
            valign="middle",
            color=contrast_color(self.category_color)
        )
        self.amount_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))

        self.add_widget(self.timestamp_label)
        self.add_widget(self.category_label)
        self.add_widget(self.note_label)
        self.add_widget(self.amount_label)

        self.bind(
            timestamp_text=self.timestamp_label.setter("text"),
            category_text=self.category_label.setter("text"),
            note_text=self.note_label.setter("text"),
            amount_text=self.amount_label.setter("text"),
            category_color=self.update_color,
            pos=self.update_rect, size=self.update_rect,
        )

    def on_release(self):
        # The "no transactions" placeholder row has no entry behind it #
        if self.index >= 0:
            App.get_running_app().open_edit_window(self.index)

    def update_rect(self, *args):
        self.bg_rect.pos = (self.x, self.y)
        self.bg_rect.size = (self.width, self.height)
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, BORDER_RADIUS)

    def update_color(self, instance, value):
        self.bg_color_instruction.rgba = value
        self.timestamp_label.color = self.category_label.color = self.note_label.color = self.amount_label.color = contrast_color(value)
