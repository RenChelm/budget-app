from kivy.uix.textinput import TextInput
from kivy.utils import platform

## TEXT BOX (TAPPING IT AGAIN REOPENS A HIDDEN ANDROID KEYBOARD) ##

class TextBox(TextInput):
    def on_touch_down(self, touch):
        # Android's hide-keyboard button closes the keyboard without telling Kivy, so the box keeps focus #
        # and tapping it again did nothing; refocusing asks Android for the keyboard again #
        if platform == "android" and self.focus and self.collide_point(*touch.pos) and not keyboard_visible():
            self.focus = False
            self.focus = True
        return super().on_touch_down(touch)

def keyboard_visible():
    from jnius import autoclass
    from android import mActivity

    # Android 10 and older can't report it, so assume hidden (an open keyboard just flickers) #
    if autoclass("android.os.Build$VERSION").SDK_INT < 30:
        return False
    insets = mActivity.getWindow().getDecorView().getRootWindowInsets()
    return insets is not None and insets.isVisible(autoclass("android.view.WindowInsets$Type").ime())
