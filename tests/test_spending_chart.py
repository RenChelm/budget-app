import pytest

from ui.spending_chart import (
    MAX_SLICES,
    OTHER_COLOR,
    RING_SIZE,
    SERIES_COLORS,
    CategoryChart,
    NameChart,
    SpendingRing,
    chart_slices,
    name_slices,
)
from ui.week_row import UNCATEGORIZED_COLOR

FOOD_COLOR = [1, 0.6, 0.2, 1]
GAS_COLOR = [0.3, 0.6, 0.9, 1]


def total(name, amount, color=None):
    return {"name": name, "color": color, "amount": amount}


## SLICES ##

def test_slices_share_the_total_and_label_uncategorized():
    slices = chart_slices([total("Food", 30.0, FOOD_COLOR), total(None, 10.0)])

    assert [(s["name"], s["share"]) for s in slices] == [("Food", 0.75), ("Uncategorized", 0.25)]
    assert slices[0]["color"] == FOOD_COLOR
    assert slices[1]["color"] == UNCATEGORIZED_COLOR


def test_categories_with_nothing_spent_get_no_slice():
    # A refund can bring a category to $0 or below #
    slices = chart_slices([total("Food", 20.0, FOOD_COLOR), total("Gas", 0.0, GAS_COLOR), total("Refunds", -5.0)])

    assert [s["name"] for s in slices] == ["Food"]
    assert slices[0]["share"] == 1


def test_smallest_categories_fold_into_other_past_the_slice_limit():
    categories = [total(f"Category {i}", 100.0 - i) for i in range(MAX_SLICES + 2)]

    slices = chart_slices(categories)

    assert len(slices) == MAX_SLICES
    assert [s["name"] for s in slices[:-1]] == [f"Category {i}" for i in range(MAX_SLICES - 1)]
    assert slices[-1]["name"] == "Other (3)"
    assert slices[-1]["amount"] == sum(100.0 - i for i in range(MAX_SLICES - 1, MAX_SLICES + 2))
    assert slices[-1]["color"] == OTHER_COLOR
    assert sum(s["share"] for s in slices) == pytest.approx(1)


def test_exactly_the_slice_limit_needs_no_other():
    slices = chart_slices([total(f"Category {i}", 10.0) for i in range(MAX_SLICES)])

    assert [s["name"] for s in slices] == [f"Category {i}" for i in range(MAX_SLICES)]


## RING ##

def test_slices_run_clockwise_from_the_top_with_gaps_between(kivy_window):
    ring = SpendingRing(chart_slices([total("Food", 30.0, FOOD_COLOR), total("Gas", 10.0, GAS_COLOR)]))

    (food_start, food_end), (gas_start, gas_end) = ring.slice_angles(radius=65)

    assert 0 < food_start < 1
    assert food_end < 270 < gas_start
    assert gas_end < 360


def test_a_single_category_fills_the_whole_ring(kivy_window):
    ring = SpendingRing(chart_slices([total("Food", 30.0, FOOD_COLOR)]))

    assert ring.slice_angles(radius=65) == [(0, 360)]


def test_ring_shows_the_total_spent_in_the_middle(kivy_window):
    ring = SpendingRing(chart_slices([total("Food", 30.0, FOOD_COLOR), total("Gas", 12.5, GAS_COLOR)]))

    assert ring.total_label.text == "$42.50"
    assert ring.spent_label.text == "spent"


## CHART ##

def test_legend_lists_each_slice_with_its_amount_and_share(kivy_window):
    chart = CategoryChart([total("Food", 30.0, FOOD_COLOR), total(None, 10.0)])

    rows = [(r.name_label.text, r.amount_label.text, r.share_label.text) for r in chart.legend_rows]
    assert rows == [("Food", "$30.00", "75%"), ("Uncategorized", "$10.00", "25%")]


def test_period_with_no_spending_shows_an_empty_ring_and_no_legend(kivy_window):
    chart = CategoryChart([])

    assert chart.legend_rows == []
    assert len(chart.ring.arcs) == 1
    assert chart.ring.total_label.text == "$0.00"
    assert chart.ring.slice_angles(radius=65) == [(0, 360)]


def test_chart_is_tall_enough_for_its_legend(kivy_window):
    one = CategoryChart([total("Food", 30.0, FOOD_COLOR)])
    two = CategoryChart([total("Food", 30.0, FOOD_COLOR), total("Gas", 10.0, GAS_COLOR)])
    one.do_layout()
    two.do_layout()

    assert one.height > RING_SIZE
    assert two.height - one.height == pytest.approx(two.legend_rows[0].height + two.spacing)


## RETAILERS AND BRANDS ##

def named(name, amount):
    return {"name": name, "amount": amount}


def test_name_slices_take_the_palette_in_order_biggest_first():
    slices = name_slices([named("Walmart", 50.0), named("Target", 30.0), named("Aldi", 20.0)])

    assert [(s["name"], s["share"]) for s in slices] == [("Walmart", 0.5), ("Target", 0.3), ("Aldi", 0.2)]
    assert [s["color"] for s in slices] == SERIES_COLORS[:3]


def test_name_slices_use_a_names_own_color_and_the_palette_for_the_rest():
    slices = name_slices([{**named("Walmart", 50.0), "color": [0.9, 0.3, 0.3, 1]}, named("Target", 30.0), {**named("Aldi", 20.0), "color": None}])

    assert [s["color"] for s in slices] == [[0.9, 0.3, 0.3, 1], SERIES_COLORS[1], SERIES_COLORS[2]]


def test_name_slices_skip_refunded_names_without_skipping_a_color():
    slices = name_slices([named("Walmart", 50.0), named("Target", -5.0), named("Aldi", 20.0)])

    assert [s["name"] for s in slices] == ["Walmart", "Aldi"]
    assert [s["color"] for s in slices] == SERIES_COLORS[:2]


def test_name_slices_fill_every_palette_color_before_folding_into_other():
    assert len(SERIES_COLORS) == MAX_SLICES

    full = name_slices([named(f"Store {i}", 100.0 - i) for i in range(MAX_SLICES)])
    folded = name_slices([named(f"Store {i}", 100.0 - i) for i in range(MAX_SLICES + 3)])

    assert [s["color"] for s in full] == SERIES_COLORS
    assert [s["color"] for s in folded] == SERIES_COLORS[:MAX_SLICES - 1] + [OTHER_COLOR]
    assert folded[-1]["name"] == "Other (4)"


def test_neighboring_slices_never_share_a_color():
    # Around the ring, including the last slice back to the first #
    for count in range(2, MAX_SLICES + 4):
        colors = [tuple(s["color"]) for s in name_slices([named(f"Store {i}", 100.0 - i) for i in range(count)])]
        assert all(colors[i] != colors[i - 1] for i in range(len(colors)))


@pytest.mark.parametrize("kind, title", [("retailer", "Spending by Retailer/Platform"), ("brand", "Spending by Brand/Creator")])
def test_name_chart_is_titled_for_its_kind(kivy_window, kind, title):
    chart = NameChart(kind, [named("Walmart", 10.0)], spent=10.0)

    assert chart.title_label.text == title


def test_name_chart_rings_only_spending_that_has_a_name_and_notes_the_rest(kivy_window):
    chart = NameChart("retailer", [named("Walmart", 30.0), named("Target", 10.0)], spent=65.5)

    assert chart.ring.total_label.text == "$40.00"
    assert [r.share_label.text for r in chart.legend_rows] == ["75%", "25%"]
    assert chart.note_label.text == "Not counting $25.50 with no retailer/platform"


def test_name_chart_has_no_note_when_everything_has_a_name(kivy_window):
    chart = NameChart("brand", [named("Lay's", 12.0)], spent=12.0)

    assert chart.note_label is None


def test_name_chart_with_nothing_named_shows_how_to_add_one_instead_of_a_ring(kivy_window):
    chart = NameChart("brand", [], spent=40.0)

    assert chart.ring is None
    assert chart.legend_rows == []
    assert chart.note_label.text == "Nothing here has a brand/creator yet. Pick one under Advanced when adding or editing a transaction."


def test_name_chart_is_tall_enough_for_a_wrapped_message(kivy_window):
    chart = NameChart("retailer", [], spent=0.0, width=200)
    chart.do_layout()                   # Gives the message its width, so it wraps #
    chart.note_label.texture_update()
    chart.do_layout()

    assert chart.note_label.height > chart.title_label.height
    assert chart.height >= chart.title_label.height + chart.note_label.height
