from kivy.uix.boxlayout import BoxLayout
from kivy.metrics import dp

from ui.category_select_popup import CategorySelectPopup
from ui.expanding_popup import ExpandingPopup
from ui.name_select_popup import NameSelectPopup
from ui.rounded_button import RoundedButton

## PICKS WHICH OF THE USER'S OWN LISTS TO OPEN: CATEGORIES, RETAILERS OR BRANDS ##

class CustomPopup(ExpandingPopup):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        self.buttons = {}
        for key, text, open_menu in (
            ("categories", "Categories", lambda: CategorySelectPopup(self.app).open()),
            ("retailers", "Retailers", lambda: NameSelectPopup(self.app, "retailer").open()),
            ("brands", "Brands", lambda: NameSelectPopup(self.app, "brand").open()),
        ):
            btn = RoundedButton(
                text=text,
                fill_color=(0.51765, 0.878, 0.737, 1),
                color=(0, 0, 0, 1),
                size_hint_y=None,
                height=dp(50)
            )
            btn.bind(on_release=lambda inst, open_menu=open_menu: self._choose(open_menu))
            self.buttons[key] = btn
            layout.add_widget(btn)

        self.title = "Custom"
        self.title_color = (1, 1, 1, 1)
        self.content = layout
        self.size_hint_x = 0.8
        self.fit_to(layout)

    def _choose(self, open_menu):
        # Swaps this popup for the chosen list, so closing the list goes straight back to the main page #
        self.dismiss()
        open_menu()
