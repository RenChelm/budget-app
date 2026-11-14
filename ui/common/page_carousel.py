import math
from time import monotonic

from kivy.animation import Animation
from kivy.metrics import dp
from kivy.uix.carousel import Carousel

# A bit easier to swipe than Kivy's defaults (0.2 and 200ms) #
SWIPE_MIN_MOVE = 0.12      # Share of the width a slow drag must cover to turn the page; shorter drags snap back
SWIPE_TIMEOUT = 300        # Milliseconds a swipe has to get going before the touch goes to the page instead

# Like Android's own pages, a quick flick turns the page however short it was #
FLING_VELOCITY = dp(400)   # Per second, measured over the last moment before the finger lifts
VELOCITY_WINDOW = 0.1      # Seconds of movement the speed is measured over; a finger that stopped first has none

# The page finishes sliding at the finger's speed, within these limits (Kivy's fixed 0.5s capped fast flicks) #
MIN_SETTLE_DURATION = 0.1
MAX_SETTLE_DURATION = 0.3

def swipe_velocity(samples, now, window=VELOCITY_WINDOW):
    # Pixels per second over the last `window` seconds of (time, position) samples #
    if not samples:
        return 0

    # Only the finger's latest run in one direction counts, so a flick back isn't averaged with the drag before it #
    first, heading = len(samples) - 1, 0
    while first > 0:
        delta = samples[first][1] - samples[first - 1][1]
        if delta and heading and (delta > 0) != (heading > 0):
            break
        heading = heading or delta
        first -= 1
    run = samples[first:]

    # Where the finger was when the window began, between the samples either side of it #
    window_start = now - window
    i = next((i for i, (t, pos) in enumerate(run) if t >= window_start), len(run) - 1)
    t0, start = run[i]
    if i > 0 and t0 > window_start:
        t_before, before = run[i - 1]
        start = before + (start - before) * (window_start - t_before) / (t0 - t_before)
        t0 = window_start

    end = samples[-1][1]
    return (end - start) / (now - t0) if now > t0 else 0

def settle_duration(distance, speed, longest):
    # Out-quad easing starts at twice its average speed, so this picks up at the finger's speed and slows to a stop #
    if speed <= 0:
        return longest
    return min(max(2 * distance / speed, MIN_SETTLE_DURATION), longest)

## SWIPEABLE PAGES, WITH THE SAME SWIPE FEEL EVERYWHERE IN THE APP ##

class PageCarousel(Carousel):
    def __init__(self, **kwargs):
        # Swiping still needs Kivy's 20dp of sideways movement, so wobbly taps don't turn pages #
        # Mostly-vertical drags are handed to the page so lists still scroll #
        super().__init__(
            direction="right",
            min_move=SWIPE_MIN_MOVE,
            scroll_timeout=SWIPE_TIMEOUT,
            ignore_perpendicular_swipes=True,
            anim_move_duration=MAX_SETTLE_DURATION,
            **kwargs
        )

    def _position(self, touch):
        return touch.x if self.direction[0] in "rl" else touch.y

    def _samples(self, touch):
        return touch.ud.setdefault(self._get_uid("samples"), [])

    def on_touch_down(self, touch):
        handled = super().on_touch_down(touch)
        if self._touch is touch:
            self._samples(touch).append((monotonic(), self._position(touch)))
        return handled

    def on_touch_move(self, touch):
        ud = touch.ud.get(self._get_uid())
        starting = self._touch is touch and ud is not None and ud["mode"] == "unknown"
        if self._touch is touch:
            self._samples(touch).append((monotonic(), self._position(touch)))

        handled = super().on_touch_move(touch)

        # Kivy drops the whole move that starts a swipe; keep what went past the 20dp it needs, so the page #
        # follows the finger no matter how big that move was #
        if starting and ud["mode"] == "scroll":
            moved = self._position(touch) - (touch.ox if self.direction[0] in "rl" else touch.oy)
            self._offset += moved - math.copysign(self.scroll_distance, moved)
        return handled

    def on_touch_up(self, touch):
        # A swipe ending settles with the finger's speed; everything else (taps, other touches) is Kivy's as usual #
        ud = touch.ud.get(self._get_uid())
        swiping = self._touch is touch and ud is not None and ud["mode"] == "scroll"
        if not swiping or self not in [ref() for ref in touch.grab_list]:
            return super().on_touch_up(touch)

        samples = self._samples(touch)
        now = monotonic()
        samples.append((now, self._position(touch)))

        touch.ungrab(self)
        self._touch = None
        self._start_animation(velocity=swipe_velocity(samples, now))
        return True

    def _start_animation(self, *args, velocity=0, **kwargs):
        # Kivy's version, but a flick turns the page and the page keeps the flick's speed #
        # `velocity` is in pixels per second along the swipe; the page moves the same way as the finger #
        direction = kwargs.get("direction", self.direction)[0]
        extent = self.width if direction in "rl" else self.height
        min_move = kwargs.get("min_move", self.min_move)
        offset = kwargs.get("offset", self._offset)

        if abs(velocity) >= FLING_VELOCITY:
            # Flicked toward the page that's partly showing, it turns; flicked back, it returns #
            if velocity < 0:
                new_offset = -extent if offset <= 0 else 0
            else:
                new_offset = extent if offset >= 0 else 0
        elif offset < min_move * -extent:
            new_offset = -extent
        elif offset > min_move * extent:
            new_offset = extent
        else:
            new_offset = 0

        # The first and last pages have nothing past them #
        towards_next = new_offset < 0 if direction in "rt" else new_offset > 0
        towards_prev = new_offset > 0 if direction in "rt" else new_offset < 0
        if not self.loop or len(self.slides) == 1:
            if (self.index == 0 and towards_prev) or (self.index == len(self.slides) - 1 and towards_next):
                new_offset = 0

        # Only speed toward where the page is going carries over #
        distance = new_offset - self._offset
        speed = abs(velocity) if distance and math.copysign(1, velocity) == math.copysign(1, distance) else 0
        longest = self.anim_move_duration if new_offset else self.anim_cancel_duration

        anim = Animation(_offset=new_offset, d=settle_duration(abs(distance), speed, longest), t=self.anim_type)
        anim.cancel_all(self)

        def _cmp(*l):
            if self._skip_slide is not None:
                self.index = self._skip_slide
                self._skip_slide = None

        anim.bind(on_complete=_cmp)
        anim.start(self)
