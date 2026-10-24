import json
import os

from kivy.config import Config
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '800')

from kivy.app import App
from kivy.core.window import Window

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp

from datetime import datetime

from ui.add_transaction_popup import AddTransactionPopup
from ui.edit_transaction_popup import EditTransactionPopup
from ui.category_select_popup import CategorySelectPopup
from ui.sort_controls import SortControls
from ui.menu_button import MenuButton
from ui.history_screen import HistoryScreen
from ui.week_carousel import WeekCarousel
from ui.week_screen import WeekScreen
from ui.budget_popup import BudgetPopup
from ui.color_utils import contrast_color

from budget_periods import next_period_start, period_start, set_weekly_max, summarize_week, weekly_max_for

class BudgetApp(App):
    def build(self):

        # Android moves the app up so the text box being typed in stays above the keyboard #
        Window.softinput_mode = "below_target"

        self.saved_amounts = []
        self.saved_categories = []
        self.sort_by = "date"
        self.sort_descending = True
        self.transactions_file = os.path.join(self.user_data_dir, "transactions.json")
        self.categories_file = os.path.join(self.user_data_dir, "categories.json")
        self.budget_file = os.path.join(self.user_data_dir, "budget.json")

        # Load saved entries from file #
        try:
            with open(self.transactions_file, "r") as f:
                content = f.read().strip()
                if content:
                    self.saved_amounts = json.loads(content)

                    # Convert timestamp strings back to datetime objects #
                    for entry in self.saved_amounts:
                        if isinstance(entry.get("timestamp"), str):
                            entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])
                else:
                    self.saved_amounts = []
        except (FileNotFoundError, json.JSONDecodeError):
            self.saved_amounts = []

        try:
            with open(self.categories_file, "r") as f:
                content = f.read().strip()
                if content:
                    self.saved_categories = json.loads(content)

                else:
                    self.saved_categories = []
        except (FileNotFoundError, json.JSONDecodeError):
            self.saved_categories = []

        # Defaults to calendar months with no weekly max until the user sets one #
        self.budget_settings = {"start_day": 1, "weekly_max_history": []}
        try:
            with open(self.budget_file, "r") as f:
                content = f.read().strip()
                if content:
                    self.budget_settings.update(json.loads(content))

                    for change in self.budget_settings["weekly_max_history"]:
                        if isinstance(change.get("from"), str):
                            change["from"] = datetime.fromisoformat(change["from"])
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        root = BoxLayout(orientation="vertical")

        with root.canvas.before:
            Color(0.125, 0.259, 0.188, 1)  # Forest Green
            self.bg_rect = Rectangle(pos=root.pos, size=root.size)

        root.bind(
            pos=lambda i, v: setattr(self.bg_rect, "pos", i.pos),
            size=lambda i, v: setattr(self.bg_rect, "size", i.size)
        )

        ## TOP BAR ##

        top_bar = FloatLayout(size_hint=(1, 0.1))

        top_bar.canvas.before.clear()
        with top_bar.canvas.before:
            Color(0.192, 0.4, 0.29, 1)  # Seafoam Green  
            
            self.top_rect = Rectangle(pos=top_bar.pos, size=top_bar.size)

        top_bar.bind(pos = lambda i, v: setattr(self.top_rect, 'pos', i.pos),
                     size = lambda i, v: setattr(self.top_rect, 'size', i.size))

        # Title is its own layer so it stays centered on any screen width #
        top_bar.add_widget(Label(
            text="Transactions",
            font_size=sp(20),
            color=(1, 1, 1, 1),
            pos_hint={"center_x": 0.5, "center_y": 0.5}
        ))

        top_bar_controls = BoxLayout(
            pos_hint={"x": 0, "y": 0},
            padding=[dp(6), dp(10)]
        )
        top_bar_controls.add_widget(SortControls(self, size_hint=(None, 1), width=dp(110)))
        top_bar_controls.add_widget(Widget())  # Spacer #
        top_bar_controls.add_widget(MenuButton(size_hint=(None, 1), width=dp(36)))
        top_bar.add_widget(top_bar_controls)

        root.add_widget(top_bar)

        ## MAIN CONTENT AREA ##
        
        main = FloatLayout()

        # The weeks of the current budget period; swipe sideways to change week #
        self.week_carousel = WeekCarousel(
            self,
            size_hint=(1, 0.7),
            pos_hint={"center_y": 0.63}
        )

        main.add_widget(self.week_carousel)

        ## BOTTOM DIVIDER ##

        divider_bot = Widget(
            size_hint=(1, None),
            height=dp(9),
            pos_hint={"y": 0.264}
        )
        with divider_bot.canvas.before:
            Color(0.8, 0.8, 0.8, 1)  # Light Gray
            divider_bot.rect = Rectangle(pos=divider_bot.pos, size=divider_bot.size)

        divider_bot.bind(
            pos=lambda inst, val: setattr(inst.rect, "pos", inst.pos),
            size=lambda inst, val: setattr(inst.rect, "size", inst.size)
        )
        main.add_widget(divider_bot)

        ## TOP DIVIDER ##

        divider_top = Widget(
            size_hint=(1, None),
            height=dp(9),
            pos_hint={"y": 0.984}
        )
        with divider_top.canvas.before:
            Color(0.8, 0.8, 0.8, 1)  # Light Gray
            divider_top.rect = Rectangle(pos=divider_top.pos, size=divider_top.size)

        divider_top.bind(
            pos=lambda inst, val: setattr(inst.rect, "pos", inst.pos),
            size=lambda inst, val: setattr(inst.rect, "size", inst.size)
        )
        main.add_widget(divider_top)


        ## BOTTOM CENTER INFO PANEL ##

        info_panel = BoxLayout(
            orientation="vertical",
            size_hint=(0.5, None),
            height=dp(185),
            pos_hint={"center_x": 0.5, "y": 0.005},
            spacing=dp(5)
        )

        ## BOTTOM LEFT BUTTON CLUSTER ##

        btn_cluster_left = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(90),
            pos_hint={"x": 0.01, "y": 0.005},
            spacing=dp(3)
        )

        ## VIEW HISTORY BUTTON ##

        btn_history = Button(
            text="View\nHistory",
            halign="center",
            valign="middle",
            background_normal="",
            background_color=(0.51765, 0.878, 0.737, 1),
            color=(0, 0, 0, 1),
            size_hint=(1, None),
            height=dp(91),
            on_release=self.open_history
        )

        ## VIEW BUDGET BUTTON ##

        btn_budget = Button(
            text="View\nBudget",
            halign="center",
            valign="middle",
            background_normal="",
            background_color=(0.51765, 0.878, 0.737, 1),
            color=(0, 0, 0, 1),
            size_hint=(1, None),
            height=dp(91),
            on_release=lambda x: BudgetPopup(self).open()
        )

        # Center text #
        btn_history.text_size = btn_history.size
        btn_history.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        btn_budget.text_size = btn_budget.size
        btn_budget.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))

        btn_cluster_left.add_widget(btn_history)
        btn_cluster_left.add_widget(btn_budget)
        main.add_widget(btn_cluster_left)

        # Stats for whichever week is showing #
        self.spent_label = Label(text="Spent: $0.00", halign="center", valign="middle", color=(1, 1, 1, 1))
        self.spent_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        self.left_label = Label(text="", halign="center", valign="middle", color=(1, 1, 1, 1))
        self.left_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        self.trans_label = Label(text="Transactions: 0", halign="center", valign="middle", color=(1, 1, 1, 1))
        self.trans_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))

        info_panel.add_widget(self.spent_label)
        info_panel.add_widget(self.left_label)
        info_panel.add_widget(self.trans_label)

        self.week_carousel.bind(index=lambda inst, val: self.update_info_panel())

        main.add_widget(info_panel)

        ## BOTTOM RIGHT BUTTON CLUSTER ##

        btn_cluster = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(90),
            pos_hint={"right": 0.99, "y": 0.005},
            spacing=dp(3)
        )

        ## ADD BUTTON ##

        btn_add = Button(
            text="Add",
            halign="center",
            valign="middle",
            background_normal="",
            background_color=(0.51765, 0.878, 0.737, 1),
            color=(0, 0, 0, 1),
            size_hint=(1, None),
            height=dp(91),
            on_release=self.open_transaction_window
        )

        ## CATEGORIES BUTTON ##

        btn_categories = Button(
            text="Categories",
            halign="center",
            valign="middle",
            background_normal="",
            background_color=(0.51765, 0.878, 0.737, 1),
            color=(0, 0, 0, 1),
            size_hint=(1, None),
            height=dp(91),
            on_release=lambda x: CategorySelectPopup(self).open()
        )

        # Center text #
        btn_add.text_size = btn_add.size
        btn_add.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        btn_categories.text_size = btn_categories.size
        btn_categories.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))

        btn_cluster.add_widget(btn_add)
        btn_cluster.add_widget(btn_categories)
        main.add_widget(btn_cluster)

        root.add_widget(main)

        ## SCREENS ##

        self.screen_manager = ScreenManager()

        main_screen = Screen(name="main")
        main_screen.add_widget(root)
        self.screen_manager.add_widget(main_screen)

        self.history_screen = HistoryScreen(self, name="history")
        self.screen_manager.add_widget(self.history_screen)

        self.week_screen = WeekScreen(self, name="week")
        self.screen_manager.add_widget(self.week_screen)

        self.update_display()

        return self.screen_manager

    def on_start(self):
        Window.bind(on_keyboard=self.on_back_key)

    def on_resume(self):
        # The app may have been in the background across a week boundary #
        self.update_display()
        self.show_current_week()

    ## SCREEN NAVIGATION - METHODS ##

    def go_to_screen(self, name, direction):
        self.screen_manager.transition.direction = direction
        self.screen_manager.current = name

    def open_history(self, instance=None):
        self.history_screen.refresh()
        self.go_to_screen("history", "left")

    def open_week(self, start, end, week_index):
        self.week_screen.show_period(start, end, week_index)
        self.go_to_screen("week", "left")

    def show_history(self, *args):
        # Returns to the period the week came from, not the current one #
        self.history_screen.refresh(open_start=self.week_screen.carousel.period[0])
        self.go_to_screen("history", "right")

    def show_main(self, *args):
        self.go_to_screen("main", "right")

    def show_current_week(self, now=None):
        self.week_carousel.index = self.week_carousel.week_index_for(now or datetime.now())

    def show_week_of(self, moment):
        # The main page only holds the current period's weeks #
        start, end = self.week_carousel.period
        if start <= moment < end:
            self.week_carousel.index = self.week_carousel.week_index_for(moment)

    def on_back_key(self, window, key, *args):
        # Android back button (Esc on desktop) steps back a screen instead of closing the app #
        if key == 27 and self.screen_manager.current != "main":
            self.screen_manager.current_screen.go_back()
            return True
        return False

    ## BUDGET SETTINGS - METHOD ##

    def update_budget(self, start_day, weekly_max, now=None):
        self.budget_settings["start_day"] = start_day

        # A new max applies from the current period on, leaving past periods' max as it was #
        current_start = period_start(now or datetime.now(), start_day)
        self.budget_settings["weekly_max_history"] = set_weekly_max(
            self.budget_settings["weekly_max_history"], current_start, weekly_max
        )

        with open(self.budget_file, "w") as f:
            json.dump(self.budget_settings, f, default=str)

        self.update_display()

    ## ADD TRANSACTION WINDOW - METHOD ##
    
    def open_transaction_window(self, instance):
        # Adds to the week being viewed: a past week pre-fills its first day, otherwise blank means now #
        page = self.week_carousel.current_slide
        day = page.start.date() if page.end <= datetime.now() else None
        AddTransactionPopup(self, day=day).open()

    ## CATEGORY SELECTION - METHOD ##

    def select_category(self, category, category_btn, popup):
        self.selected_category = category
        if category_btn is not None:
            category_btn.text = category["name"]
            category_btn.background_normal = ""
            category_btn.background_color = category["color"]
            category_btn.color = contrast_color(category["color"])
        popup.dismiss()

    ## DELETE ENTRY - METHOD ##

    def delete_entry(self, index):
        if 0 <= index < len(self.saved_amounts):
            del self.saved_amounts[index]

            with open(self.transactions_file, "w") as f:
                json.dump(self.saved_amounts, f, default=str)
            
            self.update_display()

    ## EDIT ENTRY WINDOW - METHOD ##

    def open_edit_window(self, index):
        EditTransactionPopup(self, index).open()

    ## ERROR POPUP - METHOD ##

    def show_error(self, message):
        popup = Popup(
            title="Error",
            content=Label(text=message),
            size_hint=(0.6, 0.3)
        )
        popup.open()

    ## SORTING - METHODS ##

    def sort_key(self, pair):
        entry = pair[1]
        if self.sort_by == "amount":
            return (entry["amount"], entry["timestamp"])
        return entry["timestamp"]

    def set_sort_method(self, method):
        self.sort_by = method
        self.sort_descending = True
        self.update_display()

    def toggle_sort_order(self):
        self.sort_descending = not self.sort_descending
        self.update_display()

    ## TRANSACTION ROWS - METHOD ##

    def transaction_rows(self, start, end):
        indexed_entries = sorted(
            ((i, entry) for i, entry in enumerate(self.saved_amounts) if start <= entry["timestamp"] < end),
            key=self.sort_key,
            reverse=self.sort_descending
        )

        rows = []
        for original_index, sorted_entry in indexed_entries:
            t = sorted_entry["timestamp"].strftime("%b %d, %I:%M %p")
            category = sorted_entry["category"]["name"] if sorted_entry["category"] else "Uncategorized"
            amount = f"${sorted_entry['amount']:.2f}"
            color = sorted_entry["category"]["color"] if sorted_entry["category"] else [0.30, 0.45, 0.32, 1]
            note = sorted_entry.get("note") or ""

            rows.append({
                "timestamp_text": t,
                "category_text": category,
                "amount_text": amount,
                "note_text": note,
                "index": original_index,
                "category_color": color
            })

        return rows

    ## UPDATE DISPLAY - METHODS ##

    def update_display(self):
        now = datetime.now()
        start_day = self.budget_settings["start_day"]
        start = period_start(now, start_day)
        end = next_period_start(start, start_day)

        # Rebuild the week pages when a new period begins or the start day changes #
        if self.week_carousel.period != (start, end):
            self.week_carousel.show_period(start, end, now=now)
        else:
            self.week_carousel.refresh(now)

        if self.week_screen.carousel.period is not None:
            self.week_screen.carousel.refresh(now)

        self.update_info_panel(now)

    def update_info_panel(self, now=None):
        page = self.week_carousel.current_slide
        if page is None:
            return

        weekly_max = weekly_max_for(self.week_carousel.period[0], self.budget_settings["weekly_max_history"])
        week = summarize_week(self.saved_amounts, page.start, page.end, weekly_max, now or datetime.now())

        self.spent_label.text = f"Spent: ${week['spent']:.2f}"
        self.trans_label.text = f"Transactions: {week['count']}"

        if week["left"] is None:
            self.left_label.text = "No weekly max set"
        elif week["left"] < 0:
            self.left_label.text = f"Over by: ${-week['left']:.2f}"
        else:
            self.left_label.text = f"Left: ${week['left']:.2f}"

if __name__ == "__main__":
    BudgetApp().run()