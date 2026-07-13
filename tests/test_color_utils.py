import pytest

from ui.color_utils import contrast_color


@pytest.mark.parametrize("bg, expected", [
    ((1, 1, 1, 1), (0, 0, 0, 1)),        # white background -> black text
    ((0, 0, 0, 1), (1, 1, 1, 1)),        # black background -> white text
    ((0.9, 0.9, 0.9, 1), (0, 0, 0, 1)),  # light gray -> black text
    ((0.1, 0.1, 0.1, 1), (1, 1, 1, 1)),  # dark gray -> white text
])
def test_contrast_color(bg, expected):
    assert contrast_color(bg) == expected


def test_contrast_color_ignores_alpha_channel():
    opaque = contrast_color((0.9, 0.9, 0.9, 1))
    transparent = contrast_color((0.9, 0.9, 0.9, 0))
    assert opaque == transparent


def test_contrast_color_switches_at_the_midpoint():
    assert contrast_color((0.49, 0.49, 0.49, 1)) == (1, 1, 1, 1)
    assert contrast_color((0.51, 0.51, 0.51, 1)) == (0, 0, 0, 1)
