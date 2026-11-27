--!strict
-- THE VICTORY SCENE on screen (27 Nov 2026; shared/VictoryData.luau has the why, client/Victory.client.luau runs it).
-- THE RISER: a set of our own, built on this client far off the map (STAGE_AT): a round stage, a curved riser behind it
-- for teammates, a curved backdrop with a cove and white light panels; one accent, the stage's lip, in the winning
-- team's colour (ReplicatedStorage.JankfireVictory.Stage, from tools/roblox/victory_stage.py). The winning side walks up
-- onto it (or onto a map's own spot) as clean copies of their bodies (Replay.templates: the look each player spawned
-- with), each landing a mocap pose with their weapon (THE WALK-UP, below). The camera is ours:
--   CLOSE  0 - ~3.2 s  a wide lens low in front of the one in front, pushing in as they walk at it and land their pose
--   WIDE   then - LEN  a cut to a wide front shot that pushes in and orbits a little to the held framing
--   HOLD   after       the held framing (the team on the left two-thirds, the card on the right), a slow drift
-- losers see the winners from the floor: one long low lens drifting across them, a colder, greyer grade. (A map's walk
-- spot - the Spooky Forest - is its own scene: THE WALK, below.)
--   Scene.start(msg, opts)   opts.hold = straight to the held shot (a cinematic played, a skip, the card alone)
--   Scene.hold()             jump to the held shot
--   Scene.stop()             everything back as it was
--   Scene.on(), Scene.t()    running?  seconds since it started
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")
local ContentProvider = game:GetService("ContentProvider")
local TweenService = game:GetService("TweenService")

local me = Players.LocalPlayer
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local V = require(Shared:WaitForChild("VictoryData")) :: any
local Flair = require(Shared:WaitForChild("Flair")) :: any
local TeamColors = require(Shared:WaitForChild("TeamColors")) :: any
local Replay = require(script.Parent:WaitForChild("Replay")) :: any
local WeaponModels = require(Shared:WaitForChild("WeaponModels")) :: any
local GunSkins = require(Shared:WaitForChild("GunSkins")) :: any
local GunHats = require(Shared:WaitForChild("GunHats")) :: any

local Scene = {}

local STAGE_AT = Vector3.new(0, 3400, 48000) -- far from every map, map room, copy row and photo stage
local FLOOR_TOP = 0
local STAGE_TOP = 1.2
local RISER_TOP = 2.6
-- where the bodies stand (stage space: +Z toward the camera, +X to the camera's right)
local FRONT = Vector3.new(0, STAGE_TOP, 1.0)
-- (placed by the held lens's angles - 27 Nov, Play: a lone teammate at the left stood exactly behind the one in front.
-- from the held lens the one in front sits ~26% across; teammates at ~52%, ~13% and ~39%, clear of them and of the card)
local MATES = {
	[1] = { Vector3.new(4.6, RISER_TOP, -7.6) },
	[2] = { Vector3.new(4.6, RISER_TOP, -7.6), Vector3.new(-6.4, RISER_TOP, -6.8) },
	[3] = { Vector3.new(4.6, RISER_TOP, -7.6), Vector3.new(-6.4, RISER_TOP, -6.8), Vector3.new(0.6, RISER_TOP, -9.6) },
}

-- the shots, stage space: { t0, t1, from = { at, look, fov }, to = { ... }, ease }
local RISE_T = 2.1
-- (Studio tuning: workspace attribute VictoryShots = JSON { rise = { from, to }, stage = { from, to }, lose = { from, to },
-- hold = k, loseHold = k } with each k = { at = { x, y, z }, look = { x, y, z }, fov }: replaces the numbers below)
local function tuned(): any?
	if not RunService:IsStudio() then return nil end
	local j = workspace:GetAttribute("VictoryShots")
	if type(j) ~= "string" or j == "" then return nil end
	local ok, t = pcall(function() return game:GetService("HttpService"):JSONDecode(j) end)
	if not ok or type(t) ~= "table" then return nil end
	local function k(x: any): any?
		if type(x) ~= "table" or type(x.at) ~= "table" or type(x.look) ~= "table" then return nil end
		return { at = Vector3.new(x.at[1], x.at[2], x.at[3]), look = Vector3.new(x.look[1], x.look[2], x.look[3]), fov = tonumber(x.fov) or 40 }
	end
	local out = {}
	for name, v in t do
		if type(v) == "table" and v.from then out[name] = { from = k(v.from), to = k(v.to) } else out[name] = k(v) end
	end
	return out
end
local function shotsFor(win: boolean, len: number): { any }
	local tu = tuned()
	if tu and win and tu.rise and tu.stage then
		return { { t0 = 0, t1 = RISE_T, ease = "inout", from = tu.rise.from, to = tu.rise.to },
			{ t0 = RISE_T, t1 = len, ease = "out", from = tu.stage.from, to = tu.stage.to } }
	elseif tu and not win and tu.lose then
		return { { t0 = 0, t1 = len, ease = "out", from = tu.lose.from, to = tu.lose.to } }
	end
	if win then
		return {
			{ t0 = 0, t1 = RISE_T, ease = "inout",
				from = { at = Vector3.new(3.4, 1.8, 5.6), look = Vector3.new(0, 2.9, 1.0), fov = 50 },
				to = { at = Vector3.new(3.6, 5.6, 6.6), look = Vector3.new(0, 5.4, 1.0), fov = 44 } },
			{ t0 = RISE_T, t1 = len, ease = "out",
				from = { at = Vector3.new(-7.5, 3.6, 30), look = Vector3.new(1.0, 4.2, -3.0), fov = 40 },
				to = { at = Vector3.new(5.4, 4.6, 17.5), look = Vector3.new(4.2, 4.6, -2.5), fov = 36 } },
		}
	end
	return {
		{ t0 = 0, t1 = len, ease = "out",
			from = { at = Vector3.new(-8, 2.0, 38), look = Vector3.new(-1.5, 4.6, -2.0), fov = 26 },
			to = { at = Vector3.new(-1.5, 2.3, 34), look = Vector3.new(4.4, 4.7, -2.0), fov = 24 } },
	}
end
local function holdOf(win: boolean): any
	local tu = tuned()
	if tu and win and tu.hold then return tu.hold end
	if tu and not win and tu.loseHold then return tu.loseHold end
	return if win then { at = Vector3.new(5.4, 4.6, 17.5), look = Vector3.new(4.2, 4.6, -2.5), fov = 36 }
		else { at = Vector3.new(-1.5, 2.3, 34), look = Vector3.new(4.4, 4.7, -2.0), fov = 24 }
end

-- ------------------------------------------------------------------ the set
local kit: Instance? = nil
local function kitOf(): Instance?
	if kit and kit.Parent then return kit end
	local f = ReplicatedStorage:FindFirstChild("JankfireVictory")
	kit = f
	return f
end
local setModel: Model? = nil
local function buildSet(): Model?
	if setModel and setModel.Parent then return setModel end
	local k = kitOf()
	local src = k and k:FindFirstChild("Stage")
	if not (src and src:IsA("Model")) then return nil end
	local m = src:Clone()
	m.Name = "JankVictoryStage"
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
	end
	setModel = m
	return m
end

-- the poses and stings, loaded early (a clip's first play waits on the asset: memory roblox-flair)
task.spawn(function()
	local list = {}
	local ids = {}
	for _, p in V.POSES do table.insert(ids, p.anim) end
	for _, t in { V.WALK, V.ARRIVE } do
		for _, v in t do if type(v) == "string" and string.sub(v, 1, 13) == "rbxassetid://" then table.insert(ids, v) end end
	end
	for _, id in ids do
		local a = Instance.new("Animation")
		a.AnimationId = id
		table.insert(list, a)
	end
	local k = kitOf()
	if k then for _, s in k:GetChildren() do if s:IsA("Sound") then table.insert(list, s) end end end
	pcall(function() ContentProvider:PreloadAsync(list) end)
end)

-- ------------------------------------------------------------------ the bodies
local function sourceOf(uid: number): Model?
	local t = Replay.templates and Replay.templates[uid]
	if t then return t:Clone() end
	local p = Players:GetPlayerByUserId(uid)
	local ch = p and p.Character
	if ch then
		local was = ch.Archivable
		ch.Archivable = true
		local c = ch:Clone()
		ch.Archivable = was
		return c
	end
	local looks = ReplicatedStorage:FindFirstChild("JankVictoryLooks") -- (Studio tests: VictoryServer builds these)
	local l = looks and looks:FindFirstChild(tostring(uid))
	if l and l:IsA("Model") then return l:Clone() end
	return nil
end

-- EVERY BODY HOLDS ITS OWN WEAPON (main's notes from the reference, 27 Nov: "every player holding their own equipped
-- weapon in the pose, so skins get shown off"): the one in its hand at the end, else its loadout's first; its skin, wrap
-- and hat, built and gripped as Fight.showWeapon grips a held gun ("in the fist, pointing where the forearm points"),
-- so the pose's arm carries it. a test body (no player) holds the local player's
local HAND_K = 3 * 1.5 -- (Fight's own)
local function weaponOf(uid: number): (string?, Player?)
	local p = Players:GetPlayerByUserId(uid) or me -- (a test body: no player of its own)
	if not p then return nil, nil end
	local ch = p.Character
	local hw = ch and ch:FindFirstChild("HeldWeapon")
	local wid = hw and hw:GetAttribute("Weapon")
	if type(wid) ~= "string" then
		local lo = p:GetAttribute("Loadout")
		wid = if type(lo) == "string" then string.split(lo, ",")[1] else nil
	end
	if type(wid) ~= "string" or wid == "" or wid == "shredder" then return nil, p end -- (the Shredder is a Tool: not built here)
	return wid, p
end
local function arm(body: Model, uid: number)
	local wid, p = weaponOf(uid)
	if not wid or not p then return end
	local hand = body:FindFirstChild("RightHand") :: BasePart? or body:FindFirstChild("Right Arm") :: BasePart?
	if not hand then return end
	local ok, w = pcall(WeaponModels.build, wid, HAND_K, GunSkins.skinFor(p, wid))
	if not ok or not w or not w.PrimaryPart then return end
	w.Name = "VictorWeapon"
	pcall(function()
		local wrId, md = WeaponModels.wrapFor(p, wid)
		if wrId then WeaponModels.wrap(w, wrId, md) end
		GunHats.attach(w, wid, GunHats.hatFor(p, wid), HAND_K, nil, GunHats.THIRD)
	end)
	for _, d in w:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = false; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.Massless = true; d.CastShadow = true end
	end
	local grip = w.PrimaryPart:FindFirstChild("Grip") :: Attachment?
	local off = if grip then grip.Position else Vector3.zero
	w:PivotTo(hand.CFrame * CFrame.new(0, -hand.Size.Y * 0.35, 0) * CFrame.Angles(-math.pi / 2, 0, 0) * CFrame.new(-off))
	local weld = Instance.new("WeldConstraint")
	weld.Part0 = hand; weld.Part1 = w.PrimaryPart; weld.Parent = w.PrimaryPart
	w.Parent = body
end

type Body = { model: Model, track: AnimationTrack?, root: BasePart }
local function standAt(m: Model, hum: Humanoid?, root: BasePart, cf: CFrame)
	local up = if hum and hum.RigType == Enum.HumanoidRigType.R6 then 3 else ((hum and hum.HipHeight or 2) + root.Size.Y / 2)
	m:PivotTo(cf * CFrame.new(0, up, 0) * (root.CFrame:ToObjectSpace(m:GetPivot())))
end
local function makeBody(entry: any, cf: CFrame, pose: string, parent: Instance, still: boolean?): Body?
	local src = sourceOf(entry.uid)
	if not src then return nil end
	local m = Replay.clean(src) :: Model
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not root then m:Destroy(); return nil end
	m.Name = "Victor_" .. tostring(entry.uid)
	local hum = m:FindFirstChildOfClass("Humanoid")
	if hum then
		hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
		pcall(function() (hum :: any).EvaluateStateMachine = false end)
		hum.PlatformStand = false
	end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.CastShadow = true; d.LocalTransparencyModifier = 0 end
	end
	m:SetAttribute("TPPlayer", nil)
	m.Parent = parent
	standAt(m, hum, root, cf)
	local b: Body = { model = m, root = root, track = nil }
	-- the action: their emote, else a victory pose (mocap)
	local animator = hum and hum:FindFirstChildOfClass("Animator")
	if hum and not animator then animator = Instance.new("Animator"); animator.Parent = hum end
	local r6 = hum ~= nil and hum.RigType == Enum.HumanoidRigType.R6
	local id = if type(entry.emote) == "string" then Flair.emoteAnim(entry.emote, r6) else nil
	-- (a victory pose holds the weapon up to show it; a dance emote doesn't - a gun along a dancing forearm reads wrong)
	if not id then
		id = (V.POSES[pose] or V.POSES.victory).anim
		pcall(arm, m, entry.uid)
	end
	if animator and not still then
		local a = Instance.new("Animation")
		a.AnimationId = id
		local ok, tr = pcall(function() return (animator :: Animator):LoadAnimation(a) end)
		if ok and tr then
			tr.Looped = true
			tr.Priority = Enum.AnimationPriority.Action
			tr:Play(0.15)
			b.track = tr
		end
	end
	return b
end

-- ------------------------------------------------------------------ THE WALK (a map's walk spot)
-- (27 Nov, the owner, for the Spooky Forest: "make them walk in the forest scared as the screen distorts".) the winners
-- walk the spot's path: the one in front leads with the gun up, teammates huddle behind (V.WALK.mates). the lens:
--   TRACK   0 - 3.0 s        a slow backward track in front of them
--   LOW     3.0 - 4.7 s      low at their side, looking up through the trees
--   BEHIND  4.7 s - stop     behind the last of them, over the shoulder, into the dark ahead
--   STARTLE stop - end       the stinger: everyone flinches, the lens whips in on the one in front; then held for the card
-- the screen builds unease over the walk: colour draining toward a cold green, a breathing FOV, a heartbeat-timed
-- vignette and blur, double-vision flickers, a rising shake; the startle flashes and kicks
local WALK_TRACK, WALK_LOW = 3.0, 4.7
local function pathOf(cfs: { CFrame }): any
	local pts, acc = {}, { 0 }
	for i, c in cfs do pts[i] = c.Position end
	for i = 2, #pts do acc[i] = acc[i - 1] + (pts[i] - pts[i - 1]).Magnitude end
	return { pts = pts, acc = acc, total = acc[#acc] }
end
local function flat(v: Vector3): Vector3
	local f = Vector3.new(v.X, 0, v.Z)
	return if f.Magnitude > 1e-3 then f.Unit else Vector3.new(0, 0, -1)
end
-- where the path is at distance d along it, and which way it runs there (past either end it carries straight on)
local function along(P: any, d: number): (Vector3, Vector3)
	local pts, acc = P.pts, P.acc
	local n = #pts
	if d <= 0 then local f = flat(pts[2] - pts[1]); return pts[1] + f * d, f end
	for i = 2, n do
		if d <= acc[i] then
			local u = (d - acc[i - 1]) / math.max(1e-3, acc[i] - acc[i - 1])
			return pts[i - 1]:Lerp(pts[i], u), flat(pts[i] - pts[i - 1])
		end
	end
	local f = flat(pts[n] - pts[n - 1])
	return pts[n] + f * (d - acc[n]), f
end

-- the screen's unease: a vignette (four edges, dark at the rim) and a flash, under the card (DisplayOrder 46)
local function fearGui(): any
	local g = Instance.new("ScreenGui")
	g.Name = "JankVictoryFear"; g.ResetOnSpawn = false; g.IgnoreGuiInset = true; g.DisplayOrder = 46
	local edges = {}
	for _, e in { { "Top", UDim2.new(1, 0, 0.32, 0), UDim2.fromScale(0, 0), 90 }, { "Bottom", UDim2.new(1, 0, 0.32, 0), UDim2.fromScale(0, 0.68), -90 },
		{ "Left", UDim2.new(0.26, 0, 1, 0), UDim2.fromScale(0, 0), 0 }, { "Right", UDim2.new(0.26, 0, 1, 0), UDim2.fromScale(0.74, 0), 180 } } do
		local f = Instance.new("Frame")
		f.Name = e[1]; f.BackgroundColor3 = Color3.new(0, 0, 0); f.BorderSizePixel = 0; f.Size = e[2]; f.Position = e[3]
		local gr = Instance.new("UIGradient")
		gr.Rotation = e[4]
		gr.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) })
		gr.Parent = f
		f.Parent = g
		table.insert(edges, f)
	end
	local flash = Instance.new("Frame")
	flash.Name = "Flash"; flash.BackgroundColor3 = Color3.fromRGB(235, 242, 238); flash.BorderSizePixel = 0; flash.Size = UDim2.fromScale(1, 1)
	flash.BackgroundTransparency = 1; flash.Parent = g
	g.Parent = me:WaitForChild("PlayerGui")
	return { gui = g, edges = edges, flash = flash }
end

local function walkSound(name: string, looped: boolean, vol: number?): Sound?
	local k = kitOf()
	local src = k and k:FindFirstChild(name)
	if not (src and src:IsA("Sound")) then return nil end
	local s = src:Clone()
	s.Looped = looped
	if vol then s.Volume = vol end
	local master = SoundService:FindFirstChild("JankMaster")
	local g = master and master:FindFirstChild("Music") -- (the bed, the heartbeat and the stinger are APM music: the MUSIC slider)
	if g and g:IsA("SoundGroup") then s.SoundGroup = g end
	s.Parent = SoundService
	s:Play()
	if not looped then s.Ended:Once(function() s:Destroy() end) end
	return s
end

-- the bodies on the path: each with its offset (right, back), its walk and its upper-body layer
local function walkBodies(s: any, stage: { any }, folder: Instance)
	local P = s.walk.P
	for i, e in stage do
		if i > 1 + #V.WALK.mates then break end
		local off = if i == 1 then Vector2.zero else V.WALK.mates[i - 1]
		local pos, f = along(P, -off.Y)
		local right = f:Cross(Vector3.yAxis)
		local at = pos + right * off.X
		local cf = CFrame.lookAt(at, at + f)
		local he = table.clone(e)
		he.emote = nil -- (everyone walks: no dances on the path)
		local b = makeBody(he, cf, "victory", folder, true)
		if not b then continue end
		-- the walk under, the upper body over it
		local hum = b.model:FindFirstChildOfClass("Humanoid")
		local animator = hum and hum:FindFirstChildOfClass("Animator")
		local r6 = hum ~= nil and hum.RigType == Enum.HumanoidRigType.R6
		local function load(id: string, prio: Enum.AnimationPriority, looped: boolean): AnimationTrack?
			if not animator then return nil end
			local a = Instance.new("Animation")
			a.AnimationId = id
			local ok, tr = pcall(function() return (animator :: Animator):LoadAnimation(a) end)
			if not ok or not tr then return nil end
			tr.Priority = prio; tr.Looped = looped
			return tr
		end
		local walk = load(if r6 then V.WALK.walk6 else V.WALK.walk, Enum.AnimationPriority.Movement, true)
		local upper = load(if i == 1 then V.WALK.guard else V.WALK.look, Enum.AnimationPriority.Action, true)
		if walk then walk:Play(0.2); walk:AdjustSpeed(V.WALK.animSpeed) end
		if upper then
			upper:Play(0.2)
			upper.TimePosition = (i - 1) * 2.7 -- (each teammate glances back at its own moment)
		end
		local root = b.root
		local hum2 = hum
		local up = if hum2 and hum2.RigType == Enum.HumanoidRigType.R6 then 3 else ((hum2 and hum2.HipHeight or 2) + root.Size.Y / 2)
		table.insert(s.walk.bodies, { b = b, off = off, walk = walk, upper = upper, up = up, rootToPivot = root.CFrame:ToObjectSpace(b.model:GetPivot()),
			startle = load(V.WALK.startle, Enum.AnimationPriority.Action4, true) })
		table.insert(s.bodies, b)
	end
end

-- the group's lead distance at time t (they stop for the startle)
local function walkDist(s: any, t: number): number
	return math.min(t, s.walk.tStop) * V.WALK.speed
end

local function walkMove(s: any, t: number)
	local d = walkDist(s, t)
	for _, w in s.walk.bodies do
		local pos, f = along(s.walk.P, d - w.off.Y)
		local right = f:Cross(Vector3.yAxis)
		local at = pos + right * w.off.X + Vector3.new(0, w.up, 0)
		local rootCF = CFrame.lookAt(at, at + f)
		w.b.model:PivotTo(rootCF * w.rootToPivot)
	end
	if t >= s.walk.tStop and not s.walk.startled then
		s.walk.startled = true
		for i, w in s.walk.bodies do
			if w.walk then w.walk:Stop(0.12) end
			if w.upper then w.upper:Stop(0.08) end
			if w.startle then
				-- (they snap into a guard, the weapon up by the face, each a beat apart)
				local tr = w.startle :: AnimationTrack
				task.delay(0.04 * (i - 1), function() tr:Play(0.06) end)
			end
		end
		if s.walk.heart then TweenService:Create(s.walk.heart, TweenInfo.new(0.4), { Volume = 0 }):Play() end
		walkSound("Stinger", false)
		s.walk.kickAt = t
	end
end

-- the lens for the walk at time t
local function walkCam(s: any, t: number): (Vector3, Vector3, number)
	local W = s.walk
	local len = s.len
	local tt = if s.hold then math.max(t, len) else t
	local d = walkDist(s, tt)
	local L, f = along(W.P, d)
	local right = f:Cross(Vector3.yAxis)
	local k = if W.bodies[1] then W.bodies[1].up / 3 else 1
	local up = Vector3.yAxis * k
	right *= k
	local fk = f * k
	if tt < WALK_TRACK then
		return L + fk * 9.5 + up * 4.2 + right * 0.9, L + up * 3.3 + fk * 0.6, 46
	elseif tt < WALK_LOW then
		-- (on the one in front's left: teammates huddle on the right, behind)
		local u = (tt - WALK_TRACK) / (WALK_LOW - WALK_TRACK)
		return L - right * (12.5 - u * 1.5) + fk * 1.0 + up * 1.2, L + up * 3.2 - fk * 0.8, 46
	elseif tt < W.tStop then
		-- high behind them all, a wide lens into the dark ahead: they're small in the lower third
		local back = W.bodies[#W.bodies] and W.bodies[#W.bodies].off.Y or 2.5
		local u = (tt - WALK_LOW) / math.max(0.1, W.tStop - WALK_LOW)
		local behind = L - fk * (back + 8.5 - u * 1.2)
		return behind + up * 6.8 + right * 1.0, L + fk * 16 + up * 2.2, 58
	end
	-- the startle: a whip in to a two-shot, the one in front's face and the huddle behind, then held (a slow drift
	-- while the card is up)
	local close = L + fk * 7.0 + up * 4.2 - right * 0.6
	local look = L + up * 3.7 + right * 0.4
	local behind = L - fk * 8.0 + up * 6.8 + right * 1.0
	local w = math.clamp((tt - W.tStop) / 0.16, 0, 1)
	w = 1 - (1 - w) ^ 3
	local at = behind:Lerp(close, w)
	if tt > len then
		local k = (tt - len) * 0.3
		at += right * math.sin(k) * 0.25 + up * math.sin(k * 0.7) * 0.08
	end
	return at, look, 46
end

-- the screen's unease, each frame
local function walkFear(s: any, t: number, cf: CFrame, fov: number): (CFrame, number)
	local W = s.walk
	local len = s.len
	local u = math.clamp(t / W.tStop, 0, 1)
	if s.hold or t > len then u = 1 end
	-- the heartbeat: 70 beats a minute rising to 150 (a sharp pulse on each)
	local bps = (70 + 80 * u) / 60
	W.beat = (W.beat or 0) + bps * (W.dt or 0)
	local ph = W.beat % 1
	local pulse = math.max(0, 1 - ph * 5) ^ 2 + 0.5 * math.max(0, 1 - math.abs(ph - 0.28) * 6) ^ 2
	if W.heart then W.heart.PlaybackSpeed = 0.85 + 0.75 * u end
	-- colour draining toward a cold green
	local cc = s.cc
	cc.Saturation = (if s.win then -0.12 else -0.45) - 0.55 * u
	cc.Contrast = 0.06 + 0.16 * u
	cc.Brightness = -0.02 - 0.05 * u - 0.05 * pulse * u
	cc.TintColor = Color3.fromRGB(238, 244, 240):Lerp(if s.win then Color3.fromRGB(192, 214, 204) else Color3.fromRGB(182, 200, 214), u)
	-- blur on the beats, and double-vision flickers that come more often as it builds
	local flick = 0
	if t < W.tStop and math.random() < (0.25 + 1.8 * u) * (W.dt or 0) then W.flickUntil = t + 0.06 + 0.05 * math.random() end
	if W.flickUntil and t < W.flickUntil then flick = 7 + 5 * u end
	local kick = if W.kickAt then math.max(0, 1 - (t - W.kickAt) / 0.45) else 0
	W.blur.Size = 0.8 * u + 3.2 * pulse * u + flick + 14 * kick ^ 2
	-- the vignette darkens with it, beating
	for _, e in W.fear.edges do e.BackgroundTransparency = math.clamp(0.6 - 0.38 * u - 0.18 * pulse * u, 0, 1) end
	W.fear.flash.BackgroundTransparency = if W.kickAt and t - W.kickAt < 0.07 then 0.15 else 1
	-- the lens breathes and shakes, more and more; the startle kicks it
	local amp = 0.02 + 0.13 * u ^ 1.5 + 0.5 * kick
	local n1, n2, n3 = math.noise(t * 5.3, 1.7), math.noise(t * 4.7, 8.1), math.noise(t * 3.9, 3.3)
	local shaken = cf * CFrame.new(n1 * amp, n2 * amp, 0) * CFrame.Angles(math.rad(n2 * (0.3 + 1.6 * u + 6 * kick)), math.rad(n1 * (0.3 + 1.4 * u)), math.rad(n3 * (0.4 + 1.2 * u + 4 * kick)))
	local breathe = 2.6 * u * math.sin(t * 2.2) - 4 * kick + (if flick > 0 then 1.5 else 0)
	return shaken, fov + breathe
end


-- ------------------------------------------------------------------ THE WALK-UP (every pose spot and THE RISER)
-- (27 Nov, the owner: "Instead of an emote on the example victory you should be can it be a walk up into a dynamic pose
-- with a perspective shot?") each body starts a few studs behind its mark, walks up toward the lens, slows onto the mark
-- and lands a mocap pose (V.POSES; a once pose is held on its last frame). the one in front first and furthest,
-- teammates behind, each landing V.ARRIVE.stagger later. the winners' lens:
--   CLOSE  0 - landed+0.6 s  a wide lens low in front of the one in front, pushing in as they walk at it: they grow huge
--                            and the weapon arm comes at the glass; a kick as the pose lands, then a settle
--   WIDE   then - LEN        a cut to the spot's wide (THE RISER: its stage shot): the whole team in their poses
-- losers keep their long low lens across the winners. every body and every track is set from t each frame (the tracks
-- paused and scrubbed), so a frozen photo (VictoryFreeze) is exactly that moment
local function smooth(u: number): number
	u = math.clamp(u, 0, 1)
	return u * u * (3 - 2 * u)
end

-- a ray that passes what a walk passes: a body, an invisible non-colliding part, a small non-colliding prop (a tuft of
-- grass). anything seen, or anything solid, stops it; a floor ray stops at anything
local function blockHit(rp: RaycastParams, from: Vector3, dir: Vector3, floor: boolean): RaycastResult?
	for _ = 1, 10 do
		local h = workspace:Raycast(from, dir, rp)
		if not h or floor then return h end
		local x = h.Instance
		local m = x:FindFirstAncestorOfClass("Model")
		local small = x.Size.X < 2 and x.Size.Y < 2 and x.Size.Z < 2
		if (m and m:FindFirstChildOfClass("Humanoid")) or (not x.CanCollide and (x.Transparency >= 0.95 or small)) then
			rp:AddToFilter(x)
		else
			return h
		end
	end
	return nil
end
local function rayParams(skip: { Instance }): RaycastParams
	local rp = RaycastParams.new()
	rp.FilterType = Enum.RaycastFilterType.Exclude
	rp.FilterDescendantsInstances = skip
	return rp
end
-- how far back from a floor point a body can start (at most want): a clear walk at knee, chest and head height, and
-- floor at the same height all the way
local function roomBehind(at: Vector3, back: Vector3, want: number, skip: { Instance }): number
	local rp = rayParams(skip)
	local d = want
	for _, hgt in { 1.0, 2.8, 4.6 } do
		local o = at + Vector3.new(0, hgt, 0)
		local h = blockHit(rp, o, back * (want + 1.2), false)
		if h then d = math.min(d, (h.Position - o).Magnitude - 1.2) end
	end
	local k = 1.5
	while k <= d do
		local f = blockHit(rp, at + back * k + Vector3.new(0, 3, 0), Vector3.new(0, -6, 0), true)
		if not f or math.abs(f.Position.Y - at.Y) > 0.8 then d = k - 1.5; break end
		k += 1.5
	end
	return if d < 1.2 then 0 else d
end

-- each body: where it ends (fin), which way it walks (dir), how far (dist), when (t0, tw; the pose from tPose)
local function arriveBodies(s: any, ends: { any }, folder: Instance, riser: boolean)
	local A: any = { bodies = {}, hero = nil, land = 2.6, cut = 3.2, near0 = 5.6, near1 = 3.3 }
	s.arrive = A
	local skip: { Instance } = { folder }
	for _, p in Players:GetPlayers() do if p.Character then table.insert(skip, p.Character) end end
	local pets = workspace:FindFirstChild("ClientPets")
	if pets then table.insert(skip, pets) end
	local AR = V.ARRIVE
	local tHero = AR.minArrive
	for i, en in ends do
		local fin: CFrame = en.cf
		local dir = flat(fin.LookVector)
		local want = if i == 1 then (if riser then AR.riserHero else AR.hero) else (if riser then AR.riserMate else AR.mate)
		local dist = want
		if riser then
			-- (THE RISER's own set isn't queryable: its depths are known. a teammate stays on the riser's top)
			if i > 1 then
				local loc = s.frame:PointToObjectSpace(fin.Position)
				local ld = s.frame:VectorToObjectSpace(dir)
				while dist > 0 and Vector3.new(loc.X - ld.X * dist, 0, loc.Z - ld.Z * dist).Magnitude > 10.9 do dist -= 0.2 end
				dist = math.max(0, dist)
			end
		else
			dist = roomBehind(fin.Position, -dir, want, skip)
		end
		local he = table.clone(en.e)
		he.emote = nil -- (no emotes: everyone walks in and lands a pose)
		local b = makeBody(he, fin, en.pose, folder, true)
		if not b then continue end
		-- when: the one in front lands first (never sooner than minArrive: a short walk starts late, from an idle);
		-- each teammate stagger s later, walking a little slower (a walk too long for the time is cut short)
		local speed = if i == 1 then AR.speed else AR.mateSpeed
		local T = if i == 1 then math.max(AR.minArrive, 1.3 * dist / speed) else tHero + AR.stagger * (i - 1)
		if i == 1 then tHero = T end
		local tw = 1.3 * dist / speed
		if tw > T then dist = T * speed / 1.3; tw = T end
		local hum = b.model:FindFirstChildOfClass("Humanoid")
		local animator = hum and hum:FindFirstChildOfClass("Animator")
		local r6 = hum ~= nil and hum.RigType == Enum.HumanoidRigType.R6
		local function load(id: string): AnimationTrack?
			if not animator then return nil end
			local an = Instance.new("Animation")
			an.AnimationId = id
			local ok, tr = pcall(function() return (animator :: Animator):LoadAnimation(an) end)
			if not ok or not tr then return nil end
			tr.Priority = Enum.AnimationPriority.Action; tr.Looped = true -- (one priority: the weights below share it out)
			return tr
		end
		local pd = V.POSES[en.pose] or V.POSES.victory
		local up = if r6 then 3 else ((hum and hum.HipHeight or 2) + b.root.Size.Y / 2)
		local a = {
			b = b, fin = fin, dir = dir, dist = dist, t0 = T - tw, tw = math.max(tw, 1e-3), tPose = T - 0.12,
			once = pd.once == true, poseLen = pd.len, holdAt = pd.hold, up = up, rootToPivot = b.root.CFrame:ToObjectSpace(b.model:GetPivot()),
			idle = load(if r6 then AR.idle6 else AR.idle),
			walk = if dist > 0 then load(if r6 then V.WALK.walk6 else V.WALK.walk) else nil,
			pose = load(pd.anim),
		}
		b.track = a.pose
		table.insert(A.bodies, a)
		table.insert(s.bodies, b)
		if i == 1 then A.hero = a end
	end
	local h = A.hero
	if not h then return end
	A.land = h.tPose + (if h.holdAt then h.holdAt elseif h.once then h.poseLen else 0.9)
	A.cut = math.clamp(A.land + 0.6, 2.4, math.max(2.4, s.len - 1.3))
	-- the close lens's room in front of the one in front (a map's spot: a wall there pulls it in)
	local k = h.up / 3
	A.near0, A.near1 = 5.6 * k, 3.6 * k
	if not riser then
		local o = h.fin.Position + Vector3.new(0, 1.5 * k, 0)
		local hit = blockHit(rayParams(skip), o, h.dir * (6.4 * k), false)
		if hit then
			local df = (hit.Position - o).Magnitude - 0.7
			A.near1 = math.max(2.0, math.min(A.near1, df))
			A.near0 = math.max(A.near1, math.min(A.near0, df))
		end
	end
end

-- a body's floor point at t: a steady walk easing onto its mark
local function arriveAt(a: any, t: number): Vector3
	if a.dist <= 0 then return a.fin.Position end
	local tau = math.clamp((t - a.t0) / a.tw, 0, 1)
	local g = 1 - (1 - tau) ^ 1.3
	return a.fin.Position - a.dir * (a.dist * (1 - g))
end

-- a paused track at a moment and a weight
local function scrub(tr: AnimationTrack?, w: number, at: number, loop: boolean, stopAt: number?)
	if not tr then return end
	local L = tr.Length
	if L <= 0 then return end -- (still loading: preloaded at the top, so rare)
	if not tr.IsPlaying then tr:Play(0, 0.001, 0) end
	tr:AdjustSpeed(0)
	tr.TimePosition = if loop then at % L else math.clamp(at, 0, math.min(L - 0.02, stopAt or L))
	tr:AdjustWeight(math.max(w, 0.001), 0)
end

local function arriveMove(s: any, t: number)
	local te = if s.hold then 1e3 else t -- (skipped or held: everyone on their mark, in their pose)
	for _, a in s.arrive.bodies do
		local p = arriveAt(a, te)
		a.b.model:PivotTo(CFrame.lookAt(p, p + a.dir) * CFrame.new(0, a.up, 0) * a.rootToPivot)
		-- idle (before a late start) -> walk -> pose; the walk's clip follows the distance walked (feet on the floor)
		local wP = math.clamp((te - a.tPose) / V.ARRIVE.blend, 0, 1)
		local wI, wW
		if a.walk then
			wI = 1 - math.clamp((te - a.t0) / 0.2, 0, 1)
			wW = (1 - wI) * (1 - wP)
		else
			wI, wW = 1 - wP, 0
		end
		local walked = a.dist - (a.fin.Position - p).Magnitude
		scrub(a.idle, wI, te, true)
		scrub(a.walk, wW, walked / V.ARRIVE.stride, true)
		scrub(a.pose, wP, te - a.tPose, not a.once, a.holdAt)
	end
end

-- the winners' close lens at t (before the cut)
local function arriveCam(s: any, t: number): (CFrame, number)
	local A = s.arrive
	local h = A.hero
	local k = h.up / 3
	local F, U = h.dir, Vector3.yAxis
	local R = F:Cross(U) -- (their right: the weapon hand's side)
	local base = h.fin.Position
	local u = smooth(t / A.land) -- (the push runs the whole walk and lands with the pose)
	local near = A.near0 + (A.near1 - A.near0) * u
	-- (on their off hand's side, a little above the knee - Studio v1476, Platform: on the weapon side the walk's arm swing
	-- blacked out the glass and the raised weapon arm stood between the lens and the face)
	-- (it ends square in front and a little higher: with both arms up, a lens off to either side puts an arm over the
	-- face - Studio v1476/R, Platform)
	local at = base + F * near - R * k * (1.5 - 1.35 * u) + U * k * (1.3 + 0.9 * u)
	-- the settle once the pose is held: a slow ease back and round
	local sd = 1 - math.exp(-math.max(0, t - A.land) * 2.2)
	at += (F * 0.3 - R * 0.2 + U * 0.1) * k * sd
	local look = (arriveAt(h, t) + U * k * 3.35):Lerp(base + U * k * 4.1 + R * k * 0.25, u)
	local fov = 60 + 10 * u
	-- the kick as the pose lands
	local kt = t - (A.land - 0.08)
	if kt > 0 then fov -= 3.5 * math.exp(-kt * 7) end
	return CFrame.lookAt(at, look), fov
end

-- ------------------------------------------------------------------ the look (Lighting, saved and put back)
local LIGHT_PROPS = { "ClockTime", "Brightness", "Ambient", "OutdoorAmbient", "ExposureCompensation", "EnvironmentDiffuseScale",
	"EnvironmentSpecularScale", "GlobalShadows", "ShadowSoftness", "GeographicLatitude", "FogEnd", "FogStart" }
local function saveLook(): any
	local s = { props = {}, fx = {}, atmo = nil }
	for _, k in LIGHT_PROPS do s.props[k] = (Lighting :: any)[k] end
	for _, e in Lighting:GetChildren() do
		if e:IsA("PostEffect") then s.fx[e] = e.Enabled; e.Enabled = false end
	end
	local a = Lighting:FindFirstChildOfClass("Atmosphere")
	if a then s.atmo = { a = a, Density = a.Density, Haze = a.Haze, Glare = a.Glare, Offset = a.Offset } end
	return s
end
local function setLook(win: boolean)
	local L = Lighting :: any
	L.ClockTime = 14.2; L.GeographicLatitude = 30
	L.Brightness = 2.4; L.ExposureCompensation = if win then 0.05 else -0.1
	L.Ambient = Color3.fromRGB(78, 76, 74); L.OutdoorAmbient = Color3.fromRGB(128, 126, 124)
	L.EnvironmentDiffuseScale = 0.6; L.EnvironmentSpecularScale = 0.4
	L.GlobalShadows = true; L.ShadowSoftness = 0.35
	L.FogEnd = 100000; L.FogStart = 0
	local a = Lighting:FindFirstChildOfClass("Atmosphere")
	if a then a.Density = 0; a.Haze = 0; a.Glare = 0 end
end
local function putLook(s: any)
	if not s then return end
	for k, v in s.props do pcall(function() (Lighting :: any)[k] = v end) end
	for e, on in s.fx do if e.Parent then e.Enabled = on end end
	if s.atmo and s.atmo.a.Parent then
		s.atmo.a.Density = s.atmo.Density; s.atmo.a.Haze = s.atmo.Haze; s.atmo.a.Glare = s.atmo.Glare; s.atmo.a.Offset = s.atmo.Offset
	end
end

-- ------------------------------------------------------------------ what else stands at a map's spot
-- (Studio v1421: a figure with an overhead padlock stood behind the bodies at RooftopV3's spot; Replay.hideLive covers
-- players and workspace.Dummies only.) every other body near the spot - an NPC, a stand-in, a dummy - is hidden on this
-- screen while the scene runs, with its overhead tags; looked for at the start and 1.5 s in, put back at the end
local hiddenNear: { [Instance]: number } = {} -- (a part or decal -> its LocalTransparencyModifier before; a gui -> 1)
local function hideNear(center: Vector3, keep: Instance)
	for _, d in workspace:GetDescendants() do
		if d:IsA("Humanoid") then
			local m = d.Parent
			if not m or m:IsDescendantOf(keep) then continue end
			local root = m:FindFirstChild("HumanoidRootPart") or m:FindFirstChild("Head")
			if not (root and root:IsA("BasePart")) or (root.Position - center).Magnitude > 450 then continue end -- (a far spawn shows too: v1436)
			for _, x in m:GetDescendants() do
				if (x:IsA("BasePart") or x:IsA("Decal")) and hiddenNear[x] == nil then
					hiddenNear[x] = (x :: any).LocalTransparencyModifier; (x :: any).LocalTransparencyModifier = 1
				elseif (x:IsA("BillboardGui") or x:IsA("SurfaceGui")) and x.Enabled and hiddenNear[x] == nil then
					hiddenNear[x] = 1; x.Enabled = false
				end
			end
		end
	end
end
-- (the owner's pet, the knee-high Mini Mannequin, follows them on every screen: client/Pets, workspace.ClientPets.
-- it has no Humanoid, so the look above misses it: v1449, The Gut's spot. written every frame: the pet's follower
-- rewrites its parts' LocalTransparencyModifier now and then so nothing can leave it hidden - the spot check, 27 Nov,
-- found it standing by the team on four maps)
local function hidePets()
	local f = workspace:FindFirstChild("ClientPets")
	if not f then return end
	for _, x in f:GetDescendants() do
		if x:IsA("BasePart") or x:IsA("Decal") then
			if hiddenNear[x] == nil then hiddenNear[x] = (x :: any).LocalTransparencyModifier end
			if (x :: any).LocalTransparencyModifier ~= 1 then (x :: any).LocalTransparencyModifier = 1 end
		elseif x:IsA("Highlight") and x.Enabled then -- (its pink outline draws even with the parts hidden)
			hiddenNear[x] = 1; x.Enabled = false
		end
	end
end
local function showNear()
	for x, v in hiddenNear do
		if x.Parent then
			if x:IsA("LayerCollector") or x:IsA("Highlight") then (x :: any).Enabled = true else (x :: any).LocalTransparencyModifier = v end
		end
	end
	table.clear(hiddenNear)
end

-- ------------------------------------------------------------------ the run
type State = {
	msg: any, win: boolean, len: number, t0: number, hold: boolean, held: number?, frame: CFrame, folder: Folder,
	bodies: { Body }, look: any, cc: ColorCorrectionEffect, bloom: BloomEffect, fov: number, shots: { any }, sting: Sound?,
	holdK: any, spot: any?, lit: { Light }, blurs: { [Instance]: boolean }, sweptAt: number, walk: any?, arrive: any?,
}
local st: State? = nil

local function ease(u: number, kind: string): number
	u = math.clamp(u, 0, 1)
	if kind == "out" then return 1 - (1 - u) ^ 4 end
	return u * u * (3 - 2 * u)
end
local function lerpShot(a: any, b: any, u: number): (Vector3, Vector3, number)
	return a.at:Lerp(b.at, u), a.look:Lerp(b.look, u), a.fov + (b.fov - a.fov) * u
end

local function camAt(s: State, t: number): (CFrame, number)
	if s.walk then
		local wa, wl, wf = walkCam(s, t)
		return CFrame.lookAt(wa, wl), wf
	end
	if s.arrive and s.arrive.hero and s.win and not s.hold and t < s.arrive.cut then return arriveCam(s, t) end
	local at, look, fov
	if s.hold or t >= s.len then
		local h = if s.spot then s.holdK else holdOf(s.win)
		local since = if s.held then t - s.held else t - s.len
		-- a slow drift round the held framing (the bodies keep moving, the lens breathes)
		local w = since * 0.32
		at = h.at + Vector3.new(math.sin(w) * 0.55, math.sin(w * 0.7) * 0.18, math.cos(w) * 0.3 - 0.3)
		look, fov = h.look, h.fov
	else
		local shot = s.shots[#s.shots]
		for _, sh in s.shots do if t < sh.t1 then shot = sh; break end end
		local u = ease((t - shot.t0) / (shot.t1 - shot.t0), shot.ease)
		at, look, fov = lerpShot(shot.from, shot.to, u)
	end
	local wa, wl = s.frame:PointToWorldSpace(at), s.frame:PointToWorldSpace(look)
	return CFrame.lookAt(wa, wl), fov
end

local function step(dt: number?)
	local s = st
	if not s then return end
	if Replay.mode and Replay.mode() == "potm" then Scene.stop("replay"); return end -- (the play of the match has the screen)
	local t = os.clock() - s.t0
	local fz = workspace:GetAttribute("VictoryFreeze") -- (Studio photos: the lens held at that moment)
	if type(fz) == "number" then t = fz; s.held = if s.hold then fz - 0.001 else s.held end
	local cam = workspace.CurrentCamera :: Camera
	if s.walk and s.hold then t = math.max(t, s.len) end -- (skipped: the walk's end, held)
	local cf, fov = camAt(s, t)
	if s.walk then
		s.walk.dt = dt or (1 / 60)
		walkMove(s, t)
		cf, fov = walkFear(s, t, cf, fov)
	end
	if s.arrive then arriveMove(s, t) end
	if s.spot then
		Replay.hideLive(true) -- (in the map itself: the live bodies would stand among ours)
		-- (a whole-workspace look is costly on these maps: once at the start, once 1.5 s in for late arrivals)
		if s.sweptAt == 0 or (s.sweptAt > 0 and os.clock() - s.t0 > 1.5) then
			s.sweptAt = if s.sweptAt == 0 then 1 else -1
			hideNear(s.spot.hero.Position, s.folder)
		end
		hidePets() -- (cheap: a pet moves its parts every frame, so its hide is kept every frame)
	end
	cam.CameraType = Enum.CameraType.Scriptable
	cam.CFrame = cf
	cam.FieldOfView = fov
end

-- the stage's front faces the sun a little to one side, so the light falls on faces (the set is our own: it can turn)
local function frameFor(): CFrame
	local sun = Lighting:GetSunDirection()
	local h = Vector3.new(sun.X, 0, sun.Z)
	local front = if h.Magnitude > 0.1 then h.Unit else Vector3.new(0, 0, 1)
	front = CFrame.Angles(0, math.rad(-32), 0):VectorToWorldSpace(front)
	return CFrame.lookAt(STAGE_AT, STAGE_AT - front) -- (local +Z = front, toward the lens)
end

local function sting(win: boolean): Sound?
	local k = kitOf()
	local src = k and k:FindFirstChild(if win then "Win" else "Lose")
	if not (src and src:IsA("Sound")) then return nil end
	local s = src:Clone()
	local master = SoundService:FindFirstChild("JankMaster")
	local g = master and master:FindFirstChild("Music")
	if g and g:IsA("SoundGroup") then s.SoundGroup = g end
	s.Parent = SoundService
	s:Play()
	s.Ended:Once(function() s:Destroy() end)
	-- (a longer sting fades out under the card: the kit's FadeAt attribute, seconds)
	local fade = src:GetAttribute("FadeAt")
	if type(fade) == "number" then
		task.delay(fade, function()
			if not s.Parent then return end
			TweenService:Create(s, TweenInfo.new(1.6, Enum.EasingStyle.Sine), { Volume = 0 }):Play()
			task.delay(1.7, function() if s.Parent then s:Destroy() end end)
		end)
	end
	return s
end

-- THE MAP'S OWN SPOT (the server reads the arena's "Victory" model: world space). the losers' lens, when the map has
-- none: the held wide pulled back, lowered toward the floor and narrowed
local function loseOf(spot: any): (any, any)
	local w = spot.wide[2]
	local dir = (w.look - w.at).Unit
	local floorY = spot.hero.Position.Y
	local back = w.at - dir * 14
	local b = { at = Vector3.new(back.X, floorY + (w.at.Y - floorY) * 0.55, back.Z), look = w.look, fov = w.fov * 0.72 }
	local side = dir:Cross(Vector3.yAxis).Unit
	local a = { at = b.at - side * 4, look = w.look - side * 1.5, fov = b.fov + 2 }
	return a, b
end
local function spotShots(spot: any, win: boolean, len: number): ({ any }, any)
	if win then
		return { { t0 = 0, t1 = RISE_T, ease = "inout", from = spot.rise[1], to = spot.rise[2] },
			{ t0 = RISE_T, t1 = len, ease = "out", from = spot.wide[1], to = spot.wide[2] } }, spot.hold or spot.wide[2]
	end
	local a, b = if spot.lose then spot.lose[1] else nil, if spot.lose then spot.lose[2] else nil
	if not (a and b) then a, b = loseOf(spot) end
	return { { t0 = 0, t1 = len, ease = "out", from = a, to = b } }, b
end

function Scene.on(): boolean return st ~= nil end
function Scene.t(): number return if st then os.clock() - st.t0 else 0 end
function Scene.win(): boolean return st ~= nil and st.win end

function Scene.start(msg: any, opts: any?): boolean
	Scene.stop("restart")
	local win = msg.youWon == true
	local len = tonumber(msg.len) or V.LEN
	local spot = if type(msg.spot) == "table" and typeof(msg.spot.hero) == "CFrame" then msg.spot else nil
	local folder = Instance.new("Folder")
	folder.Name = "JankVictory"
	local look, frame, shots, holdK = nil, CFrame.identity, nil, nil
	local lit: { Light } = {}
	local blurs: { [Instance]: boolean } = {}
	if spot then
		-- the map's own light and look stay; only a menu's blur or depth of field goes, and the spot's lights come on
		for _, root in { Lighting, workspace.CurrentCamera } :: { Instance } do
			for _, e in root:GetChildren() do
				if (e:IsA("BlurEffect") or e:IsA("DepthOfFieldEffect")) and (e :: any).Enabled then blurs[e] = true; (e :: any).Enabled = false end
			end
		end
		if typeof(spot.lights) == "Instance" then
			for _, l in (spot.lights :: Instance):GetDescendants() do
				if l:IsA("Light") and not l.Enabled then l.Enabled = true; table.insert(lit, l) end
			end
		end
		-- (a walk spot has a path, no lenses of its own: its lens is walkCam's)
		if spot.kind == "walk" then shots, holdK = {}, nil else shots, holdK = spotShots(spot, win, len) end
	else
		local set = buildSet()
		if not set then warn("[jankfire] victory: no stage kit (ReplicatedStorage.JankfireVictory.Stage)"); return false end
		look = saveLook()
		setLook(win)
		frame = frameFor()
		set:PivotTo(frame)
		set.Parent = folder
		-- the accent: the winning side's colour on the stage's lip
		local wt = tonumber(msg.winner) or 1
		local accent = TeamColors.color(((wt - 1) % 4) + 1)
		local lip = set:FindFirstChild("Lip", true)
		if lip and lip:IsA("BasePart") then lip.Color = accent end
		shots = shotsFor(win, len)
	end
	folder.Parent = workspace
	-- the bodies (built once the state is up): where each ends and its pose - the one in front, then teammates
	local bodies = {}
	local stage = if type(msg.stage) == "table" then msg.stage else {}
	local walking = spot ~= nil and spot.kind == "walk" and type(spot.path) == "table" and #spot.path >= 2
	local ends = {}
	if not walking then
		local used: { [string]: boolean } = {}
		local mates = {}
		for i, e in stage do
			if i == 1 then
				-- (the one in front faces the held lens a little; every body faces the camera side, +Z; a map's spot says)
				local cf = if spot then spot.hero else frame * CFrame.lookAt(FRONT, Vector3.new(2.4, FRONT.Y, 20))
				table.insert(ends, { e = e, cf = cf, pose = V.pick(V.HERO_POSES, e.uid) })
			else
				table.insert(mates, e)
			end
		end
		local places = MATES[math.min(#mates, 3)] or {}
		for i, e in mates do
			local cf: CFrame
			if spot then
				if not spot.mates[i] then break end
				cf = spot.mates[i]
			else
				local at = places[i]
				if not at then break end
				-- (a teammate turns a little toward the middle of the front)
				cf = frame * CFrame.lookAt(at, Vector3.new(at.X * 0.35, at.Y, 18))
			end
			local pose = V.pick(V.MATE_POSES, e.uid, used)
			used[pose] = true
			table.insert(ends, { e = e, cf = cf, pose = pose })
		end
	end
	-- the grade (ours alone while it runs: the arena's post effects are off)
	local cam = workspace.CurrentCamera :: Camera
	local cc = Instance.new("ColorCorrectionEffect")
	cc.Name = "JankVictoryGrade"
	if win then
		cc.Saturation = 0.06; cc.Contrast = 0.08; cc.Brightness = 0.01; cc.TintColor = Color3.fromRGB(255, 251, 246)
	else
		cc.Saturation = -0.42; cc.Contrast = 0.06; cc.Brightness = -0.03; cc.TintColor = Color3.fromRGB(226, 231, 240)
	end
	cc.Parent = cam
	local bloom = Instance.new("BloomEffect")
	bloom.Name = "JankVictoryBloom"; bloom.Intensity = 0.35; bloom.Size = 22; bloom.Threshold = 1.6
	bloom.Parent = cam
	local s: State = {
		msg = msg, win = win, len = len, t0 = os.clock(), hold = opts ~= nil and opts.hold == true, held = nil, frame = frame,
		folder = folder, bodies = bodies, look = look, cc = cc, bloom = bloom, fov = cam.FieldOfView, shots = shots,
		sting = nil, holdK = holdK, spot = spot, lit = lit, blurs = blurs, sweptAt = 0,
	}
	if s.hold then s.held = 0 end
	st = s
	if walking then
		local blur = Instance.new("BlurEffect")
		blur.Name = "JankVictoryFearBlur"; blur.Size = 0; blur.Parent = cam
		s.walk = { P = pathOf(spot.path), bodies = {}, tStop = math.max(1, len - V.WALK.startleAt), fear = fearGui(), blur = blur }
		walkBodies(s, stage, folder)
		if not (opts and opts.quiet) then
			s.walk.amb = walkSound("WalkAmb", true)
			s.walk.heart = walkSound("Heartbeat", true)
		end
	else
		arriveBodies(s, ends, folder, spot == nil)
		-- (the winners: the close lens, then the wide from the cut - the old crane lens goes)
		local A = s.arrive
		if win and A and A.hero and #s.shots > 0 then
			local wide = table.clone(s.shots[#s.shots])
			wide.t0 = A.cut
			s.shots = { wide }
		end
		if not (opts and opts.quiet) then s.sting = sting(win) end
	end
	RunService:BindToRenderStep("JankVictoryCam", Enum.RenderPriority.Last.Value + 80, step)
	step()
	return true
end

function Scene.hold()
	local s = st
	if not s or s.hold then return end
	s.hold = true
	s.held = os.clock() - s.t0
end

function Scene.stop(why: string?)
	local s = st
	if not s then return end
	st = nil
	pcall(function() RunService:UnbindFromRenderStep("JankVictoryCam") end)
	for _, b in s.bodies do if b.track then pcall(function() (b.track :: AnimationTrack):Stop(0) end) end end
	if setModel then setModel.Parent = nil end -- (kept for the next match)
	s.folder:Destroy()
	s.cc:Destroy(); s.bloom:Destroy()
	if s.sting and s.sting.Parent then s.sting:Destroy() end
	putLook(s.look)
	for _, l in s.lit do if l.Parent then l.Enabled = false end end
	for e in s.blurs do if e.Parent then (e :: any).Enabled = true end end
	if s.spot then Replay.hideLive(false); showNear() end
	if s.arrive then
		for _, a in s.arrive.bodies do
			for _, tr in { a.idle, a.walk } do if tr then pcall(function() tr:Stop(0) end) end end
		end
	end
	if s.walk then
		local W = s.walk
		if W.fear and W.fear.gui then W.fear.gui:Destroy() end
		if W.blur then W.blur:Destroy() end
		for _, snd in { W.amb, W.heart } do if snd and snd.Parent then snd:Destroy() end end
		for _, w in W.bodies do
			for _, tr in { w.walk, w.upper, w.startle } do if tr then pcall(function() tr:Stop(0) end) end end
		end
	end
	local cam = workspace.CurrentCamera :: Camera
	cam.CameraType = Enum.CameraType.Custom
	cam.FieldOfView = s.fov
	if why and RunService:IsStudio() then print("[jankfire] VictoryStop: " .. why) end
end

return Scene
