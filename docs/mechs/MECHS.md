# Mechs: names for the Gameplay session

**Phase 1 (concept) version.** The joint names below are real (they're the node names in the concept files and will
stay the bone names in phase 2). File names and clip names are the plan; they become real in phase 2, after the owner
approves the look. Concept notes and pictures: `docs/mechs/CONCEPT.md`.

## Space
three.js / game space: metres, y up, the mech faces **-z**, its right side is **+x**, feet on y = 0, the root at the
ground between the feet. Poses are three.js XYZ eulers / quaternions per joint (they drop straight into
`node.rotation` / `node.quaternion`). `_L` = the mech's left (-x), `_R` = its right (+x).

## Files (phase 2 plan)
| file | what |
|---|---|
| `public/models/x_mech_paperplane.glb` | PAPER PLANE: skinned (rigid weights, one bone per joint below), its clips, a `lod1` |
| `public/models/x_mech_nightshift.glb` | NIGHT SHIFT: the same |
| `x_` prefix | loaded late (only when a mech is in play), like the Overdrive Rig; a code fallback stands in until it lands |

Concept stand-ins today (not shipped): `docs/mechs/concept/mech_paperplane_concept.glb`, `mech_nightshift_concept.glb`
(+ `*_poses.json`: `ready` stance, PAPER PLANE `jet`).

## Joints (both frames)
`root` > `hips` > `waist` > `chest` > `neck` > `head`
`chest` > `hatch` (the cockpit hatch: PAPER PLANE's nose lifts, NIGHT SHIFT's breastplate drops), `backpack`
`chest` > `shoulder_L|R` > `upperarm_L|R` > `forearm_L|R` > `hand_L|R`
`hips` > `thigh_L|R` > `shin_L|R` > `foot_L|R` > `toe_L|R`
`hips` > `skirt_L|R` (hip plates on their own hinge so they clear the thighs)

PAPER PLANE also: `shoulder_L|R` > `pod_L|R` (missile pods, 3 pencils each, they point forward), `backpack` >
`wing_L|R` (hinged at the shoulder blades; rest = stowed V, jet mode = swung down flat), `wing_L` > `crane` (the
origami crane drone: detach it from here, fly it at the target, bring it back).
NIGHT SHIFT also: `head` > `beacon` (the security light: spin it about y), `hand_R` > `sword` (grip through the
fist), `forearm_L` > `shield`.

Rest pivots (game coords) are in each file's root `jf` meta: `joints: { name: { at: [x, y, z], parent } }`.

## Materials (roles)
`<p>_paint` = the team / player colour (tint it), `<p>_white`, `<p>_dark`, `<p>_accent`, `<p>_frame` (metal),
`<p>_chrome`, `<p>_glow` (visor slats / bar, sword edges: emissive), `<p>_thrust` (thruster throats: emissive, scale the glow
with boost), `<p>_glass` (canopy / visor). `<p>` = `pp` (PAPER PLANE), `ns` (NIGHT SHIFT). Decals have their own
materials (`*_sticker`, `ns_ledmat` = the PLEASE HOLD screen, emissive).

## Clips (phase 2 plan, names to use)
Shared: `idle`, `walk`, `run`, `boost_dash`, `jump`, `land`, `hover`, `hit_react`, `drop_in` (from the sky, with a dust
ring pose at touchdown), `pilot_in` (the pilot climbs in; hatch opens and closes), `destroy` (armour flies off, the
cockpit pops: the pilot ejects).
PAPER PLANE: `jet_in` (transform to jet), `jet_fly`, `jet_out`, `missile_salvo` (pods flip up, 3 + 3 pencils on
spiralling trails), `lunge` (the dash-at-them that heals), `crane_launch` / `crane_return` (the drone; its own flap clip
`crane_flap` loops while it flies).
NIGHT SHIFT: `sword_combo_1`, `sword_combo_2`, `sword_combo_3` (each stamps an OVERTIME mark; the 4th clocks them
out), `triple_shift` (three dashing slashes), `shield_block`, `shield_bash`, `ground_slam` (the big overhead one).

## Markers (phase 2 plan)
Named empties in the glb for gameplay hooks: `mk_missile_L0..2` / `mk_missile_R0..2` (pencil tips), `mk_thrust_*`
(nozzle throats, for flames), `mk_seat` (pilot seat + eye), `mk_sword_base` / `mk_sword_tip`, `mk_shield_face`,
`mk_beacon`, `mk_eject` (where the pilot pops out), `mk_crane_beak` (PAPER PLANE's drone), `mk_calf_L|R*` (NIGHT
SHIFT's leg boosters). Hitboxes stay boxes on the server; sizes:
PAPER PLANE about 1.6 x 4.9 x 1.4 m (wings excluded), NIGHT SHIFT about 2.4 x 5.7 x 1.6 m (shield excluded).
