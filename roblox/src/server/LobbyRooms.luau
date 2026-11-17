--!strict
-- LOBBY ROOMS: the private lobbies' rooms (roblox/docs/MATCHMAKING.md). one small room per party, built from code when
-- a party needs one and destroyed when it empties. they stand in a row high over the hub (workspace.PartyLobbies, out of
-- Map so ZoneCull leaves them alone; each is well under its 200-part piece size anyway), enclosed, lit from a ceiling
-- panel. the look follows the house rules: few big rounded shapes, flat quiet colours, white light panels, colour only
-- where it means something (the leader's plinth ring is the one amber thing).
-- a room: a dais along the back wall with four plinths in a shallow arc, a light wall behind them, fins on the side
-- walls, a ceiling light over the lineup, and the camera spot facing them (the Play screen's view of the party).
local Workspace = game:GetService("Workspace")

local LobbyRooms = {}

LobbyRooms.ORIGIN = Vector3.new(-200, 720, -10900) -- the first room's floor centre (the hub's Origin is (-200, 240, -10000))
LobbyRooms.STEP = Vector3.new(80, 0, 0) -- room k is (k - 1) steps along
LobbyRooms.SPOTS = 4 -- plinths

local ACCENT = Color3.fromRGB(214, 150, 40) -- (the HUD amber, darker: Neon brightens it)
local RING = Color3.fromRGB(150, 156, 168)
local C = {
	floor = Color3.fromRGB(44, 47, 54), dais = Color3.fromRGB(58, 62, 70), plinth = Color3.fromRGB(72, 76, 86),
	wall = Color3.fromRGB(34, 37, 44), back = Color3.fromRGB(28, 31, 37), fin = Color3.fromRGB(48, 52, 60),
	ceil = Color3.fromRGB(26, 28, 33), panel = Color3.fromRGB(104, 110, 122), trim = Color3.fromRGB(86, 90, 100),
}

export type Room = { slot: number, model: Model, origin: CFrame, spots: { CFrame }, cam: CFrame, focus: Vector3 }

local rooms: { [number]: Room } = {}

local function folder(): Folder
	local f = Workspace:FindFirstChild("PartyLobbies")
	if not f then
		f = Instance.new("Folder")
		f.Name = "PartyLobbies"
		f.Parent = Workspace
	end
	return f :: Folder
end

local function part(parent: Instance, name: string, size: Vector3, cf: CFrame, color: Color3, shape: Enum.PartType?, mat: Enum.Material?): Part
	local p = Instance.new("Part")
	p.Name = name
	p.Anchored = true
	p.CanTouch = false
	p.CastShadow = false
	p.TopSurface = Enum.SurfaceType.Smooth
	p.BottomSurface = Enum.SurfaceType.Smooth
	p.Material = mat or Enum.Material.SmoothPlastic
	p.Color = color
	if shape then p.Shape = shape end
	p.Size = size
	p.CFrame = cf
	p.Parent = parent
	return p
end

-- where the plinths stand, in the room's own space (x across, z toward the camera): a shallow arc, the middle two
-- forward. member i takes SPOT_ORDER[i] (the first two in the middle)
local SPOT_X = { -5.1, -1.7, 1.7, 5.1 }
local SPOT_Z = { -6.4, -5.8, -5.8, -6.4 }
LobbyRooms.SPOT_ORDER = { 2, 3, 1, 4 }
local DAIS_TOP = 1.0
local PLINTH_H = 0.8

local function build(slot: number): Room
	local o = CFrame.new(LobbyRooms.ORIGIN + LobbyRooms.STEP * (slot - 1))
	local m = Instance.new("Model")
	m.Name = ("Lobby%d"):format(slot)
	local function at(x: number, y: number, z: number): CFrame return o * CFrame.new(x, y, z) end
	-- the shell: 40 wide, 30 deep, 20 high; the back wall at z -12, the front at z +18
	part(m, "Floor", Vector3.new(40, 1, 31), at(0, -0.5, 3), C.floor)
	part(m, "Ceiling", Vector3.new(40, 1, 31), at(0, 20.5, 3), C.ceil)
	part(m, "Back", Vector3.new(40, 21, 1), at(0, 10, -12.5), C.back)
	part(m, "Front", Vector3.new(40, 21, 1), at(0, 10, 18.5), C.wall)
	for _, sx in { -1, 1 } do
		part(m, "Side", Vector3.new(1, 21, 31), at(sx * 20.5, 10, 3), C.wall)
		-- three fins on each side wall, a thick rounded rib each
		for i, z in { -6, 2, 10 } do
			local fin = part(m, "Fin" .. i, Vector3.new(20, 1.6, 1.6), at(sx * 19.4, 10, z), C.fin, Enum.PartType.Cylinder)
			fin.CFrame = at(sx * 19.4, 10, z) * CFrame.Angles(0, 0, math.rad(90))
		end
		-- a cut corner where the wall meets the ceiling (45 degrees)
		local cut = part(m, "Cove", Vector3.new(3, 3, 31), at(sx * 19.2, 19.2, 3), C.ceil)
		cut.CFrame = at(sx * 19.2, 19.2, 3) * CFrame.Angles(0, 0, math.rad(45))
	end
	-- the light wall behind the lineup: one big pale panel, framed
	part(m, "PanelFrame", Vector3.new(30, 11, 0.6), at(0, 8.5, -11.9), C.trim)
	local panel = part(m, "LightPanel", Vector3.new(28.6, 9.6, 0.4), at(0, 8.5, -11.6), C.panel, nil, Enum.Material.Neon)
	panel.Transparency = 0.3
	local wl = Instance.new("SurfaceLight")
	wl.Face = Enum.NormalId.Front; wl.Brightness = 0.6; wl.Range = 16; wl.Angle = 110; wl.Color = Color3.fromRGB(226, 230, 238); wl.Shadows = false
	wl.Parent = panel
	-- the dais: one long rounded step across the back, a lower lip in front of it
	part(m, "Dais", Vector3.new(26, DAIS_TOP, 8), at(0, DAIS_TOP / 2, -7), C.dais)
	part(m, "DaisLip", Vector3.new(26, DAIS_TOP, DAIS_TOP), at(0, DAIS_TOP / 2, -3), C.dais, Enum.PartType.Cylinder) -- (a cylinder runs along x)
	-- the plinths: a round block, a thin light ring round its foot
	local spots = {}
	for i = 1, LobbyRooms.SPOTS do
		local x, z = SPOT_X[i], SPOT_Z[i]
		local pl = part(m, "Plinth" .. i, Vector3.new(PLINTH_H, 3.2, 3.2), at(x, DAIS_TOP + PLINTH_H / 2, z) * CFrame.Angles(0, 0, math.rad(90)), C.plinth, Enum.PartType.Cylinder)
		pl:SetAttribute("Spot", i)
		local ring = part(m, "Ring" .. i, Vector3.new(0.14, 3.5, 3.5), at(x, DAIS_TOP + 0.08, z) * CFrame.Angles(0, 0, math.rad(90)), RING, Enum.PartType.Cylinder, Enum.Material.Neon)
		ring.Transparency = 0.6
		ring.CanCollide = false
		-- where a body stands: on top of the plinth, facing the camera (the room's +z; rooms are never turned)
		local top = at(x, DAIS_TOP + PLINTH_H, z).Position
		spots[i] = CFrame.lookAt(top, top + Vector3.new(0, 0, 1))
	end
	-- the ceiling light over the lineup
	local cl = part(m, "CeilingPanel", Vector3.new(22, 0.4, 8), at(0, 19.8, -4), C.panel, nil, Enum.Material.Neon)
	cl.Transparency = 0.25
	local sl = Instance.new("SurfaceLight")
	sl.Face = Enum.NormalId.Bottom; sl.Brightness = 1.4; sl.Range = 24; sl.Angle = 100; sl.Color = Color3.fromRGB(236, 238, 244); sl.Shadows = false
	sl.Parent = cl
	-- a soft front light from behind the camera, so faces aren't dark
	local fill = part(m, "Fill", Vector3.new(1, 1, 1), at(0, 9, 14), C.ceil)
	fill.Transparency = 1
	fill.CanCollide = false
	local pl = Instance.new("PointLight")
	pl.Brightness = 0.9; pl.Range = 30; pl.Color = Color3.fromRGB(230, 232, 240); pl.Shadows = false
	pl.Parent = fill
	-- the camera: in front, a little over eye height, looking at the lineup's chests
	local camPos = at(0, 5.6, 11.5).Position
	local focus = at(0, 3.1, -6).Position -- (low: the lineup sits in the upper middle, clear of the big button)
	local cam = CFrame.lookAt(camPos, focus)
	m:SetAttribute("Slot", slot)
	m:SetAttribute("CameraCF", cam)
	m:SetAttribute("Focus", focus)
	m.WorldPivot = o
	m.Parent = folder()
	return { slot = slot, model = m, origin = o, spots = spots, cam = cam, focus = focus }
end

-- a free room (built now), or nil if something went wrong
function LobbyRooms.claim(): Room?
	local k = 1
	while rooms[k] do k += 1 end
	local ok, r = pcall(build, k)
	if not ok then warn("[jankfire] lobby room: " .. tostring(r)); return nil end
	rooms[k] = r :: Room
	return r :: Room
end

function LobbyRooms.release(r: Room)
	if rooms[r.slot] == r then rooms[r.slot] = nil end
	if r.model.Parent then r.model:Destroy() end
end

-- the standing spot for the i-th member of a party (SPOT_ORDER), or nil past the last plinth
function LobbyRooms.spot(r: Room, i: number): CFrame?
	local k = LobbyRooms.SPOT_ORDER[i]
	return if k then r.spots[k] else nil
end

-- light the rings: the leader's amber, the other taken spots pale, empty ones dim
function LobbyRooms.rings(r: Room, taken: number, leaderIndex: number?)
	for i = 1, LobbyRooms.SPOTS do
		local ring = r.model:FindFirstChild("Ring" .. LobbyRooms.SPOT_ORDER[i]) :: BasePart?
		if ring then
			local on = i <= taken
			ring.Color = if i == leaderIndex then ACCENT else RING
			ring.Transparency = if on then 0.35 else 0.8
		end
	end
end

function LobbyRooms.count(): number
	local n = 0
	for _ in rooms do n += 1 end
	return n
end

return LobbyRooms
