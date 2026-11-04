# Review findings for the client side (30; some are the same bug reported by two reviewers: fix once)

## 1. [medium] Killstreak picks can be swapped mid-life, so one life can earn all 6 streaks
(id streak-swap-midlife, area client-ui, public/js/main.js:346)

**Problem:** The LOADOUT screen, which the pause menu opens, sends {t:'streaks'} as soon as you click, even while you are alive. server.js:1382 applies it at once (`p.streaks = validStreaks(m.list)`). kill() then checks the new picks against the current count (`killer.streak !== st.kills`). Weapons only change on respawn ('loadout switches when you respawn'), but streak picks change mid-life. A player can swap a pick just before each threshold and earn far more than the 3 streaks they picked. Earned streaks also stay in the pocket after death, so they stockpile.

**Failure:** Default picks are Moon Boots (3), Chicken Strike (4) and Scythe (5). After 5 kills the player has earned all three. They press B → LOADOUT → Spinbot (sent instantly) and resume, and the 6th kill earns Spinbot. They swap to Spy Satellite before kill 7 and Giant Duck before kill 10. That is all 6 streaks in one life (aimbot + wallhack + black hole) in the public room. A crafted client sending {t:'streaks',list:[...]} before each kill gets the same result without the menu.

**Suggested fix:** Server: store incoming picks as p.nextStreaks and apply them on respawn, or ignore 'streaks' while p.alive && p.streak > 0. Client: show 'killstreaks switch when you respawn' as the weapon loadout does, and keep the tray on the active picks until then.

**Verifier notes:** Fix it on the server. In 'streaks': `const l = validStreaks(m.list); if (!p.alive || !p.streak) { p.streaks = l; p.nextStreaks = null; } else p.nextStreaks = l;`. In kill(), where `t.streak = 0`, apply `if (t.nextStreaks) { t.streaks = t.nextStreaks; t.nextStreaks = null; }`. Do NOT apply pending picks in resetWorld/startRound: p.streak is not reset there (startRound only zeroes kills/deaths), so applying them there would reopen the hole across rounds. The 'ignore while alive && streak>0' variant on its own is incomplete. The dropped message is never resent (the client only sends 'streaks' on click), so server and client picks stay out of sync. Echo the active list back (e.g. {t:'streaks', list:p.streaks, pending:!!p.nextStreaks}) so the client keys the tray, deployStreak and the 'PRESS N' toast (main.js:1479 uses S.loadout.streaks) on the active picks, and show 'killstreaks switch when you respawn'.

## 2. [medium] Any cosmetic click in all-weapons mode calls setLoadout(S.loadout): randomizer loadout dropped, pending loadout applied mid-life
(id cosmetics-reset-loadout, area client-ui, public/js/main.js:388)

**Problem:** These all call setLoadout(S.loadout): setPartAll (every wrap/hat/effect chip click in the default 'every weapon' mode) and the RANDOMIZE, RESET and COPY THIS LOOK TO ALL buttons (lines 388, 617, 624, 631). The server-assigned randomizer loadout is thrown away while G.forcedLoadout stays set, so the UI still says the randomizer is on. Any pending loadout change is also applied mid-life, skipping applyLoadout's 'switches when you respawn' rule. Before this PR only the APPLY TO ALL button did this. Now it is the path for every cosmetic click, and the randomizer is new. The server does not enforce loadouts, so the client's weapons are what gets used.

**Failure:** Verified on a local server (port 4130). Bots room, mode Randomizer, saved loadout sniper/revolver/katana. Life 1 forced loadout: banana,snowball,slapper. Press B → COSMETICS → click an owned wrap. W.slots becomes sniper,revolver,katana while G.forcedLoadout is still banana,snowball,slapper, so the player plays Randomizer with their own guns. In any mode, picking a new primary in LOADOUT shows 'switches when you respawn', but clicking a wrap equips it immediately.

**Suggested fix:** Refresh the visuals without touching the loadout: replace `rebuildViewmodels(); setLoadout(S.loadout)` with `rebuildOne()` (rebuild viewmodels, re-show the current weapon, showSlots). At minimum use `setLoadout(G.forcedLoadout || <current slots>)`.

**Verifier notes:** The suggested fix is correct and complete. rebuildOne() (weapons.js) is rebuildViewmodels(), which re-applies the katana length and sets wrap.visible = id === W.cur, plus visibility and showSlots() for the new hotbar icons. Single-weapon setSkin() already uses it. Replace `rebuildViewmodels(); setLoadout(S.loadout)` with `rebuildOne()` at all four sites (setPartAll, skRandom all-mode, skReset all-mode, skAll). Avoid the setLoadout(G.forcedLoadout || ...) fallback. setLoadout also re-equips (cancels reload/ADS/animations), and for a forced loadout it resets W.item to 'frag'. Same pattern: loadTripoModels().then (main.js:84-90) calls setLoadout(G.settings.loadout) and would drop a forced loadout if the models finish loading after joining. Use rebuildOne() there too.

## 3. [medium] Killstreak picker can never drop Moon Boots or Chicken Strike: only the 3rd pick can be chosen
(id streak-picker-stuck, area client-ui, public/js/main.js:343)

**Problem:** Clicking an unpicked streak does `list = [...list.slice(0, 2), id]` on the kills-sorted picks, so it always keeps the two cheapest current picks. Clicks on picked streaks are refused with a toast. The default picks include the two cheapest streaks overall (Moon Boots 3, Chicken Strike 4), so they can never be removed. That contradicts 'players pick 3 in the loadout'.

**Failure:** I simulated every click sequence with the shared validStreaks (breadth-first search). From the default [moonboots, chickenstrike, scythe], only 4 of the 20 possible three-streak sets are reachable, all [moonboots, chickenstrike, X]. A player who wants Spinbot + Satellite + Giant Duck clicks Spinbot and gets [Moon Boots, Chicken Strike, Spinbot]. Clicking Satellite replaces Spinbot, and clicking Moon Boots only toasts 'you need 3 killstreaks'.

**Suggested fix:** Let a click on a picked streak deselect it and a click on an unpicked one fill the free slot, requiring 3 before leaving the screen. Or keep picks in click order and drop the oldest instead of the most expensive. validStreaks can still sort for the 5/6/7 key order.

**Verifier notes:** The direction is right, with one trap. validStreaks() pads any list shorter than 3 with the defaults (moonboots, chickenstrike first) and re-sorts by kills. So (a) a deselect must not be stored through validStreaks, or Moon Boots/Chicken Strike come straight back. (b) Click order is lost on every save and on reload (validLoadout sorts at startup), so 'drop the oldest' needs its own stored order. Simplest correct version: keep a UI-only draft. A click on a picked streak removes it from the draft (2 picks, nothing saved or sent). A click on an unpicked one when the draft has 2 adds it and commits S.loadout.streaks = validStreaks(draft) and sends 'streaks'. A click on an unpicked one when 3 are picked toasts 'click one of your picks to drop it first'. All 20 sets are then reachable in at most 2 clicks, and the server only ever sees 3-sets.

## 4. [medium] Item charges and frozen state desync: client resets on every 'spawn' (server doesn't on round resets) and not on 'welcome' (server does)
(id item-charges-desync, area client-ui, public/js/main.js:1082)

**Problem:** The client treats every 'spawn' as a fresh life (`resetItems(); ME.frozenUntil = 0; G.frost = 0`). The server's resetWorld (server.js:1325-1334) runs on every round start, every Plant & Defuse round and every map change. It sends 'spawn' but does not reset p.ic, p.frozenUntil or p.frost; only the death-respawn path in tick() resets them. The welcome handler never calls resetItems(), so charges spent in one room carry into the next even though the server starts you with full charges. The server sends no 'ic' when it rejects a use, so the client stays wrong.

**Failure:** Verified. (1) Throw both frags (HUD x0), then a map change starts a new round and sends 'spawn': the HUD shows x2. Press G: the client sends 'item', the server rejects it (n=0, no frag), and the HUD drops to x1 with a fresh 16 s timer. (2) Throw both frags in Training, quit, join another room: the HUD shows x0 and G sends nothing for up to 16-28 s, though the server would allow it. (3) A player frozen when a round resets can walk away because the client cleared frozenUntil, but the server still thinks they are frozen, so the next snowball shatters (kills) them.

**Suggested fix:** Server: make resetWorld reset per-life state like the respawn path (p.ic = {}, frozenUntil, frost, healLeft), or send an 'ic' sync for the item. Client: call resetItems() and clear G.frost / ME.frozenUntil in the welcome handler. Better still, the server answers a rejected 'item' with the real {t:'ic'} state.

**Verifier notes:** Server: in resetWorld reset the same per-life fields the tick() respawn path resets (p.ic = {}, frozenUntil = 0, frost = 0, healLeft = 0, and the slip/burn/sleep timers), matching the client's 'spawn' semantics. Client: call resetItems() in resetWorldState() or the welcome handler. resetWorldState already clears ME.frozenUntil and G.frost, so only resetItems is missing. Also, in useItem, answer a rejection with the real `{t:'ic', i, n, next}` so any leftover desync heals itself. Caveat: once resetWorld refills items, any player's map change in MATCH SETTINGS (allowed in the public room) also refills everyone's items. If that matters, send 'ic' syncs right after the 'spawn' instead of resetting. Related server-trust gap: useItem accepts any m.i, so a crafted client can use all five items, not just its loadout item.

## 5. [medium] Client item charges drift from the server after match/bomb-round resets and after changing rooms
(id item-charges-desync, area client-3d, public/js/weapons.js:244)

**Problem:** The client keeps its own copy of item charges in W.ic and only corrects it when a use succeeds (the server's 'ic' message). Two paths break that. (1) main.js:1082 calls resetItems() on every 'spawn' message. The server only resets p.ic = {} in the death-respawn tick (server.js:1703). resetWorld() (server.js:1325) also sends 'spawn' but never touches p.ic, and it runs on every match start (startRound), every Plant & Defuse round (newBombRound) and every map change. After those the client thinks it has full charges and the server does not. (2) The 'welcome' handler never calls resetItems(), but joining a room creates a fresh server player with full charges, so the client stays at its old count. In both cases the server drops the rejected 'item' silently (it sends no 'ic'), so the client never finds out.

**Failure:** Reproduced on port 4140. Case (b): in a Bots room throw both frags (server sends ic:1, ic:0). Change the map, which runs resetWorld and sends 'spawn'; the client now shows x2. Press G: the toss animation and sound play, the HUD drops to x1 and 'item' is sent, but the server sends nothing back (no 'ps', no 'ic') and no grenade appears. In Bomb mode this happens every round. Case (a): throw both frags in Training, quit, join Training again. W.ic.frag.n is still 0, so G only shows 'Frag Grenade: recharging' and sends nothing, although the new server player has 2 charges.

**Suggested fix:** Make both sides reset at the same moments. Either reset p.ic (and frost/frozenUntil) in resetWorld(), or stop calling resetItems() for resetWorld spawns (for example with a flag in the spawn message). Call resetItems() in the 'welcome' handler. Have the server reply with an 'ic' carrying the real count when it rejects a use, so the client can correct itself.

**Verifier notes:** Preferred fix: in resetWorld's player loop, add `p.ic = {}; p.frost = 0; p.frozenUntil = 0; p.healLeft = 0; p.slipUntil = 0; p.sleepUntil = 0; p.burnUntil = 0;`. This mirrors the respawn tick and the client's 'spawn' handler, which also clears ME.frozenUntil, slipUntil and sleepUntil. It covers startRound, newBombRound and map changes, since all of them go through resetWorld. A flag in the spawn message alone would fix case (b) but not case (a). Also call resetItems() in the 'welcome' handler or in resetWorldState(). As a safety net, when useItem rejects a valid item for c.n <= 0 or the 400 ms spam limit, reply with {t:'ic', i, n:c.n, next}. The client's optimistic decrement then gets undone.

## 6. [medium] Team colour is lost on any player who picked clothing colours
(id team-colour-clothes, area client-3d, public/js/models.js:848)

**Problem:** buildCharacter now paints the sash/tee/hoodie/jacket/sleeves with lk.topColor and the shorts/pants/skirt with lk.bottomColor. It falls back to `c` (the colour passed in) only when those fields are ''. In team games the 'teams' handler calls r.setLook(r.outfit, teamColour), so the team colour arrives only as `c` and any custom clothing colour wins. That leaves no team colour on the body; only the thin outline shell and the name tag still show it. CLOTH_COLORS even includes '#ff4f4f', which is exactly RED's team colour. The spec says team colours override player colours.

**Failure:** Measured with buildCharacter: a RED team player in #4fd8ff top and pants has 0 of 33 body meshes in team colour. A BLUE team player in #ff4f4f hoodie and pants has 0 of 39 meshes in blue, and their whole body is RED's colour. In TDM, Tags or Bomb, enemies dressed in your team's colour read as teammates (friendly fire is off, so players hold fire), and killcam ghosts show the same.

**Suggested fix:** When the remote is on a team, ignore topColor/bottomColor (pass a team flag into buildCharacter, or have setLook build with a look whose clothing colours are cleared), or at least tint the clothes with the team colour.

**Verifier notes:** The direction is right, but every build path needs it. (1) main.js:884-885 sets r.team only after the constructor has already called build(). Pass the team into the Remote constructor and, in build(), use `this.team ? { ...this.outfit, topColor: '', bottomColor: '' } : this.outfit`. The 'teams' handler sets r.team before setLook, so it then rebuilds correctly, including the restore when teams turn off. (2) Replay ghosts (replay.js:50) and kill effects (killfx.js:21 buildCharacter(c.color, c.look)) get no team information. Add team to infoOf (main.js:1520) and to the server clip info (server.js:869), or strip clothing colours whenever the colour is TEAMS[1].color or TEAMS[2].color. Related gap: the server 'look' handler (server.js:1404-1409) sets p.color = p.look.color even when teamsOn(). A mid-match look change therefore drops the team colour from the outline, tag and marker too. Keep TEAMS[p.team].color when p.team is set.

## 7. [low] Holding F to plant/defuse then losing window focus roots the player in place
(id use-stuck-on-blur, area client-ui, public/js/main.js:731)

**Problem:** Holding F sets G.using. That blocks all movement input (frame(): `playing = ... && !G.using`) and keeps a 200 ms 'use' interval running. Only an F keyup or death clears it. The window 'blur' handler clears keys, fire and aim but not G.using. A keyup that happens while the window has no focus never reaches the page.

**Failure:** Verified on Bazaar (Bots, Plant & Defuse). The carrier stands in site A, holds F, then alt-tabs (window blur). 'use' keeps being sent and the plant completes while they are away. Back in the game, holding W for 1.5 s moves them 0.00 m. They stay rooted, an easy kill, until they press and release F again or die. This is easy to hit in the desktop app (overlays, notifications, alt-tab).

**Suggested fix:** Call stopUse() in the 'blur' handler, and also in pause() and on pointer-lock loss. Optionally stop the interval when !keys.KeyF.

**Verifier notes:** Call stopUse() in the 'blur' handler and in pause(). Pointer-lock loss already goes through pause(). The most robust single change is in the interval: `if (!G.using || !ME.alive || !keys.KeyF) { stopUse(); return; }`. blur, pause() and openChat() all clear keys, and keys.KeyF is set at the end of the F keydown before the first tick, so every path is covered.

## 8. [low] Frost screen overlay never fades: G.frost is never decayed client-side
(id frost-overlay-never-decays, area client-ui, public/js/main.js:1309)

**Problem:** Only 'frost' messages set G.frost (line 955), and only freeze, spawn or quit clear it. The server decays frost by one stack per 3 s but never tells the client. The frozen vignette (#freezeFx opacity = frost*0.15) therefore stays on screen for the rest of the life, including the death screen and killcam.

**Failure:** Verified by injecting {t:'frost', n:3}: #freezeFx opacity was 0.45 right away and still 0.45 ten seconds later, when the server's frost is back to 0. A player hit by 3 snowballs who survives plays the rest of that life behind a 45% frost vignette.

**Suggested fix:** Record when the last 'frost' message arrived and decay G.frost client-side by one stack per WEAPONS.snowball.frostDecay seconds, as the server does. Or have the server send a frost update when it decays.

**Verifier notes:** Mirror the server formula. In net.on('frost') store G.frostT = performance.now(). In frame() use `const fr = Math.max(0, (G.frost || 0) - Math.floor((now - (G.frostT || 0)) / (WEAPONS.snowball.frostDecay * 1000)))` for the opacity. Also clear G.frost in the 'kill' handler when you are the victim.

## 9. [low] Vote countdown jumps back to 14s whenever anyone votes; vote keys auto-repeat
(id vote-countdown-resets, area client-ui, public/js/main.js:979)

**Problem:** showVote() recomputes `G.voteEnds = now + v.left` every time it re-renders. 'votes' updates (line 994) and your own castVote (line 992) re-render with the original vote object, whose `left` is from when the vote opened, so the timer restarts at the full duration. The vote key branch (line 675) also has no e.repeat guard. Holding 1/2/3 sends a vote on every key auto-repeat, and the server broadcasts 'votes' to everyone each time.

**Failure:** Verified: the vote opens with left=14000 and the panel shows 8s after 6 s. A 'votes' update arrives and the panel shows 14s, though only about 8 s of voting remain. A player holding '2' sends about 30 votes/s, each broadcast to every client, which keeps everyone's countdown stuck at 14s.

**Suggested fix:** Set G.voteEnds only when a new vote arrives (the 'vote' handler and welcome), not inside showVote. Add `!e.repeat` to the vote key check, and rate-limit 'vote' on the server.

**Verifier notes:** Set G.voteEnds only in net.on('vote') and in the welcome handler (from m.vote.left), not inside showVote. Add !e.repeat to the vote key check. Server: skip the broadcast when the vote did not change (`if (this.vote.votes.get(p.id) === m.i) break;`) and add a small per-player rate limit. That removes the broadcast amplification a crafted client can trigger whatever the client does.

## 10. [low] Duplicate id 'speedLines' makes the speed-lines setting checkbox dead
(id speedlines-duplicate-id, area client-ui, public/index.html:273)

**Problem:** The HUD canvas (index.html:21) and the settings checkbox (index.html:273) both use id="speedLines". getElementById returns the canvas, so bindCheck('speedLines') (main.js:290) and applySettingsToUI (main.js:1666) set .checked and the change listener on the canvas instead of the checkbox.

**Failure:** Verified: SETTINGS shows the box unchecked while speed lines are on. Clicking it leaves G.settings.speedLines = true. There is no way to turn speed lines (and the arrow/card streaks) off from the menu, which matters for motion-sensitive players.

**Suggested fix:** Rename the checkbox (for example id="speedLinesOn") and use that id in bindCheck and applySettingsToUI.

**Verifier notes:** If you rename the checkbox, also change applySettingsToUI, whose loop uses the element id as the settings key (`$(id).checked = !!S[id]`). Use bindCheck('speedLinesOn', 'speedLines') and `$('speedLinesOn').checked = !!S.speedLines`. Simpler: rename the canvas instead (index.html:21, speedlines.js:10, and the two #speedLines rules at style.css:284-285) and leave bindCheck and applySettingsToUI as they are.

## 11. [low] Killstreak tray progress (x/y) and 'streak N' text are wrong between thresholds
(id streak-tray-stale, area client-ui, public/js/main.js:1447)

**Problem:** The new tray shows `min(n, kills)/kills` for each pick and a 'streak N' line, both from G.streakN. G.streakN only changes on {t:'streak', earned} messages and on reset (line 1477). The server sends 'earned' only when the count exactly matches one of your 3 picks (server.js:810), so the counter is stale most of the time.

**Failure:** Default picks 3/4/5: after kills 1 and 2 the tray still shows 0/3, 0/4, 0/5 and no streak text. With Moon Boots / Chicken Strike / Giant Duck, kills 5 to 9 show Giant Duck stuck at 4/10 and 'streak 4'.

**Suggested fix:** Have the server send {t:'streak', n} on every kill, or add the streak count to the snapshot row. Update G.streakN and call renderStreak from it.

**Verifier notes:** Server: in kill(), after `killer.streak++`, send(killer, {t:'streak', n: killer.streak}) for human killers. Client: the 'streak' handler needs a branch for that shape before the reward branch. Today a message with neither reset nor earned falls through to `STREAKS[m.reward]` and returns. Add `if (m.n != null && !m.earned && !m.reward) { G.streakN = m.n; renderStreak(m.n); return; }`. Putting the streak count in the snapshot row also works.

## 12. [low] Shield bubbles that are up when you join are never shown (welcome.bubbles ignored)
(id bubbles-missing-on-join, area client-ui, public/js/main.js:795)

**Problem:** The server's welcome message lists the live bubbles (`bubbles: [{id,p,r,left}]`, server.js:307). The welcome handler restores tags, katana lengths and the vote, but never calls addBubble for the bubbles.

**Failure:** Verified: a second client drops a shield bubble in the Online room and the browser joins 0.3 s later. G.bubbles.size is 0. For up to 7 s the joiner sees no dome and shoots at players who cannot be hurt, getting only 'bubhit' sparks.

**Suggested fix:** In the welcome handler, remove any stale bubble meshes and then run `for (const b of m.bubbles || []) addBubble(b)`.

**Verifier notes:** In the welcome handler add `for (const b of m.bubbles || []) addBubble(b);`. The payload already has {id,p,r,left}, and addBubble uses left. resetWorldState() already removes stale bubble meshes on quit or disconnect, so no extra cleanup is needed.

## 13. [low] Plant & Defuse is offered for maps without bomb sites and silently falls back to Deathmatch
(id bomb-on-siteless-map, area client-ui, public/js/main.js:229)

**Problem:** The BOTS setup and MATCH SETTINGS mode selects (lines 229-231, 240) offer every game on every map, but only Bazaar has bomb sites. The server's setGame refuses 'bomb' on other maps and keeps Deathmatch with no message. The client gives no feedback, and the match-settings select keeps showing Plant & Defuse.

**Failure:** Verified: BOTS → mode Plant & Defuse, map left at the default Islands → GO. The match is dm, labelled 'Bots · Islands', with no teams, no bomb and no explanation. In MATCH SETTINGS, choosing Plant & Defuse on Crate does nothing and the select still reads Plant & Defuse.

**Suggested fix:** When Plant & Defuse is selected, limit or switch the map select to maps with sites (mapsFor from shared/modes.js), or show a toast. Resync cfgGame from G.round.game after the server's 'round'/'cfg' reply.

**Verifier notes:** The server sends nothing back when it refuses, so 'resync after the server reply' never fires. The client must handle it itself. When Plant & Defuse is selected, limit or switch the map select to mapsFor('bomb', MAPS, MAP_ORDER) on the setup screen. In MATCH SETTINGS, if the current map has no sites, revert cfgGame to G.round.game with a toast. Server: have setCfg send a chat line or toast when setGame refuses, and have addHuman switch to a bomb map instead of silently falling back to Deathmatch.

## 14. [low] Frozen players can still grapple or glitch-dash
(id frozen-can-grapple, area client-ui, public/js/main.js:674)

**Problem:** Being frozen only zeroes horizontal velocity once per frame and blocks WASD/jump (lines 1248-1250). The freeze handler releases the hook, which shows that intent, but tryHook (E, mouse buttons 4/5, right-click with swapAim) and the scythe dash (V) are not blocked. hookStep and the dash branch of stepPlayer set velocity inside every sub-step, so the player still moves.

**Failure:** Verified in Training. Frozen without a hook: moved 0.00 m in 1.5 s. Frozen, then E on a dummy 63 m away: moved 1.92 m in 1.5 s, and the vertical pull is not zeroed at all. With the Scythe Rifle, holding V dashes at the full 38 m/s while frozen.

**Suggested fix:** While performance.now() < ME.frozenUntil, ignore tryHook and dash input and release any hook each frame.

**Verifier notes:** Gate the dash where it is computed: add a !frozen check to the dashing condition in updateWeapons. That also stops the dash 'hit' messages, which a velocity-only fix in frame() would miss. Return early from tryHook while performance.now() < ME.frozenUntil, which covers every input path. While frozen, also call releaseHook() each frame. The sleep arrow (ME.sleepUntil) has the same gap and can share the guard.

## 15. [low] Animated weapon hats (propeller, halo, googly eyes) keep every discarded weapon in memory forever
(id ticking-hat-retention, area client-3d, public/js/skins.js:348)

**Problem:** makeHat puts hats that animate into liveHats. skinTick only removes one when `!h.parent`. A discarded weapon is detached from the scene but still owns its hat (hat.parent is the weapon group), so the hat and the whole weapon model stay referenced forever and are walked by inScene() every frame. The mechanism predates the PR, but the PR makes it hit far more often: hats now apply to every weapon, each cosmetics click rebuilds all ~31 viewmodels (rebuildViewmodels), the hotbar renders extra hatted weapons through icons.js weaponIcon (its cache is cleared on every rebuild), and Remote.setWeapon builds a new hatted weapon every time another player switches weapons.

**Failure:** Measured after GC with --enable-precise-memory-info. 30 rebuildViewmodels with a propeller hat on all weapons: +43 MB retained, versus +3 MB with a top hat. Another player with a propeller hat switching weapons 300 times: +17.2 MB retained, versus +1.2 MB with a top hat (about 57 KB per switch). A lobby with a few propeller-hat players over a multi-hour session grows by hundreds of MB, and the per-frame liveHats walk grows with it.

**Suggested fix:** In skinTick, drop any hat that is not in a scene, whatever its parent (or unregister hats when their weapon is removed or rebuilt). Also dispose the discarded weapon's geometries in Remote.setWeapon, rebuildViewmodels and weaponIcon.

**Verifier notes:** `if (!inScene(h)) { liveHats.delete(h); continue; }` is safe for the current callers. Every buildWeapon caller attaches synchronously before the next frame: weapons.js:339 into vmRoot in G.vmScene; remote.js:115 after build() has added the root to G.scene; preview.js:39 into the preview scene; icons.js renders once and never needs ticking. Hidden viewmodels stay in G.vmScene. Optionally also dispose the discarded weapon's geometries in setWeapon, rebuildViewmodels and weaponIcon. Never dispose the shared M(), visibleMat(), HM() or finish materials, or cached textures.

## 16. [low] Rebuilt or discarded characters (team re-colour, killcam ghosts, ice block) never free GPU geometries or name-tag textures
(id character-rebuild-gpu-leak, area client-3d, public/js/remote.js:97)

**Problem:** setLook() calls build(), which creates a whole new character: every bx/ball/limb/cylZ part gets a new geometry, plus a new name-tag CanvasTexture, SpriteMaterial and card mesh. The old root is only removed from the scene, never disposed, and dispose() does the same. The new ice block (BoxGeometry plus MeshBasicMaterial) is also dropped without dispose on setLook and dispose. This PR adds a frequent trigger: the 'teams' handler calls r.setLook for every remote whose colour changed, which is every match start in team games. It also makes characters heavier (hair, jackets, sleeves, pants). Killcam and highlight ghosts (replay.js playClip/stopReplay) go through the same build and dispose for every player in the clip on every death. three r170 keeps undisposed geometries in WebGLBindingStates, so they are never released.

**Failure:** Measured with renderer.info.memory in Training. Ten team re-colours of 8 remotes (what 'teams' does) took geometries from 462 to 5582 (+64 per rebuilt character) and textures +80 (one name tag each). Five short replays with 9 ghosts each: +2610 geometries, +40 textures. A few hours of TDM with killcams keeps tens of thousands of geometries and hundreds of 128x32 textures on the GPU.

**Suggested fix:** In Remote.dispose(), and before rebuilding in setLook()/build(), walk the old root and dispose geometries (not the shared cached M()/visibleMat materials), the name-tag texture and SpriteMaterial, the card material, and the ice geometry and material. Call that from stopReplay for ghosts. On a team change, consider recolouring the outline and tag instead of rebuilding.

**Verifier notes:** Add a helper that disposes the old ch.root: its geometries (shells share the body geometry, and a double dispose is harmless), the tag texture and SpriteMaterial, the marker SpriteMaterial (not the shared markerTexture()), the card geometry and material (not the shared cardTex()), the ice geometry and material, and the weapon geometries. Call it in build() before rebuilding and in dispose(). stopReplay already calls g.dispose() for ghosts, so no extra call is needed there. Caveat: breakApart gibs reuse the body geometries (remote.js:168) and live about 5 s in G.gibs. Disposing while gibs are flying makes three re-upload those geometries, and they then leak again. Clone the geometry per gib and dispose it when the gib expires (updateGibs, resetWorldState), or defer the disposal. killfx.js characters (buildCharacter at :21, removed at :221 and :225) leak the same way. Recolouring shells, marker and tag on a team change avoids rebuilds, but it conflicts with the team-colour-clothes fix, which needs the clothes recoloured.

## 17. [low] Cape swings forward through the body instead of streaming out behind
(id cape-swings-forward, area client-3d, public/js/remote.js:228)

**Problem:** The cape hangs down (-y) from a pivot on the back (+z); the character faces -z. A positive rotation.x moves the bottom edge toward -z, which is forward. The rest pose (models.js:805, 0.1) and the speed target (0.1 + up to 1.15 + flutter) are both positive, so the faster a player moves, the further the cape swings forward through the torso and legs.

**Failure:** Measured with buildCharacter plus a side-view render. At rotation 0.38 (running at about 8 m/s) the cape's bottom edge is at z = -0.21, in front of the body centre. At 1.25 (33 m/s or more, common with bhop or grapple) it sits at z = -0.77, y = 1.2, sticking out of the chest past the gun hand (gun slot z = -0.56). Every caped player who moves shows this, including killcam ghosts.

**Suggested fix:** Flip the sign: piv.rotation.x = -0.1, and in Remote.update ease rotation.x toward -(0.1 + Math.min(1.15, hs * 0.035) + flutter).

**Verifier notes:** The suggested sign flip is correct and complete. Set piv.rotation.x = -0.1 at models.js:805. At remote.js:228 use tgt = -(0.1 + Math.min(1.15, hs * 0.035) + (hs > 2 ? Math.sin(now * 0.014) * 0.07 : 0)). Remotes, replay ghosts and the static preview pose all go through these two lines.

## 18. [low] ADS height clamp for guns without sights measures in the wrong space and never lowers the gun
(id ads-clamp-wrong-space, area client-3d, public/js/weapons.js:227)

**Problem:** adsPose resets g's own position and rotation, but o.matrixWorld still includes the wrap and vmRoot transforms (the wrap sits about 0.2 below centre) and g's scale, and the result is then multiplied by s again. box.max.y therefore comes out about 0.2 too low, so `Math.min(w.ads.p[1], -0.03 - box.max.y * s)` always returns ads.p[1]. The 'keep the whole thing under the middle of the screen' clamp never takes effect.

**Failure:** Turkey Launcher skin (chicken_turkey): the gun's own top is y = 0.263, so the intended ADS y is -0.201, but the actual wrap y is -0.15. At full ADS its tail-feather fan reaches NDC y +0.056, above the crosshair, and covers the right and lower part of the screen while aiming (screenshot shots/ads_chicken_chicken_turkey.png; the default chicken is a slim tube below centre).

**Suggested fix:** Measure the box in g's local space: use each mesh's matrix relative to g, i.e. inverse(g.matrixWorld) x o.matrixWorld with g at identity. Then multiply by s once and add no wrap offset.

**Verifier notes:** After g.updateMatrixWorld(true), use inv = g.matrixWorld.clone().invert() and union bbox.applyMatrix4(tmp.multiplyMatrices(inv, o.matrixWorld)). That removes the wrap, vmRoot and g scale, so you multiply by s exactly once, and the result no longer depends on the wrap pose at the first ADS. Also exclude every mesh under g.userData.hat. The current check skips only the hat's direct children, so propeller blades, which are grandchildren inside the prop group, would count once the box is in local space. The hat is hidden while aiming anyway.

## 19. [low] The 'speed lines' setting cannot be turned off because two elements share the id
(id speedlines-toggle-dead, area client-3d, public/index.html:273)

**Problem:** The PR added both <canvas id="speedLines"> (line 21, used by speedlines.js) and <input type="checkbox" id="speedLines">. getElementById returns the canvas, so bindCheck('speedLines', 'speedLines') (main.js:290) and the settings sync at main.js:1666 set .checked on the canvas and attach the change listener to it, not to the checkbox.

**Failure:** Verified: G.settings.speedLines is true but the checkbox renders unchecked. Clicking it only toggles the box; G.settings.speedLines stays true and nothing is saved. updateSpeedLines(..., S.speedLines !== false) and the bow/card streak tracers can never be disabled.

**Suggested fix:** Rename one id (for example the canvas to 'speedLinesCv' in index.html, style.css and speedlines.js).

**Verifier notes:** Rename the canvas as suggested (index.html:21, style.css:284-285, speedlines.js:10). That is complete. Renaming the checkbox instead would also require changing main.js:290 and the loop at main.js:1666, which uses the setting key as the element id.

## 20. [low] Randomizer mode replaces the player's item with a frag grenade every life
(id randomizer-forces-frag, area client-3d, public/js/weapons.js:392)

**Problem:** The server's randomLoadout() sends only primary, secondary and melee. setLoadout(m.lo) runs validLoadout, which fills item with DEFAULT_LOADOUT.item ('frag'), and `W.item = v.item` overwrites the player's chosen item. The server uses whatever item id the client sends, so frags are what get thrown. The item is neither the player's choice nor random.

**Failure:** Verified: with loadout item 'medkit', join a Bots room in Randomizer. G.forcedLoadout = {primary: chicken, secondary: cards, melee: slapper} and W.item = 'frag'. The hotbar shows the frag and G throws frags for the whole match.

**Suggested fix:** In setLoadout, keep the player's own validated item when lo has no item, or have randomLoadout include a random item.

**Verifier notes:** Option 1, keep the player's own item: at main.js:999 call setLoadout(m.lo ? { ...m.lo, item: S.loadout.item } : S.loadout), or have setLoadout keep W.item when lo.item is not a valid ITEMS id. Option 2, randomize it: add lo.item = pick(ITEM_ORDER) in randomLoadout() and show it in the HUD message. Either is complete. Leaving the randomizer already restores S.loadout through lo:null.

## 21. [low] A frozen player killed by anything except a snowball respawns still inside the ice block
(id ice-after-respawn, area client-3d, public/js/remote.js:219)

**Problem:** Remote.frozenUntil is cleared only by the 'shatter' fx. Neither the 'kill' handler nor a respawn (snap() seeing alive go from false to true) clears it, while the server zeroes frozenUntil on respawn. The respawned remote keeps the ice block and its legs stay locked (walk is cancelled) until the old timer runs out.

**Failure:** Verified in Training: freeze a dummy with 4 snowballs, then kill it with the spoon. It respawns 0.7 s later and is drawn inside the ice block (307 ms still left in that run; up to about 1.7 s is possible). Humans who skip the killcam respawn after 1.5 s, so a kill within 0.9 s of the freeze shows the same.

**Suggested fix:** Clear frozenUntil for the victim in the 'kill' handler, or in Remote.snap() when alive goes false to true.

**Verifier notes:** Clear it in Remote.snap when alive goes from false to true: if (alive && !this.alive) { this.buf.length = 0; this.frozenUntil = 0; }. That covers every death cause and replay ghosts. Optionally also zero victim.frozenUntil in the 'kill' handler.

## 22. [low] Killcam and highlight ghosts always show a base-length katana (and are never shown frozen)
(id ghost-katana-length, area client-3d, public/js/replay.js:50)

**Problem:** Ghost Remotes are built from clip.info (name, color, skins, look, from main.js infoOf and server.js:869), which carries no katana kill count, and nothing calls setKat on them. setWeapon('katana') therefore applies length 0. The recorded events (REC_T / recordEv) don't include 'kat' or 'freeze', so frozen state never appears in replays either.

**Failure:** You are killed from 7.8 m by a player with a 10-kill katana (reach 2.8 + 10 x 0.5). The killcam shows them swinging a normal 1.3 m blade at you from across the room. The end-of-match highlight shows the same.

**Suggested fix:** Add kat (and frozenUntil) to infoOf and to the server's clip info, or record 'kat' events, and call g.setKat(info.kat) when creating ghosts.

**Verifier notes:** Add kat to infoOf (kat: id === G.myId ? (W.kat || 0) : (G.kat.get(id) || 0)) and to the server clip info (kat: pl.kat || 0). Right after constructing each ghost, set g.katN = i.kat || 0. setWeapon happens later in snap, so that is enough; g.setKat also works. This is the count when the clip is taken, so it can be one too high after a katana kill. For exactness, record 'kat' (server REC_T and client recordEv) and apply g.setKat(m.n) in applyEv. For frozen state, record 'freeze' and the 'shatter' fx (REC_FX and client recordEv) and set g.frozenUntil in applyEv. Remote.update compares frozenUntil with performance.now while replays can run at 0.3x, so that duration must be scaled or moved to a replay clock.

## 23. [low] window.jf IPC is callable from any remote page (JOIN address): it can start a LAN-listening server and force persisted fullscreen
(id desktop-ipc-any-origin, area maps-desktop, desktop/main.cjs:108)

**Problem:** preload.cjs exposes window.jf to every page the window loads: the file:// launcher, https://jankfire.onrender.com (now the default PLAY ONLINE target via config.json), and any address typed into JOIN or picked from 'recent'. None of the ipcMain handlers check e.senderFrame.url. A hostile server page can call: jf.host(), which imports server.js inside the app; it listens on all interfaces (server.listen(PORT) with no host) and keeps a LAN-reachable game and account server running until quit. jf.info(), which returns the LAN addresses and port while hosting. jf.join() with any http(s) URL, and jf.quit(). And the new jf.display('fullscreen'), which goes fullscreen with no user gesture and no browser 'press Esc' overlay, and writes it to userData/display.json so the next launch starts fullscreen too. jf.host and jf.join are only used by the launcher. The new handlers do validate their arguments (mode whitelist, normalize()), but they don't check who is calling.

**Failure:** Electron 33 under Xvfb running the real desktop/main.cjs (userData redirected to scratch). The launcher calls jf.join('127.0.0.1:4150'), a plain page I served. On http://127.0.0.1:4150/, Object.keys(window.jf) is [desktop, info, host, join, launcher, fullscreen, display, displayGet, quit]. window.jf.display('fullscreen') returns 'fullscreen', win.isFullScreen() becomes true, and display.json reads {"mode":"fullscreen"}. I did not call jf.host() because it would bind port 3000, but nothing in the code stops it.

**Suggested fix:** In main.cjs, check e.senderFrame.url in each handler. Allow jf:host and jf:join only from the file:// launcher. Allow display, displayGet, launcher, info and quit only from the launcher, http://localhost:<local.port> and the configured official origin. Optionally the preload can skip exposing host/join when location.protocol isn't file:.

**Verifier notes:** Restrict jf:host and jf:join to the launcher: check that e.senderFrame.url starts with pathToFileURL(LAUNCHER).href and that e.senderFrame === win.webContents.mainFrame. Return info.hosting only to the launcher and localhost. Defense in depth: expose host/join in preload.cjs only when location.protocol === 'file:'. With contextIsolation and sandbox, that alone closes them. Do not limit launcher, quit, display and displayGet to launcher+localhost+official as suggested. The game page on a friend's LAN server or a custom address joined through JOIN uses jf.launcher ('change server'), jf.quit and jf.display, so that allowlist would break the desktop UI there.

## 24. [low] Display mode desyncs from F11 / jf.fullscreen: windowed size lost, stale persisted fullscreen, stale 150 ms maximize fallback
(id display-mode-desync, area maps-desktop, desktop/main.cjs:128)

**Problem:** displayMode only changes through jf:display. F11 (line 92) and jf:fullscreen (line 121; the launcher's 'fullscreen (F11)' link and older pages) toggle fullscreen directly. So applyDisplay() saves windowedBounds from a window that is actually fullscreen whenever displayMode is still 'windowed'. Leaving 'fullscreen' with F11 leaves display.json and displayGet at 'fullscreen'. Separately, the 150 ms maximize fallback (line 134) doesn't check that the mode is still 'maximized', so a quick maximized->fullscreen switch (for example a double click on the in-game cycle button) resizes the fullscreen window to the work area.

**Failure:** Real main.cjs in Electron under Xvfb at 1920x1080. Start: 1280x760 at (320,160). jf.fullscreen() (same as F11) gives 1920x1080 fullscreen. Then jf.display('maximized') and jf.display('windowed') leave the window at 1919x1079 at (0,0): the 1280x760 windowed size is gone for the session. jf.display('fullscreen') followed by F11 to leave: the window is no longer fullscreen, but display.json and jf.displayGet() still say 'fullscreen', so the next launch starts fullscreen and Settings shows Fullscreen. jf.display('maximized') immediately followed by jf.display('fullscreen'): 660 ms later isFullScreen() is true but the bounds are 1919x1079.

**Suggested fix:** Send F11 and jf:fullscreen through applyDisplay (toggle 'fullscreen' against the last non-fullscreen mode, and persist it). Save windowedBounds only when !win.isFullScreen() && !win.isMaximized(), or use win.getNormalBounds(). In the fallback timeout, require displayMode === 'maximized' && !win.isFullScreen() before setBounds.

**Verifier notes:** The suggested fix is correct. Simpler and more complete: listen to win.on('enter-full-screen'/'leave-full-screen'). That covers F11, jf:fullscreen and OS exits. On leave, set displayMode to the last non-fullscreen mode and persist it. Use win.getNormalBounds() for windowedBounds, which also covers a user-maximized window. In the timeout require displayMode === 'maximized' && !win.isFullScreen(). The page caches S.display and calls displayGet only at load, so the cycle button and Settings should re-read jf.displayGet(), or main should push the mode to the page.

## 25. [low] Scenery adds 138 to 475 separate meshes (draw calls) per map; the map itself is merged to 8 to 42
(id scenery-draw-calls, area maps-desktop, public/js/scenery.js:51)

**Problem:** buildScenery creates every mountain, snow cap, cliff block, hill, tree cone, trunk, shed, roof, stack, mesa, isle, palm, city tower and cloud as its own Mesh with its own geometry. Nothing is merged or instanced, and the meshes share only 3 to 9 materials. world.js merges map boxes per material precisely to keep draw calls to 'a couple dozen'. The scenery multiplies the static draw calls by 10 to 25x every frame, and the low-res jank settings don't reduce draw calls.

**Failure:** Running buildScenery in node with three 0.170 for each map: Suburb 475 meshes (6,870 triangles, 7 materials) against 42 merged map meshes. Rooftop 367 against 15. Skyline 269 against 16. Warehouse 221, Desert 201, Bazaar 175 against 19. Crate and Range 138, which include 90 transparent cloud spheres that three.js sorts every frame. After frustum culling that is still a few hundred extra draw calls per frame on Suburb, which costs CPU time each frame on low-end machines.

**Suggested fix:** Build the scenery geometries in world space and merge them per material with mergeGeometries, as buildMap does (about 10 draw calls per map), or use one InstancedMesh per repeated shape (trees, towers, clouds, mountains).

**Verifier notes:** The suggested fix is fine. Bake each mesh's transform into its geometry (m.updateMatrix(); geo.applyMatrix4(m.matrix)), group the geometries by material, and mergeGeometries them into one Mesh per material (~3-10 per map). All these primitives are indexed with position/normal/uv, so they merge. Merged clouds lose per-cloud sorting, which is acceptable at uniform opacity (or set depthWrite:false). Also dispose the per-build materials and the city CanvasTexture on rebuild; today only geometries are disposed.

## 26. [low] On sky maps the new cloud sea sits mostly under the opaque void plane
(id sky-clouds-under-void, area maps-desktop, public/js/scenery.js:136)

**Problem:** For the 'sky' theme (Crate, Platform, Range), scenery.js keeps the opaque void plane visible at killY-25 (line 67). The 'sea of clouds below' is placed at killY-30 to killY-50 with vertical half-heights of 7.5 to 22.5 m. The opaque plane writes depth, so the transparent clouds are hidden wherever they are below it.

**Failure:** Replaying scenery.js's seeded rng: on Crate the void plane is at y=-55, 42 of the 90 clouds lie entirely below it, and only about 11% of the cloud layer's height rises above it. Platform: 43/90. Range: 42/90. Looking down from these maps you see the flat dark-magenta void with a few cloud tops poking through, not the intended cloud sea.

**Suggested fix:** Hide voidMesh for the sky theme as the other themes do, or put the clouds above the void plane (centres above killY-25 plus their half-height), or move the void plane below the cloud layer.

**Verifier notes:** For the sky theme either set voidMesh.visible = false (as the other themes do), or lower it under the layer inside buildScenery, e.g. voidMesh.position.y = map.killY - 80. loadMap sets killY-25 before calling buildScenery, so the override sticks. Alternatively raise the cloud centres to ≥ killY-25+0.25*s.

## 27. [low] Late joiners don't see active shield bubbles (welcome.bubbles ignored) or smoke clouds (not synced)
(id late-join-bubbles-smoke, area protocol, public/js/main.js:806)

**Problem:** The server puts `bubbles` in 'welcome', but the client's welcome handler never reads m.bubbles. It handles players, peels, projs, holes, round, team, kat, tags and vote, and nothing calls addBubble on join. Smoke grenades are a one-shot 'smoke' broadcast with no server state, so there is nothing to send. Frozen players' ice is also not in welcome.

**Failure:** Verified with Playwright. A ws client pops a bubble in the Online room, then a browser joins. window.__welcome.bubbles.length is 1, but JANK.G.bubbles.size is 0. The joiner sees no dome for up to 7 s, and their shots at people inside just make 'bubhit' sparks. A player who joins during a 10 s smoke can see straight through it.

**Suggested fix:** Add `for (const b of m.bubbles || []) addBubble(b);` to the welcome handler. Keep smoke clouds in a room map with expiry (removing them in tickItems) and include them, plus frozen ids and remaining time, in welcome.

**Verifier notes:** addBubble already uses m.left, so `for (const b of m.bubbles || []) addBubble(b);` in welcome fully fixes bubbles. For smoke: when a smokegren pops, keep {p, r, until} in a room list, prune it in tickItems, and send [{p, r, dur: until-now}] in welcome (the client already sets until = now + dur). Clear the list on resetWorld or a map change. Optionally send frozen ids with their remaining ms.

## 28. [low] Client frost overlay never decays: one snowball leaves the screen frosted for the rest of the life
(id frost-overlay-never-decays, area protocol, public/js/main.js:955)

**Problem:** G.frost is set from 'frost' messages and is cleared only on 'freeze', 'spawn' and leaving the room. The server decays frost by one stack every 3 s, but it sends no update when frost decays, and the client never decays G.frost itself. The freezeFx overlay is drawn at min(0.6, G.frost*0.15) every frame, so it stays on screen long after the server's frost is gone.

**Failure:** Get hit by 3 snowballs, then escape. The server's frost drops back to 0 over about 9 s, but the client keeps G.frost=3. The icy inset vignette stays at 0.45 opacity, partly blocking the view, until you die or get frozen. A single hit leaves a permanent 0.15 tint.

**Suggested fix:** Store the time of the last frost hit and decay G.frost on the client by the same 1-stack-per-frostDecay rule. Alternatively, have the server send 'frost' with the decayed n.

**Verifier notes:** Decay on the client using the server's rule. On 'frost', store G.frostT = performance.now(). When drawing, use shown = Math.max(0, G.frost - Math.floor((now - G.frostT) / (WEAPONS.snowball.frostDecay*1000))). The server only computes decay when the next hit lands, so having it 'send the decayed n' would need a new timer.

## 29. [low] Killstreak tray progress only updates at milestones (shows 0/6 after 5 kills)
(id streak-tray-progress-stale, area protocol, public/js/main.js:1477)

**Problem:** The new tray renders `${min(n, st.kills)}/${st.kills}` using G.streakN. G.streakN is only set by {t:'streak', earned} (when the streak hits one of your 3 picks) and by reset. The server sends no per-kill streak count and the client does not count its own kills, so progress and the 'streak N' label are stale between milestones.

**Failure:** With the default picks (3/4/5), after 2 kills the tray still reads 0/3 0/4 0/5. With picks spinbot/satellite/giantduck it reads 0/6 0/7 0/10 after 5 kills, then jumps to 6/6. After 8 or 9 kills it still reads 7/10.

**Suggested fix:** Send the killer the current streak on every kill (e.g. {t:'streak', n}) and update G.streakN. Alternatively, count your own kills from 'kill' events (m.k===G.myId) and reset on 'streak reset'.

**Verifier notes:** If the server sends {t:'streak', n} on every kill, the client handler must change too. Today a message with neither reset nor earned falls through to the reward branch and returns at `if (!st) return` without updating G.streakN. Add `if (m.n != null) { G.streakN = m.n; renderStreak(m.n); }` before that check. Alternatively, count locally on 'kill' events where m.k === G.myId && m.v !== G.myId, and reset on {reset}.

## 30. [low] Randomizer 'loadout' has no item, so the client silently switches everyone's item to Frag
(id randomizer-forces-frag, area protocol, public/js/main.js:999)

**Problem:** The server's randomLoadout() returns only primary/secondary/melee. The client's 'loadout' handler calls setLoadout(m.lo), which runs validLoadout(lo) and fills item with DEFAULT_LOADOUT.item ('frag'), and setLoadout then sets W.item = 'frag'. For the whole Randomizer match the item is neither random nor the player's pick. When the mode ends, lo:null restores it.

**Failure:** Pick Shield Bubble in LOADOUT and join a Randomizer match. The HUD item slot shows Frag Grenade and G throws frags every life.

**Suggested fix:** Have the server include an item in the random loadout (random or the player's), or have the client merge: setLoadout({ ...S.loadout, ...m.lo }).

**Verifier notes:** A client merge, setLoadout({ ...S.loadout, ...m.lo }), keeps the player's item and is enough by itself. If the server starts enforcing p.item (item-projectiles-via-fire fix), it must keep p.item in rand, or put a random item in randomLoadout and set p.item to it. Otherwise client and server disagree and the item is refused.

