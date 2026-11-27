--!strict
-- THE VICTORY SCENE on screen (27 Nov 2026; shared/VictoryData.luau has the why, client/Victory.client.luau runs it).
-- THE RISER: a set of our own, built on this client far off the map (STAGE_AT): a round stage, a curved riser behind it
-- for teammates, a curved backdrop with a cove and white light panels; one accent, the stage's lip, in the winning
-- team's colour (ReplicatedStorage.JankfireVictory.Stage, from tools/roblox/victory_stage.py). The winning side stands on
-- it as clean copies of their bodies (Replay.templates: the look each player spawned with), each playing their emote or a
-- mocap victory pose. The camera is ours:
--   RISE   0 - 2.1 s  a low lens at the side of the one in front cranes up from the boots to the face
--   STAGE  2.1 - LEN  a cut to a wide front shot that pushes in and orbits a little to the held framing
--   HOLD   after      the held framing (the team on the left two-thirds, the card on the right), a slow drift
-- losers see the winners from the floor: one long low lens drifting across them, a colder, greyer grade.
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
	for _, p in V.POSES do
		local a = Instance.new("Animation")
		a.AnimationId = p.anim
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
local function makeBody(entry: any, cf: CFrame, pose: string, parent: Instance, seatY: number?): Body?
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
	if animator then
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
	-- (a sitting pose: once the clip has the body down, its seat goes onto the ledge's top)
	if seatY then
		task.delay(0.3, function()
			local lt = m:FindFirstChild("LowerTorso") :: BasePart? or m:FindFirstChild("Torso") :: BasePart?
			if not lt or not m.Parent then return end
			local bottom = lt.Position.Y - lt.Size.Y / 2
			m:PivotTo(m:GetPivot() + Vector3.new(0, (seatY :: number) + 0.05 - bottom, 0))
		end)
	end
	return b
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
-- it has no Humanoid, so the look above misses it: v1449, The Gut's spot)
local function hidePets()
	local f = workspace:FindFirstChild("ClientPets")
	if not f then return end
	for _, x in f:GetDescendants() do
		if (x:IsA("BasePart") or x:IsA("Decal")) and hiddenNear[x] == nil then
			hiddenNear[x] = (x :: any).LocalTransparencyModifier; (x :: any).LocalTransparencyModifier = 1
		end
	end
end
local function showNear()
	for x, v in hiddenNear do
		if x.Parent then
			if x:IsA("LayerCollector") then (x :: any).Enabled = true else (x :: any).LocalTransparencyModifier = v end
		end
	end
	table.clear(hiddenNear)
end

-- ------------------------------------------------------------------ the run
type State = {
	msg: any, win: boolean, len: number, t0: number, hold: boolean, held: number?, frame: CFrame, folder: Folder,
	bodies: { Body }, look: any, cc: ColorCorrectionEffect, bloom: BloomEffect, fov: number, shots: { any }, sting: Sound?,
	holdK: any, spot: any?, lit: { Light }, blurs: { [Instance]: boolean }, sweptAt: number,
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

local function step()
	local s = st
	if not s then return end
	if Replay.mode and Replay.mode() == "potm" then Scene.stop("replay"); return end -- (the play of the match has the screen)
	local t = os.clock() - s.t0
	local fz = workspace:GetAttribute("VictoryFreeze") -- (Studio photos: the lens held at that moment)
	if type(fz) == "number" then t = fz; s.held = if s.hold then fz - 0.001 else s.held end
	local cam = workspace.CurrentCamera :: Camera
	local cf, fov = camAt(s, t)
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
		shots, holdK = spotShots(spot, win, len)
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
	-- the bodies: the one in front, then the riser
	local bodies = {}
	local stage = if type(msg.stage) == "table" then msg.stage else {}
	local used: { [string]: boolean } = {}
	local mates = {}
	for i, e in stage do
		if i == 1 then
			local pose = V.pick(V.HERO_POSES, e.uid)
			-- (the one in front faces the held lens a little; every body faces the camera side, +Z; a map's spot says)
			local cf = if spot then spot.hero else frame * CFrame.lookAt(FRONT, Vector3.new(2.4, FRONT.Y, 20))
			-- (the one in front always takes a victory pose with the weapon up - main, 27 Nov: "a proper victory pose
			-- from mocap ... with the weapon raised to show its skin"; teammates keep their own emotes)
			local he = table.clone(e)
			he.emote = nil
			local b = makeBody(he, cf, pose, folder)
			if b then table.insert(bodies, b) end
		else
			table.insert(mates, e)
		end
	end
	local places = MATES[math.min(#mates, 3)] or {}
	for i, e in mates do
		local cf: CFrame
		local pose = V.pick(V.MATE_POSES, e.uid, used)
		local seatY: number? = nil
		if spot then
			if not spot.mates[i] then break end
			cf = spot.mates[i]
		else
			local at = places[i]
			if not at then break end
			if i == 2 and not e.emote then
				-- (THE RISER's second teammate sits on its front edge, legs over it)
				pose = V.SIT_POSE
				local flat = Vector3.new(at.X, 0, at.Z).Unit * 7.6
				at = Vector3.new(flat.X, RISER_TOP, flat.Z)
				seatY = frame:PointToWorldSpace(Vector3.new(0, RISER_TOP, 0)).Y
			end
			-- (a teammate turns a little toward the middle of the front)
			cf = frame * CFrame.lookAt(at, Vector3.new(at.X * 0.35, at.Y, 18))
		end
		used[pose] = true
		local b = makeBody(e, cf, pose, folder, seatY)
		if b then table.insert(bodies, b) end
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
	if not (opts and opts.quiet) then s.sting = sting(win) end
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
	local cam = workspace.CurrentCamera :: Camera
	cam.CameraType = Enum.CameraType.Custom
	cam.FieldOfView = s.fov
	if why and RunService:IsStudio() then print("[jankfire] VictoryStop: " .. why) end
end

return Scene
