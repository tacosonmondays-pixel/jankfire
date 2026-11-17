--!strict
-- SPEED LINES, THE WIND AT SPEED AND THE FOV KICK (17 Nov 2026, the owner: "when you pick up speed with the grapple can
-- you add those speed lines and wind effects from jank fire"). The web game's speedlines.js, ported: white anime streaks
-- run in from the screen's edges toward the point your velocity aims at on the screen. They start at 22 m/s and are at
-- full strength by 82 m/s (k = (speed - 22) / 60): 14 + 70k of them, random widths, each 0.12-0.52 x k opaque, all
-- redrawn at 30 fps; past mach 1 they go hot pink and yellow. Grapple swings, pads and slides alike: it reads the
-- body's real speed (1 m = 3 studs, Config).
-- The wind: a recorded wind loop (Pro Sound Effects "Barstow Wind Light Blustery Low Howl 1", the owner's rule: real
-- recordings only) rising with the speed, a little faster as it rises, on the EFFECTS volume (a Sound in SoundService:
-- SettingsApply puts it in that group); and thin wind streaks in the edges of the view, flying past you, as the lines grow.
-- The FOV kick (the web's main.js): + min(35, horizontal speed x 0.3) + 6 sprinting + the rope's swell (1.5 + up to 2.5
-- on a rope), eased; written to the player's SpeedFov attribute, which Arsenal adds to the base FOV.
-- Settings: gfx.speedLines (the lines, the wind streaks and the wind sound) and fov.kick, both on unless set off.
-- Off in menus (LoadoutOpen), during a replay or killcam, a finisher (FinisherT) and while dead.
-- Cheap: nothing while you're slow (one speed check a frame); the lines' labels change 30 times a second, at most 84.
-- Under every other screen (DisplayOrder -2), so the HUD and the touch buttons draw over it.
-- Test hook (Studio): the player attribute SpeedLinesTest = a speed in m/s draws as if you were going that fast (the
-- focus straight ahead); remove it to go back to the real speed.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local SoundService = game:GetService("SoundService")

local me = Players.LocalPlayer
local STUDIO = RunService:IsStudio()
local STUD = 3 -- studs a metre (Config: 1 m = 3 studs)
local WEDGE = "rbxassetid://103897494524802" -- (ui_speedline: a white wedge, its point at the left, its base the right edge)
local STREAK = "rbxassetid://127914373549121" -- (vfx_streak: a soft white streak along v)
local WIND = "rbxassetid://9113286782"
local MAXN = 84
local MACH = 1235 / 3.6 -- (m/s: the web's hot lines past 1235 km/h)
local HOT = { Color3.fromHex("ff4fd8"), Color3.fromHex("ffe14d") }
local WHITE = Color3.new(1, 1, 1)

local Settings: any = nil
do
	local ok, S = pcall(require, script.Parent:WaitForChild("Settings", 10) :: ModuleScript)
	if ok then Settings = S end
end
local Replay: any = nil
task.spawn(function()
	local m = script.Parent:WaitForChild("Replay", 10)
	if m and m:IsA("ModuleScript") then
		local ok, R = pcall(require, m)
		if ok then Replay = R end
	end
end)
local function setting(key: string): boolean
	if not Settings then return true end
	local ok, v = pcall(Settings.get, key)
	return not (ok and v == false)
end

-- the screen's streaks
local gui = Instance.new("ScreenGui")
gui.Name = "JankSpeedLines"; gui.ResetOnSpawn = false; gui.IgnoreGuiInset = true; gui.DisplayOrder = -2
gui.Parent = me:WaitForChild("PlayerGui")
local lines: { ImageLabel } = {}
for i = 1, MAXN do
	local l = Instance.new("ImageLabel")
	l.Name = "Line"; l.BackgroundTransparency = 1; l.BorderSizePixel = 0; l.Image = WEDGE; l.ScaleType = Enum.ScaleType.Stretch
	l.AnchorPoint = Vector2.new(0.5, 0.5); l.Visible = false
	l.Parent = gui
	lines[i] = l
end
local shown = 0

-- the wind's sound
local wind = Instance.new("Sound")
wind.Name = "SpeedWind"; wind.SoundId = WIND; wind.Looped = true; wind.Volume = 0
wind.Parent = SoundService
local windVol = 0

-- the wind streaks: a ring of emitters a little ahead of the camera, flying back past the edges of the view
local streakPart = Instance.new("Part")
streakPart.Name = "SpeedWindStreaks"; streakPart.Anchored = true; streakPart.CanCollide = false; streakPart.CanQuery = false
streakPart.CanTouch = false; streakPart.Transparency = 1; streakPart.Size = Vector3.new(16, 0.2, 16); streakPart.CastShadow = false
local streaks = Instance.new("ParticleEmitter")
streaks.Name = "Wind"; streaks.Texture = STREAK; streaks.Orientation = Enum.ParticleOrientation.VelocityParallel
streaks.Shape = Enum.ParticleEmitterShape.Disc; streaks.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
streaks.ShapePartial = 0.55 -- (an annulus: none across the middle of the view)
streaks.EmissionDirection = Enum.NormalId.Bottom; streaks.SpreadAngle = Vector2.new(4, 4)
streaks.LockedToPart = true; streaks.LightEmission = 0.7; streaks.LightInfluence = 0; streaks.Brightness = 1.2
streaks.Color = ColorSequence.new(WHITE)
streaks.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.45), NumberSequenceKeypoint.new(1, 0.3) }) -- (the texture's line is a quarter of its width)
streaks.Squash = NumberSequence.new(-2) -- (longer along their flight)
streaks.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.2, 0.55),
	NumberSequenceKeypoint.new(0.7, 0.7), NumberSequenceKeypoint.new(1, 1) })
streaks.Lifetime = NumberRange.new(0.18, 0.28); streaks.Speed = NumberRange.new(70, 100); streaks.Rate = 0
streaks.Enabled = false
streaks.Parent = streakPart

local acc = 0
local rng = Random.new()
local fovNow = 0

local function hide()
	if shown > 0 then for i = 1, shown do lines[i].Visible = false end; shown = 0 end
end

-- the web's drawing, on this screen: (fx, fy) the focus in -1..1, k the strength, hot past mach 1
local function draw(k: number, fx: number, fy: number, hot: boolean)
	local cam = workspace.CurrentCamera
	if not cam then return end
	local vp = cam.ViewportSize
	local W, H = vp.X, vp.Y
	local s = H / 180 -- (the web drew on a 320 x 180 canvas)
	local cx, cy = (fx * 0.5 + 0.5) * W, (-fy * 0.5 + 0.5) * H
	local R = math.sqrt(W * W + H * H) * 0.75
	local n = math.min(MAXN, math.floor(14 + k * 70 + 0.5))
	for i = 1, n do
		local l = lines[i]
		local a = rng:NextNumber() * math.pi * 2
		local r0 = R * (0.42 + rng:NextNumber() * 0.3 - k * 0.12)
		local len = R - r0
		local wdt = (0.9 + rng:NextNumber() * 3.2 * k) * s -- (a little wider than the web's: on the hub's light walls the web's widths barely read)
		local mid = r0 + len / 2
		l.Position = UDim2.fromOffset(cx + math.cos(a) * mid, cy + math.sin(a) * mid)
		l.Size = UDim2.fromOffset(len, wdt * 2)
		l.Rotation = math.deg(a)
		l.ImageTransparency = 1 - math.min(0.9, (0.25 + rng:NextNumber() * 0.5) * k) -- (the web's 0.12-0.52 vanished on light walls)
		l.ImageColor3 = if hot then HOT[rng:NextInteger(1, 2)] else WHITE
		if not l.Visible then l.Visible = true end
	end
	for i = n + 1, shown do lines[i].Visible = false end
	shown = n
end

RunService.RenderStepped:Connect(function(dt: number)
	local cam = workspace.CurrentCamera
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local alive = hum ~= nil and hum.Health > 0 and root ~= nil
	local busy = me:GetAttribute("LoadoutOpen") == true or me:GetAttribute("FinisherT") ~= nil
		or (Replay ~= nil and Replay.isPlaying ~= nil and Replay.isPlaying())
	local vel = if root then root.AssemblyLinearVelocity else Vector3.zero
	local test = if STUDIO then me:GetAttribute("SpeedLinesTest") else nil
	if type(test) == "number" and cam then vel = cam.CFrame.LookVector * test * STUD; alive = true end
	local speed = vel.Magnitude / STUD
	local on = alive and not busy and cam ~= nil

	-- the FOV kick (eased like the web's, 6 a second)
	local kickOn = setting("fov.kick")
	local hs = Vector2.new(vel.X, vel.Z).Magnitude / STUD
	local want = 0
	if on and kickOn then
		want = math.min(35, hs * 0.3) + (if me:GetAttribute("Sprinting") == true then 6 else 0)
			+ (if me:GetAttribute("OnRope") == true then 1.5 + math.min(2.5, hs * 0.08) else 0)
	end
	fovNow += (want - fovNow) * math.min(1, dt * 6)
	if math.abs(fovNow - want) < 0.01 then fovNow = want end
	local fa = me:GetAttribute("SpeedFov")
	local fr = math.floor(fovNow * 100 + 0.5) / 100
	if fa ~= fr and not (fr == 0 and fa == nil) then me:SetAttribute("SpeedFov", if fr == 0 then nil else fr) end

	-- the lines, the streaks and the wind
	local linesOn = on and setting("gfx.speedLines")
	local k = if linesOn then math.clamp((speed - 22) / 60, 0, 1) else 0
	local kw = if linesOn then math.clamp((speed - 15) / 60, 0, 1) else 0
	windVol += ((kw ^ 1.3) * 0.6 - windVol) * math.min(1, dt * 4)
	if windVol < 0.004 then
		if wind.Playing then wind:Stop() end
	else
		if not wind.Playing then wind:Play() end
		wind.Volume = windVol
		wind.PlaybackSpeed = 0.85 + 0.45 * kw
	end
	if k > 0.01 and cam then
		if streakPart.Parent ~= cam then streakPart.Parent = cam end
		local dir = if speed > 1 then vel.Unit else cam.CFrame.LookVector
		-- (the disc 14 studs ahead, square to the flight; they fly back along it, locked to it, so they pass at their own
		-- speed whatever yours is)
		local at = cam.CFrame.Position + dir * 14
		local right = dir:Cross(Vector3.yAxis)
		if right.Magnitude < 1e-3 then right = Vector3.xAxis else right = right.Unit end
		local back = right:Cross(dir)
		streakPart.CFrame = CFrame.fromMatrix(at, right, dir, back)
		streaks.Rate = 60 * k
		if not streaks.Enabled then streaks.Enabled = true end
	elseif streaks.Enabled then
		streaks.Enabled = false
	end
	acc += dt
	if acc < 1 / 30 then return end
	acc = 0
	if k <= 0.01 or not cam then hide(); return end
	local fx, fy = 0, 0
	if speed > 1 then
		local v = cam.CFrame:VectorToObjectSpace(vel.Unit)
		if v.Z < -0.2 then
			local f = 1 / math.tan(math.rad(cam.FieldOfView) / 2)
			local vp = cam.ViewportSize
			fx = math.clamp((v.X / -v.Z) * f / (vp.X / math.max(1, vp.Y)), -0.7, 0.7)
			fy = math.clamp((v.Y / -v.Z) * f, -0.7, 0.7)
		end
	end
	draw(k, fx, fy, speed > MACH)
end)
