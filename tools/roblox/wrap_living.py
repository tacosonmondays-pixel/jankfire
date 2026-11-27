"""LIVING CAMOS: wraps whose picture moves and changes shape (26-27 Nov 2026; the owner: "are you able to make some
camos like warp around like a lavalamp one ... maybe one of them has lighting effects, lava that courses through and
glows"). docs/WRAP-TEXTURES.md "Living camos".

A Texture only scrolls (WRAP FLOW), so shape changes are a FLIPBOOK of whole wrap pictures: N seamless tiles, each a
moment of a loop, worn one after another (client/WrapAnim swaps the piece's SurfaceAppearance frames). Every frame is
seamless in space (the field is periodic over the tile) and the last frame runs into the first (every motion is a
whole number of cycles over the loop).

  lavalamp: soft blobs (metaballs) rising at two speeds and swaying, so they meet, merge, stretch and split; warm
            orange, rose and gold on a deep plum glass; the blobs glow softly
  molten:   dark basalt cut by a net of cracks; molten lava courses through them (bright pulses flowing along the gun),
            the hot cores pale yellow, the cooler lava orange-red; the glow mask follows the lava
  chrome:   liquid metal: a slowly swirling mercury surface (domain-warped bands of light and dark silver with a faint
            cold tint); worn with full metal and low roughness, so the room's reflections move over it too

Shapes only: no text, codes, logos. Usage: py tools/roblox/wrap_living.py <out dir> [kind ...] [--frames N] [--size P]
Writes <kind>_f<NN>_color.png and <kind>_f<NN>_emit.png, plus <kind>_sheet.jpg (all frames) for checking.
"""
import os, sys, math
import numpy as np
from PIL import Image

TAU = 2 * math.pi


def _grid(n):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float64)
    return (yy + 0.5) / n, (xx + 0.5) / n          # v (down), u (along the gun), both 0..1


def _wd(d):
    return (d + 0.5) % 1.0 - 0.5                     # periodic distance on the unit tile


def _smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _pnoise(u, v, k, phase, seed):
    """a cheap periodic noise: a few sines whose wave numbers are whole, so it tiles"""
    rng = np.random.default_rng(seed)
    out = np.zeros_like(u)
    for i in range(6):
        a, b = rng.integers(-k, k + 1, 2)
        if a == 0 and b == 0:
            a = 1
        out += np.sin(TAU * (a * u + b * v) + rng.uniform(0, TAU) + phase * rng.choice([-1, 1]) * (1 + i % 2))
    return out / 6


# ---------------------------------------------------------------------------------------------------- lava lamp
# (27 Nov, the 0.6 m tiles: six big round blobs were squashed and cut on every gun ("bokeh discs"); twelve smaller
# ones now, each with a lobed outline that turns as it goes, so none of them is a circle)
_lr = np.random.default_rng(77)
LAMP_BLOBS = [  # u0, v0, radius, rise cycles per loop (+ up, - sinking: they pass through each other), sway, colour
    (float(_lr.uniform(0, 1)), float(_lr.uniform(0, 1)), float(_lr.uniform(0.034, 0.058)), 1 if k % 2 == 0 else -1,
     float(_lr.uniform(0.02, 0.04)), k % 3) for k in range(12)]
LAMP_LOBES = [(float(_lr.uniform(0, 6.283)), float(_lr.uniform(0, 6.283)), 1 if _lr.uniform() < 0.5 else -1) for _ in range(12)]
LAMP_COL = [np.array([1.00, 0.52, 0.18]), np.array([0.96, 0.34, 0.46]), np.array([1.00, 0.78, 0.30])]
LAMP_BASE_TOP, LAMP_BASE_BOT = np.array([0.16, 0.06, 0.20]), np.array([0.28, 0.08, 0.22])


def lavalamp(t, n):
    v, u = _grid(n)
    field = np.zeros_like(u)
    wsum = np.zeros_like(u)
    col = np.zeros(u.shape + (3,))
    for i, (u0, v0, r, cyc, sway, ci) in enumerate(LAMP_BLOBS):
        cv = (v0 - cyc * t) % 1.0                                     # rising = v falling (v runs down)
        cu = (u0 + sway * math.sin(TAU * (t + i * 0.17))) % 1.0
        rr = r * (1 + 0.18 * math.sin(TAU * (t * 2 + i * 0.31)))       # each blob breathes as it goes
        du, dv = _wd(u - cu), _wd(v - cv) * 0.8                        # (a little taller than wide)
        ph1, ph2, turn = LAMP_LOBES[i]
        ang = np.arctan2(dv, du)
        lob = 1 + 0.16 * np.sin(3 * ang + ph1 + TAU * t * turn) + 0.12 * np.sin(2 * ang + ph2 - TAU * t * turn)
        d2 = (du * du + dv * dv) / (lob * lob)
        f = rr * rr / (d2 + 1e-5)
        field += f
        w = f ** 2
        wsum += w
        col += w[..., None] * LAMP_COL[ci]
    col /= np.maximum(wsum, 1e-9)[..., None]
    inside = _smooth(0.93, 1.07, field)                                # the blob's edge: where blobs meet they merge
    core = _smooth(2.2, 7.0, field)                                    # (a soft inner glow, not a ring)
    halo = _smooth(0.35, 0.85, field) * (1 - inside)
    g = (0.5 - 0.5 * np.cos(TAU * v))[..., None]                     # (a periodic glow up and down: the tile repeats)
    base = LAMP_BASE_TOP * (1 - g) + LAMP_BASE_BOT * g
    blob = col * (0.84 + 0.16 * core[..., None]) + core[..., None] * np.array([0.08, 0.07, 0.04])
    rgb = base * (1 - inside[..., None]) + blob * inside[..., None]
    rgb = rgb + halo[..., None] * col * 0.18
    emit = np.clip(inside * (0.32 + 0.33 * core) + halo * 0.12, 0, 1)
    return np.clip(rgb, 0, 1), emit


# ---------------------------------------------------------------------------------------------------- molten
def _cracks(n, seed=31, cells=6):
    """a static net of cracks: a periodic Voronoi's borders, wobbled; 1 on the crack's centre line"""
    rng = np.random.default_rng(seed)
    v, u = _grid(n)
    pts = rng.uniform(0, 1, (cells * cells, 2))
    # (stretched along the gun: the plates are longer than tall)
    # the true distance to the border between the two nearest cells: |r2|^2 - |r1|^2 over 2 |r1 - r2| (r = the pixel
    # from each seed); plain d2 - d1 smears into wide fans where the seeds are far apart
    wu = u + 0.007 * _pnoise(u, v, 3, 0, 3); wv = v + 0.007 * _pnoise(u, v, 3, 1, 4)
    big = 9.0
    d1 = np.full(u.shape, big); d2 = np.full(u.shape, big)
    r1u = np.zeros_like(u); r1v = np.zeros_like(u); r2u = np.zeros_like(u); r2v = np.zeros_like(u)
    for px, py in pts:
        ru, rv = _wd(wu - px), _wd(wv - py)
        d = np.hypot(ru, rv)
        first = d < d1
        second = (~first) & (d < d2)
        d2 = np.where(first, d1, np.where(second, d, d2))
        r2u = np.where(first, r1u, np.where(second, ru, r2u)); r2v = np.where(first, r1v, np.where(second, rv, r2v))
        d1 = np.where(first, d, d1)
        r1u = np.where(first, ru, r1u); r1v = np.where(first, rv, r1v)
    sep = np.maximum(np.hypot(r1u - r2u, r1v - r2v), 1e-6)
    edge = np.abs(d2 * d2 - d1 * d1) / (2 * sep)
    width = 0.0065 + 0.0065 * (0.5 + 0.5 * _pnoise(u, v, 4, 2, 5))   # cracks swell and narrow along their length
    crack = np.exp(-(edge / width) ** 2)
    rim = np.exp(-(edge / (width * 2.2)) ** 2)
    return crack, rim, d1


_MOLTEN_CACHE = {}


def molten(t, n):
    """lava rivers coursing between drifting dark crust (not a still net of cracks: that is the Lava wrap). The field
    drifts one tile along the gun per loop and churns (its warp turns once per loop), so the channels flow, bend,
    meet and part; bright pulses run down them; the crust beside them glows warm"""
    v, u = _grid(n)
    q1 = _pnoise(u, v, 2, TAU * t, 41)
    q2 = _pnoise(u, v, 2, TAU * t + 2.1, 42)
    wu = u + 0.10 * q1 - t                      # (a whole tile per loop: seamless in time)
    wv = v + 0.10 * q2
    f = _pnoise(wu, wv, 2, 0, 43) + 0.3 * _pnoise(2 * wu, 2 * wv, 2, 0, 44)   # (low and broad: a few big rivers, not worms)
    r = np.abs(f)                               # 0 along the rivers (the field's zero lines)
    chan = 1 - _smooth(0.045, 0.12, r)
    core = 1 - _smooth(0.0, 0.06, r)
    near = (1 - _smooth(0.12, 0.28, r)) * (1 - chan)
    pulse = 0.5 + 0.5 * np.sin(TAU * (3 * u - 2 * t) + 2.0 * _pnoise(u, v, 3, TAU * t, 45))
    heat = np.clip(0.30 + 0.70 * pulse ** 1.4, 0, 1)
    # the crust: dark basalt, a faint cooled texture
    grain = 0.5 + 0.5 * _pnoise(u, v, 6, 0, 46)
    rock = np.array([0.085, 0.07, 0.065]) * (0.8 + 0.4 * grain[..., None])
    lava = (np.array([0.62, 0.10, 0.03]) * (1 - heat[..., None]) + np.array([1.0, 0.50, 0.08]) * heat[..., None])
    lava = lava + np.array([0.0, 0.30, 0.42]) * (core * heat)[..., None] * 0.6          # white-hot middles
    rgb = rock * (1 - chan[..., None]) + lava * chan[..., None]
    rgb = rgb + np.array([0.40, 0.09, 0.02]) * (near * heat * 0.45)[..., None]           # the crust's lit edge
    emit = np.clip(chan * (0.35 + 0.65 * heat) * (0.7 + 0.3 * core) + near * heat * 0.12, 0, 1)
    return np.clip(rgb, 0, 1), emit


# ---------------------------------------------------------------------------------------------------- liquid chrome
def _ring(u, v, k, t, seed, width=0.5):
    """isotropic periodic noise (for chrome: _pnoise's six waves streak diagonally): every whole wave vector whose
    length is within width of k, in all directions, random phases; each wave turns once per loop (seamless in time)"""
    rng = np.random.default_rng(seed)
    out = np.zeros_like(u)
    m = 0
    K = int(math.ceil(k + width))
    for a in range(-K, K + 1):
        for b in range(0, K + 1):
            if b == 0 and a <= 0:
                continue                                  # one of each +- pair
            if abs(math.hypot(a, b) - k) > width:
                continue
            turn = rng.choice([-1, 1])
            out += np.sin(TAU * (a * u + b * v) + rng.uniform(0, TAU) + TAU * t * turn)
            m += 1
    return out / math.sqrt(max(m, 1) / 2)


def chrome(t, n):
    """liquid chrome: a flowing rippled metal surface that mirrors a baked studio (a bright graded sky, a sharp
    horizon line, a dark-to-grey floor and two softbox windows), the chrome-ball read. The ripples churn once per
    loop, so the reflections slide and bend like mercury. (27 Nov: the first take, soft grey bands, read as smoke
    to both critics, one called it AI: no mirror. This one mirrors.)"""
    v, u = _grid(n)
    # mostly a still shape that wobbles (a part of it churns once per loop, the warp drifts): mercury, not boiling;
    # a whole-surface churn changed too much per frame for an 8-a-second swap
    wu = u + 0.04 * _ring(u, v, 1.5, t, 21)
    wv = v + 0.04 * _ring(u, v, 1.5, t, 22)
    h = 0.85 * _ring(wu, wv, 3.0, 0, 23) + 0.35 * _ring(wu, wv, 3.0, t, 25) + 0.25 * _ring(wu, wv, 5.0, t, 24)
    # the surface's slope (periodic differences) -> a normal; looking straight on, the reflection follows the normal
    s = 0.055 * n
    gu = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5 * s
    gv = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5 * s
    nz = 1 / np.sqrt(1 + gu * gu + gv * gv)
    nx, ny = -gu * nz, gv * nz                     # ny > 0: the surface faces up (towards the sky)
    # the studio, looked up by the normal: a graded sky above a sharp horizon, a graded floor below
    hz = -0.04
    up = _smooth(hz - 0.008, hz + 0.008, ny)
    sky = 0.34 + 0.66 * _smooth(hz, hz + 0.8, ny) ** 0.8
    d = hz - ny                                 # darkest right under the horizon, lighter further down
    below = 0.03 + 0.47 * _smooth(0.0, 0.85, d) ** 0.7
    lum = up * sky + (1 - up) * below
    # two softbox windows (sharp edged, white), one each side
    box = (_smooth(0.18, 0.21, nx) * (1 - _smooth(0.40, 0.43, nx)) * _smooth(0.26, 0.29, ny) * (1 - _smooth(0.60, 0.63, ny)))
    box2 = (_smooth(-0.55, -0.52, nx) * (1 - _smooth(-0.36, -0.33, nx)) * _smooth(0.10, 0.13, ny) * (1 - _smooth(0.32, 0.35, ny)))
    lum = np.maximum(lum, np.maximum(box, box2 * 0.92))
    # cool sky, a touch warm floor (quiet: near-neutral silver)
    cool = np.array([0.93, 0.97, 1.04])
    warm = np.array([1.00, 0.98, 0.95])
    rgb = lum[..., None] * (up[..., None] * cool + (1 - up[..., None]) * warm)
    emit = np.zeros_like(u)
    return np.clip(rgb, 0, 1), emit


KINDS = {'lavalamp': lavalamp, 'molten': molten, 'chrome': chrome}


def main():
    args = sys.argv[1:]
    out = args.pop(0)
    frames, size = 32, 512
    if '--frames' in args:
        i = args.index('--frames'); frames = int(args[i + 1]); del args[i:i + 2]
    if '--size' in args:
        i = args.index('--size'); size = int(args[i + 1]); del args[i:i + 2]
    kinds = args or list(KINDS)
    os.makedirs(out, exist_ok=True)
    for k in kinds:
        thumbs = []
        for f in range(frames):
            rgb, emit = KINDS[k](f / frames, size)
            Image.fromarray((rgb * 255 + 0.5).astype(np.uint8), 'RGB').save(os.path.join(out, '%s_f%02d_color.png' % (k, f)))
            Image.fromarray((np.clip(emit, 0, 1) * 255 + 0.5).astype(np.uint8), 'L').save(os.path.join(out, '%s_f%02d_emit.png' % (k, f)))
            thumbs.append(Image.fromarray((rgb * 255 + 0.5).astype(np.uint8), 'RGB').resize((160, 160)))
        cols = 8
        rows = (len(thumbs) + cols - 1) // cols
        sheet = Image.new('RGB', (cols * 162, rows * 162), (20, 20, 22))
        for i, th in enumerate(thumbs):
            sheet.paste(th, ((i % cols) * 162, (i // cols) * 162))
        sheet.save(os.path.join(out, '%s_sheet.jpg' % k), quality=88)
        print(k, frames, 'frames at', size)


# ---------------------------------------------------------------------------------------------------- the book
# which wrap wears which kind, and how (ids in Roster: the old Lava Lamp row moves; Molten is new).
# emit: 'own' = its own glow mask per frame, 'color' = the colour picture doubles as the mask, None = no glow
LIVING = {
    'lavalamp': {'kind': 'lavalamp', 'fps': 8, 'rough': 'const_rough_030.png', 'metal': None, 'emit': 'own', 'glow': 1.8},
    'molten': {'kind': 'molten', 'fps': 8, 'rough': 'const_rough_070.png', 'metal': None, 'emit': 'own', 'glow': 4.5,
               'light': {'color': 'ff6a1a', 'lo': 0.35, 'hi': 1.35, 'period': 1.8, 'range': 1.0}},
    # (Liquid Chrome as a living camo failed the blind critics twice on 27 Nov: "smoke", then "melted plastic, glints
    # from no light"; it stays the plain Metal wrap. the chrome kind is kept here for a later try:
    # 'lchrome': {'kind': 'chrome', 'fps': 8, 'rough': 'const_rough_020.png', 'metal': 'const_metal_035.png', ...})
}
# (the shared constant maps, uploaded long ago: tools/roblox/wrap_upload.py const_file)
CONST_IDS = {'const_rough_030.png': 108755586406528, 'const_rough_070.png': 122441279549464,
             'const_rough_010.png': 135427404135006, 'const_metal_100.png': 95597645833170}
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
MANIFEST = os.path.join(REPO, 'roblox', 'assets', 'wraps', 'assets.json')
BOOK = os.path.join(REPO, 'roblox', 'studio-tools', 'WrapLivingBook.luau')


def book(wdir):
    """writes roblox/studio-tools/WrapLivingBook.luau from the uploaded frames (assets.json, by file hash)"""
    import json, hashlib
    sys.path.insert(0, HERE)
    from wrap_partners import partner_of
    man = json.load(open(MANIFEST))
    def idof(f):
        h = hashlib.sha1(open(os.path.join(wdir, f), 'rb').read()).hexdigest()
        e = man.get(h)
        if not e:
            raise SystemExit('not uploaded: ' + f)
        return e['id']
    rows = []
    for wid, spec in LIVING.items():
        k = spec['kind']
        frames = sorted(f for f in os.listdir(wdir) if f.startswith(k + '_f') and f.endswith('_color.png'))
        fr = []
        for f in frames:
            col = idof(f)
            emit = None
            if spec['emit'] == 'own':
                emit = idof(f.replace('_color.png', '_emit.png'))
            elif spec['emit'] == 'color':
                emit = col
            fr.append((col, emit))
        # the still look (frame 1): the chip's band and the gun's glow pieces, as the main book works them out
        first = os.path.join(wdir, frames[0])
        p = partner_of(first, wid)
        a = np.asarray(Image.open(first).convert('RGB').resize((256, 256)), np.float32) / 255.0
        px = a.reshape(-1, 3)
        mx, mn = px.max(1), px.min(1)
        sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
        score = sat * mx if float(sat.max()) > 0.15 else mx
        top = px[score >= np.quantile(score, 0.98)].mean(0)
        top = top * (max(float(top.max()), 0.85) / max(float(top.max()), 1e-3))
        acc = ''.join('%02x' % int(round(max(0.0, min(1.0, float(v))) * 255)) for v in top)
        rows.append((wid, spec, fr, p, acc))
    L = ['-- GENERATED by tools/roblox/wrap_living.py book: do not edit by hand. Run in Studio (Edit) through',
         '-- execute_luau, then save; run it again after WrapBook.luau (whose delete loop clears JankfireWraps).',
         '-- LIVING CAMOS (docs/WRAP-TEXTURES.md "Living camos"): ReplicatedStorage.JankfireWrapLiving.<id> holds one',
         '-- SurfaceAppearance per frame (client/WrapAnim swaps them), and JankfireWraps.<id> is the still picture (frame 1)',
         '-- that WeaponModels.wrap lays and every picker shows. SurfaceAppearance maps are PluginSecurity: Edit only.',
         'local RS = game:GetService("ReplicatedStorage")',
         'local lib = RS:FindFirstChild("JankfireWraps")',
         'local live = RS:FindFirstChild("JankfireWrapLiving")',
         'if not live then live = Instance.new("Folder"); live.Name = "JankfireWrapLiving"; live.Parent = RS end',
         'local function sa(name, col, emit, rough, metal, glow)',
         '\tlocal s = Instance.new("SurfaceAppearance")',
         '\ts.Name = name',
         '\ts.ColorMap = "rbxassetid://" .. col',
         '\tif rough then s.RoughnessMap = "rbxassetid://" .. rough end',
         '\tif metal then s.MetalnessMap = "rbxassetid://" .. metal end',
         '\tif emit then s.EmissiveMaskContent = Content.fromUri("rbxassetid://" .. emit); s.EmissiveStrength = glow end',
         '\treturn s',
         'end',
         'local n = 0']
    for wid, spec, fr, p, acc in rows:
        rough = CONST_IDS[spec['rough']]
        metal = CONST_IDS[spec['metal']] if spec['metal'] else None
        r = str(rough); m = str(metal) if metal else 'nil'
        L.append('do -- %s (%s, %d frames at %d a second)' % (wid, spec['kind'], len(fr), spec['fps']))
        L.append('\tlocal old = live:FindFirstChild("%s"); if old then old:Destroy() end' % wid)
        L.append('\tlocal f = Instance.new("Folder"); f.Name = "%s"' % wid)
        L.append('\tf:SetAttribute("Fps", %d)' % spec['fps'])
        if spec.get('light'):
            lt = spec['light']
            L.append('\tf:SetAttribute("Light", true); f:SetAttribute("LightColor", Color3.fromHex("%s"))' % lt['color'])
            L.append('\tf:SetAttribute("LightLo", %s); f:SetAttribute("LightHi", %s); f:SetAttribute("LightPeriod", %s); f:SetAttribute("LightRange", %s)'
                     % (lt['lo'], lt['hi'], lt['period'], lt['range']))
        L.append('\tlocal F = {')
        for col, emit in fr:
            L.append('\t\t{ %d, %s },' % (col, emit if emit else 'nil'))
        L.append('\t}')
        L.append('\tfor i, x in F do sa(string.format("f%%02d", i - 1), x[1], x[2], %s, %s, %s).Parent = f end' % (r, m, spec['glow']))
        L.append('\tf.Parent = live')
        L.append('\tif lib then')
        L.append('\t\tlocal still = lib:FindFirstChild("%s"); if still then still:Destroy() end' % wid)
        L.append('\t\tlocal s = sa("%s", F[1][1], F[1][2], %s, %s, %s)' % (wid, r, m, spec['glow']))
        L.append('\t\ts:SetAttribute("Swatch", "rbxassetid://" .. F[1][1])')
        L.append('\t\ts:SetAttribute("Dark", Color3.fromHex("%s"))' % p['c'])
        L.append('\t\ts:SetAttribute("Accent", Color3.fromHex("%s"))' % acc)
        L.append('\t\ts:SetAttribute("Living", true)')
        L.append('\t\ts.Parent = lib')
        L.append('\tend')
        L.append('\tn += 1')
        L.append('end')
    L.append('return n .. " living camos built"')
    with open(BOOK, 'w', newline='\n') as fh:
        fh.write('\n'.join(L) + '\n')
    print('wrote', BOOK)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == 'book':
        book(sys.argv[2])
    else:
        main()
