--!strict
-- JANKFIRE anti-cheat, the server's side (17 Nov 2026; docs/ANTI-CHEAT.md has the why of every check). movement is
-- the client's, like the web game, so this watches what every body really does, ten times a second, against what the
-- game itself can do to a body:
--   * teleport: a step longer than any move in the game (Main's old check, with every push's room on top)
--   * noclip: a straight step that goes in one face of something solid and out the opposite face, at two heights of
--     the body out of three; and a body whose middle stays inside something solid
--   * fly: free flight that doesn't fall with gravity (a parabola fitted through a window of looks), or a body hanging
--     still in the air
--   * speed: going faster than a sprint for a long time on the ground (a slide or a bhop landing carries speed for
--     well under a second; ground friction eats the rest)
-- what the game itself does to bodies counts as a "push" and is never flagged: the server's knockback (Fight.knock:
-- guns, the katana, frags, the duck's black hole, parry shoves), a shot's recoil, an item, a rope (the server's own
-- Rope_<id>), a ledge launch or a BONK (ImpactRemote), a marble slip, the Shredder (its JFShredded group), a soap bubble,
-- the speed-trap cage or a pop quiz (attributes Trap / Jail / Quiz), water, a seat, a spawn, any server teleport
-- (TeleportT, or a server write to the root's CFrame). jump pads and grapple jumps need nothing: their arcs are free
-- flight. a future streak that bends the rules (Moon Boots) sets ACGravity (x gravity) or calls the ACGrace
-- attribute (os.clock() until): AntiCheat stays out of its way. a mode that runs everyone faster sets ACSpeed (x the
-- ground limit and a rope's throw; classic modes' Spoons & Grapples: 1.6).
-- a catch is put back where it was last fine, and scores points (AntiCheatRules.C.weights); enough points inside the
-- window is a kick. bans are the owner's switch (C.BANS, off). aim signals (headshot share, snaps before hits, hits
-- through smoke) are only written to the review log: the server never acts on them. a Studio Play test never kicks (it
-- writes "would kick"): ServerStorage.JankAC (Studio only) reads and resets the state for tests.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")
local CollectionService = game:GetService("CollectionService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local Hitbox = require(Shared:WaitForChild("Hitbox"))
local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local ACR = require(script.Parent:WaitForChild("AntiCheatRules"))
local Log = require(script.Parent:WaitForChild("AntiCheatLog"))
local Reports = require(script.Parent:WaitForChild("Reports")) -- (players' reports, confirm cheater, erasure)
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local C = ACR.C
local W = Weapons.list
local STUDIO = RunService:IsStudio()
local now = os.clock
local Terrain = workspace.Terrain

-- ------------------------------------------------------------------ who's the owner (the panel, kicks, bans)
local OWNER_IDS = { [2833796200] = true } -- the game's owner (ShopKeeper.OWNER)
local function isAdmin(p: Player): boolean
	if OWNER_IDS[p.UserId] then return true end
	if game.CreatorType == Enum.CreatorType.User then return p.UserId == game.CreatorId end
	local ok, rank = pcall(function() return p:GetRankInGroup(game.CreatorId) end)
	return ok and rank == 255
end

-- ------------------------------------------------------------------ the world's solid geometry
-- what's moved on clients only (the server's copy stands still or shut), so the server can't judge a body against it:
-- the hub's spinning bits, the training area's roll-up doors and shutters, laser gates, the VIP doors (their own
-- collision groups do the job), anything marked ACPass
local SKIP_TAGS = { "HubSpin", "HubHolo", "LaserGate", "VipDoor" }
local skipCache: { [Instance]: boolean } = {}
local function skip(part: Instance): boolean
	local c = skipCache[part]
	if c ~= nil then return c end
	local out = false
	if not (part :: BasePart).Anchored then out = true end
	local a: Instance? = part
	while a and a ~= workspace and not out do
		if a:GetAttribute("ACPass") or a:GetAttribute("Shutter") ~= nil or a:GetAttribute("Laser") ~= nil then out = true; break end
		if a.Name == "LaserBar" or a.Name == "LaserField" or a.Name == "DoorBlock" then out = true; break end
		if a.Name == "Door" and a.Parent and a.Parent.Name == "Lot" then out = true; break end -- (the back lot's garage door)
		for _, tag in SKIP_TAGS do if CollectionService:HasTag(a, tag) then out = true; break end end
		a = a.Parent
	end
	skipCache[part] = out
	return out
end
task.spawn(function() while true do task.wait(30); table.clear(skipCache) end end)

-- solid but invisible to rays (CanCollide, not CanQuery: the hub's barrier box, a few roofs): rays and overlap queries
-- skip them, so the server keeps its own list and tests their boxes itself
local hidden: { BasePart } = {}
local pads: { BasePart } = {} -- (and every jump pad: the Pad attribute is its throw)
local function scanHidden()
	local list, padList = {}, {}
	local map = workspace:FindFirstChild("Map")
	if map then
		for _, d in map:GetDescendants() do
			if d:IsA("BasePart") then
				if d.CanCollide and not d.CanQuery and d.Anchored then table.insert(list, d) end
				if typeof(d:GetAttribute("Pad")) == "Vector3" then table.insert(padList, d) end
			end
		end
	end
	hidden, pads = list, padList
end
task.spawn(function() while true do scanHidden(); task.wait(20) end end)
local function inBox(part: BasePart, p: Vector3, pad: number): boolean
	local l = part.CFrame:PointToObjectSpace(p)
	local h = part.Size / 2
	return math.abs(l.X) <= h.X + pad and math.abs(l.Y) <= h.Y + pad and math.abs(l.Z) <= h.Z + pad
end
-- a segment against a box: (enter fraction, exit fraction, enter axis, exit axis) or nil. an axis is 1..3 (x y z),
-- negative for the box's minus face
local function segBox(part: BasePart, a: Vector3, b: Vector3): (number?, number?, number?, number?)
	local la, lb = part.CFrame:PointToObjectSpace(a), part.CFrame:PointToObjectSpace(b)
	local h = part.Size / 2
	local t0, t1 = 0, 1
	local ax0, ax1 = 0, 0
	local A, B, H = { la.X, la.Y, la.Z }, { lb.X, lb.Y, lb.Z }, { h.X, h.Y, h.Z }
	for i = 1, 3 do
		local d = B[i] - A[i]
		if math.abs(d) < 1e-9 then
			if math.abs(A[i]) > H[i] then return nil end
		else
			local e0, e1 = (-H[i] - A[i]) / d, (H[i] - A[i]) / d
			local s0, s1 = if d > 0 then -i else i, if d > 0 then i else -i
			if e0 > e1 then e0, e1 = e1, e0 end
			if e0 > t0 then t0, ax0 = e0, s0 end
			if e1 < t1 then t1, ax1 = e1, s1 end
			if t0 > t1 then return nil end
		end
	end
	return t0, t1, ax0, ax1
end

local water: { BasePart } = {}
local function scanWater()
	water = {}
	for _, w in CollectionService:GetTagged("JankWater") do
		if w:IsA("BasePart") and w:IsDescendantOf(workspace) then table.insert(water, w) end
	end
end
scanWater()
CollectionService:GetInstanceAddedSignal("JankWater"):Connect(scanWater)
CollectionService:GetInstanceRemovedSignal("JankWater"):Connect(scanWater)

local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
mapParams.RespectCanCollide = true
mapParams.IgnoreWater = true
local function mapList(): { Instance }
	local map = workspace:FindFirstChild("Map")
	return if map then { map, Terrain } else { Terrain }
end
-- the first solid map hit along a ray, past anything skipped
local function castSolid(o: Vector3, d: Vector3, len: number, group: string): RaycastResult?
	mapParams.FilterDescendantsInstances = mapList()
	mapParams.CollisionGroup = group
	local from, left = o, len
	for _ = 1, 6 do
		local r = workspace:Raycast(from, d * left, mapParams)
		if not r then return nil end
		if r.Instance == Terrain or not skip(r.Instance) then
			if from ~= o then
				-- (re-cast from past a skipped part: report the distance from the real start)
				return { Instance = r.Instance, Position = r.Position, Normal = r.Normal, Distance = (r.Position - o).Magnitude, Material = r.Material } :: any
			end
			return r
		end
		local moved = (r.Position - from).Magnitude + 0.05
		left -= moved
		if left <= 0 then return nil end
		from = r.Position + d * 0.05
	end
	return nil
end

-- a straight step a -> b through solid: (studs of solid crossed, what) or nil. in by one face, out by the opposite one
local function throughSolid(a: Vector3, b: Vector3, group: string): (number?, Instance?)
	local v = b - a
	local len = v.Magnitude
	if len < 0.3 then return nil, nil end
	local u = v / len
	local fwd = castSolid(a, u, len, group)
	local back = fwd and castSolid(b, -u, len, group)
	if fwd and back then
		local thick = len - fwd.Distance - back.Distance
		if thick >= C.noclipMin and ACR.throughSlab(fwd.Normal, back.Normal) then return thick, fwd.Instance end
	end
	-- the ray-blind solids (the hub's barrier box): their own boxes
	for _, part in hidden do
		if not part.Parent or skip(part) then continue end
		local t0, t1, ax0, ax1 = segBox(part, a, b)
		if t0 and t1 and ax0 and ax1 and t0 > 0 and t1 < 1 and ax0 == -ax1 and (t1 - t0) * len >= C.noclipMin then
			return (t1 - t0) * len, part
		end
	end
	return nil, nil
end

-- the body's middle inside something solid (a small box round the root, the real shapes of what it touches)
local probe = Instance.new("Part")
probe.Name = "ACProbe"
probe.Anchored = true; probe.CanCollide = false; probe.CanQuery = false; probe.CanTouch = false
probe.Transparency = 1
probe.Size = Vector3.new(0.6, 1.4, 0.6)
probe.Parent = workspace.CurrentCamera or workspace -- (the server's camera isn't replicated: nobody sees this)
local overlap = OverlapParams.new()
overlap.FilterType = Enum.RaycastFilterType.Include
overlap.RespectCanCollide = true
local function insideSolid(at: Vector3, group: string): Instance?
	probe.CFrame = CFrame.new(at)
	local map = workspace:FindFirstChild("Map")
	if not map then return nil end
	overlap.FilterDescendantsInstances = { map } -- (not the Terrain: its water would count as inside)
	overlap.CollisionGroup = group
	for _, part in workspace:GetPartsInPart(probe, overlap) do
		if not skip(part) then return part end
	end
	for _, part in hidden do
		if part.Parent and not skip(part) and inBox(part, at, -0.3) then return part end
	end
	return nil
end

-- standing on something (a floor, a ledge's edge, a body, a dummy), in water, or seated
local downParams = RaycastParams.new()
downParams.FilterType = Enum.RaycastFilterType.Exclude
downParams.RespectCanCollide = true
local function support(ch: Model, root: BasePart, hum: Humanoid): string?
	if hum.SeatPart then return "seat" end
	local feetY = root.Position.Y - root.Size.Y / 2 - hum.HipHeight
	downParams.FilterDescendantsInstances = { ch }
	downParams.CollisionGroup = root.CollisionGroup
	downParams.IgnoreWater = false
	local reach = (root.Position.Y - feetY) + 2.5
	local hit = workspace:Blockcast(CFrame.new(root.Position), Vector3.new(1.8, 0.4, 1.8), Vector3.new(0, -reach, 0), downParams)
	if hit then return if hit.Material == Enum.Material.Water then "water" else "ground" end
	local under = Vector3.new(root.Position.X, feetY - 0.6, root.Position.Z)
	for _, part in hidden do
		if part.Parent and inBox(part, under, 1.0) then return "ground" end
	end
	-- (6 studs round the water: its Terrain fill reaches whole 4-stud cells past the part, and swimming out pops you up
	-- the pool's wall, which looks like hovering)
	for _, w in water do
		if w.Parent and inBox(w, root.Position, 6) then return "water" end
	end
	return nil
end

-- anything to bounce off under where the body was (a mid-air kick with nothing within kickClear studs under the feet
-- is a jump in mid-air)
local function groundNear(ch: Model, hum: Humanoid, root: BasePart, at: Vector3): boolean
	downParams.FilterDescendantsInstances = { ch }
	downParams.CollisionGroup = root.CollisionGroup
	downParams.IgnoreWater = false
	local reach = root.Size.Y / 2 + hum.HipHeight + C.kickClear
	if workspace:Blockcast(CFrame.new(at), Vector3.new(2.4, 0.4, 2.4), Vector3.new(0, -reach, 0), downParams) then return true end
	local under = at - Vector3.new(0, root.Size.Y / 2 + hum.HipHeight + 0.6, 0)
	for _, part in hidden do
		if part.Parent and inBox(part, under, C.kickClear) then return true end
	end
	return false
end

-- something solid right beside the body (wedged on an edge, a wall it's sliding down): a fly verdict there is only
-- written down
local nearParams = OverlapParams.new()
nearParams.FilterType = Enum.RaycastFilterType.Exclude
nearParams.RespectCanCollide = true
local function nearSolid(ch: Model, root: BasePart): boolean
	nearParams.FilterDescendantsInstances = { ch }
	nearParams.CollisionGroup = root.CollisionGroup
	for _, part in workspace:GetPartBoundsInBox(root.CFrame * CFrame.new(0, -0.8, 0), Vector3.new(4.5, 7.5, 4.5), nearParams) do
		if part.Anchored and not skip(part) then return true end
	end
	return false
end

-- ------------------------------------------------------------------ each player's watch
type Sample = { t: number, p: Vector3, air: boolean }
type Aim = { t: number, yaw: number, pitch: number? }
type St = {
	samples: { Sample },
	trusted: Vector3?, trustedT: number, -- the last look that was fine (where a catch is put back to)
	ground: Vector3?, -- the last look on the ground (where a flyer is put back to)
	groundSince: number?,
	airSince: number?,
	stillSince: number?,
	moving: boolean, -- on the move before it last stopped (a body that freezes mid-run is lag, not a cheat)
	frozeT: number?,
	grace: number, -- no checks until then (a spawn, a teleport, a put back)
	push: number, pushMag: number, -- the last push, and how big (studs/s)
	pushAway: number, -- the last push that came from the server (it lands a round trip later)
	rope: number,
	insideN: number,
	tp: any,
	points: { { t: number, w: number } },
	kicked: boolean,
	acc: number,
	worst: { [string]: number }, -- the closest each check came on this player (tests read it)
	verdicts: { { t: number, kind: string, info: string, act: string } },
	-- aim
	aims: { Aim },
	aimT: number,
	shot: { t: number, yaw: number, pitch: number, eye: Vector3, wid: string }?,
	hits: number, heads: number, snaps: number, smoke: number, gunHits: number,
	flagT: { [string]: number },
	probes: number, probeT: number,
	selfT: number, -- when this script last put the body back (its own CFrame write)
	cfWrites: number, -- server writes to the root's CFrame seen (tests: physics must never count here)
	slipSeen: number?, -- the fighter's last marble slip already counted as a push
	kickSeen: number, -- the last upward kick already judged
	hookAsks: { number }, -- hook requests in the last 10 s
	noCharge: { number }, -- hook requests with no charge left (ranked), last 60 s
	-- the climb: from the last take-off (the ground, a missed landing, a push), how high, and how fast it could go up
	baseY: number, baseT: number, maxY: number, v0: number,
	speedNow: number,
	knownGround: boolean, -- seen standing since the last teleport, spawn or put back
}
local st: { [Player]: St } = {}

local function fresh(): St
	return {
		samples = {}, trusted = nil, trustedT = 0, ground = nil, groundSince = nil, airSince = nil, stillSince = nil,
		moving = false, grace = now() + 1, push = -math.huge, pushMag = 0, pushAway = -math.huge, rope = -math.huge,
		insideN = 0, tp = nil, points = {}, kicked = false, acc = 0, worst = {}, verdicts = {},
		aims = {}, aimT = 0, shot = nil, hits = 0, heads = 0, snaps = 0, smoke = 0, gunHits = 0, flagT = {},
		probes = 0, probeT = 0, selfT = -math.huge, cfWrites = 0, kickSeen = -math.huge,
		baseY = 0, baseT = -math.huge, maxY = 0, v0 = 0, speedNow = 0, knownGround = false, hookAsks = {}, noCharge = {},
	}
end

-- a take-off: the climb is measured from here, at most as high as v0 (studs/s up) throws a body
local function rebase(s: St, at: Vector3, t: number, v0: number)
	s.baseY, s.baseT, s.maxY, s.v0 = at.Y, t, at.Y, v0
end
-- how fast a body leaving the ground here could be going up: a jump (a slide jump is the biggest) on top of its speed
-- (a ramp can turn speed into height), or a jump pad's throw if one is near
local function takeoffV0(s: St, at: Vector3): number
	local v = C.jumpV0 + C.speedV0 * s.speedNow
	for _, pad in pads do
		local pv = pad:GetAttribute("Pad")
		if typeof(pv) == "Vector3" and pad.Parent and (pad.Position - at).Magnitude < C.padNear + pad.Size.Magnitude / 2 then
			v = math.max(v, pv.Magnitude + v)
		end
	end
	return v
end

local function restart(s: St, at: Vector3?, grace: number)
	table.clear(s.samples)
	s.trusted, s.trustedT = at, now()
	s.groundSince, s.airSince, s.stillSince = nil, nil, nil
	s.insideN = 0
	s.grace = math.max(s.grace, now() + grace)
	s.knownGround, s.speedNow = false, 0 -- (until it's seen standing again, its next take-off is unknown)
end

local function worst(s: St, k: string, v: number)
	if v > (s.worst[k] or -math.huge) then s.worst[k] = v end
end

-- a push the game gave this body. away = the server sent it (it lands on the client a round trip from now)
local function pushed(p: Player?, mag: number, away: boolean?)
	local s = p and st[p]
	if not s then return end
	local t = now()
	s.pushMag = if t - s.push < 1.5 then math.max(s.pushMag, mag) else mag
	s.push = t
	if away then s.pushAway = t end
end

-- ------------------------------------------------------------------ the ladder: put back, points, kick, ban
local function verdict(s: St, kind: string, info: string, act: string)
	table.insert(s.verdicts, { t = now(), kind = kind, info = info, act = act })
	while #s.verdicts > 40 do table.remove(s.verdicts, 1) end
end

local function banFor(uid: number, secs: number, reason: string, by: string): (boolean, string?)
	if not C.BANS then return false, "bans are switched off (AntiCheatRules.C.BANS)" end
	if STUDIO then
		Log.add(uid, "ban", "would ban", ("%s: %s, %s (Studio: no ban)"):format(by, reason, if secs < 0 then "for good" else ("%d days"):format(secs // 86400)))
		return true, nil
	end
	local ok, err = pcall(function()
		Players:BanAsync({
			UserIds = { uid }, ApplyToUniverse = true, Duration = secs,
			DisplayReason = "Banned for cheating.", PrivateReason = string.sub(by .. ": " .. reason, 1, 900),
			ExcludeAltAccounts = false,
		})
	end)
	Log.add(uid, "ban", if ok then "ban" else "ban failed", ("%s: %s, %s%s"):format(by, reason, if secs < 0 then "for good" else ("%d days"):format(secs // 86400), if ok then "" else (" (" .. tostring(err) .. ")")))
	return ok, if ok then nil else tostring(err)
end

local function kick(p: Player, s: St, why: string)
	if s.kicked then return end
	if STUDIO or not C.KICK or not C.KICK_MOVE then -- (KICK_MOVE off: movement kicks only written down)
		Log.add(p, "kick", "would kick", why)
		verdict(s, "kick", why, "would kick")
		table.clear(s.points) -- (a Studio test goes on: start counting again)
		return
	end
	s.kicked = true
	Log.add(p, "kick", "kick", why)
	if C.AUTO_BAN and C.BANS then
		task.spawn(function()
			if Log.kicksWithin(p.UserId, C.AUTO_BAN_DAYS) >= C.AUTO_BAN_KICKS then
				banFor(p.UserId, if C.BAN_DAYS > 0 then C.BAN_DAYS * 86400 else -1, ("%d kicks in %d days, the last: %s"):format(C.AUTO_BAN_KICKS, C.AUTO_BAN_DAYS, why), "auto")
			end
		end)
	end
	Log.flush()
	p:Kick("Disconnected by the server's movement check. If this was a mistake, rejoin.")
end

-- a catch: put back (to `to`), points, maybe a kick. soft = only written down (the server isn't sure)
local function caught(p: Player, s: St, kind: string, info: string, to: Vector3?, soft: boolean?)
	if soft then
		verdict(s, kind, info, "flag")
		if now() - (s.flagT[kind] or -math.huge) > 20 then
			s.flagT[kind] = now()
			Log.add(p, kind, "flag", info)
		end
		return
	end
	local ch = p.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if root and to then
		s.selfT = now()
		root.AssemblyLinearVelocity = Vector3.zero
		root.CFrame = CFrame.new(to) * root.CFrame.Rotation
		-- (the client's updates already on their way still show it where it was: wait them out, a round trip)
		restart(s, to, 0.15 + 2 * math.clamp(p:GetNetworkPing(), 0, 1))
	end
	local pts = ACR.strike(s.points, now(), C.weights[kind] or 1)
	verdict(s, kind, info, "put back")
	Log.add(p, kind, "put back", ("%s; %d/%d points"):format(info, pts, C.kickAt), C.weights[kind] or 1)
	if pts >= C.kickAt then kick(p, s, ("%d points in %d s, the last: %s (%s)"):format(pts, C.window, kind, info)) end
end

-- ------------------------------------------------------------------ the pushes the server knows about
-- the server's knockback (guns, the katana, frags, the black hole's pull, parry shoves): every Fight.hurt goes through it
do
	local knock = Fight.knock
	Fight.knock = function(t: any, v: Vector3, wid: string)
		if t and t.kind == "player" then pushed(t.ref, v.Magnitude, true) end
		return knock(t, v, wid)
	end
end
-- your own shot's recoil, a swing, an item, a rope, a ledge launch or a BONK: the client pushes itself as it sends these
local function listen(name: string, parent: Instance, fn: (Player, ...any) -> ())
	task.spawn(function()
		local r = parent:WaitForChild(name, 60)
		if r and r:IsA("RemoteEvent") then (r :: RemoteEvent).OnServerEvent:Connect(fn) end
	end)
end
listen("Swing", Remotes, function(p) pushed(p, 30) end)
listen("Item", Remotes, function(p) pushed(p, 80) end)
-- a hook request: whether it swings anyone is decided in look() (the server's own Rope_<id>, or a refused hook's
-- round trip, a few at most). in a ranked match with no charge left (HookChargeServer: HookLimit, HookN) the client
-- should never have asked: its own gate was skipped. written down, never acted on
listen("Grapple", Remotes, function(p, what)
	if what ~= "hook" then return end
	local s = st[p]
	if not s then return end
	local t = now()
	table.insert(s.hookAsks, t)
	while #s.hookAsks > 0 and t - s.hookAsks[1] > 10 do table.remove(s.hookAsks, 1) end
	if p:GetAttribute("HookLimit") == true and p:GetAttribute("HookN") == 0 then
		table.insert(s.noCharge, t)
		while #s.noCharge > 0 and t - s.noCharge[1] > 60 do table.remove(s.noCharge, 1) end
		if #s.noCharge >= 3 then
			caught(p, s, "hook", ("%d hooks asked for with no charge left in 60 s (the client's own gate skipped)"):format(#s.noCharge), nil, true)
		end
	end
end)
listen("ImpactRemote", ReplicatedStorage, function(p, kind) if kind == "launch" or kind == "ragdoll" then pushed(p, 300) end end)

-- ------------------------------------------------------------------ one look at one body
local function flatSpeed(samples: { Sample }, since: number): number?
	local d, t0, t1 = 0, nil, nil
	for i = 2, #samples do
		local a, b = samples[i - 1], samples[i]
		if a.t < since then continue end
		t0 = t0 or a.t
		t1 = b.t
		d += Vector3.new(b.p.X - a.p.X, 0, b.p.Z - a.p.Z).Magnitude
	end
	if not t0 or not t1 or t1 - t0 < 0.3 then return nil end
	return d / (t1 - t0)
end

local function look(p: Player, s: St)
	local ch = p.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not ch or not hum or not root or hum.Health <= 0 then s.trusted = nil; return end
	-- (Studio: the movement checks are off unless a test turns them on, script attribute StudioOn: other sessions'
	-- Play tests move their test player in ways no client could)
	if STUDIO and not script:GetAttribute("StudioOn") then s.trusted = nil; return end
	local t = now()
	local pos = root.Position
	-- a server teleport (laser doors, matches, lobbies, items: the TeleportT stamp) starts afresh from the new spot
	local tp = p:GetAttribute("TeleportT")
	if tp ~= s.tp then s.tp = tp; restart(s, nil, 0.5); return end
	local grace = p:GetAttribute("ACGrace")
	if type(grace) == "number" and grace > t then restart(s, nil, 0); return end
	if t < s.grace then return end
	-- (after a spawn or a teleport: wherever the body is now is fine. after a put back the trusted spot stays where it
	-- was put: a client that ignores the put back is caught again from there)
	if not s.trusted then s.trusted, s.trustedT = pos, t; s.ground = pos; return end
	local f = Fight.byPlayer[p]
	if f then
		-- a marble slip or a parry stagger lands a round trip after the server says so
		if f.slipT and f.slipT ~= s.slipSeen then s.slipSeen = f.slipT; pushed(p, 40, true) end
		if f.staggerUntil and f.staggerUntil > t then pushed(p, 40, true) end
	end
	if root.CollisionGroup == "JFShredded" then pushed(p, 90, true) end -- (in a Shredder's stream: Shredder pulls you)
	local bound = p:GetAttribute("Trap") or p:GetAttribute("Jail") or p:GetAttribute("Quiz")
	if bound then s.rope = t end -- (a soap bubble floats you, a cage hangs you, a quiz holds you: no fly or speed checks)
	-- a mode that runs everyone faster (classic modes: Spoons & Grapples x1.6) sets ACSpeed for the match: the ground
	-- limit and a rope's throw grow with it
	local am = p:GetAttribute("ACSpeed")
	local sm = if type(am) == "number" and am > 1 then math.min(am, 3) else 1
	local group = root.CollisionGroup
	local ping = math.clamp(p:GetNetworkPing(), 0, 1)
	-- on a rope: the server's own (Main draws Rope_<id> for a hook it accepted). a hook it refused still swings the
	-- client until the "cut" gets there, a round trip: that counts too, but only while the client isn't asking more
	-- than 4 times in 10 s (asking over and over to keep the fly check away is no rope)
	if Terrain:FindFirstChild("Rope_" .. p.UserId) then
		s.rope = t
	else
		local ask = s.hookAsks[#s.hookAsks]
		if ask and t - ask < 0.3 + 2 * ping and #s.hookAsks <= 4 then s.rope = math.max(s.rope, ask) end
	end
	local from = s.trusted :: Vector3
	local step = pos - from
	local dist = step.Magnitude
	local lastPush = math.max(s.push, s.rope)
	-- 1) teleport. a body that stopped dead mid-run and then jumps ahead is lag catching up: it gets its time back
	local dt = t - s.trustedT
	if not s.moving then dt = math.min(dt, C.SAMPLE * 2 + ping) end
	dt = math.min(dt, C.stallCredit + ping)
	local room = ACR.moveRoom(dt, if t - lastPush < 1.5 then s.pushMag else 0, ping)
	worst(s, "teleport", dist / room)
	if dist > room then
		caught(p, s, "teleport", ("%.0f studs in %.2f s (room %.0f)"):format(dist, dt, room), from)
		return
	end
	-- 2) through a wall (a step that ends inside something waits: the inside check below takes it, and the step out
	-- is measured from the last clear look, across the whole wall)
	local inside = insideSolid(pos, group)
	-- (not while on a rope: a tight swing round a post is the one way a body's path bends hard enough between two looks
	-- for the straight line to cut through something. on foot or in the air the turns are far too wide)
	if not inside and dist <= C.noclipLen and dist >= 0.3 and t - s.rope > 0.3 then
		local n, thick, what = 0, 0, nil
		for _, up in { 0, 1.2, -1.2 } do
			local o = Vector3.new(0, up, 0)
			local th, w = throughSolid(from + o, pos + o, group)
			if th then n += 1; thick = math.max(thick, th); what = what or w end
		end
		worst(s, "noclip", n / 2)
		if n >= 2 then
			caught(p, s, "noclip", ("through %.1f studs of %s"):format(thick, if what then what.Name else "?"), from)
			return
		end
	end
	if inside then
		s.insideN += 1
		worst(s, "inside", s.insideN / C.insideFor)
		if s.insideN >= C.insideFor then
			caught(p, s, "inside", ("middle inside %s for %.1f s"):format(inside.Name, s.insideN * C.SAMPLE), from)
		end
		return -- (the trusted look stays the last clear one)
	end
	s.insideN = 0
	-- the look is fine: it's the new trusted spot
	local on = support(ch, root, hum)
	local moved = dist > 0.02
	-- (moving = it was on the move when it last stopped, and hasn't stood still for long: lag, if it jumps ahead next)
	if moved then
		s.moving, s.frozeT = true, nil
		s.trusted, s.trustedT = pos, t
	else
		s.frozeT = s.frozeT or t
		if t - (s.frozeT :: number) > 1.5 then s.moving = false end
		s.trusted = pos
	end
	-- how fast it's going (over the last quarter second or so: a take-off's speed sets how high it can climb)
	for i = #s.samples, 1, -1 do
		local smp = s.samples[i]
		if t - smp.t >= 0.25 then s.speedNow = (pos - smp.p).Magnitude / (t - smp.t); break end
	end
	-- (a body that hasn't moved at all since the last look isn't in free flight: that's lag, or an anchored body, which
	-- the still-in-the-air check takes. a falling body always moves, even at the top of its arc)
	table.insert(s.samples, { t = t, p = pos, air = on == nil and moved })
	while #s.samples > 0 and t - s.samples[1].t > 3 do table.remove(s.samples, 1) end
	if on then
		s.ground = pos
		s.knownGround = true
		s.airSince, s.stillSince = nil, nil
		s.groundSince = if on == "ground" then (s.groundSince or t) else nil
	else
		s.groundSince = nil
		if not s.airSince then
			s.airSince = t
			-- (the take-off: from the last look on the ground. a take-off the server never saw, the body already in the
			-- air when the watch started again after a teleport or a spawn, gets the most any take-off can give)
			local from0 = s.ground or pos
			rebase(s, from0, t, if s.knownGround then takeoffV0(s, from0) else C.ropeV0 * sm)
		end
		if moved then s.stillSince = nil else s.stillSince = s.stillSince or t end
	end
	-- 3) speed on the ground
	if s.groundSince and t - s.groundSince >= C.groundFor and t - lastPush > 1.2 and not bound then
		local v = flatSpeed(s.samples, math.max(s.groundSince, t - C.groundWin))
		local fast = p:GetAttribute("FastUntil")
		local star = type(fast) == "number" and fast > workspace:GetServerTimeNow()
		local lim = ACR.groundLimit(star) * sm
		if v then
			worst(s, "speed", v / lim)
			if v > lim then
				local back = s.samples[1].p
				for _, smp in s.samples do if smp.t >= t - C.groundWin then back = smp.p; break end end
				caught(p, s, "speed", ("%.0f studs/s on the ground for %.1f s (limit %.0f)"):format(v, t - s.groundSince, lim), back)
				return
			end
		end
	end
	-- 4) flying: free flight since the last push (a server push gets its round trip), fitted against gravity
	if s.airSince and not bound then
		local quietFrom = math.max(s.airSince, lastPush + C.quiet, s.pushAway + C.quiet + C.quietPing * ping)
		local gs = p:GetAttribute("ACGravity")
		local g = C.GRAV * (if type(gs) == "number" then math.clamp(gs, 0, 2) else 1)
		-- hanging still in the air
		if s.stillSince and t - math.max(s.stillSince, quietFrom) >= C.stallFor then
			local soft = nearSolid(ch, root)
			caught(p, s, "stall", ("still in the air for %.1f s%s"):format(t - s.stillSince, if soft then ", beside a wall" else ""), if soft then nil else s.ground, soft)
			if not soft then return end
			s.stillSince = t
		end
		-- a push (a knock, a rope, an item...) is a new take-off from where the body is now, as fast as the push
		if lastPush > s.baseT then
			rebase(s, pos, t, math.max(takeoffV0(s, pos), if s.rope >= s.push then C.ropeV0 * sm else s.pushMag + C.jumpV0))
		end
		-- the window, cut at the last upward kick between two looks: a landing the looks missed (a bhop's ground
		-- contact is a few ticks) starts a new arc; with ground under it, it's a new take-off too
		local ts, ys = {}, {}
		local lastT, lastY, lastV, kickAt = nil, nil, nil, nil
		for _, smp in s.samples do
			if smp.air and smp.t >= quietFrom and smp.t >= t - C.flyWin - 0.5 then
				if lastT and lastY then
					local v = (smp.p.Y - lastY) / math.max(smp.t - lastT, 1e-3)
					if lastV and v - lastV > C.kickUp then
						table.clear(ts); table.clear(ys)
						kickAt = smp
					end
					lastV = v
				end
				if smp.t >= t - C.flyWin then table.insert(ts, smp.t); table.insert(ys, smp.p.Y) end
				lastT, lastY = smp.t, smp.p.Y
			end
		end
		if kickAt and kickAt.t > s.kickSeen then
			s.kickSeen = kickAt.t
			if kickAt.t > s.baseT and groundNear(ch, hum, root, kickAt.p) then rebase(s, kickAt.p, kickAt.t, takeoffV0(s, kickAt.p)) end
		end
		-- how high it's gone since its take-off, against how high that take-off could throw it (a jump on top of its
		-- speed then, a pad's throw, a push): rising past that with nothing under it is flying (or jumping in mid-air)
		s.maxY = math.max(s.maxY, pos.Y)
		local climb = s.maxY - s.baseY
		local allow = s.v0 * s.v0 / (2 * g) * C.climbTol + C.climbAdd
		worst(s, "climb", climb / allow)
		if climb > allow then
			local soft = nearSolid(ch, root)
			caught(p, s, "fly", ("climbed %.0f studs with nothing under it (its take-off allows %.0f)%s"):format(climb, allow, if soft then ", beside a wall" else ""), if soft then nil else s.ground, soft)
			if not soft then return end
			rebase(s, pos, t, s.v0)
		end
		local kind, accel, rms = ACR.flyVerdict(ts, ys, g)
		if accel then worst(s, "fly", (accel + g) / (g * (1 - C.flyAccel))) end -- (1 = right at the line)
		if kind and accel and rms then
			-- (beside a wall it may be wedged on an edge, or climbing: only written down)
			local soft = nearSolid(ch, root)
			caught(p, s, "fly", ("%s: fell at %.0f studs/s^2 over %.1f s (gravity %.0f; fit %.2f)%s"):format(if kind == "rise" then "rising" else "hovering", -accel, ts[#ts] - ts[1], g, rms, if soft then ", beside a wall" else ""), if soft then nil else s.ground, soft)
			if soft then
				-- (written down once a window: start the next one fresh)
				s.airSince = t
			end
		end
	end
end

-- ------------------------------------------------------------------ aim: written down, never acted on
local function yawOf(v: Vector3): number return math.atan2(-v.X, -v.Z) end
local function aimAt(s: St, at: number): Aim?
	local best, bd = nil, math.huge
	for _, a in s.aims do
		local d = math.abs(a.t - at)
		if d < bd then best, bd = a, d end
	end
	return if bd < 0.08 then best else nil
end
local function finiteV(v: any): boolean
	return typeof(v) == "Vector3" and v.X == v.X and v.Y == v.Y and v.Z == v.Z and v.Magnitude < 1e6
end
listen("Fire", Remotes, function(p, wid, eye, ends)
	local s = st[p]
	if not s or type(wid) ~= "string" or not W[wid] then return end
	-- the shot's recoil shoves the shooter (Arsenal: along -look). only the big ones count as a push: the small ones,
	-- even sprayed straight down at full rate, leave well over half of gravity (the Redline: 0.9 x 22/s = 20 of 78)
	local rc = W[wid].recoil or 0
	if rc >= 8 then pushed(p, rc + 10) end
	if not finiteV(eye) or type(ends) ~= "table" or not finiteV(ends[1]) then return end
	local d = (ends[1] :: Vector3) - (eye :: Vector3)
	if d.Magnitude < 1e-3 then return end
	d = d.Unit
	s.shot = { t = now(), yaw = yawOf(d), pitch = math.deg(math.asin(math.clamp(d.Y, -1, 1))), eye = eye :: Vector3, wid = wid }
end)

local function flag(p: Player, s: St, kind: string, info: string)
	if now() - (s.flagT[kind] or -math.huge) < C.flagEvery then return end
	s.flagT[kind] = now()
	verdict(s, kind, info, "flag")
	Log.add(p, kind, "flag", info)
end

local function aimHit(t: any, by: any, wid: string, hs: boolean?)
	if not by or by.kind ~= "player" or by == t then return end
	local w = W[wid]
	if not w or w.kind == "melee" then return end
	local p = by.ref :: Player
	local s = st[p]
	if not s then return end
	local shot = s.shot
	if not shot or now() - shot.t > 0.25 or shot.wid ~= wid then return end
	local vr = Fight.root(t)
	s.gunHits += 1
	if vr and Fight.smokeBlocks(shot.eye, vr.Position) then s.smoke += 1 end
	if (w.pellets or 1) <= 1 then
		s.hits += 1
		if hs then s.heads += 1 end
		local before = aimAt(s, shot.t - C.snapBefore)
		if before then
			local dy = ACR.yawDiff(shot.yaw, before.yaw)
			local dp = if before.pitch then math.abs(shot.pitch - before.pitch) else 0
			local snap = math.sqrt(dy * dy + dp * dp)
			worst(s, "snapDeg", snap)
			if snap >= C.snapDeg then s.snaps += 1 end
		end
	end
	if s.hits >= C.aimMinHits then
		local hr, sr = s.heads / s.hits, s.snaps / s.hits
		if hr > C.headRatio then flag(p, s, "head", ("%d headshots in %d hits (%.0f%%)"):format(s.heads, s.hits, hr * 100)) end
		if sr > C.snapRatio then flag(p, s, "snap", ("%d of %d hits came right after the aim jumped %d+ degrees"):format(s.snaps, s.hits, C.snapDeg)) end
	end
	if s.smoke >= C.smokeMin and s.smoke / s.gunHits > C.smokeRatio then
		flag(p, s, "smoke", ("%d of %d hits went through a smoke cloud"):format(s.smoke, s.gunHits))
	end
end
-- (in a pcall: this runs inside Fight.hurt, and nothing here may ever stop a hit from landing)
Fight.onHurt(function(t: any, _done: number, by: any, wid: string, hs: boolean?)
	local ok, err = pcall(aimHit, t, by, wid, hs)
	if not ok then warn("[anticheat] aim: " .. tostring(err)) end
end)

-- the remotes only the server fires: a client firing one is poking at the game (written down, and dropped)
for _, name in { "Ammo", "Callout", "Dmg", "Fx", "Kill", "Knock", "Patch", "Round", "Shot", "Slip", "Spawn", "ItemFx", "LootShow", "PlayPush" } do
	listen(name, Remotes, function(p)
		local s = st[p]
		if not s then return end
		s.probes += 1
		if now() - s.probeT > 60 then
			s.probeT = now()
			verdict(s, "remote", name, "flag")
			Log.add(p, "remote", "flag", ("fired %s, a server-only remote (%d so far)"):format(name, s.probes))
		end
	end)
end

-- ------------------------------------------------------------------ players
local function watchChar(p: Player, ch: Model)
	local s = st[p]
	if not s then return end
	restart(s, nil, 1.0)
	s.ground = nil
	-- a write to the root's CFrame from a server script is a server teleport (physics never fires this)
	local root = ch:WaitForChild("HumanoidRootPart", 10) :: BasePart?
	if root then
		root:GetPropertyChangedSignal("CFrame"):Connect(function()
			local s2 = st[p]
			if not s2 or p.Character ~= ch then return end
			s2.cfWrites += 1
			if now() - s2.selfT > 0.1 then restart(s2, nil, 0.3) end
		end)
	end
end
local function added(p: Player)
	st[p] = fresh()
	-- "/ac" in the legacy chat opens the owner's panel (client/AntiCheatPanel.client.luau watches ACPanel)
	p.Chatted:Connect(function(msg: string)
		if string.lower(string.sub(msg, 1, 3)) == "/ac" and isAdmin(p) then p:SetAttribute("ACPanel", os.clock()) end
	end)
	p.CharacterAdded:Connect(function(ch) watchChar(p, ch) end)
	if p.Character then task.spawn(watchChar, p, p.Character) end
end
Players.PlayerAdded:Connect(added)
for _, p in Players:GetPlayers() do added(p) end
Players.PlayerRemoving:Connect(function(p) st[p] = nil end)

local errors = 0 -- (a broken look is warned about five times, not ten times a second)
RunService.Heartbeat:Connect(function(dt: number)
	local t = now()
	for p, s in st do
		-- the aim, up to 30 times a second (yaw from the body: first person and the shoulder camera both turn it with
		-- the view; pitch from the third-person pose's TP attribute)
		if t - s.aimT >= 1 / 30 then
			s.aimT = t
			local ch = p.Character
			local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
			if root then
				local tpv = (ch :: Model):GetAttribute("TP")
				table.insert(s.aims, { t = t, yaw = yawOf(root.CFrame.LookVector), pitch = if typeof(tpv) == "Vector3" then tpv.X else nil })
				while #s.aims > 0 and t - s.aims[1].t > 0.6 do table.remove(s.aims, 1) end
			end
		end
		s.acc += dt
		if s.acc >= C.SAMPLE then
			s.acc = 0
			local ok, err = pcall(look, p, s)
			if not ok then
				errors += 1
				if errors <= 5 then warn("[anticheat] " .. tostring(err)) end
			end
		end
	end
end)

-- ------------------------------------------------------------------ reports (server/Reports.luau)
-- what a report keeps about the reported player: this server's points, recent catches and aim counts, and their
-- totals across servers (the stored log)
local function flagsOf(uid: number): any
	local p = Players:GetPlayerByUserId(uid)
	local s = p and st[p]
	local out: any = { points = if s then ACR.points(s.points, now()) else 0, recent = {} }
	if s then
		for i = math.max(1, #s.verdicts - 11), #s.verdicts do
			local v = s.verdicts[i]
			table.insert(out.recent, { kind = v.kind, act = v.act, info = v.info, ago = math.floor(now() - v.t) })
		end
		out.aim = { hits = s.hits, heads = s.heads, snaps = s.snaps, smoke = s.smoke }
	end
	local r = Log.user(uid)
	if type(r) == "table" then out.totals = r.flags; out.kicks = r.kicks end
	return out
end
Reports.init({ Log = Log, flagsOf = flagsOf })

-- ------------------------------------------------------------------ the owner's panel (client/AntiCheatPanel.client)
local Admin = Remotes:FindFirstChild("AntiCheat") :: RemoteFunction?
if not Admin then
	local r = Instance.new("RemoteFunction")
	r.Name = "AntiCheat"
	r.Parent = Remotes
	Admin = r
end
local adminBudget: { [Player]: { n: number, t: number } } = {}
local function spend(p: Player): boolean
	local b, t = adminBudget[p], now()
	if not b then b = { n = 10, t = t }; adminBudget[p] = b end
	b.n = math.min(10, b.n + (t - b.t) * 4); b.t = t
	if b.n < 1 then return false end
	b.n -= 1
	return true
end
Players.PlayerRemoving:Connect(function(p) adminBudget[p] = nil end)
local uidArg = Reports.validUid
local function reportId(v: unknown): string?
	return if type(v) == "string" and #v <= 40 and string.match(v, "^%w+$") then v else nil
end
local function textArg(v: unknown, max: number): string
	if type(v) ~= "string" then return "" end
	return string.sub(string.gsub(v, "[%c]", " "), 1, max)
end
local function playerRow(p: Player): { [string]: any }
	local s = st[p]
	local last = s and s.verdicts[#s.verdicts]
	return {
		uid = p.UserId, name = p.Name, display = p.DisplayName,
		points = if s then ACR.points(s.points, now()) else 0,
		last = if last then ("%s %s: %s"):format(last.kind, last.act, last.info) else nil,
		hits = if s then s.hits else 0, heads = if s then s.heads else 0, snaps = if s then s.snaps else 0, smoke = if s then s.smoke else 0,
	}
end
local probed: { [Player]: boolean } = {}
;(Admin :: RemoteFunction).OnServerInvoke = function(p: Player, op: unknown, a: unknown, b: unknown, c: unknown): any
	if not spend(p) then return { ok = false, why = "slow down" } end
	if not isAdmin(p) then
		if op ~= "hello" and not probed[p] then probed[p] = true; Log.add(p, "admin", "flag", "called the owner's anti-cheat panel: " .. textArg(op, 20)) end
		return if op == "hello" then { admin = false } else nil
	end
	if op == "hello" then
		return { admin = true, bans = C.BANS, kicks = C.KICK and C.KICK_MOVE and not STUDIO, studio = STUDIO, kickAt = C.kickAt, window = C.window, reports = true }
	elseif op == "players" then
		local out = {}
		for _, q in Players:GetPlayers() do table.insert(out, playerRow(q)) end
		return out
	elseif op == "log" then
		local ok, list = pcall(Log.read, 150)
		if not ok then return {} end
		local out = {}
		for _, e in list do
			local row = table.clone(e)
			row.name = row.name or Reports.nameOf(row.uid) -- (stored lines have no names: looked up to show)
			table.insert(out, row)
		end
		return out
	elseif op == "reports" then
		local ok, list = pcall(Reports.list)
		return if ok then list else {}
	elseif op == "report" then
		local id = reportId(a)
		if not id then return nil end
		local ok, r = pcall(Reports.get, id)
		return if ok then r else nil
	elseif op == "dismiss" then
		local id = reportId(a)
		if not id then return { ok = false, why = "no such report" } end
		return { ok = Reports.setState(id, "dismissed", p.UserId) }
	elseif op == "confirm" then
		-- CONFIRM CHEATER: the restores (Stats, RankedData, Quests). b = "all": everything, else since the earliest
		-- evidence; c = the report it came from
		local uid = uidArg(a)
		if not uid then return { ok = false, why = "no such user id" } end
		if uid == p.UserId then return { ok = false, why = "that's you" } end
		local from = Reports.confirm(uid, if b == "all" then 0 else nil, p.UserId)
		local id = reportId(c)
		if id then Reports.setState(id, "confirmed", p.UserId) end
		return { ok = true, since = from }
	elseif op == "unconfirm" then
		local uid = uidArg(a)
		if not uid then return { ok = false, why = "no such user id" } end
		Reports.unconfirm(uid, p.UserId)
		return { ok = true }
	elseif op == "erase" then
		-- Roblox's right-to-erasure: every report by or about them, their chat lines, their anti-cheat records
		local uid = uidArg(a)
		if not uid then return { ok = false, why = "no such user id" } end
		local ok, res = pcall(Reports.erase, uid)
		if not ok then return { ok = false, why = tostring(res) } end
		Log.add(0, "erase", "erase", ("a user's data erased on request: %d reports, %d scrubbed, %d log lines"):format(res.reports, res.scrubbed, res.logLines))
		return { ok = true, res = res }
	elseif op == "kick" then
		local uid = uidArg(a)
		local q = uid and Players:GetPlayerByUserId(uid)
		if not q then return { ok = false, why = "not in this server" } end
		if q == p then return { ok = false, why = "that's you" } end
		local why = textArg(b, 120)
		Log.add(q, "kick", "kick", "by the owner" .. (if why ~= "" then ": " .. why else ""))
		local id = reportId(c)
		if id then Reports.setState(id, "kicked", p.UserId) end
		if STUDIO then return { ok = true, why = "Studio: written down, not kicked" } end
		q:Kick(if why ~= "" then "Kicked by the game's owner: " .. why else "Kicked by the game's owner.")
		return { ok = true }
	elseif op == "clear" then
		local uid = uidArg(a)
		local q = uid and Players:GetPlayerByUserId(uid)
		local s = q and st[q]
		if not q or not s then return { ok = false, why = "not in this server" } end
		table.clear(s.points)
		s.hits, s.heads, s.snaps, s.smoke, s.gunHits = 0, 0, 0, 0, 0
		table.clear(s.flagT)
		Log.add(q, "clear", "clear", "points and aim counts cleared by the owner")
		return { ok = true }
	elseif op == "ban" then
		local uid = uidArg(a)
		if not uid then return { ok = false, why = "no such user id" } end
		if uid == p.UserId then return { ok = false, why = "that's you" } end
		local days = if type(b) == "number" and b == b then math.clamp(math.floor(b), 0, 3650) else C.BAN_DAYS
		local why = textArg(c, 200)
		local ok, err = banFor(uid, if days > 0 then days * 86400 else -1, if why ~= "" then why else "cheating", "owner " .. p.Name)
		-- (an owner's ban is a confirmed cheater: the restores run too)
		if ok then Reports.confirm(uid, nil, p.UserId) end
		return { ok = ok, why = err }
	elseif op == "unban" then
		local uid = uidArg(a)
		if not uid then return { ok = false, why = "no such user id" } end
		if not C.BANS then return { ok = false, why = "bans are switched off (AntiCheatRules.C.BANS)" } end
		if STUDIO then Log.add(uid, "unban", "would unban", "by " .. p.Name); return { ok = true, why = "Studio: written down" } end
		local ok, err = pcall(function() Players:UnbanAsync({ UserIds = { uid }, ApplyToUniverse = true }) end)
		Log.add(uid, "unban", if ok then "unban" else "unban failed", "by " .. p.Name .. (if ok then "" else " (" .. tostring(err) .. ")"))
		-- (an unban is NOT an unconfirm: a served or forgiven ban leaves the restores as they are. a wrong catch is
		-- the owner's UNCONFIRM, which gives the player's own numbers back)
		return { ok = ok, why = if ok then nil else tostring(err) }
	end
	return nil
end

-- ------------------------------------------------------------------ Studio play tests: ServerStorage.JankAC
--   local AC = game.ServerStorage.JankAC
--   AC:Invoke("state", player)  -> { points, verdicts = { {t, kind, info, act} }, worst = { teleport =, noclip =, ... },
--                                  aim = { hits, heads, snaps, smoke } }   (worst: 1 = right at a check's line)
--   AC:Invoke("reset", player)  -> clears the points, verdicts and worst
--   AC:Invoke("knock", player, Vector3)  -> a real Fight.knock on them (the server's own knockback path)
--   AC:Invoke("shred", player, secs)  -> what a Shredder does to its victim: JFShredded + "pull"s toward the sky
if STUDIO then
	local old = ServerStorage:FindFirstChild("JankAC")
	if old then old:Destroy() end
	local fn = Instance.new("BindableFunction")
	fn.Name = "JankAC"
	fn.OnInvoke = function(op: any, a: any, b: any): any
		local s = typeof(a) == "Instance" and st[a :: Player] or nil
		if op == "state" and s then
			local v = {}
			for _, x in s.verdicts do table.insert(v, { t = math.floor((x.t - now()) * 10) / 10, kind = x.kind, info = x.info, act = x.act }) end
			return { points = ACR.points(s.points, now()), verdicts = v, worst = table.clone(s.worst), cfWrites = s.cfWrites, errors = errors,
				trusted = s.trusted, air = s.airSince ~= nil, ground = s.groundSince ~= nil,
				aim = { hits = s.hits, heads = s.heads, snaps = s.snaps, smoke = s.smoke, gunHits = s.gunHits } }
		elseif op == "reset" and s then
			table.clear(s.points); table.clear(s.verdicts); table.clear(s.worst); s.cfWrites = 0
			s.hits, s.heads, s.snaps, s.smoke, s.gunHits = 0, 0, 0, 0, 0
			table.clear(s.flagT)
			return true
		elseif op == "knock" and s and typeof(b) == "Vector3" then
			local f = Fight.byPlayer[a]
			if f then Fight.knock(f, b, "test") end
			return f ~= nil
		elseif op == "shred" and s then
			local p = a :: Player
			local ch = p.Character
			local rem = ReplicatedStorage:FindFirstChild("ShredderRemote") :: RemoteEvent?
			if not ch or not rem then return false end
			task.spawn(function()
				local t0 = now()
				while now() - t0 < (tonumber(b) or 1.5) and p.Character == ch do
					for _, d in ch:GetDescendants() do if d:IsA("BasePart") and not d:FindFirstAncestorOfClass("Tool") then d.CollisionGroup = "JFShredded" end end
					rem:FireClient(p, "pull", Vector3.new(0, 30, 0))
					task.wait(0.09)
				end
				task.wait(0.8)
				for _, d in ch:GetDescendants() do if d:IsA("BasePart") and not d:FindFirstAncestorOfClass("Tool") then d.CollisionGroup = "JFPlayers" end end
			end)
			return true
		elseif op == "config" then
			return table.clone(C)
		elseif op == "left" and type(a) == "number" then -- (a user id that "just left": somebody to report in a solo test)
			Reports.testLeft(a)
			return true
		elseif op == "chat" then -- (the public chat a report would keep right now)
			return Reports.chatNow()
		elseif op == "rec" and s then -- (what Recorder.forReport hands a report for this player now: its size)
			local m = script.Parent:FindFirstChild("Recorder")
			local okR, R = pcall(require, m :: ModuleScript)
			if not okR or type(R) ~= "table" or type(R.forReport) ~= "function" then return "no recorder" end
			local rec = R.forReport(a)
			if type(rec) ~= "table" then return "no match" end
			return { id = rec.id, mode = rec.mode, secs = rec.secs, bytes = #game:GetService("HttpService"):JSONEncode(rec) }
		end
		return nil
	end
	fn.Parent = ServerStorage
end
