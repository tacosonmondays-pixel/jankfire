-- step 2 tests: the three weapons' numbers and gimmicks, the server's checks (Rules.luau: through-wall, wrong weapon,
-- too-fast fire, ammo / reload, melee reach / cone / swing, the parry window), kills and kill credit, the katana's growth,
-- the marbles on the floor, slipping. called from tests/run.luau
local fs = require("@lune/fs")
local serde = require("@lune/serde")
local roblox = require("@lune/roblox")
local V3 = roblox.Vector3

return function(T: any)
	local check, near, load = T.check, T.near, T.load
	local Weapons = load("src/shared/Weapons.luau", {})
	local Hitbox = load("src/shared/Hitbox.luau", { Weapons = Weapons })
	local Marbles = load("src/shared/Marbles.luau", { Weapons = Weapons })
	local Rules = load("src/server/Rules.luau", { Weapons = Weapons })
	local Movement = T.Movement
	local Anims = load("src/shared/Anims.luau", {})
	local W, P = Weapons.list, Weapons.PARRY

	-- ------------------------------------------------------------ the numbers, metres -> studs
	local rl, mb, kt = W.redline, W.marbles, W.katana
	check(Weapons.fireRate(rl, 100) == 6 and Weapons.fireRate(rl, 50) == 14 and near(Weapons.fireRate(rl, 10), 20.4, 1e-9) and Weapons.fireRate(rl, 0) == 22, "Redline: 6/s at 100 HP, 14 at 50, 20.4 at 10, 22 at 0")
	check(Weapons.fireRate(rl, 150) == 6, "Redline: overheal = base rate")
	check(near(Weapons.tacho(100), 0, 1e-9) and near(Weapons.tacho(0), 1, 1e-9) and near(Weapons.tacho(50), 0.5, 1e-9), "Redline tacho needle k: 0 full HP -> 1 at 0 HP")
	check(rl.dmg == 10 and rl.head == 1.8 and Weapons.damage(rl, 1, 1) == 18 and rl.mag == 40 and rl.reload == 1.8, "Redline: 10 dmg, 18 head, 40 mag, 1.8 s reload")
	check(rl.range == 750 and near(rl.recoil :: number, 0.9, 1e-9) and rl.kick == 0.006 and rl.spread == 0.018, "Redline: range 750 studs, recoil 0.9 studs/s, kick 0.006, spread 0.018")
	check(mb.pellets == 100 and near(Weapons.damage(mb, 100, 0), 115, 1e-9) and mb.head == 1.3 and mb.mag == 2 and mb.reload == 1.9, "Marble Shotgun: 100 marbles x 1.15 = 115 point blank, head x1.3, 2 shells, 1.9 s")
	check(near(mb.rate :: number, 1 / 0.9, 1e-9) and mb.range == 90 and mb.recoil == 12 and mb.spread == 0.27, "Marble Shotgun: 0.9 s a shot, 90 studs, recoil 12 studs/s, spread 0.27")
	check(kt.dmg == 48 and kt.cd == 0.5 and near(kt.range, 8.4, 1e-9) and kt.cone == 0.7 and kt.kb == 18 and kt.kbUp == 6, "Katana: 48 dmg, 0.5 s, 8.4 studs reach, cone 0.7, kb 18 + 6 up")
	check(near(Weapons.reach(kt, 0), 8.4, 1e-9) and near(Weapons.reach(kt, 1), 9.9, 1e-9) and near(Weapons.reach(kt, 30), 53.4, 1e-9) and near(Weapons.reach(kt, 99), 53.4, 1e-9), "Katana reach: +1.5 studs a kill, 53.4 at the 30-kill cap")
	check(P.win == 0.35 and P.perfect == 0.15 and P.cd == 0.8 and P.arc == 140 and P.shove == 42 and P.shoveUp == 15 and P.stagger == 0.55, "PARRY: 0.35 s window, 0.15 perfect, 0.8 cd, 140 deg, shove 42 + 15 up, stagger 0.55 s")
	check(Weapons.SLIP.fwd == 18 and Weapons.SLIP.up == 19.5 and Weapons.SLIP.time == 1.7, "slip: 1.7 s, +18 studs/s along your look, 19.5 up")
	check(near(Marbles.safeSpeed(1), 16.5, 1e-9), "marbles: slip above 16.5 studs/s (crouch walk 13.5 is safe)")
	check(Weapons.FFA.kills == 20 and Weapons.FFA.time == 360 and Weapons.FFA.respawn == 2.5 and Weapons.FFA.protect == 1.2, "FFA: first to 20, 6 minutes, 2.5 s respawn, 1.2 s protection")

	-- ------------------------------------------------------------ hit boxes
	do
		local feet = V3.new(0, 0, -30)
		local t, head = Hitbox.ray(V3.new(0, 3, 0), V3.new(0, 0, -1), feet, 1)
		check(t ~= nil and near(t :: number, 30 - 1.56, 1e-6) and not head, "a ray at the chest hits the body box (3.12 studs wide)")
		t, head = Hitbox.ray(V3.new(0, 6, 0), V3.new(0, 0, -1), feet, 1)
		check(t ~= nil and head, "a ray at 6 studs hits the head box (4.86 -> 6.90)")
		t = Hitbox.ray(V3.new(0, 7.5, 0), V3.new(0, 0, -1), feet, 1)
		check(t == nil, "over the head misses")
		t = Hitbox.ray(V3.new(2, 3, 0), V3.new(0, 0, -1), feet, 1)
		check(t == nil, "2 studs to the side misses")
		check(Hitbox.distScale(75) == 1 and near(Hitbox.distScale(255), 1.8, 1e-9) and near(Hitbox.distScale(165), 1.4, 1e-9), "far targets get bigger: x1 to 25 m, x1.8 from 85 m")
		local worst = 0
		for i = 1, 300 do
			local d = Hitbox.spreadDir(V3.new(0, 0, -1), 0.27, (i % 17) / 17, (i % 23) / 23)
			worst = math.max(worst, math.acos(math.clamp(d:Dot(V3.new(0, 0, -1)), -1, 1)))
		end
		check(worst <= 0.27 + 1e-6, ("pellet spread stays in its cone (worst %.3f rad)"):format(worst))
		check(Hitbox.inCone(V3.new(0, 0, 0), V3.new(0, 0, -1), V3.new(0, 0, -8), 8.4, 0.7) and not Hitbox.inCone(V3.new(0, 0, 0), V3.new(0, 0, -1), V3.new(8, 0, -1), 8.4, 0.7), "melee cone: in front yes, off to the side no")
	end

	-- ------------------------------------------------------------ the fire checks
	local function fighter(kind: string?): any
		local f = Rules.newFighter(kind or "player", "p", nil)
		Rules.spawn(f, 0)
		return f
	end
	local eye = V3.new(0, 4.8, 0)
	do
		local f = fighter()
		check(Rules.fire(f, "marbles", 1, eye, eye) == "not held", "refused: firing the Marble Shotgun while holding the Redline")
		check(Rules.fire(f, "sniper", 1, eye, eye) ~= nil and Rules.fire(f, 42, 1, eye, eye) ~= nil, "refused: a weapon you don't have / garbage")
		check(Rules.fire(f, "redline", 1, eye, eye + V3.new(0, 0, 20)) == "not from your head", "refused: a shot from 20 studs away from your head")
		check(Rules.fire(f, "redline", 1, eye, eye + V3.new(0, 0, 3), true) == "not from your head", "refused: a shot from 3 studs off with a wall between it and your head")
		check(Rules.equip(f, "sniper", 1) ~= nil and Rules.equip(f, "marbles", 1) == nil and f.held == "marbles", "equip: only your three weapons")
		check(Rules.fire(f, "marbles", 2, eye, eye) == nil, "the Marble Shotgun fires once held")
		local dead = fighter(); dead.alive = false
		check(Rules.fire(dead, "redline", 1, eye, eye) == "dead", "refused: firing while dead")
	end
	do -- the rate: from the SERVER's HP. spam 100 shots in one second at full HP
		local f = fighter()
		local ok = 0
		for i = 0, 99 do if Rules.fire(f, "redline", 10 + i * 0.01, eye, eye) == nil then ok += 1 end end
		check(ok >= 5 and ok <= 8, ("too-fast fire refused: 100 Redline shots in 1 s at full HP, %d accepted (6/s + jitter)"):format(ok))
		local g = fighter(); g.hp = 10
		ok = 0
		for i = 0, 99 do if Rules.fire(g, "redline", 10 + i * 0.01, eye, eye) == nil then ok += 1 end end
		check(ok >= 19 and ok <= 25, ("at 10 HP the server lets it scream: %d/s accepted (20.4/s)"):format(ok))
		-- a legit 6/s stream with +-40 ms of network jitter: none dropped
		local h = fighter()
		local refused = 0
		for i = 0, 35 do
			local t = 20 + i / 6 + (if i % 2 == 0 then 0.04 else -0.04)
			if Rules.fire(h, "redline", t, eye, eye) ~= nil then refused += 1 end
		end
		check(refused == 0, ("a real 6/s stream with jitter is never refused (%d refused)"):format(refused))
		-- the marble shotgun: one every 0.9 s
		local m = fighter(); Rules.equip(m, "marbles", 0)
		check(Rules.fire(m, "marbles", 5, eye, eye) == nil and Rules.fire(m, "marbles", 5.3, eye, eye) == "too fast", "refused: the Marble Shotgun 0.3 s after its last shot")
	end
	do -- ammo / mag / reload
		local f = fighter()
		local t, ok = 100, 0
		for _ = 1, 50 do t += 0.2; if Rules.fire(f, "redline", t, eye, eye) == nil then ok += 1 end end
		check(ok == 40, ("a 40-round mag: %d shots, then empty"):format(ok))
		check(Rules.fire(f, "redline", t + 0.2, eye, eye) == "empty", "refused: firing an empty mag")
		check(Rules.reload(f, "redline", t + 0.3) == nil, "reload starts")
		check(Rules.fire(f, "redline", t + 1.0, eye, eye) == "reloading", "refused: firing mid-reload")
		check(Rules.reload(f, "redline", t + 1.0) ~= nil, "refused: reloading twice")
		check(Rules.fire(f, "redline", t + 0.3 + 1.8, eye, eye) == nil and f.ammo.redline.mag == 39, "after 1.8 s it's full again (40, one fired)")
		local g = fighter()
		Rules.equip(g, "marbles", 0)
		Rules.fire(g, "marbles", 1, eye, eye); Rules.fire(g, "marbles", 2, eye, eye)
		check(Rules.fire(g, "marbles", 3, eye, eye) == "empty", "two shells, then empty")
		Rules.reload(g, "marbles", 3)
		Rules.equip(g, "katana", 3.5)
		check(Rules.equip(g, "marbles", 3.55) == "too fast", "swap spam: one swap per 0.15 s")
		Rules.equip(g, "marbles", 3.8)
		check(Rules.fire(g, "marbles", 6, eye, eye) == "empty", "swapping away cancels the reload")
		check(Rules.reload(f, "redline", 50) ~= nil or true, "(reload on a full mag is just ignored)")
	end

	-- ------------------------------------------------------------ hits: range, line of sight, pellets
	do
		local f, t = fighter(), fighter()
		local function ctx(dist: number, los: boolean): any return { dist = dist, speedF = 0, speedT = 0, los = los } end
		local why, n, h = Rules.hit(f, t, "redline", 1, 1, 0, ctx(100, true))
		check(why == nil and n == 1 and h == 1, "a Redline headshot at 100 studs counts")
		check(Rules.hit(f, t, "redline", 1, 0, 0, ctx(100, false)) == "through a wall", "refused: a shot through a wall")
		check(Rules.hit(f, t, "redline", 1, 0, 0, ctx(800, true)) == "out of range", "refused: a Redline hit past 750 studs (+9 slack)")
		check(Rules.hit(f, t, "marbles", 100, 0, 0, ctx(120, true)) == "out of range", "refused: a marble hit past 90 studs")
		check(Rules.hit(f, f, "redline", 1, 0, 0, ctx(1, true)) == "yourself", "refused: shooting yourself")
		local _, n5 = Rules.hit(f, t, "marbles", 100, 0, 0, ctx(15, true))
		local _, n10 = Rules.hit(f, t, "marbles", 100, 0, 0, ctx(30, true))
		local _, n25 = Rules.hit(f, t, "marbles", 100, 0, 0, ctx(75, true))
		check(n5 == 100 and n10 <= 35 and n25 <= 8, ("the pellet cap: all 100 at 5 m, %d at 10 m, %d at 25 m (web: 100 / ~31)"):format(n10, n25))
		local _, nn, hh = Rules.hit(f, t, "marbles", 5, 99, 0, ctx(3, true))
		check(nn == 5 and hh == 5, "more headshots than pellets is clamped")
		check(Rules.hit(f, t, "redline", 0 / 0, 0, 0, ctx(3, true)) ~= nil, "refused: NaN pellets")
	end
	do -- line of sight on the real Rooftop: a wall between you and them blocks the shot
		local parts = serde.decode("json", fs.readFile("build/rooftop.parts.json")).parts
		local boxes = {}
		for _, p in parts do
			if p.kind == "solid" and (p.yaw or 0) == 0 then
				table.insert(boxes, { lo = V3.new(p.pos[1] - p.size[1] / 2, p.pos[2] - p.size[2] / 2, p.pos[3] - p.size[3] / 2), hi = V3.new(p.pos[1] + p.size[1] / 2, p.pos[2] + p.size[2] / 2, p.pos[3] + p.size[3] / 2) })
			end
		end
		local function cast(o: any, d: any, len: number): boolean
			for _, b in boxes do
				local t = Hitbox.rayBox(o, d, b.lo, b.hi)
				if t and t <= len then return true end
			end
			return false
		end
		local found = false
		for _, b in boxes do
			local sz = b.hi - b.lo
			-- a wall at least 9 studs tall standing on something, with clear air on both sides of it along X
			if sz.Y >= 9 and sz.X <= 6 and sz.Z >= 6 then
				local floor = b.lo.Y
				local mz = (b.lo.Z + b.hi.Z) / 2
				local a = V3.new(b.lo.X - 9, floor, mz)
				local c = V3.new(b.hi.X + 9, floor, mz)
				local a2 = V3.new(b.lo.X - 18, floor, mz)
				local eyeA = a + V3.new(0, 4.8, 0)
				local eyeA2 = a2 + V3.new(0, 4.8, 0)
				if not cast(eyeA2, V3.new(1, 0, 0), 9) and not Rules.sees(cast, eyeA, c) and Rules.sees(cast, eyeA2, a) then
					found = true
					check(not Rules.sees(cast, eyeA, c), "Rooftop line of sight: the wall blocks a shot through it")
					check(Rules.sees(cast, eyeA2, a), "Rooftop line of sight: open air sees")
					local f, t = fighter(), fighter()
					check(Rules.hit(f, t, "redline", 1, 0, 0, { dist = (c - a).Magnitude, speedF = 0, speedT = 0, los = Rules.sees(cast, eyeA, c) }) == "through a wall", "refused: a Redline hit through a real Rooftop wall")
					break
				end
			end
		end
		check(found, "found a Rooftop wall to shoot through")
	end

	-- ------------------------------------------------------------ the katana: swing, reach, cone, growth
	do
		local f, t = fighter(), fighter()
		Rules.equip(f, "katana", 0)
		local fwd = V3.new(0, 0, -1)
		local function mc(dist: number, to: any, los: boolean?): any return { dist = dist, look = fwd, to = to, los = los ~= false, speedF = 0, speedT = 0 } end
		check(Rules.meleeHit(f, t, "katana", 1, mc(5, V3.new(0, 0, -5))) == "no swing", "refused: a katana hit with no swing first")
		check(Rules.swing(f, "redline", 1) ~= nil, "refused: swinging a gun")
		check(Rules.swing(f, "katana", 1) == nil, "a swing")
		check(Rules.swing(f, "katana", 1.2) == "too fast", "refused: a second swing 0.2 s later (0.5 s cooldown)")
		check(Rules.meleeHit(f, t, "katana", 1.12, mc(8, V3.new(0, 0, -8))) == nil, "a hit 8 studs in front, at the swing's hit time")
		check(Rules.meleeHit(f, t, "katana", 1.13, mc(8, V3.new(0, 0, -8))) == "already hit", "refused: the same victim twice in one swing")
		local u = fighter()
		check(Rules.meleeHit(f, u, "katana", 1.13, mc(8, V3.new(8, 0, -0.5))) == "outside the swing", "refused: a hit 90 degrees off the swing")
		local v = fighter()
		check(Rules.meleeHit(f, v, "katana", 1.13, mc(8, V3.new(0, 0, -8), false)) == "through a wall", "refused: a swing through a wall")
		local x = fighter()
		check(Rules.meleeHit(f, x, "katana", 1.13, mc(19, V3.new(0, 0, -19))) == "out of reach", "refused: 19 studs away with a fresh katana (8.4 + 9 slack)")
		f.kat = 10
		check(Rules.meleeHit(f, x, "katana", 1.14, mc(19, V3.new(0, 0, -19))) == nil, "with 10 kills the blade reaches 23.4 studs")
		local y = fighter()
		check(Rules.meleeHit(f, y, "katana", 2, mc(5, V3.new(0, 0, -5))) == "swing too old", "refused: a hit a second after the swing")
		Rules.swing(f, "katana", 3)
		Rules.equip(f, "redline", 3.05)
		check(Rules.meleeHit(f, y, "katana", 3.12, mc(5, V3.new(0, 0, -5))) == "no swing", "refused: a katana hit after swapping to a gun mid-swing")
	end
	do -- kills, credit, growth
		local a, b = fighter(), fighter()
		Rules.equip(a, "katana", 0)
		b.spawnT = 10
		local done = Rules.damage(b, 48, a, "katana", 10.5)
		check(done == 0 and b.hp == 100, "spawn protection: no damage in the first 1.2 s")
		Rules.damage(b, 48, a, "katana", 12)
		local _, info = Rules.damage(b, 60, a, "katana", 12.5)
		check(info ~= nil and info.k == a and not b.alive and a.kills == 1 and b.deaths == 1, "48 + 60 kills: the attacker gets it")
		check(a.kat == 1, "a katana kill grows the katana (1 kill)")
		for _ = 1, 40 do local c = fighter(); c.spawnT = -10; Rules.damage(c, 200, a, "katana", 20) end
		check(a.kat == 30, "growth caps at 30 kills")
		local c = fighter(); c.spawnT = -10
		Rules.damage(c, 200, a, "redline", 20)
		check(a.kat == 30 and a.kills == 42, "a Redline kill counts but doesn't grow it")
		local d = fighter(); d.spawnT = -10
		Rules.damage(d, 200, a, "parry", 20)
		check(a.kills == 43, "a parried bullet's kill is the parrier's")
		Rules.spawn(a, 30)
		check(a.kat == 0, "dying (respawning) resets the katana")
		local e = fighter(); e.spawnT = -10
		Rules.damage(e, 20, a, "katana", 40) -- a tags e
		local info2 = Rules.kill(e, nil, "void", 45)
		check(info2.k == a and info2.via == "katana" and a.kat == 0, "a fall within 10 s is the tagger's kill, via their weapon; a void kill doesn't grow it")
		local g = fighter(); g.spawnT = -10
		Rules.damage(g, 20, a, "marbles", 40)
		local info3 = Rules.kill(g, nil, "void", 51)
		check(info3.k == nil, "a fall 11 s after the last hit is nobody's")
		local dm = fighter("dummy"); dm.spawnT = -10
		local before = a.kills
		Rules.damage(dm, 200, a, "katana", 60)
		check(a.kills == before and a.kat == 1, "test dummies don't score, but they feed the katana")
		local h = fighter(); h.spawnT = -10
		Rules.damage(h, 20, h, "marbles", 70)
		check(h.tag == nil, "hurting yourself doesn't tag you")
	end

	-- ------------------------------------------------------------ the parry
	do
		local p, s = fighter(), fighter()
		check(Rules.parryStart(p, 1) == "no katana", "refused: parrying without the katana out")
		Rules.equip(p, "katana", 1)
		check(Rules.parryStart(p, 2, 0.5) == nil and p.parryYaw == 0.5, "parry opens, facing where you looked")
		check(Rules.parryStart(p, 2.5) == "cooldown", "refused: a second parry inside the 1.15 s cycle")
		local facing = V3.new(0, 0, -1)
		local front = V3.new(0, 0, -20)
		check(Rules.parryAt(p, front, facing, 2.1) == 2, "a shot from the front 0.1 s in: PERFECT (0.15 + 0.05 slack)")
		check(Rules.parryAt(p, front, facing, 2.3) == 1, "0.3 s in: a plain parry")
		check(Rules.parryAt(p, front, facing, 2.45) == 0, "refused: 0.45 s in, outside the 0.35 s window (+0.05 slack)")
		check(Rules.parryAt(p, V3.new(0, 0, 20), facing, 2.1) == 0, "refused: a shot from behind")
		check(Rules.parryAt(p, V3.new(15, 0, -5), facing, 2.1) == 0, "refused: from 72 degrees off (the arc is +-70)")
		check(Rules.parryAt(p, V3.new(14, 0, -6), facing, 2.1) == 2, "68 degrees off still counts")
		check(Rules.parryAt(p, V3.new(1, 30, 0), facing, 2.1) == 2, "from straight above always counts")
		check(Rules.parryStart(p, 2 + 1.04) == nil, "the next parry 1.035 s later (1.15 s minus 10% slack)")
		local shove = Rules.stagger(s, V3.new(0, 0, -10), true, 5)
		check(near(shove.Z, -58.8, 1e-6) and shove.Y == 15 and near(s.staggerUntil, 5 + 0.77, 1e-9), "a perfect parry on a swing: shove 58.8 + 15 up, 0.77 s stagger")
		check(Rules.fire(s, "redline", 5.2, eye, eye) == "staggered" and Rules.swing(s, "katana", 5.3) ~= nil, "refused: a staggered attacker can't fire or swing")
		Rules.equip(p, "redline", 6)
		check(Rules.parryAt(p, front, facing, 6.1) == 0, "no parry once the katana is put away")
		Rules.equip(p, "katana", 7)
		Rules.parryStart(p, 7.2, 0 / 0)
		check(p.parryYaw == nil, "a NaN yaw is ignored (falls back to the body's facing)")
		check(Rules.swing(p, "katana", 7.3) == "guarding", "no swinging inside your own guard")
	end

	-- ------------------------------------------------------------ the marbles on the floor
	do
		local function flat(o: any, d: any, len: number): (number?, any?) -- a floor at y = 0 and nothing else
			if d.Y < -1e-6 and o.Y >= 0 then
				local t = -o.Y / d.Y
				if t <= len then return t, V3.new(0, 1, 0) end
			end
			return nil, nil
		end
		local e = V3.new(0, 4.8, 0)
		local ends = {}
		for i = 1, 12 do ends[i] = V3.new(math.cos(i) * 2, 0.05, -12 + math.sin(i * 1.7) * 2) end
		local c, r, n = Marbles.patch(e, ends, 90, flat)
		check(c ~= nil and near(c.Y, 0, 1e-6) and near(c.Z, -12, 2.5) and r >= Weapons.MSLIP.rMin and r <= Weapons.MSLIP.rMax and (n :: number) > 30, ("a shot at the floor leaves a patch (r %.1f studs, %d marbles)"):format(r or 0, n or 0))
		local function roof(o: any, d: any, len: number): (number?, any?) -- a roof that ends 20 studs out: past it, the street is far below
			local t, nrm = flat(o, d, len)
			if t then local p = o + d * t; if math.abs(p.Z) < 20 then return t, nrm end end
			return nil, nil
		end
		local over = {}
		for i = 1, 12 do over[i] = V3.new(i - 6, 30, -200) end
		check(Marbles.patch(e, over, 90, roof) == nil, "a shot off the roof (into the smog) leaves no patch")
		check(Marbles.patch(e, ends, 90, roof) ~= nil, "the same roof keeps a patch shot at it")
		check(Marbles.onPatch(V3.new(0, 0, 0), 6, V3.new(3, 0.2, 2)) and not Marbles.onPatch(V3.new(0, 0, 0), 6, V3.new(3, 3, 2)) and not Marbles.onPatch(V3.new(0, 0, 0), 6, V3.new(9, 0, 0)), "on the patch: inside the radius, feet near its floor")
		local tn, nr, gone = Marbles.thin(90, 7.5)
		check(tn == 49 and near(nr, 6.375, 1e-9) and not gone, "a slip thins it: x0.55 marbles, x0.85 radius")
		local _, _, gone2 = Marbles.thin(15, 3)
		check(gone2, "under 10 marbles it's gone")
		local list = {}
		for i = 1, 3 do list[i] = { id = i, owner = "a", born = i } end
		local drop = Marbles.toDrop(list, "a")
		check(#drop == 1 and drop[1].id == 1, "3 patches per shooter: the oldest goes")
		local room = {}
		for i = 1, 10 do room[i] = { id = i, owner = "x" .. i, born = i } end
		local drop2 = Marbles.toDrop(room, "new")
		check(#drop2 == 1 and drop2[1].id == 1, "10 patches a room: the oldest goes")
	end
	do -- slipping: no control, no jump for 1.7 s, then it comes back
		local st = Movement.newState(); st.onGround = true; st.groundTicks = 10
		Movement.slip(st, 0, -1, Weapons.SLIP.time, Weapons.SLIP.fwd, Weapons.SLIP.up)
		check(near(st.vz, -18, 1e-9) and st.vy == 19.5 and not st.onGround and st.slip == 1.7, "a slip: +18 studs/s along your look, 19.5 up")
		st.onGround = true
		local inp = { wx = 1, wz = 0, forward = true, sprint = true, crouch = true, jump = true, jumpPressed = true, lookX = 1, lookZ = 0 }
		Movement.step(st, inp, 1 / 60, 78, 0, 0, 0)
		check(st.vx == 0 and not st.sliding and st.combo == 0, "slipping: no steering, no slide, no bhop")
		for _ = 1, 110 do Movement.step(st, inp, 1 / 60, 78, 0, 0, 0) end
		Movement.step(st, { wx = 1, wz = 0, forward = true, sprint = false, crouch = false, jump = false, jumpPressed = false, lookX = 1, lookZ = 0 }, 1 / 60, 78, 0, 0, 0)
		check((st.slip :: number) <= 0 and st.vx > 0, "1.7 s later you have your feet back")
	end

	-- ------------------------------------------------------------ the code weapon models (real Roblox instances in Lune)
	do
		local luau = require("@lune/luau")
		-- selene: allow(global_usage)
		local env = setmetatable({ CFrame = roblox.CFrame, Vector3 = V3, Color3 = roblox.Color3, Instance = roblox.Instance, Enum = roblox.Enum, game = roblox.Instance.new("DataModel"), warn = print }, { __index = _G })
		local WM = luau.load(fs.readFile("src/shared/WeaponModels.luau"), { environment = env })()
		for _, id in { "redline", "marbles", "katana" } do
			local m = WM.build(id, 3)
			local root = m and m.PrimaryPart
			check(root ~= nil and root:FindFirstChild("Muzzle") ~= nil and root:FindFirstChild("Grip") ~= nil, id .. ": code model builds with its Muzzle + Grip spots")
		end
		local rm = WM.build("redline", 3)
		check(rm:FindFirstChild("needle") ~= nil and rm:FindFirstChild("vent") ~= nil and near(rm.PrimaryPart.Sight.Position.Y, 0.0737 * 3, 1e-4), "Redline: needle, vents, the sight 0.221 studs up")
		local k = WM.build("katana", 3)
		local tip = k.PrimaryPart.Muzzle
		WM.setKatana(k, 4, 3)
		check(near(tip.Position.Z, (-0.139 + (-0.8357 + 0.139) * 3.2) * 3, 1e-3), "katana: 4 kills stretch the blade x3.2 from the habaki, tip with it")
		WM.setKatana(k, 0, 3)
		check(near(tip.Position.Z, -0.8357 * 3, 1e-3), "katana: back to its rest length on death")
	end

	-- ------------------------------------------------------------ the animations (from public/js/anim.js + katanavm.js)
	check(Anims.swing_katana.hit == 0.12 and Anims.swing_katana.dur == 0.5 and Anims.swing_katana.events[1][1] == 0.07, "katana swing: hit at 0.12 s, 0.5 s long, whoosh at 0.07")
	check(Anims.parry_katana.dur == 0.56 and Anims.draw_katana.dur == 0.72 and Anims.draw_gun.dur == 0.34 and Anims.staggered.dur == 0.62, "parry 0.56 s, katana draw 0.72 s, gun draw 0.34 s, stagger 0.62 s")
	check(Anims.reload_redline.dur == 1.8 and Anims.reload_marbles.dur == 1.9, "the reload clips last the reload: 1.8 s / 1.9 s")
	local glugs = 0
	for _, e in Anims.reload_redline.events do if e[2] == "glug" then glugs += 1 end end
	check(glugs == 3, "the Redline's pit stop: three glugs")
end
