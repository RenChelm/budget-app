import math

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex

from ui.name_select_popup import NAME_KINDS
from ui.week_row import EMPTY_COLOR, UNCATEGORIZED_COLOR

MAX_SLICES = 6                       # Past this, the smallest slices fold into one "Other" slice
OTHER_COLOR = (0.85, 0.85, 0.85, 1)  # Light gray, so it stands apart from uncategorized's mid gray
MUTED_TEXT_COLOR = (1, 1, 1, 0.6)
RING_SIZE = dp(150)
RING_THICKNESS = dp(20)
SLICE_GAP = dp(2)                    # Background showing between slices
TITLE_HEIGHT = dp(28)
LEGEND_ROW_HEIGHT = dp(26)
SECTION_SPACING = dp(8)
CHART_GAP = dp(12)

# Retailers and brands have no colors of their own, so slices take these in order, biggest first #
# In this order every pair of neighbors around the ring (including last back to first, and Other's gray) #
# stays apart for color-blind viewers too, checked against the app's green background #
SERIES_COLORS = [get_color_from_hex(h) for h in ("#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300")]

def chart_slices(categories, limit=MAX_SLICES):
    # Only categories with money spent get a slice; refunds can leave one at $0 or less #
    spending = [category for category in categories if category["amount"] > 0]
    if len(spending) > limit:
        rest = spending[limit - 1:]
        other = {"name": f"Other ({len(rest)})", "color": OTHER_COLOR, "amount": sum(c["amount"] for c in rest)}
        spending = spending[:limit - 1] + [other]

    total = sum(category["amount"] for category in spending)
    return [
        {
            "name": category["name"] or "Uncategorized",
            "color": category["color"] or UNCATEGORIZED_COLOR,
            "amount": category["amount"],
            "share": category["amount"] / total,
        }
        for category in spending
    ]

def name_slices(totals, limit=MAX_SLICES):
    # Retailer or brand slices, colored by size so neighboring slices always differ (see SERIES_COLORS) #
    # Names past the palette are always folded into Other, so they never need a color of their own #
    spending = [total for total in totals if total["amount"] > 0]
    colored = [{**total, "color": SERIES_COLORS[i] if i < len(SERIES_COLORS) else OTHER_COLOR} for i, total in enumerate(spending)]
    return chart_slices(colored, limit)

## DONUT RING (SLICES CLOCKWISE FROM THE TOP, BIGGEST FIRST, TOTAL IN THE MIDDLE) ##

class SpendingRing(FloatLayout):
    def __init__(self, slices, **kwargs):
        super().__init__(**kwargs)
        self.slices = slices

        # Kivy's Line width is half the stroke, so this draws a RING_THICKNESS wide ring #
        self.arcs = []
        with self.canvas.before:
            for color in [s["color"] for s in slices] or [EMPTY_COLOR]:
                Color(*color)
                self.arcs.append(Line(width=RING_THICKNESS / 2, cap="none"))

        total = sum(s["amount"] for s in slices)
        self.total_label = Label(
            text=f"${total:.2f}",
            font_size=sp(18),
            bold=True,
            color=(1, 1, 1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.56}
        )
        self.spent_label = Label(
            text="spent",
            font_size=sp(12),
            color=MUTED_TEXT_COLOR,
            pos_hint={"center_x": 0.5, "center_y": 0.41}
        )
        self.add_widget(self.total_label)
        self.add_widget(self.spent_label)

        self.bind(pos=self.update_ring, size=self.update_ring)

    def slice_angles(self, radius):
        # A lone slice (or the empty track) is a full circle with no gap #
        if len(self.slices) <= 1:
            return [(0, 360)]

        gap = math.degrees(SLICE_GAP / radius)
        angles = []
        start = 0
        for s in self.slices:
            end = start + s["share"] * 360
            # A sliver too thin for its gap still shows as a hairline #
            angles.append((start + gap / 2, max(end - gap / 2, start + gap / 2 + 0.5)))
            start = end
        return angles

    def update_ring(self, *args):
        radius = (min(self.width, self.height) - RING_THICKNESS) / 2
        if radius <= 0:
            return

        cx, cy = self.center
        for arc, (start, end) in zip(self.arcs, self.slice_angles(radius)):
            arc.circle = (cx, cy, radius, start, end)

## ONE LEGEND ROW (SWATCH, NAME, AMOUNT, SHARE) ##

class LegendRow(BoxLayout):
    def __init__(self, chart_slice, **kwargs):
        super().__init__(size_hint_y=None, height=LEGEND_ROW_HEIGHT, spacing=dp(8), **kwargs)

        swatch_box = AnchorLayout(size_hint_x=None, width=dp(14))
        swatch = Widget(size_hint=(None, None), size=(dp(12), dp(12)))
        with swatch.canvas:
            Color(*chart_slice["color"])
            swatch.rect = RoundedRectangle(pos=swatch.pos, size=swatch.size, radius=[dp(3)])
        swatch.bind(
            pos=lambda inst, val: setattr(inst.rect, "pos", inst.pos),
            size=lambda inst, val: setattr(inst.rect, "size", inst.size)
        )
        swatch_box.add_widget(swatch)
        self.add_widget(swatch_box)

        self.name_label = self._make_label(chart_slice["name"], "left", (1, 1, 1, 1), shorten=True)
        self.amount_label = self._make_label(f"${chart_slice['amount']:.2f}", "right", (1, 1, 1, 1), width=dp(80))
        self.share_label = self._make_label(f"{chart_slice['share']:.0%}", "right", MUTED_TEXT_COLOR, width=dp(44))

    def _make_label(self, text, halign, color, width=None, shorten=False):
        label = Label(
            text=text,
            font_size=sp(14),
            halign=halign,
            valign="middle",
            color=color,
            shorten=shorten,
            shorten_from="right"
        )
        if width is not None:
            label.size_hint_x = None
            label.width = width
        label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        self.add_widget(label)
        return label

## SPENDING CHART (TITLE + RING + LEGEND, OR A MESSAGE WHEN THERE'S NOTHING TO SHOW) ##

class SpendingChart(BoxLayout):
    def __init__(self, title, slices, note=None, empty_text=None, **kwargs):
        # The top padding keeps each chart's title clear of whatever's above it, like the legend of the chart before #
        super().__init__(orientation="vertical", size_hint_y=None, spacing=SECTION_SPACING, padding=[0, CHART_GAP, 0, 0], **kwargs)
        self.slices = slices
        self.ring = None
        self.legend_rows = []
        self.note_label = None
        self.bind(minimum_height=self.setter("height"))

        self.title_label = Label(
            text=title,
            font_size=sp(15),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=TITLE_HEIGHT
        )
        self.add_widget(self.title_label)

        # With `empty_text`, nothing to chart shows the message instead of an empty ring #
        if not slices and empty_text is not None:
            self.note_label = self._make_note(empty_text)
            return

        ring_box = AnchorLayout(size_hint_y=None, height=RING_SIZE)
        self.ring = SpendingRing(slices, size_hint=(None, None), size=(RING_SIZE, RING_SIZE))
        ring_box.add_widget(self.ring)
        self.add_widget(ring_box)

        # The legend carries each slice's name and figures, so nothing depends on telling colors apart #
        self.legend_rows = [LegendRow(s) for s in slices]
        for row in self.legend_rows:
            self.add_widget(row)

        if note is not None:
            self.note_label = self._make_note(note)

    def _make_note(self, text):
        # Muted text that wraps onto as many lines as it needs #
        label = Label(text=text, font_size=sp(13), halign="center", valign="middle", color=MUTED_TEXT_COLOR, size_hint_y=None)
        label.bind(
            width=lambda inst, val: setattr(inst, "text_size", (inst.width, None)),
            texture_size=lambda inst, val: setattr(inst, "height", inst.texture_size[1])
        )
        self.add_widget(label)
        return label

class CategoryChart(SpendingChart):
    def __init__(self, categories, **kwargs):
        super().__init__("Spending by Category", chart_slices(categories), **kwargs)

## SPENDING BY RETAILER OR BRAND (ONLY TRANSACTIONS THAT HAVE ONE) ##

class NameChart(SpendingChart):
    def __init__(self, kind, totals, spent, **kwargs):
        name = NAME_KINDS[kind].lower()

        # Spending without one is left out of the ring, and the note says how much that was #
        missing = round(spent - sum(total["amount"] for total in totals), 2)
        note = f"Not counting ${missing:.2f} with no {name}" if missing > 0 else None
        super().__init__(
            f"Spending by {NAME_KINDS[kind]}",
            name_slices(totals),
            note=note,
            empty_text=f"Nothing here has a {name} yet. Pick one under Advanced when adding or editing a transaction.",
            **kwargs
        )
