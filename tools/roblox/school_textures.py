# Jankfield High's surfaces (20 Nov 2026; the zombies school, tools/roblox/school_layout.py). Eighteen seamless,
# low-contrast pictures drawn here from noise and simple shapes (ours, not anyone's art), for SurfaceAppearances on the
# kit's meshes (school_models.py gives them world-scaled box-projected UVs, so the stud size of one repeat below is a
# contract: TEX holds it for the kit). Quiet colours: the owner wants less colour; the base stays grey/cream/wood.
#   file             px          studs (w x h)  what
#   lino.png         512x512     8 x 8          hall floor: vinyl composition tiles 2x2 studs, two close warm greys in
#                                               a checker, fine fleck, thin soft seams
#   cafetile.png     512x512     9 x 9          cafeteria/kitchen quarry tiles 3x3 studs, warm grey-beige, each a hair
#                                               different, darker grout ~0.12 stud
#   terrazzo.png     1024x1024   12 x 12        lobby terrazzo: pale cream, grey chips (a few muted ochre/sage),
#                                               soft polished mottling, a faint brass divider every 6 studs both ways
#   rtile_floor.png  512x512     4 x 4          restroom floor: 0.5-stud square mosaic, one pale blue-grey, light grout
#   rtile_wall.png   512x1024    8 x 16         restroom wall, floor at the picture's bottom: white-ish subway tile
#                                               (1 x 0.5, running bond) to 6 studs, a darker trim row at 6, pale
#                                               grey-green paint above, slight grime at the floor
#   hallwall.png     512x1024    8 x 16         hall wall, floor at the bottom: sage-grey glazed block wainscot (2 x 1
#                                               blocks) to 4.5 studs over a dark cove base 0.4 high, a cap band, cream
#                                               plaster above (the ceiling is at 15), scuffs near the floor
#   classwall.png    512x1024    8 x 16         classroom wall, floor at the bottom: painted cinder block (2 x 1),
#                                               warm off-white, mortar a touch darker, a dark rubber skirting 0.5 high
#   block.png        512x512     8 x 8          plain painted cinder block (2 x 1), light grey: gym, stairwells,
#                                               basement
#   brick.png        512x512     6 x 6          outside and courtyard brick, running bond, 1.5 x 0.5 bricks, muted
#                                               red-brown, gentle variation, recessed grey-beige mortar
#   gymwood.png      1024x1024   16 x 16        gym maple: 0.5-stud strips along x, staggered butt joints, honey-pale
#   woodfloor.png    1024x1024   16 x 16        art/music room oak: 1-stud strips along x, darker and warmer
#   carpet.png       1024x1024   16 x 16        library/office carpet: muted blue-grey low pile, fleck, mottling
#   ceiling.png      512x512     8 x 8          white acoustic ceiling tiles 2x2 studs, thin light-grey T-bars, pits
#   concrete.png     1024x1024   24 x 24        basement/roof concrete: mid grey, soft stains, hairline cracks,
#                                               saw-cut joints every 12 studs
#   chalkboard.png   1024x384    16 x 6         a classroom board: dark green slate, faint eraser smudges (no
#                                               writing), a thin aluminium frame painted round the edge (not tiled)
#   pavers.png       512x512     8 x 8          courtyard pavers: 2 x 1 stud bricks in a basket weave, warm grey-tan,
#                                               weathering, moss in the joints
#   rubber.png       512x512     12 x 12        weight-room rubber: charcoal, sparse grey and muted coloured fleck,
#                                               4x4-stud tile seams
#   lockers.png      512x416     8 x 6.5        a run of 4 locker doors (2 studs each), muted blue-grey steel, 3 vent
#                                               slots at the top of each, a recessed handle, dark gaps between doors
# Rules (memory roblox-upload-content-rules): no text, letters, digits, logos, codes; no QR-like patterns (no random
# light/dark squares: only uniform tiles in regular grout grids).
#   <blender python> tools/roblox/school_textures.py <out_dir>
import sys, os, math

TEX = {
    'lino': (8.0, 8.0), 'cafetile': (9.0, 9.0), 'terrazzo': (12.0, 12.0), 'rtile_floor': (4.0, 4.0),
    'rtile_wall': (8.0, 16.0), 'hallwall': (8.0, 16.0), 'classwall': (8.0, 16.0), 'block': (8.0, 8.0),
    'brick': (6.0, 6.0), 'gymwood': (16.0, 16.0), 'woodfloor': (16.0, 16.0), 'carpet': (16.0, 16.0),
    'ceiling': (8.0, 8.0), 'concrete': (24.0, 24.0), 'chalkboard': (16.0, 6.0), 'pavers': (8.0, 8.0),
    'rubber': (12.0, 12.0), 'lockers': (8.0, 6.5),
}
PIXELS = {
    'lino': (512, 512), 'cafetile': (512, 512), 'terrazzo': (1024, 1024), 'rtile_floor': (512, 512),
    'rtile_wall': (512, 1024), 'hallwall': (512, 1024), 'classwall': (512, 1024), 'block': (512, 512),
    'brick': (512, 512), 'gymwood': (1024, 1024), 'woodfloor': (1024, 1024), 'carpet': (1024, 1024),
    'ceiling': (512, 512), 'concrete': (1024, 1024), 'chalkboard': (1024, 384), 'pavers': (512, 512),
    'rubber': (512, 512), 'lockers': (512, 416),
}

# ---- the v2 set (20 Nov 2026, Jankfield High v2A / v2B; vault Hubs/Jankfield High v2 plan): subtle surfaces for the
# chunky rebuild (the shape does the work; the picture only gives the surface life). Written with --v2.
#   a_terrazzo   1024x1024  12 x 12   v2A halls: warm terrazzo, small soft chips, a faint brass divider every 6 studs
#   a_plaster    512x512    8 x 8     v2A walls: warm off-white painted plaster, very soft trowel mottling (no lines)
#   a_tile       512x512    8 x 8     v2A wainscot: deep muted sage-grey glazed tile 2 x 1, running bond, lighter grout
#   a_brick      512x512    6 x 6     v2A outside/courtyard: older, darker, calmer brick 1.5 x 0.5, warm-grey mortar
#   a_stone      512x512    8 x 8     v2A piers, pilasters, copings: pale warm limestone, faint 4 x 2 blocks
#   a_hextile    512x512    4 x 4     v2A restroom floor: small pale warm-white hexagon mosaic, light grout
#   b_polished   1024x1024  16 x 16   v2B halls: polished concrete, cloudy, fine pale aggregate, saw cuts every 8
#   b_board      512x512    8 x 8     v2B walls and fins: board-formed concrete, faint 1-stud boards, tie holes 2 x 2
#   b_felt       512x512    8 x 8     v2B wall panels: acoustic felt, one muted olive-grey, fine soft grain
#   b_vinyl      1024x1024  16 x 16   v2B classrooms: sheet vinyl, muted cool blue-grey, fine speckle, no tiles
#   b_porcelain  512x512    16 x 16   v2B restrooms: 4 x 4 stud porcelain tiles, light warm grey, faint veining
#   b_whiteboard 1024x384   16 x 6    v2B classrooms: a whiteboard, faint ghost smudges only, aluminium frame (not tiled)
#   b_ceiling    512x512    8 x 8     v2B ceiling coffers: smooth light cast concrete, faint form joints every 4 studs
#   <blender python> tools/roblox/school_textures.py <out_dir> --v2
TEX2 = {
    'a_terrazzo': (12.0, 12.0), 'a_plaster': (8.0, 8.0), 'a_tile': (8.0, 8.0), 'a_brick': (6.0, 6.0),
    'a_stone': (8.0, 8.0), 'a_hextile': (4.0, 4.0),
    'b_polished': (16.0, 16.0), 'b_board': (8.0, 8.0), 'b_felt': (8.0, 8.0), 'b_vinyl': (16.0, 16.0),
    'b_porcelain': (16.0, 16.0), 'b_whiteboard': (16.0, 6.0), 'b_ceiling': (8.0, 8.0),
}
PIXELS2 = {
    'a_terrazzo': (1024, 1024), 'a_plaster': (512, 512), 'a_tile': (512, 512), 'a_brick': (512, 512),
    'a_stone': (512, 512), 'a_hextile': (512, 512),
    'b_polished': (1024, 1024), 'b_board': (512, 512), 'b_felt': (512, 512), 'b_vinyl': (1024, 1024),
    'b_porcelain': (512, 512), 'b_whiteboard': (1024, 384), 'b_ceiling': (512, 512),
}

if __name__ == '__main__':
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    _args = [a for a in sys.argv[1:] if not a.startswith('--')]
    V2 = '--v2' in sys.argv
    OUT = _args[0] if _args else 'out_school_tex'
    os.makedirs(OUT, exist_ok=True)

    def hexrgb(h):
        return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64)

    def pnoise(h, w, sigma_px, aniso=(1.0, 1.0), g=None):
        """periodic (seamless) smooth noise, zero mean, about unit amplitude: white noise blurred in frequency space"""
        n = g.standard_normal((h, w))
        fy = np.fft.fftfreq(h)[:, None] * h
        fx = np.fft.fftfreq(w)[None, :] * w
        sy, sx = sigma_px * aniso[0], sigma_px * aniso[1]
        k = np.exp(-2 * (math.pi ** 2) * ((fy * sy / h) ** 2 + (fx * sx / w) ** 2))
        out = np.real(np.fft.ifft2(np.fft.fft2(n) * k))
        return out / (np.abs(out).max() + 1e-9)

    def pblur(a, sigma_px):
        """a periodic gaussian blur of a 2-D array"""
        h, w = a.shape
        fy = np.fft.fftfreq(h)[:, None]
        fx = np.fft.fftfreq(w)[None, :]
        k = np.exp(-2 * (math.pi ** 2) * (sigma_px ** 2) * (fy ** 2 + fx ** 2))
        return np.real(np.fft.ifft2(np.fft.fft2(a) * k))

    def save(name, arr):
        img = Image.fromarray(np.clip(np.round(arr), 0, 255).astype(np.uint8), 'RGB')
        p = os.path.join(OUT, name + '.png')
        img.save(p, optimize=True)
        print('WROTE', p, img.size)
        return img

    def coords(H, W):
        y = (np.arange(H)[:, None] + 0.5).repeat(W, 1)
        x = (np.arange(W)[None, :] + 0.5).repeat(H, 0)
        return y, x

    def grid(H, W, cw, ch, bond=0.0, y0=0.0):
        """a tile grid (cell cw x ch px; every other row shifted by bond*cw): row, col (wrapped), local x, y, distance
        to the cell's nearest edge. W must hold a whole number of cells (and H an even number of rows with a bond)"""
        y, x = coords(H, W)
        yy = y - y0
        row = np.floor(yy / ch)
        xo = x + (row % 2) * bond * cw
        col = np.floor(xo / cw)
        ncol = int(round(W / cw))
        lx = xo - col * cw
        ly = yy - row * ch
        d = np.minimum(np.minimum(lx, cw - lx), np.minimum(ly, ch - ly))
        return row.astype(int), (col.astype(int) % ncol), lx, ly, d

    def smooth(e0, e1, v):
        t = np.clip((v - e0) / (e1 - e0), 0, 1)
        return t * t * (3 - 2 * t)

    def cellrand(g, rows, cols, n_r, n_c):
        tab = g.standard_normal((n_r + 2, n_c + 2))
        return tab[np.mod(rows, n_r), np.mod(cols, n_c)]

    def tint(shade, base):
        return base[None, None, :] * shade[:, :, None]

    # ------------------------------------------------------------------------------------------------ the pictures
    def lino():
        g = np.random.default_rng(101)
        H = W = 512
        PX = 64.0
        row, col, lx, ly, d = grid(H, W, 2 * PX, 2 * PX)
        a, b = hexrgb('beba af'.replace(' ', '')), hexrgb('c4c0b5')
        chk = ((row + col) % 2)[:, :, None]
        rgb = a[None, None, :] * (1 - chk) + b[None, None, :] * chk
        var = cellrand(g, row, col, 4, 4)
        shade = 1 + 0.008 * var
        # fleck: fine dark and light chips, soft
        f = pnoise(H, W, 0.7, g=g)
        shade += 0.035 * np.clip(f - 0.35, 0, 1) - 0.03 * np.clip(-f - 0.35, 0, 1)
        shade += 0.012 * pnoise(H, W, 40, g=g)
        seam = 1 - smooth(0.6, 1.6, d)
        shade -= 0.05 * seam
        return save('lino', rgb * shade[:, :, None])

    def cafetile():
        g = np.random.default_rng(202)
        H = W = 512
        T = 512 / 3.0
        PX = 512 / 9.0
        row, col, lx, ly, d = grid(H, W, T, T)
        base = hexrgb('b9ab96')
        var = cellrand(g, row, col, 3, 3)
        shade = 1 + 0.014 * var + 0.012 * pnoise(H, W, 6, g=g) + 0.015 * pnoise(H, W, 30, g=g)
        # each tile a little domed: lighter in the middle
        shade += 0.015 * smooth(0, T * 0.4, d)
        rgb = tint(shade, base)
        gw = 0.12 * PX
        gm = 1 - smooth(gw / 2 - 0.6, gw / 2 + 0.8, d)
        grout = hexrgb('8e8577') * (1 + 0.03 * pnoise(H, W, 2, g=g))[:, :, None]
        return save('cafetile', rgb * (1 - gm[:, :, None]) + grout * gm[:, :, None])

    def terrazzo():
        g = np.random.default_rng(303)
        H = W = 1024
        PX = 1024 / 12.0
        base = hexrgb('dcd5c7')
        shade = 1 + 0.025 * pnoise(H, W, 60, g=g) + 0.01 * pnoise(H, W, 6, g=g)
        rgb = tint(shade, base)
        # chips: soft-edged blobs, mostly grey, a few muted ochre and sage; drawn wrapped so the picture tiles
        img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB')
        dr = ImageDraw.Draw(img)
        cols = [('a29f97', 30), ('b6b3ab', 36), ('8b8882', 10), ('c8c3b8', 22), ('b49868', 4), ('8f9a82', 4)]
        pool = [c for c, n in cols for _ in range(n)]
        for _ in range(2200):
            cx, cy = g.uniform(0, W), g.uniform(0, H)
            r = g.uniform(1.8, 5.5) if g.uniform() < 0.85 else g.uniform(5.5, 9.0)
            c = tuple(int(v) for v in hexrgb(pool[g.integers(len(pool))]))
            pts = []
            n = int(g.integers(5, 8))
            ang0 = g.uniform(0, 2 * math.pi)
            for k in range(n):
                a = ang0 + 2 * math.pi * k / n
                rr = r * g.uniform(0.6, 1.15)
                pts.append((rr * math.cos(a), rr * math.sin(a)))
            for ox in (-W, 0, W):
                for oy in (-H, 0, H):
                    if -12 < cx + ox < W + 12 and -12 < cy + oy < H + 12:
                        dr.polygon([(cx + ox + px, cy + oy + py) for (px, py) in pts], fill=c)
        a = np.asarray(img).astype(np.float64)
        # soften the chips a hair (polished, not sharp)
        for k in range(3): a[:, :, k] = 0.7 * a[:, :, k] + 0.3 * pblur(a[:, :, k], 0.8)
        # the brass divider strips every 6 studs both ways (faint), at 0 and 512 px
        y, x = coords(H, W)
        dx = np.minimum(np.abs(((x + 256) % 512) - 256), 9999)
        dy = np.minimum(np.abs(((y + 256) % 512) - 256), 9999)
        dmin = np.minimum(dx, dy)
        strip = 1 - smooth(1.2, 2.4, dmin)
        brass = hexrgb('ad9764')
        a = a * (1 - 0.6 * strip[:, :, None]) + brass * (0.6 * strip[:, :, None])
        return save('terrazzo', a)

    def rtile_floor():
        g = np.random.default_rng(404)
        H = W = 512
        PX = 128.0
        row, col, lx, ly, d = grid(H, W, 0.5 * PX, 0.5 * PX)
        base = hexrgb('c3cbcd')
        shade = 1 + 0.008 * cellrand(g, row, col, 8, 8) + 0.012 * pnoise(H, W, 40, g=g) + 0.006 * pnoise(H, W, 2, g=g)
        shade += 0.012 * smooth(0, 10, d)
        rgb = tint(shade, base)
        gw = 3.2
        gm = 1 - smooth(gw / 2 - 0.5, gw / 2 + 0.7, d)
        grout = hexrgb('dcdfdb')
        return save('rtile_floor', rgb * (1 - gm[:, :, None]) + grout * gm[:, :, None])

    def wall_base(H, W, PX):
        y, x = coords(H, W)
        hgt = (H - y) / PX                     # studs over the floor (the picture's bottom is the floor)
        return y, x, hgt

    def rtile_wall():
        g = np.random.default_rng(505)
        H, W = 1024, 512
        PX = 64.0
        y, x, hgt = wall_base(H, W, PX)
        # the plaster above
        paint = hexrgb('c8cfc2')
        shade = 1 + 0.012 * pnoise(H, W, 3, aniso=(1.0, 0.6), g=g) + 0.012 * pnoise(H, W, 50, g=g)
        rgb = tint(shade, paint)
        # the subway tiles from the floor to 6 studs: 1 x 0.5 studs (64 x 32 px), running bond; rows counted from the floor
        TH = 32.0
        row, col, lx, ly, d = grid(H, W, 64, TH, bond=0.5, y0=H % TH)   # (H is a whole number of rows)
        tile_col = hexrgb('e5e3db')
        ts = 1 + 0.01 * cellrand(g, row, col, 32, 8) + 0.012 * smooth(0, 6, d) + 0.006 * pnoise(H, W, 20, g=g)
        tiles = tint(ts, tile_col)
        gm = 1 - smooth(0.9, 2.0, d)
        tiles = tiles * (1 - gm[:, :, None]) + hexrgb('cbc9c0') * gm[:, :, None]
        in_tile = (hgt < 6.0)[:, :, None]
        rgb = np.where(in_tile, tiles, rgb)
        # the trim row at 6 studs (a darker tile band, 0.35 tall) with a soft shadow line over it
        trim = (hgt >= 6.0) & (hgt < 6.35)
        trim_col = hexrgb('9faa9f') * (1 + 0.01 * pnoise(H, W, 8, g=g))[:, :, None]
        rgb = np.where(trim[:, :, None], trim_col, rgb)
        edge = np.exp(-((hgt - 6.35) * PX / 1.5) ** 2) + np.exp(-((hgt - 6.0) * PX / 1.5) ** 2)
        rgb *= (1 - 0.06 * edge)[:, :, None]
        # slight grime at the floor
        grime = np.exp(-hgt / 0.5) * (0.7 + 0.3 * (0.5 + 0.5 * pnoise(H, W, 14, g=g)))
        rgb *= (1 - 0.1 * grime)[:, :, None]
        return save('rtile_wall', rgb)

    def blockwall(H, W, PX, g, paint, mortar_dark, y0=0.0, glaze=False):
        """painted cinder block 2 x 1 studs, running bond; rows counted from y0 (px from the top)"""
        row, col, lx, ly, d = grid(H, W, 2 * PX, PX, bond=0.5, y0=y0)
        shade = 1 + 0.006 * cellrand(g, row, col, int(H / PX) + 2, int(W / (2 * PX)))
        # the block's face: a fine sprayed paint texture over pitted block
        shade += 0.014 * pnoise(H, W, 1.2, g=g) + 0.01 * pnoise(H, W, 5, g=g) + 0.008 * pnoise(H, W, 60, g=g)
        if glaze:
            shade += 0.02 * smooth(0, 14, d) + 0.012 * pnoise(H, W, 25, g=g)
        jm = 1 - smooth(1.6, 3.2, d)           # (painted-over mortar: a soft shallow joint)
        shade -= mortar_dark * jm
        return tint(shade, paint)

    def hallwall():
        g = np.random.default_rng(606)
        H, W = 1024, 512
        PX = 64.0
        y, x, hgt = wall_base(H, W, PX)
        plaster = tint(1 + 0.01 * pnoise(H, W, 3, aniso=(1.0, 0.5), g=g) + 0.014 * pnoise(H, W, 60, g=g), hexrgb('e0d8c4'))
        glaze = blockwall(H, W, PX, g, hexrgb('a8ae9f'), 0.07, y0=H % PX, glaze=True)
        rgb = np.where((hgt < 4.5)[:, :, None], glaze, plaster)
        # the cove base (0.4 high, darker) and the cap band (4.5 to 4.75)
        cove = hgt < 0.4
        rgb = np.where(cove[:, :, None], tint(1 + 0.01 * pnoise(H, W, 6, g=g), hexrgb('6e7369')), rgb)
        cap = (hgt >= 4.5) & (hgt < 4.75)
        rgb = np.where(cap[:, :, None], tint(1 + 0.008 * pnoise(H, W, 6, g=g), hexrgb('8e9488')), rgb)
        lines = sum(np.exp(-((hgt - h) * PX / 1.2) ** 2) for h in (0.4, 4.5, 4.75))
        rgb *= (1 - 0.07 * lines)[:, :, None]
        # scuffs near the floor: a few soft dark streaks along x, under 2 studs
        sc = np.clip(pnoise(H, W, 5, aniso=(0.25, 3.0), g=g) - 0.45, 0, 1) * (hgt < 2.2) * (hgt > 0.4)
        rgb *= (1 - 0.18 * pblur(sc, 1.0))[:, :, None]
        return save('hallwall', rgb)

    def classwall():
        g = np.random.default_rng(707)
        H, W = 1024, 512
        PX = 64.0
        y, x, hgt = wall_base(H, W, PX)
        rgb = blockwall(H, W, PX, g, hexrgb('e3dccb'), 0.045, y0=H % PX)
        skirt = hgt < 0.5
        rgb = np.where(skirt[:, :, None], tint(1 + 0.012 * pnoise(H, W, 4, g=g), hexrgb('404145')), rgb)
        rgb *= (1 - 0.08 * np.exp(-((hgt - 0.5) * PX / 1.3) ** 2))[:, :, None]
        grime = np.exp(-np.maximum(hgt - 0.5, 0) / 0.6) * (hgt >= 0.5)
        rgb *= (1 - 0.05 * grime)[:, :, None]
        return save('classwall', rgb)

    def block():
        g = np.random.default_rng(808)
        H = W = 512
        rgb = blockwall(H, W, 64.0, g, hexrgb('c9c8c2'), 0.05)
        return save('block', rgb)

    def brick():
        g = np.random.default_rng(909)
        H = W = 512
        PX = 512 / 6.0
        bw, bh = 1.5 * PX, 0.5 * PX
        row, col, lx, ly, d = grid(H, W, bw, bh, bond=0.5)
        var = cellrand(g, row, col, 12, 4)
        var2 = cellrand(g, row + 7, col + 3, 12, 4)
        base = hexrgb('86594c')
        shade = 1 + 0.04 * var + 0.012 * pnoise(H, W, 1.0, g=g) + 0.025 * pnoise(H, W, 6, g=g)
        rgb = tint(shade, base)
        # a gentle hue shift per brick (some browner, some redder)
        rgb[:, :, 0] *= 1 + 0.015 * var2
        rgb[:, :, 2] *= 1 - 0.02 * var2
        # the brick's arrises: a little lighter at the top edge, darker at the bottom (recessed mortar)
        rgb *= (1 + 0.04 * smooth(0, 3, ly) * (1 - smooth(3, 6, ly)) - 0.05 * (1 - smooth(0, 4, bh - ly)))[:, :, None]
        mw = 0.07 * PX                          # (about 6 px of mortar)
        mm = 1 - smooth(mw / 2 - 0.6, mw / 2 + 0.9, d)
        mortar = tint(1 + 0.04 * pnoise(H, W, 1.5, g=g), hexrgb('a39b8b')) * 0.93
        rgb = rgb * (1 - mm[:, :, None]) + mortar * mm[:, :, None]
        return save('brick', rgb)

    def planks(H, W, PX, strip_studs, base_hex, seed, lengths, var_amt, grain_amt, name):
        g = np.random.default_rng(seed)
        y, x = coords(H, W)
        sw = strip_studs * PX
        nstrip = int(round(H / sw))
        row = np.floor(y / sw).astype(int)
        ly = y - row * sw
        img = np.zeros((H, W))
        joint = np.full((H, W), 1e9)
        boardvar = np.zeros((H, W))
        for r in range(nstrip):
            # this strip's boards: lengths summing to the picture's width, rotated by a random offset
            ls, tot = [], 0
            while tot < W:
                L = int(g.choice(lengths))
                ls.append(L); tot += L
            ls[-1] -= tot - W
            if ls[-1] < min(lengths) * 0.5 and len(ls) > 1:
                ls[-2] += ls[-1]; ls.pop()
            off = int(g.integers(0, W))
            edges = np.cumsum([0] + ls)[:-1]
            sel = row == r
            xs = (x[sel] - off) % W
            idx = np.searchsorted(edges, xs, side='right') - 1
            lx = xs - edges[idx]
            dj = np.minimum(lx, np.array(ls)[idx] - lx)
            joint[sel] = dj
            vals = g.standard_normal(len(ls))
            boardvar[sel] = vals[idx]
        grain = pnoise(H, W, 1.2, aniso=(0.35, 12.0), g=g) + 0.5 * pnoise(H, W, 4, aniso=(0.5, 18.0), g=g)
        shade = 1 + var_amt * boardvar + grain_amt * grain + 0.015 * pnoise(H, W, 80, g=g)
        dside = np.minimum(ly, sw - ly)
        shade -= 0.07 * (1 - smooth(0.4, 1.3, dside))      # the long seams
        shade -= 0.06 * (1 - smooth(0.4, 1.3, joint))      # the butt joints
        return save(name, tint(shade, hexrgb(base_hex)))

    def gymwood():
        return planks(1024, 1024, 64.0, 0.5, 'd0ab78', 1010, (192, 256, 320, 384), 0.018, 0.02, 'gymwood')

    def woodfloor():
        return planks(1024, 1024, 64.0, 1.0, 'a27d5a', 1111, (256, 320, 384, 448, 512), 0.022, 0.03, 'woodfloor')

    def carpet():
        g = np.random.default_rng(1212)
        H = W = 1024
        base = hexrgb('77818c')
        f = pnoise(H, W, 0.6, g=g)
        shade = 1 + 0.05 * f + 0.025 * pnoise(H, W, 3, g=g) + 0.03 * pnoise(H, W, 70, g=g)
        rgb = tint(shade, base)
        fl = np.clip(pnoise(H, W, 0.7, g=g) - 0.55, 0, 1)
        rgb = rgb * (1 - 0.6 * fl[:, :, None]) + hexrgb('9aa2aa') * (0.6 * fl[:, :, None])
        return save('carpet', rgb)

    def ceiling():
        g = np.random.default_rng(1313)
        H = W = 512
        PX = 64.0
        row, col, lx, ly, d = grid(H, W, 2 * PX, 2 * PX)
        base = hexrgb('e8e6e0')
        shade = 1 + 0.004 * cellrand(g, row, col, 4, 4) + 0.01 * pnoise(H, W, 30, g=g)
        pits = np.clip(-pnoise(H, W, 0.7, g=g) - 0.45, 0, 1)
        shade -= 0.12 * pits
        shade -= 0.025 * (1 - smooth(2.5, 7.0, d))       # the tile's bevel toward the T-bar
        rgb = tint(shade, base)
        tb = 1 - smooth(1.6, 2.6, d)                     # the T-bar, ~4 px
        rgb = rgb * (1 - tb[:, :, None]) + hexrgb('d0d0cc') * tb[:, :, None]
        return save('ceiling', rgb)

    def wrapped_lines(W, H, polylines, width, value):
        """draw polylines on a W x H mask wrapped round both edges (so it tiles)"""
        img = Image.new('L', (W, H), 0)
        dr = ImageDraw.Draw(img)
        for pl in polylines:
            for ox in (-W, 0, W):
                for oy in (-H, 0, H):
                    dr.line([(px + ox, py + oy) for (px, py) in pl], fill=value, width=width)
        return np.asarray(img).astype(np.float64) / 255.0

    def concrete():
        g = np.random.default_rng(1414)
        H = W = 1024
        PX = 1024 / 24.0
        base = hexrgb('9d9b95')
        shade = 1 + 0.02 * pnoise(H, W, 1.0, g=g) + 0.03 * pnoise(H, W, 12, g=g) + 0.04 * pnoise(H, W, 90, g=g)
        stains = np.clip(pnoise(H, W, 45, g=g) - 0.4, 0, 1)
        shade -= 0.08 * stains
        rgb = tint(shade, base)
        # hairline cracks: wandering lines (wrapped)
        pls = []
        for _ in range(7):
            x0, y0 = g.uniform(0, W), g.uniform(0, H)
            ang = g.uniform(0, 2 * math.pi)
            pl = [(x0, y0)]
            for _ in range(int(g.integers(10, 24))):
                ang += g.normal(0, 0.45)
                x0 += 9 * math.cos(ang); y0 += 9 * math.sin(ang)
                pl.append((x0, y0))
            pls.append(pl)
        cr = pblur(wrapped_lines(W, H, pls, 1, 255), 0.5)
        rgb *= (1 - 0.18 * np.clip(cr * 1.6, 0, 1))[:, :, None]
        # saw-cut joints every 12 studs (512 px), at 0 and 512
        y, x = coords(H, W)
        dx = np.abs(((x + 256) % 512) - 256)
        dy = np.abs(((y + 256) % 512) - 256)
        j = 1 - smooth(0.8, 2.0, np.minimum(dx, dy))
        rgb *= (1 - 0.16 * j)[:, :, None]
        return save('concrete', rgb)

    def chalkboard():
        g = np.random.default_rng(1515)
        H, W = 384, 1024
        base = hexrgb('34473c')
        shade = 1 + 0.02 * pnoise(H, W, 1.0, g=g) + 0.03 * pnoise(H, W, 40, g=g)
        rgb = tint(shade, base)
        # eraser smudges: broad, heavily blurred sweeps (long gentle arcs, far too soft to read as marks)
        img = Image.new('L', (W, H), 0)
        dr = ImageDraw.Draw(img)
        for _ in range(9):
            cx, cy = g.uniform(80, W - 80), g.uniform(60, H - 60)
            rx, ry = g.uniform(90, 260), g.uniform(30, 80)
            a0 = g.uniform(0, 360); a1 = a0 + g.uniform(60, 150)
            dr.arc([cx - rx, cy - ry, cx + rx, cy + ry], a0, a1, fill=int(g.uniform(40, 80)), width=int(g.uniform(26, 44)))
        img = img.filter(ImageFilter.GaussianBlur(14))
        sm = np.asarray(img).astype(np.float64) / 255.0
        haze = 0.5 + 0.5 * pnoise(H, W, 60, g=g)
        rgb = rgb * (1 - 0.25 * sm[:, :, None]) + hexrgb('6f8278') * (0.25 * sm[:, :, None])
        rgb = rgb * (1 - 0.06 * haze[:, :, None]) + hexrgb('5c6f64') * (0.06 * haze[:, :, None])
        # the aluminium frame (0.2 studs = 13 px) and its inner shadow
        y, x = coords(H, W)
        e = np.minimum(np.minimum(x, W - x), np.minimum(y, H - y))
        fr = e < 13
        alu = tint(1 + 0.03 * pnoise(H, W, 2, aniso=(0.3, 6), g=g), hexrgb('a9adb0'))
        rgb = np.where(fr[:, :, None], alu, rgb)
        rgb *= (1 - 0.18 * np.exp(-((e - 13) / 3.0) ** 2) * (e >= 13))[:, :, None]
        # the chalk tray's lip along the bottom (a slightly lighter band in the frame)
        rgb = np.where(((H - y) < 13)[:, :, None], rgb * 1.06, rgb)
        return save('chalkboard', rgb)

    def pavers():
        g = np.random.default_rng(1616)
        H = W = 512
        PX = 64.0
        B = 2 * PX                                  # a basket block: two 2 x 1 pavers, side by side
        y, x = coords(H, W)
        bi, bj = np.floor(x / B).astype(int), np.floor(y / B).astype(int)
        lx, ly = x - bi * B, y - bj * B
        horiz = ((bi + bj) % 2) == 0                # pavers lying along x in this block, else along y
        # inside the block: two pavers 2 x 1 studs (128 x 64 px)
        u = np.where(horiz, ly, lx)                 # across the pair
        k = np.floor(u / PX)
        lu = u - k * PX
        v = np.where(horiz, lx, ly)
        d = np.minimum(np.minimum(lu, PX - lu), np.minimum(v, B - v))
        pid = (bi * 7 + bj * 13 + k.astype(int) * 3) % 29
        tab = g.standard_normal(32)
        var = tab[pid]
        base = hexrgb('aaa08d')
        shade = 1 + 0.03 * var + 0.02 * pnoise(H, W, 1.2, g=g) + 0.03 * pnoise(H, W, 18, g=g)
        shade += 0.02 * smooth(0, 8, d)
        rgb = tint(shade, base)
        jm = 1 - smooth(1.2, 2.6, d)
        moss = 0.5 + 0.5 * pnoise(H, W, 10, g=g)
        joint = hexrgb('7c7668') * (1 - moss[:, :, None] * 0.6) + hexrgb('6e7a58') * (moss[:, :, None] * 0.6)
        rgb = rgb * (1 - jm[:, :, None]) + joint * jm[:, :, None]
        return save('pavers', rgb)

    def rubber():
        g = np.random.default_rng(1717)
        H = W = 512
        T = 512 / 3.0
        base = hexrgb('2f3032')
        shade = 1 + 0.04 * pnoise(H, W, 0.8, g=g) + 0.05 * pnoise(H, W, 30, g=g)
        rgb = tint(shade, base)
        # sparse fleck: mostly grey, a few muted colours
        fl = pnoise(H, W, 0.6, g=g)
        pick = pnoise(H, W, 0.6, g=g)
        m = np.clip((fl - 0.55) * 4, 0, 1)
        grey = hexrgb('686a6c')
        col = np.where((pick > 0.55)[:, :, None], hexrgb('56677d'), np.where((pick < -0.6)[:, :, None], hexrgb('7a6355'), grey[None, None, :]))
        rgb = rgb * (1 - 0.7 * m[:, :, None]) + col * (0.7 * m[:, :, None])
        row, cl, lx, ly, d = grid(H, W, T, T)
        rgb *= (1 - 0.35 * (1 - smooth(0.6, 1.6, d)))[:, :, None]
        return save('rubber', rgb)

    def lockers():
        g = np.random.default_rng(1818)
        H, W = 416, 512
        PX = 64.0
        y, x = coords(H, W)
        base = hexrgb('6f7e8c')
        shade = 1 + 0.012 * pnoise(H, W, 1.0, g=g) + 0.015 * pnoise(H, W, 40, g=g)
        DW = 2 * PX                                  # a door: 2 studs
        lx = (x % DW) - DW / 2                       # (from the door's middle: the doors start at the picture's edge)
        dgap = DW / 2 - np.abs(lx)                   # px from the door's edge
        # the door's slight press-formed edge
        shade += 0.03 * smooth(2, 9, dgap) - 0.02
        # top and bottom frame
        dt, db = y, H - y
        frame = (dt < 10) | (db < 14)
        shade = np.where(frame, shade * 0.86, shade)
        # 3 vent slots near the top: 0.9 studs wide, 0.08 tall, at 0.45, 0.65, 0.85 studs below the top frame
        for k in range(3):
            cy = 10 + (0.4 + 0.16 * k) * PX
            sl = (np.abs(y - cy) < 2.0) & (np.abs(lx) < 0.7 * PX)
            shade = np.where(sl, shade * 0.72, shade)
            lip = (np.abs(y - (cy + 3.0)) < 1.0) & (np.abs(lx) < 0.7 * PX)
            shade = np.where(lip, shade * 1.06, shade)
        # the recessed handle: a vertical slot at mid-height near the door's right edge
        hy = H * 0.52
        hd = (np.abs(y - hy) < 0.22 * PX) & (np.abs(lx - 0.6 * PX) < 0.15 * PX)
        shade = np.where(hd, shade * 0.82, shade)
        rim = (np.abs(y - hy) < 0.27 * PX) & (np.abs(lx - 0.6 * PX) < 0.2 * PX) & ~hd
        shade = np.where(rim, shade * 1.06, shade)
        lift = (np.abs(y - (hy - 0.12 * PX)) < 1.5) & (np.abs(lx - 0.6 * PX) < 0.1 * PX)
        shade = np.where(lift, shade * 0.9, shade)
        rgb = tint(shade, base)
        gap = dgap < 2.2
        rgb = np.where(gap[:, :, None], hexrgb('2b2f33'), rgb)
        return save('lockers', rgb)

    # ================================================================ the v2 set (20 Nov 2026)
    def a_terrazzo():
        g = np.random.default_rng(2101)
        H = W = 1024
        base = hexrgb('cbbca4')
        shade = 1 + 0.022 * pnoise(H, W, 70, g=g) + 0.008 * pnoise(H, W, 6, g=g)
        rgb = tint(shade, base)
        img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB')
        dr = ImageDraw.Draw(img)
        cols = [('a79c88', 30), ('b9ad97', 34), ('8f8676', 10), ('d6cbb6', 20), ('a8875c', 6), ('8a8a74', 4)]
        pool = [c for c, n in cols for _ in range(n)]
        for _ in range(2600):
            cx, cy = g.uniform(0, W), g.uniform(0, H)
            r = g.uniform(1.6, 4.6) if g.uniform() < 0.88 else g.uniform(4.6, 7.0)
            c = tuple(int(v) for v in hexrgb(pool[g.integers(len(pool))]))
            n = int(g.integers(5, 8))
            ang0 = g.uniform(0, 2 * math.pi)
            pts = [(r * g.uniform(0.6, 1.15) * math.cos(ang0 + 2 * math.pi * k / n), r * g.uniform(0.6, 1.15) * math.sin(ang0 + 2 * math.pi * k / n)) for k in range(n)]
            for ox in (-W, 0, W):
                for oy in (-H, 0, H):
                    if -10 < cx + ox < W + 10 and -10 < cy + oy < H + 10:
                        dr.polygon([(cx + ox + px, cy + oy + py) for (px, py) in pts], fill=c)
        a = np.asarray(img).astype(np.float64)
        for k in range(3): a[:, :, k] = 0.55 * a[:, :, k] + 0.45 * pblur(a[:, :, k], 1.0)     # (soft: polished)
        y, x = coords(H, W)
        dmin = np.minimum(np.abs(((x + 256) % 512) - 256), np.abs(((y + 256) % 512) - 256))
        strip = 1 - smooth(1.2, 2.4, dmin)
        a = a * (1 - 0.45 * strip[:, :, None]) + hexrgb('a68d5c') * (0.45 * strip[:, :, None])
        return save('a_terrazzo', a)

    def a_plaster():
        g = np.random.default_rng(2102)
        H = W = 512
        base = hexrgb('e0d6c3')
        shade = 1 + 0.016 * pnoise(H, W, 34, g=g) + 0.01 * pnoise(H, W, 9, g=g) + 0.005 * pnoise(H, W, 1.2, g=g)
        # trowel mottling: soft overlapping patches a touch lighter / darker (isotropic: no strokes)
        sw = pnoise(H, W, 18, g=g)
        shade += 0.012 * np.tanh(sw * 3)
        return save('a_plaster', tint(shade, base))

    def a_tile():
        g = np.random.default_rng(2103)
        H = W = 512
        PX = 64.0
        row, col, lx, ly, d = grid(H, W, 2 * PX, PX, bond=0.5)
        var = cellrand(g, row, col, 8, 4)
        base = hexrgb('7b887d')
        shade = 1 + 0.012 * var + 0.008 * pnoise(H, W, 2, g=g) + 0.01 * pnoise(H, W, 40, g=g)
        # the glaze: a soft sheen, lighter toward each tile's upper middle, a pillowed edge
        shade += 0.025 * smooth(0, 10, d) * (1 - ly / PX) * 0.8
        shade -= 0.03 * (1 - smooth(2, 7, d))
        rgb = tint(shade, base)
        gw = 0.08 * PX
        gm = 1 - smooth(gw / 2 - 0.5, gw / 2 + 0.9, d)
        grout = tint(1 + 0.02 * pnoise(H, W, 2, g=g), hexrgb('b4b5a8'))
        return save('a_tile', rgb * (1 - gm[:, :, None]) + grout * gm[:, :, None])

    def a_brick():
        g = np.random.default_rng(2104)
        H = W = 512
        PX = 512 / 6.0
        bw, bh = 1.5 * PX, 0.5 * PX
        row, col, lx, ly, d = grid(H, W, bw, bh, bond=0.5)
        var = cellrand(g, row, col, 12, 4)
        var2 = cellrand(g, row + 5, col + 2, 12, 4)
        base = hexrgb('6f4d40')
        shade = 1 + 0.03 * var + 0.01 * pnoise(H, W, 1.0, g=g) + 0.02 * pnoise(H, W, 7, g=g) + 0.02 * pnoise(H, W, 60, g=g)
        rgb = tint(shade, base)
        rgb[:, :, 0] *= 1 + 0.012 * var2
        rgb[:, :, 2] *= 1 - 0.015 * var2
        rgb *= (1 + 0.035 * smooth(0, 3, ly) * (1 - smooth(3, 6, ly)) - 0.045 * (1 - smooth(0, 4, bh - ly)))[:, :, None]
        mw = 0.07 * PX
        mm = 1 - smooth(mw / 2 - 0.6, mw / 2 + 0.9, d)
        mortar = tint(1 + 0.035 * pnoise(H, W, 1.5, g=g), hexrgb('958b7b')) * 0.9
        return save('a_brick', rgb * (1 - mm[:, :, None]) + mortar * mm[:, :, None])

    def a_stone():
        g = np.random.default_rng(2105)
        H = W = 512
        PX = 64.0
        row, col, lx, ly, d = grid(H, W, 4 * PX, 2 * PX, bond=0.5)
        var = cellrand(g, row, col, 4, 2)
        base = hexrgb('cdc4b2')
        shade = 1 + 0.012 * var + 0.025 * pnoise(H, W, 40, g=g) + 0.012 * pnoise(H, W, 8, g=g) + 0.006 * pnoise(H, W, 1.0, g=g)
        rgb = tint(shade, base)
        jm = 1 - smooth(0.4, 1.4, d)
        return save('a_stone', rgb * (1 - 0.1 * jm[:, :, None]))

    def a_hextile():
        g = np.random.default_rng(2106)
        H = W = 512
        cw, rs = 64.0, 51.2                       # (8 columns, 10 rows: the lattice repeats on the picture's edges)
        sy = (cw / math.sqrt(3)) / (rs / 1.5)     # (rows a hair squashed so a whole number fit: about 8 %)
        y, x = coords(H, W)
        j0 = np.floor(y / rs).astype(int)
        best = np.full((H, W), 1e9); second = np.full((H, W), 1e9); bi = np.zeros((H, W), int); bj = np.zeros((H, W), int)
        for dj in (-1, 0, 1, 2):
            j = j0 + dj
            cy = j * rs
            off = (np.mod(j, 2)) * cw / 2
            i0 = np.floor((x - off) / cw).astype(int)
            for di in (-1, 0, 1):
                i = i0 + di
                cx = i * cw + off
                dd = np.sqrt((x - cx) ** 2 + ((y - cy) * sy) ** 2)
                nb = dd < best
                second = np.where(nb, best, np.minimum(second, dd))
                bi = np.where(nb, i, bi); bj = np.where(nb, j, bj)
                best = np.where(nb, dd, best)
        edge = (second - best) / 2.0
        var = cellrand(g, bj, bi, 10, 8)
        base = hexrgb('e3ddd0')
        shade = 1 + 0.008 * var + 0.006 * pnoise(H, W, 1.5, g=g) + 0.01 * pnoise(H, W, 40, g=g)
        shade += 0.012 * smooth(0, 6, edge)
        rgb = tint(shade, base)
        gm = 1 - smooth(1.0, 2.2, edge)
        grout = hexrgb('c9c2b4')
        return save('a_hextile', rgb * (1 - gm[:, :, None]) + grout * gm[:, :, None])

    def b_polished():
        g = np.random.default_rng(2201)
        H = W = 1024
        base = hexrgb('a7a8a5')
        shade = 1 + 0.045 * pnoise(H, W, 90, g=g) + 0.022 * pnoise(H, W, 22, g=g) + 0.008 * pnoise(H, W, 2, g=g)
        rgb = tint(shade, base)
        agg = pnoise(H, W, 0.7, g=g)
        rgb = rgb * (1 + 0.07 * np.clip((agg - 0.5) * 3, 0, 1))[:, :, None]
        y, x = coords(H, W)
        dmin = np.minimum(np.abs(((x + 256) % 512) - 256), np.abs(((y + 256) % 512) - 256))
        j = 1 - smooth(0.7, 1.8, dmin)
        return save('b_polished', rgb * (1 - 0.12 * j[:, :, None]))

    def b_board():
        g = np.random.default_rng(2202)
        H = W = 512
        PX = 64.0
        y, x = coords(H, W)
        base = hexrgb('b3b6b4')
        row = np.floor(y / PX).astype(int)
        rv = g.standard_normal(8)[np.mod(row, 8)]
        shade = 1 + 0.004 * rv + 0.02 * pnoise(H, W, 32, g=g) + 0.01 * pnoise(H, W, 6, g=g) + 0.006 * pnoise(H, W, 1.0, g=g)
        ly = y - row * PX
        seam = 1 - smooth(0.5, 1.6, np.minimum(ly, PX - ly))
        shade -= 0.014 * seam
        # tie holes on a 2 x 2 stud grid, offset half a cell: soft small dimples
        tx = np.abs(((x + 64) % 128) - 64); ty = np.abs(((y + 64) % 128) - 64)
        tr = np.sqrt(tx ** 2 + ty ** 2)
        shade -= 0.1 * (1 - smooth(2.5, 4.5, tr))
        shade += 0.03 * (1 - smooth(4.5, 6.5, tr)) * smooth(3.5, 4.5, tr)
        blot = np.clip(pnoise(H, W, 20, g=g) - 0.45, 0, 1)
        shade -= 0.05 * blot
        return save('b_board', tint(shade, base))

    def b_felt():
        g = np.random.default_rng(2203)
        H = W = 512
        base = hexrgb('6e725f')
        shade = 1 + 0.018 * pnoise(H, W, 0.7, aniso=(1.0, 2.2), g=g) + 0.012 * pnoise(H, W, 0.7, aniso=(2.2, 1.0), g=g)
        shade += 0.012 * pnoise(H, W, 5, g=g) + 0.012 * pnoise(H, W, 50, g=g)
        return save('b_felt', tint(shade, base))

    def b_vinyl():
        g = np.random.default_rng(2204)
        H = W = 1024
        base = hexrgb('8b939b')
        shade = 1 + 0.018 * pnoise(H, W, 70, g=g) + 0.008 * pnoise(H, W, 8, g=g)
        f1, f2 = pnoise(H, W, 0.7, g=g), pnoise(H, W, 0.7, g=g)
        shade += 0.05 * np.clip((f1 - 0.55) * 3, 0, 1) - 0.045 * np.clip((f2 - 0.55) * 3, 0, 1)
        return save('b_vinyl', tint(shade, base))

    def b_porcelain():
        g = np.random.default_rng(2205)
        H = W = 512
        T = 128.0
        row, col, lx, ly, d = grid(H, W, T, T)
        var = cellrand(g, row, col, 4, 4)
        base = hexrgb('c5c0b6')
        shade = 1 + 0.01 * var + 0.012 * pnoise(H, W, 24, g=g) + 0.005 * pnoise(H, W, 1.5, g=g)
        rgb = tint(shade, base)
        pls = []
        for _ in range(9):
            x0, y0 = g.uniform(0, W), g.uniform(0, H)
            ang = g.uniform(0, 2 * math.pi)
            pl = [(x0, y0)]
            ang = g.uniform(-0.5, 0.5) + (0 if g.uniform() < 0.5 else math.pi)       # (mostly one drift direction)
            for _ in range(int(g.integers(10, 18))):
                ang += g.normal(0, 0.08)
                x0 += 12 * math.cos(ang); y0 += 12 * math.sin(ang)
                pl.append((x0, y0))
            pls.append(pl)
        vein = pblur(wrapped_lines(W, H, pls, 2, 255), 3.0)
        rgb *= (1 - 0.035 * np.clip(vein * 2.0, 0, 1))[:, :, None]
        gm = 1 - smooth(0.5, 1.4, d)
        return save('b_porcelain', rgb * (1 - gm[:, :, None]) + hexrgb('a9a499') * gm[:, :, None])

    def b_whiteboard():
        g = np.random.default_rng(2206)
        H, W = 384, 1024
        base = hexrgb('ecefed')
        shade = 1 + 0.006 * pnoise(H, W, 1.0, g=g) + 0.008 * pnoise(H, W, 60, g=g)
        rgb = tint(shade, base)
        # ghost smudges: a few very soft, wide blobs (no strokes, nothing shaped)
        img = Image.new('L', (W, H), 0)
        dr = ImageDraw.Draw(img)
        for _ in range(7):
            cx, cy = g.uniform(100, W - 100), g.uniform(70, H - 70)
            rx, ry = g.uniform(60, 160), g.uniform(25, 60)
            dr.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=int(g.uniform(70, 140)))
        sm = np.asarray(img.filter(ImageFilter.GaussianBlur(28))).astype(np.float64) / 255.0
        ghost = hexrgb('c9d0d6')
        rgb = rgb * (1 - 0.22 * sm[:, :, None]) + ghost * (0.22 * sm[:, :, None])
        # the aluminium frame round the edge
        y, x = coords(H, W)
        dd = np.minimum(np.minimum(x, W - x), np.minimum(y, H - y))
        fr = dd < 14
        al = tint(1 + 0.02 * pnoise(H, W, 1.0, g=g) + 0.04 * (1 - smooth(10, 14, dd)), hexrgb('b7bbbe'))
        rgb = np.where(fr[:, :, None], al, rgb)
        rgb = np.where(((dd >= 14) & (dd < 16))[:, :, None], rgb * 0.9, rgb)
        return save('b_whiteboard', rgb)

    def b_ceiling():
        g = np.random.default_rng(2207)
        H = W = 512
        base = hexrgb('c8c9c5')
        shade = 1 + 0.02 * pnoise(H, W, 36, g=g) + 0.01 * pnoise(H, W, 7, g=g) + 0.005 * pnoise(H, W, 1.0, g=g)
        y, x = coords(H, W)
        dmin = np.minimum(np.abs(((x + 128) % 256) - 128), np.abs(((y + 128) % 256) - 128))
        shade -= 0.05 * (1 - smooth(0.5, 1.5, dmin))
        return save('b_ceiling', tint(shade, base))

    def contact(names, pics, texd, out_name):
        TH = 300
        cells = []
        for nm, im in zip(names, pics):
            w, h = im.size
            tile = Image.new('RGB', (w * 2, h * 2))
            for i in (0, 1):
                for j in (0, 1): tile.paste(im, (i * w, j * h))
            s_ = TH / (h * 2)
            tile = tile.resize((max(1, int(w * 2 * s_)), TH), Image.LANCZOS)
            cells.append((nm, tile))
        try: F = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 17)
        except Exception: F = ImageFont.load_default()
        cols = 6
        cells = [(nm, t.resize((int(t.size[0] * min(1.0, 420 / t.size[0])), int(TH * min(1.0, 420 / t.size[0]))), Image.LANCZOS)) for nm, t in cells]
        cw = 440
        rows = (len(cells) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * cw + 20, rows * (TH + 46) + 20), (30, 30, 34))
        dr = ImageDraw.Draw(sheet)
        for k, (nm, t) in enumerate(cells):
            cx, cy = 20 + (k % cols) * cw, 20 + (k // cols) * (TH + 46)
            sheet.paste(t, (cx, cy))
            sw, sh = texd[nm]
            dr.text((cx, cy + TH + 6), '%s  (%g x %g studs, shown 2x2)' % (nm, sw, sh), font=F, fill=(230, 230, 230))
        sheet.save(os.path.join(OUT, out_name), quality=90)
        print('SHEET', os.path.join(OUT, out_name), sheet.size)

    if V2:
        pics2 = [a_terrazzo(), a_plaster(), a_tile(), a_brick(), a_stone(), a_hextile(),
                 b_polished(), b_board(), b_felt(), b_vinyl(), b_porcelain(), b_whiteboard(), b_ceiling()]
        contact(list(TEX2), pics2, TEX2, 'sheet.jpg')
    else:
        pics = [lino(), cafetile(), terrazzo(), rtile_floor(), rtile_wall(), hallwall(), classwall(), block(), brick(),
                gymwood(), woodfloor(), carpet(), ceiling(), concrete(), chalkboard(), pavers(), rubber(), lockers()]
        contact(list(TEX), pics, TEX, 'sheet.jpg')
