# PALLET JACK, the machine Bev put in him, one part a year (docs/story/TRAIN.md §2). It is the Overdrive Rig
# (tools/blender/make_rig.py) with no suit round it: every piece is its own named part, so the game can move, light or
# break it.
#   boiler (a beer keg sunk in his lower back) · fire (its door slots + the level glass: emissive) · gauge + needle ·
#   valve (the bleed wheel) · stackL / stackR (they slide up out of their sleeves) + flapL / flapR (rain caps) ·
#   collar (the welded steel collarbone) · shinL / shinR (the pistons) + lockL / lockR (their toggle clamps) ·
#   the rocket forearm: cock (the cocking collar), ram (the chrome ram the fist rides out on), fist (bare knuckles)
# J.marks collects pivots, axes and marker spots (joint frame) for the parts file.
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jackbody import *  # noqa


def _v(p): return [round(float(x), 4) for x in p]


# ------------------------------------------------------------------------------------------------ the boiler
def keg_surf(dent=None):
    y0, y1, r, cz = KEG['y0'], KEG['y1'], KEG['r'], KEG['cz']
    prof = [(y0, 0.9), (y0 + 0.006, 1.03), (y0 + 0.022, 1.035), (y0 + 0.03, 0.985), (y0 + 0.044, 0.985), (y0 + 0.056, 1.0), (y0 + 0.1, 1.0), (y0 + 0.108, 1.05), (y0 + 0.12, 1.05), (y0 + 0.128, 1.0),
            (y0 + 0.182, 1.0), (y0 + 0.19, 1.05), (y0 + 0.202, 1.05), (y0 + 0.21, 1.0), (y1 - 0.056, 1.0), (y1 - 0.044, 0.985), (y1 - 0.03, 0.985), (y1 - 0.022, 1.035), (y1 - 0.006, 1.03), (y1, 0.9)]
    return Surf([(y, r * k, r * k, r * k, 0.0, cz, 2.0) for y, k in prof]), [y for y, _ in prof]


def boiler(J):
    M = J.M; ts = J.S['torso']
    y0, y1, r, cz = KEG['y0'], KEG['y1'], KEG['r'], KEG['cz']
    ks, rows = keg_surf(); J.S['keg'] = ks
    A0, A1 = PI - 2.2, PI + 2.2
    kg = []
    body = ks.mesh('keg', M['keg'], rows, seg=18, a0=A0, a1=A1, uv=(1, 0, 0, 1), deg=40)
    def kt(p, n):
        c = (1, 1, 1)
        c = mix3(c, (0.5, 0.48, 0.46), 0.75 * smooth01(p.y, y1 - 0.07, y1))                      # soot settling on the top chime
        c = mix3(c, (0.62, 0.5, 0.44), 0.5 * smooth01(y0 + 0.05 - p.y, 0, 0.05))                 # rust round the bottom
        c = mix3(c, (0.7, 0.62, 0.6), 0.45 * smooth01(abs(p.x), 0.085, 0.14))                    # grime where it goes into him
        return c
    tint(body, kt); kg.append(body)
    for yy, rr in ((y1 - 0.012, 0.86), (y0 + 0.012, 0.86)):
        d = cyl(r * rr, 0.004, (0, yy, cz), M['kegplain'], axis='y', seg=18, name='kegend'); tint(d, lambda p, n: 0.55); kg.append(d)
    # the fire door on the back: blued plate, a hinge, a latch, rivets. its three slots are the glow (tag fire)
    dz = cz + r + 0.002; dy = y0 + 0.068
    kg.append(cyl(0.054, 0.016, (0, dy, dz), M['blued'], axis='z', seg=14, bev=0.003, name='firedoor'))
    kg.append(cyl(0.008, 0.07, (-0.058, dy, dz), M['steel'], axis='y', seg=6, name='doorhinge'))
    kg.append(box((0.03, 0.014, 0.012), (0.056, dy, dz + 0.004), M['steel'], bev=0.003, name='doorlatch'))
    for i in range(8):
        t = TAU * i / 8 + 0.39; kg.append(rivet((math.cos(t) * 0.045, dy + math.sin(t) * 0.045, dz + 0.008), 0.0055, M['steel'], (0, 0, 1)))
    fire = [box((0.052 - abs(i) * 0.012, 0.0085, 0.004), (0, dy + i * 0.018, dz + 0.0095), M['glow'], name='fireslot') for i in (-1, 0, 1)]
    # a level glass up his right side of it: you can see what it runs on
    gp0 = ks.p(y0 + 0.09, PI - 1.15, 0.016); gp1 = ks.p(y0 + 0.2, PI - 1.15, 0.016)
    kg.append(rod(tuple(gp0), tuple(gp1), 0.011, M['glass'], seg=8, name='levelglass'))
    fire.append(rod(tuple(gp0 + Vector((0, 0.004, 0))), tuple(gp0.lerp(gp1, 0.62)), 0.0062, M['marrow'], seg=6, name='level'))
    for q in (gp0, gp1):
        kg.append(rod(tuple(q), tuple(ks.p(q.y, PI - 1.15, -0.004)), 0.007, M['brass'], seg=6, name='glassstub'))
        kg.append(ball(0.012, tuple(q), M['brass'], seg=6, rings=4, name='glassnut'))
    # a relief valve on the top of it, and the manifold: a copper elbow off each side of the keg, out and up to a stack
    kg.append(rod((0, y1 - 0.014, cz + 0.07), (0, y1 + 0.026, cz + 0.07), 0.016, M['brass'], seg=8, name='relief'))
    kg.append(cyl(0.022, 0.012, (0, y1 + 0.03, cz + 0.07), M['red'], axis='y', seg=8, name='reliefcap'))
    mf = []
    for sx in (-1, 1):
        B = STACK_B(sx)
        q = ks.p(y1 - 0.075, PI - sx * 1.2); nk = ks.n(y1 - 0.075, PI - sx * 1.2)
        mf.append(sweep([tuple(q - nk * 0.01), tuple(q + nk * 0.035), (B[0] - sx * 0.012, q.y + 0.012, B[2] - 0.012), (B[0], q.y + 0.045, B[2]), (B[0], B[1] + 0.006, B[2])], 0.024, M['copper'], seg=8, name='elbow'))
        mf.append(rod(tuple(q + nk * 0.004), tuple(q + nk * 0.02), 0.032, M['brass'], seg=8, name='union'))
    J.P.add('spine', mf, 'stackBase')
    # where it goes into him: the singlet cut away, raw skin, a welt of scar all the way round, six lugs bolted through
    sk = ts.mesh('kegskin', M['skin'], [y0 - 0.032, y0 + 0.05, y0 + 0.15, y0 + 0.25, y1 + 0.022], seg=10, a0=PI - 0.6, a1=PI + 0.6, off=0.0085)
    tint(sk, lambda p, n: mix3((1.0, 0.86, 0.84), (0.9, 0.56, 0.52), smooth01(0.24 - abs(p.x), 0, 0.1)))
    lip = ts.line('keglip', [(y0 - 0.012, PI - 0.24), (y0 + 0.02, PI - 0.44), (y0 + 0.15, PI - 0.47), (y1 - 0.03, PI - 0.44), (y1 + 0.008, PI - 0.24), (y1 + 0.012, PI), (y1 + 0.008, PI + 0.24), (y1 - 0.03, PI + 0.44),
                          (y0 + 0.15, PI + 0.47), (y0 + 0.02, PI + 0.44), (y0 - 0.012, PI + 0.24), (y0 - 0.014, PI), (y0 - 0.012, PI - 0.24)], 0.016, M['scar'], sink=0.3, seg=4, n=20, taper=False)
    base = [sk, lip]
    for sx in (-1, 1):
        for yy in (y0 + 0.05, y0 + 0.155, y0 + 0.26):
            a = PI + sx * 0.5
            base.append(ts.plate('lug', M['steel'], yy, a, 0.04, 0.045, off=0.012, n=3.0, spokes=8, sink=0.002))
            base.append(hexbolt(tuple(ts.p(yy, a, 0.012)), 0.0085, 0.008, M['blued'], tuple(ts.n(yy, a))))
    J.P.add('spine', base)
    J.P.add('spine', kg, 'boiler', note='the boiler: a beer keg sunk in his lower back (RETURN EMPTY), fire door, level glass, manifold')
    J.P.add('spine', fire, 'fire', note='what glows: the fire door slots (pj_glow) and the level glass (pj_marrow)')
    J.marks['boilerAt'] = ('spine', (0, (y0 + y1) / 2, cz + r))
    J.marks['fireAt'] = ('spine', (0, dy, dz + 0.012))
    gauge(J, ks); valve(J, ks)


def gauge(J, ks):
    """the pressure gauge on a stub off his left side of the keg, tipped up so whoever is behind him can read it"""
    M = J.M; y0 = KEG['y0']
    q = ks.p(y0 + 0.262, PI + 0.95); nk = ks.n(y0 + 0.262, PI + 0.95)
    d = (nk * 0.8 + Vector((0, 0.52, 0))).normalized()
    c = q + nk * 0.03 + Vector((0, 0.03, 0))
    stem = [rod(tuple(q - nk * 0.005), tuple(q + nk * 0.024), 0.01, M['brass'], seg=6, name='gstem'), rod(tuple(q + nk * 0.02), tuple(c + d * 0.02), 0.009, M['brass'], seg=6, name='gstem2'),
            ball(0.014, tuple(q + nk * 0.022), M['brass'], seg=6, rings=4, name='gnut')]
    case = [cyl(0.05, 0.03, (0, 0, 0.013), M['brass'], axis='z', seg=16, bev=0.003, name='gcase')]
    case.append(lathe([(0.041, -0.0035), (0.051, -0.0035), (0.051, 0.002), (0.041, 0.002)], (0, 0, 0), M['chrome'], seg=16, axis='z', name='gbezel', cap=False))
    face = cyl(0.042, 0.002, (0, 0, -0.001), M['dial'], axis='z', seg=16, name='gface'); face['keep_uv'] = 1
    bpy.context.view_layer.update(); flip_uv(face, (0, 0, 0), (0.084, 0.084))
    ndl = [box((0.0045, 0.036, 0.002), (0, 0.013, -0.0045), M['needle'], name='needle'), cyl(0.007, 0.004, (0, 0, -0.005), M['dark'], axis='z', seg=8, name='needlehub')]
    orient(case + [face] + ndl, tuple(c), tuple(d))
    J.P.add('spine', stem + case + [face], 'gauge', note='the pressure gauge (its face is pj_dial)')
    J.P.add('spine', ndl, 'needle', pivot=tuple(c), note='the gauge needle: turns about `axis` (0 = straight up the dial, + = clockwise as you read it)')
    J.marks['needle'] = ('spine', tuple(c), tuple(-d))
    J.marks['gaugeAt'] = ('spine', tuple(c))


def valve(J, ks):
    """the bleed valve on his right side of it: a brass gate valve, a red wheel, a spout that drips"""
    M = J.M; y0 = KEG['y0']
    q = ks.p(y0 + 0.14, PI - 0.8); nk = ks.n(y0 + 0.14, PI - 0.8)
    body = [rod(tuple(q - nk * 0.006), tuple(q + nk * 0.05), 0.014, M['brass'], seg=8, name='vstub'),
            box((0.034, 0.042, 0.034), tuple(q + nk * 0.05), M['brass'], bev=0.006, name='vbody'),
            rod(tuple(q + nk * 0.05), tuple(q + nk * 0.05 + Vector((0, -0.055, 0))), 0.011, M['brass'], seg=6, name='vspout'),
            rod(tuple(q + nk * 0.05 + Vector((0, 0.018, 0))), tuple(q + nk * 0.05 + Vector((0, 0.06, 0))), 0.007, M['steel'], seg=6, name='vstem'),
            blob('drip', tuple(q + nk * 0.05 + Vector((0, -0.066, 0))), (0.007, 0.012, 0.007), M['marrow'])]
    hc = q + nk * 0.05 + Vector((0, 0.062, 0))
    wh = [lathe([(0.032, -0.005), (0.04, -0.005), (0.04, 0.005), (0.032, 0.005)], (0, 0, 0), M['red'], seg=14, axis='y', name='vwheel', cap=False),
          cyl(0.011, 0.014, (0, 0, 0), M['red'], axis='y', seg=8, name='vhub')]
    for i in range(4): wh.append(box((0.07, 0.007, 0.01), (0, 0, 0), M['red'], rot=(0, PI / 4 * i, 0), name='vspoke'))
    for o in wh: o.location = gv(*hc)
    J.P.add('spine', body, 'valveBody', note='the bleed valve body and spout')
    J.P.add('spine', wh, 'valve', pivot=tuple(hc), note='the bleed wheel: turns about +y of the spine')
    J.marks['valve'] = ('spine', tuple(hc), (0, 1, 0))
    J.marks['bleedAt'] = ('spine', tuple(q + nk * 0.05 + Vector((0, -0.07, 0))))


# ------------------------------------------------------------------------------------------------ the stacks
def STACK_B(sx): return (sx * 0.232, KEG['y1'] + 0.012, 0.318)
def STACK_T(sx): return (sx * 0.29, 0.835, 0.378)
STACK_RISE = 0.07   # how far the game slides a stack up out of its sleeve when the rig comes up


def stacks(J, bent=False):
    M = J.M
    for sx, nm in ((-1, 'L'), (1, 'R')):
        B = Vector(STACK_B(sx)); T = Vector(STACK_T(sx)); u = (T - B).normalized(); Ln = (T - B).length
        f = gdir(tuple(u), src=(0, 1, 0))
        # the sleeve it slides in (fixed): wrapped so it doesn't burn the vest, two clamps
        st = [rod(tuple(B), tuple(B + u * 0.2), 0.043, M['wrap'], seg=12, name='sleeve' + nm), rod(tuple(B - u * 0.012), tuple(B + u * 0.012), 0.05, M['steel'], seg=12, name='sleevebase')]
        for t in (0.05, 0.185): st.append(rod(tuple(B + u * t), tuple(B + u * (t + 0.016)), 0.047, M['steel'], seg=12, name='clamp'))
        if sx > 0:  # a bar across the two, so they stand on their own
            Bo = Vector(STACK_B(-1)); uo = (Vector(STACK_T(-1)) - Bo).normalized()
            st.append(rod(tuple(Bo + uo * 0.03), tuple(B + u * 0.03), 0.011, M['steel'], seg=6, name='crossbar'))
            st.append(box((0.05, 0.026, 0.026), tuple((Bo + uo * 0.03 + B + u * 0.03) / 2), M['blued'], bev=0.004, name='turnbuckle'))
        J.P.add('spine', st, 'stackBase', note='the stacks\' sleeves, clamps and the bar across')
        if bent: continue
        # the stack itself: chrome going straw and blue, then black. a perforated shield, a rolled lip, the dark inside
        pipe = rod(tuple(B + u * 0.1), tuple(T), 0.034, M['chrome'], seg=12, r1=0.036, name='stack' + nm)
        def heat(p, n, B=B, u=u, Ln=Ln):
            t = (p - B).dot(u) / Ln
            c = (1, 1, 1)
            c = mix3(c, (0.95, 0.78, 0.5), 0.6 * gauss(t - 0.5, 0.14))
            c = mix3(c, (0.5, 0.52, 0.8), 0.6 * gauss(t - 0.7, 0.12))
            c = mix3(c, (0.2, 0.19, 0.19), smooth01(t, 0.86, 1.0))
            return c
        tint(pipe, heat)
        sp = [pipe, rod(tuple(B + u * (Ln * 0.5)), tuple(B + u * (Ln * 0.76)), 0.041, M['blued'], seg=12, name='shield' + nm)]
        for i in range(6):
            a = TAU * i / 6; side = f((math.cos(a) * 0.0418, 0, math.sin(a) * 0.0418))
            for t in (0.58, 0.68):
                o = box((0.011, 0.03, 0.004), (0, 0, 0), M['soot'], name='slot'); orient([o], tuple(B + u * (Ln * t) + side), tuple(side.normalized()), src=(0, 0, -1)); sp.append(o)
        sp.append(sweep([tuple(T + f((math.cos(TAU * i / 12) * 0.036, 0, math.sin(TAU * i / 12) * 0.036))) for i in range(13)], 0.0065, M['chrome'], seg=5, name='lip' + nm))
        ins = cyl(0.033, 0.003, (0, 0, 0), M['soot'], axis='y', seg=12, name='throat'); orient([ins], tuple(T - u * 0.012), tuple(u), src=(0, 1, 0)); sp.append(ins)
        gl = cyl(0.026, 0.003, (0, 0, 0), M['glow'], axis='y', seg=10, name='ember'); orient([gl], tuple(T - u * 0.006), tuple(u), src=(0, 1, 0)); sp.append(gl)
        J.P.add('spine', sp, 'stack' + nm, pivot=tuple(B + u * 0.1), note='a thruster stack: slides %.2f along `axis` when the rig comes up' % STACK_RISE)
        J.marks['stack' + nm] = ('spine', tuple(B + u * 0.1), tuple(u))
        # the rain cap: a disc on a hinge at the back of the lip, a counterweight behind it. shut at rest
        hg = T + f((0, 0.006, 0.04))
        fl = [cyl(0.041, 0.005, (0, 0.006, 0), M['steel'], axis='y', seg=12, name='flap' + nm), cyl(0.0065, 0.036, (0, 0.006, 0.04), M['blued'], axis='x', seg=6, name='flaphinge'),
              box((0.022, 0.008, 0.034), (0, 0.008, 0.058), M['steel'], bev=0.002, name='flapweight'), cyl(0.012, 0.012, (0, 0.01, 0.07), M['blued'], axis='x', seg=6, name='weight')]
        orient(fl, tuple(T), tuple(u), src=(0, 1, 0))
        tint(fl[0], lambda p, n: 0.5)
        J.P.add('spine', fl, 'flap' + nm, pivot=tuple(hg), note='its rain cap: hinged about `axis`, + opens it (about 1.2 rad is wide open)')
        J.marks['flap' + nm] = ('spine', tuple(hg), tuple(f((1, 0, 0))))
        J.marks['stackTip' + nm] = ('spine', tuple(T))


# ------------------------------------------------------------------------------------------------ the collarbone
COLLAR = [(0.476, -0.64), (0.47, -0.42), (0.461, -0.2), (0.457, 0.0), (0.461, 0.2), (0.47, 0.42), (0.476, 0.64)]
WELD_A = 0.13   # the weld sits a hand's width to his right of the middle: your hand goes on his chest LEFT of it


def collar(J):
    M = J.M; ts = J.S['torso']
    P_ = ts.path(COLLAR, off=0.01, n=11)
    bar = sweep(P_, 0.023, M['chrome'], seg=8, name='collarbar')
    tint(bar, lambda p, n: mix3((1, 1, 1), (0.62, 0.66, 0.95), 0.7 * gauss(p.x - 0.05, 0.05)))   # the heat of the weld, still in it
    cl = [bar]
    wp = ts.p(0.458, WELD_A, 0.01)
    for i in range(7):
        t = TAU * i / 7
        cl.append(blob('weld', (wp.x + 0.004 * math.sin(i * 2.1), wp.y + math.cos(t) * 0.024, wp.z + math.sin(t) * 0.024), (0.012, 0.0135, 0.0135), M['blued'], seg=6, rings=4))
    for a in (-0.36, -0.14, 0.4):
        q = ts.p(0.463, a, 0.032); cl.append(hexbolt(tuple(q), 0.0075, 0.006, M['blued'], tuple(ts.n(0.463, a))))
    J.P.add('spine', cl, 'collar', note='the welded steel collarbone (the weld is to his right of centre)')
    # where the bar goes under: a lip of scar each side, then it runs on under the skin to the shoulder's anchor
    base = []
    for sx in (-1, 1):
        q = ts.p(0.476, sx * 0.66, 0.006)
        base.append(blob('collarlip', tuple(q), (0.03, 0.032, 0.022), M['scar'], seg=10, rings=7))
        base.append(ts.line('collarridge', [(0.476, sx * 0.62), (0.482, sx * 0.85), (0.486, sx * 1.1), (0.482, sx * 1.3)], 0.019, M['skin'], sink=0.36, seg=6, n=6, taper=False))
    J.P.add('spine', base)
    J.marks['weldAt'] = ('spine', tuple(wp))
    hp = ts.p(0.4, -0.42, 0.007)
    J.marks['chest'] = ('spine', tuple(hp), tuple(ts.n(0.4, -0.42)))


# ------------------------------------------------------------------------------------------------ the shins
PISTON_Z = -0.064


def shins(J, blown=False):
    M = J.M
    for kn, sx, nm in (('kneeL', -1, 'L'), ('kneeR', 1, 'R')):
        z = PISTON_Z
        sh = [box((0.075, 0.034, 0.05), (0, -0.128, z + 0.008), M['steel'], bev=0.006, name='trunnion' + nm)]
        for s2 in (-1, 1): sh.append(hexbolt((s2 * 0.024, -0.128, z - 0.017), 0.0075, 0.007, M['blued'], (0, 0, -1)))
        sleeve = rod((0, -0.138, z), (0, -0.226, z), 0.033, M['red'], seg=12, name='sleeve' + nm)
        tint(sleeve, lambda p, n: mix3((1, 1, 1), (0.6, 0.56, 0.54), 0.5 * smooth01(-0.2 - p.y, 0, 0.03)))
        sh.append(sleeve)
        sh.append(cyl(0.038, 0.02, (0, -0.232, z), M['steel'], axis='y', seg=8, name='gland' + nm))
        rd = rod((0, -0.226, z), (0, -0.33, z), 0.019, M['chrome'], seg=10, name='rod' + nm); sh.append(rd)
        sh.append(box((0.05, 0.03, 0.03), (0, -0.326, z + 0.004), M['steel'], bev=0.005, name='clevis' + nm))
        sh.append(tube([(sx * 0.0, -0.15, z + 0.03), (sx * 0.02, -0.152, z + 0.05), (sx * 0.03, -0.175, 0.012), (sx * 0.028, -0.2, 0.03)], 0.0095, M['hose'], seg=6, name='hose' + nm))
        sh.append(ball(0.013, (0, -0.15, z + 0.032), M['brass'], seg=6, rings=4, name='port' + nm))
        # the clamp round the rod under the gland (fixed), and its toggle lever (the lock: it snaps flat when the rig comes up)
        sh.append(cyl(0.031, 0.02, (0, -0.256, z), M['blued'], axis='y', seg=10, name='clampring' + nm))
        sh.append(box((0.016, 0.024, 0.02), (sx * 0.036, -0.256, z), M['blued'], bev=0.003, name='clampear' + nm))
        J.P.add(kn, sh, 'shin' + nm, note='a shin piston: red sleeve, chrome rod, down the front of the leg to the boot\'s guard')
        piv = (sx * 0.042, -0.25, z)
        if not blown:
            lv = [box((0.014, 0.085, 0.012), (sx * 0.042, -0.25 - 0.036, z), M['steel'], bev=0.003, name='lever' + nm), cyl(0.008, 0.026, piv, M['chrome'], axis='z', seg=6, name='leverpin'),
                  ball(0.012, (sx * 0.042, -0.25 - 0.08, z), M['red'], seg=6, rings=4, name='leverknob')]
            for o in lv[:1] + lv[2:]:   # modelled open: swung out from the leg
                o.data.transform(o.matrix_basis.copy()); o.matrix_basis = Matrix.Identity(4)
                o.data.transform(Matrix.Translation(gv(*piv)) @ Matrix.Rotation(sx * 0.95, 4, gv(0, 0, 1)) @ Matrix.Translation(-gv(*piv)))
            J.P.add(kn, lv, 'lock' + nm, pivot=piv, note='the shin lock: a toggle lever, modelled open; turn it `shut` rad about z and it slaps up flat against the sleeve')
            J.marks['lock' + nm] = (kn, piv, (0, 0, 1)); J.vals['lock' + nm] = dict(shut=round(sx * (PI - 0.95), 4))


# ------------------------------------------------------------------------------------------------ the rocket forearm
COCK_Y = -0.236
COCK_PULL = 0.04     # how far back (up the arm) the collar comes when it cocks
PUNCH_REACH = 0.24   # how far the fist rides out on the ram
SLEEVE_END = -0.176  # where his skin stops and the steel starts


def forearm_right(J):
    M = J.M; fk, hk, sx = 'foreR', 'handR', 1
    E_ = SLEEVE_END
    F = Surf([(0.055, 0.092, 0.092, 0.102, 0, 0.004, 2.2), (-0.02, 0.119, 0.115, 0.121, 0, 0.0, 2.3), (-0.09, 0.122, 0.118, 0.122, 0, 0.0, 2.4), (E_ + 0.02, 0.118, 0.114, 0.118, 0, 0.0, 2.4), (E_, 0.114, 0.11, 0.114, 0, 0.0, 2.4)])
    J.S[fk] = F
    fo = F.mesh('fore' + fk, M['skin'], [0.055, 0.01, -0.03, -0.07, -0.11, -0.15, E_], seg=16, cap=(True, True))
    def scorch(p, n):
        c = mix3((1, 1, 1), (0.94, 0.8, 0.78), 0.5 * smooth01(p.y, -0.02, 0.05))
        c = mix3(c, (0.42, 0.34, 0.33), 0.8 * gauss(p.y + 0.02, 0.05) * smooth01(n.z, 0.2, 0.9))    # scorched behind the elbow
        c = mix3(c, (0.9, 0.62, 0.58), 0.7 * smooth01(E_ + 0.05 - p.y, 0, 0.05))                    # raw where it meets the steel
        return c
    tint(fo, scorch)
    fp = [fo]
    # the flange the skin stops at: riveted steel, a lip of scar round it
    fp.append(F.band('flange', M['steel'], E_ - 0.012, E_ + 0.016, off=0.007, seg=16, rows=2))
    for i in range(8):
        a = TAU * i / 8 + 0.2; fp.append(rivet(tuple(F.p(E_ + 0.002, a, 0.0075)), 0.0075, M['blued'], tuple(F.n(E_ + 0.002, a))))
    fp.append(F.line('flangelip', [(E_ + 0.027 + 0.004 * math.sin(i * 1.7), TAU * i / 12) for i in range(13)], 0.011, M['scar'], sink=0.3, seg=4, taper=False))
    fp.append(cyl(0.1, 0.008, (0, E_ - 0.006, 0), M['dark'], axis='y', seg=16, name='flangeface'))
    # the exhaust: a blued bell behind the elbow, pointing up and back clear of the arm; vents down each side
    d = Vector((0, 0.62, 0.78)).normalized(); o0 = Vector((0, -0.03, 0.103))
    bell = lathe([(0.02, 0.0), (0.026, 0.02), (0.036, 0.05), (0.048, 0.078), (0.05, 0.082), (0.044, 0.08), (0.03, 0.05), (0.018, 0.02)], (0, 0, 0), M['blued'], seg=12, axis='y', name='bell', cap=False)
    thr = cyl(0.03, 0.003, (0, 0.05, 0), M['soot'], axis='y', seg=10, name='bellthroat')
    orient([bell, thr], tuple(o0), tuple(d), src=(0, 1, 0)); fp += [bell, thr]
    fp.append(box((0.06, 0.04, 0.05), tuple(o0 + Vector((0, -0.005, -0.01))), M['steel'], bev=0.008, rot=(0.6, 0, 0), name='bellmount'))
    for s2 in (-1, 1):
        for i in range(3): fp.append(box((0.006, 0.026, 0.012), tuple(F.p(-0.1 - i * 0.02, s2 * 1.75, 0.002)), M['soot'], rot=(0, -s2 * 1.75, 0), name='vent'))
    J.P.add(fk, fp)
    J.marks['elbowAt'] = (fk, tuple(o0 + d * 0.085), tuple(d))
    pl = [F.plate('plate_fore', M['scar'], -0.08, 0.0, 0.12, 0.13, off=0.007, n=3.4, spokes=14)]
    for (dy, da) in ((0.04, -0.36), (0.04, 0.36), (-0.04, -0.36), (-0.04, 0.36)):
        y, a = -0.08 + dy, da; pl.append(rivet(tuple(F.p(y, a, 0.007)), 0.008, M['steel'], tuple(F.n(y, a))))
    pl.append(F.plate('hatch', M['steel'], -0.095, 1.45, 0.07, 0.075, off=0.008, n=4.0, spokes=10, sink=0.002))
    for dy in (-0.022, 0.022): pl.append(rivet(tuple(F.p(-0.095 + dy, 1.45, 0.009)), 0.006, M['blued'], tuple(F.n(-0.095, 1.45))))
    J.P.add(fk, pl, 'plates')
    J.P.add(fk, [F.line('l_r1', [(0.03, 0.5), (-0.03, 0.72), (-0.09, 0.6), (-0.145, 0.72)], 0.012, M['lines'], n=6), F.line('l_r2', [(0.02, -0.7), (-0.05, -0.9), (-0.11, -0.75), (-0.15, -0.9)], 0.012, M['lines'], n=6),
                 F.line('l_r3', [(0.0, 2.5), (-0.07, 2.3), (-0.145, 2.45)], 0.011, M['lines'], n=5)], 'lines')
    # the cocking collar: red, a hazard band, two lugs and a charging handle. it slides back up the arm
    ck = [lathe([(0.086, -0.024), (0.106, -0.024), (0.109, -0.017), (0.109, 0.017), (0.106, 0.024), (0.086, 0.024)], (0, COCK_Y, 0), M['red'], seg=16, axis='y', name='cock', cap=False)]
    hz = Surf([(COCK_Y - 0.03, 0.109, 0.109, 0.109), (COCK_Y + 0.03, 0.109, 0.109, 0.109)]).band('cockhaz', M['haz'], COCK_Y - 0.011, COCK_Y + 0.011, off=0.0018, seg=16, rows=1, uv=(0, 6, 0, 1))
    ck.append(hz)
    for s2 in (-1, 1): ck.append(box((0.03, 0.032, 0.044), (s2 * 0.116, COCK_Y, 0), M['steel'], bev=0.006, name='cocklug'))
    ck.append(tube([(-0.03, COCK_Y, -0.105), (-0.03, COCK_Y, -0.135), (0.03, COCK_Y, -0.135), (0.03, COCK_Y, -0.105)], 0.0085, M['chrome'], seg=6, name='cockhandle'))
    J.P.add(fk, ck, 'cock', pivot=(0, COCK_Y, 0), note='the cocking collar: slides +y (up the arm) %.3f to cock' % COCK_PULL)
    J.marks['cock'] = (fk, (0, COCK_Y, 0), (0, 1, 0))
    fist(J, hk, sx)


def fist(J, hk, sx):
    """the right hand: it stays a fist. the skin is gone off the knuckles and what's under it is steel"""
    M = J.M; out = []
    hand = blob('fistback', (0, -0.088, -0.004), (0.08, 0.074, 0.06), M['skin'], seg=14, rings=10, fn=lambda p, n: 0.006 * max(0.0, -n.z))
    def raw(p, n):
        c = mix3((1, 1, 1), (0.9, 0.5, 0.46), 0.85 * smooth01(-0.118 - p.y, 0, 0.03) * smooth01(-n.z + 0.3, 0, 0.6))
        return mix3(c, (1.0, 0.84, 0.82), 0.3)
    tint(hand, raw); out.append(hand)
    for fi in range(4):
        x = (fi - 1.5) * 0.038 * -sx
        f = limb('ffing%d' % fi, [(x, -0.13, -0.04), (x, -0.16, -0.034), (x, -0.172, 0.02), (x, -0.162, 0.062), (x, -0.112, 0.07), (x, -0.086, 0.046)], [0.021, 0.0225, 0.022, 0.021, 0.019, 0.016], M['skin'], seg=8)
        tint(f, lambda p, n: mix3((1, 1, 1), (0.92, 0.6, 0.56), 0.7 * smooth01(-0.15 - p.y, 0, 0.02) * smooth01(0.03 - p.z, 0, 0.04)))
        out.append(f)
    tb = Vector((-sx * 0.07, -0.062, 0.006))
    out.append(limb('fthumb', [tuple(tb + Vector((sx * 0.02, 0.03, 0))), tuple(tb), tuple(tb + Vector((sx * 0.012, -0.05, 0.05))), tuple(tb + Vector((sx * 0.05, -0.078, 0.082))), tuple(tb + Vector((sx * 0.082, -0.084, 0.086)))], [0.028, 0.028, 0.025, 0.022, 0.017], M['skin'], seg=8))
    out.append(blob('fthumbnail', tuple(tb + Vector((sx * 0.082, -0.08, 0.1))), (0.012, 0.011, 0.005), M['nail'], sub=0))
    J.P.add(hk, out)
    # bare knuckles: a steel bar under four domes, a raw edge of skin round it
    kn = [box((0.158, 0.03, 0.05), (0, -0.158, -0.03), M['steel'], bev=0.009, name='knucklebar')]
    for fi in range(4):
        x = (fi - 1.5) * 0.038
        d = ball(0.0215, (x, -0.165, -0.036), M['steel'], scale=(1, 0.8, 1), seg=8, rings=5, name='knuckle')
        tint(d, lambda p, n: mix3((0.75, 0.75, 0.78), (1.25, 1.25, 1.25), smooth01(-p.y, 0.172, 0.182)))  # polished where they land
        kn.append(d)
    edge = [(-0.082, -0.14, -0.056), (0.082, -0.14, -0.056), (0.084, -0.146, -0.004), (-0.084, -0.146, -0.004), (-0.082, -0.14, -0.056)]
    kn.append(sweep(edge, [0.006, 0.0075, 0.006, 0.0075, 0.006], M['lip'], seg=5, name='rawedge'))
    J.P.add(hk, kn, 'fist', note='his knuckles: bare steel, the skin worn off them')
    # the ram the fist rides out on (hidden up the forearm until it fires), the wrist cuff
    rm = [rod((0, 0.012, 0), (0, 0.012 + PUNCH_REACH + 0.04, 0), 0.071, M['chrome'], seg=14, name='ram')]
    for i in range(3): rm.append(cyl(0.0725, 0.004, (0, 0.085 + i * 0.07, 0), M['dark'], axis='y', seg=14, name='ramring'))
    cuff = lathe([(0.07, 0.03), (0.09, 0.03), (0.092, 0.02), (0.092, -0.012), (0.084, -0.02), (0.07, -0.02)], (0, 0, 0), M['steel'], seg=14, axis='y', name='wristcuff', cap=False)
    rm.append(cuff)
    for i in range(6):
        a = TAU * i / 6; rm.append(hexbolt((math.sin(a) * 0.092, 0.005, -math.cos(a) * 0.092), 0.007, 0.006, M['blued'], (math.sin(a), 0, -math.cos(a))))
    J.P.add(hk, rm, 'ram', note='the chrome ram and wrist cuff: move handR -y by up to %.2f and the fist rides out on it' % PUNCH_REACH)
    J.marks['fistAt'] = (hk, (0, -0.184, -0.034), (0, -1, 0))
    J.marks['gripR'] = (hk, (0, -0.125, 0.03), (1, 0, 0))
    J.marks['palmL'] = ('handL', (0, -0.1, 0.042), (0, 0, 1))
