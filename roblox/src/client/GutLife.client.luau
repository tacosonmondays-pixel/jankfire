--!strict
-- THE GUT arena's life, on your own screen (17 Nov 2026; the arena: tools/roblox/gut_models.py, built by
-- ServerStorage.PolishBackup.WebArena as workspace.Map.Gut, copies in Map.ArenaCopies). Two things:
--   the heart on the tower beats (a swell and a flare of its light on the lub, a smaller one on the dub) and turns
--   slowly, on one clock every screen shares (the server's time), so everyone sees the same beat;
--   now and then the train passes through the subway behind the platform's glass. The server picks when (GutTrain sets
--   the arena's TrainAt, the server time the train's face reaches the station, and TrainDir, 1 from the west, -1 from
--   the east). For WARN seconds before, the signals at both tunnel mouths and the lamps along the glass flash red, the
--   station's lights flicker and a rumble grows; then the face (the enamel mask) and its wagons rush through and away.
-- Nothing here touches play: the heart and the train never collide or take shots, and the train runs on its own track
-- behind a full-height glass screen. Arenas out of your world (ZoneCull) or far away are left alone.
-- Sounds: the arena's attributes TrainSound and RumbleSound (rbxassetid strings, recordings), set when it is built.
local RunService = game:GetService("RunService")

local BEAT_RATE = 0.72        -- beats a second (the web Gut's own clock)
local TURN_SECS = 48          -- one slow turn of the heart
local SWELL = 0.06            -- how much bigger it gets on the lub
local WARN = 6.0              -- seconds of warning before the face reaches the station
local SPEED = 120             -- studs a second
local PARK_FACE = -470        -- where the face waits, deep in the west tunnel (arena-local x)
local STATION_END = -100      -- the platform's west end
local RUN_TO = 560            -- the face runs on to here, deep in the far tunnel
local TRACK_Z = 58            -- the track's middle (arena-local z)
local NEAR = 1600             -- studs from the camera: nearer than this the arena lives
local HEART_Y = 134           -- the heart's middle above the street (gut_heart_dims.HEART_Y)

type Arena = {
	root: Model, origin: CFrame,
	heart: Model?, heartBase: CFrame?, heartLight: PointLight?, glows: { { part: BasePart, base: Color3 } },
	flush: { { part: BasePart, h: number, s: number, v: number } }, scale: number,
	train: Model?, sig: { BasePart }, lamps: { { light: PointLight, base: number } },
	ran: number,               -- the TrainAt last run (so each run plays once)
}
local arenas: { [Model]: Arena } = {}

local function isGut(m: Instance): boolean
	return m:IsA("Model") and m:GetAttribute("MapId") == "gut"
end

local function setup(root: Model): Arena
	local O = CFrame.new(root:GetPivot().Position)
	local a: Arena = { root = root, origin = O, glows = {}, flush = {}, scale = 1, sig = {}, lamps = {}, ran = -1 }
	local shell = root:FindFirstChild("Shell")
	if shell then
		for _, code in { "A", "B", "C", "V" } do -- (A B C the anatomical hearts, V the first candy one: the build keeps one)
			local h = shell:FindFirstChild("gu_heart" .. code)
			if h and h:IsA("Model") and not a.heart then
				a.heart = h
				local py = root:GetAttribute("HeartPivotY")      -- (the big anatomical heart rests on its apex: it swells and turns round that)
				local c = O * CFrame.new(0, if type(py) == "number" then py else HEART_Y, 0)
				h.WorldPivot = c                 -- (turn and swell round this point)
				a.heartBase = c
				for _, p in h:GetDescendants() do
					if p:IsA("BasePart") then
						if p.Material == Enum.Material.Neon then table.insert(a.glows, { part = p, base = p.Color })
						else local hh, ss, vv = p.Color:ToHSV(); table.insert(a.flush, { part = p, h = hh, s = ss, v = vv }) end
					end
				end
				local first = h:FindFirstChildWhichIsA("BasePart", true)
				if first then
					local at = Instance.new("Attachment")
					at.Name = "HeartGlow"
					at.WorldCFrame = c
					at.Parent = first
					local l = Instance.new("PointLight")
					l.Color = Color3.fromRGB(255, 118, 138); l.Range = 52; l.Brightness = 1.2; l.Shadows = false
					l.Parent = at
					a.heartLight = l
				end
			end
		end
		local t = shell:FindFirstChild("gu_trn")
		if t and t:IsA("Model") then a.train = t end
		local s = shell:FindFirstChild("gu_sig")
		if s then for _, p in s:GetDescendants() do if p:IsA("BasePart") then table.insert(a.sig, p) end end end
	end
	local lights = root:FindFirstChild("Lights")
	if lights then
		for _, mk in lights:GetChildren() do
			if mk:IsA("BasePart") and mk.Position.Y < O.Position.Y - 8 then
				local l = mk:FindFirstChildWhichIsA("PointLight")
				if l then table.insert(a.lamps, { light = l, base = l.Brightness }) end
			end
		end
	end
	return a
end

local function scan()
	local map = workspace:FindFirstChild("Map")
	if not map then return end
	local seen: { [Model]: boolean } = {}
	local function look(parent: Instance?)
		if not parent then return end
		for _, m in parent:GetChildren() do
			if isGut(m) then
				seen[m :: Model] = true
				if not arenas[m :: Model] then arenas[m :: Model] = setup(m :: Model) end
			end
		end
	end
	look(map); look(map:FindFirstChild("ArenaCopies"))
	for m in arenas do if not seen[m] then arenas[m] = nil end end
end

-- one beat (0..1 of it): the lub at 0.06 (up fast, down over about a quarter second), the dub at 0.27, 60% of it
local function beat(ph: number): number
	local lub = if ph < 0.06 then (ph / 0.06) ^ 2 else math.exp(-(ph - 0.06) / 0.11)
	local dub = 0
	if ph >= 0.21 and ph < 0.27 then dub = 0.6 * ((ph - 0.21) / 0.06) ^ 2 elseif ph >= 0.27 then dub = 0.6 * math.exp(-(ph - 0.27) / 0.11) end
	return math.max(lub, dub)
end

local WHITE = Color3.new(1, 1, 1)
local RED, AMBER = Color3.fromRGB(255, 52, 60), Color3.fromRGB(255, 176, 70)

local function heartStep(a: Arena, now: number)
	local h, base = a.heart, a.heartBase
	if not h or not base then return end
	local ph = (now * BEAT_RATE) % 1
	local g = beat(ph)
	local ang = (now / TURN_SECS) % 1 * 2 * math.pi
	h:PivotTo(base * CFrame.Angles(0, ang, 0))
	local s = 1 + SWELL * g
	if math.abs(s - a.scale) > 0.002 then
		a.scale = s
		pcall(function() h:ScaleTo(s) end)
	end
	if a.heartLight then a.heartLight.Brightness = 1.2 + 4.0 * g end
	for _, gl in a.glows do
		local c = gl.base:Lerp(WHITE, 0.45 * g)
		if gl.part.Color ~= c then gl.part.Color = c end
	end
	-- the muscle and vessels flush a little brighter on each beat
	for _, f in a.flush do
		local c = Color3.fromHSV(f.h, f.s * (1 - 0.08 * g), math.min(1, f.v * (1 + 0.2 * g)))
		if f.part.Color ~= c then f.part.Color = c end
	end
end

-- the train's place along its run (arena-local CFrame for its model, which waits at the identity)
local function trainAt(dir: number, faceX: number): CFrame
	local dx = faceX - PARK_FACE
	if dir >= 0 then return CFrame.new(dx, 0, 0) end
	-- from the east: the parked train turned half round about the track's line, then run the other way
	return CFrame.new(-dx, 0, 0) * CFrame.new(0, 0, TRACK_Z) * CFrame.Angles(0, math.pi, 0) * CFrame.new(0, 0, -TRACK_Z)
end

local function sound(parent: Instance, id: any, vol: number, looped: boolean): Sound?
	if type(id) ~= "string" or id == "" then return nil end
	local s = Instance.new("Sound")
	s.SoundId = id; s.Volume = vol; s.Looped = looped
	s.RollOffMode = Enum.RollOffMode.InverseTapered; s.RollOffMinDistance = 30; s.RollOffMaxDistance = 420
	s.Parent = parent
	return s
end

local function runTrain(a: Arena, at: number, dir: number)
	local train, root, O = a.train, a.root, a.origin
	if not train then return end
	local start = at - WARN
	local tStart = at - (STATION_END - PARK_FACE) / SPEED          -- (when it must set off to reach the station at `at`)
	local tEnd = at + (RUN_TO - STATION_END) / SPEED
	-- the rumble: from the tunnel mouth it comes out of, growing
	local mouth = Instance.new("Part")
	mouth.Name = "GutRumble"; mouth.Anchored = true; mouth.CanCollide = false; mouth.CanQuery = false; mouth.CanTouch = false
	mouth.Transparency = 1; mouth.Size = Vector3.new(1, 1, 1)
	mouth.CFrame = O * CFrame.new(if dir >= 0 then -104 else 104, -24, TRACK_Z)
	mouth.Parent = workspace
	local rumble = sound(mouth, root:GetAttribute("RumbleSound"), 0, true)
	if rumble then rumble:Play() end
	-- the train's own light and sound, on its face
	local face = train:FindFirstChildWhichIsA("BasePart", true)
	local spot, pass
	if face then
		local att = Instance.new("Attachment")
		att.Name = "TrainFace"
		local p = (O * CFrame.new(PARK_FACE + 1.5, -24, TRACK_Z)).Position      -- (the train waits parked here, facing +x)
		att.WorldCFrame = CFrame.lookAt(p, p + O.XVector)
		att.Parent = face
		spot = Instance.new("SpotLight")
		spot.Color = Color3.fromRGB(255, 236, 214); spot.Brightness = 3; spot.Range = 60; spot.Angle = 70; spot.Shadows = false
		spot.Face = Enum.NormalId.Front
		spot.Parent = att
		pass = sound(att, root:GetAttribute("TrainSound"), 0.9, false)
	end
	local played = false
	local con: RBXScriptConnection
	con = RunService.RenderStepped:Connect(function()
		local now = workspace:GetServerTimeNow()
		if not root.Parent or now > tEnd + 0.5 then
			con:Disconnect()
			train:PivotTo(O)
			for _, p in a.sig do p.Material = Enum.Material.SmoothPlastic; p.Color = Color3.fromHex("4a3038") end
			for _, l in a.lamps do l.light.Brightness = l.base end
			if spot and spot.Parent then spot.Parent:Destroy() end
			mouth:Destroy()
			return
		end
		-- the warning: the signals flash red (amber on the glass), the lights flicker more as it nears, the rumble grows
		local k = math.clamp((now - start) / WARN, 0, 1)
		local on = (now * 2.5) % 1 < 0.55 and now < at + 2.5
		for i, p in a.sig do
			p.Material = if on then Enum.Material.Neon else Enum.Material.SmoothPlastic
			p.Color = if on then (if i % 2 == 0 then RED else AMBER) else Color3.fromHex("4a3038")
		end
		local flick = if now < at + 2.5 then k * k else 0
		for _, l in a.lamps do l.light.Brightness = l.base * (1 - 0.55 * flick * math.random()) end
		if rumble then rumble.Volume = 0.9 * k * (if now > at + 2.5 then math.clamp(1 - (now - at - 2.5) / 3, 0, 1) else 1) end
		-- the run
		local faceX = if now < tStart then PARK_FACE else math.min(RUN_TO, STATION_END + (now - at) * SPEED)
		train:PivotTo(O * trainAt(dir, faceX))
		if pass and not played and now >= at - 1.2 then played = true; pass:Play() end
	end)
end

local look = 0
RunService.RenderStepped:Connect(function(dt)
	look += dt
	if look > 2 then look = 0; scan() end
	local cam = workspace.CurrentCamera
	if not cam then return end
	local eye = cam.CFrame.Position
	local now = workspace:GetServerTimeNow()
	for _, a in arenas do
		if not a.root.Parent then continue end
		if (a.origin.Position - eye).Magnitude > NEAR then continue end
		heartStep(a, now)
		local at = a.root:GetAttribute("TrainAt")
		if type(at) == "number" and at ~= a.ran and now >= at - WARN and now < at + 4 then
			a.ran = at
			local dir = a.root:GetAttribute("TrainDir")
			runTrain(a, at, if type(dir) == "number" then dir else 1)
		end
	end
end)
scan()
