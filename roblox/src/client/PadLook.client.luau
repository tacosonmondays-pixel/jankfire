--!strict
-- looking with a controller's right stick (18 Nov 2026, controller support; layout and numbers: docs/CONTROLLER.md).
-- the stick turns the camera the way the phone's look (TouchControls) and the guns' kick already do: a change from this
-- frame's look, after the camera module and the shoulder camera (Camera + 2), so first person, the shoulder camera, the
-- aim's zoom and the recoil all read it back next frame like everything else that moves the view. Roblox's own stick
-- turn is switched off for it (SettingsApply's CameraInput wrapper), so nothing turns twice.
--   the stick: a round inner deadzone, an outer one (pushed that far counts as all the way), a response curve
--   (LINEAR / STANDARD / DYNAMIC), the look speed (pad.sens) and its up-down part (pad.ySpeed, pad.invert); held all the
--   way over, the turn speeds up (pad.accel); with the sights up, the web game's rule: the zoom's share and pad.ads
--   aim assist (pad.assist, pad.assistK; a controller only, never a mouse): public/js/aimassist.js's rules and ring, as
--   on a phone: near an enemy in plain sight your turn slows down, and while you move or look, the crosshair follows a
--   little of the way they drift across your view (your strafe or theirs) plus a small tug toward their body. never a
--   teammate, never through a wall, never the head, never while your sticks are still. ranked keeps it to 60 %.
-- Studio tests: player attribute PadTest = "stick2:x,y" / "stick1:x,y" (a pretend stick, -1..1), "clear", "state"
-- (writes PadState as JSON: the look this frame, the target, the slow-down), "press:ButtonR2" / "release:ButtonR2"
-- (a pretend button through Keys: every Keys.began listener hears it as a pad's); a "#n" on the end makes a repeat count
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local HttpService = game:GetService("HttpService")

local me = Players.LocalPlayer
local J = script.Parent
local Pad = require(J:WaitForChild("Pad")) :: any
local Settings = require(J:WaitForChild("Settings")) :: any
local Keys = require(J:WaitForChild("Keys")) :: any
local MenuCursor = require(J:WaitForChild("MenuCursor")) :: any
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons")) :: any
local Hitbox = require(Shared:WaitForChild("Hitbox")) :: any
local W = Weapons.list :: { [string]: any }
local SM = Weapons.S :: number
local S = Settings.get

-- ------------------------------------------------------------------ the numbers (CONTROLLER.md)
local YAW_RATE = math.rad(240) -- full stick at look speed 1.00 (Roblox's own pad camera: 4 degrees a frame at 60 fps)
local PITCH_K = 0.77 -- up and down is this much of side to side (Roblox's own)
local ACCEL_AT, ACCEL_WAIT, ACCEL_RAMP, ACCEL_MAX = 0.92, 0.12, 0.4, 1.75 -- held past 92 % for 0.12 s: up to 1.75x over 0.4 s
local PITCH_MAX = math.rad(80)
-- aim assist (aimassist.js: RING, PULL, RANGE, RATE; the pad's own: ROT, TUG)
local RING, PULL, RANGE, RATE = 0.14, 0.085, 90 * SM, 0.38
local TUG = 0.6 -- the tug at 60 % of the phone's
local ROT, ROT_MAX = 0.35, 1.2 -- the crosshair follows 35 % of a target's drift, at most 1.2 rad/s
local RANKED_CAP = 0.6
local ACTIVE_FOR = 0.35 -- seconds a stick push counts as "doing something"
local STICK_ON = 0.2 -- a move stick pushed this far counts

local CURVES: { [string]: (number) -> number } = {
	linear = function(t) return t end,
	standard = function(t) return t ^ 1.7 end,
	dynamic = function(t) return t * t * (3 - 2 * t) end,
}
local function shape(raw: Vector2): Vector2
	local m = raw.Magnitude
	local inner = math.clamp(tonumber(S("pad.dead")) or 0.12, 0, 0.45)
	local outer = math.clamp(1 - (tonumber(S("pad.outer")) or 0.05), inner + 0.05, 1) -- (pad.outer: the edge's share that counts as all the way)
	if m <= inner then return Vector2.zero end
	local t = math.clamp((m - inner) / (outer - inner), 0, 1)
	local f = CURVES[S("pad.curve")] or CURVES.standard
	return raw / m * f(t)
end
Settings.padShape = shape -- (the tests read it)

-- ------------------------------------------------------------------ when the stick may turn the view
local function alive(): (Model?, BasePart?)
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or hum.Health <= 0 or not root then return nil, nil end
	return ch, root
end
local function menuUp(): boolean
	return MenuCursor.on() or me:GetAttribute("LoadoutOpen") == true or me:GetAttribute("SettingsOpen") == true
end
local function cinematic(): boolean
	if me:GetAttribute("Finishing") or me:GetAttribute("LootOpening") ~= nil then return true end
	local dc = me:GetAttribute("DeathCamState")
	if type(dc) == "string" and string.sub(dc, 1, 3) ~= "off" then return true end
	return false
end
local function camOk(cam: Camera): boolean
	if cam.CameraType == Enum.CameraType.Custom then return true end
	-- (the shoulder camera: Scriptable while ThirdPerson is on; any other scripted camera is a cinematic's own)
	return cam.CameraType == Enum.CameraType.Scriptable and me:GetAttribute("ThirdPerson") == true
end

-- how far the sights are up and the held gun's zoom (as the phone reads it: Arsenal's view is base / (1 + (zoom-1)*aim))
local function aimState(): (number, number)
	local L = Settings.live
	local w = W[(L and L.wid) or ""]
	local z = if w and w.ads and type(w.ads.zoom) == "number" then w.ads.zoom else 1
	return math.clamp((L and L.aim) or 0, 0, 1), math.max(1, z)
end

-- ------------------------------------------------------------------ aim assist
local assistParams = RaycastParams.new()
assistParams.FilterType = Enum.RaycastFilterType.Include
local function wrapA(a: number): number
	while a > math.pi do a -= 2 * math.pi end
	while a < -math.pi do a += 2 * math.pi end
	return a
end
local function fightZone(): boolean
	local z = me:GetAttribute("Zone")
	return z ~= "hub" and z ~= "staging"
end
local function strength(): number
	if S("pad.assist") == false then return 0 end
	local k = math.clamp(tonumber(S("pad.assistK")) or 1, 0, 1)
	if me:GetAttribute("HookLimit") == true then k = math.min(k, RANKED_CAP) end -- (ranked: HookChargeServer's flag)
	return k
end
type Target = { ang: number, size: number, zoom: number, yawErr: number, pitchErr: number, dir: Vector3, model: Model }
local function target(cam: Camera): Target?
	local e, l = cam.CFrame.Position, cam.CFrame.LookVector
	local aim, z = aimState()
	local zoom = if aim > 0.5 then z else 1
	local yaw, pitch = math.atan2(-l.X, -l.Z), math.asin(math.clamp(l.Y, -1, 1))
	local myTeam = me:GetAttribute("Team")
	local map = workspace:FindFirstChild("Map")
	if map then assistParams.FilterDescendantsInstances = { map } end
	local best: Target? = nil
	local bestAng = math.huge
	local function try(m: Model, pl: Player?)
		if pl and myTeam ~= nil and pl:GetAttribute("Team") == myTeam then return end -- (never a teammate)
		local hum = m:FindFirstChildOfClass("Humanoid")
		local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not hum or not root or hum.Health <= 0 then return end
		local c = Hitbox.feet(root.Position) + Vector3.new(0, Weapons.BOX.bodyTop / 2, 0) -- (the body box's middle: never the head)
		local to = c - e
		local d = to.Magnitude
		if d > RANGE or d < 0.8 * SM then return end
		local dir = to / d
		local size = math.atan2(0.45 * SM, d) -- (up close the ring grows with them)
		local ang = math.acos(math.clamp(dir:Dot(l), -1, 1))
		if ang > (RING + size) / zoom or ang >= bestAng then return end -- (scoped in, the ring shrinks with the zoom)
		if map and workspace:Raycast(e, to, assistParams) then return end -- (a wall in the way)
		bestAng = ang
		best = { ang = ang, size = size, zoom = zoom, dir = dir, model = m,
			yawErr = wrapA(math.atan2(-dir.X, -dir.Z) - yaw), pitchErr = math.asin(dir.Y) - pitch }
	end
	for _, pl in Players:GetPlayers() do if pl ~= me and pl.Character then try(pl.Character, pl) end end
	local dm = workspace:FindFirstChild("Dummies")
	if dm then for _, m in dm:GetChildren() do if m:IsA("Model") then try(m, nil) end end end
	return best
end

-- ------------------------------------------------------------------ the turn, each frame
local held = 0 -- seconds the stick has been all the way over
local activeUntil = 0
local last = { yaw = 0, pitch = 0, slow = 1, tug = 0, rot = 0, ang = -1, stick = Vector2.zero, k = 0 }
local lastDir: Vector3? = nil
local lastModel: Model? = nil
RunService:BindToRenderStep("JankPadLook", Enum.RenderPriority.Camera.Value + 2, function(dtRaw: number)
	local dt = math.min(dtRaw, 0.1)
	local cam = workspace.CurrentCamera
	last.yaw, last.pitch, last.tug, last.rot, last.ang = 0, 0, 0, 0, -1
	if not cam or not Pad.on() or menuUp() or cinematic() or not camOk(cam) or UIS:GetFocusedTextBox() then
		held, lastDir, lastModel = 0, nil, nil
		return
	end
	local _, root = alive()
	if not root then held, lastDir, lastModel = 0, nil, nil; return end
	local now = os.clock()
	local s = shape(Pad.stick(2))
	last.stick = s
	if s.Magnitude > 0 or Pad.stick(1).Magnitude > STICK_ON then activeUntil = now + ACTIVE_FOR end

	-- speed: look speed x the aim's share (the web game's rule, as the mouse: SettingsApply's aimK) x acceleration
	local aim, zoom = aimState()
	local m = math.clamp(tonumber(S("pad.ads")) or 1, 0.1, 3)
	local aimK = (1 + (m - 1) * aim) / (1 + (zoom - 1) * aim)
	local sens = math.clamp(tonumber(S("pad.sens")) or 1, 0.05, 5)
	local accel = 1
	if S("pad.accel") ~= false and aim < 0.3 and s.Magnitude >= ACCEL_AT then
		held += dt
		accel = 1 + (ACCEL_MAX - 1) * math.clamp((held - ACCEL_WAIT) / ACCEL_RAMP, 0, 1)
	else
		held = 0
	end
	-- aim assist
	local k = if fightZone() then strength() else 0
	last.k = k
	local slow = 1
	local t: Target? = nil
	if k > 0 then
		t = target(cam)
		if t then
			local close = 1 - math.min(1, t.ang / ((RING + t.size) / t.zoom)) -- (0 at the ring's rim, 1 dead on)
			slow = 1 - math.min(0.6, 0.55 * k) * (0.35 + 0.65 * close)
			last.ang = math.deg(t.ang)
		end
	end
	last.slow = slow
	local ySign = if S("pad.invert") == true then -1 else 1
	local ySpeed = math.clamp(tonumber(S("pad.ySpeed")) or 1, 0.2, 3)
	local rate = YAW_RATE * sens * aimK * slow
	local yawD = -s.X * rate * accel * dt
	local pitchD = s.Y * rate * PITCH_K * ySpeed * ySign * dt
	if t and now <= activeUntil then
		-- the drift: how far their body moved across your view since last frame, from where you stand now
		if lastDir and lastModel == t.model then
			local a0 = math.atan2(-lastDir.X, -lastDir.Z)
			local a1 = math.atan2(-t.dir.X, -t.dir.Z)
			local dyaw = wrapA(a1 - a0)
			local dpitch = math.asin(math.clamp(t.dir.Y, -1, 1)) - math.asin(math.clamp(lastDir.Y, -1, 1))
			local cap = ROT_MAX * dt
			local ry = math.clamp(dyaw * ROT * k, -cap, cap)
			local rp = math.clamp(dpitch * ROT * k, -cap, cap)
			yawD += ry; pitchD += rp
			last.rot = math.deg(math.sqrt(ry * ry + rp * rp)) / dt
		end
		-- the tug toward the body (aimassist.js's, at TUG of its rate)
		local zone = (PULL + t.size) / t.zoom
		if t.ang <= zone and t.ang >= 0.004 then
			local fall = 1 - t.ang / zone
			local step = math.min(t.ang * 0.5, RATE * TUG * math.min(1.5, k) * (0.3 + 0.7 * fall) * dt / t.zoom)
			local f = step / t.ang
			yawD += t.yawErr * f
			pitchD += t.pitchErr * f
			last.tug = math.deg(step) / dt
		end
	end
	if t then lastDir, lastModel = t.dir, t.model else lastDir, lastModel = nil, nil end
	if yawD == 0 and pitchD == 0 then return end
	last.yaw, last.pitch = math.deg(yawD), math.deg(pitchD)
	local cf = cam.CFrame
	local pitch = math.asin(math.clamp(cf.LookVector.Y, -1, 1))
	local want = math.clamp(pitch + pitchD, -PITCH_MAX, PITCH_MAX)
	cam.CFrame = CFrame.new(cf.Position) * CFrame.fromAxisAngle(Vector3.yAxis, yawD) * cf.Rotation * CFrame.Angles(want - pitch, 0, 0)
end)

-- ------------------------------------------------------------------ Studio tests
if RunService:IsStudio() then
	me:GetAttributeChangedSignal("PadTest"):Connect(function()
		local raw = me:GetAttribute("PadTest")
		if type(raw) ~= "string" then return end
		local cmd = string.gsub(raw, "#%d+$", "")
		local op, rest = string.match(cmd, "^(%a+%d?):?(.*)$")
		if op == "stick1" or op == "stick2" then
			local x, y = string.match(rest, "^(%-?[%d%.]+),(%-?[%d%.]+)$")
			local code = if op == "stick1" then Enum.KeyCode.Thumbstick1 else Enum.KeyCode.Thumbstick2
			Pad.fake[code] = Vector3.new(tonumber(x) or 0, tonumber(y) or 0, 0)
		elseif op == "trigger" then
			local name, z = string.match(rest, "^(%w+),([%d%.]+)$")
			if name then Pad.fake[(Enum.KeyCode :: any)[name]] = Vector3.new(0, 0, tonumber(z) or 0) end
		elseif op == "clear" then
			table.clear(Pad.fake)
		elseif op == "press" or op == "release" then
			local ok, code = pcall(function() return (Enum.KeyCode :: any)[rest] end)
			if ok and code and Keys.padPress then Keys.padPress(code, op == "press") end
		elseif op == "state" then
			local cam = workspace.CurrentCamera
			local l = cam and cam.CFrame.LookVector or Vector3.zAxis
			me:SetAttribute("PadState", HttpService:JSONEncode({
				on = Pad.on(), yaw = last.yaw, pitch = last.pitch, slow = last.slow, tug = last.tug, rot = last.rot, ang = last.ang,
				k = last.k, stick = { last.stick.X, last.stick.Y }, look = { l.X, l.Y, l.Z }, fam = Pad.family(),
				wid = (Settings.live and Settings.live.wid) or "", aim = (Settings.live and Settings.live.aim) or 0,
				third = me:GetAttribute("ThirdPerson") == true, assistOn = S("pad.assist"), dead = S("pad.dead"),
				sel = (function() local o = game:GetService("GuiService").SelectedObject; return o and o:GetFullName() or "" end)(),
			}))
		end
	end)
end
