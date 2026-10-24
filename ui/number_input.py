from kivy.clock import Clock
from kivy.utils import platform

from ui.text_box import TextBox

# android.text.InputType flags #
TYPE_CLASS_NUMBER = 2
TYPE_NUMBER_FLAG_DECIMAL = 8192

## NUMERIC TEXT INPUT (OPENS THE NUMBER PAD ON ANDROID) ##

class NumberInput(TextBox):
    def __init__(self, decimal=True, **kwargs):
        super().__init__(
            input_type="number",
            input_filter="float" if decimal else "int",
            multiline=False,
            **kwargs
        )
        self.decimal = decimal
        self.bind(focus=self.on_number_focus)

    def on_number_focus(self, instance, focused):
        # Kivy's "number" pad has no decimal key on some keyboards (e.g. Samsung) #
        # Swap in the decimal pad on the next frame, after Kivy has opened its own #
        if focused and self.decimal and platform == "android":
            Clock.schedule_once(lambda dt: self.request_decimal_keyboard())

    def request_decimal_keyboard(self):
        from android import mActivity
        mActivity.changeKeyboard(TYPE_CLASS_NUMBER | TYPE_NUMBER_FLAG_DECIMAL)
