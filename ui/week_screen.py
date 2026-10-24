from budget_periods import format_range
from ui.back_screen import BackScreen
from ui.week_carousel import WeekCarousel

## WEEK SCREEN (OPENED BY TAPPING A WEEK IN HISTORY) ##

class WeekScreen(BackScreen):
    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)

        self.carousel = WeekCarousel(app)
        self.layout.add_widget(self.carousel)

    def show_period(self, start, end, week_index):
        self.title_label.text = format_range(start, end, with_year=True)
        self.carousel.show_period(start, end, week_index)

    def go_back(self):
        self.app.show_history()
