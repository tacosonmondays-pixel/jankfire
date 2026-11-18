--!strict
-- THE TALL GUY FROM HR, in the hub (18 Nov 2026; the web's: server/hrguy.js + shared/hr.js, the Scary Forest's).
-- 3.5 m of grey suit and no face (Shared.LoreRigs.hr, the web's own buildHR; the template ServerStorage.LoreHR, made by
-- PolishBackup.LoreSpots.hr()). Rules kept from the web: he turns up out of sight, never moves while anyone has him in
-- view, and every time nobody is looking he blinks a few metres closer in a new, slightly worse pose. Staring right at
-- him fills your meter (faster up close); full, or he reaches you unseen, and he has you.
-- What the hub changes (owner's ask relayed by main: rare, harmless, only in a quiet part):
--   * only on the back lot (TheLot's OnLot attribute: only players who found the garage's gold Carls get there), only
--     for someone with nobody else within ALONE studs, at most once in COOLDOWN s each, a ROLL chance every EVERY s
--     once they've been there FIRST s. (with these numbers a lone player meets him about once in 10 minutes on the lot)
--   * never hurts anyone. "having you" = a short scare (full static, a deep boom: LoreLife/HrGuy.client), then you're
--     back in the spawn lounge (a TeleportT stamp first: the anti-cheat starts afresh), and it counts as finding him
--     (the lore count, LoreNPCs' find "hr", once per player)
-- Looking: each client on the lot tells the server where its camera is and where it looks (remote HrLook, a few times
-- a second); the server tests the web's hrSight and a clear line, the same for everyone. (a client that lies only
-- changes how fast he gets ITSELF: nothing here can touch anyone else)
-- He is a Model "HrGuy" in workspace.Map.Lore while he visits (attributes Hr = true, Pose = the pose's seed, Target =
-- the user id he's after); each client poses him from Pose (HrGuy.client). Your meter: your attribute HrStare (0..1).
-- Studio play tests: ServerStorage.HrTest (BindableFunction, Studio only): "state", "come" (he visits the first player
-- now, wherever they are), "leave", "take" (he has the first player now).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local LoreR = Remotes:WaitForChild("Lore") :: RemoteEvent
local LookR = Remotes:WaitForChild("HrLook") :: RemoteEvent
local STUDIO = RunService:IsStudio()

local M = 3 -- studs per web metre
local HR = {
	height = 3.55 * M,
	life = 60, -- s he hangs about unseen before he gives up
	far = { 34 * M, 48 * M }, -- how far from his target he turns up (a little closer than the forest's: the lot is smaller)
	see = 66 * M, -- how far you can make him out
	watchAng = 0.85, stareAng = 0.2,
	rate = { 0.13, 0.95 }, decay = 0.32,
	step = { 3.5 * M, 6.5 * M }, stepEvery = { 0.8, 1.6 },
	reach = 2.4 * M,
	-- the hub's rarity
	EVERY = 90, ROLL = 0.15, FIRST = 60, COOLDOWN = 1200, ALONE = 90,
}
local function rr(a: { number }): number return a[1] + math.random() * (a[2] - a[1]) end
local function clamp(v: number, a: number, b: number): number return math.max(a, math.min(b, v)) end

-- the lot's ground (TrainingLot's barrier box, a few studs in) and its floor height band
local LOT_LO, LOT_HI = Vector3.new(-180, 236, -8728), Vector3.new(180, 246, -8308)

type Look = { eye: Vector3, dir: Vector3, t: number }
local looks: { [Player]: Look } = {}
local lotSince: { [Player]: number } = {}
local lastVisit: { [Player]: number } = {}
local stare: { [Player]: number } = {}

local S = { on = false, model = nil :: Model?, p = Vector3.zero, yaw = 0, target = nil :: Player?, born = 0, stepT = 0, pose = 0, nextRoll = 0 }

local function lore(): Instance?
	local map = workspace:FindFirstChild("Map")
	return map and map:FindFirstChild("Lore")
end
local function rootOf(p: Player): BasePart?
	local ch = p.Character
	local r = ch and ch:FindFirstChild("HumanoidRootPart")
	return if r and r:IsA("BasePart") then r else nil
end
local function alive(p: Player): boolean
	local ch = p.Character
	local h = ch and ch:FindFirstChildOfClass("Humanoid")
	return h ~= nil and h.Health > 0
end

local rayParams = RaycastParams.new()
rayParams.FilterType = Enum.RaycastFilterType.Exclude
local function refreshFilter()
	local ex: { Instance } = {}
	for _, p in Players:GetPlayers() do if p.Character then table.insert(ex, p.Character) end end
	local l = lore(); if l then table.insert(ex, l) end
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	local bar = hub and hub:FindFirstChild("Barrier"); if bar then table.insert(ex, bar) end
	rayParams.FilterDescendantsInstances = ex
end

-- the web's hrSight, in studs: how an eye looking along dir relates to him standing at feet
local function sight(eye: Vector3, dir: Vector3, feet: Vector3)
	local c = feet + Vector3.new(0, HR.height * 0.62, 0)
	local d = c - eye
	local dist = math.max(d.Magnitude, 1e-3)
	local ang = math.acos(clamp(dir.Unit:Dot(d / dist), -1, 1))
	local inRange = dist < HR.see
	return { d = dist, ang = ang, c = c, view = inRange and ang < HR.watchAng, stare = inRange and ang < HR.stareAng + math.atan(HR.height * 0.4 / dist) }
end
local function clear(eye: Vector3, to: Vector3): boolean
	local r = workspace:Raycast(eye, to - eye, rayParams)
	return r == nil or (r.Position - to).Magnitude < 2
end
-- who is looking his way (fresh reports only), with their sight
local function sights(at: Vector3): { { any } }
	local out = {}
	local now = os.clock()
	for p, l in looks do
		if now - l.t > 1.0 or not alive(p) then continue end
		local h = sight(l.eye, l.dir, at)
		if (h.view or h.stare) and clear(l.eye, h.c) then table.insert(out, { p, h }) end
	end
	return out
end
local function stareRate(d: number): number
	local k = 1 - clamp(d / HR.see, 0, 1)
	return HR.rate[1] + (HR.rate[2] - HR.rate[1]) * k * k
end

-- can he stand here? on the lot's ground (not a container top, a roof or a bank), clear of everything solid
local function standOk(x: number, z: number): Vector3?
	if x < LOT_LO.X or x > LOT_HI.X or z < LOT_LO.Z or z > LOT_HI.Z then return nil end
	local r = workspace:Raycast(Vector3.new(x, 270, z), Vector3.new(0, -50, 0), rayParams)
	if not r or r.Position.Y < LOT_LO.Y or r.Position.Y > LOT_HI.Y then return nil end
	local op = OverlapParams.new()
	op.FilterType = Enum.RaycastFilterType.Exclude
	op.FilterDescendantsInstances = rayParams.FilterDescendantsInstances
	for _, q in workspace:GetPartBoundsInBox(CFrame.new(r.Position + Vector3.new(0, HR.height / 2 + 0.4, 0)), Vector3.new(2.4, HR.height, 2.4), op) do
		if q:IsA("BasePart") and q.CanCollide then return nil end
	end
	return r.Position
end
local function eyeOf(p: Player): Vector3?
	local r = rootOf(p)
	return r and r.Position + Vector3.new(0, 1.6, 0)
end
-- would the target see him at s if they turned round? (he wants to be found)
local function openTo(t: Player, s: Vector3): boolean
	local e = eyeOf(t)
	return e ~= nil and clear(e, s + Vector3.new(0, HR.height * 0.62, 0))
end

-- ------------------------------------------------------------------ his body
local function setPose(seed: number)
	S.pose = seed
	if S.model then S.model:SetAttribute("Pose", seed) end
end
local function place()
	local m = S.model
	if not m then return end
	local t = S.target
	local face = Vector3.new(0, 0, -1)
	local tr = t and rootOf(t)
	if tr then
		local d = Vector3.new(tr.Position.X - S.p.X, 0, tr.Position.Z - S.p.Z)
		if d.Magnitude > 0.1 then face = d.Unit end
	end
	m:PivotTo(CFrame.lookAt(S.p, S.p + face))
end
local function spawnModel(): Model?
	local tpl = ServerStorage:FindFirstChild("LoreHR")
	local l = lore()
	if not tpl or not l then return nil end
	local m = tpl:Clone() :: Model
	m.Name = "HrGuy"
	m:SetAttribute("Hr", true)
	m.Parent = l
	return m
end

local function leave(why: string)
	if S.model then S.model:Destroy() end
	S.model = nil
	S.on = false
	if S.target then lastVisit[S.target] = os.clock() end
	S.target = nil
	for p in stare do p:SetAttribute("HrStare", nil) end
	table.clear(stare)
end

-- he has them: the scare, then back to the spawn lounge, and it counts as a find
local function take(p: Player)
	local at = S.p
	LoreR:FireClient(p, "hrtake", at)
	local who = p
	leave("took")
	lastVisit[who] = os.clock()
	local ev = ServerStorage:FindFirstChild("LoreFindEvent")
	if ev and ev:IsA("BindableEvent") then ev:Fire(who, "hr") end
	task.delay(0.9, function()
		local r = rootOf(who)
		local map = workspace:FindFirstChild("Map")
		local hub = map and map:FindFirstChild("Hub")
		local spawns = hub and hub:FindFirstChild("HubSpawns")
		local list = if spawns then spawns:GetChildren() else {}
		local s = list[math.random(1, math.max(1, #list))]
		if r and s and s:IsA("BasePart") then
			who:SetAttribute("TeleportT", os.clock()) -- (the anti-cheat starts afresh from the new spot)
			local ch = who.Character :: Model
			ch:PivotTo(s.CFrame * CFrame.new(0, 3.5, 0))
		end
	end)
end

-- somewhere out of everyone's sight, far from the target, ideally where they'd see him if they turned round
local function arrivalSpot(t: Player): Vector3?
	local r = rootOf(t)
	if not r then return nil end
	local best, bs = nil, -1
	for _ = 1, 60 do
		local a = math.random() * math.pi * 2
		local d = rr(HR.far)
		local s = standOk(r.Position.X + math.cos(a) * d, r.Position.Z + math.sin(a) * d)
		if not s or #sights(s) > 0 then continue end
		local score = math.random() + (if openTo(t, s) then 5 else 0)
		if score > bs then bs = score; best = s end
	end
	return best
end

local function visit(t: Player): boolean
	refreshFilter()
	local s = arrivalSpot(t)
	if not s then return false end
	local m = spawnModel()
	if not m then return false end
	S.model = m
	S.on = true
	S.p = s
	S.target = t
	S.born = os.clock()
	S.stepT = rr(HR.stepEvery) + 1.5
	m:SetAttribute("Target", t.UserId)
	setPose(math.random(0, 999))
	place()
	return true
end

-- ------------------------------------------------------------------ who might get a visit
local function lonely(p: Player): boolean
	local r = rootOf(p)
	if not r or p:GetAttribute("OnLot") ~= true or not alive(p) then return false end
	for _, q in Players:GetPlayers() do
		if q ~= p then
			local qr = rootOf(q)
			if qr and (qr.Position - r.Position).Magnitude < HR.ALONE then return false end
		end
	end
	return true
end

LookR.OnServerEvent:Connect(function(p: Player, eye: any, dir: any)
	if typeof(eye) ~= "Vector3" or typeof(dir) ~= "Vector3" or dir.Magnitude < 0.5 then return end
	local r = rootOf(p)
	if not r or (eye - r.Position).Magnitude > 40 then return end -- (a camera further than this from you: not believed)
	looks[p] = { eye = eye, dir = dir.Unit, t = os.clock() }
end)
Players.PlayerRemoving:Connect(function(p)
	looks[p] = nil; lotSince[p] = nil; lastVisit[p] = nil; stare[p] = nil
	if S.target == p then leave("gone") end
end)

local sendT = 0
RunService.Heartbeat:Connect(function(dt)
	local now = os.clock()
	-- who's on the lot and since when
	for _, p in Players:GetPlayers() do
		if p:GetAttribute("OnLot") == true then lotSince[p] = lotSince[p] or now else lotSince[p] = nil end
	end
	if not S.on then
		if now < S.nextRoll then return end
		S.nextRoll = now + HR.EVERY
		for p, since in lotSince do
			if now - since >= HR.FIRST and now - (lastVisit[p] or -1e9) >= HR.COOLDOWN and lonely(p) and math.random() < HR.ROLL then
				if visit(p) then break end
			end
		end
		return
	end
	local t = S.target
	local tr = t and rootOf(t)
	if not t or not tr or not alive(t) or t:GetAttribute("OnLot") ~= true then leave("gone"); return end
	refreshFilter()
	local seen = sights(S.p)
	-- the meters: staring fills yours, looking away drains it
	local staring: { [Player]: boolean } = {}
	for _, x in seen do
		local p, h = x[1], x[2]
		if h.stare then
			staring[p] = true
			stare[p] = math.min(1, (stare[p] or 0) + stareRate(h.d) * dt)
		end
	end
	for p, k in stare do
		if not staring[p] then
			local v = k - HR.decay * dt
			if v <= 0 then stare[p] = nil; p:SetAttribute("HrStare", nil) else stare[p] = v end
		end
	end
	for p, k in stare do if k >= 1 and alive(p) then take(p); return end end
	if now - S.born > HR.life and #seen == 0 then leave("bored"); return end
	-- nobody's looking: blink closer, a new pose each time. close enough and still unseen: he has them
	if #seen == 0 then
		S.stepT -= dt
		local flat = Vector3.new(tr.Position.X - S.p.X, 0, tr.Position.Z - S.p.Z)
		local d = flat.Magnitude
		if d < HR.reach then take(t); return end
		if S.stepT <= 0 then
			S.stepT = rr(HR.stepEvery)
			local st = math.min(d - 3.6, rr(HR.step))
			local pick: Vector3?, pickOpen = nil, false
			for k = 0, 9 do
				if pick and pickOpen then break end
				local side = (math.random() - 0.5) * (k + 1) * 0.5
				local a = math.atan2(flat.Z, flat.X) + side
				local s = standOk(S.p.X + math.cos(a) * st, S.p.Z + math.sin(a) * st)
				if s then
					local open = openTo(t, s)
					if not pick or (open and not pickOpen) then pick = s; pickOpen = open end
				end
			end
			if pick then
				S.p = pick
				setPose(math.random(0, 999))
			end
			place()
			if Vector3.new(tr.Position.X - S.p.X, 0, tr.Position.Z - S.p.Z).Magnitude < HR.reach then take(t); return end
		end
	end
	-- everyone's meter, ten times a second
	if now - sendT >= 0.1 then
		sendT = now
		for p, k in stare do p:SetAttribute("HrStare", math.floor(k * 50 + 0.5) / 50) end
	end
end)

if STUDIO then
	local hook = ServerStorage:FindFirstChild("HrTest") or Instance.new("BindableFunction")
	hook.Name = "HrTest"
	hook.Parent = ServerStorage;
	(hook :: BindableFunction).OnInvoke = function(op: string): any
		local p = Players:GetPlayers()[1]
		if op == "state" then
			return { on = S.on, at = tostring(S.p), target = S.target and S.target.Name, pose = S.pose,
				onLot = p and p:GetAttribute("OnLot"), look = p and looks[p] and tostring(looks[p].dir), stare = p and stare[p] or 0,
				seen = S.on and #sights(S.p) or 0, nextRoll = math.floor(S.nextRoll - os.clock()) }
		elseif op == "come" and p then
			if S.on then leave("test") end
			refreshFilter()
			return visit(p)
		elseif op == "leave" then
			leave("test"); return true
		elseif op == "take" and p then
			if not S.on then return "not here" end
			take(p); return true
		end
		return "ops: state, come, leave, take"
	end
end
