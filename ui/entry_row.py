from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.metrics import dp, sp

from ui.color_utils import contrast_color


class EntryRowBackground(FloatLayout):
    edit_color = ListProperty([1, 1, 0, 1])
    delete_color = ListProperty([1, 0, 0, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self.edit_color_instruction = Color(*self.edit_color)
            self.edit_rect = RoundedRectangle(radius=[dp(0)], pos=self.pos, size=self.size)

        with self.canvas.before:
            self.delete_color_instruction = Color(*self.delete_color)
            self.delete_rect = RoundedRectangle(radius=[dp(0)], pos=self.pos, size=self.size)

        self.edit_label = Label(
            text="Edit",
            size_hint=(None, None),
            size=(dp(180), dp(30)),
            color=(1, 1, 1, 1),
        )
        self.delete_label = Label(
            text="Delete",
            size_hint=(None, None),
            size=(dp(180), dp(30)),
            color=(1, 1, 1, 1),
        )
        self.add_widget(self.edit_label)
        self.add_widget(self.delete_label)

        self.bind(
            pos=self.update_rect, size=self.update_rect,
            edit_color=self.update_edit_color, delete_color=self.update_delete_color
        )
        self.update_rect()

    def update_rect(self, *args):
        self.edit_rect.pos = (self.x + dp(180), self.y)
        self.edit_rect.size = (self.width - dp(180), self.height)
        self.delete_rect.pos = (self.x, self.y)
        self.delete_rect.size = (self.width - dp(180), self.height)
        self.edit_label.center = (self.edit_rect.pos[0] + self.edit_rect.size[0] / 2, self.y + self.height / 2)
        self.delete_label.center = (self.x + self.delete_rect.size[0] / 2, self.y + self.height / 2)

    def update_edit_color(self, instance, value):
        self.edit_color_instruction.rgba = value

    def update_delete_color(self, instance, value):
        self.delete_color_instruction.rgba = value


class EntryRow(FloatLayout):
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

        self.background = EntryRowBackground(
            size_hint=(None, None),
            pos=self.pos,
            size=self.size
        )
        self.add_widget(self.background)

        with self.canvas:
            self.bg_color_instruction = Color(*self.category_color)
            self.bg_rect = RoundedRectangle(
                radius=[dp(10)],
                pos=self.pos,
                size=self.size
            )

        self.bind(pos=self.update_rect, size=self.update_rect, category_color=self.update_color)

        ## TIMESTAMP (TOP-LEFT) ##

        self.timestamp_label = Label(
            text="",
            size_hint=(None, None),
            size=(dp(180), dp(30)),
            pos_hint={"x": 0.00, "y": 0.60},
            halign="left",
            valign="middle",
            color=contrast_color(self.category_color)
        )
        self.timestamp_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        self.bind(timestamp_text=self.timestamp_label.setter("text"))

        ## CATEGORY (BOTTOM-LEFT) ##

        self.category_label = Label(
            text="",
            size_hint=(None, None),
            size=(dp(180), dp(30)),
            pos_hint={"x": 0.00, "y": 0.20},
            halign="left",
            valign="middle",
            color=contrast_color(self.category_color)
        )
        self.category_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        self.bind(category_text=self.category_label.setter("text"))

        ## NOTE (MIDDLE) ##

        self.note_label = Label(
            text="",
            size_hint=(None, None),
            size=(dp(180), dp(30)),
            pos_hint={"x": 0.25, "y": 0.20},
            halign="left",
            valign="middle",
            color=contrast_color(self.category_color)
        )
        self.note_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        self.bind(note_text=self.note_label.setter("text"))

        ## AMOUNT (TOP-RIGHT) ##

        self.amount_label = Label(
            text="",
            size_hint=(None, None),
            size=(dp(100), dp(30)),
            pos_hint={"right": 0.95, "y": 0.60},
            halign="right",
            valign="middle",
            color=contrast_color(self.category_color)
        )
        self.amount_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        self.bind(amount_text=self.amount_label.setter("text"))

        ## EDIT BUTTON (BOTTOM-RIGHT) ##

        self.edit_btn = Button(
            text="Edit",
            size_hint=(None, None),
            size=(dp(60), dp(30)),
            pos_hint={"right": 0.95, "y": 0.20},
            background_normal="",
            background_color=(0.3, 0.5, 0.8, 1),
            color=(1, 1, 1, 1),
        )
        self.edit_btn.bind(on_release=self.on_edit_pressed)

        ## DELETE BUTTON (FAR-RIGHT) ##

        self.delete_btn = Button(
            text="X",
            size_hint=(None, None),
            size=(dp(40), dp(30)),
            pos_hint={"right": 0.80, "y": 0.20},
            background_normal="",
            background_color=(0.8, 0.3, 0.3, 1),
            color=(1, 1, 1, 1),
        )
        self.delete_btn.bind(on_release=self.on_delete_pressed)
    
        self.add_widget(self.timestamp_label)
        self.add_widget(self.category_label)
        self.add_widget(self.note_label)
        self.add_widget(self.amount_label)
        self.add_widget(self.edit_btn)
        self.add_widget(self.delete_btn)

    def update_rect(self, *args):
        self.background.pos = self.pos
        self.background.size = self.size
        self.bg_rect.pos = (self.x, self.y)
        self.bg_rect.size = (self.width, self.height)

    def update_color(self, instance, value):
        self.bg_color_instruction.rgba = value
        self.timestamp_label.color = self.category_label.color = self.note_label.color = self.amount_label.color = contrast_color(value)

    def on_delete_pressed(self, instance):
        App.get_running_app().delete_entry(self.index)

    def on_edit_pressed(self, instance):
        app = App.get_running_app()
        app.open_edit_window(self.index)