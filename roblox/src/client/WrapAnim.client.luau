--!strict
-- WrapAnim: the animated wraps come alive on every gun this player can see (their own in hand, everyone else's, the
-- hub racks, the loadout previews). docs/WRAP-TEXTURES.md, "Animated wraps".
--
-- The web game animates 18 wraps in its shader (public/js/wrappack.js): scrolling patterns, pulses running along traces,
-- a glint sweeping over gold, hue that shifts with the angle, flicker. A Roblox SurfaceAppearance cannot scroll its
-- texture, and its maps can only be set in Edit, so stepping through pre-drawn frames would mean swapping whole
-- SurfaceAppearances at runtime: a texture reload each time, a hitch and a blink. What CAN change at runtime, cheaply,
-- is the glow (EmissiveStrength, EmissiveTint) and the tint (Color). So each animated wrap gets a slow, smooth change
-- of those, off one shared clock so every gun wearing it moves in step: a breathing glow, a pulse, a glint that swells
-- and fades, a drift between two colours, an iridescent tint. Nothing flickers (the owner: smooth and subtle).
--
-- WeaponModels.wrap tags each worn picture "WrapSA" and gives it the attribute Wrap = <wrap id>, on the server (world
-- guns) and the client (the held gun, previews) alike; this script finds them by the tag.
-- Cost: one Heartbeat step at 20 Hz. A wrap's value is worked out once a step and written to each of its pieces;
-- pieces further than NEAR studs from the camera are skipped (checked twice a second). The attribute StepUs on this
-- script is the slowest step of the last second, in microseconds.
local CS = game:GetService("CollectionService")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local TAU = math.pi * 2
local HZ = 20
local NEAR = 160

-- k: the kind of change, p: its period in seconds, lo/hi: the glow's range as a share of the wrap's own
-- EmissiveStrength, a/b: two glow colours to drift between, p2: the glow's own period when it differs, sat: saturation
type Spec = { k: string, p: number, lo: number?, hi: number?, a: Color3?, b: Color3?, p2: number?, sat: number? }
local SPEC: { [string]: Spec } = {
	hex = { k = "breathe", p = 2.6, lo = 0.7, hi = 1.25 },        -- web: light running along the grooves
	circuit = { k = "breathe", p = 2.0, lo = 0.6, hi = 1.3 },     -- web: pulses running along the traces
	kintsugi = { k = "glint", p = 4.5, lo = 0.5, hi = 1.6 },      -- web: a glint sweeping along the gold
	crt = { k = "breathe", p = 2.2, lo = 0.85, hi = 1.2 },        -- web: a bright bar rolling up the screen
	tokyo = { k = "breathe", p = 1.6, lo = 0.82, hi = 1.1 },      -- web: neon flicker (a hum here, never a flicker)
	stonks = { k = "breathe", p = 2.0, lo = 0.8, hi = 1.15 },     -- web: the chart scrolling
	vapor = { k = "breathe", p = 5.0, lo = 0.85, hi = 1.15 },     -- web: the grid scrolling
	corp = { k = "breathe", p = 2.1, lo = 0.7, hi = 1.1 },        -- web: the smileys pulsing
	blackhole = { k = "breathe", p = 4.0, lo = 0.8, hi = 1.2 },   -- web: the disk swirling
	lavalamp = { k = "breathe", p = 6.0, lo = 0.75, hi = 1.2 },   -- web: the blobs rising and merging
	glitch = { k = "drift", p = 5.0, lo = 0.85, hi = 1.1, a = Color3.fromHex("ff8ae8"), b = Color3.fromHex("8ae8ff") },
	aurora = { k = "drift", p = 9.0, p2 = 5.0, lo = 0.75, hi = 1.15, a = Color3.fromHex("b8ffd8"), b = Color3.fromHex("e2c4ff") },
	nebula = { k = "drift", p = 10.0, p2 = 7.0, lo = 0.85, hi = 1.1, a = Color3.fromHex("ffd2f0"), b = Color3.fromHex("cadaff") },
	opal = { k = "hue", p = 12.0, sat = 0.5 },                     -- web: the fire shifting as it turns
	holo = { k = "iris", p = 8.0, sat = 0.12 },                    -- web: the hue sweeping with the angle
}
script:SetAttribute("Animated", (function() local n = 0; for _ in SPEC do n += 1 end; return n end)())

type Entry = { spec: Spec, es: number, tint: Color3, col: Color3, near: boolean }
local live: { [SurfaceAppearance]: Entry } = {}

local function add(inst: Instance)
	if not inst:IsA("SurfaceAppearance") or inst:IsDescendantOf(ReplicatedStorage) then return end
	local id = inst:GetAttribute("Wrap")
	local spec = if type(id) == "string" then SPEC[id] else nil
	if not spec then return end
	live[inst] = { spec = spec, es = inst.EmissiveStrength, tint = inst.EmissiveTint, col = inst.Color, near = true }
end
for _, sa in CS:GetTagged("WrapSA") do add(sa) end
CS:GetInstanceAddedSignal("WrapSA"):Connect(add)
CS:GetInstanceRemovedSignal("WrapSA"):Connect(function(inst) live[inst :: any] = nil end)

local function wave(t: number, p: number): number return 0.5 + 0.5 * math.sin(TAU * t / p) end
local function smooth(x: number): number return x * x * (3 - 2 * x) end

-- one wrap's look at time t: a glow factor, and (when the kind sets them) a glow colour and a tint
type Look = { f: number?, tint: Color3?, col: Color3? }
local function look(s: Spec, t: number): Look
	local lo, hi = s.lo or 1, s.hi or 1
	if s.k == "breathe" then return { f = lo + (hi - lo) * wave(t, s.p) } end
	if s.k == "glint" then return { f = lo + (hi - lo) * wave(t, s.p) ^ 6 } end
	if s.k == "drift" then
		return { f = lo + (hi - lo) * wave(t, s.p2 or s.p), tint = (s.a :: Color3):Lerp(s.b :: Color3, smooth(wave(t, s.p))) }
	end
	if s.k == "hue" then return { tint = Color3.fromHSV((t / s.p) % 1, s.sat or 0.5, 1) } end
	if s.k == "iris" then
		local h = (t / s.p) % 1
		return { col = Color3.fromHSV(h, s.sat or 0.12, 1), tint = Color3.fromHSV((h + 0.5) % 1, 0.4, 1) }
	end
	return {}
end

local acc, nearAcc, worst, worstAcc = 0, 0, 0, 0
RunService.Heartbeat:Connect(function(dt: number)
	acc += dt; nearAcc += dt; worstAcc += dt
	if acc < 1 / HZ then return end
	acc = 0
	local t0 = os.clock()
	local cam = workspace.CurrentCamera
	if nearAcc >= 0.5 and cam then
		nearAcc = 0
		local at = cam.CFrame.Position
		for sa, e in live do
			local p = sa.Parent
			e.near = not (p and p:IsA("BasePart") and p:IsDescendantOf(workspace)) or (p.Position - at).Magnitude < NEAR
		end
	end
	local t = workspace:GetServerTimeNow() -- (one clock for everyone: the same wrap pulses in step on every screen)
	local cache: { [Spec]: Look } = {}
	for sa, e in live do
		if not sa.Parent then live[sa] = nil; continue end
		if not e.near then continue end
		local l = cache[e.spec]
		if not l then l = look(e.spec, t); cache[e.spec] = l end
		if l.f then sa.EmissiveStrength = e.es * l.f end
		if l.tint then sa.EmissiveTint = l.tint end
		if l.col then sa.Color = l.col end
	end
	local us = (os.clock() - t0) * 1e6
	if us > worst then worst = us end
	if worstAcc >= 1 then
		script:SetAttribute("StepUs", math.floor(worst + 0.5))
		script:SetAttribute("Live", (function() local n = 0; for _ in live do n += 1 end; return n end)())
		worst, worstAcc = 0, 0
	end
end)
