from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ColorProperty, StringProperty
from kivy.uix.button import Button

from ui.entry_row import BORDER_RADIUS

PRESSED_SHADE = 0.8     # How much darker it gets while held down #

## BUTTON WITH ROUNDED CORNERS (ROUNDED AS MUCH AS THE ENTRY ROWS) ##

class RoundedButton(Button):
    fill_color = ColorProperty((0.51765, 0.878, 0.737, 1))

    # Button's own square background is hidden; the rounded one is drawn behind it instead #
    background_normal = StringProperty("")
    background_down = StringProperty("")
    background_color = ColorProperty((0, 0, 0, 0))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            self.fill_instruction = Color()
            self.bg_rect = RoundedRectangle(radius=[BORDER_RADIUS])

        self.bind(pos=self._redraw, size=self._redraw, state=self._recolor, fill_color=self._recolor)
        self._redraw()
        self._recolor()

    def _redraw(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def _recolor(self, *args):
        r, g, b, a = self.fill_color
        shade = PRESSED_SHADE if self.state == "down" else 1
        self.fill_instruction.rgba = (r * shade, g * shade, b * shade, a)
