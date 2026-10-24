from datetime import date, datetime

from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.utils import platform

DATE_FORMAT = "%b %d, %Y"

## DATE FIELD (OPENS ANDROID'S DATE PICKER; TYPED ON DESKTOP) ##

class DateInput(TextInput):
    def __init__(self, day=None, **kwargs):
        super().__init__(multiline=False, **kwargs)
        self._listener = None
        self._text_before_edit = ""
        if day is not None:
            self.set_day(day)
        self.bind(focus=self.restore_if_cleared)

    def restore_if_cleared(self, instance, focused):
        # Clearing the field (desktop typing) keeps the date it had; only a new date replaces it #
        if focused:
            self._text_before_edit = self.text
        elif not self.text.strip():
            self.text = self._text_before_edit

    def set_day(self, day):
        self.text = day.strftime(DATE_FORMAT)

    def parse_day(self):
        # None when blank; otherwise raises ValueError with a message to show the user #
        text = self.text.strip()
        if not text:
            return None
        try:
            day = datetime.strptime(text, DATE_FORMAT).date()
        except ValueError:
            try:
                day = date.fromisoformat(text)  # Also accept YYYY-MM-DD when typing on desktop #
            except ValueError:
                raise ValueError("Please enter a valid date.") from None
        if day > date.today():
            raise ValueError("Date can't be in the future.")
        return day

    def on_touch_down(self, touch):
        # On Android a tap opens the native picker instead of the keyboard #
        if platform == "android" and self.collide_point(*touch.pos):
            self.open_date_picker()
            return True
        return super().on_touch_down(touch)

    def open_date_picker(self):
        try:
            initial = self.parse_day() or date.today()
        except ValueError:
            initial = date.today()

        Window.release_all_keyboards()
        self._listener = _DateSetListener(self._on_date_set)
        _show_date_picker(initial, self._listener)

    @mainthread
    def _on_date_set(self, year, month, day):
        self.set_day(date(year, month, day))

if platform == "android":
    from jnius import PythonJavaClass, autoclass, java_method
    from android import mActivity
    from android.runnable import run_on_ui_thread

    class _DateSetListener(PythonJavaClass):
        __javainterfaces__ = ["android/app/DatePickerDialog$OnDateSetListener"]
        __javacontext__ = "app"

        def __init__(self, callback):
            super().__init__()
            self.callback = callback

        @java_method("(Landroid/widget/DatePicker;III)V")
        def onDateSet(self, view, year, month, day):
            self.callback(year, month + 1, day)  # Java months are 0-based #

    @run_on_ui_thread
    def _show_date_picker(initial, listener):
        # The app's own theme is pre-Material, so ask for the device's dialog theme #
        style = autoclass("android.R$style")
        theme = getattr(style, "Theme_DeviceDefault_Dialog_Alert", style.Theme_Material_Dialog_Alert)

        dialog = autoclass("android.app.DatePickerDialog")(
            mActivity, theme, listener, initial.year, initial.month - 1, initial.day
        )
        # Transactions have already happened, so future days can't be picked #
        dialog.getDatePicker().setMaxDate(autoclass("java.lang.System").currentTimeMillis())
        dialog.show()
