from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp, sp

MINT = (0.51765, 0.878, 0.737, 1)       # Leftover added
SALMON = (0.96, 0.62, 0.6, 1)           # Overspend subtracted
TAP_SLOP = dp(8)

## PILL BUTTON THAT MOVES A WEEK'S/MONTH'S LEFTOVER OR OVERSPEND ONTO THE NEXT ONE ##

def carry_over_text(carry_over, unit, with_amount=True):
    # It sits on the week/month the amount comes from, so it always names where it goes #
    # Says what tapping does before it's on ("Add $20.00 to next month") and what happened after ("Subtracted from next week") #
    amount = f" ${abs(carry_over['amount']):.2f}" if with_amount else ""
    if carry_over["over"]:
        verb = "Subtracted" if carry_over["carried"] else "Subtract"
        return f"{verb}{amount} from next {unit}"
    verb = "Added" if carry_over["carried"] else "Add"
    return f"{verb}{amount} to next {unit}"

class CarryOverButton(ButtonBehavior, Label):
    def __init__(self, carry_over, unit, with_amount=True, outline_color=(1, 1, 1, 1), **kwargs):
        super().__init__(
            text=carry_over_text(carry_over, unit, with_amount),
            font_size=sp(12),
            bold=True,
            halign="center",
            valign="middle",
            shorten=True,
            **kwargs
        )
        self.carried = carry_over["carried"]

        # On: filled pill; off: outlined in the surrounding text color #
        fill = SALMON if carry_over["over"] else MINT
        self.color = (0, 0, 0, 1) if self.carried else outline_color

        with self.canvas.before:
            Color(*(fill if self.carried else (0, 0, 0, 0)))
            self.bg_rect = RoundedRectangle()
            Color(*((0, 0, 0, 0) if self.carried else outline_color))
            self.border_line = Line(width=dp(1.2))

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        radius = self.height / 2 - dp(1)
        self.text_size = (self.width - dp(12), self.height)
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.bg_rect.radius = [radius]
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, radius)

    def collide_point(self, x, y):
        # A little extra room above and below so the slim pill is easier to tap #
        return self.x <= x <= self.right and self.y - TAP_SLOP <= y <= self.top + TAP_SLOP
