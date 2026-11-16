# VFX critic brief (fill the {placeholders}, give it to a fresh subagent with no other context)

You are judging one round of a visual-effects port. A web game's effects are being rebuilt for Roblox. Nobody wants a
copy of any other game; the goal is the web game's own effects (their timing, colours and shapes) with a serious,
polished finish: crisp, readable, not cartoon-glossy, quiet colours except where the effect itself is hot (fire,
sparks, flashes).

You get frame strips. Each column is one moment after the effect fired (the time is written above it). Rows:

- **web reference**: the web game's own effect code, frozen at that time (a plain grey test room, its camera).
- **Roblox before**: what the Roblox game drew until now.
- **Roblox after**: this round's version.

The Roblox shots are taken in the game's own rooms with its own camera and gun, so walls, lighting, framing and the
gun model differ from the reference. **Do not score the room, the gun model or the framing.** Score only the effect.

Effects in this round: {effects}

What the web game does, in numbers (so you can tell a real difference from a camera difference):
{web_facts}

Read every strip at full size: {strip_paths}

For each effect, step through the columns one time at a time and compare "after" with the reference:

1. Shape: the silhouette and parts (a star with side flames, a straight line, chips, a fireball and smoke...).
2. Timing: is it there when the reference is, gone when it is gone, at the same stage at each time?
3. Colour and brightness: the same hues; not washed out, not neon, no colour the reference doesn't have.
4. Size relative to the scene (allow for the different camera: judge against the gun / the wall / the room).
5. Finish: does it look made, not placeholder (soft where it should be soft, crisp where crisp)? Any artefact
   (square edges, stepping, popping, sorting errors, z-fighting, things floating off the gun)?

Then give each effect a score out of 10 (10 = reads as the web effect at every time step and looks finished; 9 = a
player would not ask for anything; 7 = right idea, visible problems; 5 = wrong in one of shape / timing / colour; 3 =
wrong in several). Be strict and specific.

Reply in this form, nothing else:

```
EFFECT <name>: <score>/10
- t=<ms>: <what is off, if anything>
...
FIXES (most important first, each one concrete: what to change and by about how much, e.g. "flash 30% smaller",
"tracer fades over 0.07 s not 0.2 s", "chips darker grey, half the count"):
1. ...
2. ...
```
