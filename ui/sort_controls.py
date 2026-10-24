import math

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Line, Triangle
from kivy.properties import BooleanProperty
from kivy.metrics import dp, sp

from ui.entry_row import BORDER_WIDTH

SORT_LABELS = {"date": "Date", "amount": "Amount"}
SORT_OPTION_LABELS = {"date": "By Date", "amount": "By Amount"}

## SORT ICON (UP + DOWN ARROW) ##

class SortIconButton(ButtonBehavior, Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(1, 1, 1, 1)
            self.up_shaft = Line(width=dp(1.3))
            self.up_head = Triangle()
            self.down_shaft = Line(width=dp(1.3))
            self.down_head = Triangle()

        self.bind(pos=self.update_icon, size=self.update_icon)

    def update_icon(self, *args):
        cx, cy = self.x + self.width / 2, self.y + self.height / 2
        half_h = dp(9)
        offset = dp(4.5)
        head = dp(4.5)

        # Up arrow (left) #
        ux = cx - offset
        self.up_shaft.points = [ux, cy - half_h, ux, cy + half_h - head]
        self.up_head.points = [ux - head, cy + half_h - head, ux + head, cy + half_h - head, ux, cy + half_h]

        # Down arrow (right) #
        dx = cx + offset
        self.down_shaft.points = [dx, cy + half_h, dx, cy - half_h + head]
        self.down_head.points = [dx - head, cy - half_h + head, dx + head, cy - half_h + head, dx, cy - half_h]

## SORT ORDER INDICATOR (EQUILATERAL TRIANGLE) ##

class SortOrderTriangle(Widget):
    descending = BooleanProperty(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        with self.canvas:
            Color(1, 1, 1, 1)
            self.triangle = Triangle()

        self.bind(pos=self.update_triangle, size=self.update_triangle, descending=self.update_triangle)

    def update_triangle(self, *args):
        cx, cy = self.x + self.width / 2, self.y + self.height / 2
        side = dp(11)
        half_h = side * math.sqrt(3) / 4

        if self.descending:  # Pointing down #
            self.triangle.points = [cx - side / 2, cy + half_h, cx + side / 2, cy + half_h, cx, cy - half_h]
        else:  # Pointing up #
            self.triangle.points = [cx - side / 2, cy - half_h, cx + side / 2, cy - half_h, cx, cy + half_h]

## SORT ORDER TOGGLE (METHOD TEXT + TRIANGLE, TAPPABLE AS ONE) ##

class SortOrderToggle(ButtonBehavior, BoxLayout):
    pass

## SORT CONTROLS (ICON + METHOD TEXT + ORDER TOGGLE) ##

class SortControls(BoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="horizontal", spacing=dp(2), **kwargs)
        self.app = app

        self.icon_btn = SortIconButton(size_hint=(None, 1), width=dp(26))

        self.method_label = Label(
            text=SORT_LABELS[app.sort_by],
            font_size=sp(13),
            color=(1, 1, 1, 1),
            size_hint=(None, 1)
        )
        self.method_label.bind(texture_size=lambda inst, val: setattr(inst, "width", val[0]))

        self.order_triangle = SortOrderTriangle(size_hint=(None, 1), width=dp(16), descending=app.sort_descending)

        self.order_toggle = SortOrderToggle(orientation="horizontal", spacing=dp(2), size_hint=(None, 1))
        self.order_toggle.bind(minimum_width=self.order_toggle.setter("width"))
        self.order_toggle.add_widget(self.method_label)
        self.order_toggle.add_widget(self.order_triangle)

        ## DROPDOWN MENU ##

        self.dropdown = DropDown(auto_width=False, width=dp(120))
        for method, text in SORT_OPTION_LABELS.items():
            option = Button(
                text=text,
                background_normal="",
                background_color=(0.51765, 0.878, 0.737, 1),
                color=(0, 0, 0, 1),
                size_hint_y=None,
                height=dp(40)
            )
            option.bind(on_release=lambda btn, m=method: self.dropdown.select(m))
            self.dropdown.add_widget(option)

        # Black border around the menu + separator between options #
        # Inset so the dropdown's scroll clipping doesn't thin the outer edges #
        container = self.dropdown.container
        with container.canvas.after:
            Color(0, 0, 0, 1)
            self.dropdown_border = Line(width=BORDER_WIDTH)
            self.dropdown_separators = [Line(width=BORDER_WIDTH) for _ in range(len(SORT_OPTION_LABELS) - 1)]
        container.bind(pos=self.update_dropdown_border, size=self.update_dropdown_border)

        self.dropdown.bind(on_select=lambda inst, method: self.select_method(method))
        self.icon_btn.bind(on_release=self.dropdown.open)
        self.order_toggle.bind(on_release=lambda x: self.toggle_order())

        self.add_widget(self.icon_btn)
        self.add_widget(self.order_toggle)

    def update_dropdown_border(self, container, *args):
        inset = BORDER_WIDTH
        self.dropdown_border.rectangle = (
            container.x + inset, container.y + inset,
            container.width - 2 * inset, container.height - 2 * inset
        )

        # Children are stored bottom-to-top; a separator sits on each option's top edge #
        options = container.children
        for separator, option in zip(self.dropdown_separators, options):
            separator.points = [container.x, option.top, container.right, option.top]

    def select_method(self, method):
        self.app.set_sort_method(method)
        self.refresh()

    def toggle_order(self):
        self.app.toggle_sort_order()
        self.refresh()

    def refresh(self):
        self.method_label.text = SORT_LABELS[self.app.sort_by]
        self.order_triangle.descending = self.app.sort_descending
