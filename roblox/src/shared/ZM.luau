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
	hold = 0.3, power = 1, revive = 3, bleed = 30, -- hold E to buy / to throw the power switch / to revive; a downed friend lasts
	regenAfter = 4, regen = 25, -- 4 s without a hit and you heal 25 HP a second
	swipe = 15, swipeRamp = 1, swipeMax = 34, swipeCd = 1.1, windup = 0.35, iframe = 0.45, -- the claws
	reach = 1.5 * S, reachHit = 2.2 * S, reachUp = 2.6 * S, -- (reachUp: you can't hide on a crate)
	crate = 950, spin = 3.6, offer = 8,
	cola = 2500, colaMax = 3,
	guns = 2, startGuns = { "revolver" }, startMelee = "knife",
	planks = 6, tear = 1.3, tearRun = 0.85, board = 0.6, boardPay = 10, boardCap = 20,
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

return ZM
