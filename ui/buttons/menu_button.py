from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line
from kivy.metrics import dp

## MENU ICON (THREE BARS) ##

class MenuButton(ButtonBehavior, Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(1, 1, 1, 1)
            self.bars = [Line(width=dp(1.5), cap="round") for _ in range(3)]

        self.bind(pos=self.update_icon, size=self.update_icon)

    def update_icon(self, *args):
        cx, cy = self.x + self.width / 2, self.y + self.height / 2
        half_w = dp(10)
        gap = dp(6)

        for i, bar in enumerate(self.bars):
            y = cy + (1 - i) * gap
            bar.points = [cx - half_w, y, cx + half_w, y]
