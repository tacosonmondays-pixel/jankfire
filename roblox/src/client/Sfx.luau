--!strict
-- the sounds: every one is a Sound in ReplicatedStorage.JankfireSounds, played by name. since 16 Nov 2026 they are
-- recordings: Pro Sound Effects (Roblox's licensed library) and Freesound CC0 cuts (roblox/assets/sounds/store.json;
-- the list, levels and history in roblox/docs/SOUNDS.md). special skins add their own layers (shared/SkinSounds,
-- below). a Sound with an empty SoundId stays silent, never an error
-- takes: Sounds named "<name>#2", "<name>#3"... beside "<name>" are other takes of the same sound. play() picks one at
-- random (never the same one twice running), so a burst of fire or a run of footsteps doesn't sound copied
-- a Sound's attributes: Jitter = its pitch is nudged at random by up to that much (0.03 = 3%); RollMin / RollMax = how
-- far a copy out in the world carries (else the ROLL table below)
-- out in the world (17 Nov 2026, the owner: "gun fire audio should be proportional to where players are"): a copy with a
-- position is a 3D sound there, InverseTapered between RollOffMin and Max (full inside Min, silent past Max), and it
-- dips duller and quieter when a wall stands between it and you (one ray). gunshots (gun_*) and blasts (LOUD) are heard
-- like real ones: a close take that crossfades, from NEAR_END to FAR_FULL studs, into a far take (thin and dull,
-- FAR_EQ), arriving late by the distance over the speed of sound. recorded distance takes slot in by name:
-- "<sound>@<studs>" beside "<sound>" (gun_ar@179 = recorded 50 m off; 1 m = 3.57 studs) replace the made-up far take,
-- and a shot crossfades between the two recordings either side of its distance. your own shots stay close and on you
-- (no position), as before. other sounds out in the world keep the air's top-end loss from 40 studs
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")
local Players = game:GetService("Players")

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
-- recorded distance takes: layers.gun_ar = { { 179, "gun_ar@179" }, ... }, nearest first
local layers: { [string]: { { any } } } = {}

local function index()
	table.clear(takes)
	table.clear(layers)
	if not lib then return end
	for _, s in ipairs(lib:GetChildren()) do
		if s:IsA("Sound") and s.SoundId ~= "" then
			local base = string.match(s.Name, "^(.-)#%d+$") or s.Name
			local t = takes[base]
			if not t then t = {}; takes[base] = t end
			table.insert(t, s)
		end
	end
	for base, t in takes do
		table.sort(t, function(a, b) return a.Name < b.Name end)
		local snd, d = string.match(base, "^(.-)@(%d+)$")
		if snd and d then
			local L = layers[snd]
			if not L then L = {}; layers[snd] = L end
			table.insert(L, { tonumber(d) :: number, base })
		end
	end
	for _, L in layers do table.sort(L, function(a, b) return a[1] < b[1] end) end
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

-- ---------------------------------------------------------------- out in the world
-- how far a copy carries, { RollOffMinDistance, RollOffMaxDistance } in studs: by name, else by prefix, else the default
-- (a Sound's RollMin / RollMax attributes win). gunfire: full inside 12 studs, about -12 dB at 40, -22 dB at 120, a
-- faint crack (-30 dB) across a map at 300, gone past 520. a reload's clicks only carry a few strides
local ROLL_EXACT: { [string]: { number } } = {
	boom = { 24, 1100 }, blow = { 16, 650 }, hole = { 18, 750 }, bigpop = { 12, 420 }, -- (blasts)
	swing = { 6, 170 }, ting = { 6, 170 }, bonk = { 6, 170 }, tink = { 6, 150 }, thwack = { 6, 170 }, -- (melee)
	click = { 4, 80 }, reload = { 4, 90 }, empty = { 4, 60 }, -- (gun handling: someone else's reload)
}
local ROLL_PREFIX: { { any } } = { { "gun_", 12, 520 }, { "skin_", 8, 220 } }
local ROLL_DEFAULT = { 15, 600 }
local LOUD: { [string]: boolean } = { boom = true, blow = true, hole = true } -- (blasts: heard like gunfire)
local NEAR_END, FAR_FULL = 60, 90 -- (studs: the close take hands over to the far take between these, equal-power)
local FAR_EQ = { -8, 0, -20 } -- (the made-up far take: LowGain, MidGain, HighGain dB: thin and dull)
local FAR_GAIN = 0.9
local OCC_EQ, OCC_GAIN = { 0, -5, -12 }, 0.6 -- (through a wall: duller and quieter)
local STUDS_PER_S, MAX_LATE = 1225, 0.4 -- (the speed of sound, 343 m/s at 0.28 m a stud; the most a shot arrives late)

local function roll(name: string, s: Sound): (number, number)
	local r = ROLL_EXACT[name]
	if not r then
		for _, p in ROLL_PREFIX do
			if string.sub(name, 1, #p[1]) == p[1] then r = { p[2], p[3] }; break end
		end
	end
	local rr = r or ROLL_DEFAULT
	return num(s, "RollMin", rr[1]), num(s, "RollMax", rr[2])
end

-- InverseTapered as the engine has it: inverse near Min, linear-squared near Max, whichever is quieter (0..1)
function Sfx.atten(d: number, mn: number, mx: number): number
	if d <= mn then return 1 end
	if d >= mx then return 0 end
	return math.min(mn / d, ((mx - d) / (mx - mn)) ^ 2)
end

local wallRay = RaycastParams.new()
wallRay.FilterType = Enum.RaycastFilterType.Exclude
wallRay.RespectCanCollide = true
-- is something solid between your ears (the camera) and `to`? (players' bodies don't count)
local function walled(from: Vector3, to: Vector3): boolean
	local v = to - from
	if v.Magnitude < 3 then return false end
	local skip: { Instance } = { holder }
	for _, p in Players:GetPlayers() do if p.Character then table.insert(skip, p.Character) end end
	wallRay.FilterDescendantsInstances = skip
	local hit = workspace:Raycast(from, v, wallRay)
	return hit ~= nil and (hit.Position - to).Magnitude > 2
end

local function addEq(a: { number }?, b: { number }?): { number }?
	if not a then return b end
	if not b then return a end
	return { a[1] + b[1], a[2] + b[2], a[3] + b[3] }
end

-- one copy of s out in the world at `at`: k = the pitch factor; eq = { low, mid, high } dB; info = attributes on the
-- copy (Dist, Walled, Late, Layer: what a test reads back), plus Atten, the engine's distance gain
local function emit(s: Sound, name: string, at: Vector3, gain: number, k: number, eq: { number }?, info: { [string]: any }): Sound
	local c = s:Clone()
	c.Volume = s.Volume * gain
	c.PlaybackSpeed = s.PlaybackSpeed * k
	c.RollOffMode = Enum.RollOffMode.InverseTapered
	local mn, mx = roll(name, s)
	c.RollOffMinDistance, c.RollOffMaxDistance = mn, mx
	if eq and (eq[1] ~= 0 or eq[2] ~= 0 or eq[3] ~= 0) then
		local e = Instance.new("EqualizerSoundEffect")
		e.LowGain, e.MidGain, e.HighGain = eq[1], eq[2], eq[3]
		e.Parent = c
	end
	for key, v in info do c:SetAttribute(key, v) end
	c:SetAttribute("Atten", math.floor(Sfx.atten(info.Dist or 0, mn, mx) * 1000 + 0.5) / 1000)
	local a = Instance.new("Attachment")
	a.WorldPosition = at
	a.Parent = workspace.Terrain
	c.Parent = a
	c.Ended:Once(function() a:Destroy() end)
	c:Play()
	task.delay(8, function() if a.Parent then a:Destroy() end end)
	return c
end

-- a gunshot or a blast out in the world: the close and far takes by distance, late by the distance, dipped by a wall
local function heard(name: string, s: Sound, at: Vector3, gain: number, k: number)
	local cam = workspace.CurrentCamera
	local ear = if cam then cam.CFrame.Position else at
	local d = (ear - at).Magnitude
	local occ = cam ~= nil and walled(ear, at)
	local g = gain * (if occ then OCC_GAIN else 1)
	local wall = if occ then OCC_EQ else nil
	local late = math.min(d / STUDS_PER_S, MAX_LATE)
	local function info(layer: string): { [string]: any }
		return { Dist = math.floor(d + 0.5), Walled = occ, Late = math.floor(late * 1000 + 0.5) / 1000, Layer = layer }
	end
	local function go()
		local L = layers[name]
		if L then
			-- recorded distance takes: the two either side of d (the plain recording counts as 0 studs)
			local lo, hi = { 0, name }, nil
			for _, ly in L do
				if ly[1] <= d then lo = ly else hi = ly; break end
			end
			local t = if hi then math.clamp((d - lo[1]) / (hi[1] - lo[1]), 0, 1) else 0
			local a = if lo[2] == name then s else src(lo[2])
			if a and t < 0.99 then emit(a, name, at, g * math.cos(t * math.pi / 2), k, wall, info(lo[2])) end
			local b = hi and src(hi[2])
			if b and hi and t > 0.01 then emit(b, name, at, g * math.sin(t * math.pi / 2), k, wall, info(hi[2])) end
		else
			local t = math.clamp((d - NEAR_END) / (FAR_FULL - NEAR_END), 0, 1)
			if t < 0.99 then emit(s, name, at, g * math.cos(t * math.pi / 2), k, wall, info("near")) end
			if t > 0.01 then emit(s, name, at, g * math.sin(t * math.pi / 2) * FAR_GAIN, k, addEq(FAR_EQ, wall), info("far")) end
		end
	end
	if late > 0.02 then task.delay(late, go) else go() end
end

-- play a sound: on you (no position) or out in the world at `at`. returns the playing copy (to duck or stop it), or nil
-- (a gunshot or blast out in the world may still be on its way: nil)
function Sfx.play(name: string, at: Vector3?, vol: number?, pitch: number?): Sound?
	if Sfx.mute[name] then return nil end
	local s = src(name)
	if not s then return nil end
	local j = num(s, "Jitter", 0)
	local k = (pitch or 1) * (if j > 0 then 1 + (rng:NextNumber() * 2 - 1) * j else 1)
	if at then
		if string.sub(name, 1, 4) == "gun_" or LOUD[name] then
			heard(name, s, at, vol or 1, k)
			return nil
		end
		-- anything else: where it is, the air taking the top off from 40 studs (-14 dB above 4 kHz and -4 dB in the mids
		-- at 300), a wall's dip on top
		local cam = workspace.CurrentCamera
		local ear = if cam then cam.CFrame.Position else at
		local d = (ear - at).Magnitude
		local occ = cam ~= nil and walled(ear, at)
		local air = if d > 40 then { 0, -4 * math.clamp((d - 40) / 260, 0, 1), -14 * math.clamp((d - 40) / 260, 0, 1) } else nil
		return emit(s, name, at, (vol or 1) * (if occ then OCC_GAIN else 1), k, addEq(air, if occ then OCC_EQ else nil),
			{ Dist = math.floor(d + 0.5), Walled = occ })
	end
	local c = s:Clone()
	c.Volume = s.Volume * (vol or 1)
	c.PlaybackSpeed = s.PlaybackSpeed * k
	c.Parent = SoundService -- (a Sound in SoundService plays for you alone, not in the world)
	c.Ended:Once(function() c:Destroy() end)
	c:Play()
	task.delay(6, function() if c.Parent then c:Destroy() end end)
	return c
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
	if type(w.id) == "string" then Sfx.skinFire(w.id, at) end
end

-- ---------------------------------------------------------------- the special skins' own layers (shared/SkinSounds)
-- a high-tier skin adds a short themed recording on top of the base gun's sound (17 Nov 2026): on each shot, on its
-- reload / cycle clip events and on a melee hit. yours from your own "Skins"; someone else's shot from the player
-- standing at its muzzle
local me = Players.LocalPlayer
local SkinSounds: any, GunSkins: any = nil, nil
task.spawn(function()
	local folder = ReplicatedStorage:WaitForChild("Jankfire", 10)
	local a = folder and folder:WaitForChild("SkinSounds", 10)
	local b = folder and folder:WaitForChild("GunSkins", 10)
	if a then local ok, m = pcall(require, a); if ok then SkinSounds = m end end
	if b then local ok, m = pcall(require, b); if ok then GunSkins = m end end
end)
local shotN: { [string]: number } = {}

local function layersFor(p: Player?, wid: string): (string?, any)
	if not (SkinSounds and GunSkins and p) then return nil, nil end
	local id = GunSkins.skinFor(p, wid)
	return id, if id then SkinSounds.skin[id] else nil
end

local function shooterAt(at: Vector3): Player?
	local best, bd = nil, 8
	for _, p in ipairs(Players:GetPlayers()) do
		local ch = p.Character
		local r = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if p ~= me and r then
			local d = (r.Position - at).Magnitude
			if d < bd then best, bd = p, d end
		end
	end
	return best
end

-- a shot's layer: at = nil for yours, else the muzzle out in the world
function Sfx.skinFire(wid: string, at: Vector3?)
	local p = if at then shooterAt(at) else me
	local id, L = layersFor(p, wid)
	if not (id and L) then return end
	local key = id .. (if p then tostring(p.UserId) else "")
	local n = (shotN[key] or 0) + 1
	shotN[key] = n
	if L.fire and (not L.chance or rng:NextNumber() < L.chance) then Sfx.play(L.fire, at) end
	if L.alt and n % L.alt.every == 0 then Sfx.play(L.alt.name, at) end
end

-- your weapon's clip event (Reloads.luau: magIn, spinCyl, leverClack, shell, whoosh...)
function Sfx.skinEvent(wid: string, ev: string)
	local _, L = layersFor(me, wid)
	local name = L and L.ev and L.ev[ev]
	if name then Sfx.play(name) end
end

-- your melee hit landed
function Sfx.skinHit(wid: string)
	local _, L = layersFor(me, wid)
	if L and L.hit then Sfx.play(L.hit) end
end

-- a skinned gadget's layer (SkinSounds .item): p = the gadget's owner, gid = the gadget (frag, smoke, duck, medkit),
-- ev = throw / blast / cloud / land / open; at = out in the world, nil = on you. nothing for an unskinned gadget
function Sfx.skinItem(p: Player?, gid: string, ev: string, at: Vector3?)
	local _, L = layersFor(p, gid)
	local name = L and L.item and L.item[ev]
	if name then Sfx.play(name, at) end
end

local _ = holder
return Sfx
