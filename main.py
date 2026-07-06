import json
import os

from kivy.config import Config
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '800')

from kivy.app import App

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout

from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp

from datetime import datetime

from ui.entry_row import EntryRow
from ui.add_transaction_popup import AddTransactionPopup
from ui.edit_transaction_popup import EditTransactionPopup
from ui.category_select_popup import CategorySelectPopup
from ui.color_utils import contrast_color

class BudgetApp(App):
    def build(self):

        self.saved_amounts = []
        self.saved_categories = []
        self.transactions_file = os.path.join(self.user_data_dir, "transactions.json")
        self.categories_file = os.path.join(self.user_data_dir, "categories.json")

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

        root = BoxLayout(orientation="vertical")

        with root.canvas.before:
            Color(0.125, 0.259, 0.188, 1)  # Forest Green
            self.bg_rect = Rectangle(pos=root.pos, size=root.size)

        root.bind(
            pos=lambda i, v: setattr(self.bg_rect, "pos", i.pos),
            size=lambda i, v: setattr(self.bg_rect, "size", i.size)
        )

        ## TOP BAR ##

        top_bar = BoxLayout(
            size_hint=(1, 0.1),
            padding=dp(10),
            spacing=dp(10)
        )

        top_bar.canvas.before.clear()
        with top_bar.canvas.before:
            Color(0.192, 0.4, 0.29, 1)  # Seafoam Green  
            
            self.top_rect = Rectangle(pos=top_bar.pos, size=top_bar.size)

        top_bar.bind(pos = lambda i, v: setattr(self.top_rect, 'pos', i.pos),
                     size = lambda i, v: setattr(self.top_rect, 'size', i.size))

        top_bar.add_widget(Label(text="Transactions", font_size=sp(24), color=(1, 1, 1, 1)))

        root.add_widget(top_bar)

        ## MAIN CONTENT AREA ##
        
        main = FloatLayout()

        self.rv = RecycleView(
            size_hint=(1, 0.7),
            pos_hint={"center_y": 0.63}
        )   

        layout = RecycleBoxLayout(
            default_size=(None, None),
            default_size_hint=(1, None),
            size_hint=(1, None),
            orientation='vertical'
        )
        layout.bind(minimum_height=layout.setter('height'))
        
        self.rv.add_widget(layout)
        self.rv.layout_manager = layout

        self.rv.viewclass = "EntryRow"
        self.rv.data = []

        main.add_widget(self.rv)

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

        ## BOTTOM LEFT CATEGORIES BUTTON ##

        btn_categories = Button(
            text="Categories",
            halign="center",
            valign="middle",
            background_normal="",
            background_color=(0.51765, 0.878, 0.737, 1),
            color=(0, 0, 0, 1),
            size_hint=(None, None),
            width=dp(90),
            height=dp(185),
            pos_hint={"x": 0.02, "y": 0.005},
            on_release=lambda x: CategorySelectPopup(self).open()
        )

        btn_categories.text_size = btn_categories.size
        btn_categories.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        main.add_widget(btn_categories)

        self.spent_label = Label(text="Total Spent: $0.00", halign="center", valign="middle", color=(1, 1, 1, 1))
        self.spent_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        self.trans_label = Label(text="Total Transactions: 0", halign="center", valign="middle", color=(1, 1, 1, 1))
        self.trans_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))

        info_panel.add_widget(self.spent_label)
        info_panel.add_widget(self.trans_label)

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

        ## VIEW BUDGET BUTTON ##

        btn_budget = Button(
            text="View\nBudget",
            halign="center",
            valign="middle",
            background_normal="",
            background_color=(0.51765, 0.878, 0.737, 1),
            color=(0, 0, 0, 1),
            size_hint=(1, None),
            height=dp(91)
        )

        # Center text #
        btn_add.text_size = btn_add.size
        btn_add.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))
        btn_budget.text_size = btn_budget.size
        btn_budget.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))

        btn_cluster.add_widget(btn_add)
        btn_cluster.add_widget(btn_budget)
        main.add_widget(btn_cluster)

        root.add_widget(main)
        
        self.update_display()

        return root

    ## ADD TRANSACTION WINDOW - METHOD ##
    
    def open_transaction_window(self, instance):
        AddTransactionPopup(self).open()

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

    ## UPDATE DISPLAY - METHOD ##

    def update_display(self):
        if not self.saved_amounts:
            self.rv.data = [{
                "timestamp_text": "No entries yet.",
                "category_text": "",
                "amount_text": "",
                "note_text": "",
                "index": -1
            }]
            return
            
        indexed_entries = sorted(
            enumerate(self.saved_amounts),
            key=lambda pair: pair[1]["timestamp"],
            reverse=True
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

        self.rv.data = rows

        total_spent = sum(entry["amount"] for entry in self.saved_amounts)
        total_transactions = len(self.saved_amounts)

        self.spent_label.text = f"Total Spent: ${total_spent:.2f}"
        self.trans_label.text = f"Total Transactions: {total_transactions}"


if __name__ == "__main__":
    BudgetApp().run()