from datetime import datetime

from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.metrics import dp, sp

from budget_periods import format_money, format_period, history_periods
from ui.back_screen import BackScreen
from ui.carry_over_button import CarryOverButton
from ui.page_carousel import PageCarousel
from ui.week_row import WeekRow

## ONE BUDGET PERIOD (HEADER + 4-5 WEEK ROWS + NEIGHBOR HINTS) ##

class PeriodPage(BoxLayout):
    def __init__(self, period, previous_period=None, next_period=None, on_week_tap=None, on_carry_over=None, mode="monthly", **kwargs):
        super().__init__(orientation="vertical", padding=[dp(12), dp(14)], spacing=dp(10), **kwargs)
        self.period = period

        weeks = period["weeks"]
        weekly_max = period["weekly_max"]
        spent = sum(week["spent"] for week in weeks)

        ## HEADER ##

        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(76))

        self.title_label = self._make_header_label(format_period(period["start"], period["end"], mode, with_year=True), sp(18), bold=True)

        if weekly_max is None:
            self.total_label = self._make_header_label(f"${spent:.2f} spent", sp(14))
        else:
            self.total_label = self._make_header_label(f"${spent:.2f} of {format_money(period['budget'])} · ${weekly_max:.2f}/week", sp(14))

        self.summary_label = self._make_header_label(self._summary_text(weeks, weekly_max), sp(14))

        header.add_widget(self.title_label)
        header.add_widget(self.total_label)

        # Monthly mode: explains a total raised or lowered by last month's amount, since its button is on last month's page #
        self.last_month_label = None
        carried_in = round(period["carried_in"], 2)
        if carried_in != 0:
            text = f"Last month's ${carried_in:.2f} leftover added" if carried_in > 0 else f"Last month's ${-carried_in:.2f} overspend subtracted"
            self.last_month_label = self._make_header_label(text, sp(13))
            header.add_widget(self.last_month_label)
            header.height += dp(25)

        header.add_widget(self.summary_label)

        # In monthly mode, what was left (or overspent) this month can be added to (or subtracted from) next month #
        carry_over = period["carry_over"]
        self.carry_btn = None
        if carry_over is not None and on_carry_over is not None:
            self.carry_btn = CarryOverButton(carry_over, unit="month", size_hint=(0.9, None), height=dp(28))
            self.carry_btn.bind(on_release=lambda inst: on_carry_over(period, not carry_over["carried"]))

            carry_row = AnchorLayout(size_hint_y=None, height=dp(38))
            carry_row.add_widget(self.carry_btn)
            header.add_widget(carry_row)
            header.height += carry_row.height

        self.add_widget(header)

        ## WEEK ROWS ##

        # Tapping a week opens its transactions #
        self.week_rows = []
        for number, week in enumerate(weeks, start=1):
            row = WeekRow(week, number, on_carry_over=on_carry_over)
            if on_week_tap is not None:
                row.bind(on_release=lambda inst, i=number - 1: on_week_tap(period, i))
            self.week_rows.append(row)
            self.add_widget(row)

        ## NEIGHBOR HINTS ##

        hints = BoxLayout(size_hint_y=None, height=dp(24))
        self.older_label = self._make_hint_label(
            f"‹ {format_period(previous_period['start'], previous_period['end'], mode)}" if previous_period else "", "left"
        )
        self.newer_label = self._make_hint_label(
            f"{format_period(next_period['start'], next_period['end'], mode)} ›" if next_period else "", "right"
        )
        hints.add_widget(self.older_label)
        hints.add_widget(self.newer_label)
        self.add_widget(hints)

        self.add_widget(Widget())  # Spacer #

    def _summary_text(self, weeks, weekly_max):
        if weekly_max is None:
            return "Set a weekly max with View Budget"

        current = next((week for week in weeks if week["status"] == "current"), None)
        if current is not None:
            if current["left"] < 0:
                return f"This week: ${-current['left']:.2f} over"
            per_day = current["left"] / current["days_left"]
            days = f"{current['days_left']} day" + ("" if current["days_left"] == 1 else "s")
            return f"This week: ${per_day:.2f}/day · {days} left"

        weeks_over = sum(1 for week in weeks if week["left"] < 0)
        if weeks_over == 0:
            return "Under budget every week"
        return f"Over budget in {weeks_over} of {len(weeks)} weeks"

    def _make_header_label(self, text, font_size, bold=False):
        label = Label(text=text, font_size=font_size, bold=bold, halign="center", valign="middle", color=(1, 1, 1, 1))
        label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        return label

    def _make_hint_label(self, text, halign):
        label = Label(text=text, font_size=sp(13), halign=halign, valign="middle", color=(1, 1, 1, 0.6))
        label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        return label

## HISTORY SCREEN (SWIPE RIGHT FOR OLDER PERIODS) ##

class HistoryScreen(BackScreen):
    def __init__(self, app, **kwargs):
        super().__init__(app, title="History", **kwargs)

        ## PERIOD PAGES ##

        self.carousel = PageCarousel()
        self.layout.add_widget(self.carousel)

    def refresh(self, now=None, open_start=None):
        settings = self.app.budget_settings
        periods = history_periods(self.app.saved_amounts, settings, now or datetime.now())

        self.carousel.clear_widgets()
        for i, period in enumerate(periods):
            self.carousel.add_widget(PeriodPage(
                period,
                previous_period=periods[i - 1] if i > 0 else None,
                next_period=periods[i + 1] if i + 1 < len(periods) else None,
                on_week_tap=lambda tapped, week_index: self.app.open_week(tapped["start"], tapped["end"], week_index),
                on_carry_over=self.app.set_carry_over,
                mode=settings["mode"]
            ))

        # Opens on the current period unless asked for another (e.g. coming back from one of its weeks) #
        starts = [period["start"] for period in periods]
        self.carousel.index = starts.index(open_start) if open_start in starts else len(periods) - 1

    def go_back(self):
        self.app.show_main()
