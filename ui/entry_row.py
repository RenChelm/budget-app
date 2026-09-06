from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.metrics import dp, sp
from kivy.animation import Animation

from ui.color_utils import contrast_color

SWIPE_REVEAL_WIDTH = dp(180)
SWIPE_LOCK_DISTANCE = dp(10)    # movement needed before we commit to horizontal vs vertical
SWIPE_OPEN_THRESHOLD = dp(90)   # drag past this far before release snaps fully open
BORDER_WIDTH = dp(1.1)
BORDER_RADIUS = dp(10)

class EntryRowBackground(FloatLayout):
    edit_color = ListProperty([1, 1, 0, 1])
    delete_color = ListProperty([1, 0, 0, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self.delete_color_instruction = Color(*self.delete_color)
            self.delete_rect = RoundedRectangle(radius=[BORDER_RADIUS], pos=self.pos, size=self.size)
            Color(0, 0, 0, 1)
            self.delete_border = Line(width=BORDER_WIDTH)

            self.edit_color_instruction = Color(*self.edit_color)
            self.edit_rect = RoundedRectangle(radius=[BORDER_RADIUS], pos=self.pos, size=self.size)
            Color(0, 0, 0, 1)
            self.edit_border = Line(width=BORDER_WIDTH)

        self.edit_label = Label(
            text="Edit",
            size_hint=(None, None),
            size=(dp(180), dp(30)),
            color=(0, 0, 0, 1),
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
        self.delete_rect.pos = (self.x, self.y)
        self.delete_rect.size = (SWIPE_REVEAL_WIDTH, self.height)
        self.delete_border.rounded_rectangle = (
            self.x, self.y, SWIPE_REVEAL_WIDTH, self.height, BORDER_RADIUS
        )

        self.edit_rect.pos = (self.right - SWIPE_REVEAL_WIDTH, self.y)
        self.edit_rect.size = (SWIPE_REVEAL_WIDTH, self.height)
        self.edit_border.rounded_rectangle = (
            self.right - SWIPE_REVEAL_WIDTH, self.y, SWIPE_REVEAL_WIDTH, self.height, BORDER_RADIUS
        )

        self.delete_label.center = (self.x + SWIPE_REVEAL_WIDTH / 2, self.center_y)
        self.edit_label.center = (self.right - SWIPE_REVEAL_WIDTH / 2, self.center_y)

    def update_edit_color(self, instance, value):
        self.edit_color_instruction.rgba = value

    def update_delete_color(self, instance, value):
        self.delete_color_instruction.rgba = value

class EntryRowContent(FloatLayout):
    category_color = ListProperty([0.30, 0.45, 0.32, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
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
        
        self.bind(pos=self.update_rect, size=self.update_rect, category_color=self.update_color)

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

    def update_rect(self, *args):
        self.bg_rect.pos = (self.x, self.y)
        self.bg_rect.size = (self.width, self.height)
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, BORDER_RADIUS)

    def update_color(self, instance, value):
        self.bg_color_instruction.rgba = value
        self.timestamp_label.color = self.category_label.color = self.note_label.color = self.amount_label.color = contrast_color(value)
            
class EntryRow(FloatLayout):
    timestamp_text = StringProperty("")
    category_text = StringProperty("")
    amount_text = StringProperty("")
    note_text = StringProperty("")
    index = NumericProperty(0)
    category_color = ListProperty([0.30, 0.45, 0.32, 1])
    swipe_x = NumericProperty(0)    # 0 = closed, -max_swipe = edit revealed, +max_swipe = delete revealed

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(70)
        self.max_swipe = SWIPE_REVEAL_WIDTH

        self.background = EntryRowBackground(
            size_hint=(None, None),
            pos=self.pos,
            size=self.size
        )
        self.add_widget(self.background)

        self.content = EntryRowContent(
            size_hint=(None, None), 
            pos=self.pos, 
            size=self.size
        )
        self.add_widget(self.content)

        self.bind(
            timestamp_text=self.content.timestamp_label.setter("text"),
            category_text=self.content.category_label.setter("text"),
            note_text=self.content.note_label.setter("text"),
            amount_text=self.content.amount_label.setter("text"),
            category_color=self.content.setter("category_color"),
            pos=self.update_rect, size=self.update_rect,
            swipe_x=self._reposition_content,
            index=self.reset_swipe,
        )

        self._touch = None
        self._drag_axis = None      # None = undecided, "x" = swipe, "y" = list scroll

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch = touch
            self._start_x, self._start_y = touch.pos
            self._start_swipe_x = self.swipe_x
            self._drag_axis = None
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._touch is not touch:
            return super().on_touch_move(touch)

        dx = touch.x - self._start_x
        dy = touch.y - self._start_y

        if self._drag_axis is None:
            if abs(dx) > SWIPE_LOCK_DISTANCE or abs(dy) > SWIPE_LOCK_DISTANCE:
                self._drag_axis = "x" if abs(dx) > abs(dy) else "y"
                if self._drag_axis == "x":
                    touch.grab(self)

        if self._drag_axis == "x":
            new_x = self._start_swipe_x + dx
            self.swipe_x = max(-self.max_swipe, min(self.max_swipe, new_x))
            return True

        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self._drag_axis = None
            self._touch = None
            self._resolve_swipe()
            return True

        if self._touch is touch:
            self._touch = None
            if self.swipe_x != 0:
                self.close_swipe()
                return True

        return super().on_touch_up(touch)

    def _resolve_swipe(self, *args):
        if self.swipe_x <= -SWIPE_OPEN_THRESHOLD:
            self.close_swipe()
            self.on_edit_pressed(self)
        elif self.swipe_x >= SWIPE_OPEN_THRESHOLD:
            self.close_swipe()
            self.on_delete_pressed(self)
        else:
            self.close_swipe()

    def close_swipe(self):
        Animation.cancel_all(self, "swipe_x")
        Animation(swipe_x=0, duration=0.18, t="out_cubic").start(self)

    def reset_swipe(self, *args):
        Animation.cancel_all(self, "swipe_x")
        self.swipe_x = 0

    def on_delete_pressed(self, instance):
        App.get_running_app().delete_entry(self.index)

    def on_edit_pressed(self, instance):
        App.get_running_app().open_edit_window(self.index)

    def update_rect(self, *args):
        self.background.pos = self.pos
        self.background.size = self.size
        self.content.size = self.size
        self._reposition_content()

    def _reposition_content(self, *args):
        self.content.pos = (self.x + self.swipe_x, self.y)
