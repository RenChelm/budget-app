from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.metrics import dp

class CategorySelectPopup(Popup):
    def __init__(self, app, category_btn, **kwargs):
        super().__init__(**kwargs)
        self.app = app 
        self.category_btn = category_btn

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        categories = ["Food", "Bills", "Entertainment", "Subscriptions",
                      "Rent","Insurance", "Savings", "Medicine", "Therapy",
                      "Credit Card", "Personal Care/Hygiene", "Other"]

        popup = self

        for cat in categories:
            btn = Button(text=cat, size_hint_y=None, height=dp(40))
            btn.bind(on_release=lambda instance, c=cat: self.app.select_category(c, self.category_btn, popup))
            layout.add_widget(btn)

        self.title="Select Category"
        self.content=layout
        self.size_hint=(0.8, 0.84)

