from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp

from ui.chevron_button import ChevronButton

## SCREEN WITH A TITLED TOP BAR AND BACK BUTTON ##

class BackScreen(Screen):
    def __init__(self, app, title="", **kwargs):
        super().__init__(**kwargs)
        self.app = app

        self.layout = BoxLayout(orientation="vertical")

        with self.layout.canvas.before:
            Color(0.125, 0.259, 0.188, 1)  # Forest Green
            self.bg_rect = Rectangle(pos=self.layout.pos, size=self.layout.size)

        self.layout.bind(
            pos=lambda i, v: setattr(self.bg_rect, "pos", i.pos),
            size=lambda i, v: setattr(self.bg_rect, "size", i.size)
        )

        ## TOP BAR ##

        top_bar = FloatLayout(size_hint=(1, 0.1))

        with top_bar.canvas.before:
            Color(0.192, 0.4, 0.29, 1)  # Seafoam Green
            self.top_rect = Rectangle(pos=top_bar.pos, size=top_bar.size)

        top_bar.bind(pos=lambda i, v: setattr(self.top_rect, "pos", i.pos),
                     size=lambda i, v: setattr(self.top_rect, "size", i.size))

        self.title_label = Label(
            text=title,
            font_size=sp(20),
            color=(1, 1, 1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        )
        top_bar.add_widget(self.title_label)

        top_bar_controls = BoxLayout(
            pos_hint={"x": 0, "y": 0},
            padding=[dp(6), dp(10)]
        )
        self.back_btn = ChevronButton(size_hint=(None, 1), width=dp(36), on_release=lambda x: self.go_back())
        top_bar_controls.add_widget(self.back_btn)
        top_bar_controls.add_widget(Widget())  # Spacer #
        top_bar.add_widget(top_bar_controls)

        self.layout.add_widget(top_bar)
        self.add_widget(self.layout)

    def go_back(self):
        raise NotImplementedError
