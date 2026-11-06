# Third-person locomotion (loco.js)

`locomotion_before_after.mp4`: every motion, main on the left, this branch on the right (real time, 30 fps).
`sheet_<motion>.jpg`: 24-frame contact sheets, before on top, after below.
`killcam_ghosts.png`: killcam / play-of-the-round ghosts in a real bots match (same rig).

Motions: idle, walk 5, run 10, sprint 14.5, zoom 32, a ramp through all of them, strafe left / right, backpedal,
run + jump, bhop chain, fall from height + land, Plant & Defuse slow walk, crouch walk, sprint > slide, marbles slip,
a wrong-knee mannequin, grapple hang, knife and pistol (free left arm).

Foot slide (planted foot's ground speed, m/s; the lab's `slipm.cjs`): walk 7.06 -> 0.06, run 9.46 -> 0.13,
sprint 5.36 -> 0.17, backpedal 8.2 -> 0.73, strafe 5.1 -> 1.2, crouch 10.1 -> 0.29.
