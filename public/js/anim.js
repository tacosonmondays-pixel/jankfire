// Keyframed viewmodel animations: melee swings, throws, inspects.
// A key is { t: seconds, p: [x,y,z] offset, r: [x,y,z] radians offset, s: scale, e: easing into this key }.
// Offsets are added on top of the weapon's normal pose. Spins can go past 2π and end on a multiple of 2π so
// there's no pop when the animation finishes. Principles used: short anticipation, snappy strike,
// held follow-through for weight, slower recovery for heavy stuff.

const PI2 = Math.PI * 2;
const EASE = {
  linear: (u) => u,
  smooth: (u) => u * u * (3 - 2 * u),
  snap: (u) => 1 - Math.pow(1 - u, 3), // fast out of the gate: strikes
  in: (u) => u * u * u, // accelerating: falling, wind-ups
  back: (u) => { const c = 1.9; return 1 + (c + 1) * Math.pow(u - 1, 3) + c * Math.pow(u - 1, 2); }, // overshoot
};
const K = (t, p = [0, 0, 0], r = [0, 0, 0], e = 'smooth', s = 1) => ({ t, p, r, e, s });

export const ANIMS = {
  // ------------------------------------------------------------ melee
  swing_bread: { hit: 0.19, keys: [
    K(0), K(0.13, [0.12, 0.08, 0.1], [0.25, -0.9, -0.3]),
    K(0.24, [-0.38, -0.02, -0.12], [-0.15, 1.9, 0.5], 'snap'),
    K(0.38, [-0.42, -0.06, -0.08], [-0.2, 2.1, 0.6]),
    K(0.62),
  ], events: [[0.15, 'whoosh']], trail: [0.12, 0.34] },
  swing_bread2: { hit: 0.19, keys: [ // backhand for the combo
    K(0), K(0.13, [-0.3, 0.06, 0.05], [0.2, 1.4, 0.4]),
    K(0.24, [0.14, -0.05, -0.12], [-0.1, -0.9, -0.5], 'snap'),
    K(0.38, [0.18, -0.08, -0.08], [-0.15, -1.1, -0.55]),
    K(0.62),
  ], events: [[0.15, 'whoosh']], trail: [0.12, 0.34] },
  swing_spoon: { hit: 0.1, keys: [
    K(0), K(0.06, [0.02, 0.02, 0.08], [0.2, 0, 0]),
    K(0.12, [-0.09, 0.05, -0.2], [-0.12, 0.38, 0.1], 'snap'), // jab in toward the middle, side-on so the spoon doesn't hide behind your fist
    K(0.22, [-0.09, 0.05, -0.19], [-0.14, 0.4, 0.1]),
    K(0.4),
  ], events: [[0.07, 'whoosh']], trail: [0.05, 0.18] },
  swing_spoon2: { hit: 0.11, keys: [ // overhead stab
    K(0), K(0.07, [0, 0.14, 0.05], [0.9, 0, 0]),
    K(0.13, [-0.07, -0.02, -0.17], [-0.45, 0.35, 0.15], 'snap'),
    K(0.24, [-0.07, -0.03, -0.16], [-0.5, 0.37, 0.15]),
    K(0.42),
  ], events: [[0.08, 'whoosh']], trail: [0.06, 0.2] },
  throw_slipper: { hit: 0.16, keys: [
    K(0), K(0.12, [0.05, 0.2, 0.15], [1.0, 0, 0.4], 'in'),
    K(0.2, [-0.05, -0.05, -0.25], [-0.8, 0, -0.2], 'snap'),
    K(0.3, [-0.05, -0.12, -0.2], [-0.9, 0, -0.2]),
  ], events: [[0.14, 'whoosh']], trail: [0.12, 0.24] },
  throw_snowball: { keys: [
    K(0), K(0.07, [0.03, 0.1, 0.1], [0.9, 0, 0.3], 'in'),
    K(0.13, [-0.04, -0.03, -0.2], [-0.7, 0, -0.1], 'snap'), K(0.22, [-0.04, -0.06, -0.18], [-0.8, 0, -0.1]), K(0.34),
  ], events: [[0.1, 'whoosh']], trail: [0.07, 0.16] },
  toss_item: { keys: [K(0), K(0.08, [0, -0.08, 0.06], [0.4, 0, 0.2], 'in'), K(0.16, [0, -0.04, -0.05], [-0.3, 0, 0], 'snap'), K(0.34)] },
  catch_slipper: { keys: [K(0, [0.05, -0.25, -0.1], [-0.6, 0, 0]), K(0.18, [0, 0.02, 0], [0.1, 0, 0], 'back'), K(0.3)], events: [[0.12, 'thwack']] },
  yank_popper: { keys: [K(0), K(0.05, [0, 0.02, 0.12], [0.5, 0, 0.1], 'snap'), K(0.32)] },

  // Blood Cross finger gun. channels: index + thumb pivots (radians about X), curl = how far the fist is open (0 shut, 1 open hand,
  // below 0 squeezed). bang: the hammer (thumb) snaps down, the fist squeezes, the wrist kicks up and the barrel (index) flicks.
  // draw: an open hand comes up and snaps shut into the gun, thumb cocked with a click. inspect: blow the blood off the fingertip
  bang_bloodcross: { keys: [K(0), K(0.035, [0, 0.018, 0.028], [0.32, 0.03, 0.08], 'snap'), K(0.12, [0, 0.007, 0.01], [0.1, 0.01, 0.03]), K(0.3)],
    ch: { index: [[0, 0], [0.03, 0.22], [0.15, 0]], thumb: [[0, 0], [0.025, -0.95], [0.09, -0.95], [0.22, 0.12], [0.3, 0]], curl: [[0, 0], [0.03, -0.12], [0.2, 0]] } },
  draw_bloodcross: { keys: [K(0, [0.03, -0.24, 0.08], [-0.8, 0.25, 0.4]), K(0.22, [0, 0.012, 0], [0.08, 0, 0.02], 'snap'), K(0.45)],
    ch: { curl: [[0, 0.9], [0.14, 0.85], [0.27, -0.06], [0.34, 0]], thumb: [[0, -0.6], [0.2, -0.6], [0.3, 0.15], [0.38, 0]], index: [[0, 0.12], [0.25, 0]] },
    events: [[0.3, 'click']] },
  inspect_bloodcross: { keys: [
    K(0), K(0.32, [-0.07, 0.045, -0.01], [1.05, -0.25, 0.05]), // fingertip up in front of your mouth
    K(0.95, [-0.075, 0.05, -0.012], [1.08, -0.27, 0.06]), // ...and blow the blood off it
    K(1.12, [-0.01, 0.012, 0], [0.15, 0, 0]),
    K(1.5, [0, 0.012, 0], [0.05, 0, PI2 + 0.25]), // spin it round the finger like a pistol
    K(1.72, [0, 0, 0], [0, 0, PI2], 'back'), K(1.95, [0, 0, 0], [0, 0, PI2]),
    ], ch: { thumb: [[0.25, 0], [0.35, -0.45], [0.95, -0.45], [1.1, 0], [1.62, 0], [1.68, -0.35], [1.78, 0.1], [1.86, 0]], curl: [[1.1, 0], [1.2, 0.22], [1.5, 0.22], [1.64, 0]] },
    events: [[0.5, 'bloodpuff'], [1.18, 'whoosh'], [1.69, 'click']] },

  // knife, done like CS: left click alternates a right->left and a left->right diagonal slash (fast, ~0.4s),
  // right click is a heavy stab: pull back, punch forward, hold, slow recovery (~0.9s)
  swing_knife: { hit: 0.1, keys: [
    K(0), K(0.06, [0.07, 0.07, 0.04], [0.25, -0.55, -0.55]), // cock up and right
    K(0.13, [-0.14, -0.06, -0.12], [-0.2, 0.9, 0.75], 'snap'), // rip down-left
    K(0.22, [-0.16, -0.08, -0.1], [-0.25, 0.98, 0.8]), K(0.4),
  ], events: [[0.07, 'whoosh']], trail: [0.06, 0.2] },
  swing_knife2: { hit: 0.1, keys: [
    K(0), K(0.06, [-0.1, 0.05, 0.03], [0.2, 0.75, 0.6]), // backhand: cock up and left
    K(0.13, [0.1, -0.06, -0.12], [-0.2, -0.75, -0.7], 'snap'), // rip down-right
    K(0.22, [0.11, -0.08, -0.1], [-0.25, -0.82, -0.75]), K(0.4),
  ], events: [[0.07, 'whoosh']], trail: [0.06, 0.2] },
  // (the katana's swings, draw, inspect and parry live in katanavm.js: two-handed, posed by where the blade points)
  stab_knife: { hit: 0.29, keys: [
    K(0), K(0.22, [0.05, 0.07, 0.16], [0.5, 0.15, 0.15], 'in'), // wind up: pull back and raise
    K(0.29, [-0.08, 0.02, -0.24], [-0.12, 0.42, 0.12], 'snap'), // thrust in toward the middle, the blade side-on so you see it go in
    K(0.46, [-0.08, 0.015, -0.23], [-0.14, 0.44, 0.12]), // hold it in
    K(0.85, [0, 0, 0], [0, 0, 0], 'smooth'),
  ], events: [[0.25, 'whooshBig']], trail: [0.23, 0.34] },
  swing_slapper: { hit: 0.17, keys: [
    K(0), K(0.1, [0.05, 0.12, 0.15], [0.9, 0, 0.2], 'in'),
    K(0.18, [-0.08, -0.02, -0.21], [-0.62, 0.34, 0.15], 'snap'), K(0.32, [-0.08, -0.04, -0.2], [-0.68, 0.36, 0.15]), K(0.52), // the slap lands in the middle, the hand in sight
  ], events: [[0.12, 'whoosh']], trail: [0.1, 0.26] },
  // zombie claw: a quick raking swipe across, then a backhand the other way
  swing_claw: { hit: 0.1, keys: [
    K(0), K(0.07, [0.1, 0.1, 0.06], [0.6, -0.5, -0.5], 'in'),
    K(0.14, [-0.16, -0.08, -0.12], [-0.5, 0.9, 0.7], 'snap'), K(0.24, [-0.18, -0.1, -0.1], [-0.55, 1.0, 0.75]), K(0.42),
  ], events: [[0.08, 'whoosh']], trail: [0.06, 0.22] },
  swing_claw2: { hit: 0.1, keys: [
    K(0), K(0.07, [-0.14, 0.1, 0.05], [0.6, 0.7, 0.6], 'in'),
    K(0.14, [0.1, -0.08, -0.12], [-0.5, -0.7, -0.7], 'snap'), K(0.24, [0.12, -0.1, -0.1], [-0.55, -0.8, -0.75]), K(0.42),
  ], events: [[0.08, 'whoosh']], trail: [0.06, 0.22] },
  swing_scythe: { hit: 0.24, keys: [ // heavy: slower wind-up, long follow-through
    K(0), K(0.16, [0.2, 0.15, 0.15], [0.4, -1.2, -0.6]),
    K(0.3, [-0.38, -0.06, -0.2], [-0.25, 1.95, 0.85], 'snap'), K(0.48, [-0.42, -0.09, -0.16], [-0.3, 2.1, 0.92]), K(0.78), // (the follow-through stays half on screen)
  ], events: [[0.2, 'whoosh']], trail: [0.16, 0.44] },
  swing_scythe2: { hit: 0.24, keys: [
    K(0), K(0.16, [-0.35, 0.18, 0.1], [0.5, 1.6, 0.6]),
    K(0.3, [0.12, -0.08, -0.2], [-0.25, -1.25, -0.75], 'snap'), K(0.48, [0.14, -0.11, -0.16], [-0.3, -1.35, -0.8]), K(0.78),
  ], events: [[0.2, 'whoosh']], trail: [0.16, 0.44] },
  fold_scythe: { keys: [K(0), K(0.15, [0, -0.18, 0.06], [0.7, 0, 0.9], 'snap'), K(0.4)], events: [[0.12, 'click'], [0.2, 'click']] },
  // scales of justice, swung like a mace: a heavy overhead smash, then (click again) a flat side swing.
  // the pans hang on chains (scales.js), so every swing flings them about
  swing_scales: { hit: 0.22, keys: [
    K(0), K(0.14, [0, 0.18, 0.05], [0.5, -0.1, 0.3], 'in'), // heave it up and back over your head
    K(0.23, [-0.18, 0.1, 0.06], [-0.65, 0.05, 0.2], 'snap'), // SMASH: the beam lands right across the middle of the screen
    K(0.36, [-0.19, 0.06, 0.06], [-0.8, 0.05, 0.2]), // it's heavy: it sinks a little and stays down a moment
    K(0.6),
  ], events: [[0.02, 'chains'], [0.15, 'whooshBig'], [0.3, 'chains']], trail: [0.14, 0.34] },
  swing_scales2: { hit: 0.19, keys: [
    K(0), K(0.12, [0.08, 0.16, 0.06], [-0.2, -0.6, -0.95], 'in'), // cock it out to the right
    K(0.22, [-0.14, 0.27, 0], [-0.25, 2.25, -1.25], 'snap'), // sweep it flat across the middle, head first
    K(0.34, [-0.24, 0.22, 0], [-0.25, 2.7, -1.25]), K(0.58),
  ], events: [[0.02, 'chains'], [0.12, 'whooshBig'], [0.28, 'chains']], trail: [0.12, 0.3] },
  draw_scales: { keys: [K(0, [0.02, -0.32, 0.06], [-0.6, 0, 0.35]), K(0.3, [0, 0.015, 0], [0.06, 0, -0.05], 'back'), K(0.46)], events: [[0.05, 'chains'], [0.3, 'chains']] },
  inspect_scales: { keys: [ // hold it up, jiggle it, watch the pans swing
    K(0), K(0.4, [-0.13, 0.08, 0.06], [0.12, 0.35, 0.1]),
    K(0.9, [-0.13, 0.09, 0.06], [0.12, 0.45, 0.1]),
    K(1.0, [-0.12, 0.09, 0.06], [0.12, 0.45, -0.22], 'snap'), K(1.12, [-0.13, 0.09, 0.06], [0.12, 0.45, 0.2], 'snap'),
    K(1.25, [-0.13, 0.09, 0.06], [0.12, 0.45, 0.05]),
    K(2.0, [-0.13, 0.09, 0.06], [0.1, 0.4, 0.05]), K(2.5),
  ], events: [[0.95, 'chains'], [1.1, 'chains'], [1.6, 'ting']] },


  // ------------------------------------------------------------ card deck: flick the card off the top of the fan
  throw_card: { keys: [
    K(0), K(0.08, [0.03, 0.06, 0.08], [0.55, 0.25, 0.35], 'in'), // cock the wrist back
    K(0.14, [-0.05, -0.02, -0.14], [-0.65, -0.15, -0.25], 'snap'), // FLICK
    K(0.22, [-0.06, -0.04, -0.12], [-0.75, -0.15, -0.3]), K(0.42),
  ], events: [[0.12, 'flick']], trail: [0.09, 0.2] },
  throw_card_ult: { keys: [ // face cards + jokers: big spinning wind-up
    K(0), K(0.16, [0.08, 0.12, 0.14], [0.9, 0.6, 0.7], 'in'),
    K(0.24, [-0.12, -0.03, -0.2], [-1.0, -0.4, -0.45], 'snap'),
    K(0.36, [-0.12, -0.06, -0.17], [-1.05, -0.4, -0.5]), K(0.6),
  ], events: [[0.06, 'ultcharge'], [0.22, 'flick']], trail: [0.17, 0.3] },
  raise_card: { keys: [ // hearts + aces: hold it up, it bursts
    K(0), K(0.14, [-0.07, 0.1, -0.06], [0.7, 0, 0], 'snap'),
    K(0.32, [-0.07, 0.115, -0.07], [0.75, 0, 0.05]),
    K(0.36, [-0.07, 0.1, -0.06], [0.7, 0, 0], 'snap', 0.9), K(0.58),
  ], events: [[0.31, 'burst']] },

  // ------------------------------------------------------------ draws: what it looks like when you pull it out
  draw_gun: { keys: [K(0, [0.03, -0.26, 0.06], [-0.9, 0.35, 0.45]), K(0.2, [0, 0.012, 0], [0.09, -0.03, -0.06], 'snap'), K(0.34)], events: [[0.19, 'click']] },
  draw_heavy: { keys: [K(0, [0.06, -0.36, 0.12], [-0.7, 0.25, 0.65]), K(0.3, [0, 0.02, 0], [0.1, 0, -0.05], 'snap'), K(0.48)], events: [[0.28, 'clunk']] },
  draw_knife: { keys: [K(0, [0, -0.18, 0.02], [-0.8, 0, -PI2]), K(0.28, [0, 0.015, 0], [0.08, 0, 0], 'snap'), K(0.4)], events: [[0.24, 'shing']] },
  draw_melee: { keys: [ // toss it up a bit and catch it
    K(0, [0, -0.26, 0], [-0.5 - PI2, 0, 0]), K(0.16, [0, 0.1, 0], [-PI2 * 0.45, 0, 0.3], 'snap'), // one forward flip
    K(0.3, [0, -0.02, 0], [-0.1, 0, 0], 'in'), K(0.42),
  ], events: [[0.29, 'thwack']] },
  // the loaf's too long for the toss-and-catch (its first frame filled the screen): heaved up from low right onto the shoulder
  draw_bread: { keys: [K(0, [0.12, -0.5, 0.12], [-0.9, 0.1, 0.5]), K(0.22, [0, 0.03, 0], [0.12, 0, -0.06], 'snap'), K(0.34, [0, -0.012, 0], [-0.05, 0, 0.02]), K(0.46)], events: [[0.2, 'thwack']] },
  draw_scythe: { keys: [K(0, [0, -0.3, 0], [0, 0, -PI2]), K(0.42, [0, 0.02, 0], [0.05, 0, 0], 'snap'), K(0.55)], events: [[0.38, 'shing']] },
  draw_cards: { keys: [K(0, [0, -0.2, 0], [-0.6, 0, 0], 'smooth', 0.4), K(0.24, [0, 0.02, 0], [0.05, 0, 0], 'back', 1), K(0.34)], events: [[0.08, 'riffle']] },
  draw_bow: { keys: [K(0, [-0.12, -0.26, 0], [0, 0, 0.9]), K(0.3, [0, 0, 0], [0, 0, 0], 'back'), K(0.4)], events: [[0.2, 'thwack']] },

  // ------------------------------------------------------------ gun follow-ups
  pump_shotgun: { keys: [
    K(0), K(0.1, [0.01, -0.035, 0.07], [0.16, 0, -0.28]), K(0.17, [0.01, -0.035, -0.01], [0.13, 0, -0.28], 'snap'), K(0.32),
  ], events: [[0.09, 'click'], [0.13, 'shellRed'], [0.17, 'click']] },
  bolt_sniper: { keys: [
    K(0), K(0.12, [0.02, -0.045, 0.04], [0.12, 0.22, -0.55]), K(0.22, [0.02, -0.045, 0.09], [0.12, 0.22, -0.55], 'snap'),
    K(0.3, [0.02, -0.045, 0.03], [0.12, 0.22, -0.55], 'snap'), K(0.48),
  ], events: [[0.1, 'click'], [0.2, 'shell'], [0.29, 'click']] },

  // ------------------------------------------------------------ melee inspects (the good ones)
  inspect_bread: { keys: [
    K(0), K(0.35, [-0.2, 0.15, 0.05], [0.3, 0.5, 0.2]),
    K(0.55, [-0.2, 0.7, -0.2], [0.3 + PI2, 0.5, 0.2], 'snap'), // toss it
    K(0.85, [-0.2, 0.85, -0.25], [0.3 + PI2 * 1.5, 0.5, 0.2], 'linear'),
    K(1.15, [-0.2, 0.12, 0.05], [0.3 + PI2 * 2, 0.5, 0.2], 'in'), // catch
    K(1.3, [-0.2, 0.06, 0.05], [0.3 + PI2 * 2, 0.5, 0.2]),
    K(1.7, [-0.3, 0.12, 0.2], [0.1 + PI2 * 2, 1.4, 0.3]), // up to the mouth
    K(1.85, [-0.3, 0.1, 0.24], [0.1 + PI2 * 2, 1.4, 0.3]),
    K(2.0, [-0.3, 0.12, 0.2], [0.1 + PI2 * 2, 1.4, 0.3]),
    K(2.15, [-0.3, 0.1, 0.24], [0.1 + PI2 * 2, 1.4, 0.3]),
    K(2.5, [-0.15, 0.1, 0], [0.6 + PI2 * 2, 0.3, 0.6]), // hold it up, proud
    K(3.2, [0, 0, 0], [PI2 * 2, 0, 0]),
  ], events: [[0.5, 'whoosh'], [1.15, 'thwack'], [1.82, 'crunch'], [1.86, 'crumbs'], [2.12, 'crunch'], [2.16, 'crumbs']] },
  inspect_slipper: { keys: [
    K(0), K(0.3, [-0.15, 0.12, 0], [-1.2, 0, 0]),
    K(2.0, [-0.15, 0.14, 0], [-1.2, PI2 * 3, 0], 'linear'), // spin it on one finger
    K(2.2, [-0.22, 0.02, 0.05], [-0.4, PI2 * 3, 0.6], 'snap'), // slap your own hand
    K(2.8, [0, 0, 0], [0, PI2 * 3, 0]),
  ], events: [[2.18, 'thwack']] },
  inspect_spoon: { keys: [
    K(0), K(0.25, [-0.1, 0.1, 0.02]),
    K(1.3, [-0.1, 0.12, 0.02], [0, 0, PI2 * 2], 'linear'), // baton twirl
    K(1.6, [-0.12, 0.08, 0.12], [1.2, 0.4, PI2 * 2]), // check your reflection
    K(2.0, [-0.12, 0.08, 0.12], [1.2, 0.4, PI2 * 2]),
    K(2.1, [-0.1, 0.08, 0.12], [1.2, 0.5, PI2 * 2]), // polish polish
    K(2.2, [-0.14, 0.08, 0.12], [1.2, 0.3, PI2 * 2]),
    K(2.3, [-0.1, 0.08, 0.12], [1.2, 0.5, PI2 * 2]),
    K(2.4, [-0.14, 0.08, 0.12], [1.2, 0.3, PI2 * 2]),
    K(3.0, [0, 0, 0], [0, 0, PI2 * 2]),
  ], events: [[1.65, 'ting'], [2.15, 'squeak'], [2.35, 'squeak']] },

  // ------------------------------------------------------------ knives: one style each, modelled on how the real knife families move
  // classic combat knife: turn it over to look at the flipside, then back
  inspect_knife: { keys: [
    K(0), K(0.3, [-0.07, 0.06, 0.01], [0.15, 0.75, 0.15]),
    K(0.7, [-0.07, 0.06, 0.01], [0.15, 0.75, 0.15 + Math.PI]), // roll to the flipside
    K(1.1, [-0.07, 0.06, 0.01], [0.15, 0.75, 0.15 + Math.PI]),
    K(1.5, [-0.07, 0.06, 0.01], [0.15, 0.75, 0.15 + PI2]), // and back
    K(1.9, [0, 0, 0], [0, 0, PI2]),
  ], events: [[0.7, 'ting']] },
  // kitchen knife = bayonet family: rolls round the hand on draw; inspect rolls it over, then one little end-over-end toss
  draw_knife_kitchen: { keys: [K(0, [0.02, -0.16, 0.02], [-0.6, 0, PI2]), K(0.32, [0, 0.015, 0], [0.06, 0, 0], 'snap'), K(0.44)], events: [[0.3, 'shing']] },
  inspect_knife_kitchen: { keys: [
    K(0), K(0.3, [-0.07, 0.06, 0.01], [0.15, 0.7, 0.2]),
    K(0.65, [-0.07, 0.06, 0.01], [0.15, 0.7, 0.2 + Math.PI]),
    K(1.0, [-0.07, 0.06, 0.01], [0.15, 0.7, 0.2 + Math.PI]),
    K(1.3, [-0.07, 0.06, 0.01], [0.15, 0.7, 0.2 + PI2]),
    K(1.5, [-0.06, 0.2, 0.0], [0.15 + Math.PI, 0.7, 0.2 + PI2], 'snap'), // toss
    K(1.7, [-0.07, 0.07, 0.01], [0.15 + PI2, 0.7, 0.2 + PI2], 'in'), // catch
    K(2.1, [0, 0, 0], [PI2, 0, PI2]),
  ], events: [[0.65, 'ting'], [1.7, 'thwack']] },
  // bowie = huntsman/bowie family: vertical barrel-roll toss and catch; inspect ends holding the blade upright
  draw_knife_bowie: { keys: [
    K(0, [0, -0.2, 0.02], [-0.5, 0, 0]),
    K(0.18, [0, 0.12, -0.02], [-0.5 + Math.PI, 0, Math.PI], 'snap'),
    K(0.36, [0, 0, 0], [-0.1 + PI2, 0, PI2], 'in'),
    K(0.5, [0, 0, 0], [PI2, 0, PI2]),
  ], events: [[0.36, 'thwack']] },
  inspect_knife_bowie: { keys: [
    K(0), K(0.25, [-0.05, 0.02, 0], [0.2, 0.4, 0.1]),
    K(0.55, [-0.05, 0.17, -0.09], [0.2 + Math.PI, 0.4, 0.1 + Math.PI], 'snap'), // big toss, barrel rolling
    K(0.85, [-0.05, 0.04, 0], [0.2 + PI2, 0.4, 0.1 + PI2], 'in'), // catch
    K(1.15, [-0.08, 0.1, 0], [1.25 + PI2, 0.5, 0.1 + PI2]), // blade straight up
    K(1.6, [-0.08, 0.1, 0], [1.2 + PI2, 0.95, 0.12 + PI2]), // turn it in the light
    K(2.0, [0, 0, 0], [PI2, 0, PI2]),
  ], events: [[0.85, 'thwack'], [1.3, 'ting']] },
  // cleaver = falchion family: flips out on draw; inspect balances it upright on a fingertip (and nearly drops it)
  draw_knife_cleaver: { keys: [K(0, [0, -0.2, 0], [-0.6 - PI2, 0, 0]), K(0.34, [0, 0.02, 0], [0.05, 0, 0], 'back'), K(0.48)], events: [[0.32, 'clunk']] },
  inspect_knife_cleaver: { keys: [
    K(0), K(0.35, [-0.08, 0.08, 0.02], [1.35, 0.4, 0]),
    K(0.65, [-0.08, 0.09, 0.02], [1.4, 0.4, 0.18]), K(0.9, [-0.08, 0.09, 0.02], [1.38, 0.4, -0.2]),
    K(1.1, [-0.07, 0.09, 0.02], [1.45, 0.4, 0.12]), K(1.25, [-0.08, 0.1, 0.02], [1.35, 0.4, -0.05]),
    K(1.45, [-0.04, 0, 0.04], [0.4, 0.2, 0.3], 'snap'), // grab it
    K(1.9),
  ], events: [[1.45, 'thwack']] },
  swing_knife_cleaver: { hit: 0.14, keys: [ // overhead chop
    K(0), K(0.09, [0.02, 0.12, 0.08], [1.0, 0.1, 0.1], 'in'),
    K(0.16, [-0.03, -0.1, -0.14], [-0.9, 0, -0.05], 'snap'), K(0.26, [-0.03, -0.11, -0.12], [-0.95, 0, -0.05]), K(0.46),
  ], events: [[0.1, 'whoosh']], trail: [0.09, 0.24] },
  // switchblade = flip knife / stiletto family: the blade flicks out on draw; inspect is a snappy double flip, then shut and open
  draw_knife_switch: { keys: [
    K(0, [0, -0.12, 0.03], [0.6, 0, 0.25]), K(0.14, [0, -0.01, 0.01], [0.45, 0, 0.12]),
    K(0.2, [0, 0.02, -0.02], [-0.18, 0, 0], 'snap'), K(0.36),
  ], ch: { blade: [[0, Math.PI], [0.14, Math.PI], [0.19, 0]] }, events: [[0.18, 'shing']] },
  inspect_knife_switch: { keys: [
    K(0), K(0.2, [-0.05, 0.05, 0.01], [0.15, 0.6, 0.1]),
    K(0.42, [-0.05, 0.08, 0.02], [0.15 + PI2, 0.6, 0.1], 'snap'), // flip
    K(0.64, [-0.05, 0.08, 0.02], [0.15 + PI2 * 2, 0.6, 0.1], 'snap'), // flip again
    K(0.8, [-0.05, 0.05, 0.01], [0.15 + PI2 * 2, 0.6, 0.1]),
    K(1.5, [-0.05, 0.05, 0.01], [0.15 + PI2 * 2, 0.7, 0.1]),
    K(1.9, [0, 0, 0], [PI2 * 2, 0, 0]),
  ], ch: { blade: [[0.85, 0], [0.95, Math.PI], [1.25, Math.PI], [1.31, 0]] }, events: [[0.42, 'click'], [0.64, 'click'], [0.95, 'click'], [1.31, 'shing']] },
  // karambit: reverse grip, spins round your finger through the ring (draw + inspect), hooking rakes, hammer-fist stab
  draw_knife_karambit: { keys: [K(0, [-0.04, -0.12, 0], [0, 1.25, 0]), K(0.12, [-0.05, 0, 0], [0, 1.25, 0], 'snap'), K(0.5, [-0.05, 0.01, 0], [0.05, 1.25, 0]), K(0.66)],
    ch: { spin: [[0.06, 0], [0.5, PI2 * 2]] }, events: [[0.5, 'shing']] },
  inspect_knife_karambit: { keys: [
    K(0), K(0.3, [-0.06, 0.05, 0], [0.1, 1.25, 0]), // turn it side-on so the spin reads
    K(1.3, [-0.06, 0.05, 0], [0.1, 1.25, 0]),
    K(1.6, [-0.06, 0.05, -0.02], [0.1, 0.4, Math.PI]), // look at the flipside
    K(1.9, [-0.06, 0.05, -0.02], [0.1, 0.4, Math.PI]),
    K(2.3, [0, 0, 0], [0, 0, PI2]),
  ], ch: { spin: [[0.3, 0], [0.75, PI2 * 2], [0.85, PI2 * 2], [1.25, PI2 * 3]] }, events: [[0.75, 'ting'], [1.25, 'ting']] },
  swing_knife_karambit: { hit: 0.1, keys: [
    K(0), K(0.06, [0.08, 0.05, 0.02], [-0.2, -0.6, -0.9]),
    K(0.13, [-0.15, -0.04, -0.1], [0.3, 0.9, 0.9], 'snap'), K(0.22, [-0.17, -0.06, -0.08], [0.35, 1.0, 1.0]), K(0.4),
  ], events: [[0.07, 'whoosh']], trail: [0.06, 0.2] },
  swing_knife_karambit2: { hit: 0.1, keys: [
    K(0), K(0.06, [-0.1, 0.04, 0.02], [-0.2, 0.7, 0.8]),
    K(0.13, [0.1, -0.05, -0.1], [0.3, -0.8, -0.9], 'snap'), K(0.22, [0.11, -0.07, -0.08], [0.35, -0.9, -1.0]), K(0.4),
  ], events: [[0.07, 'whoosh']], trail: [0.06, 0.2] },
  stab_knife_karambit: { hit: 0.29, keys: [
    K(0), K(0.22, [0.04, 0.14, 0.12], [-0.6, 0.1, 0.2], 'in'),
    K(0.29, [-0.08, 0.0, -0.22], [0.35, 0.42, 0.2], 'snap'), K(0.46, [-0.08, -0.01, -0.21], [0.37, 0.44, 0.2]), K(0.85), // (side-on: the claw stays in sight)
  ], events: [[0.25, 'whooshBig']], trail: [0.23, 0.34] },
  // (butterfly: draw + inspect live in balisong.js)
  inspect_slapper: { keys: [ // wave hello, then clap
    K(0), K(0.3, [-0.1, 0.12, 0.05], [0.3, 0, 0]),
    K(0.5, [-0.1, 0.12, 0.05], [0.3, 0, 0.6]), K(0.7, [-0.1, 0.12, 0.05], [0.3, 0, -0.6]),
    K(0.9, [-0.1, 0.12, 0.05], [0.3, 0, 0.6]), K(1.1, [-0.1, 0.12, 0.05], [0.3, 0, -0.6]),
    K(1.3, [-0.14, 0.05, 0.02], [-0.3, 0.9, 0], 'snap'), K(1.45, [-0.08, 0.08, 0.04], [0.2, 0.3, 0]),
    K(1.6, [-0.14, 0.05, 0.02], [-0.3, 0.9, 0], 'snap'), K(2.1),
  ], events: [[1.3, 'thwack'], [1.6, 'thwack']] },
  inspect_scythe: { keys: [
    K(0), K(0.4, [-0.15, 0.12, 0.05], [0.4, 0.6, 0]),
    K(1.6, [-0.15, 0.14, 0.05], [0.4, 0.6, PI2], 'linear'), // twirl it
    K(1.85, [-0.1, -0.12, -0.05], [0.9, 0.3, PI2], 'snap'), // plant the blade
    K(2.4, [-0.1, -0.12, -0.05], [0.9, 0.3, PI2]), K(2.9, [0, 0, 0], [0, 0, PI2]),
  ], events: [[0.4, 'whoosh'], [1.85, 'thwack']] },

  // ------------------------------------------------------------ everything else
  inspect_gun: { keys: [
    K(0), K(0.35, [-0.08, 0.05, 0.04], [0.15, 0.9, 0.5]),
    K(1.1, [-0.09, 0.06, 0.04], [0.2, 0.95, 0.55]),
    K(1.5, [-0.05, 0.06, 0.02], [0.6, -0.5, -0.6]),
    K(2.0, [-0.05, 0.07, 0.02], [0.62, -0.55, -0.62]),
    K(2.4),
  ] },
  inspect_revolver: { keys: [
    K(0), K(0.2, [-0.05, 0.04, 0]),
    K(1.0, [-0.05, 0.04, 0], [-PI2 * 2, 0, 0], 'linear'), // spin it around the trigger finger
    K(1.3, [-0.06, 0.05, 0.03], [-PI2 * 2, 0.9, 0.3], 'back'),
    K(1.9, [0, 0, 0], [-PI2 * 2, 0, 0]),
  ], events: [[1.0, 'click']] },
  inspect_shotgun: { keys: [
    K(0), K(0.25, [-0.04, 0.04, 0], [0.2, 0.4, 0.3]),
    K(0.4, [-0.04, 0.04, 0.07], [0.2, 0.4, 0.3], 'snap'), K(0.52, [-0.04, 0.04, 0], [0.2, 0.4, 0.3], 'snap'),
    K(0.7, [-0.04, 0.04, 0.07], [0.2, 0.4, 0.3], 'snap'), K(0.82, [-0.04, 0.04, 0], [0.2, 0.4, 0.3], 'snap'),
    K(1.4, [-0.03, 0.05, 0], [0.4, -0.3, -0.3]), K(1.9),
  ], events: [[0.4, 'click'], [0.52, 'click'], [0.7, 'click'], [0.82, 'click']] },
  inspect_minigun: { keys: [
    K(0), K(0.4, [-0.04, 0.06, 0.03], [0.25, 0.4, 0]),
    K(1.6, [-0.05, 0.06, 0.03], [0.25, 0.5, 0.05]),
    K(2.0, [-0.04, 0.04, 0], [-0.1, -0.3, -0.2]), K(2.5),
  ], events: [[0.4, 'spin']] },
  inspect_sniper: { keys: [
    K(0), K(0.45, [-0.1, 0.05, 0.08], [0.1, 1.2, 0.2]),
    K(1.0, [-0.12, 0.05, 0.12], [0.1, 1.25, 0.2]), K(1.6, [-0.1, 0.05, 0.08], [0.1, 1.2, 0.2]),
    K(2.2),
  ], events: [[0.8, 'blow']] },
  inspect_cig: { keys: [
    K(0), K(0.4, [-0.13, 0.04, 0.1], [0, 1.0, 0]), // long drag
    K(1.3, [-0.13, 0.04, 0.11], [0, 1.0, 0]),
    K(1.55, [-0.02, 0, 0], [0, 0.3, 0]),
    K(1.68, [0, 0.02, 0], [0, 0.3, -0.9], 'snap'), // flick the ash
    K(2.1),
  ], events: [[1.35, 'smoke'], [1.68, 'spark']] },
  inspect_duck: { keys: [
    K(0), K(0.25, [-0.06, 0.06, 0.04], [0, 0.6, 0]),
    K(0.4, [-0.06, 0.04, 0.04], [0, 0.6, 0], 'snap', 0.65), K(0.6, [-0.06, 0.06, 0.04], [0, 0.6, 0], 'back', 1),
    K(0.85, [-0.06, 0.04, 0.04], [0, 0.6, 0], 'snap', 0.6), K(1.05, [-0.06, 0.06, 0.04], [0, 0.6, 0], 'back', 1),
    K(1.5),
  ], events: [[0.4, 'squeak'], [0.85, 'squeak']] },
  inspect_reverse: { keys: [
    K(0), K(0.25, [-0.06, 0.06, 0.04]),
    K(1.1, [-0.06, 0.08, 0.04], [Math.PI, PI2 * 2, 0], 'linear'),
    K(1.5, [-0.06, 0.08, 0.06], [PI2, PI2 * 2, 0], 'back'),
    K(2.0, [0, 0, 0], [PI2, PI2 * 2, 0]),
  ], events: [[1.5, 'ting']] },
  inspect_popper: { keys: [
    K(0), K(0.4, [-0.1, 0.05, 0.05], [0, Math.PI, 0]), K(1.2, [-0.1, 0.06, 0.07], [0.1, Math.PI, 0]),
    K(1.7, [0, 0, 0], [0, PI2, 0]),
  ] },
  // items that pop into your left hand for a moment (G): up from below, do the thing, drop away
  pop_popper: { keys: [
    K(0, [0.03, -0.3, 0.08], [0.9, 0, -0.3]), K(0.07, [0, 0, 0], [0, 0, 0], 'snap'),
    K(0.1, [0, 0.03, 0.09], [0.55, 0, -0.1], 'snap'), // yank
    K(0.24, [0, 0.01, 0.03], [0.18, 0, -0.04]), K(0.34, [0, 0, 0.02], [0.1, 0, 0]),
    K(0.5, [0.03, -0.32, 0.08], [0.9, 0, -0.3], 'in'),
  ], events: [[0.08, 'pop']] },
  pop_reverse: { keys: [ // flash it at the camera: grows, spins twice, drops
    K(0, [0, -0.3, 0.05], [0.8, 0, 0], 'smooth', 0.6), K(0.08, [0, 0, 0], [0, 0, 0], 'snap'),
    K(0.16, [0, 0.01, 0.02], [0, 0, 0], 'back', 1.45),
    K(0.5, [0, 0.01, 0.02], [0, PI2 * 2, 0], 'linear', 1.3), K(0.62, [0, 0, 0], [0, PI2 * 2, 0], 'smooth', 1),
    K(0.8, [0, -0.32, 0.05], [0.8, PI2 * 2, 0], 'in', 0.8),
  ], events: [[0.1, 'flash']] },
  pop_laptop: { keys: [ // up from below, shoved at them screen first, held there while it loads, dropped
    K(0, [0, -0.34, 0.06], [0.9, 0, 0], 'smooth', 0.7), K(0.1, [0, 0, 0], [0, 0, 0], 'snap'),
    K(0.18, [0.02, 0.03, -0.07], [-0.12, -0.06, 0], 'back', 1.1), K(0.7, [0.02, 0.025, -0.06], [-0.1, -0.05, 0.02], 'smooth', 1.1),
    K(0.9, [0, -0.36, 0.06], [0.9, 0, 0], 'in', 0.8),
  ], events: [[0.14, 'ads']] },
  dip_item: { keys: [K(0), K(0.1, [0.03, -0.08, 0.04], [-0.2, -0.15, -0.3]), K(0.38, [0.03, -0.07, 0.04], [-0.18, -0.15, -0.28]), K(0.55)] }, // the gun makes room
  inspect_chicken: { keys: [
    K(0), K(0.3, [-0.05, 0.05, 0.03], [0.1, 0.5, 0.2]),
    K(0.45, [-0.03, 0.06, 0.03], [0.1, 0.5, 0.45], 'snap'), K(0.6, [-0.05, 0.05, 0.03], [0.1, 0.5, 0.0], 'snap'),
    K(0.75, [-0.03, 0.06, 0.03], [0.1, 0.5, 0.45], 'snap'), K(1.3),
  ], events: [[0.45, 'squawk']] },
  inspect_blower: { keys: [
    K(0), K(0.3, [-0.04, 0.05, 0.02], [0.2, 0.3, 0.1]),
    K(0.5, [-0.03, 0.06, 0.02], [0.25, 0.3, 0.15], 'snap'), K(0.7, [-0.04, 0.05, 0.02], [0.2, 0.3, 0.1]),
    K(1.4),
  ], events: [[0.45, 'rev']] },
  inspect_shredder: { keys: [ // swing the intake round to look down it, blip the motor so the teeth spin in your face, swing back
    K(0), K(0.45, [-0.19, 0.1, -0.045], [-0.36, 2.84, 0.1]), K(0.66, [-0.19, 0.102, -0.045], [-0.33, 2.88, 0.12]),
    K(0.73, [-0.185, 0.112, -0.035], [-0.25, 2.84, 0.18], 'snap'), K(0.86, [-0.19, 0.1, -0.045], [-0.38, 2.9, 0.08]),
    K(1.2, [-0.19, 0.101, -0.045], [-0.35, 2.86, 0.11]), K(1.62, [-0.02, 0.015, 0.01], [-0.04, 0.2, 0.02]), K(1.85),
  ], events: [[0.64, 'rev'], [0.66, 'spin']] },
  draw_shredder: { keys: [ // hauled up heavy, then the motor catches: a jolt, a couple of shudders, settle
    K(0, [0.07, -0.4, 0.14], [-0.75, 0.3, 0.7]), K(0.3, [0, 0.02, 0], [0.1, 0, -0.05], 'snap'), K(0.44, [0.004, -0.004, 0.008], [-0.04, 0.01, 0.02]),
    K(0.52, [-0.006, 0.022, 0.016], [0.16, -0.05, -0.08], 'snap'), K(0.62, [0.004, -0.01, 0.004], [-0.07, 0.03, 0.05]),
    K(0.71, [-0.002, 0.007, 0.002], [0.05, -0.015, -0.03]), K(0.92),
  ], events: [[0.28, 'clunk'], [0.5, 'startup']] },
};

const SPECIAL = new Set(['katana', 'bread', 'slipper', 'spoon', 'revolver', 'shotgun', 'minigun', 'sniper', 'cig', 'duck', 'reverse', 'popper', 'chicken', 'blower', 'knife', 'slapper', 'scythe']);
SPECIAL.add('scales'); // on its own line so other new weapons can add theirs without touching the list
// weapon skins get their own inspect when they have one (butterfly flips, karambit spins...)
export function inspectFor(id, model) {
  if (model && ANIMS['inspect_' + model]) return 'inspect_' + model;
  if (id === 'scythe_rifle') return 'inspect_sniper';
  return SPECIAL.has(id) ? 'inspect_' + id : 'inspect_gun';
}
SPECIAL.add('shredder'); // inspect_shredder
for (const id of ['pistol', 'akimbo', 'sawnoff']) SPECIAL.add(id); // their inspects live in sidearms.js

// overdrive rig: the giant mechanical forearms that replace your guns (rigarms.js plays these). arm: which forearm the
// keys move ('both' = the two, mirrored). offsets are camera space, on top of the arms' rest pose
Object.assign(ANIMS, {
  rig_on: { arm: 'both', keys: [K(0, [0.12, -0.6, 0.3], [1.0, 0, 0]), K(0.34, [0, 0.035, 0], [-0.1, 0, 0], 'back'), K(0.55)], events: [[0.04, 'servo'], [0.3, 'clank']] },
  rig_off: { arm: 'both', keys: [K(0), K(0.45, [0.12, -0.65, 0.3], [1.0, 0, 0], 'in')], events: [[0.02, 'servo']] },
  // the rocket punch: from wherever the wind-up had it, snap all the way out to the middle, hold through the dash, back
  rig_punch: { arm: 'r', keys: [K(0), K(0.05, [-0.18, 0.05, -0.14], [-0.23, 0.05, -0.22], 'snap'), K(0.28, [-0.18, 0.05, -0.17], [-0.23, 0.05, -0.22]), K(0.55)] },
  // quickhack: a quick look at the wrist deck (it turns to face you), then back down
  rig_hack: { arm: 'l', keys: [K(0), K(0.13, [0.2, -0.04, -0.3], [0.78, -0.04, -0.18], 'snap'), K(0.48, [0.21, -0.03, -0.31], [0.8, -0.05, -0.19]), K(0.7)], events: [[0.1, 'beep']] },
  rig_miss: { arm: 'both', keys: [K(0), K(0.06, [0, -0.05, 0.05], [0.14, 0, 0], 'snap'), K(0.32)] }, // the rack kicks on your back
  rig_leap: { arm: 'both', keys: [K(0), K(0.08, [0.05, -0.14, 0.14], [0.55, 0, 0], 'snap'), K(0.5)] }, // arms thrown back off the jump
  rig_land: { arm: 'both', keys: [K(0), K(0.06, [0, -0.12, -0.02], [-0.32, 0, 0], 'snap'), K(0.38)] }, // slam down with the landing
  rig_jolt: { arm: 'both', keys: [K(0), K(0.04, [0, 0.025, 0.07], [-0.22, 0, 0], 'snap'), K(0.24)] }, // a blocked hit knocks the guard back
});

const RIFLE_IDS = ['burst', 'lmg', 'dmr', 'lever', 'autoshot']; // their inspects + draws live in rifles.js
for (const id of RIFLE_IDS) SPECIAL.add(id);
SPECIAL.add('bloodcross'); // the Blood Cross blows the blood off its fingertip, every skin
// what plays when you pull a weapon out
const HEAVY = new Set(['minigun', 'blower', 'bowling', 'chicken']);
export function drawFor(id, model) {
  if (model && ANIMS['draw_' + model]) return 'draw_' + model;
  if (RIFLE_IDS.includes(id) && ANIMS['draw_' + id]) return 'draw_' + id; // the rifle pack brings its own (rifles.js)
  if (ANIMS['draw_' + id]) return 'draw_' + id; // weapons with their own draw (the sidearms add theirs in sidearms.js)
  if (id === 'bloodcross') return 'draw_bloodcross';
  if (id === 'knife') return 'draw_knife';
  if (id === 'katana') return 'draw_katana';
  if (id === 'scythe') return 'draw_scythe';
  if (id === 'cards') return 'draw_cards';
  if (id === 'bow') return 'draw_bow';
  if (id === 'scales') return 'draw_scales';
  if (['bread', 'spoon', 'slapper', 'slipper', 'popper', 'duck', 'reverse', 'cig'].includes(id)) return 'draw_melee';
  if (id === 'shredder') return 'draw_shredder'; // up it comes, then the motor catches
  return HEAVY.has(id) ? 'draw_heavy' : 'draw_gun';
}

Object.assign(ANIMS, {
  // your swing got parried: whatever you're holding gets knocked up and away, then you get it back
  staggered: { keys: [
    K(0), K(0.07, [0.08, 0.12, 0.14], [0.75, -0.45, 0.65], 'snap'),
    K(0.32, [0.06, 0.08, 0.1], [0.55, -0.32, 0.45]), K(0.62),
  ] },
});

for (const a of Object.values(ANIMS)) a.dur = a.keys[a.keys.length - 1].t;

// returns { p, r, s } at time t, or null when finished
export function sample(name, t) {
  const a = ANIMS[name];
  if (!a || t >= a.dur) return null;
  const k = a.keys;
  let i = 0;
  while (i < k.length - 2 && t >= k[i + 1].t) i++;
  const k0 = k[i], k1 = k[i + 1];
  const u = Math.max(0, Math.min(1, (t - k0.t) / Math.max(1e-6, k1.t - k0.t)));
  const e = (EASE[k1.e] || EASE.smooth)(u);
  const L = (a0, a1) => a0 + (a1 - a0) * e;
  if (a.slerp) return { p: [L(k0.p[0], k1.p[0]), L(k0.p[1], k1.p[1]), L(k0.p[2], k1.p[2])], r: slerpR(a.slerp, k0.r, k1.r, e), s: L(k0.s, k1.s) };
  return {
    p: [L(k0.p[0], k1.p[0]), L(k0.p[1], k1.p[1]), L(k0.p[2], k1.p[2])],
    r: [L(k0.r[0], k1.r[0]), L(k0.r[1], k1.r[1]), L(k0.r[2], k1.r[2])],
    s: L(k0.s, k1.s),
  };
}

// anims with slerp: base euler (the katana): keys hold offsets from that base, but the turn between two keys goes the short
// way round as one rotation (big two-handed cuts would wobble through odd angles if each euler angle eased on its own)
function quatOf(x, y, z) { // euler XYZ -> quaternion [x, y, z, w]
  const c1 = Math.cos(x / 2), c2 = Math.cos(y / 2), c3 = Math.cos(z / 2), s1 = Math.sin(x / 2), s2 = Math.sin(y / 2), s3 = Math.sin(z / 2);
  return [s1 * c2 * c3 + c1 * s2 * s3, c1 * s2 * c3 - s1 * c2 * s3, c1 * c2 * s3 + s1 * s2 * c3, c1 * c2 * c3 - s1 * s2 * s3];
}
function eulerOf(q) { // quaternion -> euler XYZ (same as three.js)
  const [x, y, z, w] = q, m11 = 1 - 2 * (y * y + z * z), m12 = 2 * (x * y - z * w), m13 = 2 * (x * z + y * w), m22 = 1 - 2 * (x * x + z * z), m23 = 2 * (y * z - x * w), m32 = 2 * (y * z + x * w), m33 = 1 - 2 * (x * x + y * y);
  const ry = Math.asin(Math.max(-1, Math.min(1, m13)));
  if (Math.abs(m13) < 0.9999999) return [Math.atan2(-m23, m33), ry, Math.atan2(-m12, m11)];
  return [Math.atan2(m32, m22), ry, 0];
}
function slerpR(b, r0, r1, u) {
  const a = quatOf(b[0] + r0[0], b[1] + r0[1], b[2] + r0[2]), c = quatOf(b[0] + r1[0], b[1] + r1[1], b[2] + r1[2]);
  let d = a[0] * c[0] + a[1] * c[1] + a[2] * c[2] + a[3] * c[3];
  if (d < 0) { d = -d; for (let i = 0; i < 4; i++) c[i] = -c[i]; }
  let ka = 1 - u, kc = u;
  if (d < 0.9995) { const th = Math.acos(d), sn = Math.sin(th); ka = Math.sin((1 - u) * th) / sn; kc = Math.sin(u * th) / sn; }
  const q = [0, 1, 2, 3].map((i) => a[i] * ka + c[i] * kc), n = Math.hypot(...q);
  const e = eulerOf(q.map((v) => v / n));
  return [e[0] - b[0], e[1] - b[1], e[2] - b[2]];
}

// extra moving parts (butterfly handles, switchblade blade, karambit ring spin): [[t, ...values]], eased between keys
export function sampleCh(name, ch, t) {
  const a = ANIMS[name];
  const k = a && a.ch && a.ch[ch];
  if (!k) return null;
  if (t <= k[0][0]) return k[0].slice(1);
  if (t >= k[k.length - 1][0]) return k[k.length - 1].slice(1);
  let i = 0;
  while (i < k.length - 2 && t >= k[i + 1][0]) i++;
  const k0 = k[i], k1 = k[i + 1];
  const u = EASE.smooth(Math.max(0, Math.min(1, (t - k0[0]) / Math.max(1e-6, k1[0] - k0[0]))));
  return k0.slice(1).map((v, j) => v + (k1[j + 1] - v) * u);
}

// events crossed between t0 (exclusive) and t1 (inclusive)
export function eventsBetween(name, t0, t1) {
  const a = ANIMS[name];
  if (!a || !a.events) return [];
  return a.events.filter(([t]) => t > t0 && t <= t1).map(([, ev]) => ev);
}
