"""Upload guard for tripo_bake.py atlases: soften the packed small-island strips and drop tiny isolated metal marks.

The bake packer puts the many small UV islands in a strip along the top and the right of each 1024 atlas. In the
normal, metal and roughness maps those strips read as block mosaics, and in the metal map a small painted motif (a
banner crown turned on its side) can stand alone like a letter. Both are what the account's upload rules forbid
(no QR- or barcode-like patterns, nothing that reads as text). Run this on every normal/metal/rough map before upload
and look at each file at full size afterwards.

    python bake_guard.py <map.png> --kind normal|metal|rough --top 140 --right 930 [--out other.png]

--top: the strip runs from y=0 to here; --right: the strip runs from this x to the right edge (pick both by eye from
the colour map). The first run keeps the untouched map as orig_maps/<name> next to it and always works from that
copy, so it can be re-run with other numbers. Used on the four Ducky guns (place v708, 17 Nov 2026).
"""
import argparse, os, shutil
from PIL import Image, ImageDraw, ImageFilter


def strip_mask(w, h, top, right, feather=10, grow=10):
    m = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(m)
    d.rectangle((0, 0, w, top + grow), fill=255)
    d.rectangle((right - grow, 0, w, h), fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather))


def drop_small_marks(im, top, right, max_px=900, max_box=45, on=60):
    """Clear small stand-alone metal islands (motifs) inside the atlas body; real pieces are bigger or in the strips."""
    w, h = im.size
    p = im.load()
    seen = bytearray(w * h)
    gone = []
    for y in range(h):
        for x in range(w):
            if seen[y * w + x] or p[x, y] < on:
                continue
            seen[y * w + x] = 1
            st, c = [(x, y)], []
            while st:
                a, b = st.pop()
                c.append((a, b))
                for u, v in ((a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)):
                    if 0 <= u < w and 0 <= v < h and not seen[v * w + u] and p[u, v] >= on:
                        seen[v * w + u] = 1
                        st.append((u, v))
            if len(c) > max_px:
                continue
            xs = [q[0] for q in c]
            ys = [q[1] for q in c]
            if min(ys) <= top + 15 or max(xs) >= right - 15 or min(xs) <= 2:
                continue
            if max(xs) - min(xs) > max_box or max(ys) - min(ys) > max_box:
                continue
            for a, b in c:
                for u in range(a - 2, a + 3):
                    for v in range(b - 2, b + 3):
                        if 0 <= u < w and 0 <= v < h and p[u, v] < 150:
                            p[u, v] = 0
            gone.append((len(c), min(xs), min(ys), max(xs), max(ys)))
    return gone


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('png')
    ap.add_argument('--kind', choices=('normal', 'metal', 'rough'), required=True)
    ap.add_argument('--top', type=int, required=True)
    ap.add_argument('--right', type=int, required=True)
    ap.add_argument('--out')
    a = ap.parse_args()
    keep = os.path.join(os.path.dirname(os.path.abspath(a.png)), 'orig_maps', os.path.basename(a.png))
    if not os.path.exists(keep):
        os.makedirs(os.path.dirname(keep), exist_ok=True)
        shutil.copy(a.png, keep)
    src = Image.open(keep)
    if a.kind == 'normal':
        im = src.convert('RGB')
        out = Image.composite(im.filter(ImageFilter.GaussianBlur(5)), im, strip_mask(*im.size, a.top, a.right, 8, 0))
    else:
        im = src.convert('L')
        if a.kind == 'metal':
            print('small metal marks cleared:', drop_small_marks(im, a.top, a.right))
        out = Image.composite(im.filter(ImageFilter.GaussianBlur(10)), im.filter(ImageFilter.GaussianBlur(1.5)),
                              strip_mask(*im.size, a.top, a.right))
    out.save(a.out or a.png)
    print('wrote', a.out or a.png)


if __name__ == '__main__':
    main()
