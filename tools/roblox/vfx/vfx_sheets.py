# The VFX pipeline's textures (roblox/docs/VFX-PIPELINE.md, step 2), made in Blender with no image generators:
# flat emission shapes (the flash star, the flame spike, the spark streak, the glow, the tracer core, the shock ring,
# the chips) and a small volume bake (the impact dust puff). Each comes out as a PNG with straight alpha, sized for
# Roblox ParticleEmitter / Beam textures (square; flipbooks 2x2 / 4x4 / 8x8, at most 1024 px).
#
#   blender -b --factory-startup -P tools/roblox/vfx/vfx_sheets.py -- <out dir> [name ...]
#
# names: flash spike spark glow tracer ring chips dust (default: all). The shapes follow the web game's own effects:
# the flash is weapons.js:114-145's 16-point star with its white -> #fff2a0 -> #ff9a1a -> clear orange gradient.
# Image rule (roblox-upload-content-rules): shapes and gradients only, never text, codes, logos or links.
import bpy, sys, os, math, random, tempfile
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
OUT = argv[0]
ONLY = set(argv[1:])
os.makedirs(OUT, exist_ok=True)
TMP = tempfile.mkdtemp(prefix='jfvfx')


def hexc(h, a=1.0):
    h = h.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]  # sRGB -> linear (Blender's ramp is linear)
    return (*c, a)


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 24; sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 0; sc.render.film_transparent = True
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    cam = bpy.data.cameras.new('cam'); cam.type = 'ORTHO'; cam.ortho_scale = 2.0
    co = bpy.data.objects.new('cam', cam); sc.collection.objects.link(co); sc.camera = co
    co.location = (0, 0, 10)
    w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
    return sc


def ramp_mat(name, stops, sx=1.0, sy=1.0, oy=0.0, axis=None, ox=0.0):
    """emission whose colour + alpha come from a ramp over the distance from the centre (an ellipse sx by sy, moved ox
    right and oy up), or over |y| alone (axis='y'). stops: [(pos 0..1, '#rrggbb', alpha)]"""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    tc = N('ShaderNodeTexCoord')
    mp = N('ShaderNodeMapping'); mp.inputs['Location'].default_value = (-ox / sx, -oy / sy, 0); mp.inputs['Scale'].default_value = (1 / sx, 1 / sy, 1)
    L(tc.outputs['Object'], mp.inputs['Vector'])
    if axis == 'y':
        sep = N('ShaderNodeSeparateXYZ'); L(mp.outputs['Vector'], sep.inputs['Vector'])
        ab = N('ShaderNodeMath'); ab.operation = 'ABSOLUTE'; L(sep.outputs['Y'], ab.inputs[0]); fac = ab.outputs[0]
    else:
        ln = N('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; L(mp.outputs['Vector'], ln.inputs[0]); fac = ln.outputs['Value']
    rp = N('ShaderNodeValToRGB'); L(fac, rp.inputs['Fac'])
    cr = rp.color_ramp; cr.interpolation = 'LINEAR'
    cr.elements[0].position = stops[0][0]; cr.elements[0].color = hexc(stops[0][1], stops[0][2])
    cr.elements[1].position = stops[-1][0]; cr.elements[1].color = hexc(stops[-1][1], stops[-1][2])
    for pos, col, a in stops[1:-1]:
        cr.elements.new(pos).color = hexc(col, a)
    em = N('ShaderNodeEmission'); em.inputs['Strength'].default_value = 1.0; L(rp.outputs['Color'], em.inputs['Color'])
    tr = N('ShaderNodeBsdfTransparent'); mix = N('ShaderNodeMixShader')
    L(rp.outputs['Alpha'], mix.inputs['Fac']); L(tr.outputs[0], mix.inputs[1]); L(em.outputs[0], mix.inputs[2])
    out = N('ShaderNodeOutputMaterial'); L(mix.outputs[0], out.inputs['Surface'])
    return m


def poly(name, pts, mat, z=0.0):
    me = bpy.data.meshes.new(name)
    v = [(0.0, 0.0, z)] + [(x, y, z) for x, y in pts]
    f = [(0, 1 + i, 1 + (i + 1) % len(pts)) for i in range(len(pts))]
    me.from_pydata(v, [], f); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o); o.data.materials.append(mat)
    return o


def render(cell):
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = cell; sc.render.resolution_percentage = 100
    p = os.path.join(TMP, 'r.png'); sc.render.filepath = p
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(p); px = np.array(img.pixels[:], dtype=np.float32).reshape(cell, cell, 4); bpy.data.images.remove(img)
    return px  # bottom row first, straight alpha


def save(name, cells, n, cell):
    sheet = np.zeros((n * cell, n * cell, 4), dtype=np.float32)
    for k, px in enumerate(cells):
        r, c = k // n, k % n
        sheet[(n - 1 - r) * cell:(n - r) * cell, c * cell:(c + 1) * cell] = px
    img = bpy.data.images.new(name, n * cell, n * cell, alpha=True); img.alpha_mode = 'STRAIGHT'
    img.pixels[:] = np.clip(sheet, 0, 1).reshape(-1)
    path = os.path.join(OUT, name + '.png'); img.filepath_raw = path; img.file_format = 'PNG'; img.save()
    a = sheet[:, :, 3]
    print('SHEET', name, '%dx%d' % (n * cell, n * cell), 'cover %.3f' % float((a > 0.05).mean()), os.path.getsize(path) // 1024, 'kB', flush=True)


STAR_STOPS = [(0.0, '#ffffff', 1.0), (0.25, '#fff2a0', 1.0), (0.6, '#ff9a1a', 1.0), (1.0, '#ff5000', 0.0)]
# round 2 (the critic: the spikes read too orange; the web's orange is a thin rim on the tips): pale yellow down most of
# each spike, orange only on the outer fifth
STAR2_STOPS = [(0.0, '#ffffff', 1.0), (0.3, '#fff8d8', 1.0), (0.7, '#fff2a0', 1.0), (0.86, '#ffb84a', 0.95), (1.0, '#ff8a1a', 0.0)]


def star_pts(points, r_out, r_in, rnd, jit):
    pts = []
    for i in range(points * 2):
        a = math.pi * 2 * i / (points * 2)
        r = (r_out * (1 - jit * rnd.random())) if i % 2 == 0 else r_in * (0.9 + 0.2 * rnd.random())
        pts.append((math.cos(a) * r, math.sin(a) * r))
    return pts


def make_flash():
    """the face star: 4 cells (2x2), each the web's 16-point star (outer 1, inner 6/16) with the spike tips jittered a
    little, so a Random flipbook flickers between them the way the web re-rolls the star every frame"""
    cells = []
    for k in range(4):
        fresh(); rnd = random.Random(11 + k)
        m = ramp_mat('star', STAR2_STOPS)
        poly('star', star_pts(16, 0.98, 0.37, rnd, 0.0 if k == 0 else 0.22), m)
        cells.append(render(256))
    save('vfx_flash_star', cells, 2, 256)


def make_spike():
    """a side spike: the web's 0.4 x 0.14 m plane with the star texture squeezed onto it; here a flame tongue drawn
    upright (the particle's up runs along the barrel), hot at the root, orange at the point"""
    fresh()
    pts = []
    for i in range(48):
        u = i / 47  # 0 = root (bottom), 1 = tip (top)
        y = -0.95 + 1.9 * u
        w = 0.3 * math.sin(math.pi * min(1.0, u * 1.15 + 0.02)) ** 0.8 * (1 - u) ** 0.35 + 0.004
        pts.append((w, y))
    pts += [(-x, y) for x, y in reversed(pts)]
    m = ramp_mat('spike', STAR_STOPS, sx=0.3, sy=1.55, oy=-0.6)
    poly('spike', pts, m)
    save('vfx_spike', [render(256)], 1, 256)


def make_spike_h():
    """the same flame lying down for a Beam (a Beam's texture runs u along it): root at the left edge, tip at the right"""
    fresh()
    pts = []
    for i in range(48):
        u = i / 47
        x = -0.95 + 1.9 * u
        w = 0.3 * math.sin(math.pi * min(1.0, u * 1.15 + 0.02)) ** 0.8 * (1 - u) ** 0.35 + 0.004
        pts.append((x, w))
    pts += [(x, -y) for x, y in reversed(pts)]
    m = ramp_mat('spikeh', STAR_STOPS, sx=1.55, sy=0.3, ox=-0.6)
    poly('spikeh', pts, m)
    save('vfx_spike_h', [render(256)], 1, 256)


def make_spark():
    """a spark streak: a thin stadium, white-hot down the middle, warm at the edges (the particle stretches it along
    its flight)"""
    fresh()
    pts, rr, half = [], 0.13, 0.82
    for i in range(24):
        a = math.pi * i / 23
        pts.append((math.cos(a) * rr, half + math.sin(a) * rr))
    for i in range(24):
        a = math.pi + math.pi * i / 23
        pts.append((math.cos(a) * rr, -half + math.sin(a) * rr))
    m = ramp_mat('spark', [(0.0, '#ffffff', 1.0), (0.45, '#fff6d0', 1.0), (0.8, '#ffc060', 0.55), (1.0, '#ff8020', 0.0)], sx=0.135, sy=0.95)
    poly('spark', pts, m)
    save('vfx_spark', [render(128)], 1, 128)


def make_glow():
    """a soft round glow (the light round the flash and the blast's core): falls off like a lamp in haze"""
    fresh()
    pts = [(math.cos(a) * 0.99, math.sin(a) * 0.99) for a in np.linspace(0, math.tau, 96, endpoint=False)]
    m = ramp_mat('glow', [(0.0, '#ffffff', 1.0), (0.12, '#ffffff', 0.82), (0.35, '#ffffff', 0.32), (0.65, '#ffffff', 0.08), (1.0, '#ffffff', 0.0)])
    poly('glow', pts, m)
    save('vfx_glow', [render(256)], 1, 256)


def make_tracer():
    """a Beam texture: u runs along the beam, v across it. a white-hot core with soft edges, the same all along"""
    fresh()
    m = ramp_mat('tracer', [(0.0, '#ffffff', 1.0), (0.22, '#ffffff', 0.95), (0.5, '#ffffff', 0.45), (0.8, '#ffffff', 0.1), (1.0, '#ffffff', 0.0)], axis='y')
    poly('tracer', [(1.05, -1.05), (1.05, 1.05), (-1.05, 1.05), (-1.05, -1.05)], m)
    save('vfx_tracer', [render(64)], 1, 64)


def make_lines():
    """the hologram's scanline: one soft horizontal line per tile (a Texture repeats it up the model), a bright thin
    middle and a soft glow either side, nothing else (plain lines, nothing like a code)"""
    fresh()
    m = ramp_mat('lines', [(0.0, '#ffffff', 0.85), (0.12, '#ffffff', 0.55), (0.3, '#ffffff', 0.12), (0.55, '#ffffff', 0.0), (1.0, '#ffffff', 0.0)], axis='y')
    poly('lines', [(1.05, -1.05), (1.05, 1.05), (-1.05, 1.05), (-1.05, -1.05)], m)
    save('vfx_lines', [render(64)], 1, 64)


def make_feather():
    """a soft white feather for the angel skins: a thin quill, a curved vane wider on one side, the tip rounded; white
    to pale grey so the particle's colour tints it"""
    fresh()
    vane = []
    for i in range(40):
        u = i / 39  # base -> tip along y
        y = -0.85 + 1.75 * u
        bend = 0.08 * math.sin(u * math.pi)  # a slight curve
        w = 0.34 * math.sin(math.pi * min(1.0, u * 1.08)) ** 0.7 * (1 - 0.35 * u)
        vane.append((bend + w, y))
    left = []
    for i in range(40):
        u = 1 - i / 39
        y = -0.85 + 1.75 * u
        bend = 0.08 * math.sin(u * math.pi)
        w = 0.3 * math.sin(math.pi * min(1.0, u * 1.08)) ** 0.7 * (1 - 0.35 * u)
        left.append((bend - w, y))
    poly('vane', vane + left, ramp_mat('v', [(0.0, '#ffffff', 1.0), (0.55, '#f6f4f0', 0.95), (0.85, '#e2ded8', 0.6), (1.0, '#d8d4ce', 0.0)], sx=0.38, sy=1.0))
    quill = [(0.012, -0.98), (0.012 + 0.08 * math.sin(math.pi * 0.5), 0.0), (0.006, 0.9), (-0.006, 0.9), (-0.012 + 0.08 * math.sin(math.pi * 0.5), 0.0), (-0.012, -0.98)]
    poly('quill', quill, ramp_mat('q', [(0.0, '#c8c2b8', 1.0), (1.0, '#c8c2b8', 1.0)]), z=0.01)
    save('vfx_feather', [render(128)], 1, 128)


def make_petal():
    """a cherry blossom petal (for the Japanese set): rounded, a small notch at the tip, pale in the middle; white-pink so
    the particle's colour tints it"""
    fresh()
    pts = []
    for i in range(64):
        a = math.tau * i / 64
        r = 0.8 * (0.62 + 0.38 * math.cos(a - math.pi / 2)) ** 0.55  # wide at the top, narrowing to the base
        x, y = math.cos(a) * r * 0.78, math.sin(a) * r - 0.1
        if abs(a - math.pi / 2) < 0.2: y -= 0.12 * (1 - abs(a - math.pi / 2) / 0.2)  # the notch
        pts.append((x, y))
    poly('petal', pts, ramp_mat('p', [(0.0, '#fff6fa', 1.0), (0.55, '#ffe0ec', 1.0), (0.85, '#ffc8dc', 0.95), (1.0, '#ffc0d6', 0.0)], sx=0.8, sy=0.8, oy=-0.1))
    save('vfx_petal', [render(64)], 1, 64)


def make_sparkle():
    """a four-point sparkle (the owner: sparkles you notice in first person are real shapes): long thin points, a
    small bright core, white so the colour tints it"""
    fresh()
    pts = []
    for i in range(8):
        a = math.tau * i / 8
        r = 0.97 if i % 2 == 0 else 0.13
        pts.append((math.cos(a) * r, math.sin(a) * r))
    poly('spk', pts, ramp_mat('s', [(0.0, '#ffffff', 1.0), (0.2, '#ffffff', 0.95), (0.6, '#ffffff', 0.6), (1.0, '#ffffff', 0.0)]))
    pts2 = [(math.cos(a) * 0.3, math.sin(a) * 0.3) for a in np.linspace(0, math.tau, 48, endpoint=False)]
    poly('core', pts2, ramp_mat('c', [(0.0, '#ffffff', 0.9), (0.4, '#ffffff', 0.35), (1.0, '#ffffff', 0.0)], sx=0.3, sy=0.3), z=-0.01)
    save('vfx_sparkle', [render(128)], 1, 128)


def make_bubble():
    """a soap bubble (the ducky skin): mostly clear, a soft pale rim, one small highlight up-left; white so the colour
    tints it"""
    fresh()
    disc = [(math.cos(a) * 0.96, math.sin(a) * 0.96) for a in np.linspace(0, math.tau, 96, endpoint=False)]
    poly('film', disc, ramp_mat('f', [(0.0, '#ffffff', 0.06), (0.62, '#ffffff', 0.1), (0.86, '#f2fbff', 0.45), (0.95, '#ffffff', 0.75), (1.0, '#ffffff', 0.0)]))
    hl = [(math.cos(a) * 0.17 - 0.38, math.sin(a) * 0.11 + 0.42) for a in np.linspace(0, math.tau, 40, endpoint=False)]
    poly('hl', hl, ramp_mat('h', [(0.0, '#ffffff', 0.95), (0.6, '#ffffff', 0.6), (1.0, '#ffffff', 0.0)], sx=0.17, sy=0.11, ox=-0.38, oy=0.42), z=0.01)
    save('vfx_bubble', [render(128)], 1, 128)


def make_ring():
    """the shock ring: a bright rim with a faint wash inside, nothing in the middle (flat on the floor)"""
    fresh()
    pts = [(math.cos(a) * 0.995, math.sin(a) * 0.995) for a in np.linspace(0, math.tau, 192, endpoint=False)]
    m = ramp_mat('ring', [(0.0, '#ffffff', 0.0), (0.55, '#ffffff', 0.0), (0.8, '#ffffff', 0.14), (0.9, '#ffffff', 0.55), (0.955, '#ffffff', 1.0), (1.0, '#ffffff', 0.0)])
    poly('ring', pts, m)
    save('vfx_ring', [render(512)], 1, 512)


def make_chips():
    """surface chips: 4 cells of small irregular flakes, light grey with a darker underside (the particle's colour and
    the room's light finish them). the web's impact is 10 grey squares; these are its polished version"""
    cells = []
    for k in range(4):
        fresh(); rnd = random.Random(40 + k)
        n = 5 + k % 3
        pts = []
        for i in range(n):
            a = math.tau * (i + rnd.uniform(-0.25, 0.25)) / n
            r = 0.55 + rnd.uniform(-0.18, 0.3)
            pts.append((math.cos(a) * r, math.sin(a) * r))
        poly('chip', pts, ramp_mat('d', [(0.0, '#e8e8e8', 1.0), (1.0, '#c4c4c4', 1.0)], sx=0.85, sy=0.85), z=0.0)
        cells.append(render(64))
    save('vfx_chips', cells, 2, 64)


def make_dust():
    """the impact puff: 16 frames (4x4) of a small volume of dust that bursts out of a point, rolls open and thins away,
    lit from the top left, pale grey so the particle's colour gives it the surface's colour"""
    fresh()
    sc = bpy.context.scene; FR = 16
    sc.frame_start, sc.frame_end = 1, FR; sc.cycles.samples = 32; sc.cycles.max_bounces = 2; sc.cycles.volume_bounces = 1
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0)); box = bpy.context.object
    m = bpy.data.materials.new('dust'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new

    def val(keys):
        n = N('ShaderNodeValue')
        for f, v in keys: n.outputs[0].default_value = v; n.outputs[0].keyframe_insert('default_value', frame=f)
        return n.outputs[0]

    def math_(op, a, b):
        n = N('ShaderNodeMath'); n.operation = op
        for i, x in enumerate((a, b)):
            if isinstance(x, float): n.inputs[i].default_value = x
            else: L(x, n.inputs[i])
        return n.outputs[0]
    tc = N('ShaderNodeTexCoord')
    nz = N('ShaderNodeTexNoise'); nz.noise_dimensions = '4D'; nz.inputs['Scale'].default_value = 3.2; nz.inputs['Detail'].default_value = 4.0
    L(tc.outputs['Object'], nz.inputs['Vector']); L(val([(1, 0.0), (FR, 0.9)]), nz.inputs['W'])
    ln = N('ShaderNodeVectorMath'); ln.operation = 'LENGTH'; L(tc.outputs['Object'], ln.inputs[0])
    R = val([(1, 0.12), (4, 0.42), (9, 0.62), (FR, 0.78)])                         # bursts out, then creeps
    edge = math_('ADD', math_('SUBTRACT', R, ln.outputs['Value']), math_('MULTIPLY', math_('SUBTRACT', nz.outputs['Fac'], 0.5), 0.55))
    eat = val([(1, 0.0), (7, 0.02), (FR, 0.34)])                                    # eaten away from the inside out at the end
    body = math_('MINIMUM', math_('MAXIMUM', math_('MULTIPLY', math_('SUBTRACT', edge, eat), 14.0), 0.0), 1.0)
    dens = val([(1, 9.0), (5, 7.0), (11, 3.5), (FR, 0.6)])
    vol = N('ShaderNodeVolumePrincipled'); vol.inputs['Color'].default_value = (0.78, 0.77, 0.75, 1)
    L(math_('MULTIPLY', body, dens), vol.inputs['Density'])
    out = N('ShaderNodeOutputMaterial'); L(vol.outputs['Volume'], out.inputs['Volume']); box.data.materials.append(m)
    if nt.animation_data and nt.animation_data.action:
        for fc in getattr(nt.animation_data.action, 'fcurves', []):
            for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 4.5; so = bpy.data.objects.new('sun', sun); sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(40), math.radians(-35), math.radians(-30))
    sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.75, 0.77, 0.82, 1)
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
    cells = []
    edgefade = np.clip((0.5 - np.abs(np.linspace(-0.5, 0.5, 128))) * 14, 0, 1); edgefade = edgefade[None, :] * edgefade[:, None]
    for f in range(FR):
        sc.frame_set(1 + f)
        px = render(128); px[:, :, 3] *= edgefade; cells.append(px)
    save('vfx_dust_4x4', cells, 4, 128)


JOBS = {'flash': make_flash, 'spike': make_spike, 'spikeh': make_spike_h, 'spark': make_spark, 'glow': make_glow, 'tracer': make_tracer, 'ring': make_ring,
        'chips': make_chips, 'dust': make_dust, 'lines': make_lines, 'feather': make_feather, 'petal': make_petal,
        'sparkle': make_sparkle, 'bubble': make_bubble}
for name, fn in JOBS.items():
    if not ONLY or name in ONLY: fn()
