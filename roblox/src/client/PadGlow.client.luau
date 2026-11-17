--!strict
-- the hub's queue pads, lit on your own screen (owner, 17 Nov: "can we try removing the circles on the pads and then
-- make them glow?", then "pads should glow when you step on them!"). each side of a pad has a Glow (HubRotunda's B.pad:
-- a thin neon face in its team's colour over the plate, a soft PointLight in it, attribute Team). while the side is
-- open it breathes, quietly; the moment someone steps on it, it flares (a quick flash toward white and a burst of
-- light) and then holds clearly bright while they stay. Matches lights that side's Slot markers while it is taken
-- (specks buried in the plate: their Transparency, 0 while the place is taken, is the only thing read here). nothing
-- here changes what the pads do, only how they look. pads out of your world (ZoneCull) or far from the camera are
-- left alone
local RunService = game:GetService("RunService")

local OPEN, BREATH, TAKEN = 0.78, 0.04, 0.03 -- (the Glow's see-through: open, how far it breathes, taken)
local LIGHT_OPEN, LIGHT_TAKEN, LIGHT_FLARE = 0.12, 1.6, 4.5 -- (its light's brightness: open, taken, at the flare's peak)
local RANGE, RANGE_FLARE = 7, 13 -- (its light's reach, and at the flare's peak)
local FLARE = 0.5 -- (seconds the flare takes to settle)
local PERIOD = 3.4 -- (seconds a breath)
local FAR = 160 -- (studs from the camera)

type Side = { pad: Model, glow: BasePart, light: PointLight?, team: number, slots: { BasePart }, k: number, phase: number, base: Color3, taken: boolean, flareAt: number }
local sides: { Side } = {}
local known: { [BasePart]: Side } = {}

local function scan()
	local seen: { [BasePart]: boolean } = {}
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	local pads = hub and hub:FindFirstChild("QueuePads")
	if not pads then table.clear(sides); table.clear(known); return end
	table.clear(sides)
	for _, pad in pads:GetChildren() do
		if not pad:IsA("Model") then continue end
		local slots: { [number]: { BasePart } } = {}
		for _, c in pad:GetChildren() do
			if c.Name == "Slot" and c:IsA("BasePart") then
				local t = c:GetAttribute("Team")
				if type(t) == "number" then slots[t] = slots[t] or {}; table.insert(slots[t], c) end
			end
		end
		for _, c in pad:GetChildren() do
			if c.Name == "Glow" and c:IsA("BasePart") then
				local t = c:GetAttribute("Team")
				if type(t) ~= "number" then continue end
				seen[c] = true
				local s = known[c] -- (kept across rescans: its state, its own colour)
				if not s then
					s = { pad = pad, glow = c, light = c:FindFirstChildOfClass("PointLight"), team = t, slots = {}, k = 0, phase = math.random() * PERIOD, base = c.Color, taken = false, flareAt = -math.huge }
					known[c] = s
				end
				s.slots = slots[t] or {}
				table.insert(sides, s)
			end
		end
	end
	for g in known do if not seen[g] then known[g] = nil end end
end

local WHITE = Color3.new(1, 1, 1)
local look = 0
RunService.RenderStepped:Connect(function(dt)
	look += dt
	if look > 3 then look = 0; scan() end
	local cam = workspace.CurrentCamera
	if not cam then return end
	local eye = cam.CFrame.Position
	local now = os.clock()
	for _, s in sides do
		local g = s.glow
		if not g.Parent or not g:IsDescendantOf(workspace) or (g.Position - eye).Magnitude > FAR then continue end
		local taken = false
		for _, q in s.slots do if q.Transparency < 0.5 then taken = true; break end end
		if taken and not s.taken then s.flareAt = now end -- (someone just stepped on: flare)
		s.taken = taken
		-- (k: 0 open .. 1 taken; up fast, down a little slower)
		s.k += ((if taken then 1 else 0) - s.k) * math.min(1, dt * (if taken then 14 else 5))
		local breath = math.sin((now + s.phase) / PERIOD * 2 * math.pi) * BREATH
		local tr = (OPEN + breath) * (1 - s.k) + TAKEN * s.k
		local f = math.clamp(1 - (now - s.flareAt) / FLARE, 0, 1)
		f = f * f -- (a quick flash that settles softly)
		if math.abs(g.Transparency - tr) > 0.004 then g.Transparency = tr end
		local col = if f > 0 then s.base:Lerp(WHITE, 0.55 * f) else s.base
		if g.Color ~= col then g.Color = col end
		local l = s.light
		if l then
			local b = (LIGHT_OPEN * (1 + breath * 3)) * (1 - s.k) + LIGHT_TAKEN * s.k + LIGHT_FLARE * f
			if math.abs(l.Brightness - b) > 0.01 then l.Brightness = b end
			local r = RANGE + (RANGE_FLARE - RANGE) * f
			if math.abs(l.Range - r) > 0.05 then l.Range = r end
		end
	end
end)
scan()
