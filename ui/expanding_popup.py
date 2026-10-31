from kivy.metrics import dp
from kivy.uix.popup import Popup

POPUP_CHROME = dp(28)       # Popup's own 12dp padding above and below its content, plus the 4dp title separator
SCREEN_MARGIN = dp(8)

## POPUP THAT FITS ITS CONTENT AND GROWS DOWNWARD ##

class ExpandingPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.growing = None     # The part that opens and closes, e.g. an Advanced section #
        self.top_hint = None    # Pins the top to this share of the screen height instead #

    def fit_to(self, layout, growing=None):
        # Call after setting `content`; the height then follows the content as rows are added or opened #
        self.growing = growing
        title_label = self._container.parent.children[-1]
        update = lambda *args: setattr(self, "height", layout.minimum_height + title_label.height + POPUP_CHROME)
        layout.bind(minimum_height=update)
        title_label.bind(height=update)
        layout.do_layout()
        update()

    def _align_center(self, *args):
        # Kivy re-centers a popup whenever it resizes, which would grow it up and down at once #
        # Instead the top stays where it sits with `growing` closed, so opening it only grows the popup downward #
        if not self._is_open:
            return
        window = self._window
        if self.top_hint is not None:
            top = window.height * self.top_hint
        else:
            closed_height = self.height - (self.growing.height if self.growing is not None else 0)
            top = window.center[1] + closed_height / 2

        # Shifts up rather than run off the bottom of the screen #
        self.center_x = window.center[0]
        self.top = min(max(top, self.height + SCREEN_MARGIN), window.height)
