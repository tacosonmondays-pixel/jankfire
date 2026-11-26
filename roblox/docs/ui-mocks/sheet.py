"""Compose the comparison sheet (today + A-D, screen by screen) and one board per direction.
Texts for the boards come from README.md section 3. Usage: python sheet.py [--notes <folder>]"""
import os
import re
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

import common

HERE = common.HERE
PNG = os.path.join(HERE, "png")
OUT = os.path.join(HERE, "sheets")
NOTES = r"C:\Users\soup2\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\side-session-notes"
DOCS = os.path.abspath(os.path.join(HERE, ".."))
BG = (21, 23, 26)
FG = (242, 240, 235)
DIM = (150, 154, 160)

TODAY_SRC = {  # today's UI, from captures already in the repo (crop boxes in source pixels)
    "hub": (os.path.join(NOTES, "three_hubs_final.jpg"), (14, 120, 654, 431)),
    "match": (os.path.join(NOTES, "local_f6d4e505-8093-4c63-b4ec-8c76fd4df317", "team-colours", "1v1v1_hud_pastel.jpg"), None),
    "loadout": (os.path.join(DOCS, "shop", "loadout-skins-after.jpg"), None),
    "shop": (os.path.join(DOCS, "shop", "shop-deals.jpg"), None),
    "phone": (os.path.join(DOCS, "touch", "phone-hud-after-v957.jpg"), None),
    "scoreboard": (os.path.join(DOCS, "matchmaking", "66_scoreboard_2v2.jpg"), None),
}
BLURB = {  # two lines each on the comparison sheet
    "A": "Made of the hub's parts: flat panels, the lip only on what you buy, a stencil cut through every hero number.",
    "B": "A TV sports graphic: black slabs, a broadcast score bug, a skew for press and a cut corner for you.",
    "D": "The hubs' enamel wayfinding signs: Butter arrows for Play, Buy and Done, and 'you are here' on your team.",
}
ROWS = [("hub", "HUB"), ("match", "MATCH"), ("loadout", "LOADOUT"), ("shop", "SHOP"), ("phone", "PHONE"), ("scoreboard", "TAB")]


def verdicts():
    """Critic rounds per direction, from verdicts.json: {"A": [[round, score, "note"], ...], ...}."""
    import json
    p = os.path.join(HERE, "verdicts.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def verdict_line(rounds):
    if not rounds:
        return ""
    scores = " > ".join(str(r[1]) for r in rounds)
    last = rounds[-1]
    return f"Anti-AI critic: {scores} (round {last[0]}). {last[2]}"


def font(w=800, size=24):
    name = {800: "BuilderSans-ExtraBold.otf", 700: "BuilderSans-Bold.otf", 500: "BuilderSans-Medium.otf", 400: "BuilderSans-Regular.otf"}[w]
    return ImageFont.truetype(os.path.join(common.FONTS, name), size)


def today_frames():
    d = os.path.join(HERE, "img", "today")
    os.makedirs(d, exist_ok=True)
    out = {}
    for k, (src, box) in TODAY_SRC.items():
        p = os.path.join(d, k + ".jpg")
        if not os.path.exists(p):
            im = Image.open(src).convert("RGB")
            if box:
                im = im.crop(box)
            im.save(p, quality=90)
        out[k] = p
    return out


def fit(path, w, h, fill=(12, 13, 15)):
    im = Image.open(path).convert("RGB")
    im.thumbnail((w, h), Image.LANCZOS)
    if im.width < w * 0.98 and im.height < h * 0.98:  # small sources: scale up to fit
        s = min(w / im.width, h / im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    cell = Image.new("RGB", (w, h), fill)
    cell.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return cell


def directions():
    """Parse README section 3 into {letter: {name, tag, text, bullets, risk}}."""
    md = open(os.path.join(HERE, "README.md"), encoding="utf-8").read()
    sec = md.split("## 3.")[1].split("## 4.")[0]
    out = {}
    for block in re.split(r"\n### ", sec)[1:]:
        head, body = block.split("\n", 1)
        m = re.match(r"([A-D])\. (\w+): (.*)", head.strip())
        if not m:
            continue
        letter, name, tag = m.groups()
        raw = body.split("Why it won't read as AI:")[0].strip().replace("**", "")
        paras, cur = [], []
        for ln in raw.splitlines():
            if ln.startswith("- "):
                if cur:
                    paras.append(" ".join(cur))
                    cur = []
                paras.append(ln)
            elif ln.strip():
                cur.append(ln.strip())
        if cur:
            paras.append(" ".join(cur))
        text = "\n".join(paras)
        bullets = re.findall(r"^- (.*)$", body.split("Why it won't read as AI:")[1].split("Risk:")[0], re.M)
        risk = body.split("Risk:")[1].strip().replace("\n", " ")
        out[letter] = {"name": name, "tag": tag, "text": text, "bullets": bullets, "risk": risk}
    return out


def draw_wrapped(d, xy, text, f, fill, width_px, line_h):
    x, y = xy
    avg = f.getlength("abcdefghijklmnopqrstuvwxyz") / 26
    for para in text.split("\n"):
        for line in textwrap.wrap(para, max(10, int(width_px / avg))):
            d.text((x, y), line, font=f, fill=fill)
            y += line_h
    return y


def comparison(dirs, today):
    cw, ch, gap, left, top = 720, 405, 16, 170, 380
    vd = verdicts()
    cols = [("today", "TODAY", "The current UI, for reference")] + [
        (L.lower(), f"{L}  {dirs[L]['name']}", BLURB[L]) for L in "ABD"]
    W = left + len(cols) * cw + (len(cols) - 1) * gap + 40
    H = top + len(ROWS) * (ch + gap) + 30
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((40, 34), "JANKFIRE: NEW UI DIRECTIONS", font=font(800, 64), fill=FG)
    d.text((42, 116), "Mocks, 21-26 Nov 2026. Three directions, the same six screens each; today's UI on the left. "
           "Roblox fonts only, the pastel team colours, our own icons, real labels. Scores: the owner's anti-AI player critic, 1-10, a fresh critic each round.", font=font(500, 26), fill=DIM)
    for i, (key, name, tag) in enumerate(cols):
        x = left + i * (cw + gap)
        d.text((x, 186), name, font=font(800, 40), fill=FG if key != "today" else DIM)
        y2 = draw_wrapped(d, (x, 236), tag, font(500, 21), DIM, cw - 10, 26)
        if key != "today":
            draw_wrapped(d, (x, max(y2 + 8, 296)), verdict_line(vd.get(key.upper(), [])), font(700, 21), (245, 221, 138), cw - 10, 26)
    for r, (fr, label) in enumerate(ROWS):
        y = top + r * (ch + gap)
        d.text((40, y + ch // 2 - 16), label, font=font(800, 26), fill=DIM)
        for i, (key, name, tag) in enumerate(cols):
            x = left + i * (cw + gap)
            path = today[fr] if key == "today" else os.path.join(PNG, f"{key}_{fr}.png")
            sheet.paste(fit(path, cw, ch), (x, y))
    return sheet


def board(L, info):
    cw, ch, gap, pad = 940, 529, 20, 40
    W = pad * 2 + cw * 2 + gap
    H = 150 + 3 * (ch + gap) + 560
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.text((pad, 34), f"{L}  {info['name']}", font=font(800, 64), fill=FG)
    d.text((pad + 2, 108), info["tag"].capitalize(), font=font(500, 28), fill=DIM)
    l = L.lower()
    cells = [f"{l}_hub", f"{l}_match", f"{l}_loadout", f"{l}_shop", f"{l}_phone", f"{l}_scoreboard"]
    for i, c in enumerate(cells):
        x = pad + (i % 2) * (cw + gap)
        y = 150 + (i // 2) * (ch + gap)
        img.paste(fit(os.path.join(PNG, c + ".png"), cw, ch), (x, y))
    x, y = pad + 4, 150 + 3 * (ch + gap) + 10
    vl = verdict_line(verdicts().get(L, []))
    if vl:
        y = draw_wrapped(d, (x, y), vl, font(700, 22), (245, 221, 138), W - 2 * pad, 30) + 10
    y = draw_wrapped(d, (x, y), info["text"], font(500, 21), FG, W - 2 * pad - 20, 28) + 12
    d.text((x, y), "Why it won't read as AI", font=font(800, 22), fill=FG)
    y += 32
    for b in info["bullets"]:
        y = draw_wrapped(d, (x, y), "- " + b, font(500, 20), DIM, W - 2 * pad - 40, 26)
    y += 8
    draw_wrapped(d, (x, y), "Risk: " + info["risk"], font(500, 20), DIM, W - 2 * pad - 30, 26)
    return img


def main():
    common.setup_fonts()
    os.makedirs(OUT, exist_ok=True)
    dirs = directions()
    today = today_frames()
    sheet = comparison(dirs, today)
    sheet.save(os.path.join(OUT, "ui_mocks_directions.jpg"), quality=86, optimize=True)
    sheet.save(os.path.join(NOTES, "ui_mocks_directions.jpg"), quality=86, optimize=True)
    print("sheet", sheet.size)
    for L, info in dirs.items():
        if L not in BLURB:
            continue
        b = board(L, info)
        name = f"ui_mocks_{L}_{info['name'].lower()}.jpg"
        b.save(os.path.join(OUT, name), quality=86, optimize=True)
        b.save(os.path.join(NOTES, name), quality=86, optimize=True)
        print("board", name, b.size)


if __name__ == "__main__":
    main()
