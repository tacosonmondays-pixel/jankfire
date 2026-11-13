--!strict
-- bots that fill the match's empty seats (MODES.md: room size = Bots + 1, every person takes a bot's seat, a bot that
-- has to go leaves when it dies or at the next round). a cheap DM brain (BotBrain.luau): hunt the nearest enemy it can
-- see, keep the range its weapon likes, strafe and hop, pick the right one of the three weapons, grapple across gaps
-- and out of the smog, and now and then parry. bodies are the server's (no client), but every shot, swing and parry
-- goes through the same Rules as a player's: the server's own line of sight, ammo, rate, reach, cone, window
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Maps = require(Shared:WaitForChild("Maps"))
local Config = require(Shared:WaitForChild("Config"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local BotBrain = require(script.Parent:WaitForChild("BotBrain"))

type Fighter = Rules.Fighter
local Bots = {}
local S = Weapons.S
local W = Weapons.list
local Fight: any
local api: any
local now = os.clock

type Brain = {
	strafe: number, strafeT: number, target: Fighter?, retarget: number, seenAt: number, jumpT: number,
	hook: { p: Vector3, len: number, t0: number, rope: Beam?, a1: Attachment? }?, slipUntil: number, leaving: boolean,
	floorY: number, stuckT: number, lastPos: Vector3?, think: number,
}
local list: { Fighter } = {}
local brain: { [Fighter]: Brain } = {}

local folder = Instance.new("Folder")
folder.Name = "Bots"
folder.Parent = workspace

local COLORS = { Color3.fromRGB(255, 79, 216), Color3.fromRGB(79, 216, 255), Color3.fromRGB(57, 255, 20), Color3.fromRGB(255, 154, 58), Color3.fromRGB(176, 125, 255), Color3.fromRGB(255, 225, 77) }

-- the knobs (ServerStorage.JankfireConfig attributes, like the web game's JF_* env vars)
local function knob(name: string, default: number): number
	local c = ServerStorage:FindFirstChild("JankfireConfig")
	local v = c and c:GetAttribute(name)
	return if type(v) == "number" then v else default
end
Bots.knob = knob

-- ------------------------------------------------------------------ bodies
local function make(f: Fighter, at: Vector3?)
	local m = api.body(f.name, COLORS[(f.id % #COLORS) + 1]) :: Model
	m:PivotTo(CFrame.new((at or Vector3.new(0, 5, 0)) + Vector3.new(0, Hitbox.ROOT_UP + 0.2, 0)))
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.MaxHealth, hum.Health = Weapons.HP, Weapons.HP
		hum.WalkSpeed = Config.gSpeed -- the run speed (10 m/s)
		hum.JumpPower = Config.jump; hum.UseJumpPower = true
		hum.AutoRotate = false -- it faces its target, not where it walks
		hum.BreakJointsOnDeath = true
		hum.DisplayName = f.name
	end
	local hs = m:FindFirstChild("Health")
	if hs then hs:Destroy() end
	m:SetAttribute("Bot", true)
	m.Parent = folder
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if root then pcall(function() root:SetNetworkOwner(nil) end) end
	f.ref = m
	Fight.byModel[m] = f
	Fight.showWeapon(f)
	local b = brain[f]
	if b then b.hook = nil; b.target = nil; b.floorY = (at or Vector3.zero).Y; b.slipUntil = 0 end
end

local function dropHook(b: Brain)
	local h = b.hook
	if not h then return end
	if h.rope then h.rope:Destroy() end
	if h.a1 then h.a1:Destroy() end
	b.hook = nil
end

-- ------------------------------------------------------------------ seats
local function newBot(): Fighter
	local taken = {}
	for _, o in Fight.all do taken[o.name] = true end
	local free = {}
	for _, n in BotBrain.NAMES do if not taken[n .. " [bot]"] then table.insert(free, n) end end
	local pool = if #free > 0 then free else BotBrain.NAMES
	local f = Rules.newFighter("bot", pool[math.random(#pool)] .. " [bot]", nil)
	brain[f] = { strafe = 1, strafeT = 0, target = nil, retarget = 0, seenAt = 0, jumpT = 0, hook = nil, slipUntil = 0, leaving = false, floorY = 0, stuckT = 0, lastPos = nil, think = 0 }
	table.insert(list, f)
	table.insert(Fight.all, f)
	return f
end
local function removeBot(f: Fighter)
	local b = brain[f]
	if b then dropHook(b) end
	brain[f] = nil
	local i = table.find(list, f); if i then table.remove(list, i) end
	local j = table.find(Fight.all, f); if j then table.remove(Fight.all, j) end
	if f.ref then Fight.byModel[f.ref] = nil; f.ref:Destroy() end
end

-- people came, went, or a round starts: add bots, or mark extra ones to leave (now if dead, else when they die)
function Bots.seats()
	local humans = 0
	for _, f in Fight.all do if f.kind == "player" and f.room == "ffa" then humans += 1 end end
	local want = BotBrain.wanted(humans, knob("Bots", 5) + 1)
	local staying = {}
	for _, f in list do if not brain[f].leaving then table.insert(staying, f) end end
	while #staying > want do
		local f = table.remove(staying) :: Fighter
		brain[f].leaving = true
		if not f.alive or not Fight.live then removeBot(f) end
	end
	while #staying < want do
		local f = newBot()
		table.insert(staying, f)
		if Fight.live then task.spawn(Fight.spawn, f) end
	end
end

-- ------------------------------------------------------------------ fighting (through the server's own rules)
local function face(f: Fighter, at: Vector3)
	local r = Fight.root(f)
	if not r then return end
	local d = Vector3.new(at.X - r.Position.X, 0, at.Z - r.Position.Z)
	if d.Magnitude > 0.1 then r.CFrame = CFrame.lookAt(r.Position, r.Position + d) end
end

-- one trigger pull at t: the bot's own rays (aim error, the gun's spread), the map first, then the target's boxes
local function shoot(f: Fighter, t: Fighter, wid: string): boolean
	local eye, tr = Fight.eye(f), Fight.root(t)
	if not eye or not tr then return false end
	if Rules.fire(f, wid, now(), eye, eye) then return false end
	local w = W[wid]
	local tf = Hitbox.feet(tr.Position)
	local aimAt = tf + Vector3.new(0, if math.random() < 0.2 then 5.8 else 3.6, 0)
	local aim = (aimAt - eye).Unit
	local n, h, ends = 0, 0, {}
	for _ = 1, w.pellets or 1 do
		local d = Hitbox.spreadDir(aim, (w.spread or 0) + BotBrain.DIFF.err, math.random(), math.random())
		local mh = Fight.castMap(eye, d, w.range)
		local mapT = if mh then (mh.Position - eye).Magnitude else w.range
		local tt, head = Hitbox.ray(eye, d, tf, 1)
		local endT = mapT
		if tt and tt < mapT then n += 1; if head then h += 1 end; endT = tt end
		if #ends < 12 then table.insert(ends, eye + d * endT) end
	end
	api.shot(Fight.model(f), wid, ends)
	if w.marbles then api.makePatch(f, eye, ends) end -- bots' marbles trip people too
	if n > 0 then
		local why, nn, hh = Rules.hit(f, t, wid, n, h, now(), {
			dist = (tf - Hitbox.feet((Fight.root(f) :: BasePart).Position)).Magnitude, speedF = 0, speedT = 0, los = Fight.sees(eye, t),
		})
		if not why then api.applyHitscan(f, t, wid, nn, hh, eye) end
	end
	local a = Rules.ammoOf(f, wid, now())
	if a and a.mag <= 0 then Rules.reload(f, wid, now()) end
	return true
end

local function swing(f: Fighter, t: Fighter)
	if Rules.swing(f, "katana", now()) then return end
	api.fx({ k = "swing", model = Fight.model(f), w = "katana" })
	task.delay(W.katana.hitT :: number, function()
		local eye, tr = Fight.eye(f), Fight.root(t)
		if not eye or not tr or not f.alive then return end
		api.applyMelee(f, t, "katana", (tr.Position - eye).Unit)
	end)
end

-- ------------------------------------------------------------------ the grapple (the bot's own rope physics, hookphys)
local function hookTo(f: Fighter, b: Brain, p: Vector3)
	local r = Fight.root(f)
	if not r then return end
	dropHook(b)
	local a1 = Instance.new("Attachment"); a1.WorldPosition = p; a1.Parent = workspace.Terrain
	local hand = (Fight.model(f) :: Model):FindFirstChild("RightHand") or r
	local a0 = hand:FindFirstChildWhichIsA("Attachment")
	local rope = Instance.new("Beam")
	rope.Attachment0 = a0; rope.Attachment1 = a1; rope.Width0 = 0.25; rope.Width1 = 0.25; rope.FaceCamera = true
	rope.Color = ColorSequence.new(Color3.fromRGB(255, 79, 216), Color3.fromRGB(255, 225, 77)); rope.LightEmission = 0.6
	rope.Parent = workspace.Terrain
	b.hook = { p = p, len = (p - r.Position).Magnitude, t0 = now(), rope = rope, a1 = a1 }
	local hum = Fight.hum(f)
	if hum then hum:ChangeState(Enum.HumanoidStateType.Freefall) end
end

local function ropeStep(f: Fighter, b: Brain, dt: number)
	local h = b.hook
	local r = Fight.root(f)
	if not h or not r then return end
	local H = Config.hook
	local d = h.p - r.Position
	local dist = d.Magnitude
	if dist < H.near + 1 or now() - h.t0 > 3 then dropHook(b); return end
	local n = d / dist
	local v = r.AssemblyLinearVelocity + n * H.pull * dt + Vector3.new(0, Config.grav * H.lift * dt, 0)
	h.len = math.min(h.len, dist)
	local radial = v:Dot(n)
	if dist >= h.len - 0.15 and radial < 0 then v -= n * radial end
	r.AssemblyLinearVelocity = v
end

-- a point to hook: the first solid thing along a ray from the head (in range), or nil
local function hookPoint(eye: Vector3, dir: Vector3): Vector3?
	local hit = Fight.castMap(eye, dir.Unit, Config.hook.range)
	return hit and hit.Position
end

-- ------------------------------------------------------------------ marbles
function Bots.slip(f: Fighter)
	local b, hum, root = brain[f], Fight.hum(f), Fight.root(f)
	if not b or not hum or not root then return end
	b.slipUntil = now() + Weapons.SLIP.time
	dropHook(b)
	local v = root.AssemblyLinearVelocity
	local flat = Vector3.new(v.X, 0, v.Z)
	local d = if flat.Magnitude > 0.1 then flat.Unit else root.CFrame.LookVector
	hum.PlatformStand = true
	root.AssemblyLinearVelocity = v + d * (4 * S) + Vector3.new(0, Weapons.SLIP.up, 0)
end

-- ------------------------------------------------------------------ the brain, 10 times a second (the rope every step)
local lastTick = now()
function Bots.tick(n: number)
	local dt = math.min(0.1, n - lastTick)
	lastTick = n
	for _, f in table.clone(list) do
		local b = brain[f]
		if not b then continue end
		if b.leaving and (not f.alive or not Fight.live) then removeBot(f); continue end
		local hum, root = Fight.hum(f), Fight.root(f)
		if not f.alive or not hum or not root then if b then dropHook(b) end continue end
		if root.Position.Y < Maps.killY(root.Position) then dropHook(b); Fight.void(f); continue end
		ropeStep(f, b, dt)
		if hum.PlatformStand then
			if n > b.slipUntil then hum.PlatformStand = false; hum:ChangeState(Enum.HumanoidStateType.GettingUp) end
			continue
		end
		if n < b.think then continue end
		b.think = n + 0.1
		if not Fight.live then hum:Move(Vector3.zero); continue end
		local eye = Fight.eye(f) :: Vector3
		-- the target (re-picked every 0.4-1 s)
		if n > b.retarget or (b.target and not b.target.alive) then
			local seen = {}
			for _, o in Fight.all do
				if o ~= f and o.alive and o.room == "ffa" and o.kind ~= "dummy" then
					local orr = Fight.root(o)
					if orr then table.insert(seen, { f = o, dist = (orr.Position - root.Position).Magnitude, vis = Fight.sees(eye, o) }) end
				end
			end
			local pick = BotBrain.target(seen)
			b.target = pick and pick.f
			b.retarget = n + 0.4 + math.random() * 0.6
		end
		local t = b.target
		local tr = t and Fight.root(t)
		local wish = Vector3.zero
		local grounded = hum.FloorMaterial ~= Enum.Material.Air
		if grounded then b.floorY = root.Position.Y end
		if t and tr then
			local to = tr.Position - root.Position
			local dist = to.Magnitude
			local vis = Fight.sees(eye, t)
			if vis and b.seenAt == 0 then b.seenAt = n elseif not vis then b.seenAt = 0 end
			-- the right weapon for the range
			local want = BotBrain.weapon(dist, f.held, f.kat)
			if want ~= f.held and Rules.equip(f, want, n) == nil then Fight.showWeapon(f) end
			local lo, hi = BotBrain.pref(f.held, f.kat)
			if n > b.strafeT then b.strafe = -b.strafe; b.strafeT = n + 0.6 + math.random() * 1.2 end
			wish = BotBrain.wish(to, dist, vis, lo, hi, b.strafe, W[f.held].kind == "melee")
			face(f, tr.Position)
			local look = root.CFrame.LookVector
			local aimOff = math.acos(math.clamp(look:Dot(Vector3.new(to.X, 0, to.Z).Unit), -1, 1))
			if BotBrain.canFire(vis, if b.seenAt > 0 then n - b.seenAt else 0, aimOff, dist, f.held, f.kat) then
				if W[f.held].kind == "melee" then swing(f, t)
				else for _ = 1, 3 do if not shoot(f, t, f.held) then break end end end
			end
			-- a parry, now and then: a gun on it from in front, or a blade about to land
			if f.held == "katana" then
				local tl = tr.CFrame.LookVector
				local toMe = (root.Position - tr.Position)
				local aimedAt = toMe.Magnitude > 0.1 and tl:Dot(toMe.Unit) > 0.97
				local threat = if aimedAt and t.held ~= "katana" and vis then "gun" elseif aimedAt and t.held == "katana" and dist < Weapons.reach(W.katana, t.kat) + 6 then "blade" else nil
				local ready = n - f.parryT >= (Weapons.PARRY.win + Weapons.PARRY.cd)
				if math.random() < BotBrain.parryChance(true, ready, threat) * 0.1 then
					local lk = (tr.Position - root.Position)
					if Rules.parryStart(f, n, math.atan2(-lk.X, -lk.Z)) == nil then api.fx({ k = "guard", model = Fight.model(f) }) end
				end
			end
			-- gaps and the grapple: never walk off a roof; hook across to them instead
			if wish.Magnitude > 0 and not b.hook then
				local ahead = root.Position + wish * 6 + Vector3.new(0, 1, 0)
				local floor = Fight.castMap(ahead, Vector3.new(0, -1, 0), 30)
				local need = BotBrain.wantHook(floor ~= nil, dist, false, 0)
				if need == "cross" and grounded then
					local p = hookPoint(eye, (tr.Position + Vector3.new(0, 6, 0)) - eye)
					if p then hookTo(f, b, p) else wish = Vector3.zero end
				elseif floor == nil then wish = Vector3.zero end
			end
		else
			-- nobody to fight: wander to a spawn
			local sp = Fight.spawnPoints(f)
			local goal = sp[(f.id % #sp) + 1]
			local to = goal - root.Position
			if Vector3.new(to.X, 0, to.Z).Magnitude > 8 then wish = Vector3.new(to.X, 0, to.Z).Unit end
		end
		-- falling into the smog: grapple back up toward the nearest spawn
		local below = b.floorY - root.Position.Y
		if not b.hook and BotBrain.wantHook(true, 0, root.AssemblyLinearVelocity.Y < -6, below) == "save" then
			local best, bd = nil, math.huge
			for _, sp in Fight.spawnPoints(f) do local d = (sp - root.Position).Magnitude; if d < bd then best, bd = sp, d end end
			if best then
				local p = hookPoint(eye, (best + Vector3.new(0, 10, 0)) - eye)
				if p then hookTo(f, b, p) end
			end
		end
		-- hops (more up close), and a jump when it's stuck on something
		if grounded and math.random() < 0.1 * (if t and tr and (tr.Position - root.Position).Magnitude < 45 then 1.2 else 0.4) then hum.Jump = true end
		if b.lastPos and wish.Magnitude > 0 and (root.Position - b.lastPos).Magnitude < 0.3 then
			b.stuckT += 0.1
			if b.stuckT > 0.5 then hum.Jump = true; b.stuckT = 0 end
		else b.stuckT = 0 end
		b.lastPos = root.Position
		hum:Move(wish)
	end
end

function Bots.init(fight: any, a: any)
	Fight, api = fight, a
	Fight.makeBot = make
	Fight.onSeats = Bots.seats
end

return Bots
