from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.metrics import dp

from budget_periods import format_money
from ui.color_utils import CONFIRM_COLOR

## ASKS WHETHER TO MOVE WHAT WAS LEFT (OR OVERSPENT) IN THE LAST WEEK/MONTH ONTO THE CURRENT ONE ##

class CarryOverPopup(Popup):
    def __init__(self, app, span, current, mode, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.span = span

        over = span["carry_over"]["over"]
        amount = abs(span["carry_over"]["amount"])
        unit = "week" if mode == "weekly" else "month"

        if over:
            question = f"Subtract the ${amount:.2f} you went over from this {unit}?"
        else:
            question = f"Add the ${amount:.2f} you didn't spend to this {unit}?"
        message = f"You spent {format_money(span['spent'])} of {format_money(span['budget'])} last {unit}.\n\n{question}"

        # Monthly mode splits it evenly over the month's weeks #
        if mode == "monthly":
            weeks = len(current["weeks"])
            message += f" Each of its {weeks} weeks gets ${amount / weeks:.2f} {'less' if over else 'more'}."

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        self.message_label = Label(text=message, color=(1, 1, 1, 1), halign="center", valign="middle")
        self.message_label.bind(size=lambda inst, val: setattr(inst, "text_size", inst.size))

        self.no_btn = Button(text="No Thanks", color=(1, 1, 1, 1))
        self.no_btn.bind(on_release=lambda x: self.answer(False))

        self.add_btn = Button(
            text=f"{'Subtract' if over else 'Add'} ${amount:.2f}",
            background_normal="",
            background_color=CONFIRM_COLOR,
            color=(1, 1, 1, 1)
        )
        self.add_btn.bind(on_release=lambda x: self.answer(True))

        btn_row = BoxLayout(size_hint=(1, None), height=dp(44), spacing=dp(10))
        btn_row.add_widget(self.no_btn)
        btn_row.add_widget(self.add_btn)

        layout.add_widget(self.message_label)
        layout.add_widget(btn_row)

        self.title = "Over Budget" if over else "Under Budget"
        self.title_color = (1, 1, 1, 1)
        self.content = layout
        self.size_hint = (0.8, None)
        self.height = dp(280)

        # Only closes through a button so it's asked once; History can change the answer later #
        self.auto_dismiss = False

    def answer(self, carried):
        self.app.set_carry_over(self.span, carried)
        self.dismiss()
