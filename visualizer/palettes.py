"""Color palettes. Each one is a list of RGB colors blended from the bass bars
(left) to the treble bars (right). Add your own to PALETTES and it joins the
C-key rotation automatically. None means a rainbow sweep."""
import colorsys

PALETTES = {
    "rainbow":   None,
    "fire":      [(90, 0, 0), (220, 40, 0), (255, 150, 0), (255, 240, 130)],
    "ocean":     [(10, 30, 110), (0, 110, 210), (0, 210, 220), (190, 255, 250)],
    "synthwave": [(70, 0, 160), (190, 0, 210), (255, 50, 140), (255, 180, 70)],
    "matrix":    [(0, 70, 20), (0, 190, 60), (120, 255, 140)],
    "ice":       [(120, 140, 255), (170, 220, 255), (255, 255, 255)],
    "mono":      [(170, 170, 185), (255, 255, 255)],
}
PALETTE_NAMES = list(PALETTES)


def palette_colors(name, n):
    """Return n RGB tuples spread evenly across the palette."""
    stops = PALETTES[name]
    colors = []
    for i in range(n):
        t = i / max(1, n - 1)                      # 0 at the left bar, 1 at the right
        if stops is None:
            r, g, b = colorsys.hsv_to_rgb((260 - 260 * t) / 360, 0.85, 1.0)   # purple -> red
            colors.append((int(r * 255), int(g * 255), int(b * 255)))
        else:
            pos = t * (len(stops) - 1)             # which pair of stops we're between
            k = min(int(pos), len(stops) - 2)
            f = pos - k
            a, b = stops[k], stops[k + 1]
            colors.append(tuple(int(a[j] + (b[j] - a[j]) * f) for j in range(3)))
    return colors
