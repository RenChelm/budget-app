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
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout

from kivy.graphics import Color, Rectangle
from kivy.graphics import Color, RoundedRectangle

from kivy.properties import StringProperty
from kivy.properties import NumericProperty

from datetime import datetime

class EntryRow(BoxLayout):
    text = StringProperty("") 
    bg_color = (0.30, 0.45, 0.32, 1)
    index = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 50
        self.padding = [10, 10]
        self.spacing = 60

        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = RoundedRectangle(
                radius=[10], 
                pos=(self.x + 5, self.y + 5), 
                size=(self.width - 2, self.height - 2)
            )

        self.bind(pos=self.update_rect, size=self.update_rect)

        # Left label (timestamp + category) #
        self.left_label = Label(
            text="",
            halign="left",
            valign="middle",
            size_hint_x=0.7
        )
        self.left_label.bind(size=lambda inst, val: setattr(inst, "text_size", (inst.width, None)))

        # Right label (amount) #
        self.right_label = Label(
            text="",
            halign="right",
            valign="middle",
            size_hint_x=0.3,
        )
        self.right_label.bind(size=lambda inst, val: setattr(inst, "text_size", (inst.width, None)))

        self.delete_btn = Button(
            text="X",
            size_hint_x=None,
            width=40,
            background_normal="",
            background_color=(0.8, 0.3, 0.3, 1),
            color=(1, 1, 1, 1)
        )
        self.delete_btn.bind(on_release=self.on_delete_pressed)

        self.edit_btn = Button(
            text="Edit",
            size_hint_x=None,
            width=60,
            background_normal="",
            background_color=(0.3, 0.5, 0.8, 1),
            color=(1, 1, 1, 1)
        )
        self.edit_btn.bind(on_release=self.on_edit_pressed)
        
        self.add_widget(self.left_label)
        self.add_widget(self.right_label)
        self.add_widget(self.delete_btn)
        self.add_widget(self.edit_btn)

    def update_rect(self, *args):
        self.bg_rect.pos = (self.x + 5, self.y + 5)
        self.bg_rect.size = (self.width - 2, self.height - 2)

    def on_text(self, instance, value):
        # Split the text into left/right parts #
        try:
            left, right = value.split("||")
        except ValueError:
            left, right = value, ""

        self.left_label.text = left
        self.right_label.text = right

    def on_delete_pressed(self, instance):
        App.get_running_app().delete_entry(self.index)

    def on_edit_pressed(self, instance):
        app = App.get_running_app()
        app.open_edit_window(self.index)


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
            Color(0.125, 0.259, 0.188, 1)  # Forest Green
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
            Color(0.192, 0.4, 0.29, 1)  # Seafoam Green  
            
            self.top_rect = Rectangle(pos=top_bar.pos, size=top_bar.size)

        top_bar.bind(pos = lambda i, v: setattr(self.top_rect, 'pos', i.pos),
                     size = lambda i, v: setattr(self.top_rect, 'size', i.size))

        top_bar.add_widget(Label(text="Transactions", font_size=24))

        root.add_widget(top_bar)

        ## MAIN CONTENT AREA ##
        main = FloatLayout()

        self.rv = RecycleView(
            size_hint=(1, 0.75),
            pos_hint={"center_x": 0.5, "center_y": 0.6}
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

        btn_add = Button(
            text="Add",
            background_normal = "",
            background_color = (0.51765, 0.878, 0.737, 1),
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
            background_color = (0.51765, 0.878, 0.737, 1),
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
        if hasattr(self, "editing_category_btn"):
            self.editing
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

    ## DELETE ENTRY - METHOD ##

    def delete_entry(self, index):
        if 0 <= index < len(self.saved_amounts):
            del self.saved_amounts[index]

            with open("data.json", "w") as f:
                json.dump(self.saved_amounts, f, default=str)
            
            self.update_display()

    ## EDIT ENTRY WINDOW - METHOD ##

    def open_edit_window(self, index):
        entry = self.saved_amounts[index]

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        amount_input = TextInput(
            text=str(entry["amount"]),
            multiline=False,
            input_filter="float",
        )

        category_btn = Button(
            text=entry["category"],
            size_hint_y=None,
            height=40
        )
        category_btn.bind(on_release=lambda inst: self.open_category_window_for_edit(index, category_btn))

        save_btn = Button(text="Save", size_hint_y=None, height=40)
        save_btn.bind(on_release=lambda inst: self.save_edit(index, amount_input.text))

        layout.add_widget(Label(text="Edit Amount:"))
        layout.add_widget(amount_input)
        layout.add_widget(Label(text="Edit Category:"))
        layout.add_widget(self.category_btn)
        layout.add_widget(save_btn)

        self.edit_window = Popup(
            title="Edit Entry",
            content=layout,
            size_hint=(0.8, 0.5)
        )
        self.edit_window.open()

    ## SAVE EDITED ENTRY - METHOD ##

    def save_edit(self, index, new_amount, new_category):
        try:
            new_amount = float(new_amount)
        except ValueError:
            return

        self.saved_amounts[index]["amount"] = new_amount
        self.saved_amounts[index]["category"] = new_category

        # Save to JSON #

        with open("data.json", "w") as f:
            json.dump(self.saved_amounts, f, default=str)

        # Refresh UI #

        self.update_display()

        # Close window #

        self.edit_window.dismiss()  

    ## OPEN CATEGORY WINDOW FOR EDIT - METHOD ##

    def open_category_window_for_edit(self, index, category_btn):
        self.editing_index = index
        self.editing_category_btn = category_btn
        self.open_category_window()
        
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
            self.rv.data = [{"text": "No entries yet ||"}]
            return
            
        sorted_entries = sorted(self.saved_amounts, key=lambda x: x["timestamp"], reverse=True)

        rows = []
        for sorted_entry in sorted_entries:
            original_index = self.saved_amounts.index(sorted_entry)

            t = sorted_entry["timestamp"].strftime("%b %d, %I:%M %p")
            category = sorted_entry["category"] or "Uncategorized"
            amount = f"${sorted_entry['amount']:.2f}"

            left = f"{t}\n{category}"
            right = amount

            rows.append({
                "text": f"{left}||{right}",
                "index": original_index
            })

        self.rv.data = rows

    ## UPDATE TOP BAR RECTANGLE ON RESIZE/MOVE - METHOD ##

    def update_rect(instance, value):
        self.top_rect.pos = instance.pos
        self.top_rect.size = instance.size

        top_bar.bind(pos=update_rect, size=update_rect)


BudgetApp().run()