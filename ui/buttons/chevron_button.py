from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.metrics import dp

## CHEVRON ICON BUTTON (BACK BUTTON, WEEK ARROWS) ##

class ChevronButton(ButtonBehavior, Widget):
    def __init__(self, pointing="left", **kwargs):
        super().__init__(**kwargs)
        self.pointing = pointing

        with self.canvas:
            Color(1, 1, 1, 1)
            self.chevron = Line(width=dp(1.5), cap="round", joint="round")

        self.bind(pos=self.update_icon, size=self.update_icon)

    def update_icon(self, *args):
        cx, cy = self.x + self.width / 2, self.y + self.height / 2
        half = dp(8)
        tip = -half / 2 if self.pointing == "left" else half / 2

        self.chevron.points = [cx - tip, cy + half, cx + tip, cy, cx - tip, cy - half]
