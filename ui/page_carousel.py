from kivy.uix.carousel import Carousel

# A bit easier to swipe than Kivy's defaults (0.2 and 200ms) #
SWIPE_MIN_MOVE = 0.12      # Share of the width a drag must cover to turn the page; shorter drags snap back
SWIPE_TIMEOUT = 300        # Milliseconds a swipe has to get going before the touch goes to the page instead

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
            **kwargs
        )
