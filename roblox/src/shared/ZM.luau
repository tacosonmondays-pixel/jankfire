--!strict
-- ZOMBIES: the rules and numbers (web shared/zombies.js, zmshop.js, zmlimbs.js), shared so the server (which runs the
-- mode, server/Zombies.luau) and the client (prompts, prices, the HUD) always agree. distances in studs (web metres x
-- S), times in seconds. the map contract (what a zombies map carries) is roblox/docs/ZOMBIES.md
local Weapons = require(script.Parent:WaitForChild("Weapons"))

local ZM = {}
local S = Weapons.S
ZM.S = S

ZM.R = {
	start = 500, hit = 10, kill = 60, bonus = 100, -- credits: start with 500, +10 a hit, +60 a kill, +100 for a headshot or melee kill
	hitCap = 10, hitGap = 0.18, -- a zombie pays for its first 10 hits only, one per 0.18 s per player
	first = 6, rest = 10, -- s before round 1 / between rounds
	hold = 0.3, power = 1, revive = 3, bleed = 30, -- hold Q to buy / to throw the power switch / to revive; a downed friend lasts
	regenAfter = 4, regen = 25, -- 4 s without a hit and you heal 25 HP a second
	swipe = 15, swipeRamp = 1, swipeMax = 34, swipeCd = 1.1, windup = 0.35, iframe = 0.45, -- the claws
	reach = 1.5 * S, reachHit = 2.2 * S, reachUp = 2.6 * S, -- (reachUp: you can't hide on a crate)
	crate = 950, spin = 3.6, offer = 8,
	cola = 2500, colaMax = 3,
	guns = 2, startGuns = { "revolver" }, startMelee = "knife",
	revolverDmg = 40, -- (the revolver's damage the zombies' HP is tuned to: one tap kills in round 1. it stays this in here
	-- after the 20 Nov PvP nerf to 33: Zombies.luau scales revolver hits on zombies by revolverDmg / its dmg)
	planks = 6, tear = 1.3, tearRun = 0.85, board = 0.6, boardPay = 10, boardCap = 20,
	doorRoll = 2.6, -- s a bought shutter takes to roll up into its housing (the recorded rattle, zm_door, lasts as long)
	climb = 1.35, climbRun = 0.85,
	maxAlive = nil :: number?, -- (a test knob: overrides the cap)
}

-- zombies in round r, solo (friends add 75% each)
function ZM.count(r: number, players: number): number
	local solo = if r <= 5 then ({ 6, 9, 13, 18, 24 })[r] else 24 + (r - 5) * 3
	return math.floor(solo * (1 + 0.75 * (math.clamp(players, 1, 4) - 1)) + 0.5)
end
-- their HP: one revolver shot in round 1, +22 a round to round 9, then +9% a round
function ZM.hp(r: number): number
	return if r <= 9 then 40 + 22 * (r - 1) else math.floor(216 * 1.09 ^ (r - 9) + 0.5)
end
function ZM.maxAlive(players: number): number
	return ZM.R.maxAlive or math.min(24, 14 + 6 * (math.max(1, players) - 1))
end
-- s between spawns
function ZM.gap(r: number, players: number): number
	return math.max(0.45, 2 - 0.15 * (r - 1)) * (if players > 1 then 0.75 else 1)
end
-- how one moves (roll 0..1): shamblers early, runners from round 4, sprinters from round 9. speed in studs/s
-- kind 0 shambler, 1 runner, 2 sprinter
function ZM.gait(r: number, roll: number, jitter: number): (number, number)
	local run = math.clamp((r - 3) * 0.22, 0, 1)
	local sprint = if r >= 9 then math.min(0.6, 0.2 + (r - 9) * 0.1) else 0
	if roll < sprint then return 9.2 * S, 2 end
	if roll < run then return (6.8 + jitter) * S, 1 end
	return (2.6 + jitter * 0.9) * S, 0
end
-- the colours (the owner, 20 Nov 2026: coloured dummies for now): shambler green, runner amber, sprinter red
ZM.GAIT_COLOR = { [0] = Color3.fromHex("8fd14f"), [1] = Color3.fromHex("ffb347"), [2] = Color3.fromHex("ff5a3a") }
ZM.GAIT_NAME = { [0] = "Shambler", [1] = "Runner", [2] = "Sprinter" }
-- claw damage: 15 in round 1, +1 a round, 34 at most
function ZM.claw(r: number): number
	local R = ZM.R
	return math.min(R.swipeMax, R.swipe + R.swipeRamp * math.max(0, r - 1))
end

-- every round you get with a gun (the mag plus the spares). melee and the hold weapons don't use ammo
ZM.AMMO = {
	revolver = 54, smg = 315, ar = 300, redline = 280, shotgun = 54, sniper = 40, minigun = 750, marbles = 22, chicken = 24,
	bowling = 20, banana = 60, snowball = 50, bow = 40, cards = 50, burst = 300, lmg = 500, dmr = 60, lever = 64,
	autoshot = 80, pistol = 84, akimbo = 280, sawnoff = 30,
} :: { [string]: number } -- (anything not here never runs out, as on the web: the nail gun, tennis, the cart, water...)
function ZM.ammo(id: string): number? return ZM.AMMO[id] end
-- a refill is half the gun's price (rounded up to 10)
function ZM.ammoPrice(price: number): number return math.ceil(price / 20) * 10 end

-- the mystery crate (weights)
ZM.CRATE = {
	minigun = 6, chicken = 6, marbles = 6, redline = 6, bowling = 5, snowball = 5, cig = 4, cards = 4, sniper = 3, ar = 3,
	smg = 3, shotgun = 3, bow = 3, banana = 3, slapper = 2, blower = 2, burst = 4, lmg = 5, dmr = 3, lever = 4, autoshot = 5,
	nailgun = 5, tennis = 4, cart = 4, akimbo = 5, sawnoff = 5, pistol = 1, water = 3, taser = 3, remote = 2,
} :: { [string]: number }
function ZM.pick(owned: { string }, rnd: (() -> number)?): string
	local r = rnd or math.random
	local pool, total = {}, 0
	for id, w in ZM.CRATE do
		if not table.find(owned, id) and Weapons.list[id] then table.insert(pool, { id, w }); total += w end
	end
	table.sort(pool, function(a, b) return a[1] < b[1] end)
	local t = r() * total
	for _, e in pool do
		t -= e[2]
		if t <= 0 then return e[1] end
	end
	return if #pool > 0 then pool[#pool][1] else "minigun"
end

-- ------------------------------------------------------------------ stage 2: the machines, drops, boards (web zmshop.js /
-- zombies.js). plain descriptions (the owner: no flavour text)
ZM.R.mach, ZM.R.machStep, ZM.R.machSpin, ZM.R.machCd = 1250, 500, 2.6, 15
ZM.R.dropChance, ZM.R.dropCap, ZM.R.dropLife, ZM.R.dropBlink, ZM.R.dropReach = 0.045, 4, 25, 5, 1.7 * S
ZM.R.upHold, ZM.R.fxGap = 1.2, 0.35
-- the colas (Jank Cola is the first). colaMax at once; all gone if you go down (Get Up Juice is used up instead)
ZM.COLAS = {
	jank = { name = "JANK COLA", price = 2500, color = Color3.fromHex("ff5a3a"), desc = "Claws hit you half as hard. You heal faster." },
	getup = { name = "GET UP JUICE", price = 1500, color = Color3.fromHex("ff4fd8"), desc = "Go down and you get back up by yourself, once.", self = 4 },
	legday = { name = "LEG DAY", price = 2000, color = Color3.fromHex("4fd8ff"), desc = "You run faster.", speed = 1.12 },
	pockets = { name = "DEEP POCKETS", price = 3000, color = Color3.fromHex("ffe14d"), desc = "Every gun holds half again as much ammo.", ammo = 1.5 },
	thirdhand = { name = "THIRD HAND", price = 4000, color = Color3.fromHex("7dff4f"), desc = "Carry three guns.", guns = 3 },
} :: { [string]: any }
-- the Warranty Voider: hold Q with the weapon in your hands (F till 27 Nov 2026). three goes per weapon, dearer each time. mul = damage to
-- zombies, ammo = what the gun holds. from the second go it rolls a side effect (again at the third)
ZM.UP = { name = "WARRANTY VOIDER", price = { 2500, 5000, 9000 }, mul = { [0] = 1, 1.6, 2.4, 3.4 }, ammo = { [0] = 1, 1.2, 1.4, 1.6 }, tier = { "VOID", "VOID II", "VOID III" } }
ZM.UPFX = {
	zap = { name = "ZAPPY", desc = "Hits jump to the zombies next to it.", color = Color3.fromHex("4fd8ff"), reach = 6 * S, n = { [2] = 2, [3] = 4 }, part = 0.4 },
	toast = { name = "TOASTY", desc = "Sets them on fire.", color = Color3.fromHex("ff8a3a"), secs = 3, tick = 0.12 },
	frost = { name = "FROSTY", desc = "Freezes them for a moment.", color = Color3.fromHex("bfefff"), secs = 1.1, again = 5 },
	boing = { name = "BOINGY", desc = "Pops them into the air.", color = Color3.fromHex("ff4fd8"), up = 9 * S },
	tips = { name = "TIPPY", desc = "+5 credits a hit.", color = Color3.fromHex("7dff4f"), pay = 5 },
} :: { [string]: any }
ZM.UPFX_ORDER = { "zap", "toast", "frost", "boing", "tips" }
-- the Cheat Machine (needs the power): pay, it rolls one of these. team ones are for everyone, the rest for whoever paid
ZM.MODS = {
	oneshot = { name = "ONE AND DONE", desc = "Every hit kills.", dur = 15, team = true, color = Color3.fromHex("ff3030") },
	taxfraud = { name = "TAX FRAUD", desc = "Double credits.", dur = 30, team = true, color = Color3.fromHex("7dff4f") },
	bottomless = { name = "BOTTOMLESS MAG", desc = "No reloads, no running out.", dur = 20, team = false, color = Color3.fromHex("ffe14d") },
	zoomies = { name = "ZOOMIES", desc = "You run 40% faster.", dur = 25, team = false, color = Color3.fromHex("4fd8ff"), speed = 1.4 },
	brainfreeze = { name = "BRAIN FREEZE", desc = "Zombies move slowly.", dur = 15, team = true, color = Color3.fromHex("bfefff") },
	bighead = { name = "BIG HEAD MODE", desc = "Zombie heads are huge. Every kill counts as a headshot.", dur = 25, team = true, color = Color3.fromHex("ffb347") },
	vampire = { name = "VAMPIRE TEETH", desc = "Your hits heal you.", dur = 20, team = false, color = Color3.fromHex("c01040") },
	bouncy = { name = "BOUNCY CASTLE", desc = "Every hit sends them flying.", dur = 20, team = true, color = Color3.fromHex("ff4fd8") },
} :: { [string]: any }
ZM.MOD_ORDER = { "oneshot", "taxfraud", "bottomless", "zoomies", "brainfreeze", "bighead", "vampire", "bouncy" }
function ZM.machPrice(uses: number): number return ZM.R.mach + ZM.R.machStep * uses end
-- drops: a zombie you kill sometimes leaves one (dropCap a round, gone after dropLife). (the web's killstreak drops wait
-- for killstreaks on Roblox)
ZM.DROPS = {
	tipjar = { name = "TIP JAR", desc = "+400 credits for everyone.", color = Color3.fromHex("7dff4f"), w = 3 },
	restock = { name = "RESTOCK", desc = "Full ammo for everyone.", color = Color3.fromHex("4fd8ff"), w = 3 },
	aisle5 = { name = "CLEAN-UP ON AISLE 5", desc = "Every zombie pops.", color = Color3.fromHex("ff4fd8"), w = 2 },
} :: { [string]: any }
ZM.DROP_ORDER = { "tipjar", "restock", "aisle5" }
function ZM.dropPick(rnd: (() -> number)?): string
	local r = rnd or math.random
	local total = 0
	for _, k in ZM.DROP_ORDER do total += ZM.DROPS[k].w end
	local t = r() * total
	for _, k in ZM.DROP_ORDER do
		t -= ZM.DROPS[k].w
		if t <= 0 then return k end
	end
	return "tipjar"
end

-- ------------------------------------------------------------------ stage 3: limbs, the special zombies, the bosses (web
-- shared/zmlimbs.js). a limb comes off after it soaks limbHp x the zombie's full HP (limbMin at least), +limbPay. no legs:
-- it crawls; one leg: it hops; no arms: it claws for half and is slow at planks
ZM.LIMB = { limbHp = 0.3, limbMin = 20, limbPay = 10, crawl = 1.4 * S, hop = 0.55, crawlUp = 0.9 * S, noArms = 0.5,
	oneArmCd = 1.4, noArmTear = 2.5, oneArmTear = 1.3, bornArmless = 0.18, random = 0.35 }
-- the specials (from = first round, w = weight, cap = at once; hp / claw multiply the round's, speed replaces the gait)
-- (26 Nov 2026, the owner: "the pourple and red ones have too much hp!": the Chonk 3.5 -> 2 times a zombie's HP; the
-- Floor Manager 16 -> 6 and the Mascot 20 -> 7 times, and the squad's bots count 0.15 each there instead of a whole
-- extra player. tables: roblox/docs/ZOMBIES.md "HP")
ZM.TYPES = {
	chonk = { name = "CHONK", from = 5, w = 2, cap = 1, scale = 1.4, hp = 2, speed = 2.3 * S, run = 0, claw = 1.6, color = Color3.fromHex("b07dff"),
		pay = 100, blast = 5 * S, blastZ = 180, blastP = 18 },
	biter = { name = "ANKLE BITER", from = 3, w = 3, cap = 6, scale = 0.6, hp = 0.4, speed = 8.2 * S, run = 2, claw = 0.5, cd = 0.7, pack = 3,
		color = Color3.fromHex("ffe14d") },
	hardhat = { name = "HARD HAT", from = 4, w = 3, cap = 4, scale = 1, hp = 1.2, hat = 3 },
	screamer = { name = "SCREAMER", from = 6, w = 1.5, cap = 1, scale = 1.08, hp = 0.7, color = Color3.fromHex("ff4fd8"), pay = 40,
		every = 9, yell = 1.3, reach = 14 * S, hype = 6, boost = 1.45, see = 20 * S },
	-- the mini bosses: one every ZM.BOSS.every rounds, never from the random roll
	manager = { name = "THE FLOOR MANAGER", boss = true, scale = 1.75, hp = 1, bossHp = 6, speed = 3.6 * S, run = 0, claw = 2,
		color = Color3.fromHex("ff3030"), reward = 1000,
		meeting = { every = 14, yell = 1.5, n = 3, reach = 22 * S, hype = 7 },
		charge = { every = 9, min = 4 * S, max = 20 * S, windup = 0.9, secs = 1.3, speed = 13 * S, reach = 1.9 * S, dmg = 34, kb = 14 * S } },
	mascot = { name = "THE MASCOT", boss = true, scale = 1.9, hp = 1, bossHp = 7, speed = 3.1 * S, run = 0, claw = 2.2,
		color = Color3.fromHex("4fd8ff"), reward = 1250,
		jump = { every = 6.5, min = 3 * S, max = 22 * S, up = 70, r = 6.5 * S, dmg = 28 } },
} :: { [string]: any }
ZM.TYPE_ORDER = { "chonk", "biter", "hardhat", "screamer" }
ZM.BOSSES = { "manager", "mascot" }
-- the lights (27 Nov 2026, the owner: "Can you make zombies having glowing eyes, also some parts of the map you need a
-- flashlight"): the areas that stay near-black till the power is on, by the school's area ids (each client dims its own
-- light while its camera is in one, ZombieLight.client; their lamps wait for the power, server/ZombieLight.luau; a map
-- without these ids has no dark areas), and the zombies' eyes' colour (two small Neon pieces, a sickly yellow-green: a
-- paler one burnt to white in the Neon)
ZM.DARK = { tunnels = true, boiler = true, lockers = true, gymwing = true } :: { [string]: boolean }
ZM.EYE = Color3.fromRGB(178, 236, 104)
ZM.BOSS = { every = 5, delay = 5, perPlayer = 0.5, perBot = 0.15, hitCap = 0.06 }
-- a boss's HP for a squad of `people` real players and `bots` bots in round r
function ZM.bossHp(ty: string, r: number, people: number, bots: number): number
	local def = ZM.TYPES[ty]
	return math.floor(ZM.hp(r) * def.bossHp * (1 + ZM.BOSS.perPlayer * (math.max(1, people) - 1) + ZM.BOSS.perBot * math.max(0, bots)) + 0.5)
end
function ZM.typeChance(r: number): number return math.min(0.4, math.max(0, 0.07 * (r - 2))) end
function ZM.pickType(r: number, alive: { [string]: number }, rnd: (() -> number)?): string
	local rr = rnd or math.random
	if rr() >= ZM.typeChance(r) then return "" end
	local pool, total = {}, 0
	for _, id in ZM.TYPE_ORDER do
		local d = ZM.TYPES[id]
		if r >= d.from and (alive[id] or 0) < d.cap then table.insert(pool, id); total += d.w end
	end
	local t = rr() * total
	for _, id in pool do
		t -= ZM.TYPES[id].w
		if t <= 0 then return id end
	end
	return ""
end

-- ------------------------------------------------------------------ the map (roblox/docs/ZOMBIES.md)
export type Area = { id: string, label: string, boxes: { { cf: CFrame, size: Vector3 } } }
export type Door = { i: number, a: string, b: string, price: number, label: string, model: Model, shutter: BasePart }
export type Window = { i: number, area: string, model: Model, out: Vector3, inn: Vector3, at: CFrame, n: Vector3 }
export type Buy = { i: number, w: string, price: number, part: BasePart }
export type Map = {
	model: Model, folder: Instance, label: string, start: string, bounds: BasePart,
	areas: { [string]: Area }, doors: { Door }, windows: { Window }, buys: { Buy },
	spawns: { CFrame }, crate: { BasePart }, power: BasePart?, mach: BasePart?, voider: BasePart?, colas: { BasePart },
}

local function inBox(cf: CFrame, size: Vector3, p: Vector3, padY: number): boolean
	local l = cf:PointToObjectSpace(p)
	return math.abs(l.X) <= size.X / 2 and math.abs(l.Z) <= size.Z / 2 and l.Y >= -size.Y / 2 - padY and l.Y <= size.Y / 2
end
-- read a map's ZM folder (anything missing is just empty; the caller checks what it needs)
function ZM.read(model: Model): (Map?, string?)
	local f = model:FindFirstChild("ZM")
	if not f then return nil, "no ZM folder" end
	local bounds = f:FindFirstChild("NavBounds")
	if not bounds or not bounds:IsA("BasePart") then return nil, "no ZM/NavBounds" end
	local m: Map = {
		model = model, folder = f, label = tostring(f:GetAttribute("Label") or model.Name), start = tostring(f:GetAttribute("Start") or ""),
		bounds = bounds, areas = {}, doors = {}, windows = {}, buys = {}, spawns = {}, crate = {}, colas = {},
		power = f:FindFirstChild("Power") :: BasePart?, mach = f:FindFirstChild("CheatMachine") :: BasePart?, voider = f:FindFirstChild("Voider") :: BasePart?,
	}
	local A = f:FindFirstChild("Areas")
	if A then
		for _, p in A:GetChildren() do
			if not p:IsA("BasePart") then continue end
			local a = m.areas[p.Name]
			if not a then a = { id = p.Name, label = tostring(p:GetAttribute("Label") or p.Name), boxes = {} }; m.areas[p.Name] = a end
			if p:GetAttribute("Label") then a.label = tostring(p:GetAttribute("Label")) end
			table.insert(a.boxes, { cf = p.CFrame, size = p.Size })
		end
	end
	-- (sorted by name so every server and client numbers them the same)
	local function sorted(folder: Instance?): { Instance }
		local out = if folder then folder:GetChildren() else {}
		table.sort(out, function(a, b) return a:GetFullName() < b:GetFullName() end)
		return out
	end
	for _, d in sorted(f:FindFirstChild("Doors")) do
		local sh = d:FindFirstChild("Shutter")
		if not d:IsA("Model") or not sh or not sh:IsA("BasePart") then continue end
		local a, b = tostring(d:GetAttribute("A") or ""), tostring(d:GetAttribute("B") or "")
		local lab = d:GetAttribute("Label")
		table.insert(m.doors, { i = #m.doors + 1, a = a, b = b, price = tonumber(d:GetAttribute("Price")) or 1000,
			label = if lab then tostring(lab) elseif m.areas[b] then m.areas[b].label else b, model = d, shutter = sh })
	end
	for _, w in sorted(f:FindFirstChild("Windows")) do
		local o, i, bd = w:FindFirstChild("Out"), w:FindFirstChild("In"), w:FindFirstChild("Boards")
		if not w:IsA("Model") or not (o and o:IsA("BasePart")) or not (i and i:IsA("BasePart")) or not (bd and bd:IsA("BasePart")) then continue end
		local n = bd.CFrame.LookVector
		table.insert(m.windows, { i = #m.windows + 1, area = tostring(w:GetAttribute("Area") or ""), model = w,
			out = o.Position - Vector3.new(0, o.Size.Y / 2, 0), inn = i.Position - Vector3.new(0, i.Size.Y / 2, 0), -- (floor points)
			at = bd.CFrame, n = Vector3.new(n.X, 0, n.Z).Unit })
	end
	for _, b in sorted(f:FindFirstChild("WallBuys")) do
		if not b:IsA("BasePart") then continue end
		local wid = tostring(b:GetAttribute("Weapon") or "")
		if not Weapons.list[wid] then continue end
		table.insert(m.buys, { i = #m.buys + 1, w = wid, price = tonumber(b:GetAttribute("Price")) or 1000, part = b })
	end
	for _, s in sorted(f:FindFirstChild("PlayerSpawns")) do if s:IsA("BasePart") then table.insert(m.spawns, s.CFrame - Vector3.new(0, s.Size.Y / 2, 0)) end end -- (floor points)
	for _, s in sorted(f:FindFirstChild("Crate")) do if s:IsA("BasePart") then table.insert(m.crate, s) end end
	for _, s in sorted(f:FindFirstChild("Colas")) do if s:IsA("BasePart") then table.insert(m.colas, s) end end
	return m, nil
end
-- which area a point is in (nil: outside, a window ledge)
function ZM.areaAt(map: Map, p: Vector3): string?
	for id, a in map.areas do
		for _, b in a.boxes do
			if inBox(b.cf, b.size, p, 1) then return id end
		end
	end
	return nil
end
-- the areas you can get to: walk out from the start through the open doors
function ZM.openAreas(map: Map, open: { boolean }): { [string]: boolean }
	local out = { [map.start] = true }
	local grew = true
	while grew do
		grew = false
		for i, d in map.doors do
			if open[i] and (out[d.a] == true) ~= (out[d.b] == true) then out[d.a] = true; out[d.b] = true; grew = true end
		end
	end
	return out
end

-- ------------------------------------------------------------------ extraction (27 Nov 2026, roblox/docs/ZOMBIES.md 4)
-- (the owner: "allow a way to extract!! If you extract at higher floors you can leave and gain rewards"; main read the
-- floors as rounds.) The break after round 10, then every 5th round, offers it; the squad votes; the next round is a
-- heavier hold-out while a helicopter comes to the zone; whoever stands in the zone when it lifts off is out.
-- times in s from the call (the server sends the call's server time; every client draws the helicopter from it)
ZM.X = {
	first = 10, every = 5, -- offered at the break after round 10, 15, 20...
	voteS = 20, -- that break lasts this long (a plain break is R.rest)
	hold = 90, -- the call to the lift-off: who's in the zone then is out
	arrive = 55, over = 62, land = 66, -- the helicopter: in sight, over the pad, down
	board = 4.2, -- s from the end of the hold-out to the lift-off (the film's first-person boarding plays in it)
	heavy = { alive = 1.5, cap = 36, gap = 0.5 }, -- the hold-out: 50% more at once (36 at most), spawning twice as fast
	intro = 9.9, -- the intro film (ZombieCine): round 1 starts 1.5 s after it, or 2.5 s after everyone skipped
	-- the intro as a news broadcast (27 Nov, the owner: "have a news broadcast actually for the intro a zombies, it'll be
	-- like breaking news", "Then it cuts to shot of the school"): s into the film. the live feed (banner, LIVE, the one
	-- headline, an aerial camera; the zoom to the boarded window), the hit and the static, signal lost, our own shot of
	-- the school, the squad, your view
	news = { banner = 0.25, line = 0.8, zoom = { 3.0, 4.0 }, hit = 4.6, static = { 4.65, 5.2 }, school = { 5.2, 7.7 }, squad = { 7.7, 9.3 } },
	outro = 9.0, -- the extraction film, then the stats card
	-- (27 Nov, the owner: "first person, helicopter door opens and there's a guy, he reaches out his hand, you take a
	-- step forward then shot its an away shot of the helicopter flying off then boom displays your round"). s into the
	-- film: the door slides back, the crew member reaches, your hand comes up, the step, the cut on contact
	film = { door = { 0.6, 1.5 }, crew = 1.3, hand = 2.0, step = { 2.6, 3.6 }, cut = 3.7 },
	reach = "rbxassetid://110255422946477", -- (vault Mixamo "Pointing Forward", frames 36-66: the arm out; mocap)
	doorSlide = Vector3.new(-0.5, 0, 3.6), -- (model space: out of the hull a hair (on the door's side), then back along the boom)
	-- which helicopter flies (ReplicatedStorage.JankfireZmKit; ZmKit.importHeli): "HeliA" the web game's JANK NEWS heli
	-- rebuilt without writing, night JANK scheme; "HeliB" the same in a dark rescue scheme; "Heli" the first, chunky one
	heli = "HeliA",
	-- the zone per map (map-local studs, the arena's origin; area = the map area it stands in, opened on the call).
	-- yaw: the way the helicopter's nose points on the pad (degrees about up; 0 = -z, the school's back). from: where it
	-- comes from, leave: where it goes (map-local, relative to the pad)
	zones = {
		JankfieldHighV2B = { at = Vector3.new(10, 32, -70), r = 14, area = "roof", yaw = 0,
			from = Vector3.new(-330, 150, -260), leave = Vector3.new(60, 160, -520) },
	} :: { [string]: any },
}
function ZM.xOffered(n: number): boolean
	return n >= ZM.X.first and (n - ZM.X.first) % ZM.X.every == 0
end
-- where the helicopter is t s after the call (lift = the lift-off's t, from ZM.X.hold + board), as a CFrame for the
-- model's pivot (the skids' feet, nose along LookVector). pad = the pad's world CFrame (its yaw in it). nil = not in
-- the sky yet. bob: a hover's small breathing
local function smooth(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end
function ZM.heliAt(pad: CFrame, z: any, t: number, lift: number?): CFrame?
	local X = ZM.X
	if t < X.arrive then return nil end
	local P = pad.Position
	local from = pad:PointToWorldSpace(z.from)
	local over = P + Vector3.new(0, 30, 0)
	local look = pad.LookVector
	local bob = math.sin(t * 1.7) * 0.18
	if lift and t >= lift then
		local u = t - lift
		local up = P + Vector3.new(0, 14 * smooth(u / 2.4), 0)
		if u < 2.4 then
			return CFrame.lookAt(up, up + look) * CFrame.Angles(math.rad(-6 * smooth(u / 2.4)), 0, 0)
		end
		local away = pad:PointToWorldSpace(z.leave)
		local k = math.clamp((u - 2.4) / 9, 0, 1)
		local e = k * k * (1.6 - 0.6 * k) -- (gathering speed)
		local p = (P + Vector3.new(0, 14, 0)):Lerp(away, e)
		local dir = (away - (P + Vector3.new(0, 14, 0)))
		local flatDir = Vector3.new(dir.X, 0, dir.Z).Unit
		local f = look:Lerp(flatDir, smooth(k * 3)).Unit
		return CFrame.lookAt(p, p + f) * CFrame.Angles(math.rad(-14 * smooth(k * 4)), 0, 0)
	end
	if t < X.over then
		local u = (t - X.arrive) / (X.over - X.arrive)
		local e = 1 - (1 - u) ^ 3 -- (slowing into the hover)
		local p = from:Lerp(over, e)
		local dir = Vector3.new(over.X - from.X, 0, over.Z - from.Z).Unit
		local f = dir:Lerp(look, smooth((u - 0.55) / 0.45)).Unit
		return CFrame.lookAt(p, p + f) * CFrame.Angles(math.rad(-10 * (1 - smooth(u / 0.9))), 0, math.rad(6 * math.sin(u * math.pi)))
	end
	if t < X.land then
		local u = smooth((t - X.over) / (X.land - X.over))
		local p = over:Lerp(P + Vector3.new(0, 0.6, 0), u)
		return CFrame.lookAt(p, p + look) + Vector3.new(0, bob * (1 - u), 0)
	end
	local p = P + Vector3.new(0, 0.6 + math.max(0, bob) * 0.4, 0)
	return CFrame.lookAt(p, p + look)
end
-- the pad's world CFrame for a zone on a map copy pivoted at `site` (Zombies' SITE)
function ZM.padOf(site: CFrame, z: any): CFrame
	return site * CFrame.new(z.at) * CFrame.Angles(0, math.rad(z.yaw or 0), 0)
end

-- ------------------------------------------------------------------ the extraction's rewards (ZombieRewards.luau)
-- (the owner: "rewards CAN be bags sprays and crates but rarely chances increase significantly if you get to way higher
-- rounds"). The band is the extraction round's (the highest `from` at or under it). Each roll on its own. Brass goes
-- through Quests.grant (its 300-a-day cap stands), XP through Stats.gift, the rest through Loot.grant. The odds are on
-- the offer and the reward screen (ZombieExtract.client)
ZM.XR = {
	bands = {
		{ from = 10, brass = 25, xp = 300, spray = 0.02, bag = 0.01, crate = 0.005, wrap = 0.03 },
		{ from = 15, brass = 35, xp = 450, spray = 0.04, bag = 0.02, crate = 0.01, wrap = 0.06 },
		{ from = 20, brass = 50, xp = 650, spray = 0.08, bag = 0.04, crate = 0.02, wrap = 0.10 },
		{ from = 25, brass = 65, xp = 850, spray = 0.13, bag = 0.07, crate = 0.04, wrap = 0.17 },
		{ from = 30, brass = 80, xp = 1100, spray = 0.20, bag = 0.10, crate = 0.06, wrap = 0.25 },
	},
	-- the rolls, in the screen's order: what Loot.grant gets (a container id; "wrap": the zombies-only wraps below)
	rolls = { "spray", "bag", "crate", "wrap" },
	names = { spray = "SPRAY CAN", bag = "DUFFEL BAG", crate = "CRATE", wrap = "ZOMBIES WRAP" },
	-- the zombies-only wraps (the wraps session's three, 27 Nov; Roster.EARNED.zombies, w.earned = "zombies"): { id =
	-- <Roster wrap id>, from = <round>, w = <weight> }. A wrap roll picks among the ones open at the extraction round by
	-- weight, leaving out ones the player has; it goes on every gun (Loot's "zmwrap:<wrap>"). Empty: no wrap roll.
	-- (later: { kind = "skin", id = ..., from = ..., w = ... } for a zombies-only skin)
	wraps = {
		{ id = "zboards", from = 10, w = 5 }, -- Boarded Up (Epic): the early one
		{ id = "zpeel", from = 20, w = 3 }, -- Locker Rot (Legendary): the middle one
		{ id = "zooze", from = 30, w = 2 }, -- Ooze (Exotic, living): the deepest
	} :: { { id: string, from: number, w: number, kind: string? } },
	overXp = 10, overXpMax = 250, -- a game over (or left behind): 10 XP a round reached, 250 at most
	gate = { share = 0.15, up = 0.5, active = 0.5 }, -- 15% of the squad's damage or kills, up half the game, active half
}
function ZM.xBand(n: number): any?
	local best = nil
	for _, b in ZM.XR.bands do if n >= b.from then best = b end end
	return best
end
-- the wrap rows open at round n (and whether there's any: no row, no wrap roll)
function ZM.xWraps(n: number): { any }
	local out = {}
	for _, w in ZM.XR.wraps do if n >= (w.from or 0) then table.insert(out, w) end end
	return out
end

return ZM
