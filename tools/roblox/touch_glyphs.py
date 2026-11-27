# The phone buttons' glyphs (27 Nov 2026, ui-mocks; main: "one consistent glyph family ... flat, bold, readable at
# thumb size ... vectors in code, never AI"). One white family on a transparent sprite sheet, drawn here as shapes at 4x
# and scaled down, uploaded once as an Image; TouchGlyphs.luau maps each button's action to its cell.
# Content rules (memory roblox-upload-content-rules): no text, no digits, nothing code-like; plain shapes only.
#   python touch_glyphs.py <out.png> [--preview <big.png>]
import math, sys
from PIL import Image, ImageDraw

CELL = 128          # one glyph's cell in the sheet
SS = 4              # drawn at 4x, then scaled down
C = CELL * SS       # the drawing cell
W = int(C * 0.115)  # the family's stroke weight
ORDER = ["fire", "aim", "jump", "crouch", "sprint", "hook", "reload", "swap", "melee", "item",
         "camera", "emote", "wave", "yank", "reel", "reelin", "lunge", "board", "settings", "auto"]
COLS = 5

def P(x, y):  # a point in cell units (0..1) to drawing pixels
    return (x * C, y * C)

def line(d, pts, w=W):
    pts = [P(*p) for p in pts]
    d.line(pts, fill=255, width=w, joint="curve")
    for p in (pts[0], pts[-1]):  # round caps
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=255)

def disc(d, x, y, r, fill=255):
    d.ellipse([P(x - r, y - r), P(x + r, y + r)], fill=fill)

def ring(d, x, y, r, w=W):
    d.ellipse([P(x - r, y - r), P(x + r, y + r)], outline=255, width=w)

def poly(d, pts, fill=255):
    d.polygon([P(*p) for p in pts], fill=fill)

def rrect(d, x0, y0, x1, y1, r, fill=255):
    d.rounded_rectangle([P(x0, y0), P(x1, y1)], radius=r * C, fill=fill)

def arc(d, x, y, r, a0, a1, w=W):
    d.arc([P(x - r, y - r), P(x + r, y + r)], a0, a1, fill=255, width=w)

def chevron(d, cx, cy, s, dirn, w=W):  # an open arrowhead: dirn "up" / "right" / "left" / "down"
    if dirn == "up": line(d, [(cx - s, cy + s * 0.6), (cx, cy - s * 0.4), (cx + s, cy + s * 0.6)], w)
    if dirn == "down": line(d, [(cx - s, cy - s * 0.6), (cx, cy + s * 0.4), (cx + s, cy - s * 0.6)], w)
    if dirn == "right": line(d, [(cx - s * 0.6, cy - s), (cx + s * 0.4, cy), (cx - s * 0.6, cy + s)], w)
    if dirn == "left": line(d, [(cx + s * 0.6, cy - s), (cx - s * 0.4, cy), (cx + s * 0.6, cy + s)], w)

def arrowhead(d, tip, back, half):  # a filled triangle pointing from back to tip
    (tx, ty), (bx, by) = tip, back
    dx, dy = tx - bx, ty - by
    n = math.hypot(dx, dy); nx, ny = -dy / n, dx / n
    poly(d, [(tx, ty), (bx + nx * half, by + ny * half), (bx - nx * half, by - ny * half)])

# ---------------------------------------------------------------- the glyphs
def g_fire(d):  # a cartridge, point up
    poly(d, [(0.5, 0.12), (0.64, 0.3), (0.64, 0.42), (0.36, 0.42), (0.36, 0.3)])
    rrect(d, 0.36, 0.46, 0.64, 0.8, 0.02)
    rrect(d, 0.32, 0.82, 0.68, 0.9, 0.02)

def g_aim(d):  # a scope reticle: a ring, four ticks outside it, a dot
    ring(d, 0.5, 0.5, 0.28)
    for (a, b) in [((0.5, 0.1), (0.5, 0.2)), ((0.5, 0.8), (0.5, 0.9)), ((0.1, 0.5), (0.2, 0.5)), ((0.8, 0.5), (0.9, 0.5))]:
        line(d, [a, b])
    disc(d, 0.5, 0.5, 0.07)

def g_jump(d):  # up, off a ground line
    chevron(d, 0.5, 0.36, 0.24, "up")
    line(d, [(0.5, 0.36), (0.5, 0.7)])
    line(d, [(0.22, 0.86), (0.78, 0.86)])

def g_crouch(d):  # a slide: a low bold arrow along the floor, speed lines behind
    line(d, [(0.34, 0.56), (0.66, 0.56)], int(W * 1.1))
    arrowhead(d, (0.9, 0.56), (0.62, 0.56), 0.17)
    line(d, [(0.08, 0.44), (0.22, 0.44)], int(W * 0.75))
    line(d, [(0.08, 0.66), (0.2, 0.66)], int(W * 0.75))
    line(d, [(0.1, 0.86), (0.9, 0.86)])

def g_sprint(d):  # run: two chevrons forward
    chevron(d, 0.38, 0.5, 0.24, "right")
    chevron(d, 0.66, 0.5, 0.24, "right")

def g_hook(d):  # a grappling hook: an eye, a shaft, two curved tines with points
    ring(d, 0.5, 0.15, 0.08, int(W * 0.85))
    line(d, [(0.5, 0.24), (0.5, 0.78)])
    arc(d, 0.5, 0.52, 0.3, 20, 160)    # the tines: one bow under the shaft
    line(d, [(0.78, 0.62), (0.88, 0.47)])   # right barb
    line(d, [(0.22, 0.62), (0.12, 0.47)])   # left barb

def g_reload(d):  # a circular arrow
    arc(d, 0.5, 0.52, 0.3, 300, 210 + 360)
    arrowhead(d, (0.27, 0.22), (0.3, 0.42), 0.12)

def g_swap(d):  # two arrows passing
    line(d, [(0.16, 0.34), (0.72, 0.34)]); arrowhead(d, (0.9, 0.34), (0.7, 0.34), 0.12)
    line(d, [(0.84, 0.66), (0.28, 0.66)]); arrowhead(d, (0.1, 0.66), (0.3, 0.66), 0.12)

def g_melee(d):  # a knife, point up-right
    poly(d, [(0.86, 0.14), (0.8, 0.36), (0.52, 0.64), (0.4, 0.52), (0.68, 0.24)])
    line(d, [(0.32, 0.5), (0.54, 0.72)], int(W * 0.9))   # the guard
    line(d, [(0.38, 0.66), (0.16, 0.86)], int(W * 1.3))  # the grip

def g_item(d):  # a grenade
    disc(d, 0.47, 0.6, 0.27)
    rrect(d, 0.38, 0.22, 0.56, 0.36, 0.03)
    line(d, [(0.56, 0.26), (0.78, 0.42)], int(W * 0.85))  # the lever

def g_camera(d):  # a camera body and lens
    rrect(d, 0.12, 0.32, 0.88, 0.82, 0.08)
    rrect(d, 0.34, 0.2, 0.6, 0.34, 0.03)
    disc(d, 0.5, 0.57, 0.17, fill=0)
    disc(d, 0.5, 0.57, 0.09)

def g_emote(d):  # a figure, arms up
    disc(d, 0.5, 0.2, 0.1)
    line(d, [(0.5, 0.36), (0.5, 0.62)])
    line(d, [(0.5, 0.42), (0.26, 0.24)]); line(d, [(0.5, 0.42), (0.74, 0.24)])
    line(d, [(0.5, 0.62), (0.34, 0.88)]); line(d, [(0.5, 0.62), (0.66, 0.88)])

def g_wave(d):  # a blade's crescent
    d.pieslice([P(0.08, 0.14), P(0.92, 0.98)], 200, 340, fill=255)
    d.pieslice([P(0.14, 0.3), P(0.86, 1.1)], 190, 350, fill=0)

def g_yank(d):  # pull: a rope from a ring, an arrow back toward you
    ring(d, 0.8, 0.5, 0.11)
    line(d, [(0.68, 0.5), (0.3, 0.5)]); arrowhead(d, (0.08, 0.5), (0.3, 0.5), 0.15)

def g_reel(d):  # lock on: four corner brackets round a dot (AUTO GRAPPLE)
    s, k = 0.36, 0.16
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = 0.5 + sx * s, 0.5 + sy * s
            line(d, [(cx, cy - sy * k), (cx, cy), (cx - sx * k, cy)])
    disc(d, 0.5, 0.5, 0.1)

def g_reelin(d):  # pull in: two arrows to a centre bar
    line(d, [(0.5, 0.18), (0.5, 0.82)])
    line(d, [(0.06, 0.5), (0.24, 0.5)]); arrowhead(d, (0.4, 0.5), (0.22, 0.5), 0.12)
    line(d, [(0.94, 0.5), (0.76, 0.5)]); arrowhead(d, (0.6, 0.5), (0.78, 0.5), 0.12)

def g_lunge(d):  # a dash: one bold arrow with speed lines
    line(d, [(0.34, 0.5), (0.7, 0.5)], int(W * 1.2)); arrowhead(d, (0.92, 0.5), (0.66, 0.5), 0.18)
    line(d, [(0.08, 0.32), (0.26, 0.32)], int(W * 0.7)); line(d, [(0.06, 0.68), (0.24, 0.68)], int(W * 0.7))

def g_board(d):  # the scoreboard: rows with a marker
    for y in (0.26, 0.5, 0.74):
        disc(d, 0.18, y, 0.06)
        line(d, [(0.34, y), (0.84, y)])

def g_settings(d):  # a gear: eight square teeth round a disc, a hole
    for i in range(8):
        a = i * math.pi / 4
        ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
        r0, r1, hw = 0.24, 0.42, 0.075
        poly(d, [(0.5 + ux * r0 + vx * hw, 0.5 + uy * r0 + vy * hw), (0.5 + ux * r1 + vx * hw, 0.5 + uy * r1 + vy * hw),
                 (0.5 + ux * r1 - vx * hw, 0.5 + uy * r1 - vy * hw), (0.5 + ux * r0 - vx * hw, 0.5 + uy * r0 - vy * hw)])
    disc(d, 0.5, 0.5, 0.31)
    disc(d, 0.5, 0.5, 0.12, fill=0)

def g_auto(d):  # auto fire: three cartridges side by side
    for x in (0.24, 0.5, 0.76):
        poly(d, [(x, 0.2), (x + 0.09, 0.34), (x + 0.09, 0.44), (x - 0.09, 0.44), (x - 0.09, 0.34)])
        rrect(d, x - 0.09, 0.48, x + 0.09, 0.8, 0.015)

DRAW = {n: globals()["g_" + n] for n in ORDER}

def sheet() -> Image.Image:
    rows = math.ceil(len(ORDER) / COLS)
    out = Image.new("RGBA", (COLS * CELL, rows * CELL), (255, 255, 255, 0))
    for i, name in enumerate(ORDER):
        m = Image.new("L", (C, C), 0)
        d = ImageDraw.Draw(m)
        # each glyph inside a 10% margin so nothing touches its neighbour
        DRAW[name](d)
        m = m.resize((CELL, CELL), Image.LANCZOS)
        tile = Image.new("RGBA", (CELL, CELL), (255, 255, 255, 0))
        tile.putalpha(m)
        out.paste(tile, ((i % COLS) * CELL, (i // COLS) * CELL))
    return out

if __name__ == "__main__":
    out = sys.argv[1]
    s = sheet()
    s.save(out)
    if "--preview" in sys.argv:
        big = sys.argv[sys.argv.index("--preview") + 1]
        bg = Image.new("RGBA", s.size, (40, 42, 48, 255))
        bg.alpha_composite(s)
        bg.convert("RGB").resize((s.size[0] * 2, s.size[1] * 2), Image.LANCZOS).save(big)
    print("cells:", {n: i for i, n in enumerate(ORDER)})
