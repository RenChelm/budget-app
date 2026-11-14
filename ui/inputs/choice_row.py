from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from kivy.metrics import dp, sp

SELECTED_COLOR = (0.51765, 0.878, 0.737, 1)    # Mint, same as the main buttons
UNSELECTED_COLOR = (0.192, 0.4, 0.29, 1)       # Seafoam Green

## ROW OF BUTTONS WHERE EXACTLY ONE IS SELECTED ##

class ChoiceRow(BoxLayout):
    value = ObjectProperty(None)

    def __init__(self, options, font_size=sp(15), **kwargs):
        super().__init__(orientation="horizontal", spacing=dp(2), **kwargs)

        # `options` maps each value to its button text #
        self.buttons = {}
        for option, text in options.items():
            btn = Button(text=text, font_size=font_size, background_normal="")
            btn.bind(on_release=lambda inst, o=option: setattr(self, "value", o))
            self.buttons[option] = btn
            self.add_widget(btn)

        self.bind(value=lambda inst, val: self.update_buttons())
        self.update_buttons()

    def update_buttons(self):
        for option, btn in self.buttons.items():
            selected = option == self.value
            btn.background_color = SELECTED_COLOR if selected else UNSELECTED_COLOR
            btn.color = (0, 0, 0, 1) if selected else (1, 1, 1, 1)
