from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.metrics import dp, sp

from budget_periods import format_range
from ui.color_utils import contrast_color
from ui.entry_row import BORDER_WIDTH, BORDER_RADIUS

UNCATEGORIZED_COLOR = (0.5, 0.5, 0.5, 1)    # Neutral gray; the main list's uncategorized green blends into the background
EMPTY_COLOR = (1, 1, 1, 0.08)               # Faint fill for weeks with nothing spent
UPCOMING_TEXT_COLOR = (1, 1, 1, 0.6)
CURRENT_BORDER_WIDTH = dp(2)
OVER_BORDER_WIDTH = dp(3)
BAR_HEIGHT = dp(6)
BAR_INSET = dp(12)

class WeekRow(ButtonBehavior, FloatLayout):
    def __init__(self, week, number, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(96)
        self.week = week

        status = week["status"]
        top = week["top_category"]
        over = week["left"] is not None and week["left"] < 0

        ## STATE-DEPENDENT STYLING ##
        # Fill shows the top category; over/under is shown by the bar, text and border instead #

        if status == "upcoming":
            fill, text_color, border_color = (0, 0, 0, 0), UPCOMING_TEXT_COLOR, (1, 1, 1, 0.35)
        elif top is None:
            fill, text_color, border_color = EMPTY_COLOR, (1, 1, 1, 1), (0, 0, 0, 1)
        else:
            fill = top["color"] or UNCATEGORIZED_COLOR
            text_color, border_color = contrast_color(fill), (0, 0, 0, 1)

        border_width = BORDER_WIDTH
        if status == "current":
            border_color, border_width = (1, 1, 1, 1), CURRENT_BORDER_WIDTH
        if over:
            border_width = OVER_BORDER_WIDTH

        self.fill_color, self.text_color = fill, text_color

        with self.canvas.before:
            Color(*fill)
            self.bg_rect = RoundedRectangle(radius=[BORDER_RADIUS])
            Color(*border_color)
            self.border_line = Line(width=border_width)

        ## PROGRESS BAR (SPENT VS WEEKLY MAX) ##

        self.show_bar = week["weekly_max"] is not None and status != "upcoming"
        self.bar_fraction = max(0, min(week["spent"] / week["weekly_max"], 1)) if self.show_bar else 0

        if self.show_bar:
            with self.canvas.before:
                Color(*text_color[:3], 0.25)
                self.bar_track = RoundedRectangle(radius=[BAR_HEIGHT / 2])
                Color(*text_color[:3], 0.85)
                self.bar_fill = RoundedRectangle(radius=[BAR_HEIGHT / 2])

        self.bind(pos=self.update_rect, size=self.update_rect)

        ## LABEL TEXT ##

        dates_text = f"Week {number} · {format_range(week['start'], week['end'])}"

        if status == "upcoming":
            spent_text, detail_text, status_text = "", "Upcoming", ""
        else:
            spent_text = f"${week['spent']:.2f}"

            if top is None:
                detail_text = "No spending"
            else:
                purchases = f"{week['count']} purchase" + ("" if week["count"] == 1 else "s")
                detail_text = f"{top['name'] or 'Uncategorized'} {week['top_share']:.0%} · {purchases}"

            if week["left"] is None:
                status_text = ""
            elif over:
                status_text = f"${-week['left']:.2f} over"
            else:
                status_text = f"${week['left']:.2f} left"

        ## DATES (TOP-LEFT) ##

        self.dates_label = self._make_label(dates_text, "left", {"x": 0.04, "y": 0.57})

        ## SPENT (TOP-RIGHT) ##

        self.spent_label = self._make_label(spent_text, "right", {"right": 0.96, "y": 0.57}, bold=True)

        ## TOP CATEGORY + PURCHASE COUNT (BOTTOM-LEFT) ##

        self.detail_label = self._make_label(detail_text, "left", {"x": 0.04, "y": 0.29}, font_size=sp(13))

        ## LEFT / OVER (BOTTOM-RIGHT) ##

        self.status_label = self._make_label(status_text, "right", {"right": 0.96, "y": 0.29}, font_size=sp(13))

    def _make_label(self, text, halign, pos_hint, font_size=sp(14), bold=False):
        label = Label(
            text=text,
            size_hint=(0.62 if halign == "left" else 0.30, None),
            height=dp(24),
            pos_hint=pos_hint,
            halign=halign,
            valign="middle",
            font_size=font_size,
            bold=bold,
            shorten=True,
            shorten_from="right",
            color=self.text_color
        )
        label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        self.add_widget(label)
        return label

    def update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, BORDER_RADIUS)

        if self.show_bar:
            bar_width = self.width - 2 * BAR_INSET
            bar_pos = (self.x + BAR_INSET, self.y + dp(11))
            self.bar_track.pos = bar_pos
            self.bar_track.size = (bar_width, BAR_HEIGHT)
            self.bar_fill.pos = bar_pos
            self.bar_fill.size = (bar_width * self.bar_fraction, BAR_HEIGHT)
