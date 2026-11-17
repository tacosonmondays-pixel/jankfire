--!strict
-- the sounds: every one is a Sound in ReplicatedStorage.JankfireSounds, played by name. since 16 Nov 2026 they are
-- layered synth renders (tools/roblox/render_sfx.mjs; the list, levels and before/after in roblox/docs/SOUNDS.md);
-- before that they were the web game's one-oscillator recipes. a Sound with an empty SoundId stays silent, never an error
-- takes: Sounds named "<name>#2", "<name>#3"... beside "<name>" are other takes of the same sound. play() picks one at
-- random (never the same one twice running), so a burst of fire or a run of footsteps doesn't sound copied
-- a Sound's attributes: Jitter = its pitch is nudged at random by up to that much (0.03 = 3%); RollMin / RollMax = how
-- far a copy out in the world carries (default 15 / 600 studs). out in the world, the further away, the less top end
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")

local Sfx = {}
Sfx.mute = {} :: { [string]: boolean } -- (names that stay quiet: Settings > AUDIO, HIT SOUND / KILL SOUND off)
local lib = ReplicatedStorage:WaitForChild("JankfireSounds", 5)
local holder = Instance.new("Part")
holder.Name = "JankfireSfx"; holder.Anchored = true; holder.CanCollide = false; holder.CanQuery = false; holder.CanTouch = false
holder.Transparency = 1; holder.Size = Vector3.new(0.1, 0.1, 0.1)
holder.Parent = workspace

local rng = Random.new()
local takes: { [string]: { Sound } } = {}
local lastTake: { [string]: number } = {}

local function index()
	table.clear(takes)
	if not lib then return end
	for _, s in ipairs(lib:GetChildren()) do
		if s:IsA("Sound") and s.SoundId ~= "" then
			local base = string.match(s.Name, "^(.-)#%d+$") or s.Name
			local t = takes[base]
			if not t then t = {}; takes[base] = t end
			table.insert(t, s)
		end
	end
	for _, t in takes do table.sort(t, function(a, b) return a.Name < b.Name end) end
end
index()
if lib then
	local queued = false
	local function soon()
		if queued then return end
		queued = true
		task.defer(function() queued = false; index() end)
	end
	lib.ChildAdded:Connect(soon); lib.ChildRemoved:Connect(soon)
end

local function src(name: string): Sound?
	local t = takes[name]
	if not t or #t == 0 then return nil end
	if #t == 1 then return t[1] end
	local i = rng:NextInteger(1, #t)
	if i == lastTake[name] then i = i % #t + 1 end
	lastTake[name] = i
	return t[i]
end

local function num(s: Sound, key: string, default: number): number
	local v = s:GetAttribute(key)
	return if type(v) == "number" then v else default
end

-- play a sound: on you (no position) or out in the world at `at`
function Sfx.play(name: string, at: Vector3?, vol: number?, pitch: number?)
	if Sfx.mute[name] then return end
	local s = src(name)
	if not s then return end
	local c = s:Clone()
	c.Volume = s.Volume * (vol or 1)
	local j = num(s, "Jitter", 0)
	c.PlaybackSpeed = s.PlaybackSpeed * (pitch or 1) * (if j > 0 then 1 + (rng:NextNumber() * 2 - 1) * j else 1)
	if at then
		local a = Instance.new("Attachment")
		a.WorldPosition = at
		a.Parent = workspace.Terrain
		c.RollOffMinDistance = num(s, "RollMin", 15); c.RollOffMaxDistance = num(s, "RollMax", 600)
		-- the air takes the top off a far sound: from 40 studs, down to -14 dB above 4 kHz (and -4 dB in the mids) at 300
		local cam = workspace.CurrentCamera
		local d = if cam then (cam.CFrame.Position - at).Magnitude else 0
		if d > 40 then
			local k = math.clamp((d - 40) / 260, 0, 1)
			local eq = Instance.new("EqualizerSoundEffect")
			eq.LowGain = 0; eq.MidGain = -4 * k; eq.HighGain = -14 * k
			eq.Parent = c
		end
		c.Parent = a
		c.Ended:Once(function() a:Destroy() end)
		c:Play()
		task.delay(6, function() if a.Parent then a:Destroy() end end)
	else
		c.Parent = SoundService -- (a Sound in SoundService plays for you alone, not in the world)
		c.Ended:Once(function() c:Destroy() end)
		c:Play()
		task.delay(6, function() if c.Parent then c:Destroy() end end)
	end
end

-- the Redline gets brighter, higher and shorter as k (0 full HP -> 1 at 0 HP) rises: three renders + a pitch nudge
function Sfx.redline(k: number, at: Vector3?)
	local name = if k < 0.33 then "gun_redline_k0" elseif k < 0.75 then "gun_redline_k5" else "gun_redline_k10"
	Sfx.play(name, at, 1, 1 + (k % 0.4) * 0.1)
end

-- a gun's shot, from its row in Weapons: the Redline's renders by HP (tacho), or its own sound (snd). k = the
-- Redline's needle (0..1), at = out in the world (someone else's gun) or nil for yours
-- heat = the Belt Sander's barrel (0..1): louder and lower the hotter it is
function Sfx.gun(w: any, k: number, at: Vector3?, heat: number?)
	if w.tacho then Sfx.redline(k, at)
	elseif type(w.snd) == "string" then
		local h = if w.heatUp and heat then heat else 0
		Sfx.play(w.snd, at, 1 + 0.4 * h, 1 - 0.15 * h)
	end
end

local _ = holder
return Sfx
