--!strict
-- ZOMBIES stage 3 (web server/zmlimbs.js + zmboss.js): limbs that come off, the special zombies and the mini bosses.
-- it plugs into the mode (Zombies.luau) through Zombies.ext, chaining onto stage 2's hooks (ZombieExtra), and uses the
-- mode's own parts (Zombies.X). the numbers: shared/ZM.luau (LIMB, TYPES, BOSS).
-- limbs: a hit that isn't a headshot is now and then a limb (the web's rule for blasts and bots: our server's hit point
-- is the chest); enough on one and it comes off as a plain part (no blood, no gore), +10. no legs: it crawls; one leg:
-- it hops; no arms: it claws for half, slow at planks. specials: CHONK (huge, slow, pops when it dies), ANKLE BITERS
-- (tiny, fast, three at a time), HARD HAT (headshots dink off the hat three times), SCREAMER (stops and shrieks:
-- every zombie near it speeds up; no sound, the owner's no-voice rule: a ring you see). bosses, one every 5 rounds:
-- THE FLOOR MANAGER (calls a meeting: three ankle biters and everyone near him hyped; charges) and THE MASCOT (jumps on
-- you: the floor ripples). no hit takes more than 6% of a boss
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local TweenService = game:GetService("TweenService")
local Debris = game:GetService("Debris")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local ZM = require(Shared:WaitForChild("ZM"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local ZombieSpecial = {}
local W = Weapons.list
local R = ZM.R
local L = ZM.LIMB
local now = os.clock
local Z: any = nil
local X: any = nil
local GROUP = "JFZombies"

local BIT = { armL = 1, armR = 2, legL = 4, legR = 8, head = 16 }
local LIMBS = { "armL", "armR", "legL", "legR" }
local PARTS = {
	armL = { "LeftUpperArm", "LeftLowerArm", "LeftHand" }, armR = { "RightUpperArm", "RightLowerArm", "RightHand" },
	legL = { "LeftUpperLeg", "LeftLowerLeg", "LeftFoot" }, legR = { "RightUpperLeg", "RightLowerLeg", "RightFoot" },
	head = { "Head" },
}
local ARMS, LEGS = 3, 12
local function crawl(lim: number): boolean return bit32.band(lim, LEGS) == LEGS end
local function hop(lim: number): boolean return bit32.band(lim, LEGS) ~= 0 and not crawl(lim) end

type ZS = {
	ty: string, lim: number, ld: { [string]: number }, hat: number, hatParts: { BasePart }, lhp: number,
	hype: number, yell: number, yellAt: number,
	boss: boolean, hp0: number, t1: number, t2: number,
	charge: { dir: Vector3, go: number, untilT: number, hit: { [any]: boolean } }?, leap: boolean, leapT: number,
}
local ZSt: { [any]: ZS } = setmetatable({}, { __mode = "k" }) :: any
type GS = { pack: { n: number, win: number }?, bossDue: { ty: string, at: number, hp: number, counted: boolean }?, boss: any?, pops: { { at: Vector3, by: any } }, forced: string? }
local GSt: { [any]: GS } = setmetatable({}, { __mode = "k" }) :: any
local function gsOf(g: any): GS
	local x = GSt[g]
	if not x then x = { pack = nil, bossDue = nil, boss = nil, pops = {}, forced = nil }; GSt[g] = x end
	return x
end
local function flat(v: Vector3): Vector3 return Vector3.new(v.X, 0, v.Z) end

-- ------------------------------------------------------------------ looks
local function recolor(m: Model, col: Color3)
	local legs = Color3.new(col.R * 0.45, col.G * 0.45, col.B * 0.45)
	for _, p in m:GetChildren() do
		if p:IsA("BasePart") and p.Name ~= "HumanoidRootPart" then
			p.Color = if string.find(p.Name, "Leg") or string.find(p.Name, "Foot") then legs else col
		end
	end
end
local function plainPart(parent: Instance, size: Vector3, cf: CFrame, col: Color3, shape: Enum.PartType?): Part
	local p = Instance.new("Part")
	p.Size = size; p.CFrame = cf; p.Color = col; p.Material = Enum.Material.SmoothPlastic
	if shape then p.Shape = shape end
	p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.Massless = true; p.Anchored = false
	p.TopSurface = Enum.SurfaceType.Smooth; p.BottomSurface = Enum.SurfaceType.Smooth
	p.Parent = parent
	return p
end
-- the Hard Hat's hat: a dome and a brim on the head
local function hardHat(m: Model): { BasePart }
	local head = m:FindFirstChild("Head") :: BasePart?
	if not head then return {} end
	local yel = Color3.fromHex("ffcf3a")
	local top = head.CFrame * CFrame.new(0, head.Size.Y * 0.45, 0)
	local dome = plainPart(m, Vector3.new(head.Size.X * 1.15, head.Size.Y * 0.55, head.Size.Z * 1.15), top, yel)
	dome.Name = "HatDome"
	local brim = plainPart(m, Vector3.new(0.18, head.Size.X * 1.5, head.Size.Z * 1.5), top * CFrame.new(0, -head.Size.Y * 0.18, 0) * CFrame.Angles(0, 0, math.pi / 2), yel, Enum.PartType.Cylinder)
	brim.Name = "HatBrim"
	for _, p in { dome, brim } do
		local w = Instance.new("WeldConstraint"); w.Part0 = head; w.Part1 = p; w.Parent = p
	end
	return { dome, brim }
end
-- a ring on the floor that grows and fades (the Screamer's shriek, a boss landing): everyone sees it
local function ring(at: Vector3, r: number, col: Color3, parent: Instance)
	local p = Instance.new("Part")
	p.Shape = Enum.PartType.Cylinder; p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
	p.Material = Enum.Material.Neon; p.Color = col; p.Transparency = 0.25
	p.Size = Vector3.new(0.3, 2, 2)
	p.CFrame = CFrame.new(at) * CFrame.Angles(0, 0, math.pi / 2)
	p.Parent = parent
	TweenService:Create(p, TweenInfo.new(0.55, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(0.3, r * 2, r * 2), Transparency = 1 }):Play()
	Debris:AddItem(p, 0.7)
end
-- a bit comes off: a plain copy flies, the one on the body goes invisible (nothing hits it)
local function cut(g: any, z: any, limb: string, by: any?, dead: boolean)
	local s = ZSt[z]
	if not s then return end
	local b = BIT[limb]
	if not b or bit32.band(s.lim, b) ~= 0 then return end
	s.lim = bit32.bor(s.lim, b)
	local away = Vector3.new(math.random() - 0.5, 0.6, math.random() - 0.5).Unit
	if by then
		local r = X.fight().root(by.f)
		if r then
			local d = flat(z.root.Position - r.Position)
			if d.Magnitude > 1e-3 then away = (d.Unit + Vector3.new(0, 0.6, 0)).Unit end
		end
	end
	for _, name in PARTS[limb] do
		local p = z.m:FindFirstChild(name)
		if not p or not p:IsA("BasePart") then continue end
		local c = p:Clone()
		for _, d in c:GetChildren() do if not d:IsA("SpecialMesh") then d:Destroy() end end
		c.Anchored = false; c.CanCollide = true; c.CanQuery = false; c.CanTouch = false; c.Massless = false
		c.CollisionGroup = GROUP
		c.Parent = g.model
		c.AssemblyLinearVelocity = away * (28 + math.random() * 14)
		c.AssemblyAngularVelocity = Vector3.new(math.random() * 16 - 8, math.random() * 16 - 8, math.random() * 16 - 8)
		Debris:AddItem(c, 4)
		p.Transparency = 1
		p.CanQuery = false
		for _, d in p:GetChildren() do if d:IsA("Decal") then d.Transparency = 1 end end
	end
	if limb == "head" then for _, h in s.hatParts do h.Transparency = 1 end end
	if not dead then
		if by then X.give(by, L.limbPay, "limb") end
		if crawl(s.lim) then
			z.kind = 0
			z.hum.HipHeight = math.max(0.4, z.hum.HipHeight * 0.25) -- (dragging itself along)
		elseif hop(s.lim) then
			z.kind = 0
		end
	end
end

-- ------------------------------------------------------------------ a new zombie: its kind, size, hat, limbs, boss HP
local function spawned(g: any, z: any)
	local gs = gsOf(g)
	local n = now()
	local alive = {}
	for _, o in g.mobs do
		local os_ = ZSt[o]
		if os_ and os_.ty ~= "" and o.f.alive then alive[os_.ty] = (alive[os_.ty] or 0) + 1 end
	end
	local ty = ""
	local bd = gs.bossDue
	if bd and bd.counted and n >= bd.at then
		ty = bd.ty
	elseif gs.pack and gs.pack.n > 0 then
		ty = "biter"
	elseif gs.forced then
		ty = gs.forced :: string
		gs.forced = nil
	else
		ty = ZM.pickType(g.n, alive)
	end
	local def = ZM.TYPES[ty]
	local s: ZS = {
		ty = ty, lim = 0, ld = {}, hat = 0, hatParts = {}, lhp = 0, hype = 0, yell = 0, yellAt = n + 4 + math.random() * 4,
		boss = false, hp0 = 0, t1 = 0, t2 = 0, charge = nil, leap = false, leapT = 0,
	}
	ZSt[z] = s
	local f = z.f
	if def then
		f.maxHp = math.max(1, math.floor((f.maxHp or 100) * def.hp + 0.5))
		if def.speed then z.speed = def.speed * (0.94 + math.random() * 0.12) end
		if def.run ~= nil then z.kind = def.run end
		if def.color then recolor(z.m, def.color) end
		s.hat = def.hat or 0
		if def.pack then
			if gs.pack and gs.pack.n > 0 then gs.pack.n -= 1
			else gs.pack = { n = math.min(def.pack - 1, g.toSpawn), win = z.win } end -- (the rest of the litter: the same window)
		end
		local k = def.scale or 1
		if k ~= 1 then
			z.k = k
			pcall(function() z.m:ScaleTo(k) end)
			local w = g.map.windows[z.win]
			local at = z.root.Position - Vector3.new(0, Hitbox.ROOT_UP, 0) + Vector3.new(0, Hitbox.ROOT_UP * k, 0)
			z.m:PivotTo(CFrame.lookAt(at, at + w.n))
		end
		if s.hat > 0 then s.hatParts = hardHat(z.m) end
		z.m:SetAttribute("ZmType", ty)
	end
	if def and def.boss then
		local members = #g.members
		local max = math.floor(ZM.hp(g.n) * def.bossHp * (1 + ZM.BOSS.perPlayer * (math.max(1, members) - 1)) + 0.5)
		f.maxHp = max
		f.hp = if bd and bd.hp > 0 then math.min(max, bd.hp) else max
		gs.bossDue = nil
		s.boss, s.hp0, s.t1, s.t2 = true, max, n + 6, n + 9
		gs.boss = z
		-- its name over it
		local bb = Instance.new("BillboardGui")
		bb.Size = UDim2.fromOffset(260, 30); bb.StudsOffset = Vector3.new(0, 3.5, 0); bb.AlwaysOnTop = false; bb.MaxDistance = 140
		local t = Instance.new("TextLabel")
		t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(1, 1); t.Text = def.name; t.TextColor3 = def.color
		t.TextStrokeTransparency = 0.35; t.TextScaled = true; t.FontFace = Font.new("rbxasset://fonts/families/BuilderSans.json", Enum.FontWeight.Heavy)
		t.Parent = bb
		bb.Adornee = z.m:FindFirstChild("Head") :: BasePart?
		bb.Parent = z.m
		g.model:SetAttribute("BossName", def.name)
		g.model:SetAttribute("BossMax", max)
		g.model:SetAttribute("BossHp", f.hp)
	else
		f.hp = f.maxHp or f.hp
		s.lhp = math.max(L.limbMin, (f.maxHp or 100) * L.limbHp)
	end
	z.hum.MaxHealth, z.hum.Health = f.maxHp or 100, f.hp
	z.hum.WalkSpeed = z.speed
	if not def and math.random() < L.bornArmless then cut(g, z, "armL", nil, false) end -- (the odd one turns up an arm short)
end

-- ------------------------------------------------------------------ hits (after stage 2's: the Voider, the machine)
local function hit(g: any, z: any, amt: number, m: any, wid: string): number
	local s = ZSt[z]
	if not s or amt <= 0 then return amt end
	if s.boss then return math.min(amt, s.hp0 * ZM.BOSS.hitCap) end -- (no one-shots: the sniper, ONE AND DONE)
	local Fight = X.fight()
	local zone: string? = if Fight.hitHs == true then "head" else nil
	if zone == "head" and s.hat > 0 then -- HARD HAT: it dinks off the hat
		s.hat -= 1
		amt *= 0.35
		if s.hat == 0 then
			for _, h in s.hatParts do
				h:ClearAllChildren()
				h.Anchored = false; h.CanCollide = true; h.Massless = false; h.Parent = g.model
				h.AssemblyLinearVelocity = Vector3.new(math.random() * 20 - 10, 40, math.random() * 20 - 10)
				Debris:AddItem(h, 4)
			end
			s.hatParts = {}
		end
	end
	local left = {}
	for _, l in LIMBS do if bit32.band(s.lim, BIT[l]) == 0 then table.insert(left, l) end end
	if not zone then zone = if #left > 0 and math.random() < L.random then left[math.random(1, #left)] else "torso" end
	local lethal = amt >= z.f.hp
	local zn = zone :: string
	if BIT[zn] and zn ~= "head" and bit32.band(s.lim, BIT[zn]) == 0 then
		s.ld[zn] = (s.ld[zn] or 0) + amt
		if lethal or s.ld[zn] >= s.lhp then cut(g, z, zn, if lethal then nil else m, lethal) end
	elseif zn == "head" and lethal then
		cut(g, z, "head", nil, true)
	end
	local w = W[wid]
	if lethal and w and w.kind ~= "hitscan" and w.kind ~= "melee" then -- (blown up, bowled over: more bits)
		for _, l in LIMBS do if math.random() < 0.5 then cut(g, z, l, nil, true) end end
	end
	return amt
end

-- ------------------------------------------------------------------ a Chonk pops: zombies near it take the blast (the
-- kills are the shooter's), the squad gets shoved and slips
local function pop(g: any, at: Vector3, by: any?)
	local C = ZM.TYPES.chonk
	local Fight = X.fight()
	local ball = Instance.new("Part")
	ball.Shape = Enum.PartType.Ball; ball.Anchored = true; ball.CanCollide = false; ball.CanQuery = false; ball.CanTouch = false
	ball.Material = Enum.Material.Neon; ball.Color = C.color; ball.Size = Vector3.new(3, 3, 3); ball.CFrame = CFrame.new(at + Vector3.new(0, 3, 0))
	ball.Parent = g.model
	TweenService:Create(ball, TweenInfo.new(0.35, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), { Size = Vector3.new(C.blast * 2, C.blast * 2, C.blast * 2), Transparency = 1 }):Play()
	Debris:AddItem(ball, 0.5)
	for _, o in table.clone(g.mobs) do
		if not o.f.alive then continue end
		local d = flat(o.root.Position - at)
		if d.Magnitude > C.blast or math.abs(o.root.Position.Y - at.Y) > 9 then continue end
		local f = 1 - (d.Magnitude / C.blast) * 0.6
		local kb = (if d.Magnitude > 1e-3 then d.Unit else Vector3.zero) * 39 * f + Vector3.new(0, 24 * f, 0)
		Fight.hurt(o.f, C.blastZ * f, if by and by.f.alive then by.f else nil, "chicken", false, kb, o.root.Position)
	end
	local SlipR = Remotes:FindFirstChild("Slip")
	for _, m in g.members do
		local r = m.f.alive and Fight.root(m.f)
		if not r then continue end
		local d = flat(r.Position - at)
		if d.Magnitude > C.blast or math.abs(r.Position.Y - at.Y) > 9 then continue end
		local f = 1 - (d.Magnitude / C.blast) * 0.6
		local kb = (if d.Magnitude > 1e-3 then d.Unit else Vector3.zero) * 39 * f + Vector3.new(0, 24 * f, 0)
		Fight.hurt(m.f, C.blastP * f, nil, "chicken", false, kb, r.Position)
		if m.p and m.f.alive and d.Magnitude < C.blast * 0.7 and SlipR and SlipR:IsA("RemoteEvent") then
			m.f.slipT = os.clock()
			SlipR:FireClient(m.p, "marbles")
		end
	end
end

-- ------------------------------------------------------------------ every tick
local function tick(g: any, _dt: number)
	local gs = gsOf(g)
	local n = now()
	local Fight = X.fight()
	-- a boss on its way: one more on the round's list (it walks in ZM.BOSS.delay s after the round starts)
	local bd = gs.bossDue
	if bd and not bd.counted and g.st == "live" then
		bd.counted = true
		bd.at = n + ZM.BOSS.delay
		g.toSpawn += 1
		X.sayAll({ k = "boss", st = "warn", name = ZM.TYPES[bd.ty].name })
	end
	-- Chonks going off
	local pops = gs.pops
	gs.pops = {}
	for _, p in pops do pop(g, p.at, p.by) end
	if g.st == "over" then return end
	for _, z in g.mobs do
		local s = ZSt[z]
		if not s or not z.f.alive or z.ph ~= "hunt" then continue end
		local t = z.target
		local tr = t and t.f.alive and Fight.root(t.f)
		-- the Screamer: it stops and shrieks, everything near it speeds up
		if s.ty == "screamer" and n >= s.yellAt then
			local S_ = ZM.TYPES.screamer
			if not tr or flat(tr.Position - z.root.Position).Magnitude > S_.see then
				s.yellAt = n + 0.8
			else
				s.yellAt = n + S_.every * (0.85 + math.random() * 0.3)
				s.yell = n + S_.yell
				for _, o in g.mobs do
					local oz = ZSt[o]
					if o ~= z and oz and flat(o.root.Position - z.root.Position).Magnitude <= S_.reach then oz.hype = n + S_.hype end
				end
				ring(X.feetOf(z.root) + Vector3.new(0, 0.3, 0), S_.reach, S_.color, g.model)
			end
		end
		if not s.boss then continue end
		-- a boss
		local def = ZM.TYPES[s.ty]
		g.model:SetAttribute("BossHp", math.max(0, math.floor(z.f.hp + 0.5)))
		local ch = s.charge
		if ch and n >= ch.go and n < ch.untilT then -- a charge: anyone it reaches goes flying (once each)
			for _, m in g.members do
				local r = m.f.alive and Fight.root(m.f)
				if not r or ch.hit[m] then continue end
				if flat(r.Position - z.root.Position).Magnitude > def.charge.reach * 1.6 or math.abs(r.Position.Y - z.root.Position.Y) > 7.5 then continue end
				ch.hit[m] = true
				Fight.hurt(m.f, def.charge.dmg, z.f, "claw", false, ch.dir * def.charge.kb + Vector3.new(0, 21, 0), r.Position)
			end
		end
		if ch and n >= ch.untilT then
			s.charge = nil
			local hl = z.m:FindFirstChild("ZmCharge")
			if hl then hl:Destroy() end
		end
		-- a jump coming down: the floor ripples
		if s.leap and n > s.leapT + 0.35 and z.hum.FloorMaterial ~= Enum.Material.Air then
			s.leap = false
			local J = def.jump
			local at = X.feetOf(z.root)
			ring(at + Vector3.new(0, 0.3, 0), J.r, def.color, g.model)
			local SlipR = Remotes:FindFirstChild("Slip")
			for _, m in g.members do
				local r = m.f.alive and Fight.root(m.f)
				if not r then continue end
				local d = flat(r.Position - at)
				if d.Magnitude > J.r or math.abs(r.Position.Y - z.root.Position.Y) > 6 then continue end
				local f = 1 - (d.Magnitude / J.r) * 0.7
				local dir = if d.Magnitude > 1e-3 then d.Unit else Vector3.zero
				Fight.hurt(m.f, J.dmg * f, z.f, "claw", false, dir * 24 * f + Vector3.new(0, 27 * f, 0), r.Position)
				if m.p and m.f.alive and d.Magnitude < J.r * 0.6 and SlipR and SlipR:IsA("RemoteEvent") then
					m.f.slipT = os.clock(); SlipR:FireClient(m.p, "marbles")
				end
			end
		end
		if s.charge or s.leap or not tr then continue end
		local dv = tr.Position - z.root.Position
		local d, dy = flat(dv).Magnitude, math.abs(dv.Y)
		if def.meeting and n >= s.t1 then -- the Floor Manager calls a meeting
			local M = def.meeting
			s.t1 = n + M.every * (0.85 + math.random() * 0.3)
			s.yell = n + M.yell
			if g.st == "live" then
				-- three ankle biters through the open window nearest him
				local best, bdist = z.win, math.huge
				for i, w in g.map.windows do
					if g.areas[w.area] then
						local dd = flat(w.inn - z.root.Position).Magnitude
						if dd < bdist then bdist, best = dd, i end
					end
				end
				g.toSpawn += M.n
				gs.pack = { n = M.n, win = best }
				g.spawnAt = math.min(g.spawnAt, n + 0.4)
			end
			for _, o in g.mobs do
				local oz = ZSt[o]
				if o ~= z and oz and flat(o.root.Position - z.root.Position).Magnitude <= M.reach then oz.hype = n + M.hype end
			end
			ring(X.feetOf(z.root) + Vector3.new(0, 0.3, 0), M.reach, def.color, g.model)
			X.sayAll({ k = "boss", st = "meeting", name = def.name })
			continue
		end
		if def.charge and n >= s.t2 and d > def.charge.min and d < def.charge.max and dy < 4.5 then -- ... and charges
			local from = z.root.Position + Vector3.new(0, 1.5, 0)
			if not workspace:Raycast(from, Vector3.new(dv.X, 0, dv.Z), g.nav.params) then
				s.t2 = n + def.charge.every * (0.85 + math.random() * 0.3)
				s.charge = { dir = flat(dv).Unit, go = n + def.charge.windup, untilT = n + def.charge.windup + def.charge.secs, hit = {} }
				local hl = Instance.new("Highlight")
				hl.Name = "ZmCharge"; hl.FillColor = def.color; hl.OutlineColor = Color3.new(1, 1, 1); hl.FillTransparency = 0.45
				hl.Parent = z.m
				continue
			end
		end
		if def.jump and n >= s.t1 and z.hum.FloorMaterial ~= Enum.Material.Air and d > def.jump.min and d < def.jump.max and dy < 9 then -- the Mascot jumps on you
			s.t1 = n + def.jump.every * (0.85 + math.random() * 0.3)
			local up = def.jump.up
			local T = 2 * up / workspace.Gravity
			local v = Vector3.new(dv.X / T, up, dv.Z / T)
			z.hum:ChangeState(Enum.HumanoidStateType.Jumping)
			task.defer(function() if z.root.Parent then z.root.AssemblyLinearVelocity = v end end)
			s.leap, s.leapT = true, n
		end
	end
end

-- ------------------------------------------------------------------ the hooks (chained onto stage 2's)
local function chainMul(ext: any, name: string, fn: (...any) -> number?)
	local prev = ext[name]
	ext[name] = function(...: any): number?
		local a = if prev then prev(...) else nil
		local b = fn(...)
		if type(a) ~= "number" then return b end
		if type(b) ~= "number" then return a end
		return a * b
	end
end
local function chainCall(ext: any, name: string, fn: (...any) -> ())
	local prev = ext[name]
	ext[name] = function(...: any)
		if prev then prev(...) end
		fn(...)
	end
end

function ZombieSpecial.install(zombies: any)
	Z = zombies
	X = zombies.X
	local ext = zombies.ext
	ext.spawned = function(g: any, z: any) spawned(g, z) end
	ext.packWindow = function(g: any): number?
		local gs = gsOf(g)
		local pk = gs.pack
		if pk and pk.n > 0 and g.map.windows[pk.win] and g.areas[g.map.windows[pk.win].area] then return pk.win end
		return nil
	end
	ext.steer = function(_g: any, z: any): Vector3?
		local s = ZSt[z]
		local ch = s and s.charge
		return if ch then ch.dir else nil
	end
	chainMul(ext, "zombieSpeed", function(_g: any, z: any): number?
		local s = ZSt[z]
		if not s then return nil end
		local n = now()
		if n < s.yell then return 0 end -- (busy shrieking, calling a meeting)
		local ch = s.charge
		if ch then
			if n < ch.go then return 0 end
			if n < ch.untilT then return ZM.TYPES[s.ty].charge.speed / math.max(1, z.speed) end
		end
		local base = if crawl(s.lim) then math.min(1, L.crawl / math.max(0.1, z.speed)) elseif hop(s.lim) then L.hop else 1
		return base * (if n < s.hype then ZM.TYPES.screamer.boost else 1)
	end)
	ext.zClaw = function(_g: any, z: any): number?
		local s = ZSt[z]
		if not s then return nil end
		local def = ZM.TYPES[s.ty]
		return ((def and def.claw) or 1) * (if bit32.band(s.lim, ARMS) == ARMS then L.noArms else 1)
	end
	ext.zCd = function(_g: any, z: any): number?
		local s = ZSt[z]
		if not s then return nil end
		local def = ZM.TYPES[s.ty]
		return ((def and def.cd) or 1) * (if bit32.band(s.lim, ARMS) ~= 0 then L.oneArmCd else 1)
	end
	ext.reachUp = function(_g: any, z: any): number?
		local s = ZSt[z]
		if not s then return nil end
		if crawl(s.lim) then return L.crawlUp end
		return R.reachUp * math.min(1.15, z.k or 1)
	end
	ext.canJump = function(_g: any, z: any): boolean
		local s = ZSt[z]
		return not (s and bit32.band(s.lim, LEGS) ~= 0)
	end
	ext.tearMul = function(_g: any, z: any): number?
		local s = ZSt[z]
		if not s then return nil end
		local a = bit32.band(s.lim, ARMS)
		return if a == ARMS then L.noArmTear elseif a ~= 0 then L.oneArmTear else nil
	end
	ext.lost = function(g: any, z: any) -- lost or wedged: a boss comes back as itself, as hurt as it was
		local s = ZSt[z]
		if s and s.boss then
			local gs = gsOf(g)
			gs.bossDue = { ty = s.ty, at = now() + 1.5, hp = math.max(1, z.f.hp), counted = true }
			gs.boss = nil
		end
	end
	local prevHit = ext.hitZombie
	ext.hitZombie = function(g: any, z: any, amt: number, m: any, wid: string): number
		local a = if prevHit then prevHit(g, z, amt, m, wid) else amt
		if type(a) ~= "number" then a = amt end
		return hit(g, z, a, m, wid)
	end
	chainCall(ext, "killed", function(g: any, z: any, k: any)
		local s = ZSt[z]
		if not s then return end
		local def = ZM.TYPES[s.ty]
		if not def then return end
		local gs = gsOf(g)
		if def.boss then
			gs.boss = nil
			for _, m in g.members do X.give(m, def.reward, "boss") end
			g.model:SetAttribute("BossName", nil); g.model:SetAttribute("BossHp", nil); g.model:SetAttribute("BossMax", nil)
			if ext.dropAt then ext.dropAt(g, nil, X.feetOf(z.root) + Vector3.new(0, 3, 0)) end -- (a drop for certain)
			X.sayAll({ k = "boss", st = "dead", name = def.name })
			return
		end
		if def.pay and k then X.give(k, def.pay, s.ty) end
		if def.blast then table.insert(gs.pops, { at = X.feetOf(z.root), by = k }) end
	end)
	chainCall(ext, "round", function(g: any)
		local gs = gsOf(g)
		gs.pack = nil
		local nextN = g.n + 1 -- (called just before the round number goes up)
		if nextN % ZM.BOSS.every == 0 then
			local ty = ZM.BOSSES[((nextN // ZM.BOSS.every) - 1) % #ZM.BOSSES + 1]
			gs.bossDue = { ty = ty, at = math.huge, hp = 0, counted = false }
		end
	end)
	chainCall(ext, "tick", tick)
	chainCall(ext, "stop", function(g: any) GSt[g] = nil end)
	-- (Studio's ServerStorage.JankZombies) type <kind>: the next zombie is one; boss: the next one is the boss
	local prevTest = ext.test
	ext.test = function(op: string, a: any, b: any): any
		local g = Z.game()
		if g and op == "type" and type(a) == "string" and ZM.TYPES[a] then
			local gs = gsOf(g)
			if ZM.TYPES[a].boss then gs.bossDue = { ty = a, at = now(), hp = 0, counted = true }; g.toSpawn += 1
			elseif a == "biter" then gs.pack = { n = 3, win = 1 }; g.toSpawn += 3
			else gs.forced = a end
			return true
		elseif g and op == "specials" then
			local out = {}
			for _, z in g.mobs do
				local s = ZSt[z]
				if s and (s.ty ~= "" or s.lim ~= 0) then table.insert(out, string.format("%s lim%d hp%d%s", s.ty, s.lim, math.floor(z.f.hp), if s.boss then " BOSS" else "")) end
			end
			return out
		end
		return if prevTest then prevTest(op, a, b) else nil
	end
	local _ = Players
end

return ZombieSpecial
