# A KATANA AND ITS SHEATH FOR A PRO ANIMATOR, BLANK AND TIDECREST (20 Nov 2026). The owner: "can you give me a blank
# katana with sheathe in the style of rivals? I am passing the cutscene to a pro animator!", then "Make a rivals katana
# then apply the skin to it!" Our own model, built here in the kit's chunky style (few big readable shapes, soft bevels,
# flat colours), to the in-game katana's sizes; never the bought katana pack's sword, never anyone else's katana.
#   STYLES  blank      neutral greys, a rounded-square iron guard, a dark diamond wrap
#           tidecrest  the live Tidecrest katana's skin (tools/roblox/gun_sets_japan2.py katana_jp_a, the J-A maki-e the
#                      owner picked) laid on this base: a dark blade, a pale edge under a waving temper line, a gold line
#                      along the back, a gold collar, a pierced iron guard with a gold rim, black lacquer handle under a
#                      gold diamond wrap, gold blossom clusters (pale petals, pink hearts) each side, beaded gold collar
#                      and cap; a matching black lacquer sheath with gold fittings, gold bands, a blossom cluster, red cord
# Sizes follow tools/roblox/finisher_r15.py (the hand's grip 0.6 studs behind the guard, a 2.3 stud blade).
#   blender -b --factory-startup -P tools/blender/katana_for_animator.py -- <out_dir>      models, rigs, renders
#   py tools/blender/katana_for_animator.py sheet <out_dir>                                 the labelled render sheets
# writes, for each style, into out_dir/<style>/:
#   katana.glb/.fbx, sheath.glb/.fbx           each on its own, its root at its own origin (Grip / SheathMouth)
#   katana_sheath_drawn.glb/.fbx, katana_sheath_sheathed.glb/.fbx      the two together
#   r15_katana_rig.fbx + .blend                a blank block R15 (the place's own part sizes and joints) with two extra
#                                              bones: "Katana" on RightHand (at Grip) and "Sheath" on LowerTorso (at the
#                                              left hip), the katana and the sheath riding on them
#   roblox/katana_sheath_roblox.glb            one piece per colour, for the Studio upload that makes the .rbxm
# and out_dir/renders/<style>_<pose>_<view>.png + marks.json, out_dir/markers.json.
# Built in ROBLOX axes and studs (x right, y up, -z forward; the blade along the katana's -Z, its edge down) and turned
# into Blender's by R2B (Z up, the rig facing -Y); 1 Blender unit = 1 stud. Every part has UVs (one atlas per model).
import sys, os, json, math

try:
    import bpy, bmesh
    from mathutils import Vector, Matrix
except ImportError:  # (plain Python: the sheet step)
    bpy = None

# ------------------------------------------------------------------------------------------------ sizes (studs)
Z_GUARD_F, Z_GUARD_B = -0.604, -0.524      # the guard (tsuba): blade-side and handle-side faces
SEPPA = 0.016                              # each washer (seppa)
Z_FACE = Z_GUARD_F - SEPPA                 # -0.62: the front washer's face = GuardFace = the sheath's mouth face
# THE LENGTH (owner, 20 Nov 19:20: "Shouldnt the blade and sheathe be longer for the animation?"): the blade and the
# sheath are the in-game katana's times LENGTH (handle, guard and pommel unchanged). 1.4: the sheathed tip ends behind
# the calf on the R15 at rest, and the sheath (3.36 studs) is the finishers' prop scabbard's length (3.42). Pass
# "--length 1.0" for the in-game proportions.
LENGTH = float(sys.argv[sys.argv.index('--length') + 1]) if '--length' in sys.argv else 1.4
BLADE_L = round(2.30 * LENGTH, 4)
Z_TIP = Z_FACE - BLADE_L                   # -2.92 at the in-game length
SORI = 0.10                                # the curve: the tip rises this far toward the back
H0, H1, T0, T1 = 0.20, 0.16, 0.05, 0.032   # the blade's height / thickness at the collar and where the point starts
KISSAKI = 0.88                             # the point starts this far along
Z_HANDLE_F = Z_GUARD_B + SEPPA             # -0.508: the handle's front (the collar, fuchi)
Z_HANDLE_B = 0.45                          # its back end (the pommel's face); the pommel's cap to 0.49
HA, HB = 0.068, 0.085                      # the handle's half thickness / half height
SAYA_L = BLADE_L + 0.14                    # the sheath: mouth face to the end cap's tip
SW0, SH0, SW1, SH1 = 0.15, 0.30, 0.13, 0.25  # its width / height at the mouth and at the end
KNOB_S = 0.42                              # the side knob (kurikata) this far down from the mouth
GRIP_IN_HAND = (0, -0.12, 0)               # finisher_r15's grip: the handle through the closed right hand
HIP_MOUTH = (-1.12, 0.10, -0.75)           # the sheath's mouth on the LowerTorso (finisher_r15's sheath_line, moved
HIP_TIP = (-1.25, -1.60, 2.20)             # 0.17 out so it clears the leg) and the way it runs: back and down

COL = {'steel': 'a7adb5', 'edge': 'e6eaef', 'spine': '7a8089', 'brass': '9c8c6a', 'iron': '3a3d45',
       'core': 'd6d1c4', 'wrap': '2b2e35', 'lacquer': '2a2c33', 'horn': 'a9a49b', 'cord': '6f675b', 'slot': '141519',
       'body': 'cfcbc3',
       # Tidecrest (gun_sets_japan2.py: katana_jp_a's slots and the J-A palette)
       'blade': '2c2f37', 'paleedge': 'cfd3d9', 'tciron': '34353b', 'lac': '2a2526', 'gold': 'c4a056', 'goldd': '8f7238',
       'pale': 'ecdcae', 'heart': 'd49aa6', 'red': '8a2e27'}
SHINY = ('steel', 'edge', 'spine', 'brass', 'blade', 'paleedge', 'gold', 'goldd')
STYLE = ['blank']
STYLES = ('blank', 'tidecrest')


def blade_c(u): return SORI * u ** 1.6     # the blade's centre line rise at u (0 at the collar, 1 at the tip)


def blade_section(u):
    """(top, bottom, thickness) of the blade at u"""
    h = H0 + (H1 - H0) * min(u / KISSAKI, 1.0)
    t = T0 + (T1 - T0) * u
    top = blade_c(u) + H0 / 2 - (H0 - h) * 0.25
    if u > KISSAKI:                           # the point: the edge sweeps up to meet the back
        k = (u - KISSAKI) / (1 - KISSAKI)
        h = h * (1 - k ** 1.35) + 0.002
        t = t * (1 - 0.8 * k) + 0.002
        top -= 0.008 * k
    return top, top - h, t


TIP = (0.0, round(blade_section(1.0)[0] - 0.001, 4), round(Z_TIP, 4))
MARKS_K = {'Grip': (0, 0, 0), 'GuardFace': (0, 0, Z_FACE), 'BladeTip': TIP}
MARKS_S = {'SheathMouth': (0, 0, 0), 'SheathHip': (-(SW0 / 2 + 0.045), 0.0, -KNOB_S)}

if bpy:
    def V(t): return Vector(t)

    def R2B(v): return Vector((-v[0], v[2], v[1]))
    RB = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))   # R2B as a 4x4 (its own inverse)

    MATS = {}

    def lin(h):
        c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)

    def mat(name):
        if name in MATS: return MATS[name]
        m = bpy.data.materials.new(name); m.use_nodes = True
        b = m.node_tree.nodes['Principled BSDF']
        b.inputs['Base Color'].default_value = (*lin(COL[name]), 1)
        b.inputs['Roughness'].default_value = 0.32 if name in SHINY else 0.55
        b.inputs['Metallic'].default_value = 0.55 if name in SHINY else 0.0
        m.diffuse_color = (*lin(COL[name]), 1)
        MATS[name] = m
        return m

    def obj(name, bm, materials, smooth=True, bevel=0.0, segs=2, parent=None):
        me = bpy.data.meshes.new(name)
        bm.normal_update(); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(o)
        for m_ in materials: o.data.materials.append(mat(m_))
        for p in o.data.polygons: p.use_smooth = smooth
        if smooth:
            try: o.data.set_sharp_from_angle(angle=math.radians(40))
            except Exception: pass
        if bevel > 0:
            md = o.modifiers.new('bev', 'BEVEL'); md.width = bevel; md.segments = segs
            md.limit_method = 'ANGLE'; md.angle_limit = math.radians(35); md.use_clamp_overlap = True
        if smooth:
            try: o.modifiers.new('wn', 'WEIGHTED_NORMAL').keep_sharp = True
            except Exception: pass
        if parent: o.parent = parent
        return o

    def loft(sections, cap0=True, cap1=True, mat_of=None, bm=None, mat=0):
        """sections: rings of Roblox points (same count each); quads between rings, caps at the ends"""
        bm = bm or bmesh.new()
        rings = [[bm.verts.new(R2B(p)) for p in s] for s in sections]
        n = len(sections[0])
        new = []
        for a, b in zip(rings, rings[1:]):
            for i in range(n):
                j = (i + 1) % n
                f = bm.faces.new([a[i], a[j], b[j], b[i]])
                f.material_index = mat_of(i) if mat_of else mat
                new.append(f)
        if cap0: f = bm.faces.new(rings[0][::-1]); f.material_index = mat; new.append(f)
        if cap1: f = bm.faces.new(rings[-1]); f.material_index = mat; new.append(f)
        bmesh.ops.recalc_face_normals(bm, faces=new)
        return bm

    def oval(cx, cy, z, a, b, n=24, p=2.0):
        out = []
        for k in range(n):
            t = 2 * math.pi * k / n
            c, s = math.cos(t), math.sin(t)
            out.append((cx + a * math.copysign(abs(c) ** (2 / p), c), cy + b * math.copysign(abs(s) ** (2 / p), s), z))
        return out

    def annulus(rout, rin, z0, z1, n=48, cy=0.0, bm=None, mat=0):
        """a flat ring (round, in the x-y plane) from z0 to z1"""
        bm = bm or bmesh.new()
        def ring(r, z): return [bm.verts.new(R2B((r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n), z))) for k in range(n)]
        o0, o1, i0, i1 = ring(rout, z0), ring(rout, z1), ring(rin, z0), ring(rin, z1)
        new = []
        for k in range(n):
            j = (k + 1) % n
            for q in ([o0[k], o0[j], o1[j], o1[k]], [i0[j], i0[k], i1[k], i1[j]], [o0[j], o0[k], i0[k], i0[j]], [o1[k], o1[j], i1[j], i1[k]]):
                f = bm.faces.new(q); f.material_index = mat; new.append(f)
        bmesh.ops.recalc_face_normals(bm, faces=new)
        return bm

    def frame_pt(face, cu, cv, h):
        """a point on a flat face: face = (axis, sign, plane value); (cu, cv) along its plane, h out of it"""
        ax, sg, pv = face
        if ax == 'x': return (sg * (pv + h), cv, cu)       # side faces: u = z, v = y
        return (cv, sg * (pv + h), cu)

    def blossom(bm, face, cu, cv, R, h0, h1, turn=90.0, mp=0, mh=1):
        """a five-petal sakura blossom standing on a flat face: round petals (material mp) round a heart (mh)"""
        for k in range(5):
            a = math.radians(turn + 72 * k)
            ca, sa = math.cos(a), math.sin(a)
            ring = []
            for i in range(14):
                t = 2 * math.pi * i / 14
                lu, lv = 0.5 * R * math.cos(t) + 0.5 * R, 0.34 * R * math.sin(t)
                if lu > 0.9 * R: lv *= 0.75                     # (the notch at the petal's tip, softened)
                ring.append((cu + lu * ca - lv * sa, cv + lu * sa + lv * ca))
            loft([[frame_pt(face, u, v, h) for u, v in ring] for h in (h0, h1)], bm=bm, mat=mp)
        hr = [(cu + 0.26 * R * math.cos(2 * math.pi * i / 12), cv + 0.26 * R * math.sin(2 * math.pi * i / 12)) for i in range(12)]
        loft([[frame_pt(face, u, v, h) for u, v in hr] for h in (h0, h1 + 0.003)], bm=bm, mat=mh)

    def cluster(bm, face, cu, cv, R, h0, h1):
        for (du, dv), k, t in zip(((0, 0), (0.95, -0.45), (-0.95, 0.4)), (1.0, 0.72, 0.68), (90, 54, 126)):
            blossom(bm, face, cu + du * R, cv + dv * R, R * k, h0, h1 - (1 - k) * 0.006, turn=t)

    def beads(bm, z, a, b, r, n, mat=0):
        """a ring of n gold beads round an oval (half sizes a, b) at z"""
        for k in range(n):
            t = 2 * math.pi * k / n
            c = R2B((a * math.cos(t), b * math.sin(t), z))
            res = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
            for v in res['verts']: v.co += c
            for f in {f for v in res['verts'] for f in v.link_faces}: f.material_index = mat

    # -------------------------------------------------------------------------------------------- the katana
    def blade_mesh():
        tc = STYLE[0] == 'tidecrest'
        st = []
        N = 96
        for i in range(N + 1):
            u = i / N
            z = Z_FACE - BLADE_L * u
            top, bot, t = blade_section(u)
            h = top - bot
            if tc and u < KISSAKI:   # the temper line waves (five gentle waves, as the live skin's)
                f = 0.66 + 0.07 * math.sin(2 * math.pi * round(5 * LENGTH) * u) * min(1.0, u / 0.08 + 0.2)
            else:
                f = 0.68
            ridge, bev = top - h * 0.30, top - h * f
            st.append([(0, bot, z), (t * 0.36, bev, z), (t * 0.5, ridge, z), (t * 0.4, top, z),
                       (-t * 0.4, top, z), (-t * 0.5, ridge, z), (-t * 0.36, bev, z)])
        if tc:   # (materials: 0 the dark blade, 1 the pale edge)
            m = {0: 1, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 1}
        else:    # (0 steel, 1 the bright edge band, 2 the darker upper flats and back)
            m = {0: 1, 1: 0, 2: 2, 3: 2, 4: 2, 5: 0, 6: 1}
        bm = loft(st, mat_of=lambda i: m[i])
        if tc:   # the gold line inlaid along the back on each face, from the collar to past half way
            for sd in (-1, 1):
                rings = []
                for i in range(25):
                    u = 0.02 + 0.58 * i / 24
                    z = Z_FACE - BLADE_L * u
                    top, bot, t = blade_section(u)
                    h = top - bot
                    w = 1.0 if u < 0.5 else max(0.15, 1 - (u - 0.5) / 0.1 * 0.85)
                    ya, yb = top - h * (0.17 + 0.05 * w), top - h * (0.17 - 0.05 * w)
                    def xf(y): return t * 0.4 + t * 0.1 * (top - y) / (0.3 * h)
                    rings.append([(sd * (xf(ya) - 0.002), ya, z), (sd * (xf(ya) + 0.005), ya, z),
                                  (sd * (xf(yb) + 0.005), yb, z), (sd * (xf(yb) - 0.002), yb, z)])
                loft(rings, bm=bm, mat=2)
        return bm

    def handle_w(z):
        u = (z - Z_HANDLE_F) / (Z_HANDLE_B - Z_HANDLE_F)
        return 1.0 - 0.07 * math.sin(math.pi * min(max(u, 0), 1))

    def katana(root):
        tc = STYLE[0] == 'tidecrest'
        metal, guardc, core, wrapc, fit = ('gold', 'tciron', 'lac', 'gold', 'gold') if tc else ('brass', 'iron', 'core', 'wrap', 'iron')
        obj('kat_blade', blade_mesh(), ['blade', 'paleedge', 'gold'] if tc else ['steel', 'edge', 'spine'], bevel=0.004, segs=1, parent=root)
        collar_l = 0.13 if tc else 0.10
        obj('kat_collar', loft([oval(0, 0.006, z, T0 / 2 + 0.02, H0 / 2 + 0.014, 20, 3.0) for z in (Z_FACE + 0.002, Z_FACE - collar_l)]),
            [metal], bevel=0.01, parent=root)
        for nm, (z0, z1) in (('kat_seppa_front', (Z_FACE, Z_GUARD_F)), ('kat_seppa_back', (Z_GUARD_B, Z_GUARD_B + SEPPA))):
            obj(nm, loft([oval(0, 0, z0, 0.088, 0.118, 28, 3.2), oval(0, 0, z1, 0.088, 0.118, 28, 3.2)]), [metal],
                bevel=0.005, parent=root)
        if tc:   # the pierced guard: a centre plate, eight spokes, the outer ring (iron), a gold rim round it
            bm = loft([oval(0, 0, z, 0.112, 0.112, 40) for z in (Z_GUARD_F, Z_GUARD_B)])
            annulus(0.226, 0.176, Z_GUARD_F, Z_GUARD_B, 56, bm=bm)
            for k in range(8):
                a = 2 * math.pi * k / 8 + math.pi / 8
                ca, sa = math.cos(a), math.sin(a)
                q = [(0.1 * ca - 0.024 * sa, 0.1 * sa + 0.024 * ca), (0.185 * ca - 0.03 * sa, 0.185 * sa + 0.03 * ca),
                     (0.185 * ca + 0.03 * sa, 0.185 * sa - 0.03 * ca), (0.1 * ca + 0.024 * sa, 0.1 * sa - 0.024 * ca)]
                loft([[(x, y, z) for x, y in q] for z in (Z_GUARD_F + 0.008, Z_GUARD_B - 0.008)], bm=bm)
            obj('kat_guard', bm, ['tciron'], bevel=0.008, segs=2, parent=root)
            obj('kat_guard_rim', annulus(0.24, 0.222, Z_GUARD_F - 0.006, Z_GUARD_B + 0.006, 64), ['gold'], bevel=0.005, parent=root)
        else:
            obj('kat_guard', loft([oval(0, 0, Z_GUARD_F, 0.205, 0.225, 44, 3.4), oval(0, 0, Z_GUARD_B, 0.205, 0.225, 44, 3.4)]),
                ['iron'], bevel=0.02, segs=3, parent=root)
        secs = []
        for k in range(11):
            z = Z_HANDLE_F + 0.05 + (Z_HANDLE_B - 0.05 - Z_HANDLE_F - 0.05) * k / 10
            w = handle_w(z)
            secs.append(oval(0, 0, z, HA * w, HB * w, 28, 2.2))
        obj('kat_tsuka', loft(secs), [core], parent=root)
        obj('kat_fuchi', loft([oval(0, 0, Z_HANDLE_F - 0.001, HA + 0.01, HB + 0.01, 28, 2.4),
                               oval(0, 0, Z_HANDLE_F + 0.075, HA + 0.008, HB + 0.008, 28, 2.4)]),
            [fit], bevel=0.01, parent=root)
        obj('kat_pommel', loft([oval(0, 0, Z_HANDLE_B - 0.07, HA + 0.008, HB + 0.008, 28, 2.4),
                                oval(0, 0, Z_HANDLE_B, HA + 0.01, HB + 0.01, 28, 2.4),
                                oval(0, 0, Z_HANDLE_B + 0.04, HA - 0.012, HB - 0.014, 28, 2.4)]),
            [fit], bevel=0.014, segs=3, parent=root)
        # the wrap (ito): two flat bands wound opposite ways, crossing on the left and right faces (the diamonds)
        z0, z1 = Z_HANDLE_F + 0.085, Z_HANDLE_B - 0.08
        turns = 5.0
        for nm, hand in (('kat_wrap_a', 1), ('kat_wrap_b', -1)):
            st = []
            n = 180
            for i in range(n + 1):
                t = i / n
                z = z0 + (z1 - z0) * t
                th = hand * 2 * math.pi * turns * t
                w = handle_w(z)
                a, b = HA * w, HB * w
                c, s = math.cos(th), math.sin(th)
                p = Vector((a * c, b * s, z))
                nrm = Vector((c / a, s / b, 0)).normalized()
                tan = Vector((-a * s * hand * 2 * math.pi * turns, b * c * hand * 2 * math.pi * turns, z1 - z0)).normalized()
                side = nrm.cross(tan).normalized()
                hw, th_ = (0.03, 0.012) if tc else (0.036, 0.012)
                ring = []
                for dx, dn in ((-hw, 0.0), (hw, 0.0), (hw * 0.85, th_), (-hw * 0.85, th_)):
                    q = p + side * dx + nrm * (dn + 0.001)
                    ring.append((q.x, q.y, q.z))
                st.append(ring)
            obj(nm, loft(st), [wrapc], parent=root)
        if tc:
            # the beaded gold bands at the collar's back and the cap's front
            bm = bmesh.new()
            beads(bm, Z_HANDLE_F + 0.072, HA + 0.011, HB + 0.011, 0.009, 16)
            beads(bm, Z_HANDLE_B - 0.068, HA + 0.011, HB + 0.011, 0.009, 16)
            obj('kat_beads', bm, ['goldd'], parent=root)
            # the hilt ornament (menuki): a cluster of three blossoms on each side, standing clear of the wrap
            bm = bmesh.new()
            zc = -0.06
            xs = HA * handle_w(zc) + 0.014
            for sd in (-1, 1):
                cluster(bm, ('x', sd, xs), zc, 0.0, 0.05, 0.0, 0.014)
            obj('kat_menuki', bm, ['pale', 'heart'], bevel=0.003, segs=1, parent=root)

    # -------------------------------------------------------------------------------------------- the sheath (saya)
    def saya_sec(s, grow=0.0, n=32):
        """the sheath's section s studs down from the mouth (its frame: the mouth face at z 0, running down -z; when
           sheathed this frame is the katana's moved by -GuardFace, so its centre follows the blade's curve)"""
        u = s / SAYA_L
        h = SH0 + (SH1 - SH0) * u + grow
        w = SW0 + (SW1 - SW0) * u + grow
        ub = min(max(s / BLADE_L, 0), 1)
        cy = blade_c(ub) + 0.012
        return oval(0, cy, -s, w / 2, h / 2, n, 2.7)

    def sheath(root):
        tc = STYLE[0] == 'tidecrest'
        body_c, fit_c, cord_c = ('lac', 'gold', 'red') if tc else ('lacquer', 'horn', 'cord')
        body = [saya_sec(s) for s in [0.07 + (SAYA_L - 0.17) * k / 30 for k in range(31)]]
        obj('saya_body', loft(body), [body_c], parent=root)
        obj('saya_mouth', loft([saya_sec(0.0, 0.018), saya_sec(0.085, 0.018)]), [fit_c], bevel=0.012, parent=root)
        slot = [[(x, y + blade_c(0) + 0.006, z) for (x, y) in ((0, -H0 / 2 - 0.006), (T0 * 0.62, -0.01), (T0 * 0.52, H0 / 2 + 0.006),
                                                               (-T0 * 0.52, H0 / 2 + 0.006), (-T0 * 0.62, -0.01))]
                for z in (0.003, -0.006)]
        obj('saya_slot', loft(slot), ['slot'], smooth=False, parent=root)
        obj('saya_cap', loft([saya_sec(SAYA_L - 0.13, 0.014), saya_sec(SAYA_L - 0.03, 0.01), saya_sec(SAYA_L, -0.045)]),
            [fit_c], bevel=0.014, segs=2, parent=root)
        # the side knob (kurikata) on the outer face (-x: away from the body when worn at the left hip) and its cord loop
        c = saya_sec(KNOB_S)
        ky = sum(p[1] for p in c) / len(c)
        kx = -(SW0 + (SW1 - SW0) * KNOB_S / SAYA_L) / 2
        knob = [[(kx - d, ky + p[1], -KNOB_S + p[0]) for p in oval(0, 0, 0, 0.034, 0.042, 20, 2.6)] for d in (-0.01, 0.045)]
        obj('saya_knob', loft(knob), [fit_c], bevel=0.01, parent=root)
        ring = []
        cx, cyy, cz, ry, rz = kx - 0.03, ky + 0.12, -KNOB_S, 0.12, 0.075
        pts = [Vector((cx, cyy + ry * math.cos(2 * math.pi * i / 36), cz + rz * math.sin(2 * math.pi * i / 36))) for i in range(36)]
        for i in range(36):
            p = pts[i]
            tan = (pts[(i + 1) % 36] - pts[i - 1]).normalized()
            n1 = Vector((1, 0, 0)); n2 = tan.cross(n1).normalized()
            r = 0.016
            ring.append([tuple(p + n1 * r * math.cos(a) + n2 * r * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(10)]])
        ring.append(ring[0])
        obj('saya_cord', loft(ring, cap0=False, cap1=False), [cord_c], parent=root)
        if tc:
            # two gold bands, and a blossom cluster on the outer face between them
            bm = bmesh.new()
            for s0 in (0.36 * SAYA_L, 0.67 * SAYA_L):
                loft([saya_sec(s0, 0.012), saya_sec(s0 + 0.05, 0.012)], bm=bm)
            obj('saya_bands', bm, ['gold'], bevel=0.006, parent=root)
            s = 0.515 * SAYA_L
            cc = saya_sec(s)
            cy_ = sum(p[1] for p in cc) / len(cc)
            xs = (SW0 + (SW1 - SW0) * s / SAYA_L) / 2
            bm = bmesh.new()
            for sd in (-1, 1):
                cluster(bm, ('x', sd, xs - 0.004), -s, cy_, 0.06, 0.0, 0.016)
            obj('saya_blossoms', bm, ['pale', 'heart'], bevel=0.003, segs=1, parent=root)

    # -------------------------------------------------------------------------------------------- the pair
    def marker(name, pos_r, parent):
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = 'ARROWS'; e.empty_display_size = 0.15
        bpy.context.scene.collection.objects.link(e)
        e.parent = parent
        e.location = R2B(pos_r)
        return e

    def uv_all(objs):
        objs = [o for o in objs if o.type == 'MESH']
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs: o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.01)
        bpy.ops.object.mode_set(mode='OBJECT')

    def build_pair():
        k = bpy.data.objects.new('Katana', None); bpy.context.scene.collection.objects.link(k)
        katana(k)
        for n_, p in MARKS_K.items(): marker(n_, p, k)
        s = bpy.data.objects.new('Sheath', None); bpy.context.scene.collection.objects.link(s)
        sheath(s)
        for n_, p in MARKS_S.items(): marker(n_, p, s)
        uv_all(k.children); uv_all(s.children)
        return k, s

    def place_r(o, m4_roblox): o.matrix_world = RB @ m4_roblox @ RB

    def T(x, y, z): return Matrix.Translation(Vector((x, y, z)))

    def sheathed(k, s):
        """the katana home in the sheath: its GuardFace on the SheathMouth"""
        place_r(k, Matrix.Identity(4))
        place_r(s, T(0, 0, Z_FACE))

    def drawn(k, s):
        place_r(k, Matrix.Identity(4))
        place_r(s, T(-0.5, -0.6, Z_FACE))

    # -------------------------------------------------------------------------------------------- the R15 rig
    SIZE = {'HumanoidRootPart': (2, 2, 1), 'LowerTorso': (2, 0.4, 1), 'UpperTorso': (2, 1.6, 1), 'Head': (1.2, 1.2, 1.2),
            'RightUpperArm': (1, 1.1687, 1), 'RightLowerArm': (1, 1.0519, 1), 'RightHand': (1, 0.3, 1),
            'LeftUpperArm': (1, 1.1687, 1), 'LeftLowerArm': (1, 1.0519, 1), 'LeftHand': (1, 0.3, 1),
            'RightUpperLeg': (1, 1.2166, 1), 'RightLowerLeg': (1, 1.1931, 1), 'RightFoot': (1, 0.3, 1),
            'LeftUpperLeg': (1, 1.2166, 1), 'LeftLowerLeg': (1, 1.1931, 1), 'LeftFoot': (1, 0.3, 1)}
    JOINTS = [('Root', 'HumanoidRootPart', 'LowerTorso', (0, -1, 0), (0, -0.2, 0)),
              ('Waist', 'LowerTorso', 'UpperTorso', (0, 0.2, 0), (0, -0.8, 0)),
              ('Neck', 'UpperTorso', 'Head', (0, 0.8, 0), (0, -0.586, 0)),
              ('RightShoulder', 'UpperTorso', 'RightUpperArm', (1, 0.563, 0), (-0.5, 0.3943, 0)),
              ('RightElbow', 'RightUpperArm', 'RightLowerArm', (0, -0.3342, 0), (0, 0.2586, 0)),
              ('RightWrist', 'RightLowerArm', 'RightHand', (0, -0.5009, 0), (0, 0.125, 0)),
              ('LeftShoulder', 'UpperTorso', 'LeftUpperArm', (-1, 0.563, 0), (0.5, 0.3943, 0)),
              ('LeftElbow', 'LeftUpperArm', 'LeftLowerArm', (0, -0.3341, 0), (0, 0.2587, 0)),
              ('LeftWrist', 'LeftLowerArm', 'LeftHand', (0, -0.5009, 0), (0, 0.125, 0)),
              ('RightHip', 'LowerTorso', 'RightUpperLeg', (0.5, -0.2, 0), (0, 0.4208, 0)),
              ('RightKnee', 'RightUpperLeg', 'RightLowerLeg', (0, -0.4009, 0), (0, 0.3792, 0)),
              ('RightAnkle', 'RightLowerLeg', 'RightFoot', (0, -0.5472, 0), (0, 0.1019, 0)),
              ('LeftHip', 'LowerTorso', 'LeftUpperLeg', (-0.5, -0.2, 0), (0, 0.4208, 0)),
              ('LeftKnee', 'LeftUpperLeg', 'LeftLowerLeg', (0, -0.4011, 0), (0, 0.379, 0)),
              ('LeftAnkle', 'LeftLowerLeg', 'LeftFoot', (0, -0.5472, 0), (0, 0.1019, 0))]

    def look_frame(pos, fwd, up_hint):
        """a Roblox CFrame (4x4) at pos whose -Z is fwd and whose +Y leans toward up_hint"""
        z = -fwd.normalized()
        y = (up_hint - z * up_hint.dot(z)).normalized()
        x = y.cross(z)
        m = Matrix.Identity(4)
        for i in range(3):
            m[i][0], m[i][1], m[i][2], m[i][3] = x[i], y[i], z[i], pos[i]
        return m

    def hip_c0():
        """the sheath's frame in the LowerTorso's space: mouth at HIP_MOUTH, running toward HIP_TIP, worn edge up
           (the katana is worn edge up: the sheath's back, its +Y, faces down)"""
        return look_frame(V(HIP_MOUTH), V(HIP_TIP) - V(HIP_MOUTH), Vector((0, -1, 0)))

    def centres():
        c = {'HumanoidRootPart': Vector((0, 3.0, 0))}   # (feet on the ground at y 0)
        for name, p0, p1, a0, a1 in JOINTS:
            c[p1] = c[p0] + V(a0) - V(a1)
        return c

    def bind(o, ao, bone):
        mw = o.matrix_world.copy()
        o.parent = ao; o.parent_type = 'BONE'; o.parent_bone = bone
        bpy.context.view_layer.update()
        o.matrix_world = mw

    def rig():
        C = centres()
        arm = bpy.data.armatures.new('R15'); ao = bpy.data.objects.new('R15', arm)
        bpy.context.scene.collection.objects.link(ao)
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = ao; ao.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bones = {}
        b = arm.edit_bones.new('HumanoidRootPart'); b.head = R2B(C['HumanoidRootPart']); b.tail = b.head + Vector((0, 0, 0.6))
        bones['HumanoidRootPart'] = b
        for name, p0, p1, a0, a1 in JOINTS:     # each bone's head at its joint (the Motor6D's pivot)
            j = C[p0] + V(a0)
            b = arm.edit_bones.new(p1); b.head = R2B(j)
            down = p1.endswith(('Arm', 'Hand', 'Leg', 'Foot'))
            b.tail = R2B(j + Vector((0, -0.45 if down else 0.45, 0)))
            b.parent = bones[p0]; bones[p1] = b
        g = C['RightHand'] + V(GRIP_IN_HAND)
        kb = arm.edit_bones.new('Katana'); kb.head = R2B(g); kb.tail = R2B(g + Vector((0, 0, -0.6))); kb.parent = bones['RightHand']
        hc = hip_c0()
        m = C['LowerTorso'] + Vector((hc[0][3], hc[1][3], hc[2][3]))
        d = -Vector((hc[0][2], hc[1][2], hc[2][2]))
        sb = arm.edit_bones.new('Sheath'); sb.head = R2B(m); sb.tail = R2B(m + d * 0.6); sb.parent = bones['LowerTorso']
        # THE STRETCH (the Tidecrest gag: the blade grows to ~10x): a bone at the GuardFace pointing down the blade; the
        # blade rides on it, so scaling it along its own length (pose scale Y) stretches the blade alone, its width and
        # thickness unchanged; BladeTip rides on it too
        gf = g + Vector((0, 0, Z_FACE))
        bs = arm.edit_bones.new('BladeStretch'); bs.head = R2B(gf); bs.tail = R2B(gf + Vector((0, 0, -0.6))); bs.parent = kb
        bs.roll = 0.0
        bpy.ops.object.mode_set(mode='OBJECT')
        for name, sz in SIZE.items():
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            for v in bm.verts: v.co = R2B((v.co.x * sz[0], v.co.y * sz[1], v.co.z * sz[2])) + R2B(C[name])
            o = obj(name, bm, ['body'] if name != 'HumanoidRootPart' else ['slot'], smooth=False, bevel=0.035)
            if name == 'HumanoidRootPart': o.hide_render = True; o.display_type = 'WIRE'
            bind(o, ao, name)
        return ao, C

    # -------------------------------------------------------------------------------------------- export
    def select_tree(roots):
        bpy.ops.object.select_all(action='DESELECT')
        for r in roots:
            r.select_set(True)
            for c in r.children_recursive: c.select_set(True)

    def export(path, roots):
        select_tree(roots)
        bpy.context.view_layer.update()
        if path.endswith('.glb'):
            bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
        else:
            bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
                                     use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False, axis_forward='-Z',
                                     axis_up='Y', object_types={'ARMATURE', 'MESH', 'EMPTY'}, primary_bone_axis='Y',
                                     secondary_bone_axis='X', mesh_smooth_type='FACE')

    def clear():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        MATS.clear()
        bpy.context.scene.unit_settings.system = 'NONE'

    def tris(objs):
        dg = bpy.context.evaluated_depsgraph_get(); n = 0
        for o in objs:
            if o.type != 'MESH': continue
            me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); n += len(me.loop_triangles)
            o.evaluated_get(dg).to_mesh_clear()
        return n

    def roblox_glb(path):
        """the sheathed pair for the Studio upload: modifiers applied, every multi-colour piece split into one piece per
           colour (an upload keeps no colours; Studio paints each piece from its name '<part>__<colour>')"""
        clear(); k, s = build_pair(); sheathed(k, s)
        bpy.context.view_layer.update()
        meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
        for o in meshes:
            mw = o.matrix_world.copy()
            o.parent = None; o.matrix_world = mw
            bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
            for md in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=md.name)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            base = o.name
            if len(o.data.materials) > 1:
                bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
                parts = [p for p in bpy.context.selected_objects]
            else:
                parts = [o]
            for p in parts:
                used = {p.data.materials[f.material_index].name for f in p.data.polygons}
                mname = used.pop() if used else p.data.materials[0].name
                p.name = '%s__%s' % (base, mname); p.data.name = p.name
        for o in [o for o in bpy.context.scene.objects if o.type == 'EMPTY']: bpy.data.objects.remove(o)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_apply=True, export_yup=True)
        return sorted(o.name for o in bpy.context.scene.objects if o.type == 'MESH')

    # -------------------------------------------------------------------------------------------- renders
    VIEWS_PAIR = [('side', (1, 0, 0), (0, 1, 0)), ('top', (0, 1, 0), (-1, 0, 0)), ('front', (0, 0, -1), (0, 1, 0)),
                  ('threequarter', (1, 0.75, -1.1), (0, 1, 0))]
    VIEWS_RIG = [('front', (0, 0, -1), (0, 1, 0)), ('side', (-1, 0, 0), (0, 1, 0)), ('top', (0, 1, 0), (0, 0, -1)),
                 ('threequarter', (-1.1, 0.55, -1.0), (0, 1, 0))]
    RES = (1500, 900)

    def stage():
        sc = bpy.context.scene
        eng = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
        sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in eng else 'BLENDER_EEVEE'
        sc.view_settings.view_transform = 'Standard'
        sc.render.resolution_x, sc.render.resolution_y = RES
        w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
        bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (*lin('5d6168'), 1); bg.inputs[1].default_value = 1.0
        for name, rot, e in (('key', (math.radians(48), 0, math.radians(-35)), 3.2), ('fill', (math.radians(62), 0, math.radians(140)), 1.4),
                             ('under', (math.radians(160), 0, math.radians(20)), 0.6)):
            ld = bpy.data.lights.new(name, 'SUN'); ld.energy = e; ld.angle = 0.25
            lo = bpy.data.objects.new(name, ld); lo.rotation_euler = rot; sc.collection.objects.link(lo)
        cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'; cam.clip_end = 500
        co = bpy.data.objects.new('c', cam); sc.collection.objects.link(co); sc.camera = co
        return co

    def render_views(prefix, views, marks, out):
        """ortho views fitted to what renders; marks: {name: object} whose picture positions are written out"""
        from bpy_extras.object_utils import world_to_camera_view
        sc = bpy.context.scene
        co = sc.camera
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        pts = []
        for o in sc.objects:
            if o.type != 'MESH' or o.hide_render: continue
            ev = o.evaluated_get(dg); me = ev.to_mesh()
            mw = o.matrix_world
            pts += [mw @ v.co for v in me.vertices]
            ev.to_mesh_clear()
        res = {}
        for vn, d, up in views:
            fwd = -R2B(V(d).normalized())        # the camera looks this way (Blender)
            u = R2B(V(up)); u = (u - fwd * u.dot(fwd)).normalized()
            r = fwd.cross(u)
            xs = [p.dot(r) for p in pts]; ys = [p.dot(u) for p in pts]; zs = [p.dot(fwd) for p in pts]
            w_, h_ = max(xs) - min(xs), max(ys) - min(ys)
            cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
            scale = max(w_, h_ * RES[0] / RES[1]) * 1.12
            centre = r * cx + u * cy + fwd * ((max(zs) + min(zs)) / 2)
            m = Matrix.Identity(4)
            for i in range(3): m[i][0], m[i][1], m[i][2] = r[i], u[i], -fwd[i]
            m.translation = centre - fwd * 60
            co.matrix_world = m
            co.data.ortho_scale = scale
            bpy.context.view_layer.update()
            p = os.path.join(out, 'renders', '%s_%s.png' % (prefix, vn))
            sc.render.filepath = p
            bpy.ops.render.render(write_still=True)
            res[vn] = {'px_per_stud': RES[0] / scale,
                       'marks': {n_: [round(c, 4) for c in world_to_camera_view(sc, co, mo.matrix_world.translation)[:2]]
                                 for n_, mo in marks.items()}}
        return res

    def stretch_about_face(o, f):
        """scale an object of the katana along the blade (Blender -Y in the katana's own frame) about the GuardFace"""
        gf = R2B((0, 0, Z_FACE))
        M = Matrix.Translation(gf) @ Matrix.Diagonal((1, f, 1, 1)) @ Matrix.Translation(-gf)
        o.matrix_world = M @ o.matrix_world

    def superlong(style, sub, out, marks, f=10.0):
        """the ready-made super-long katana (blade x f, handle as is), and the gag renders"""
        clear(); k, s = build_pair()
        bpy.data.objects.remove(s, do_unlink=True)
        for o in list(bpy.data.objects):
            if o.name.startswith('saya_') or o.name in MARKS_S: bpy.data.objects.remove(o, do_unlink=True)
        bpy.context.view_layer.update()
        stretch_about_face(bpy.data.objects['kat_blade'], f)
        tip = bpy.data.objects['BladeTip']
        tip.location = R2B((0, TIP[1], Z_FACE + (TIP[2] - Z_FACE) * f))
        export(os.path.join(sub, 'katana_superlong_x10.glb'), [k]); export(os.path.join(sub, 'katana_superlong_x10.fbx'), [k])
        # the draw, mid-stretch: the guard 5 studs out of the mouth, the blade already longer than the sheath, its tip
        # still inside (the sheath hides the rest: the gag)
        clear(); k, s = build_pair()
        D = 5.0
        fs = (D + SAYA_L - 0.6) / BLADE_L
        place_r(s, T(0, 0, Z_FACE)); place_r(k, T(0, 0, D))
        bpy.context.view_layer.update()
        blade = bpy.data.objects['kat_blade']
        gf = k.matrix_world @ R2B((0, 0, Z_FACE))
        M = Matrix.Translation(gf) @ Matrix.Diagonal((1, fs, 1, 1)) @ Matrix.Translation(-gf)
        blade.matrix_world = M @ blade.matrix_world
        stage()
        mk = {n_: bpy.data.objects[n_] for n_ in ('Grip', 'GuardFace', 'SheathMouth')}
        marks[style]['middraw'] = render_views('%s_middraw' % style, [VIEWS_PAIR[0], VIEWS_PAIR[3]], mk, out)
        return fs

    def build_style(style, out, marks, info):
        STYLE[0] = style
        sub = os.path.join(out, style)
        os.makedirs(os.path.join(sub, 'roblox'), exist_ok=True)
        # 1. each on its own, at its own origin
        clear(); k, s = build_pair(); place_r(s, T(-0.6, 0, 0))
        bpy.context.view_layer.update()
        info[style] = {'katana_tris': tris(k.children_recursive), 'sheath_tris': tris(s.children_recursive),
                       'katana_parts': sorted(o.name for o in k.children if o.type == 'MESH'),
                       'sheath_parts': sorted(o.name for o in s.children if o.type == 'MESH')}
        export(os.path.join(sub, 'katana.glb'), [k]); export(os.path.join(sub, 'katana.fbx'), [k])
        place_r(s, Matrix.Identity(4))
        export(os.path.join(sub, 'sheath.glb'), [s]); export(os.path.join(sub, 'sheath.fbx'), [s])
        # 2. together: drawn (side by side) and sheathed
        marks[style] = {}
        for pose, put in (('drawn', drawn), ('sheathed', sheathed)):
            clear(); k, s = build_pair(); put(k, s)
            export(os.path.join(sub, 'katana_sheath_%s.glb' % pose), [k, s])
            export(os.path.join(sub, 'katana_sheath_%s.fbx' % pose), [k, s])
            stage()
            mk = {n_: bpy.data.objects[n_] for n_ in list(MARKS_K) + list(MARKS_S)}
            marks[style][pose] = render_views('%s_%s' % (style, pose), VIEWS_PAIR, mk, out)
        # 3. the rig: the katana in the right hand, the sheath at the left hip
        clear(); ao, C = rig(); k, s = build_pair()
        place_r(k, T(*(C['RightHand'] + V(GRIP_IN_HAND))))
        place_r(s, T(*C['LowerTorso']) @ hip_c0())
        bind(k, ao, 'Katana'); bind(s, ao, 'Sheath')
        bind(bpy.data.objects['kat_blade'], ao, 'BladeStretch'); bind(bpy.data.objects['BladeTip'], ao, 'BladeStretch')
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(sub, 'r15_katana_rig.blend'))
        export(os.path.join(sub, 'r15_katana_rig.fbx'), [ao])
        stage()
        mk = {n_: bpy.data.objects[n_] for n_ in list(MARKS_K) + list(MARKS_S)}
        marks[style]['rig'] = render_views('%s_rig' % style, VIEWS_RIG, mk, out)
        # the rig holding the blade stretched x10 (the BladeStretch bone scaled along its length), side on
        ao.pose.bones['BladeStretch'].scale = (1.0, 10.0, 1.0)
        bpy.context.view_layer.update()
        marks[style]['rig10'] = render_views('%s_rig10' % style, [VIEWS_RIG[1]], mk, out)
        ao.pose.bones['BladeStretch'].scale = (1.0, 1.0, 1.0)
        info[style]['middraw_scale'] = superlong(style, sub, out, marks)
        # 4. the Studio upload file
        info[style]['roblox_pieces'] = roblox_glb(os.path.join(sub, 'roblox', 'katana_sheath_roblox.glb'))
        return C

    def main():
        out = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else os.path.join(os.getcwd(), 'katana_out')
        only = [a for a in sys.argv[sys.argv.index('--') + 2:] if a in STYLES] if '--' in sys.argv else []
        os.makedirs(os.path.join(out, 'renders'), exist_ok=True)
        marks, info = {}, {}
        for style in (only or STYLES):
            C = build_style(style, out, marks, info)
        with open(os.path.join(out, 'renders', 'marks.json'), 'w') as fh: json.dump(marks, fh, indent=1)
        hc = hip_c0()
        data = {
            'units': '1 unit = 1 stud. Roblox axes: x right, y up, -z forward. FBX/glTF: Y up, the rig faces +Z.',
            'katana': {'root': 'Katana (origin = Grip)', 'markers': MARKS_K, 'length_studs': round(Z_HANDLE_B + 0.04 - Z_TIP, 3),
                       'blade_studs': BLADE_L, 'length_factor': LENGTH},
            'sheath': {'root': 'Sheath (origin = SheathMouth)', 'markers': MARKS_S, 'length_studs': SAYA_L,
                       'sheathed': 'Sheath CFrame = Katana CFrame * CFrame.new(0, 0, %.3f)' % Z_FACE},
            'joints': {'Katana': {'Part0': 'RightHand', 'C0': list(GRIP_IN_HAND), 'C1': 'identity'},
                       'Sheath': {'Part0': 'LowerTorso', 'C0_matrix_rows': [[round(hc[i][j], 5) for j in range(4)] for i in range(3)],
                                  'C1': 'identity'}},
            'r15_part_centres': {n_: [round(x, 4) for x in v] for n_, v in C.items()},
            'styles': info,
        }
        with open(os.path.join(out, 'markers.json'), 'w') as fh: json.dump(data, fh, indent=1)
        print('INFO', json.dumps({s: {k: v for k, v in d.items() if k.endswith('tris')} for s, d in info.items()}))
        print('DONE', out)


# ---------------------------------------------------------------------------------------------------- the sheets
def sheets(out):
    from PIL import Image, ImageDraw, ImageFont
    rd = os.path.join(out, 'renders')
    marks = json.load(open(os.path.join(rd, 'marks.json')))
    try:
        F = ImageFont.truetype('arialbd.ttf', 30); f = ImageFont.truetype('arial.ttf', 22); fs = ImageFont.truetype('arial.ttf', 18)
    except Exception:
        F = f = fs = ImageFont.load_default()
    TW, TH = 900, 540
    names = {'side': 'SIDE', 'top': 'TOP', 'front': 'FRONT (tip end)', 'threequarter': 'THREE-QUARTER'}
    rig_names = {'front': 'FRONT', 'side': 'LEFT SIDE', 'top': 'TOP', 'threequarter': 'THREE-QUARTER'}
    MC = {'Grip': (255, 196, 0), 'GuardFace': (0, 200, 255), 'BladeTip': (255, 80, 80), 'SheathMouth': (120, 255, 120),
          'SheathHip': (230, 120, 255)}

    def tile(path, label, m, show_marks):
        im = Image.open(path).convert('RGB')
        sx = TW / im.width
        im = im.resize((TW, TH), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        d.text((18, 12), label, font=F, fill=(240, 240, 240))
        px = m['px_per_stud'] * sx     # a one-stud scale bar
        d.rectangle((18, TH - 30, 18 + px, TH - 22), fill=(240, 240, 240))
        d.text((26 + px, TH - 40), '1 stud', font=fs, fill=(240, 240, 240))
        if show_marks:
            for n_, (u, v) in m['marks'].items():
                x, y = u * TW, (1 - v) * TH
                if not (0 <= x <= TW and 0 <= y <= TH): continue
                c = MC.get(n_, (255, 255, 255))
                d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(0, 0, 0))
                d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=c)
        return im

    def legend(d, y):
        x = 24
        for n_, c in MC.items():
            d.ellipse((x, y + 4, x + 16, y + 20), fill=c, outline=(0, 0, 0), width=2)
            d.text((x + 24, y), n_, font=f, fill=(235, 235, 235)); x += 44 + int(d.textlength(n_, font=f)) + 20

    styles = [s for s in STYLES if s in marks]
    order = ['side', 'top', 'front', 'threequarter']
    rows = [(s, p) for p in ('sheathed', 'drawn') for s in styles]
    W = Image.new('RGB', (TW * 4, 80 + TH * len(rows) + 70), (38, 40, 45))
    d = ImageDraw.Draw(W)
    d.text((24, 22), 'KATANA + SHEATH: BLANK vs TIDECREST    1 unit = 1 stud    dots = markers', font=F, fill=(245, 245, 245))
    for r, (st, pose) in enumerate(rows):
        for c, vn in enumerate(order):
            W.paste(tile(os.path.join(rd, '%s_%s_%s.png' % (st, pose, vn)), '%s %s - %s' % (st.upper(), pose.upper(), names[vn]),
                         marks[st][pose][vn], vn != 'threequarter'), (c * TW, 80 + r * TH))
    legend(d, 80 + TH * len(rows) + 22)
    W.save(os.path.join(out, 'katana_render_sheet.png'))
    W.convert('RGB').resize((W.width // 2, W.height // 2), Image.LANCZOS).save(os.path.join(out, 'katana_render_sheet_small.jpg'), quality=88)
    W = Image.new('RGB', (TW * 4, 80 + TH * len(styles) + 70), (38, 40, 45))
    d = ImageDraw.Draw(W)
    d.text((24, 22), 'BLANK R15 RIG    katana on RightHand (Grip)    sheath on LowerTorso (left hip)', font=F, fill=(245, 245, 245))
    for r, st in enumerate(styles):
        for c, vn in enumerate(['front', 'side', 'top', 'threequarter']):
            W.paste(tile(os.path.join(rd, '%s_rig_%s.png' % (st, vn)), '%s - %s' % (st.upper(), rig_names[vn]), marks[st]['rig'][vn],
                         vn != 'threequarter'), (c * TW, 80 + r * TH))
    legend(d, 80 + TH * len(styles) + 22)
    W.save(os.path.join(out, 'rig_render_sheet.png'))
    # the stretch gag: the rig holding the blade at x10, and the draw mid-stretch (longer than the sheath already)
    if all('rig10' in marks[st] for st in styles):
        W = Image.new('RGB', (TW * 3, 80 + TH * len(styles) + 20), (38, 40, 45))
        d = ImageDraw.Draw(W)
        d.text((24, 22), 'THE STRETCH: BladeStretch bone scaled x10 on the rig;  the draw mid-stretch (guard 5 studs out, tip still inside)',
               font=F, fill=(245, 245, 245))
        for r, st in enumerate(styles):
            for c, (img, lab, m) in enumerate(((('%s_rig10_side.png' % st), 'RIG, BLADE x10 - LEFT SIDE', marks[st]['rig10']['side']),
                                               (('%s_middraw_side.png' % st), 'MID-DRAW - SIDE', marks[st]['middraw']['side']),
                                               (('%s_middraw_threequarter.png' % st), 'MID-DRAW - THREE-QUARTER', marks[st]['middraw']['threequarter']))):
                W.paste(tile(os.path.join(rd, img), '%s  %s' % (st.upper(), lab), m, False), (c * TW, 80 + r * TH))
        W.save(os.path.join(out, 'katana_stretch_sheet.png'))
        W.resize((W.width // 2, W.height // 2), Image.LANCZOS).save(os.path.join(out, 'katana_stretch_sheet_small.jpg'), quality=88)
    print('SHEETS', out)


if __name__ == '__main__':
    if bpy:
        main()
    elif len(sys.argv) > 2 and sys.argv[1] == 'sheet':
        sheets(sys.argv[2])
    else:
        print('usage: see the header of this file')
