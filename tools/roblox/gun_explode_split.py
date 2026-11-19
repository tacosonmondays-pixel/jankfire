# THE EXPLODED VIEW'S SPLITS (19 Nov 2026, for the owner's blueprint view: roblox/src/shared/GunExplode.luau). The
# view takes a gun apart by its pieces' nodes ("<node>_wz<zone>__<slot>"), but a few base guns keep solids of two real
# parts in one piece (the rifle's muzzle-brake ports in the same "trim" piece as the rail's slots; the revolver's
# barrel in its frame). Here, for the base guns only and only at export (gun_set.py's main loop), each such piece is
# cut into its solids and each solid takes the node of the part it is on, keeping its zone and slot: the same look, the
# same wrap, a real part in the breakdown. The builders are untouched, so every skin built on them is as before.
#   RULES[gun id] = { (node_wz, slot): rule(centre, lo, hi) -> new (node_wz, slot) or None (stays) }
#   (centre / lo / hi: the solid's box in the weapon frame, metres: x right, y up, z back, the muzzle to -z)
import bmesh
from mathutils import Vector


def _W(co): return Vector((co.x, co.z, -co.y))   # Blender frame -> weapon frame (gunkit's P inverted)


RULES = {
    'ar': {
        ('trim_wzN', 'black'): lambda c, lo, hi: ('barrel_wzN', 'black') if c.z < -0.6
            else (('rail_wzN', 'black') if c.y > 0.09 and -0.12 < c.z < 0.21 else None),   # brake ports / rail slots
        ('sight_wzN', 'frame'): lambda c, lo, hi: ('rail_wzN', 'frame'),                   # the top rail
        ('sight_wzN', 'dark'): lambda c, lo, hi: ('fsight_wzN', 'dark') if c.z < -0.3 else None,   # the front post
    },
    'sniper': {
        ('trim_wzN', 'black'): lambda c, lo, hi: ('barrel_wzN', 'black') if c.z < -1.3 else None,  # the brake's slots
        ('stock_wzA', 'body'): lambda c, lo, hi: ('fore_wzA', 'body') if c.z < -0.05
            else (('grip_wzA', 'body') if 0.09 < c.z < 0.26 and hi.z - lo.z < 0.16 else None),
        ('stock_wzN', 'dark'): lambda c, lo, hi: ('fore_wzN', 'dark') if c.z < -0.05 else None,
    },
    'shotgun': {
        ('trim_wzN', 'black'): lambda c, lo, hi: ('barrel_wzN', 'black') if c.z < -0.6 else None,  # the muzzle's face
        ('sight_wzN', 'dark'): lambda c, lo, hi: ('bead_wzN', 'dark') if c.z < -0.3 else None,   # the front blade
    },
    'revolver': {
        ('body_wzA', 'frame'): lambda c, lo, hi: ('barrel_wzA', 'frame') if c.z < -0.15 else None,  # barrel, rib, lug
        ('sight_wzN', 'dark'): lambda c, lo, hi: ('barrel_wzN', 'dark') if c.z < -0.2 else None,    # the front blade
    },
}


def _islands(bm):
    """the piece's solids: its faces grouped by shared vertices"""
    bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    seen = set(); out = []
    for f0 in bm.faces:
        if f0.index in seen: continue
        stack = [f0]; comp = []; seen.add(f0.index)
        while stack:
            f = stack.pop(); comp.append(f.index)
            for v in f.verts:
                for f2 in v.link_faces:
                    if f2.index not in seen: seen.add(f2.index); stack.append(f2)
        out.append(comp)
    return out


def split(g, wid):
    """cut the base gun's mixed pieces by RULES (nothing for any other id); returns [(old key, new key, solids)]"""
    rules = RULES.get(wid)
    if not rules: return []
    done = []
    for key, rule in rules.items():
        bm = g.pieces.get(key)
        if bm is None: continue
        to = {}
        for comp in _islands(bm):
            pts = [_W(v.co) for i in comp for v in bm.faces[i].verts]
            lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
            hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
            nk = rule((lo + hi) / 2, lo, hi) or key
            to.setdefault(nk, []).extend(comp)
        if list(to) == [key]: continue
        import bpy
        for nk, faces in to.items():
            keep = set(faces)
            part = bm.copy()
            part.faces.index_update(); part.faces.ensure_lookup_table()
            bmesh.ops.delete(part, geom=[f for f in part.faces if f.index not in keep], context='FACES')
            if nk == key:
                g.pieces[key] = part
                continue
            old = g.pieces.get(nk)
            if old is None:
                g.pieces[nk] = part
            else:
                me = bpy.data.meshes.new('split')
                part.to_mesh(me); part.free()
                old.from_mesh(me)
                bpy.data.meshes.remove(me)
            done.append((key, nk, len(faces)))
        if key not in to:
            g.pieces.pop(key, None)
        bm.free()
    return done
