# Review findings for the server side (39; some are the same bug reported by two reviewers: fix once)

## 1. [critical] New message fields are used as object keys without a type check, so one nested-array message crashes the server
(id deep-array-key-crash, area combat, server.js:625)

**Problem:** Several new lookups use client data as a property key with no `typeof === 'string'` check: useItem does `ITEMS[m.i]` (server.js:625). The 'streaks' handler calls validStreaks, which does `STREAKS[id]` (shared/weapons.js:235). The 'look' handler calls validLook, which does `HAIRS[look.hair]`, `TOPS[look.top]` and `BOTTOMS[look.bottom]` (shared/looks.js:60-62). setCfg does `GAMES[m.game]` (server.js:1310). Turning a deeply nested array into a property key recurses through Array.prototype.toString/join and throws RangeError. Nothing catches it: there is no try/catch around `me.room.handle(me, m)` (server.js:1806) or in ws's emit, so the process exits. The 'chat' handler already had the same problem through clean()/String(). The PR adds four more ways to trigger it.

**Failure:** Verified against a server on port 4110. A joined client sent the 12 KB text `{"t":"item","i":[[[[...6000 levels...]]]]}`. The server printed `RangeError: Maximum call stack size exceeded` at server.js:625 `const it = ITEMS[m.i]` and exited, which disconnected every player in every room. The same thing happened with {"t":"streaks","list":[deep]} (crash at shared/weapons.js:235), {"t":"look","look":{"hair":deep}} (shared/looks.js:60) and {"t":"cfg","game":deep} (server.js:1310).

**Suggested fix:** Before every table lookup on client data (m.i, each entry in validStreaks, look.hair/top/bottom/head/face/back, m.game, m.map/hip/diff), require `typeof x === 'string' && Object.hasOwn(TABLE, x)`. Also wrap `me.room.handle(me, m)` and the per-room tick in try/catch that logs and drops the message, so one bad message can't kill the process. That also closes the older 'chat' path.

**Verifier notes:** Per-lookup typeof/hasOwn checks alone do not close this. Many older sinks coerce client values: String(), `| 0`, Number()/clampInt, the JSON.stringify echo, WEAPONS[m.w], MAPS[m.map], ACCESSORIES[..]. Guard it centrally: (1) right after JSON.parse in the ws 'message' handler, drop any message nested deeper than a small limit. The protocol never goes past about 3 levels (fire.s [[6 nums]], join.skins {id:[...]}). Use an iterative scan or a depth-capped recursion for the check. (2) Wrap me.room.handle(me, m) in try/catch that logs and drops the message, and do the same for the per-room tick and snapshot loops. (3) Add .catch(()=>{}) to the async IIFEs in 'kfx' and 'skin', because a sync try/catch misses the 'kfx' rejection (verified crash). Still also use `typeof x === 'string' && Object.hasOwn(TABLE, x)` for ITEMS/STREAKS/GAMES/HAIRS/TOPS/BOTTOMS; ITEMS needs it anyway for '__proto__'.

## 2. [critical] One oversized WebSocket frame crashes the whole server (no 'error' listener on client sockets)
(id ws-error-crash, area protocol, server.js:1778)

**Problem:** The connection handler registers 'pong', 'message' and 'close' listeners on each client socket but no 'error' listener. When ws rejects a frame (bigger than maxPayload 40000, or a compressed frame that fails to inflate), it emits 'error' on the WebSocket. With no listener, Node throws "Unhandled 'error' event" and the process exits, so every room drops. This bug was already on origin/main and the PR did not add it. It is listed here because the PR's goal is a public Render deploy where anyone can send any frame.

**Failure:** Verified on port 4160. A client joins, then runs new WebSocket(url,{perMessageDeflate:false}).send('x'.repeat(50000)). The server log shows 'RangeError: Max payload size exceeded ... Emitted 'error' event on WebSocket instance ... throw er; // Unhandled 'error' event', the process exits, and /health stops responding. A 50 KB chat message over a compressed connection hit the same crash through Z_DATA_ERROR.

**Suggested fix:** In wss.on('connection') add ws.on('error', (e) => console.warn('ws error', e.message)). Also wrap me.room.handle(me, m) in try/catch so a throwing handler cannot take down the process.

**Verifier notes:** The main fix is correct and enough for this crash: add ws.on('error', (e) => console.warn('ws error', e.message)) at the top of wss.on('connection'). I verified it against all three frame types. Wrapping me.room.handle in try/catch is fine as extra safety, but it does not cover the async IIFEs ('kfx', 'skin') or the setTimeout callbacks (setCfg->startRound, the chickenstrike deploy, hlCandidate). As a last resort, also consider logging process.on('uncaughtException') and process.on('unhandledRejection') instead of letting one room's error take down every room.

## 3. [high] Items aren't tied to the loadout or charges: 'fire' w:frag/smokegren is unlimited and 'item' accepts any item id
(id item-projectiles-via-fire, area protocol, server.js:1023)

**Problem:** frag and smokegren are new WEAPONS entries with kind 'proj', slot 'hidden' and no cd. onFire forwards any kind 'proj' weapon to spawnProj. spawnProj's cooldown check `n - lastFire < w.cd * 750` compares against NaN, so it never blocks. Any client can throw unlimited 105-damage frags and smoke bombs without using a charge. The duck (now slot 'item') can also still be thrown through 'fire' every 3.75 s instead of 1 charge per 20 s. Separately, useItem trusts m.i and keeps charges per item id. The server never learns which item the player picked, so 'one item per loadout' is not enforced.

**Failure:** Verified. The attacker sends 30× {t:'fire',w:'frag',o,d:[0,-1,0]} and 30× {t:'fire',w:'smokegren',...} in one burst. Result: 30 frag 'ps', 30 'boom', the victim is killed, 30 'smoke' broadcasts, and 0 'ic' messages. With spam, every client's G.smokes grows without bound and spawns 11 particles per cloud per frame. In the same life, after using both frags, {t:'item',i:'bubble'}, then i:'medkit', then i:'duck' all worked (bub+, medkit fx, duck ps).

**Suggested fix:** In onFire, reject weapons whose slot is 'hidden' or 'item' (only loadout slots, plus streak weapons when earned). Send the chosen item in 'join' and on loadout change (applied at respawn), store it as p.item, and have useItem refuse any m.i !== p.item.

**Verifier notes:** Use an allow-list, not a block-list. In onFire: `if (!SLOTS.includes(w.slot) && !(w.slot === 'streak' && p.scythe)) return;`. Blocking only 'hidden'/'item' would leave 'card' (slot null, cd 0) open. Legit clients only fire loadout weapons, 'cards', 'reverse', 'bow' and the scythe, and bots call spawnProj directly, so nothing legit breaks. Also make the cooldown NaN-safe: (w.cd || 0). For items: send `item` in join and on loadout change, validated against ITEMS. Store it as p.item and apply changes under the client's applyLoadout rule (immediately while dead or within 5 s of spawn, otherwise at respawn). useItem drops any m.i !== p.item. Ship this together with the randomizer-forces-frag fix: in rand the server must keep or set p.item, or every G press there would be refused.

## 4. [medium] 'respawn' message cuts the 4.5 s Plant & Defuse respawn to 1.5 s (default killcam skip does it)
(id bomb-respawn-skip, area modes, server.js:1434)

**Problem:** In bomb games kill() sets respawnAt = now + BOMB.respawn (4.5 s, line 816). The 'respawn' handler (lines 1434-1436) lets any dead player lower respawnAt to max(now, deadT + 1500). The client sends 'respawn' whenever the killcam ends or is skipped (main.js skipReplay / onEnd). Killcam is on by default (kc: settings.killcam !== false). So a player killed by an enemy who presses SPACE is back after 1.5 s, and a crafted client can send 'respawn' after every death. Players with killcam off wait the full 4.5 s. Separately, the client dead timer hardcodes 2.5 s (main.js:1295), so it also disagrees with the 4.5 s bomb respawn.

**Failure:** Reproduced on :4100 (Bots room, Bazaar, bomb). After a {t:'tbag'} self-kill, 'spawn' arrived after 4511 ms. After {t:'tbag'} followed 30 ms later by {t:'respawn'}, 'spawn' arrived after 1507 ms. In an Online bomb match, any default client killed by an enemy who presses SPACE during the killcam respawns 3 s ahead of everyone else.

**Suggested fix:** Floor the message at the mode minimum, e.g. respawnAt = min(respawnAt, max(now(), deadT + (this.game === 'bomb' && this.teamsOn() ? BOMB.respawn : 1500))). Better: store p.minRespawnAt in kill() and never go below it. Have the client dead timer use the mode's delay.

**Verifier notes:** The suggested floor is correct for bomb. Cleaner: in kill(), next to line 816, store t.minRespawnAt = now() + (this.game === 'bomb' && this.teamsOn() ? BOMB.respawn : 1500). The handler becomes `if (!p.alive) p.respawnAt = Math.min(p.respawnAt, Math.max(now(), p.minRespawnAt || 0));`, so the floor uses the mode at death time. Optionally use 2500 as the non-bomb floor: the 1 s DM skip advantage predates the PR. Client: the dead timer at main.js:1295 should count down from BOMB.respawn/1000 when G.round.game === 'bomb'.

## 5. [medium] 'look' message replaces the team color mid-match, so players can disguise as the other team
(id look-overrides-team-color, area modes, server.js:1408)

**Problem:** The 'look' handler sets p.color = p.look.color whenever the look has a body color, then broadcasts it in 'lk'. Remote clients apply it with r.setLook(m.look, m.color). There is no teamsOn() check. In TDM, Tags and Plant & Defuse, anyone who edits their character mid-match (main.js setLook sends 'look' on every change) loses the team color until the next assignTeams. LOOK_COLORS contains '#ff4f4f', which is exactly TEAMS[1].color, so a BLUE player can look identical to RED. Remote models carry no other team marker (remote.js never reads team). This breaks 'team colors override player colors'.

**Failure:** Reproduced in the Online room (JF_ROUND_KILLS=1 to reach a vote; both players voted TDM). Teams were [[2,1,'#ff4f4f'],[1,2,'#4fa8ff']]. The BLUE player (id 1) sent {t:'look', look:{color:'#ff4f4f'}}. The RED player received lk {id:1, color:'#ff4f4f'} and now renders the enemy in RED team color.

**Suggested fix:** In the 'look' case, still store p.look and update p.ownColor, but when this.teamsOn() && p.team keep p.color = TEAMS[p.team].color and broadcast that color.

**Verifier notes:** The fix is correct. In 'look', store p.look = validLook(...), then set p.color = this.teamsOn() && p.team ? TEAMS[p.team].color : (p.look.color || p.ownColor || p.color) and broadcast that color. Leave p.ownColor alone: assignTeams already prefers p.look.color when teams end. A partial disguise remains: outfit topColor/bottomColor (CLOTH_COLORS contains '#ff4f4f') override the body color in models.js buildCharacter (848-849), so a BLUE player can still wear all-red clothes. In team games, either blank topColor/bottomColor in what the server sends, or have the client build remotes with the team color.

## 6. [medium] The bomb can disappear for the rest of the round: void death with no living attacker, empty attacking side, carrier disconnect
(id bomb-lost-no-carrier, area modes, server.js:1620)

**Problem:** When the drop point has no ground (the void), dropBomb hands the bomb to a random living attacker. If no attacker is alive, it leaves carrier = 0 and drop = null. Nothing re-issues the bomb later: newBombRound assigns it only at round start, and joinTeam and respawn never do. The same dead state happens when the attacking side is empty at round start (lines 1608-1610) and someone joins mid-round. Also, remove() calls dropBomb before players.delete (line 325), and the leaving player is still alive and in players. So the void fallback can pick the disconnecting player, leaving carrier set to the id of a player who no longer exists. In every case attackers cannot plant, and the round goes to the defenders on time. This contradicts 'the bomb drops where its carrier dies and can be picked up again'.

**Failure:** Reproduced on :4100: Bots room, bomb on Bazaar, bots:1, so I am the only attacker and the carrier. After I send 's' with p=[0,-35,0], the snapshot shows carrier 0 and drop null, and still does after my respawn. The round ends 'time' with the defenders winning. Virtual-time Room: after the side swap the attacking team is empty (carrier 0). A bot added via cfg joins the attackers, but carrier stays 0 for the whole round. Virtual-time Room, 3 humans in Bazaar bomb: when the carrier disconnects while at [90,6,0] (outside the walls), the bomb goes to the departed player in 18/40 trials.

**Suggested fix:** Pass the dropping player into dropBomb and exclude them from the fallback. When no attacker is alive, put the bomb at an attacker spawn (b.drop = map.teamSpawns.att[0]) rather than nowhere. In tickBomb, if b.ph === 'live' && !b.carrier && !b.drop (or the carrier is not in players), give it to the next living attacker.

**Verifier notes:** The suggested fix is right; to make it complete: (1) Exclude the leaver: in remove(), call players.delete before dropBomb, or pass an exclude id. (2) In the void branch, when no other attacker is alive, set b.drop to an attacker spawn (this.map.teamSpawns.att[0], falling back to spawns[0]) instead of null. (3) Send 'bombyou' to whoever gets the bomb in the fallback; it currently sends nothing. (4) Add a tickBomb guard: if b.ph === 'live' && !b.drop && (!b.carrier || !this.players.has(b.carrier)), hand the bomb to a living attacker (humans first) with 'bombyou', or else drop it at an attacker spawn. This also covers the empty attacking side and late joiners.

## 7. [medium] Changing the map out of Plant & Defuse leaves a 1-hour DM round and carries over the bomb-match kills
(id map-change-leaves-bomb-round, area modes, server.js:1306)

**Problem:** Any Online player may send a cfg map change. When the new map has no sites, setCfg switches the game to 'dm', nulls the bomb and reassigns teams, but keeps this.round from the bomb match. That round has ends = now + 3600 s (set by startRound at line 1525) and the fallback target of 20 (Online) or 15 (Bots), and p.kills/deaths are not reset. The match rotation and the vote stall until someone reaches the target, and bomb-match kills count toward it. In Tags, a map change also keeps this.tags on the server, and the client keeps its tag meshes (clearEntities does not clear tags), at old-map coordinates. They stay pickable and scorable until they expire.

**Failure:** Reproduced on :4100: Bots room on Bazaar bomb; sending {t:'cfg', map:'islands'} gives a snapshot round of {game:'dm', target:15, left:3587896 ms, over:false}. Code-traced for the Online room: a player with 19 kills from the bomb match needs one DM kill to 'win the round' and receive the roll, and with few players the DM can otherwise run for an hour.

**Suggested fix:** When the map change forces the game to dm, start a fresh round instead (this.vote = null; this.startRound(), or at least reset round.ends/target and every player's kills/deaths). Call clearTags() on every map change.

**Verifier notes:** In the forced-dm branch, call `if (!this.round.over) this.startRound()`. startRound already resets kills/deaths, target, ends, score, tags, teams and bomb, and calls resetWorld, so skip the resetWorld/newBombRound that follows to avoid a double spawn. Do not null this.vote and start a round while round.over: that cancels a running vote and lets one player skip it, and the vote sets the map anyway. Call clearTags() on every map change. Alternative: refuse Online map changes away from the site map while a bomb match is running.

## 8. [medium] The 'fire' message throws item-only projectiles (frag, smoke, duck) with no charges and no cooldown
(id fire-item-projectiles, area combat, server.js:958)

**Problem:** onFire only rejects `slot === 'streak'` (line 944). WEAPONS.frag and smokegren (slot 'hidden') and duck (now slot 'item') are all kind 'proj', so `{t:'fire', w:'frag'}` goes straight to spawnProj and never touches the item charges in itemCharges/useItem. frag and smokegren define no `cd`, so the spawnProj cooldown test `n - lastFire < w.cd * 750` (line 1023) compares against NaN and never blocks. The duck has cd 5, so it can be thrown every 3.75 s instead of one charge per 20 s. Each frag is also broadcast ('ps', then 'boom') and stepped every tick, so a burst floods every client too.

**Failure:** Verified on port 4110. A client sent 25 back-to-back {t:'fire', w:'frag', o:eye, d:[0,-1,0]} next to another player. The server spawned 25 frags; the legit 'item' path gave 2 more and correctly refused a third. There were 25 explosions of 105 dmg in a 7.5 m radius and the victim was killed. 5 {t:'fire', w:'smokegren'} messages put 5 smoke clouds on every client. A modified client can wipe a lobby every 2.2 s.

**Suggested fix:** In onFire, return early for any weapon whose slot is not primary/secondary/melee/streak, e.g. `if (!w.slot || w.slot === 'hidden' || w.slot === 'item') return;`. Make spawnProj refuse weapons without a finite cd. Item projectiles should only ever come from useItem → makeProj.

**Verifier notes:** The suggested gate is correct and breaks no legit flow. The client sends 'cards' (not 'card'), dash goes through 'hit', and bots call spawnProj directly. In onFire, after the !w check: `if (!['primary','secondary','melee','streak'].includes(w.slot)) return;` (same as rejecting slot null/'hidden'/'item'). This also closes the older unthrottled 'card' path. Optional extra guard in spawnProj: `if (!(w.cd > 0)) return;`.

## 9. [medium] Snowball frost and shatter ignore spawn protection, the reverse card and the post-match lock
(id frost-shatter-bypasses-rules, area combat, server.js:663)

**Problem:** The snowball hit branch (lines 1184-1187) checks only the bubble and friendly fire. It then calls frost() whether or not hurt()/damage() actually applied the hit. frost() freezes the target and shatters it by calling kill() directly (line 663). So the rules other damage follows never apply to frost, freeze or the shatter kill: damage() has 1.2 s spawn protection and no damage while round.over, and hurt() reflects hits off an active reverse card.

**Failure:** All three verified on port 4110. (1) Spawn protection: a player who had just joined got frost at 7/248/489 ms, was frozen at 713 ms and was shatter-killed at 960 ms, inside the 1200 ms window. No damage event was sent, only the kill. (2) Reverse card: with B's reverse card up, the 9 dmg bounced back to the thrower but B still received frost n=1. After B was frozen, B raised a reverse card and the next snowball shattered B anyway. (3) Post-match: with a 1-kill target, after the match ended (round over, vote running), 5 snowballs froze and shatter-killed a respawned player and the thrower's kills went from 1 to 2. With an account this also adds kills/xp stats and killstreak progress.

**Suggested fix:** Only apply frost when the hit really landed: have hurt()/damage() return whether damage was applied, or check spawn protection, round.over and t.reverseUntil before calling frost(). Send the shatter through the same gate (for example damage() with a lethal amount) instead of calling kill() directly.

**Verifier notes:** Gate both frost and the shatter on the same rules. The suggested example, damage() with a lethal amount, is not enough: damage() does not handle the reverse card (that check is in hurt()), so case 2b would still happen. Better: make hurt() (and damage(), which is void today) return the player actually damaged. Return null when friendly fire, the bubble, spawn protection or round.over blocks it, and the attacker when the hit is reflected. Apply frost only when the result is v.t. For a frozen target, skip the shatter while v.t.reverseUntil > now (or reflect one frost stack instead). Otherwise call hurt(v.t, owner, 'snowball', v.t.hp + 999, null) and broadcast 'shatter' only if v.t died.

## 10. [medium] Dropped bomb: every attacker bot beelines at it with force=true and no routing, so reachable drops go unrecovered for whole rounds
(id bot-drop-chase-no-route, area bots, server.js:509)

**Problem:** botGoal returns { p: B.drop, force: true, r: 0 } for every alive non-carrier attacker. botThink (447) then walks straight at the drop from wherever the bot is, including fresh respawns in the camp, and force overrides normal fight movement. Nothing uses map.nav or checks line of sight, so the whole attacking team pins itself on the camp walls, the hall walls and stalls, the Stable, or the B-gate wall. Nobody reaches the bomb and the round runs out.

**Failure:** Sim (Bazaar, bomb, 10 normal bots, seed 3): the carrier dies in the mid plaza and the bomb drops at (-14.1,0.15,-2.4), an open, reachable spot. Five attacker bots get stuck at (-8.6,0,5.9) (hall wall/stall corner), (-8.6,0,29.9), (-13.8,1.2,52.8) (camp north wall) and on the hall roof, for 76-90 s each, until defenders win on time. Over 5 seeds x 10 minutes there were 38 such episodes, and 1-2 drops per run were never picked up although all drops were at ground or terrace level.

**Suggested fix:** Route to the drop instead of beelining: follow the nav lane nearest the drop and finish with a direct leg only when there is line of sight. Send only the 1-2 nearest attackers and keep the rest on their lanes. Add a no-progress timeout that re-plans.

**Verifier notes:** The lanes are three separate polylines per site with no links between them, so "follow the lane nearest the drop" needs a graph. Treat consecutive waypoints on each lane as two-way edges, link waypoints on different lanes that can see each other (body-width line of sight) within about 15 m, and treat both spawns and both sites as junctions. Run a breadth-first search from the bot's nearest visible waypoint to the waypoint nearest the drop that can see it, then finish with a direct leg. Send only the 1-2 attackers nearest by path length, not straight-line distance; the rest keep their site plan. Clear ai.route when the chase ends (for example when someone else picks the bomb up). Otherwise those bots resume an old waypoint index from wherever they wandered (finding 4). Also re-plan when the bot moves less than 1 m in about 2 s.

## 11. [medium] Bot route progress (ai.route/ai.ri) survives death, so respawned bots walk straight from spawn at a mid-route waypoint and pin on the camp walls
(id bot-stale-route-after-respawn, area bots, server.js:488)

**Problem:** routeTo only picks a new route when !ai.route or ai.routeSite !== siteId. ai.route/ai.ri are cleared only in newBombRound (1605). kill() (780) clears only ai.hook, and the respawn block in tick() (1699-1707) clears freeze/slip/etc. but not the route. A bot that dies at waypoint k respawns 4.5 s later in its camp with ri=k and heads straight at that waypoint through the camp walls and the market hall.

**Failure:** Traced (seed 3): bot #7 died at (-15.3,0,-6.5) on route A1 index 3 (target [8,-3]) and respawned at (5.9,0.4,69.2). It walked straight north and pressed into the camp's north wall at (6.0-7.4,0,52.8), just east of the x -6..6 exit, from t=470 s until the round ended. Another bot died at A1 index 8 [31,-27.5] and sat in the camp's NE corner at (21.2,0,52.8). 3 seeds x 10 minutes gave 6-16 such episodes per run (400-840 bot-seconds), most lasting until the round ended.

**Suggested fix:** Clear ai.route/ai.ri/ai.routeSite on death or respawn (and in resetWorld), so routeTo picks again from the spawn position.

**Verifier notes:** The suggested fix is right and sufficient. In kill(), write `if (t.ai) { t.ai.hook = null; t.ai.route = null; }`. A null route forces a fresh pick from the spawn, which also overwrites ri and routeSite. I verified it in the harness (h/t3_fixed.mjs): all 6 cases then reach the site in 13-33 s. Clearing it in resetWorld too is harmless; newBombRound already does that before calling resetWorld. Keep ai.site so attackers keep their plan.

## 12. [medium] routeTo never re-plans and ignores line of sight: displaced bots, off-lane route picks and the 2.6 m early turn at doorways leave bots pinned on walls
(id bot-route-no-replan-los, area bots, server.js:494)

**Problem:** routeTo picks the nearest waypoint by 2D distance with no line-of-sight test (490) and only ever moves ri forward. Bots are often knocked off their lane by chasing targets, by knockback, and by grappling toward unseen enemies every 0.7-2.4 s (new in this PR), and afterwards they head straight for their old waypoint through buildings. The same happens when a route is first picked from off-lane: a defender heading to the planted site, a defender site switch, or a new carrier. The 2.6 m arrival radius (494) also advances the waypoint before the bot has cleared a doorway, so the next straight leg pushes it into the jamb.

**Failure:** (a) Traced: at the Spice House east door a bot is counted as arrived at [-21.5,-16.5] while still outside the wall at (-19.4,0,-17.8). It turns toward [-25,-21], slides down the outside wall and stops at (-19.4,0,-21) facing straight into it, for 64-77 s (carriers included). (b) Bomb planted at A: a defender at the B gate picks A1 index 2 [0,2] straight through two buildings and sits at (-40.4,0.4,-2.4) until the round ends (24-29 s, repeated). (c) A defender grappled over the garden block onto the Bridge still targets [22,-62] behind that block, stuck at (21.4,4.4,-29.6).

**Suggested fix:** Pick the nearest waypoint that has a clear chest-height raycast from the bot. Re-pick after grapples or knockback, and whenever distance to the current waypoint hasn't dropped for ~2 s. Only advance to waypoint i+1 when the bot is within ~1 m of waypoint i or already has line of sight to i+1.

**Verifier notes:** The direction is right but incomplete as written.
(1) In case (b), no waypoint on site A's lanes is visible from the B gate, so "nearest visible waypoint" needs a fallback. Use the same connected waypoint graph with a breadth-first search as for the drop chase, or have defenders walk their own lane back to the defender spawn and then take the other site's defender lane.
(2) The line-of-sight test must cover the body width (for example rays offset ±0.4 m at knee and chest height). A single chest-height ray passes gaps narrower than the 0.8 m body.
(3) Advance to i+1 only within about 1-1.5 m of waypoint i, or when i+1 passes that test.
(4) Re-plan after a hook release or knockback, and when the distance to the current waypoint hasn't dropped by about 1 m in about 2 s.
Fix this together with findings 1-3.

## 13. [medium] Tags are dropped at the corpse position with no ground snap, so void and mid-air kills leave unreachable tags that bots walk at and idle under
(id bot-tags-unreachable, area bots, server.js:521)

**Problem:** dropTag (1577) places the tag at victim pos + 0.9 and the client renders it there. dropBomb, by contrast, raycasts to the ground and handles the void. So tags from void deaths sit below killY and tags from mid-air deaths, now common with grappling and launching bots, float. Pickup needs the player's feet within ~1.9 m of the tag. botGoal sends every bot within 45 m (3D) straight at the nearest tag with no reachability check, and it loiters at the map edge or under the tag until the 30 s expiry whenever no enemy is visible.

**Failure:** 5 min of Tags with 10 bots: on Crate, 118 of 234 tags were dropped over the void (never scoreable) and bots spent about 240 bot-seconds parked next to unreachable tags. On Warehouse 12 of 81 tags were unreachable, and on Platform 32 of 180.

**Suggested fix:** Snap the tag to the ground below (raycast down like dropBomb). Drop it, or move it to the nearest valid ground, when there is no ground or it is below killY. In botGoal skip tags whose height above the ground under them exceeds reach.

**Verifier notes:** I raised this from low to medium because the same cause affects humans in the Online room. In Tags, void kills (common on Crate, Platform, Rooftop, Skyline and Islands) can never be confirmed or denied, so most kills on void maps never score. Fix it in dropTag: raycast down from (x, y+1, z) as dropBomb does. If ground is found above killY, place the tag at ground y + 0.9, because pickup compares against feet + 0.9. For a void death with no ground, choose one rule:
- use the victim's last grounded position (for bots, record it in stepBot when onGround; for humans, record it in the 's' handler when a short downward ray hits);
- or drop no tag and score the kill directly.
Once tags are snapped to the ground, botGoal needs no special reachability check.

## 14. [medium] Plant & Defuse 4.5 s respawn is cut to 1.5 s by 'respawn' (killcam skip)
(id bomb-respawn-skip, area protocol, server.js:1435)

**Problem:** kill() sets respawnAt = now+4500 in bomb mode, raised to now+9000 when the killcam is on. The 'respawn' handler then clamps respawnAt to max(now, deadT+1500), which ignores the mode's minimum. The client sends 'respawn' whenever the killcam ends or is skipped (any click or SPACE during it), and a crafted client can send it any time. The death screen also counts down a hardcoded 2.5 s (main.js:1295) in every mode.

**Failure:** Verified. In a bomb-mode bots room, a void death with no 'respawn' message respawns after 4519 ms. The same death followed by {t:'respawn'} respawns after 1505 ms. In real play, with killcam on (the default), a player killed by an enemy who clicks to skip respawns 3 s sooner than a player with killcam off.

**Suggested fix:** In 'respawn', clamp to the mode's minimum: Math.max(now(), p.deadT + (this.game==='bomb' && this.teamsOn() ? BOMB.respawn : 1500)). Have the client's dead timer use the same respawn time (e.g. sent in the kill or round info).

**Verifier notes:** The suggested clamp works. It is more robust to record the minimum at death: in kill(), set t.minRespawnAt = now() + (this.game==='bomb' && this.teamsOn() ? BOMB.respawn : 1500). The 'respawn' handler then sets p.respawnAt = Math.min(p.respawnAt, Math.max(now(), p.minRespawnAt || 0)). Also give the client the real delay (send it to the victim, or use BOMB.respawn when G.round.game==='bomb') so the dead timer doesn't count down a fixed 2.5 s.

## 15. [medium] Tags: void kills drop their tag below killY, so they can never be confirmed or denied
(id void-kill-tags-unreachable, area protocol, server.js:1577)

**Problem:** kill() credits void deaths to lastAttacker and calls dropTag(t), which places the tag at t.pos + 0.9. For a void death t.pos is already below map.killY (the 's' handler and stepBot kill only once y < killY). The tag therefore sits in the void, where nobody alive can reach it. It expires after 30 s without scoring for either team. Knockback-into-void is one of this game's main ways to kill, so many Tags kills cannot score. Bots also path toward tags within 45 m, including these.

**Failure:** Verified in a Tags bots room on Islands (killY -45). I knocked an enemy bot off the map with popper 'hit's. The kill was {w:'void', k: me}, and the broadcast was tag+ {p:[110.24,-44.34,242.03], team:2}, below the map edge where no player can stand.

**Suggested fix:** Drop void-kill tags like dropBomb does: raycast down from the death x/z and use the floor, or fall back to the victim's last grounded position or the killer's position. Otherwise skip the tag.

**Verifier notes:** For a void death, raycasting down at the death x/z (as dropBomb does) will almost always miss, because there was no floor there. So the fallback has to be the main path. Store the victim's position whenever they are tagged (tag() already records lastAttacker/W/T; add lastAttackPos = t.pos.slice()). Snap that point to the floor with a short downward raycast. If that fails, use the killer's position when the killer is alive and above killY; otherwise skip the tag. botGoal (521-525) should also ignore tags below killY + margin.

## 16. [medium] 'look' mid-match overrides the team color, so a player can disguise as the enemy team
(id look-overrides-team-color, area protocol, server.js:1407)

**Problem:** The 'look' handler does `if (p.look.color) p.color = p.look.color` and broadcasts 'lk' with that color, even when teamsOn() is true. Every client then rebuilds that player in the chosen color (body, outline, name, marker), which replaces the RED/BLUE team color. LOOK_COLORS contains '#ff4f4f', exactly TEAMS[1].color. Friendly fire still uses team ids, so the color is purely what everyone sees, and it stays wrong until the next round's assignTeams.

**Failure:** Verified in a TDM bots room. Teams were [[me,1,'#ff4f4f'],[bot,2,'#4fa8ff']]. Sending {t:'look',look:{color:'#4fd8ff'}} produced an lk broadcast with color '#4fd8ff'. Through the normal CHARACTER screen, a BLUE player who picks the red swatch looks exactly like a RED teammate to the RED team for the rest of the match.

**Suggested fix:** In 'look', when this.teamsOn() && p.team, keep p.color = TEAMS[p.team].color (store the chosen color in p.look / p.ownColor only) and broadcast the team color. The client's 'lk' handler for G.myId should not override G.myColor in team games.

**Verifier notes:** A server-only fix is enough. In 'look', after validLook: `if (this.teamsOn() && p.team) p.color = TEAMS[p.team].color; else if (p.look.color) p.color = p.look.color;`, then broadcast lk with p.color. assignTeams already restores p.look.color || ownColor when teams turn off, so keeping the chosen colour in p.look is enough. With the team colour in m.color, the client's 'lk' handler (main.js:857) is already correct for G.myId.

## 17. [low] Bot lane routes survive respawn and accept waypoints through walls, so bot carriers get stuck
(id bot-route-stale, area modes, server.js:488)

**Problem:** routeTo caches ai.route, ai.ri and ai.routeSite, and only newBombRound clears them. kill() and the respawn path in tick() keep them. A respawned bot therefore walks in a straight line from its spawn toward the waypoint it had reached before dying, through walls. The 2.6 m acceptance radius (line 494) also lets a bot 'reach' a door waypoint from the wrong side of a wall (Spice House doors, the Bridge stair landing), after which it pushes into the wall. A stuck carrier never plants, so bot attackers (including the bot-only team after the swap) frequently lose on time.

**Failure:** Deterministic, real Room code in virtual time: an attacker bot advanced to ri 7 on the canal-street route, was killed, and respawned at [12,0.1,66]. routeTo then returned [47,-21], 93.8 m away through walls, instead of the lane start [16,62]. 900 s virtual Bots-room match on Bazaar (9 bots): 3 of 6 bot-carried rounds had a carrier stuck for over 8 s outside a site and ended on time. The stuck spots were [-29.4,0.1,-28] heading for [-35,-28] at the Spice House west door, [19.6,0,-20.1] heading for [24,-20] under the Bridge, and on the market-hall roof.

**Suggested fix:** Clear ai.route, ai.ri and ai.site on death or respawn. When the bot is far from rt[ri], re-pick the nearest reachable waypoint. Advance ri only when the waypoint is also in line of sight (raycast at chest height), and use a smaller radius for door waypoints.

**Verifier notes:** The essential part is clearing the route on death: in kill(), set t.ai.route = null (ri and routeSite are rebuilt on the next routeTo), and optionally re-pick ai.site. Gate the ri advance on a chest-height raycast to the waypoint, so doors and landings cannot be 'reached' through a wall. Also add a stuck check: if the carrier moves less than 1 m in about 3 s, re-pick the nearest visible waypoint or jump/strafe. A goal pointing straight into a door jamb can pin a bot even with line of sight.

## 18. [low] A drawn team match still names the top fragger as winner and grants the round-win roll
(id draw-awards-winner, area modes, server.js:1489)

**Problem:** When team scores are equal, winTeam is 0, so pool falls back to the whole player list and winner becomes the top fragger (kills > 0). That player gets stat 'wins', 50 XP and a container roll when eligible. The 'round' broadcast carries winner:id and that client plays the win sound, while the header reads DRAW.

**Failure:** Virtual-time Room, Online TDM: alice kills bob and bob kills alice (1-1), then time runs out. The round-over message is {winTeam:0, winner:1, sc:[1,1]}, and roll+ is sent to alice (the guest variant; with an account it is a container plus 'wins' and XP).

**Suggested fix:** In team games set winner = winTeam ? pool[0] : null, so a draw grants no roll, stat or XP.

**Verifier notes:** The fix is correct, as long as the FFA rule stays: winner = this.teamsOn() ? (winTeam ? pool[0] || null : null) : (pool[0] && pool[0].kills > 0 ? pool[0] : null). A draw then broadcasts winner 0: no roll, stat or XP, and no win sound.

## 19. [low] The bomb always goes to the earliest-joined human attacker and cannot be passed
(id carrier-always-first-human, area modes, server.js:1609)

**Problem:** Every round, newBombRound picks att.find(p => !p.isBot): the first human attacker in join order. There is no drop or pass message (the client only sends 'use'), and friendly fire is off. Teammates therefore cannot get the bomb unless enemies kill the carrier, and an idle or griefing first joiner blocks every attacking round for their team.

**Failure:** Code-traced, Online Plant & Defuse with RED = [alice (joined first, AFK at spawn), bob]. In rounds 1-3 alice gets 'bombyou' every round. Bob can never take the bomb, every round times out, and BLUE wins 3-0 without a fight.

**Suggested fix:** Rotate or randomize the carrier among living human attackers each round. Add a drop action, or auto-drop the bomb when the carrier stays idle for N seconds.

**Verifier notes:** Pick the carrier at random (or rotate it) among living human attackers: const hs = att.filter((p) => !p.isBot); const carrier = hs.length ? pick(hs) : (att.length ? pick(att) : null). Rotation alone does not stop an AFK carrier, so also add an idle auto-drop on the server: a live-phase carrier who has not moved more than 1 m in about 10-15 s drops the bomb (dropBomb at their position). A manual drop key needs a new client message, validated server-side (alive, is carrier, ph live).

## 20. [low] New rounds (resetWorld) keep burn, freeze, sleep, heal and item state from the previous round
(id round-reset-keeps-status, area modes, server.js:1325)

**Problem:** resetWorld is used by startRound, newBombRound and map changes. It revives everyone, but unlike the respawn path in tick() (line 1703) it does not clear burnUntil/burnBy, frozenUntil/frost, sleepUntil, slipUntil, healLeft, ic or reverseUntil. Burn keeps ticking into the new round, credited to the previous round's attacker. A player still frozen server-side can be shattered right after spawning, and shatter calls kill() directly, so spawn protection does not apply. Frozen and sleeping bots stand still.

**Failure:** Virtual-time Room, Bots bomb on Bazaar: one bot is set on fire (3 s burn) and another is frozen, then newBombRound runs. Within 1.5 s of the new round the burning bot drops from 100 to 85 hp from 3 burn ticks credited to the human, and the frozen bot is still frozen and has moved 0.00 m.

**Suggested fix:** Move the per-life reset in tick() (slip, burn, sleep, frozen, frost, ic, healLeft, plus reverseUntil and ai.hook/g) into a helper, and call it from resetWorld as well.

**Verifier notes:** The fix is correct. Put the per-life reset in one helper (slipUntil, burnUntil, burnBy, burnTick, sleepUntil, frozenUntil, frost, frostT, healLeft, ic = {}, reverseUntil, g, ai.hook, lastAttacker) and call it from both resetWorld and the tick respawn path. Resetting p.ic in resetWorld matters for client sync: resetWorld sends 'spawn', the client then calls resetItems(), and without the reset the first item use of each round plays locally but the server silently rejects it. Bubbles and clouds also survive resetWorld; clearing them there is worth considering.

## 21. [low] Ownerless explosions ignore team and bubble protection (thrower left, the bomb blast)
(id ownerless-damage-ignores-teams-bubbles, area modes, server.js:701)

**Problem:** friendly() and bubbleBlocks() both return false when the attacker is null or undefined, and damage() then skips spawn protection too. Projectiles, holes and clouds look their owner up live, so after the owner leaves the room, a frag, chicken, duck or gas cloud hurts the owner's former teammates. The bomb explodes with owner null (line 1669), so a shield bubble does not protect anyone inside it from the blast, which contradicts 'nothing from outside hurts anyone inside'.

**Failure:** Virtual-time Room, Online TDM: a RED player's frag next to a RED teammate does 0 damage while the thrower is connected. With the same throw, if the thrower disconnects before the 2.2 s fuse, the teammate drops from 100 to 8 hp. Bazaar bomb: a defender stands inside a bubble (r 4.4) 6 m from the planted bomb, with the bomb outside the bubble. The blast kills the defender.

**Suggested fix:** Record the owner's team (and id) on projectiles, holes and clouds at creation, and check friendliness against that record rather than the live player. For ownerless area damage, test bubbles by source position: block the damage if the explosion point is outside the bubble and the victim is inside.

**Verifier notes:** The direction is right. Simplest complete fix for a departed owner: in remove(), delete that player's projectiles, holes and clouds (as is already done for slippers), or store the owner id and team at creation (makeProj, spawnProj, makeHole, makeCloud) and check friendliness against the stored team when the owner is gone. For ownerless area damage, pass the blast point to hurt()/bubbleBlocks and block it when the victim is inside a bubble and the point is outside. The bomb case does not change the round result (attackers have already won when it explodes); it only adds a death.

## 22. [low] 'vote' is not rate-limited (one broadcast per message), and departed players' votes still count
(id vote-broadcast-spam, area modes, server.js:1428)

**Problem:** Every valid 'vote' message stores the vote and broadcasts 'votes' to the whole room, even when the choice did not change, with no cooldown. During every 16 s vote window, one client can turn each 17-byte message into one send per player in the Online room. The pre-existing hitscan 'fire' fx relay is a similar unthrottled vector. Votes are keyed by player id and never removed in remove(), so players who have left still decide the next map and mode.

**Failure:** Reproduced in the Online room: player B sent 301 {t:'vote', i} messages and player A received 301 'votes' broadcasts. Code-traced: two players vote option 0 and leave, the remaining player votes option 1, and resolveVote picks option 0 by 2-1.

**Suggested fix:** Ignore a vote that does not change the player's choice, and rate-limit per player (e.g. 250 ms). Delete the player's entry from this.vote.votes in remove(), or count only ids still in this.players.

**Verifier notes:** The fix is right: ignore a vote equal to the stored one and throttle per player (about 250 ms). In remove(), delete p.id from this.vote.votes and broadcast the new counts, or count only ids still in this.players in voteInfo and resolveVote. A per-connection message budget in the ws 'message' handler is what actually closes the broadcast amplification, since the older 'fire' relay is a bigger path to the same thing.

## 23. [low] The server never learns the equipped item, so any client can use all five items
(id items-not-loadout-checked, area combat, server.js:624)

**Problem:** 'One item per loadout' is enforced only on the client. The join message carries no item, the server never stores one (there is no p.item), and useItem accepts any ITEMS id, each with its own charge pool. Since p.ic is also reset to {} on every respawn, a modified client gets 2 frags + medkit + bubble + duck + 2 smokes every life.

**Failure:** Verified: one player in one life sent item frag, frag, medkit, bubble, duck, smoke, smoke at 420 ms intervals. All 7 were accepted (ic replies frag:1 frag:0 medkit:0 bubble:0 duck:0 smoke:1 smoke:0) and every effect appeared: 2 frags, medkit fx, a bubble, a duck, 2 smoke grenades.

**Suggested fix:** Send the chosen item at join, validated with Object.hasOwn(ITEMS, x), and store it as p.item. Accept loadout changes only at respawn, and reject 'item' messages where `m.i !== p.item`.

**Verifier notes:** The suggested fix is incomplete as written: no message today tells the server about item changes. Add the item to the join payload and to a loadout-change message (for example, extend 'streaks' into a 'loadout' message). Validate it with typeof string + Object.hasOwn(ITEMS). Store it as p.item and apply changes at respawn, also allowing the client's 5 s after-spawn window or legit switches get refused. Then reject 'item' when m.i !== p.item. Keying charges per life instead of per item id also stops the switch-after-use trick.

## 24. [low] {t:'item', i:'__proto__'} pollutes Object.prototype: n and next become NaN for the whole process
(id item-proto-pollution, area combat, server.js:618)

**Problem:** useItem accepts any id for which `ITEMS[m.i]` is truthy, and that includes '__proto__' and 'constructor'. itemCharges then reads `p.ic['__proto__']`, which is Object.prototype, so no fresh entry is created. The check `c.n <= 0` is false for undefined, and useItem goes on to run `c.n--` (line 630) and `c.next = now() + undefined*1000` against Object.prototype.

**Failure:** Verified by loading server.js in-process on port 4110 and sending {t:'item', i:'__proto__'}. Before: ({}).n === undefined. After: ({}).n and ({}).next are NaN, `'n' in {}` is true, and `for (k in {})` yields ["n","next"]. This holds for every object in the server until restart, so any current or future code (or dependency) that reads .n/.next on plain objects or uses for...in now behaves differently. With i:'constructor' the same writes land on the global Object function.

**Suggested fix:** Validate with `typeof m.i === 'string' && Object.hasOwn(ITEMS, m.i)`, ideally also requiring m.i === p.item. Make p.ic a Map or Object.create(null). Use Object.hasOwn for the STREAKS/GAMES/HAIRS/TOPS/BOTTOMS lookups too.

**Verifier notes:** In useItem: `if (typeof m.i !== 'string' || !Object.hasOwn(ITEMS, m.i)) return;`. In itemCharges, make p.ic Object.create(null) or a Map. A crash-only fix (typeof string, depth limit, try/catch) does not stop this, because '__proto__' is a string. Use the same hasOwn check for STREAKS/GAMES/HAIRS/TOPS/BOTTOMS. Those lookups only read, so they are not pollution sinks, but ITEMS['toString'] and similar keys are truthy too.

## 25. [low] The shield bubble does nothing against damage with no attacker: the bomb blast, or projectiles from a player who left
(id bubble-no-attacker-bypass, area combat, server.js:653)

**Problem:** bubbleBlocks returns false whenever attacker is null or undefined. tickBomb explodes the bomb with `explodeAt(at, null, 'bomb', 18, 220, 60)`. Frags, ducks, chickens and gas clouds whose owner has disconnected resolve the owner to undefined. All of that damage goes straight through any bubble, against the rule 'nothing from outside hurts anyone inside'.

**Failure:** Verified with a frag. B stands in its bubble and A throws a frag 5 m away. If A stays connected the explosion is blocked ('bubhit' fx). If A disconnects 150 ms after throwing, the same explosion hits B for 56 dmg through the bubble, with no kill credit. The bomb case follows from the code: defenders sheltering in a bubble near a planted bomb take the full 220-dmg blast, because hurt(t, null, 'bomb', ...) never consults a bubble.

**Suggested fix:** Make the bubble test based on where the damage comes from. Pass the explosion or projectile origin into hurt()/damage() and block when the victim is inside a bubble and that origin (or the attacker, when known) is outside it. At minimum, treat a null attacker as outside the bubble, except for self, void and cough damage.

**Verifier notes:** The origin-based test is the right fix. Pass the explosion, projectile, hole or cloud position into hurt()/damage(), and block when the victim is inside a bubble and that origin is outside it. The fallback 'treat a null attacker as outside' is unsafe as written. hurt() is also called with attacker=null for self effects: the self knockback (0 dmg) in explodeAt/explode/tickHoles, and banana/peel self slips. Blocking null would break rocket and grenade jumps and self slips inside your own bubble. It would need a separate marker for world damage (the bomb) versus self.

## 26. [low] New rounds and matches revive players without resetting item charges or frost, while the client resets both
(id resetworld-keeps-item-frost, area combat, server.js:1330)

**Problem:** The respawn path in tick() clears frozenUntil, frost, ic and healLeft. resetWorld (used by startRound, newBombRound and map changes) only sets alive/hp/vel/pos and sends 'spawn'. The client's 'spawn' handler calls resetItems() and clears ME.frozenUntil and G.frost. So the client shows full charges and no frost while the server keeps the old state. A refused 'item' message gets no reply, so the client is never corrected.

**Failure:** Verified. A used its bubble, the match ended, and A got 'spawn' when the next match started 16 s later. A then pressed G for the bubble: a real client would play the throw and decrement its count, but the server sent nothing back (no 'ic', no 'bub+') because the bubble was still on its 28 s recharge. In Plant & Defuse, with 5 s between rounds, this hits anyone who used an item late in a round. In the same way, a player who is frozen or has frost stacks when an Online player changes the map stays frozen/frosted on the server and can be shattered while their own screen shows them unfrozen.

**Suggested fix:** Have resetWorld reset the same per-life state as the respawn path (p.ic = {}, frozenUntil = 0, frost = 0, healLeft = 0), or send the item/frost state after 'spawn'. Also send an 'ic' sync whenever an 'item' message is refused.

**Verifier notes:** The suggested fix is correct. In resetWorld also set p.ic = {}, p.frozenUntil = 0, p.frost = 0 and p.healLeft = 0. For parity, also clear p.burnUntil, p.sleepUntil and p.slipUntil, which the respawn path clears too. Also send an 'ic' with the real state when useItem refuses a valid id, so the client HUD can't drift.

## 27. [low] Killstreak picks can be swapped mid-streak, so one life can earn all six streaks
(id streak-pick-swap, area combat, server.js:1382)

**Problem:** The 'streaks' message replaces p.streaks immediately, with no respawn gating and no rate limit, and kill() checks the current picks on every kill. Swapping picks just before each threshold therefore earns streaks the player never had in their loadout of 3. The normal client sends 'streaks' whenever the loadout is edited mid-match (public/js/main.js:346), while weapon changes wait for respawn.

**Failure:** Verified. With picks [moonboots, chickenstrike, scythe], after kill 5 the client sent {t:'streaks', list:['spinbot','satellite','giantduck']}. 10 kills in a row then earned moonboots@3, chickenstrike@4, scythe@5, spinbot@6, satellite@7 and giantduck@10: all six in one life, and all stay in the pocket to deploy later.

**Suggested fix:** Store new picks as pending and apply them on respawn, like the weapon loadout, or ignore 'streaks' messages while p.streak > 0.

**Verifier notes:** Use pending picks. Do not 'ignore while p.streak > 0': the client never resends the list, so the server would keep the old picks forever while the client shows the new ones. For example, in 'streaks': `const v = validStreaks(m.list); if (!p.streak) p.streaks = v; else p.nextStreaks = v;`. In kill(), where t.streak is reset: `if (t.nextStreaks) { t.streaks = t.nextStreaks; t.nextStreaks = null; }`. The client should say the change applies after death, as it does for the weapon loadout.

## 28. [low] Black-hole pull and arrow status effects reach players inside a shield bubble
(id bubble-pull-status-bypass, area combat, server.js:1272)

**Problem:** tickHoles calls knock() and tag() directly instead of going through hurt(), so the duck's pull ignores bubbles and drags people out of the dome; once outside, the 3 dmg ticks and the blast apply. arrowHit applies sleep (line 1067) and burn (line 1065) before hurt() does its bubble check, so those effects land even though the arrow's damage is blocked.

**Failure:** Verified. With B inside its bubble, a duck item thrown 6 m away (outside the bubble) sent B 23 'kb' pull impulses of about 3.5 m/s each (roughly 80 m/s total toward the hole) within 2.5 s, which pulls a real client out of the dome. A sleep-tip arrow fired into the bubble produced 'bubhit' for the damage, but B still received {t:'sleep'} and was stuck for 2.5 s.

**Suggested fix:** In tickHoles, skip players for whom bubbleBlocks(owner, t) is true (together with the null-attacker fix), or send the pull through hurt(). In arrowHit, check bubbleBlocks and friendly before calling sleep() or burn().

**Verifier notes:** In tickHoles, add `if (this.bubbleBlocks(owner, t)) continue;` to the pull loop. Don't route the pull through hurt(): it would broadcast 'bubhit' every 100 ms per bubbled player, and a reverse card would bounce the pull onto the thrower. In arrowHit, check this.bubbleBlocks(owner, t) before sleep() and burn(). The friendly check is not needed there, because sweep() already skips teammates (server.js:1175).

## 29. [low] Using a medkit while overhealed drops HP to 100
(id medkit-strips-overheal, area combat, server.js:679)

**Problem:** tickItems clamps every heal tick with `Math.min(100, p.hp + a)`. When hp is above 100 (a hearts face card heals to 150, and heal() allows up to max(max, 100)), the first medkit tick cuts hp down to 100.

**Failure:** Verified. HP was 150 after a hearts face card. 150 ms after {t:'item', i:'medkit'} the snapshot showed hp 100: the player lost 50 HP by healing.

**Suggested fix:** Only heal below 100, e.g. `if (p.hp < 100) p.hp = Math.min(100, p.hp + a);`.

**Verifier notes:** The suggested fix is correct: `if (p.hp < 100) p.hp = Math.min(100, p.hp + a);`. healLeft still drains while overhealed, which is fine.

## 30. [low] Smoke clouds exist only on clients: bots see and shoot through them, late joiners never get them
(id smoke-not-server-side, area combat, server.js:1170)

**Problem:** When a smoke grenade's fuse ends, the server only broadcasts 'smoke' and keeps no record of it. The visibility checks in botTarget and botThink only raycast against map boxes, so bots keep aiming and firing through a cloud that blinds every human ('A thick cloud nobody can see through'). addHuman's welcome includes active bubbles but not active smokes.

**Failure:** In a Bots room a player throws a smoke between themselves and a bot. The bot's raycast finds nothing in the way, so for the 10 s the human can't see, the bot keeps tracking and firing at full accuracy. A player who joins while a cloud is active never sees it, while everyone else does. Traced in code; not reproduced.

**Suggested fix:** Keep smokes in a per-room map with expiry (like bubbles), count a ray through a smoke sphere as not visible in botTarget/botThink, and include active smokes in the welcome message.

**Verifier notes:** The suggested fix is right, but it also needs a client change: the client's welcome handler must create clouds from the new field (today it only handles the 'smoke' event). On the server, store {p, r, until} per room and expire them in tickItems. In both botTarget and botThink, treat a bot-eye-to-target segment that passes within r of a cloud center as not visible.

## 31. [low] Bots grapple onto tall roofs and then can't get off: the ledge guard treats any drop over ~5.5 m as the void
(id bot-roof-trap, area bots, server.js:478)

**Problem:** The new bot grapple (450-471) only hooks points above b.pos[1]-1, and the release hook-jump (601) regularly lands bots on rooftops (Bazaar blocks are 7-9 m; the market-hall roof is at 7.4 m). The ledge guard in botThink reverses any walk whose probe point 2.5 m ahead has no ground within 6 m below. On a roof that tall every edge, and the hall skylights, read as a cliff, so the bot oscillates near the edge. It can't hook downward to leave either.

**Failure:** A bot placed on the market-hall roof with site A as its goal was still on the roof at (6.2,7.4,26.9) after 60 s; its lowest y in that time was 7.4. In 10-minute sims there were 4-8 roof episodes per run lasting 10-76 s, e.g. a defender at (23.2,7.5,-49) and an attacker at (-13.8,9.5,0.3) that sat out the rest of the round.

**Suggested fix:** Let the ledge probe accept any ground below (e.g. raycast 40 m and block only if nothing is hit or the drop is below killY), or allow a drop when the goal is lower. Alternatively give stuck bots a downward or goal-directed hook.

**Verifier notes:** Probe down to killY: `raycast(probe, [0,-1,0], Math.max(6, probe[1] - this.map.killY), boxes)`, and turn back only when nothing is hit. There is no fall damage, so long drops are safe, and void maps stay protected. Verified with a patched harness copy (h/server_h2.mjs): the roof bot dropped off within 2-5 s and reached site A in all 6 runs. I rate it low rather than medium. Bots on roofs still target and shoot, the episode ends on death, a jump or knockback, and it only starts after a lucky hook-jump. It matters most for bomb carriers.

## 32. [low] Bots can never defuse a bomb planted on a prop inside a site; they stand motionless under it until it explodes
(id bot-cant-defuse-raised-bomb, area bots, server.js:515)

**Problem:** A defender bot stops moving (wx=wz=0, jump=false) and calls tryUse once its horizontal distance gl is under BOMB.defuseRange-0.6 = 2.0. tryUse (1683) needs the 3D distance dist3 < 2.6. siteAt (shared/modes.js:22) accepts plants up to 4 m above the site floor, and client-authoritative humans with the grapple easily reach B's wood stack (top 3.2), A's stacked crates (5.2) and the A canopy (5.6). From the floor the bot is 3.5-4.2 m away in 3D, so the defuse never starts, and the bot never jumps or moves.

**Failure:** Scripted test: a human attacker plants on top of B's wood stack, A's stacked crate and the A canopy. Defender bots walk to within 0.9-1.4 m horizontally (3D 3.5-4.2 m), then stand still for the whole fuse (about 77-88 bot-seconds each), and the bomb explodes every time. Control plants on the B paving and the A terrace were defused.

**Suggested fix:** Use the same 3D test in botGoal as tryUse does, and have the bot jump or grapple when the bomb is above reach. Alternatively limit siteAt's plant height to about the site floor + 1.5 m.

**Verifier notes:** The suggested 3D test in botGoal does not fix it on its own. From the floor the bot can never get within 2.6 m in 3D, so it would just push into the prop. Jumping or grappling is unreliable: tickBomb cancels the defuse once the defuser moves 1.6 m from where it started or leaves defuseRange+0.6, and nobody can hold a 5 s defuse mid-jump. Pick one rule and apply it in tryUse, tickBomb and objective.js canUse:
- either cap the plant height so every planted bomb can be defused from the site floor (for example require the planter's feet <= site.min[1] + 1.2 when planting, instead of siteAt's +4);
- or make the defuse check a vertical cylinder (horizontal < 2.6 and |dy| < about 4.5) and keep botGoal's horizontal check.
I rate it low: only a human can plant up there (with the grapple), it only happens in the Bots room, and the human is the one who benefits.

## 33. [low] Smoke bombs don't affect bots: the server keeps no smoke state and bot sight lines only test map boxes
(id bots-see-through-smoke, area bots, server.js:1170)

**Problem:** When a smokegren fuses, the server only broadcasts { t: 'smoke' } (1170) and keeps no cloud. botTarget's visibility raycast (393) and botThink's vis check before firing (422) only test this.boxes. Bots therefore see, track and shoot through a 10 s smoke cloud whose item description says nobody can see through it.

**Failure:** In a Bots room, a human throws smoke (G) between themselves and a bot and crosses the sightline. The bot's raycast is clear, so it keeps aiming and botFire()ing through the cloud as if it weren't there.

**Suggested fix:** Store active smoke clouds (position, radius ITEMS.smoke.r, expiry) in the room. Treat a bot's line of sight as blocked when the eye-to-target segment passes within r of an active cloud, both in botTarget scoring and in the vis check in botThink.

**Verifier notes:** The suggested fix is right. Keep this.smokes = [{p, r, until}] and push an entry at fuse time (pr.p, ITEMS.smoke.r, ITEMS.smoke.dur). Prune expired entries and clear the list in resetWorld or newBombRound; clients clear G.smokes on reset. Add a segment-sphere test (is the closest point on the eye-to-target segment within r of p?). Use it in both botTarget's visibility check and botThink's, so the bot loses seenAt and stops firing. Bullets don't need to be blocked, since smoke doesn't block human shots either.

## 34. [low] Frozen bots keep their grapple: they keep swinging and can be launched by the hook-jump while frozen
(id frozen-bot-keeps-rope, area bots, server.js:567)

**Problem:** frost() (658-674) zeroes x/z velocity on freeze but leaves ai.hook and b.g. stepBot skips botThink while frozen but still runs the rope pull, and at release applies the hook-jump v[1]=max(v1,0)*1.12+11. The client releases the local player's hook on freeze (main.js:959 releaseHook()), but bots keep theirs, so clients see a 'frozen' bot flying. resetWorld also leaves frozenUntil/frost set; only the respawn path at 1703 clears them.

**Failure:** Test: a bot frozen by its 4th snowball while on a rope traveled 12.4 m during the 2.4 s freeze. When its rope timed out at 0.88 s it was launched at vy=23.6 m/s while still frozen.

**Suggested fix:** When freezing, clear t.ai.hook and t.g (as the client does with releaseHook), and skip rope physics in stepBot while frozen. Clear frozenUntil/frost in resetWorld.

**Verifier notes:** When freezing in frost(), add `if (t.ai) t.ai.hook = null; t.g = null;`. botThink doesn't run while frozen, so no new hook can start and rope physics is skipped as a result. The resetWorld frozenUntil/frost point barely matters. The 5 s pause between bomb rounds and the 16 s vote both outlast the 2.4 s freeze. Only an instant setCfg map change can carry it over, and then a snowball could shatter a just-respawned human whose client shows them unfrozen. Clearing it in resetWorld, together with finding 9's field resets, costs nothing.

## 35. [low] resetWorld leaves bots attached to their old grapple anchor, so freshly spawned bots get dragged across the map (or toward a point from the previous map)
(id bot-rope-survives-reset, area bots, server.js:1325)

**Problem:** resetWorld (new bomb round, new match, setCfg map change) teleports bots to spawn and zeroes vel, but doesn't clear ai.hook or b.g; only kill() clears the hook. stepBot keeps pulling at HOOK.pull toward the stale anchor until hook.until (up to 2.6 s), and snapshots keep sending b.g, so clients draw a rope from the spawn to that point. After a map change via setCfg or the vote, the anchor is a coordinate on the previous map.

**Failure:** At a Bazaar bomb-round reset, a bot respawned in the attacker camp (-12,0.1,66) while still roped to its pre-reset anchor (-5,7,6.2), and was dragged 31 m out of spawn in 2.7 s. After setCfg skyline -> crate, three bots respawned on Crate still roped to Skyline anchors such as (-89,50.3,-91.1), with b.g broadcast in snapshots.

**Suggested fix:** In resetWorld set p.g = null and p.ai.hook = null for bots. Also reset the per-life fields the respawn path resets (slipUntil, burnUntil, sleepUntil, frozenUntil, frost, healLeft).

**Verifier notes:** The suggested fix is correct and complete. In resetWorld, for each player set p.g = null and `if (p.ai) { p.ai.hook = null; p.ai.route = null; }`. Also reset slipUntil, burnUntil, sleepUntil, frozenUntil, frost and healLeft, as the respawn path at line 1703 does. For humans, p.g is overwritten by the next client snapshot anyway, so setting it to null is harmless.

## 36. [low] After each match's team reshuffle, bots keep their old target for up to 1 s and aim, move and fire at players who are now teammates
(id bot-stale-target-after-team-shuffle, area bots, server.js:413)

**Problem:** startRound -> assignTeams (211-220) randomly reshuffles teams, but bots keep ai.target until the next retarget (400-1000 ms). botThink uses this.players.get(ai.target) without checking it is still an enemy, so the bot turns to it, strafes or chases it, may grapple toward it, and calls botFire on it. friendly() blocks the damage, but this breaks 'bots never target teammates': tracers and shots at teammates, and wasted reaction time.

**Failure:** 10 TDM match starts with 10 bots: 43 bots kept a target that had become a teammate, and 46 shots were fired at teammates in the first second after the reshuffle.

**Suggested fix:** After assignTeams/joinTeam set ai.target=0 and ai.retarget=0 for all bots, or have botThink drop a target for which friendly(b, t) is true.

**Verifier notes:** Real but cosmetic: under 1 s once per match, no damage, at most a couple of tracers at spawn, so it is close to unnoticeable. The cheapest fix is in botThink: `if (t && this.friendly(b, t)) { ai.target = 0; ai.seenAt = 0; }` before using t. Alternatively, reset target, retarget and seenAt for all bots in assignTeams.

## 37. [low] Item charges desync: resetWorld keeps server charges but the client refills on 'spawn', and rejected uses are silent
(id item-charge-desync-resetworld, area protocol, server.js:1325)

**Problem:** The tick respawn path resets per-life state (p.ic = {}, frozenUntil, frost, healLeft). resetWorld(), which runs on every startRound and every Plant & Defuse round (newBombRound), only sets alive/hp/pos and sends 'spawn'. The client's 'spawn' handler calls resetItems(), so it shows full charges while the server keeps the old ones. When the server refuses a use (c.n <= 0) it returns without sending 'ic', so the client is never corrected. In the other direction, W.ic is not reset on 'welcome', so after quitting and rejoining the client shows spent charges while the server has a fresh set. frozenUntil and frost are also not cleared in resetWorld (for example on a Match Settings map change), so a player can still be frozen on the server, and a snowball right after the reset shatters them.

**Failure:** Verified in a bots room on Bazaar in P&D with JF_BOMB_ROUND=3: two {t:'item',i:'frag'} give ic n=1, then n=0. The bomb round times out, the next round sends 'spawn', and the real client would now show 2/2. Another {t:'item',i:'frag'} gets no 'ic' reply and no projectile. The real client plays the toss animation and decrements its own count. This happens every round to anyone who threw grenades in the previous ~16-32 s.

**Suggested fix:** Move the per-life reset (p.ic={}, frozenUntil=0, frost=0, healLeft=0, burn/slip/sleep) into a helper and call it from both the respawn tick and resetWorld. Call resetItems() on 'welcome'. In useItem, send {t:'ic', ...} on rejection too so the client resyncs.

**Verifier notes:** The suggested fix is right. Add a resetLife(p) helper that clears slipUntil, burnUntil, sleepUntil, frozenUntil, frost, ic and healLeft, and call it from both the respawn tick and the resetWorld loop. Call resetItems() in the client's welcome handler (or in resetWorldState). When useItem refuses (c.n <= 0 or the 400 ms guard), send {t:'ic', i, n:c.n, next:c.next ? c.next-now() : 0}; the client's 'ic' handler already overwrites its count. I rated it low because the server state stays consistent and the client recovers after the next good use. The visible effect is one or two dead G presses at round start (toss animation, nothing thrown).

## 38. [low] Snowball frost/freeze/shatter ignores round-over, spawn protection and reverse card
(id shatter-ignores-round-over, area protocol, server.js:663)

**Problem:** damage() refuses all non-void damage after the round ends and during spawn protection. The snowball branch, however, always calls frost() when the target is alive and not in a bubble. frost() freezes the target at 4 stacks and on the next hit calls this.kill(t, owner, 'snowball') directly, skipping every damage() gate. The kill bumps killer.kills and streak (so killstreak pocket rewards can be earned), account kills/xp, and katana growth. Frost also applies to a reverse-card holder and to a freshly spawned player.

**Failure:** Verified with JF_ROUND_KILLS=1 JF_TARGET=1. A kills V to end the round, so the vote screen is up and damage is disabled. After V respawns, A throws 6 snowballs: V gets frost×3, then 'freeze', then fx 'shatter', then a kill credited to A, all during the round-over. The frozen victim also cannot move during the vote.

**Suggested fix:** In the snowball branch and in frost(), return early when this.round && this.round.over, inside spawn protection, or when reverse applies. Alternatively, deliver the shatter through damage(t, 9999, owner, 'snowball') so it goes through the same gates.

**Verifier notes:** Fix both halves. (1) In the snowball branch, skip frost when this.round && this.round.over, when !v.t.isBot && now()-v.t.spawnT < 1200, and when v.t.reverseUntil > now(). In that last case hurt() has already reflected the 9 dmg, so no frost should land on the card holder. (2) In frost(), deliver the shatter through this.damage(t, 9999, owner, 'snowball') or hurt() instead of kill(), so every damage gate applies. Doing only (2), as the alternative suggests, would still let players be frozen during the vote.

## 39. [low] Changing the map during Plant & Defuse leaves a DM round with a 1-hour clock (and stale tags across map changes)
(id mapchange-bomb-hour-round, area protocol, server.js:1306)

**Problem:** setCfg's new fallback switches game to 'dm' and sets bomb=null when the new map has no sites. this.round is still the bomb round, whose ends startRound set to now+3600 s, with target 20. The match turns into a DM that only ends at 20 kills or after an hour, and there is no vote until then. In the Online room any player can change the map from Match Settings, so anyone can trigger this. In the same path, resetWorld and the client's 'cfg'/'clear' handlers never clear tags, so after a map change in Tags the old tags float at their old coordinates on the new map and can still be collected.

**Failure:** Verified in a bots room on Bazaar in P&D. Sending {t:'cfg',map:'crate'} changes the game to dm, but round.left stays at 3598 s and target at 15 (bots). In Online it would be 20, with the HUD showing 'first to 20 · 59:58'.

**Suggested fix:** When setCfg changes the game, start a fresh round (startRound-like reset of round.ends/target/score). Call clearTags() (and clear bubbles) on map change.

**Verifier notes:** On the fallback path only, replace assignTeams() + resetWorld with this.startRound(). It resets round.ends/target/score, clears tags, assigns teams, resets the world and broadcasts the round start. Limiting it to the fallback means a plain DM map change doesn't wipe kills. On every map change, also call clearTags() and remove bubbles (broadcast bubx). Otherwise both stay collectable or protective at the old coordinates on the new map. The client could also clear G.smokes when the map changes.

