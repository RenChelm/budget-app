import pytest

from kivy.tests.common import UnitTestTouch
from kivy.uix.label import Label

import ui.page_carousel as page_carousel
from ui.page_carousel import (
    MAX_SETTLE_DURATION,
    MIN_SETTLE_DURATION,
    SWIPE_MIN_MOVE,
    PageCarousel,
    settle_duration,
    swipe_velocity,
)

WIDTH = 360


## FINGER SPEED ##

def test_velocity_is_the_recent_distance_over_time():
    samples = [(0.00, 300), (0.02, 280), (0.04, 260), (0.06, 240)]

    assert swipe_velocity(samples, now=0.06) == pytest.approx(-1000)


def test_velocity_only_counts_the_last_moment():
    # A slow drag that speeds up at the end is measured at the end #
    samples = [(0.0, 300), (1.0, 290), (1.05, 270), (1.10, 250)]

    assert swipe_velocity(samples, now=1.10) == pytest.approx(-400)


def test_velocity_window_starts_partway_between_two_samples():
    # Sparse touch events: the finger is placed where it was when the window began #
    samples = [(0.0, 300), (0.2, 200)]

    assert swipe_velocity(samples, now=0.2) == pytest.approx(-500)


def test_a_flick_back_isnt_averaged_with_the_drag_before_it():
    samples = [(0.0, 300), (0.1, 250), (0.2, 200), (0.21, 215), (0.22, 230)]

    assert swipe_velocity(samples, now=0.22) == pytest.approx(1500)


def test_a_finger_that_stopped_before_lifting_has_no_speed():
    samples = [(0.00, 300), (0.03, 250)]

    assert swipe_velocity(samples, now=0.30) == 0


def test_no_movement_has_no_speed():
    assert swipe_velocity([], now=1.0) == 0
    assert swipe_velocity([(1.0, 300)], now=1.0) == 0


## SLIDE-OUT TIME ##

def test_slide_out_picks_up_at_the_fingers_speed():
    # Out-quad easing starts at twice its average speed #
    duration = settle_duration(300, speed=3000, longest=MAX_SETTLE_DURATION)

    assert duration == pytest.approx(0.2)
    assert 2 * 300 / duration == pytest.approx(3000)


def test_slide_out_time_has_limits():
    assert settle_duration(300, speed=100000, longest=MAX_SETTLE_DURATION) == MIN_SETTLE_DURATION
    assert settle_duration(300, speed=500, longest=MAX_SETTLE_DURATION) == MAX_SETTLE_DURATION
    assert settle_duration(300, speed=0, longest=MAX_SETTLE_DURATION) == MAX_SETTLE_DURATION


## SWIPING ##

class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


@pytest.fixture
def swipe(kivy_window, monkeypatch):
    # A three-page carousel on its middle page, with a fake clock and recorded slide-outs #
    clock = Clock()
    monkeypatch.setattr(page_carousel, "monotonic", clock)

    animations = []

    class RecordingAnimation:
        def __init__(self, _offset, d, t):
            animations.append({"offset": _offset, "duration": d})

        def bind(self, **kwargs):
            pass

        def cancel_all(self, *args):
            pass

        def start(self, widget):
            pass

    monkeypatch.setattr(page_carousel, "Animation", RecordingAnimation)

    carousel = PageCarousel(size_hint=(None, None), size=(WIDTH, 600), pos=(0, 0))
    for i in range(3):
        carousel.add_widget(Label(text=f"Page {i}"))
    carousel.index = 1
    kivy_window.add_widget(carousel)

    def run(moves, start=300, hold=0.0, index=1):
        # `moves` are (seconds since the last move, x) steps; `hold` is a pause before lifting #
        carousel.index = index
        carousel._offset = 0
        touch = UnitTestTouch(start, 300)
        touch.touch_down()
        for seconds, x in moves:
            clock.now += seconds
            touch.touch_move(x, 300)
        clock.now += hold
        touch.touch_up()
        return animations[-1]

    run.carousel = carousel
    run.animations = animations
    yield run
    kivy_window.remove_widget(carousel)


def test_a_quick_short_flick_turns_the_page(swipe):
    # 45px in 30ms: too short to turn the page by distance alone #
    settled = swipe([(0.01, 285), (0.01, 270), (0.01, 255)])

    assert swipe.carousel._offset > -SWIPE_MIN_MOVE * WIDTH
    assert settled["offset"] == -WIDTH


def test_a_quick_flick_to_the_right_turns_back_a_page(swipe):
    settled = swipe([(0.01, 315), (0.01, 330), (0.01, 345)])

    assert settled["offset"] == WIDTH


def test_a_slow_short_drag_still_snaps_back(swipe):
    settled = swipe([(0.3, 285), (0.3, 270), (0.3, 255)])

    assert settled["offset"] == 0


def test_a_flick_that_stops_before_lifting_snaps_back(swipe):
    settled = swipe([(0.01, 285), (0.01, 270), (0.01, 255)], hold=0.3)

    assert settled["offset"] == 0


def test_a_slow_long_drag_still_turns_the_page(swipe):
    settled = swipe([(0.3, 250), (0.3, 200), (0.3, 150)], hold=0.3)

    assert settled["offset"] == -WIDTH


def test_flicking_back_partway_through_a_swipe_returns_to_the_page(swipe):
    settled = swipe([(0.1, 290), (0.1, 270), (0.1, 230), (0.1, 190), (0.1, 150), (0.01, 165), (0.01, 180), (0.01, 195)])

    assert swipe.carousel._offset < -SWIPE_MIN_MOVE * WIDTH
    assert settled["offset"] == 0


def test_flicking_past_the_last_page_snaps_back(swipe):
    settled = swipe([(0.01, 285), (0.01, 270), (0.01, 255)], index=2)

    assert settled["offset"] == 0


def test_a_fast_flick_slides_out_faster_than_before(swipe):
    # 3000px/s: Kivy took 0.5s no matter how fast the flick #
    settled = swipe([(0.01, 270), (0.01, 240), (0.01, 210)])

    remaining = WIDTH + swipe.carousel._offset
    assert settled["duration"] == pytest.approx(2 * remaining / 3000, rel=0.05)
    assert settled["duration"] < MAX_SETTLE_DURATION


def test_page_follows_the_finger_past_the_swipe_dead_zone(swipe):
    # One big 100px move starts the swipe; Kivy alone would leave the page where it was #
    swipe([(0.3, 200)], hold=0.3)

    assert swipe.carousel._offset == -100 + swipe.carousel.scroll_distance


def test_arrows_still_turn_the_page(swipe):
    swipe.carousel.load_next()
    swipe.carousel.load_previous()

    assert swipe.animations == [
        {"offset": -WIDTH, "duration": MAX_SETTLE_DURATION},
        {"offset": WIDTH, "duration": MAX_SETTLE_DURATION},
    ]


def test_a_real_flick_lands_on_the_next_page(kivy_window):
    # Real clock and animation, start to finish #
    from time import monotonic, sleep
    from kivy.clock import Clock as KivyClock

    carousel = PageCarousel(size_hint=(None, None), size=(WIDTH, 600), pos=(0, 0))
    for i in range(3):
        carousel.add_widget(Label(text=f"Page {i}"))
    kivy_window.add_widget(carousel)
    try:
        touch = UnitTestTouch(300, 300)
        touch.touch_down()
        for x in (285, 270, 255):
            sleep(0.005)
            touch.touch_move(x, 300)
        touch.touch_up()

        end = monotonic() + MIN_SETTLE_DURATION + 0.2
        while monotonic() < end:
            KivyClock.tick()
            sleep(0.01)

        assert carousel.index == 1
        assert carousel._offset == 0
    finally:
        kivy_window.remove_widget(carousel)
