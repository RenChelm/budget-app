from datetime import datetime, timedelta

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp, sp

from budget_periods import (
    format_range,
    next_period_start,
    period_bounds,
    period_start,
    period_weeks,
    week_start,
    weekly_max_for,
)
from ui.choice_row import ChoiceRow
from ui.number_input import NumberInput

MODE_LABELS = {"monthly": "Monthly", "weekly": "Weekly"}
WEEKDAY_LABELS = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
BASE_HEIGHT = dp(350)   # Everything except the mode's own settings #

class BudgetPopup(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        settings = self.app.budget_settings
        current_start = period_bounds(datetime.now(), settings)[0]
        current_max = weekly_max_for(current_start, settings["weekly_max_history"])
        self.saved_long_week_max = weekly_max_for(current_start, settings["long_week_max_history"])

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        # Monthly splits each month (from the start day) into 4 weeks; weekly keeps every week 7 days #
        self.mode_choice = ChoiceRow(MODE_LABELS, value=settings["mode"], size_hint_y=None, height=dp(40))

        self.max_input_box = NumberInput(
            text=f"{current_max:.2f}" if current_max is not None else "",
            hint_text="Weekly Max (blank = no limit)",
            size_hint_y=None,
            height=dp(40)
        )

        self.start_day_input_box = NumberInput(
            decimal=False,
            text=str(settings["start_day"]),
            hint_text="Budget Start Day (1-31)",
            size_hint_y=None,
            height=dp(40)
        )

        # Monthly mode's last week runs 7-10 days, so it can have a bigger max #
        self.long_week_input_box = NumberInput(
            text=f"{self.saved_long_week_max:.2f}" if self.saved_long_week_max is not None else "",
            hint_text="Long Week Max (blank = weekly max)",
            size_hint_y=None,
            height=dp(40)
        )

        self.weekday_choice = ChoiceRow(WEEKDAY_LABELS, value=settings["start_weekday"], font_size=sp(13), size_hint_y=None, height=dp(40))

        # Only the settings for the chosen mode are shown #
        self.start_label = self._make_label("")
        self.long_week_label = self._make_label("Long Week Max ($)")
        self.mode_section = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)

        # Live preview of the period the start day produces; the end date is derived, not entered #
        self.period_label = Label(text="", color=(1, 1, 1, 1), halign="center", valign="middle", size_hint_y=None, height=dp(44))
        self.period_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        self.start_day_input_box.bind(text=lambda inst, val: self.update_period_preview())
        self.weekday_choice.bind(value=lambda inst, val: self.update_period_preview())
        self.mode_choice.bind(value=lambda inst, val: self.show_mode())

        save_btn = Button(text="Save", size_hint_y=None, height=dp(44), color=(1, 1, 1, 1))
        save_btn.bind(on_release=lambda x: self.save_budget())

        layout.add_widget(self._make_label("Budget Period"))
        layout.add_widget(self.mode_choice)
        layout.add_widget(self._make_label("Weekly Max ($)"))
        layout.add_widget(self.max_input_box)
        layout.add_widget(self.mode_section)
        layout.add_widget(self.period_label)
        layout.add_widget(save_btn)

        self.title = "Budget"
        self.title_color = (1, 1, 1, 1)
        self.content = layout
        self.size_hint = (0.8, None)
        self.show_mode()

    def _make_label(self, text):
        return Label(text=text, size_hint_y=None, height=dp(20), color=(1, 1, 1, 1))

    def show_mode(self):
        if self.mode_choice.value == "weekly":
            self.start_label.text = "Weeks Start On"
            widgets = [self.start_label, self.weekday_choice]
        else:
            self.start_label.text = "Budget Starts On Day"
            widgets = [self.start_label, self.start_day_input_box, self.long_week_label, self.long_week_input_box]

        self.mode_section.clear_widgets()
        for widget in widgets:
            self.mode_section.add_widget(widget)

        self.mode_section.height = sum(widget.height for widget in widgets) + self.mode_section.spacing * (len(widgets) - 1)
        self.height = BASE_HEIGHT + self.mode_section.height
        self.update_period_preview()

    def _parse_start_day(self):
        try:
            start_day = int(self.start_day_input_box.text.strip())
        except ValueError:
            return None
        return start_day if 1 <= start_day <= 31 else None

    def _parse_amount(self, box):
        # Blank means none; returns False when the text isn't an amount above $0 #
        text = box.text.strip()
        if not text:
            return None
        try:
            amount = float(text)
        except ValueError:
            return False
        return amount if amount > 0 else False

    def update_period_preview(self):
        if self.mode_choice.value == "weekly":
            start = week_start(datetime.now(), self.weekday_choice.value)
            self.period_label.text = f"This week:\n{format_range(start, start + timedelta(weeks=1))}"
            return

        start_day = self._parse_start_day()
        if start_day is None:
            self.period_label.text = "Start day must be 1-31"
            return

        start = period_start(datetime.now(), start_day)
        end = next_period_start(start, start_day)
        long_start, long_end = period_weeks(start, end)[-1]
        days = (long_end - long_start).days
        long_text = f"Long week: {format_range(long_start, long_end)} ({days} days)" if days > 7 else "No long week this period"
        self.period_label.text = f"Current period: {format_range(start, end)}\n{long_text}"

    def save_budget(self):
        monthly = self.mode_choice.value == "monthly"

        # Settings hidden for the other mode keep their saved value if they don't parse #
        start_day = self._parse_start_day()
        if start_day is None:
            if monthly:
                self.app.show_error("Start day must be\nbetween 1 and 31.")
                return
            start_day = self.app.budget_settings["start_day"]

        weekly_max = self._parse_amount(self.max_input_box)  # Blank means no limit #
        if weekly_max is False:
            self.app.show_error("Please enter a weekly\nmax above $0.")
            return

        long_week_max = self._parse_amount(self.long_week_input_box)  # Blank means the weekly max #
        if long_week_max is False:
            if monthly:
                self.app.show_error("Please enter a long week\nmax above $0.")
                return
            long_week_max = self.saved_long_week_max

        self.app.update_budget(
            {"mode": self.mode_choice.value, "start_day": start_day, "start_weekday": self.weekday_choice.value},
            weekly_max,
            long_week_max
        )
        self.dismiss()
