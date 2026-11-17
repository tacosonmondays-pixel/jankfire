--!strict
-- the hub's queue pads, lit on your own screen (owner, 17 Nov: "can we try removing the circles on the pads and then
-- make them glow?"). each side of a pad has a Glow (HubRotunda's B.pad: a thin neon face in its team's colour over the
-- plate, a soft PointLight in it, attribute Team). while the side is open it breathes slowly; while someone stands on it,
-- it brightens: Matches lights that side's Slot markers then (each a speck buried in the plate: their Transparency, 0
-- while the place is taken, is the only thing read here). nothing here changes what the pads do, only how they look.
-- pads out of your world (ZoneCull) or far from the camera are left alone
local RunService = game:GetService("RunService")

local OPEN, BREATH, TAKEN = 0.45, 0.07, 0.1 -- (the Glow's see-through: open, how far it breathes, taken)
local LIGHT_OPEN, LIGHT_TAKEN = 0.45, 1.1 -- (its light's brightness)
local PERIOD = 3.4 -- (seconds a breath)
local FAR = 160 -- (studs from the camera)

type Side = { pad: Model, glow: BasePart, light: PointLight?, team: number, slots: { BasePart }, k: number, phase: number }
local sides: { Side } = {}

local function scan()
	table.clear(sides)
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	local pads = hub and hub:FindFirstChild("QueuePads")
	if not pads then return end
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
				table.insert(sides, { pad = pad, glow = c, light = c:FindFirstChildOfClass("PointLight"), team = t, slots = slots[t] or {}, k = 0, phase = math.random() * PERIOD })
			end
		end
	end
end

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
		-- (k: 0 open .. 1 taken, eased so a step on or off fades over about a third of a second)
		s.k += ((if taken then 1 else 0) - s.k) * math.min(1, dt * 6)
		local breath = math.sin((now + s.phase) / PERIOD * 2 * math.pi) * BREATH
		local tr = (OPEN + breath) * (1 - s.k) + TAKEN * s.k
		if math.abs(g.Transparency - tr) > 0.005 then g.Transparency = tr end
		local l = s.light
		if l then
			local b = (LIGHT_OPEN * (1 + breath * 2)) * (1 - s.k) + LIGHT_TAKEN * s.k
			if math.abs(l.Brightness - b) > 0.01 then l.Brightness = b end
		end
	end
end)
scan()
