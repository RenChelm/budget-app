from datetime import datetime

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.carousel import Carousel
from kivy.uix.label import Label
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.metrics import dp, sp

from budget_periods import WEEKS_PER_PERIOD, format_range, period_weeks
from ui.chevron_button import ChevronButton
from ui.entry_row import EntryRow

## ONE WEEK OF TRANSACTIONS (HEADER STRIP + LIST) ##

class WeekTransactionsPage(BoxLayout):
    def __init__(self, carousel, number, start, end, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.number = number
        self.start = start
        self.end = end

        ## HEADER STRIP (ARROWS ALSO CHANGE WEEK) ##

        header = BoxLayout(size_hint_y=None, height=dp(34))

        self.prev_btn = self._make_arrow("left", carousel.load_previous, visible=number > 1)
        self.title_label = Label(font_size=sp(15), bold=True, color=(1, 1, 1, 1))
        self.next_btn = self._make_arrow("right", carousel.load_next, visible=number < WEEKS_PER_PERIOD)

        header.add_widget(self.prev_btn)
        header.add_widget(self.title_label)
        header.add_widget(self.next_btn)
        self.add_widget(header)

        ## TRANSACTION LIST ##

        self.rv = RecycleView(do_scroll_x=False)

        layout = RecycleBoxLayout(
            default_size=(None, None),
            default_size_hint=(1, None),
            size_hint=(1, None),
            orientation='vertical'
        )
        layout.bind(minimum_height=layout.setter('height'))

        self.rv.add_widget(layout)
        self.rv.layout_manager = layout
        self.rv.viewclass = EntryRow
        self.rv.data = []

        self.add_widget(self.rv)

    def _make_arrow(self, pointing, action, visible):
        # Hidden (not removed) on the first/last week so the title stays centered #
        arrow = ChevronButton(
            pointing=pointing,
            size_hint_x=None,
            width=dp(44),
            disabled=not visible,
            opacity=1 if visible else 0
        )
        arrow.bind(on_release=lambda x: action())
        return arrow

    def refresh(self, app, now):
        name = "This Week" if self.start <= now < self.end else f"Week {self.number}"
        self.title_label.text = f"{name} · {format_range(self.start, self.end)}"
        self.rv.data = app.transaction_rows(self.start, self.end, upcoming=now < self.start)

## THE 4 WEEKS OF ONE BUDGET PERIOD (SWIPE BETWEEN WEEKS) ##

class WeekCarousel(Carousel):
    def __init__(self, app, **kwargs):
        # Mostly-vertical drags are handed to the list so it still scrolls #
        super().__init__(direction="right", ignore_perpendicular_swipes=True, **kwargs)
        self.app = app
        self.period = None

    def show_period(self, start, end, week_index=None, now=None):
        now = now or datetime.now()
        self.period = (start, end)

        self.clear_widgets()
        for number, (week_start, week_end) in enumerate(period_weeks(start, end), start=1):
            self.add_widget(WeekTransactionsPage(self, number, week_start, week_end))

        self.refresh(now)
        self.index = week_index if week_index is not None else self.week_index_for(now)

    def refresh(self, now=None):
        now = now or datetime.now()
        for page in self.slides:
            page.refresh(self.app, now)

    def week_index_for(self, moment):
        for i, page in enumerate(self.slides):
            if page.start <= moment < page.end:
                return i
        return len(self.slides) - 1 if moment >= self.period[1] else 0
