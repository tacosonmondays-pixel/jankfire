--!strict
-- ZOMBIES stage 2 (web server/zmextra.js + zmshop.js): the power switch, the colas, the Warranty Voider, the Cheat
-- Machine, power-up drops, window boards and the mystery crate. it plugs into the mode (Zombies.luau) through
-- Zombies.ext (the web's zx* / zs* hooks) and uses the mode's own parts (Zombies.X). the numbers: shared/ZM.luau.
-- the machines' models are built here (chunky boxes, quiet colours, one accent each); the markers come from the map
-- (roblox/docs/ZOMBIES.md: Power, CheatMachine, Voider, Colas, Crate, every window's Boards). buying is F (prompts)
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")
local TweenService = game:GetService("TweenService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local ZM = require(Shared:WaitForChild("ZM"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local ZombieExtra = {}
local W = Weapons.list
local R = ZM.R
local S = Weapons.S
local now = os.clock
local Z: any = nil
local X: any = nil

-- ------------------------------------------------------------------ state: per member, per game
type MS = { colas: { string }, up: { [string]: { t: number, fx: string } }, boardN: number, fxT: number }
local MSt: { [any]: MS } = setmetatable({}, { __mode = "k" }) :: any
local function ms(m: any): MS
	local x = MSt[m]
	if not x then x = { colas = {}, up = {}, boardN = 0, fxT = 0 }; MSt[m] = x end
	return x
end
local function hasCola(m: any, id: string): boolean return table.find(ms(m).colas, id) ~= nil end

type Drop = { id: number, k: string, part: BasePart, untilT: number }
type GS = {
	power: boolean, folder: Folder,
	planks: { [number]: number }, plankParts: { [number]: { BasePart } }, boardPr: { [number]: ProximityPrompt },
	boarders: { [any]: { i: number, nextT: number } }, tear: { [any]: { at: number, t0: number } },
	drops: { Drop }, dropN: number, dropId: number,
	mods: { { k: string, by: any, untilT: number } },
	mach: { st: number, k: string, by: any, untilT: number, cd: number, uses: number, last: string, pr: ProximityPrompt? },
	crate: { st: number, by: any, w: string, untilT: number, model: Model?, pr: ProximityPrompt? },
	frozen: { [any]: number }, frostOk: { [any]: number },
	burns: { { z: any, by: any, dmg: number, nextT: number, untilT: number, wid: string } },
	zaps: { { z: any, by: any, dmg: number, n: number, wid: string } },
	powerPr: ProximityPrompt?, lever: BasePart?, bottomT: number, blinkT: number,
}
local GSt: { [any]: GS } = setmetatable({}, { __mode = "k" }) :: any

local function serverT(dt: number): number return workspace:GetServerTimeNow() + dt end
local function flat(v: Vector3): Vector3 return Vector3.new(v.X, 0, v.Z) end

-- a modifier the member has right now (team ones are everyone's)
local function mod(gs: GS, k: string, m: any?): boolean
	local n = now()
	for _, x in gs.mods do
		if x.k == k and n < x.untilT and (ZM.MODS[k].team or (m ~= nil and x.by == m)) then return true end
	end
	return false
end
-- what the HUD shows: the power, the modifiers running (k:until server time), your colas and your speed
local function publishMods(g: any, gs: GS)
	local bits = {}
	local n = now()
	for _, x in gs.mods do
		if n < x.untilT then table.insert(bits, x.k .. ":" .. string.format("%.1f", serverT(x.untilT - n)) .. ":" .. (if x.by and x.by.p then x.by.p.UserId else 0)) end
	end
	g.model:SetAttribute("Mods", if #bits > 0 then table.concat(bits, ",") else nil)
	g.model:SetAttribute("Power", gs.power)
end
local function publishMe(gs: GS, m: any)
	local p = m.p
	if not p then return end
	local x = ms(m)
	p:SetAttribute("ZmColas", if #x.colas > 0 then table.concat(x.colas, ",") else nil)
	local sp = 1
	if hasCola(m, "legday") then sp *= ZM.COLAS.legday.speed end
	if mod(gs, "zoomies", m) then sp *= ZM.MODS.zoomies.speed end
	local want = if sp ~= 1 then sp else nil
	if p:GetAttribute("ZmSpeed") ~= want then p:SetAttribute("ZmSpeed", want) end
end

-- ------------------------------------------------------------------ the models
local SLATE, DARK, WOOD, LIGHT = Color3.fromRGB(64, 70, 80), Color3.fromRGB(38, 42, 50), Color3.fromRGB(122, 86, 56), Color3.fromRGB(246, 246, 240)
local function part(parent: Instance, name: string, size: Vector3, cf: CFrame, col: Color3, mat: Enum.Material?): Part
	local p = Instance.new("Part")
	p.Name = name; p.Anchored = true; p.Size = size; p.CFrame = cf; p.Color = col
	p.Material = mat or Enum.Material.SmoothPlastic
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = parent
	return p
end
-- a machine standing against a wall: base = the floor under its front middle, look = its front
local function machine(parent: Instance, name: string, base: CFrame, w: number, h: number, d: number, accent: Color3): Model
	local m = Instance.new("Model")
	m.Name = name
	local look = Vector3.new(base.LookVector.X, 0, base.LookVector.Z).Unit
	local at = base.Position
	local c = CFrame.lookAt(at + Vector3.new(0, h / 2, 0) - look * (d / 2), at + Vector3.new(0, h / 2, 0) - look * (d / 2) + look)
	local body = part(m, "Body", Vector3.new(w, h, d), c, SLATE)
	part(m, "Front", Vector3.new(w * 0.78, h * 0.62, 0.2), c * CFrame.new(0, h * 0.06, -d / 2 - 0.05), accent)
	local strip = part(m, "Light", Vector3.new(w * 0.78, 0.35, 0.2), c * CFrame.new(0, h / 2 - 0.5, -d / 2 - 0.05), LIGHT, Enum.Material.Neon)
	strip.CanCollide = false
	part(m, "Foot", Vector3.new(w + 0.2, 0.4, d + 0.2), c * CFrame.new(0, -h / 2 + 0.2, 0), DARK)
	m.PrimaryPart = body
	m.Parent = parent
	return m
end
local function floorOf(p: BasePart): CFrame return p.CFrame - Vector3.new(0, p.Size.Y / 2, 0) end

-- ------------------------------------------------------------------ the power
local function powerOn(g: any, gs: GS, by: any?)
	if gs.power then return end
	gs.power = true
	for _, l in g.model:GetDescendants() do
		if CollectionService:HasTag(l, "PowerLight") and l:IsA("Light") then l.Enabled = true end
	end
	if gs.powerPr then gs.powerPr:Destroy(); gs.powerPr = nil end
	local lv = gs.lever
	if lv then TweenService:Create(lv, TweenInfo.new(0.35), { CFrame = lv.CFrame * CFrame.Angles(math.rad(150), 0, 0) }):Play() end
	publishMods(g, gs)
	X.sayAll({ k = "power", by = if by then by.name else nil })
end

-- ------------------------------------------------------------------ the colas
local function buyCola(g: any, gs: GS, m: any, id: string)
	local def = ZM.COLAS[id]
	local x = ms(m)
	if not gs.power then X.say(m, { k = "buy", ok = false, m = "no power" }); return end
	if hasCola(m, id) then X.say(m, { k = "buy", ok = false, m = "you have it" }); return end
	if #x.colas >= R.colaMax then X.say(m, { k = "buy", ok = false, m = R.colaMax .. " colas at most" }); return end
	if not X.pay(m, def.price) then return end
	table.insert(x.colas, id)
	if def.ammo then -- (Deep Pockets: the extra comes with it)
		for _, wid in m.guns do
			local total = X.maxTotal(m, wid)
			local wr = W[wid]
			if total and wr and wr.mag and m.res[wid] then m.res[wid] = math.max(m.res[wid], math.min(total - wr.mag, math.floor(m.res[wid] * def.ammo))) end
			local a = m.f.ammo[wid]
			if a and m.res[wid] then a.res = m.res[wid] end
		end
		X.pushRes(m)
	end
	publishMe(gs, m)
	X.say(m, { k = "buy", ok = true, m = def.name })
end

-- ------------------------------------------------------------------ the Warranty Voider
local function voidIt(g: any, gs: GS, m: any)
	local _ = g
	local wid = m.f.held
	local x = ms(m)
	if not gs.power then X.say(m, { k = "buy", ok = false, m = "no power" }); return end
	if not W[wid] or (wid ~= m.melee and not table.find(m.guns, wid)) then X.say(m, { k = "buy", ok = false, m = "hold the weapon to void" }); return end
	local cur = x.up[wid] or { t = 0, fx = "" }
	local price = ZM.UP.price[cur.t + 1]
	if not price then X.say(m, { k = "buy", ok = false, m = "fully voided" }); return end
	if not X.pay(m, price) then return end
	local tier = cur.t + 1
	local fx = ""
	if tier >= 2 then
		local pool = {}
		for _, k in ZM.UPFX_ORDER do if k ~= cur.fx then table.insert(pool, k) end end
		fx = pool[math.random(1, #pool)]
	end
	x.up[wid] = { t = tier, fx = fx }
	-- comes back full
	local total = X.maxTotal(m, wid)
	local wr = W[wid]
	if total and wr.mag then
		m.res[wid] = math.max(0, total - wr.mag)
		local a = m.f.ammo[wid]
		if a then a.res = m.res[wid]; a.mag = wr.mag end
		X.pushRes(m)
		local ar = Remotes:FindFirstChild("Ammo")
		if m.p and ar and ar:IsA("RemoteEvent") then ar:FireClient(m.p, wid, wr.mag, 0) end
	end
	if m.p then m.p:SetAttribute("ZmUp_" .. wid, tier .. ":" .. fx) end
	X.say(m, { k = "buy", ok = true, m = (wr.name or wid) .. "  " .. ZM.UP.tier[tier] .. (if fx ~= "" then "  " .. ZM.UPFX[fx].name else "") })
end

-- ------------------------------------------------------------------ the Cheat Machine
local function machPrompt(gs: GS)
	local pr = gs.mach.pr
	if pr then pr.ActionText = "Play  " .. ZM.machPrice(gs.mach.uses) end
end
local function playMach(g: any, gs: GS, m: any)
	local mc = gs.mach
	local n = now()
	if not gs.power then X.say(m, { k = "buy", ok = false, m = "no power" }); return end
	if mc.st == 1 then X.say(m, { k = "buy", ok = false, m = "rolling" }); return end
	if n < mc.cd then X.say(m, { k = "buy", ok = false, m = "cooling down  " .. math.ceil(mc.cd - n) .. "s" }); return end
	if not X.pay(m, ZM.machPrice(mc.uses)) then return end
	local pool = {}
	for _, k in ZM.MOD_ORDER do if k ~= mc.last then table.insert(pool, k) end end
	mc.st, mc.by, mc.k, mc.untilT = 1, m, pool[math.random(1, #pool)], n + R.machSpin
	mc.uses += 1
	mc.last = mc.k
	machPrompt(gs)
	g.model:SetAttribute("Mach", serverT(R.machSpin))
	X.sayAll({ k = "mach", st = "spin", by = m.name })
end
local function machDone(g: any, gs: GS)
	local mc = gs.mach
	local n = now()
	mc.st = 0
	mc.cd = n + R.machCd
	g.model:SetAttribute("Mach", nil)
	local def = ZM.MODS[mc.k]
	if not def then return end
	local found = nil
	for _, x in gs.mods do
		if x.k == mc.k and n < x.untilT and (def.team or x.by == mc.by) then found = x end
	end
	if found then found.untilT = math.max(found.untilT, n) + def.dur
	else table.insert(gs.mods, { k = mc.k, by = mc.by, untilT = n + def.dur }) end
	if mc.k == "bighead" then
		local G = Z.game()
		if G then for _, z in G.mobs do local h = z.m:FindFirstChild("Head"); if h and h:IsA("BasePart") and not z.m:GetAttribute("BigHead") then h.Size *= 2.2; z.m:SetAttribute("BigHead", true) end end end
	end
	publishMods(g, gs)
	X.sayAll({ k = "mach", st = "win", mod = mc.k, name = def.name, by = if mc.by then mc.by.name else nil })
end

-- ------------------------------------------------------------------ boards (6 planks a window)
local function showPlanks(gs: GS, i: number)
	local ps = gs.plankParts[i]
	if not ps then return end
	for k, p in ps do p.Transparency = if k <= gs.planks[i] then 0 else 1 end
	local pr = gs.boardPr[i]
	if pr then pr.Enabled = gs.planks[i] < R.planks end
end
local function nail(g: any, gs: GS, m: any, i: number)
	if gs.planks[i] >= R.planks then return end
	gs.planks[i] += 1
	showPlanks(gs, i)
	local x = ms(m)
	x.boardN += 1
	if x.boardN <= R.boardCap then X.give(m, R.boardPay, "board") end
	local _ = g
end

-- ------------------------------------------------------------------ drops
local function dropAt(g: any, gs: GS, k: string, at: Vector3)
	local def = ZM.DROPS[k]
	gs.dropId += 1
	local p = Instance.new("Part")
	p.Name = "ZmDrop"
	p.Shape = Enum.PartType.Ball
	p.Size = Vector3.new(2.4, 2.4, 2.4)
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
	p.Material = Enum.Material.Neon
	p.Color = def.color
	p.CFrame = CFrame.new(at)
	p:SetAttribute("Drop", k)
	local bb = Instance.new("BillboardGui")
	bb.Size = UDim2.fromOffset(220, 26); bb.StudsOffset = Vector3.new(0, 2.4, 0); bb.AlwaysOnTop = true; bb.MaxDistance = 90
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(1, 1); t.Text = def.name; t.TextColor3 = def.color
	t.TextStrokeTransparency = 0.4; t.TextScaled = true; t.FontFace = Font.new("rbxasset://fonts/families/BuilderSans.json", Enum.FontWeight.Bold)
	t.Parent = bb
	bb.Parent = p
	p.Parent = gs.folder
	TweenService:Create(p, TweenInfo.new(1.1, Enum.EasingStyle.Sine, Enum.EasingDirection.InOut, -1, true), { CFrame = CFrame.new(at + Vector3.new(0, 1, 0)) }):Play()
	table.insert(gs.drops, { id = gs.dropId, k = k, part = p, untilT = now() + R.dropLife })
	local _ = g
end
local function grab(g: any, gs: GS, d: Drop, by: any)
	local def = ZM.DROPS[d.k]
	d.part:Destroy()
	X.sayAll({ k = "drop", name = def.name, by = by.name })
	if d.k == "tipjar" then
		for _, m in g.members do X.give(m, 400, "drop") end
	elseif d.k == "restock" then
		for _, m in g.members do
			for _, wid in m.guns do
				local total, wr = X.maxTotal(m, wid), W[wid]
				if total and wr and wr.mag then
					m.res[wid] = math.max(0, total - wr.mag)
					local a = m.f.ammo[wid]
					if a then a.res = m.res[wid] end
				end
			end
			X.pushRes(m)
		end
	elseif d.k == "aisle5" then
		local Fight = X.fight()
		for _, z in table.clone(g.mobs) do
			if z.f.alive then Fight.hurt(z.f, z.f.hp + 1, nil, "knife", false) end
		end
		for _, m in g.members do X.give(m, 100, "drop") end
	end
end

-- ------------------------------------------------------------------ the mystery crate
local function crateReset(g: any, gs: GS)
	local c = gs.crate
	c.st, c.by, c.w = 0, nil, ""
	local cm = c.model
	if cm then cm:SetAttribute("Spin", nil); cm:SetAttribute("Offer", nil); cm:SetAttribute("W", nil); cm:SetAttribute("By", nil) end
	local pr = c.pr
	if pr then pr.ActionText = "Open  " .. R.crate; pr.ObjectText = "MYSTERY CRATE" end
	local _ = g
end
local function useCrate(g: any, gs: GS, m: any)
	local c = gs.crate
	if c.st == 2 then
		if c.by ~= m then X.say(m, { k = "buy", ok = false, m = "someone else's" }); return end
		local w = c.w
		crateReset(g, gs)
		X.grant(m, w)
		X.say(m, { k = "buy", ok = true, m = (W[w] and W[w].name) or w })
		return
	end
	if c.st == 1 then X.say(m, { k = "buy", ok = false, m = "spinning" }); return end
	if not X.pay(m, R.crate) then return end
	local owned = table.clone(m.guns)
	table.insert(owned, m.melee)
	c.st, c.by, c.w, c.untilT = 1, m, ZM.pick(owned), now() + R.spin
	local cm = c.model
	if cm then
		cm:SetAttribute("Spin", serverT(R.spin)); cm:SetAttribute("W", c.w)
		cm:SetAttribute("By", if m.p then m.p.UserId else 0)
	end
	if c.pr then c.pr.ActionText = "Spinning" end
end

-- ------------------------------------------------------------------ start: the models, the prompts, the planks
local function start(g: any)
	local gs: GS = {
		power = false, folder = Instance.new("Folder"), planks = {}, plankParts = {}, boardPr = {}, boarders = {}, tear = {},
		drops = {}, dropN = 0, dropId = 0, mods = {},
		mach = { st = 0, k = "", by = nil, untilT = 0, cd = 0, uses = 0, last = "", pr = nil },
		crate = { st = 0, by = nil, w = "", untilT = 0, model = nil, pr = nil },
		frozen = {}, frostOk = {}, burns = {}, zaps = {}, powerPr = nil, lever = nil, bottomT = 0, blinkT = 0,
	}
	gs.folder.Name = "ZMExtra"
	gs.folder.Parent = g.model
	GSt[g] = gs
	local map = g.map
	local function wire(pr: ProximityPrompt, fn: (any) -> ())
		pr.Triggered:Connect(function(pl: Player)
			local m = X.buyerOf(g, pl)
			if m and Z.game() == g then fn(m) end
		end)
	end
	-- the power: off till someone throws the switch (lights tagged PowerLight wait for it)
	for _, l in g.model:GetDescendants() do
		if CollectionService:HasTag(l, "PowerLight") and l:IsA("Light") then l.Enabled = false end
	end
	if map.power then
		local pw = map.power :: BasePart
		local plate = part(gs.folder, "PowerBox", Vector3.new(2.6, 3.4, 0.8), pw.CFrame * CFrame.new(0, 0, 0.3), SLATE)
		local lever = part(gs.folder, "Lever", Vector3.new(0.5, 1.8, 0.5), plate.CFrame * CFrame.new(0, 0.2, -0.65) * CFrame.Angles(math.rad(-30), 0, 0), Color3.fromHex("ffb347"))
		gs.lever = lever
		local pr = X.prompt(plate, "Turn on", "POWER", R.power)
		gs.powerPr = pr
		wire(pr, function(m: any) powerOn(g, gs, m) end)
	else
		gs.power = true -- (a map with no switch: the machines just work)
	end
	-- the colas
	for _, c in map.colas do
		local id = tostring(c:GetAttribute("Cola") or "")
		local def = ZM.COLAS[id]
		if not def then continue end
		local mm = machine(gs.folder, "Cola_" .. id, floorOf(c), 3, 6.6, 2.6, def.color)
		local pr = X.prompt(mm.PrimaryPart, "Buy  " .. def.price, def.name, R.hold)
		wire(pr, function(m: any) buyCola(g, gs, m, id) end)
	end
	-- the Voider, the Cheat Machine
	if map.voider then
		local mm = machine(gs.folder, "Voider", floorOf(map.voider), 5, 4.2, 3, Color3.fromHex("9a7cff"))
		local pr = X.prompt(mm.PrimaryPart, "Void", ZM.UP.name, R.upHold)
		wire(pr, function(m: any) voidIt(g, gs, m) end)
	end
	if map.mach then
		local mm = machine(gs.folder, "CheatMachine", floorOf(map.mach), 3.4, 6.2, 3, Color3.fromHex("ff4fd8"))
		local pr = X.prompt(mm.PrimaryPart, "Play  " .. ZM.machPrice(0), "CHEAT MACHINE", R.hold)
		gs.mach.pr = pr
		wire(pr, function(m: any) playMach(g, gs, m) end)
	end
	-- the crate (its Start spot; the client shows the spin over it)
	local spot = nil
	for _, s in map.crate do if s:GetAttribute("Start") then spot = s end end
	spot = spot or map.crate[1]
	if spot then
		local base = floorOf(spot)
		local cm = Instance.new("Model")
		cm.Name = "Crate"
		local look = Vector3.new(base.LookVector.X, 0, base.LookVector.Z).Unit
		local c0 = CFrame.lookAt(base.Position + Vector3.new(0, 1.4, 0), base.Position + Vector3.new(0, 1.4, 0) + look)
		local body = part(cm, "Body", Vector3.new(5.4, 2.8, 2.8), c0, WOOD, Enum.Material.WoodPlanks)
		part(cm, "Lid", Vector3.new(5.6, 0.5, 3), c0 * CFrame.new(0, 1.65, 0), Color3.fromRGB(96, 66, 44), Enum.Material.WoodPlanks)
		part(cm, "Band", Vector3.new(5.5, 2.9, 0.3), c0 * CFrame.new(0, 0, 0), DARK)
		local lamp = part(cm, "Glow", Vector3.new(4.4, 0.2, 2), c0 * CFrame.new(0, 1.95, 0), LIGHT, Enum.Material.Neon)
		lamp.CanCollide = false
		cm.PrimaryPart = body
		cm.Parent = gs.folder
		gs.crate.model = cm
		local pr = X.prompt(body, "Open  " .. R.crate, "MYSTERY CRATE", R.hold)
		gs.crate.pr = pr
		wire(pr, function(m: any) useCrate(g, gs, m) end)
	end
	-- boards: 6 planks across every window, a prompt on the inside to nail them back (held: one each R.board s)
	for i, w in map.windows do
		gs.planks[i] = R.planks
		local list = {}
		local cf = w.at -- (the opening; LookVector into the room)
		for k = 1, R.planks do
			local y = -2.6 + (k - 1) * (5.2 / (R.planks - 1))
			local tilt = math.rad((if k % 2 == 0 then 1 else -1) * (4 + math.random() * 6))
			local p = part(gs.folder, "Plank", Vector3.new(6.9, 0.75, 0.35), cf * CFrame.new(0, y, 0.25) * CFrame.Angles(0, 0, tilt), WOOD, Enum.Material.WoodPlanks)
			p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
			table.insert(list, p)
		end
		gs.plankParts[i] = list
		local anchor = w.model:FindFirstChild("Boards") :: BasePart?
		if anchor then
			local pr = X.prompt(anchor, "Rebuild", "BOARDS", R.board)
			pr.Enabled = false
			gs.boardPr[i] = pr
			pr.PromptButtonHoldBegan:Connect(function(pl: Player)
				local m = X.buyerOf(g, pl)
				if not m then return end
				local r = X.fight().root(m.f)
				if not r or (r.Position - w.at.Position):Dot(w.n) < 0.3 then return end -- (only from inside)
				gs.boarders[m] = { i = i, nextT = now() + R.board }
			end)
			pr.PromptButtonHoldEnded:Connect(function(pl: Player)
				for m, b in gs.boarders do if m.p == pl and b.i == i then gs.boarders[m] = nil end end
			end)
		end
	end
	for _, m in g.members do publishMe(gs, m) end
	publishMods(g, gs)
end

-- ------------------------------------------------------------------ every tick
local function tick(g: any, _dt: number)
	local gs = GSt[g]
	if not gs then return end
	local n = now()
	local Fight = X.fight()
	-- the machine landing, modifiers running out
	if gs.mach.st == 1 and n >= gs.mach.untilT then machDone(g, gs) end
	local before = #gs.mods
	for i = #gs.mods, 1, -1 do if n >= gs.mods[i].untilT then table.remove(gs.mods, i) end end
	if #gs.mods ~= before or g.tick % 10 == 0 then publishMods(g, gs); for _, m in g.members do publishMe(gs, m) end end
	-- the crate
	local c = gs.crate
	if c.st == 1 and n >= c.untilT then
		c.st, c.untilT = 2, n + R.offer
		if c.model then c.model:SetAttribute("Offer", serverT(R.offer)) end
		if c.pr then c.pr.ActionText = "Take"; c.pr.ObjectText = (W[c.w] and W[c.w].name) or c.w end
	elseif c.st == 2 and (n >= c.untilT or not table.find(g.members, c.by)) then
		crateReset(g, gs)
	end
	-- drops: blink near the end, picked up by walking into them
	for i = #gs.drops, 1, -1 do
		local d = gs.drops[i]
		if n >= d.untilT or not d.part.Parent then
			if d.part.Parent then d.part:Destroy() end
			table.remove(gs.drops, i)
			continue
		end
		if d.untilT - n < R.dropBlink then d.part.Transparency = if math.floor(n * 6) % 2 == 0 then 0.75 else 0 end
		for _, m in g.members do
			local r = m.f.alive and Fight.root(m.f)
			if not r then continue end
			local feet = X.feetOf(r)
			if flat(feet - d.part.Position).Magnitude < R.dropReach + 1.5 and math.abs(feet.Y + 2.7 - d.part.Position.Y) < 6.6 then
				table.remove(gs.drops, i)
				grab(g, gs, d, m)
				break
			end
		end
	end
	-- boarding (held F)
	for m, b in gs.boarders do
		if not m.f.alive or not table.find(g.members, m) then gs.boarders[m] = nil; continue end
		if n >= b.nextT then
			b.nextT = n + R.board
			nail(g, gs, m, b.i)
		end
	end
	-- Bottomless Mag: the gun in your hands stays full
	if n - gs.bottomT > 0.25 then
		gs.bottomT = n
		for _, m in g.members do
			if not m.f.alive or not mod(gs, "bottomless", m) then continue end
			local wid = m.f.held
			local a, wr = m.f.ammo[wid], W[wid]
			if a and wr and wr.mag and (a.mag < wr.mag or a.reloadUntil > 0) then
				a.mag, a.reloadUntil = wr.mag, 0
				local ar = Remotes:FindFirstChild("Ammo")
				if m.p and ar and ar:IsA("RemoteEvent") then ar:FireClient(m.p, wid, wr.mag, 0) end
			end
		end
	end
	-- Big Head Mode: the new ones too
	if mod(gs, "bighead") then
		for _, z in g.mobs do
			if not z.m:GetAttribute("BigHead") then
				local h = z.m:FindFirstChild("Head")
				if h and h:IsA("BasePart") then h.Size *= 2.2 end
				z.m:SetAttribute("BigHead", true)
			end
		end
	end
	-- the Voider's side effects: zaps jump, fires burn
	local zaps = gs.zaps
	gs.zaps = {}
	for _, q in zaps do
		if not q.by.f.alive then continue end
		local from = q.z.root.Position
		local near = {}
		for _, o in g.mobs do
			if o ~= q.z and o.f.alive and (o.root.Position - from).Magnitude <= ZM.UPFX.zap.reach then table.insert(near, o) end
		end
		table.sort(near, function(a, b) return (a.root.Position - from).Magnitude < (b.root.Position - from).Magnitude end)
		for k = 1, math.min(q.n, #near) do Fight.hurt(near[k].f, q.dmg, q.by.f, q.wid, false) end
	end
	for i = #gs.burns, 1, -1 do
		local b = gs.burns[i]
		if n >= b.untilT or not b.z.f.alive then table.remove(gs.burns, i); continue end
		if n >= b.nextT then
			b.nextT = n + 0.5
			Fight.hurt(b.z.f, b.dmg, b.by.f, b.wid, false)
		end
	end
end

-- ------------------------------------------------------------------ the hooks
function ZombieExtra.install(zombies: any)
	Z = zombies
	X = zombies.X
	local ext = zombies.ext
	ext.start = start
	ext.tick = tick
	ext.stop = function(g: any)
		for _, m in g.members do
			local p = m.p
			if p then
				p:SetAttribute("ZmColas", nil); p:SetAttribute("ZmSpeed", nil)
				for wid in ms(m).up do p:SetAttribute("ZmUp_" .. wid, nil) end
			end
			MSt[m] = nil
		end
		GSt[g] = nil
	end
	ext.round = function(g: any)
		local gs = GSt[g]
		if not gs then return end
		gs.dropN = 0
		gs.mach.uses = 0
		machPrompt(gs)
		for _, m in g.members do ms(m).boardN = 0 end
	end
	ext.creditMul = function(g: any, m: any): number?
		local gs = g and GSt[g]
		return if gs and mod(gs, "taxfraud", m) then 2 else nil
	end
	ext.ammoMul = function(_g: any, m: any, wid: string): number?
		local x = ms(m)
		local u = x.up[wid]
		local k = (if hasCola(m, "pockets") then ZM.COLAS.pockets.ammo else 1) * (if u then ZM.UP.ammo[u.t] or 1 else 1)
		return if k ~= 1 then k else nil
	end
	ext.guns = function(_g: any, m: any): number?
		return if hasCola(m, "thirdhand") then ZM.COLAS.thirdhand.guns else nil
	end
	ext.dropGun = function(_g: any, m: any, wid: string)
		ms(m).up[wid] = nil
		if m.p then m.p:SetAttribute("ZmUp_" .. wid, nil) end
	end
	ext.fresh = function(_g: any, m: any)
		local x = ms(m)
		if m.p then for wid in x.up do m.p:SetAttribute("ZmUp_" .. wid, nil) end end
		x.up = {}
	end
	ext.tear = function(g: any, z: any): boolean
		local gs = GSt[g]
		if not gs or (gs.planks[z.win] or 0) <= 0 then return false end
		if g.st == "over" then return true end
		local n = now()
		local t = gs.tear[z]
		if not t then gs.tear[z] = { at = n + 0.4 + math.random() * 0.6, t0 = n }; return true end
		if n - t.t0 > 45 then return false end -- (planks going back up as fast as it rips them: it climbs through anyway)
		if n < t.at then return true end
		t.at = n + (if z.kind > 0 then R.tearRun else R.tear) * (0.8 + math.random() * 0.4) * (if mod(gs, "brainfreeze") then 2.2 else 1)
		gs.planks[z.win] -= 1
		showPlanks(gs, z.win)
		return gs.planks[z.win] > 0
	end
	ext.downed = function(g: any, m: any): number?
		local gs = GSt[g]
		local x = ms(m)
		if hasCola(m, "getup") and g.st ~= "over" then
			table.remove(x.colas, table.find(x.colas, "getup") :: number)
			if gs then publishMe(gs, m) end
			return ZM.COLAS.getup.self
		end
		x.colas = {}
		-- (the third gun goes with Third Hand)
		local cut = false
		while #m.guns > R.guns do
			local wid = table.remove(m.guns) :: string
			m.res[wid] = nil
			x.up[wid] = nil
			if m.p then m.p:SetAttribute("ZmRes_" .. wid, nil); m.p:SetAttribute("ZmUp_" .. wid, nil) end
			cut = true
		end
		if cut then X.arm(m) end
		if gs then publishMe(gs, m) end
		return nil
	end
	ext.clawMul = function(_g: any, m: any): number?
		return if hasCola(m, "jank") then 0.5 else nil
	end
	ext.regenMul = function(_g: any, m: any): number?
		return if hasCola(m, "jank") then 1.6 else nil
	end
	ext.zombieSpeed = function(g: any, z: any): number?
		local gs = GSt[g]
		if not gs then return nil end
		if (gs.frozen[z] or 0) > now() then return 0 end
		return if mod(gs, "brainfreeze") then 0.35 else nil
	end
	ext.allHeads = function(g: any): boolean
		local gs = GSt[g]
		return gs ~= nil and mod(gs, "bighead")
	end
	ext.hitZombie = function(g: any, z: any, amt: number, m: any, wid: string): number
		local gs = GSt[g]
		if not gs or amt <= 0 then return amt end
		local n = now()
		-- the Voider: harder hits, and from the second go a side effect (one every R.fxGap per player)
		local x = ms(m)
		local u = x.up[wid] or x.up[Weapons.base(wid)]
		if u then
			amt *= ZM.UP.mul[u.t] or 1
			local fx = ZM.UPFX[u.fx]
			if fx and n - x.fxT >= R.fxGap then
				x.fxT = n
				if u.fx == "zap" then table.insert(gs.zaps, { z = z, by = m, dmg = amt * fx.part, n = fx.n[u.t] or 2, wid = wid })
				elseif u.fx == "toast" then table.insert(gs.burns, { z = z, by = m, dmg = amt * fx.tick, nextT = n + 0.5, untilT = n + fx.secs, wid = wid })
				elseif u.fx == "frost" then
					if n >= (gs.frostOk[z] or 0) then gs.frozen[z] = n + fx.secs; gs.frostOk[z] = n + fx.again end
				elseif u.fx == "boing" then
					if not z.root.Anchored then z.root.AssemblyLinearVelocity += Vector3.new(0, fx.up, 0) end
				elseif u.fx == "tips" then X.give(m, fx.pay, "tip") end
			end
		end
		-- the machine's
		if mod(gs, "oneshot", m) then amt = math.max(amt, z.f.hp) end
		if mod(gs, "vampire", m) and m.f.alive and m.f.hp < (m.f.maxHp or Weapons.HP) then
			m.f.hp = math.min(m.f.maxHp or Weapons.HP, m.f.hp + math.min(8, amt * 0.15))
			X.fight().syncHp(m.f)
		end
		if mod(gs, "bouncy", m) and not z.root.Anchored then
			local r = X.fight().root(m.f)
			local away = if r then flat(z.root.Position - r.Position) else Vector3.zero
			away = if away.Magnitude > 1e-3 then away.Unit else Vector3.zero
			z.root.AssemblyLinearVelocity = away * 42 + Vector3.new(0, 33, 0)
		end
		return amt
	end
	-- (Studio's ServerStorage.JankZombies passes its other ops here) power; buy <player> <"cola:id" | "void" | "mach" |
	-- "crate">; drop <player> <kind>; x <player>: what stage 2 has going
	ext.test = function(op: string, a: any, b: any): any
		local g = Z.game()
		local gs = g and GSt[g]
		if not g or not gs then return nil end
		local Fight = X.fight()
		local m = if typeof(a) == "Instance" and Fight.byPlayer[a] then g.byF[Fight.byPlayer[a]] else nil
		if op == "power" then powerOn(g, gs, nil); return true
		elseif op == "buy" and m and type(b) == "string" then
			if string.sub(b, 1, 5) == "cola:" then buyCola(g, gs, m, string.sub(b, 6))
			elseif b == "void" then voidIt(g, gs, m)
			elseif b == "mach" then playMach(g, gs, m)
			elseif b == "crate" then useCrate(g, gs, m) end
			return true
		elseif op == "drop" and m and type(b) == "string" and ZM.DROPS[b] then
			local r = Fight.root(m.f)
			if r then dropAt(g, gs, b, X.feetOf(r) + r.CFrame.LookVector * 9 + Vector3.new(0, 3, 0)) end
			return true
		elseif op == "x" then
			local mods = {}
			for _, x in gs.mods do table.insert(mods, x.k .. string.format(" %.0fs", x.untilT - now())) end
			local planksDown = 0
			for _, n in gs.planks do if n < R.planks then planksDown += 1 end end
			return { power = gs.power, mods = mods, mach = gs.mach.st, machUses = gs.mach.uses, crate = gs.crate.st, crateW = gs.crate.w,
				drops = #gs.drops, colas = if m then ms(m).colas else nil, up = if m then ms(m).up else nil, windowsTorn = planksDown,
				guns = if m then table.concat(m.guns, ",") else nil, credits = if m then m.c else nil }
		end
		return nil
	end
	ext.killed = function(g: any, z: any, k: any)
		local gs = GSt[g]
		if not gs or not k or g.st == "over" or gs.dropN >= R.dropCap then return end
		if math.random() >= R.dropChance then return end
		gs.dropN += 1
		local w = g.map.windows[z.win]
		local at = if z.ph ~= "hunt" and w then w.inn else X.feetOf(z.root)
		dropAt(g, gs, ZM.dropPick(), at + Vector3.new(0, 3, 0))
	end
end

return ZombieExtra
