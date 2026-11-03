import math
from colorsys import hsv_to_rgb, rgb_to_hsv

from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.widget import Widget

from ui.color_utils import contrast_color
from ui.expanding_popup import ExpandingPopup

TEXTURE_SIZE = 128          # Hue and saturation change smoothly, so a small texture stretched over the wheel looks the same
TOUCH_SLOP = dp(16)         # A drag can start just outside the edge and still lands on it

## THE WHEEL'S PICTURE (HUE AROUND IT, SATURATION OUT FROM THE WHITE CENTER) ##

_wheel_pixels = None
_wheel_texture = None

def wheel_pixels():
    # RGB bytes, bottom row first like Kivy's textures; outside the circle repeats the edge so it never shows black #
    global _wheel_pixels
    if _wheel_pixels is None:
        half = (TEXTURE_SIZE - 1) / 2
        pixels = bytearray()
        for y in range(TEXTURE_SIZE):
            for x in range(TEXTURE_SIZE):
                hue, saturation = position_to_hue_saturation((x - half) / half, (y - half) / half)
                pixels.extend(round(c * 255) for c in hsv_to_rgb(hue, saturation, 1))
        _wheel_pixels = bytes(pixels)
    return _wheel_pixels

def wheel_texture():
    global _wheel_texture
    if _wheel_texture is None:
        _wheel_texture = Texture.create(size=(TEXTURE_SIZE, TEXTURE_SIZE), colorfmt="rgb")
        _wheel_texture.mag_filter = "linear"
        _wheel_texture.min_filter = "linear"
        _fill_texture(_wheel_texture)

        # Android can drop the picture when the app goes to the background, so it's drawn again on return #
        _wheel_texture.add_reload_observer(_fill_texture)
    return _wheel_texture

def _fill_texture(texture):
    texture.blit_buffer(wheel_pixels(), colorfmt="rgb", bufferfmt="ubyte")

def position_to_hue_saturation(dx, dy):
    # `dx`, `dy` measured from the center in radii; past the edge counts as the edge #
    hue = (math.atan2(dy, dx) / (2 * math.pi)) % 1
    return hue, min(math.hypot(dx, dy), 1)

## COLOR WHEEL (TAP OR DRAG TO PICK; BRIGHTNESS DIMS THE WHOLE WHEEL) ##

class ColorWheel(Widget):
    hue = NumericProperty(0)
    saturation = NumericProperty(0)
    value = NumericProperty(1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.tint = Color(1, 1, 1, 1)
            self.disc = Ellipse(texture=wheel_texture())

            # Thin rim smooths the disc's edge #
            Color(0.25, 0.25, 0.25, 1)
            self.rim = Line(width=dp(1))

            # Two-tone ring so the picked spot shows on light and dark colors alike #
            Color(0, 0, 0, 0.6)
            self.marker_outer = Line(width=dp(2.5))
            Color(1, 1, 1, 1)
            self.marker_inner = Line(width=dp(1.2))

        self.bind(pos=self._redraw, size=self._redraw, hue=self._redraw, saturation=self._redraw, value=self._redraw)

    @property
    def radius(self):
        return min(self.width, self.height) / 2

    @property
    def color(self):
        return [round(c, 4) for c in hsv_to_rgb(self.hue, self.saturation, self.value)] + [1]

    def _redraw(self, *args):
        cx, cy, r = self.center_x, self.center_y, self.radius
        self.disc.pos = (cx - r, cy - r)
        self.disc.size = (2 * r, 2 * r)
        self.rim.circle = (cx, cy, r)
        self.tint.rgb = (self.value, self.value, self.value)

        angle = self.hue * 2 * math.pi
        mx = cx + math.cos(angle) * self.saturation * r
        my = cy + math.sin(angle) * self.saturation * r
        self.marker_pos = (mx, my)
        self.marker_outer.circle = (mx, my, dp(9))
        self.marker_inner.circle = (mx, my, dp(9))

    def on_touch_down(self, touch):
        if math.hypot(touch.x - self.center_x, touch.y - self.center_y) > self.radius + TOUCH_SLOP:
            return super().on_touch_down(touch)
        touch.grab(self)
        self._pick(touch)
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            self._pick(touch)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)

    def _pick(self, touch):
        r = self.radius or 1
        self.hue, self.saturation = position_to_hue_saturation((touch.x - self.center_x) / r, (touch.y - self.center_y) / r)

## SHOWS THE PICKED COLOR AND ITS HEX CODE ##

class ColorPreview(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self.fill = Color(1, 1, 1, 1)
            self.rect = Rectangle()
        self.bind(pos=self._place, size=self._place)

    def _place(self, *args):
        self.rect.pos, self.rect.size = self.pos, self.size

    def show(self, color):
        self.fill.rgba = color
        self.color = contrast_color(color)
        self.text = "#{:02X}{:02X}{:02X}".format(*(round(c * 255) for c in color[:3]))

## CUSTOM COLOR POPUP (OPENED FROM A CATEGORY'S COLOR CHOICES) ##

class ColorWheelPopup(ExpandingPopup):
    def __init__(self, color, on_save, **kwargs):
        super().__init__(**kwargs)
        self.on_save_callback = on_save
        hue, saturation, value = rgb_to_hsv(*color[:3])

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))

        # Kept square, a little narrower than the popup so the sides are easy to reach #
        self.wheel = ColorWheel(hue=hue, saturation=saturation, value=value, size_hint_y=None)
        self.wheel.bind(width=lambda inst, width: setattr(inst, "height", width * 0.8))

        brightness_label = Label(text="Brightness", size_hint_y=None, height=dp(20), color=(1, 1, 1, 1))
        self.brightness = Slider(min=0, max=1, value=value, size_hint_y=None, height=dp(36))
        self.brightness.bind(value=lambda inst, val: setattr(self.wheel, "value", val))

        self.preview = ColorPreview(size_hint_y=None, height=dp(40))
        self.wheel.bind(hue=self._update_preview, saturation=self._update_preview, value=self._update_preview)
        self._update_preview()

        save_btn = Button(
            text="Save",
            size_hint_y=None,
            height=dp(44),
            background_normal="",
            background_color=(0.51765, 0.878, 0.737, 1),
            color=(0, 0, 0, 1)
        )
        save_btn.bind(on_release=lambda x: self._save())

        layout.add_widget(self.wheel)
        layout.add_widget(brightness_label)
        layout.add_widget(self.brightness)
        layout.add_widget(self.preview)
        layout.add_widget(save_btn)

        self.title = "Custom Color"
        self.title_color = (1, 1, 1, 1)
        self.content = layout
        self.size_hint_x = 0.85
        self.fit_to(layout)

    def _update_preview(self, *args):
        self.preview.show(self.wheel.color)

    def _save(self):
        self.on_save_callback(self.wheel.color)
        self.dismiss()
