# Third person: every body handles its weapon

Asked for on 16 Nov 2026 ("can the character aim down gun outside of scopes in like in 3rd person animations for
weapons"). In third person (V), and for everyone watching you, your Roblox character now holds its weapon in both of
its own hands, aims it where you look, goes down the sights for every gun (scoped or not), kicks when it fires,
reloads with the off hand, swings and guards the katana, and throws or uses items with the left hand.

Code: `roblox/src/client/ThirdPerson.luau` (all of the pose, on every client), `roblox/src/server/ThirdPersonRelay.server.luau`
(the network), small hooks in `client/Arsenal.client.luau` and `client_root/CrouchPoses.client.luau`.

## How it works

Every frame, for every character holding a weapon (players, the training dummies, test rigs):

1. **The gun.** Each client builds its own copy of the held gun (`WeaponModels.build` with the same skin, wrap and
   hat as the server's `HeldWeapon`, which is hidden on that client) and welds it to the chest (`UpperTorso`) where the
   stance puts it. The copy is **sized to the avatar's arms**: `k = TP.T.scale x u` studs per metre of the gun's file,
   where `u` is that avatar's shoulder-to-wrist length (clamped 1.7 to 4.5). The server's `HeldWeapon` is built at 4.5
   studs a metre, which made a rifle longer than the owner's slim avatar is tall; no arm could reach its handguard.
   On a standard blocky body the copy is about 2.9 studs a metre, on the owner's slim one about 2.0.
2. **The chest.** The waist turns the chest into the stance (bladed for rifles, gun arm forward for pistols) and takes
   part of the look pitch (`waist`, 0.35 to 0.45); the walk animation's sway is taken out of the upper body so the gun
   stays steady. The neck takes the rest of the pitch, so the head looks where the gun points; while aiming the head
   tilts down onto the stock (`cheek`).
3. **Hip and aim (ADS).** At the hip the gun sits low and right of the face, pointing where you look. Aiming blends
   (same speed as first person) to the gun up at the right eye: its rear sight (`Sight` spot) a little in front of the
   eye, on the line of sight. Every gun has this, scoped or not.
4. **The hands.** The avatar's own hands (never a custom model) go on the hold table's grip spots
   (`tools/roblox/holds.json` -> `Holds.luau`, the same spots first person uses) through a two-bone IK solved from the
   avatar's own rig attachments: shoulder, elbow, wrist and the hand's `GripAttachment`. Each hand is turned about the
   handle until the wrist faces its elbow (the first-person rule), the elbows bend toward per-stance pole points. If a
   handguard is beyond an arm's reach, the hand slides back along the gun (at most 0.18 m of the file) until it is
   reachable. One-handed guns (Plan B, Revolver, Half a Shotgun) leave the left arm to the walk animation.
5. **Fire.** A kick per shot from the gun's own first-person recoil row (`recoilVM`, x `TP.T.kick`), on springs, about
   the grip; the slide, cylinder and hammer move (`GunParts.shot`); the pump, bolt and lever cycle after a shot.
6. **Reload.** The gun goes through its first-person reload clip (`Reloads.luau`), its moving pieces move (`GunParts`),
   and the off hand takes the magazine, the cylinder or the barrels out and back for the clip's window, or rides the
   pump. One-handed guns bring the left hand in for the reload only.
7. **Sprint.** Fast on the ground, not aiming, not just fired: the gun comes down across the body (`TP.T.low`).
8. **Katana.** Its own stance (both hands on the hilt, blade forward and up at the right hip), two alternating
   slashes (right to left, left to right), the guard (blade across in front of the face), the draw and the stagger
   when a swing is parried. Keys in `KAT` at the top of the module.
9. **Items.** The left hand throws (frag, smoke, duck, the calculator) on an arc with the item in the hand until the
   release, or holds the item up for a moment (medkit at the chest, goggles to the face, camera at the eye, radar
   forward, and so on). Driven by the server's `ItemFx` events, so everyone sees it.
10. **You in third person.** With a weapon out your body turns to face where you aim (first person already did), and
    the gun points at what the crosshair is on (a ray from the camera), not along the camera.

The pose runs after the walk animation and after the crouch and slide bends: `CrouchPoses` calls `TP.step(dt)` at the
end of its own pass (and the module runs its own pass if that call stops coming). Everything is written in the
chest's own space, so the hands land exactly whatever the chest does.

Roblox's `IKControl` was the first idea. It solves during the animation step, before the crouch poses and this pass
bend the spine, so its hands slid off the gun whenever the chest moved; this solve runs after, in chest space.

## The network

Your client sends `TPState(pitch, yaw, flags)`: where you look (degrees; yaw is the offset from your body's facing)
and two flags (1 = aiming, 2 = reloading, 4 = an empty reload). It sends when something changes, at most about 12
times a second (flags at once). `ThirdPersonRelay` checks the numbers (finite, clamped, at most 30 a second per
player) and puts them on your character as the attribute `TP` (Vector3: pitch, yaw, flags). Every other client
smooths it and poses your body. Shots (`Shot`), swings and guards (`Fx`) and items (`ItemFx`) already reached every
client and drive the kicks, slashes and throws.

## Tuning

All numbers are in `TP.T` at the top of `ThirdPerson.luau`. Distances are in the avatar's arm lengths (`u`), angles in
radians. Per stance (`rifle`, `heavy` = Belt Sander, `pistol`, `shredder`, `katana`): `twist` / `twistAds`, `waist`,
`ads` (rear sight from the right eye while aiming), `hip` and `hipRot` (the gun's move from there at the hip), `cheek`,
`poleR` / `poleL` (where the elbows point).

In a Play test, change any of it live through the module's `Tune` attribute (JSON merged into `TP.T`):

```lua
game.Players.LocalPlayer.PlayerScripts.Jankfire.ThirdPerson:SetAttribute("Tune", '{"rifle":{"hip":[0.14,-0.4,0.1]}}')
```

Then write the numbers back into the file.

## Testing (Studio)

Any model tagged `TPRig` with a `TPWeapon` attribute is posed like a player. Its state comes from the same `TP`
attribute a player's does, so it tests the other-player path. Extra test attributes:

- `TPFire`, `TPSwing`, `TPGuard`, `TPStagger`: change the number to fire / swing / guard / stagger once.
- `TPItem` = `"frag:throw"` or `"medkit:use"`: once.
- Frozen poses for photos: `TPKatPose` = `"swing:0.15"`, `TPClipPose` = `"reload_ar:0.6"`,
  `TPItemPose` = `"frag:throw:0.12"`.
- `TPDebug` = true: the gun carries `HandR` / `HandL` (where each hand was sent, chest space) to check the IK.
- `TPKat`: the katana's kill count on a rig.

`ReplicatedStorage.TPWide` (made by the test on the server from a default blocky HumanoidDescription) is the wide body.

## Results (16 Nov 2026, place version 389)

![every weapon held and aimed](third-person/all-weapons-sheet.jpg)

*Every weapon at the hip and aimed, on the owner's slim avatar (test bodies posed through the other-player path), then
three reloads, a frag throw and the medkit, then a wide blocky body.*

Measured in Play tests:

- **Hands land exactly.** Each hand's part ends within 0.000 to 0.010 studs and 0.0° of where it was sent, on all 16
  weapons, both bodies, hip and aim. A few targets are out of reach on purpose and the arm stops short (straight):
  the off hand chasing a dropped magazine on the slim avatar (AR 1.25 studs short at the bottom of the drop, SMG
  0.64), the Revolver's cylinder (0.09), the katana's left hand on the wide body (0.20).
- **Your own character, real keys and mouse (training room):** V gives third person; the local gun is built, the
  server's copy is hidden, your body turns to the camera. RMB: the `TP` attribute on the server read `(0, -1, 1)`
  (aiming). 11 shots fired (30 to 19) and R: `TP` read `(5, -2, 2)` (reloading) and the magazine left the gun.
  No errors in the output.
- **First person is unchanged:** the viewmodel, the hands and the HUD are as before; your own third-person copy is
  hidden while you are in first person.
- The dummies (Plinker, Stand, Dummy) hold their guns the same way, at a level look.

**"The gun is held backwards in third person" (reported 16 Nov, against place v360):** that came from Arsenal's old
arm pose (: it turned the shoulder joint, and on the owner's avatar the shoulders are AnimationConstraints,
so the server's gun swung round behind). This work removed that code (v389). Checked again on the owner's own avatar
in third person (place v397): the Assault Rifle points along the body (0.98 of straight ahead), muzzle 2.9 studs in
front, both hands exactly on; Plan B 0.85 (the rest is the aim's yaw toward the camera), muzzle in front; the
server's copy of the gun shows 0 visible parts.

**Later tweaks (place v397):** the Wood Chipper Shredder skin gets both hands through a fallback frame (handle to
muzzle) when it has no hub and chute; no goggles model in the hand (the items client already draws them on the head);
the calculator and the laptop are held facing the holder, as in first person; a real throw starts from the top of
the wind-up when the server's launch arrives, with no item in the hand (the thrown one is already flying); your own
Marble Shotgun shows your real marble count.

Known limits and ideas for later:

- The Redline's jerry can and the marble bag (first-person reload props) are not shown in third person; the off hand
  stays on the gun for those two reloads.
- The sprint lowering and the throw's item model in the hand are in the code but were not photographed.
- Third person keeps Roblox's Classic camera, so holding RMB to aim also turns the camera. An over-the-shoulder aim
  camera (offset right, mouse locked) would make aiming in third person feel like a shooter; that is a camera change,
  not part of this pose work.
- The `TPState` remote is made by `ThirdPersonRelay` when the server starts (it is not in `default.project.json`).
