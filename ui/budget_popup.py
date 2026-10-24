from datetime import datetime

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp

from budget_periods import format_range, next_period_start, period_start, weekly_max_for
from ui.number_input import NumberInput

class BudgetPopup(Popup):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        settings = self.app.budget_settings
        current_max = weekly_max_for(period_start(datetime.now(), settings["start_day"]), settings["weekly_max_history"])

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

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

        # Live preview of the period the start day produces; the end date is derived, not entered #
        self.period_label = Label(text="", color=(1, 1, 1, 1), halign="center", valign="middle", size_hint_y=None, height=dp(44))
        self.period_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        self.start_day_input_box.bind(text=lambda inst, val: self.update_period_preview())
        self.update_period_preview()

        save_btn = Button(text="Save", size_hint_y=None, height=dp(44), color=(1, 1, 1, 1))
        save_btn.bind(on_release=lambda x: self.save_budget())

        layout.add_widget(Label(text="Weekly Max ($)", size_hint_y=None, height=dp(20), color=(1, 1, 1, 1)))
        layout.add_widget(self.max_input_box)
        layout.add_widget(Label(text="Budget Starts On Day", size_hint_y=None, height=dp(20), color=(1, 1, 1, 1)))
        layout.add_widget(self.start_day_input_box)
        layout.add_widget(self.period_label)
        layout.add_widget(save_btn)

        self.title = "Budget"
        self.title_color = (1, 1, 1, 1)
        self.content = layout
        self.size_hint = (0.8, None)
        self.height = dp(340)

    def _parse_start_day(self):
        try:
            start_day = int(self.start_day_input_box.text.strip())
        except ValueError:
            return None
        return start_day if 1 <= start_day <= 31 else None

    def update_period_preview(self):
        start_day = self._parse_start_day()
        if start_day is None:
            self.period_label.text = "Start day must be 1-31"
            return

        start = period_start(datetime.now(), start_day)
        self.period_label.text = f"Current period:\n{format_range(start, next_period_start(start, start_day))}"

    def save_budget(self):
        start_day = self._parse_start_day()
        if start_day is None:
            self.app.show_error("Start day must be\nbetween 1 and 31.")
            return

        value_max = self.max_input_box.text.strip()
        weekly_max = None  # Blank means no limit #
        if value_max:
            try:
                weekly_max = float(value_max)
            except ValueError:
                pass
            if weekly_max is None or weekly_max <= 0:
                self.app.show_error("Please enter a weekly\nmax above $0.")
                return

        self.app.update_budget(start_day, weekly_max)
        self.dismiss()
