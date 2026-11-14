from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.graphics import Color, Rectangle
from kivy.logger import Logger
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivy.utils import platform

## LETS THE APP DRAW BEHIND ANDROID'S STATUS BAR, CAMERA AND GESTURE BAR ##

class SafeArea(EventDispatcher):
    # How far the status bar and camera (top) and the gesture bar (bottom) reach into the window, in pixels #
    # Both stay 0 until the app is drawing behind them #
    top = NumericProperty(0)
    bottom = NumericProperty(0)

safe_area = SafeArea()


def draw_edge_to_edge():
    # Android 11+ only; older phones keep the normal status bar #
    # Anything that goes wrong is logged and leaves the normal status bar instead of crashing the app #
    if platform != "android":
        return

    try:
        from jnius import autoclass
        from android import mActivity
        from android.runnable import run_on_ui_thread

        if autoclass("android.os.Build$VERSION").SDK_INT < 30:
            return
    except Exception:
        Logger.exception("EdgeToEdge: Couldn't check the Android version")
        return

    # Window changes have to be made on Android's UI thread #
    @run_on_ui_thread
    def apply():
        try:
            LayoutParams = autoclass("android.view.WindowManager$LayoutParams")
            window = mActivity.getWindow()

            attrs = window.getAttributes()
            attrs.layoutInDisplayCutoutMode = LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            window.setAttributes(attrs)

            # The app's theme predates Android coloring its own bars, so that's turned on before making them see-through #
            window.clearFlags(LayoutParams.FLAG_TRANSLUCENT_STATUS | LayoutParams.FLAG_TRANSLUCENT_NAVIGATION)
            window.addFlags(LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)
            transparent = autoclass("android.graphics.Color").TRANSPARENT
            window.setStatusBarColor(transparent)
            window.setNavigationBarColor(transparent)
            window.setNavigationBarContrastEnforced(False)  # No gray band behind the gesture bar #

            # Last, so the app only moves behind the bars once everything above worked #
            # SDL keeps resetting Android's older full screen flags, but this newer switch isn't tied to them #
            window.setDecorFitsSystemWindows(False)
        except Exception:
            Logger.exception("EdgeToEdge: Couldn't draw behind the system bars")
            return
        _follow_safe_area()

    apply()


_following = False

@mainthread
def _follow_safe_area():
    # Android only knows the bars' sizes once the window is laid out, and laying it out behind them resizes it #
    global _following
    if not _following:
        _following = True
        Window.bind(on_resize=_on_window_resize)
    update_safe_area()


def _on_window_resize(*args):
    update_safe_area()


def update_safe_area():
    try:
        from jnius import autoclass
        from android import mActivity

        insets = mActivity.getWindow().getDecorView().getRootWindowInsets()
        if insets is None:  # Not laid out yet; the window resizing calls this again #
            return
        Type = autoclass("android.view.WindowInsets$Type")
        bars = insets.getInsets(Type.systemBars() | Type.displayCutout())
    except Exception:
        Logger.exception("EdgeToEdge: Couldn't read the system bar sizes")
        return

    safe_area.top = bars.top
    safe_area.bottom = bars.bottom


## STRIP BEHIND A SYSTEM BAR ##

class SafeAreaStrip(Widget):
    # Keeps the screens clear of a system bar, colored to match what sits next to it; 0 tall until edge to edge is on #
    # Can also draw a thinner bar across its middle, e.g. for the gesture handle to sit on #
    def __init__(self, side, color, bar_color=None, bar_height=0, **kwargs):
        super().__init__(size_hint_y=None, height=getattr(safe_area, side), **kwargs)
        self.bar_height = bar_height
        self.bar = None

        with self.canvas.before:
            Color(*color)
            self.rect = Rectangle()
            if bar_color is not None:
                Color(*bar_color)
                self.bar = Rectangle()

        self.bind(pos=self._redraw, size=self._redraw)
        safe_area.bind(**{side: lambda i, value: setattr(self, "height", value)})
        self._redraw()

    def _redraw(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        if self.bar is not None:
            height = min(self.bar_height, self.height)  # Hidden along with the strip off Android #
            self.bar.pos = (self.x, self.y + (self.height - height) / 2)   # center_y isn't updated yet when size changes #
            self.bar.size = (self.width, height)
