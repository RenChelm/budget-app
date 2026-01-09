import json

from kivy.config import Config
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '800')

from kivy.app import App

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from kivy.graphics import Color, Rectangle

from datetime import datetime


class BudgetApp(App):
    def build(self):

        self.saved_amounts = []

        # Load saved entries from file #

        try:
            with open("data.json", "r") as f:
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

        root = BoxLayout(orientation="vertical")

        with root.canvas.before:
            Color(0.18, 0.31, 0.18, 1)  # Forest Green
            self.bg_rect = Rectangle(pos=root.pos, size=root.size)

        root.bind(
            pos=lambda i, v: setattr(self.bg_rect, "pos", i.pos),
            size=lambda i, v: setattr(self.bg_rect, "size", i.size)
        )

        ## TOP BAR ##

        top_bar = BoxLayout(
            size_hint=(1, 0.1),
            padding=10,
            spacing=10
        )

        top_bar.canvas.before.clear()
        with top_bar.canvas.before:
            Color(0.36, 0.27, 0.21, 1)  # Bark Brown  
            
            self.top_rect = Rectangle(pos=top_bar.pos, size=top_bar.size)

        top_bar.bind(pos = lambda i, v: setattr(self.top_rect, 'pos', i.pos),
                     size = lambda i, v: setattr(self.top_rect, 'size', i.size))

        top_bar.add_widget(Label(text="Transactions", font_size=24))

        root.add_widget(top_bar)

        ## MAIN CONTENT AREA ##
        main = FloatLayout()

        self.display_label = Label(
            text="No entries yet",
            pos_hint={"center_x": 0.5, "center_y": 0.6},
            font_size=18
        )

        main.add_widget(self.display_label)

        btn_add = Button(
            text="Add",
            background_normal = "",
            background_color = (0.65, 0.77, 0.63, 1),
            color = (0, 0, 0, 1),
            halign="center",
            valign="middle",
            size_hint=(0.16, 0.12),
            pos_hint={"right": 0.99, "y": 0.14},
            on_release=self.open_transaction_window
        )

        btn_budget = Button(
            text="View\nBudget",
            background_normal = "",
            background_color = (0.41, 0.56, 0.42, 1),
            color = (0, 0, 0, 1),
            halign="center",
            valign="middle",
            size_hint=(0.16, 0.12),
            pos_hint={"right": 0.99, "y": 0.01}
        )

        # Center text properly #
        btn_add.text_size = btn_add.size
        btn_budget.text_size = btn_budget.size

        main.add_widget(btn_add)
        main.add_widget(btn_budget)

        root.add_widget(main)
        
        self.update_display()

        return root

    ## ADD TRANSACTION WINDOW - METHOD ##
    
    def open_transaction_window(self, instance):
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.input_box = TextInput(
            multiline=False,
            size_hint_y=None,
            height=40
        )

        save_btn = Button(text="Save", size_hint=(1, 0.3))
        save_btn.bind(on_release=lambda x: self.save_text())

        self.category_btn = Button(text="Select Category", size_hint=(1, 0.3))
        self.category_btn.bind(on_release=lambda x: self.open_category_window())

        layout.add_widget(self.input_box)
        layout.add_widget(save_btn)
        layout.add_widget(self.category_btn)

        self.popup = Popup(
            title="Enter Amount",
            content=layout,
            size_hint=(0.8, 0.3)
        )
        self.popup.open()

    ## CATEGORY SELECTION WINDOW - METHOD ##

    def open_category_window(self):
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        categories = ["Food", "Bills", "Transport", "Fun", "Other"]

        for cat in categories:
            btn = Button(text=cat, size_hint_y=None, height=40)
            btn.bind(on_release=lambda instance, c=cat: self.select_category(c))
            layout.add_widget(btn)

        self.category_popup = Popup(
            title="Select Category",
            content=layout,
            size_hint=(0.8, 0.5)
        )
        self.category_popup.open()

    ## CATEGORY SELECTION - METHOD ##

    def select_category(self, category):
        self.selected_category = category
        self.category_btn.text = f"{category}"
        self.category_popup.dismiss()
        
    ## SAVE TEXT AND CLOSE BUTTON - METHOD ##

    def save_text(self):
        value = self.input_box.text.strip()

        try:
            amount = float(value)
        except ValueError:
            self.show_error("Please enter a valid number.")
            return

        entry = {
            "amount": amount,
            "timestamp": datetime.now(),
            "category": getattr(self, "selected_category", None)
        }

        self.saved_amounts.append(entry)

        # Save to file #
        with open("data.json", "w") as f:
            json.dump(self.saved_amounts, f, default=str)

        self.update_display()
        self.popup.dismiss()

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
            self.display_label.text = "No entries yet"
            return
            
        sorted_entries = sorted(self.saved_amounts, key=lambda x: x["timestamp"], reverse=True)

        lines = []
        for entry in sorted_entries:
            t = entry["timestamp"].strftime("%Y-%m-%d %I:%M %p")
            lines.append(f"{t} — {entry['amount']} - {entry['category'] or 'Uncategorized'}")

        self.display_label.text = "\n".join(lines)

    def update_rect(instance, value):
        self.top_rect.pos = instance.pos
        self.top_rect.size = instance.size

        top_bar.bind(pos=update_rect, size=update_rect)


BudgetApp().run()