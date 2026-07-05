def contrast_color(bg_color):
    r, g, b = bg_color[0], bg_color[1], bg_color[2]
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return (1, 1, 1, 1) if luminance < 0.5 else (0, 0, 0, 1)