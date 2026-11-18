--!strict
-- PETS on screen (18 Nov 2026; Shared.Flair PETS, doc FLAIR.md "Pets"): every player's worn pet (the player attribute
-- Pet, FlairServer's) follows them, drawn on each screen by this script alone. nothing about it is on the server: no
-- parts there, no per-frame writes anywhere but these few anchored pieces (one BulkMoveTo per pet, PetRig), and a pet
-- far from your camera isn't moved at all (it waits, parked out of the world, till you come near).
--   * where: everywhere its owner goes (the hub, training, the playground, matches). it can't be shot or stood on and
--     blocks nothing (no collisions, no queries, no touches); your own is hidden while it's in front of you in first
--     person, and any pet right at the camera is hidden too
--   * how: it keeps a few studs behind its owner, off to one side; trots, crawls or waddles to catch up (the faster the
--     owner, the faster it goes), sits still when they stop, walks the floor under it (one ray now and then), and jumps
--     straight back to them when it falls far behind or they teleport
-- test hooks (Studio): workspace attribute PetFreeze = true holds every pet's pose (photos); a Model with a Humanoid and
-- a HumanoidRootPart, tagged PetStandIn, with its own attribute Pet, walks a pet too (a client-side stand-in for photos)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Flair = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Flair")) :: any
local PetRig = require(script.Parent:WaitForChild("PetRig")) :: any
local me = Players.LocalPlayer

local SHOW, HIDE = 150, 165   -- studs from the camera: drawn within SHOW, parked past HIDE
local SNAP = 42               -- studs behind (flat) before it jumps back to its owner
local SNAP_UP = 12            -- or this far above/below them for SNAP_T seconds (they took a pad or a lift)
local SNAP_T = 1.2
local STRIDE = { waddle = 0.75, crawl = 1.1, trot = 1.0 } -- (studs a gait cycle covers)
local MAX_HZ = { waddle = 4.2, crawl = 3.2, trot = 4.6 }   -- (cycles a second at most: a sprinting owner gets a glide)

local folder = Instance.new("Folder")
folder.Name = "ClientPets"
folder.Parent = workspace

type F = { owner: Instance, id: string, rig: any, pos: Vector3, yaw: number, vel: Vector3, phase: number, move: number,
	groundY: number, rayT: number, rayAt: Vector3, upT: number, lastRoot: Vector3?, shown: boolean, side: number, snap: boolean }
local pets: { [Instance]: F } = {}

-- (the floor under a pet: one ray, missing every body and every pet; things you walk through don't count)
local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Exclude
params.RespectCanCollide = true
local filterT = 0
local function refreshFilter()
	local list: { Instance } = { folder }
	for _, p in Players:GetPlayers() do if p.Character then table.insert(list, p.Character) end end
	for _, m in CollectionService:GetTagged("PetStandIn") do table.insert(list, m) end
	params.FilterDescendantsInstances = list
end

local function bodyOf(owner: Instance): (BasePart?, Humanoid?)
	local ch: Instance? = if owner:IsA("Player") then owner.Character else owner
	local r = ch and ch:FindFirstChild("HumanoidRootPart")
	local h = ch and ch:FindFirstChildOfClass("Humanoid")
	return (if r and r:IsA("BasePart") then r else nil), h
end
local function feetOf(r: BasePart, h: Humanoid?): Vector3
	local hip = if h then h.HipHeight else 2
	return r.Position - Vector3.new(0, hip + r.Size.Y / 2, 0)
end
local function floorAt(p: Vector3, fromY: number): number?
	local o = Vector3.new(p.X, fromY + 4, p.Z)
	local hit = workspace:Raycast(o, Vector3.new(0, -40, 0), params)
	return if hit then hit.Position.Y else nil
end

local function drop(owner: Instance)
	local f = pets[owner]
	if not f then return end
	pets[owner] = nil
	f.rig:destroy()
end
local function want(owner: Instance): string?
	local id = owner:GetAttribute("Pet")
	return if type(id) == "string" and Flair.pet(id) then id else nil
end

-- where it wants to be: behind its owner, off to its side (the slug and the dog a little further: they're longer)
local function spot(f: F, r: BasePart): Vector3
	local keep = (Flair.pet(f.id) :: any).keep
	local look = r.CFrame.LookVector
	local flat = Vector3.new(look.X, 0, look.Z)
	flat = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(0, 0, -1)
	local right = Vector3.new(-flat.Z, 0, flat.X)
	return -flat * keep + right * (f.side * 1.9)
end

local function place(f: F, at: Vector3, yaw: number)
	f.pos, f.yaw, f.vel = at, yaw, Vector3.zero
	f.groundY = at.Y
	f.rayT = 0
end

local function make(owner: Instance, id: string): F?
	local rig = PetRig.new(id)
	if not rig then return nil end
	local f: F = { owner = owner, id = id, rig = rig, pos = Vector3.zero, yaw = 0, vel = Vector3.zero, phase = 0, move = 0,
		groundY = 0, rayT = 0, rayAt = Vector3.zero, upT = 0, lastRoot = nil, shown = false, snap = true,
		side = if (if owner:IsA("Player") then owner.UserId else #owner.Name) % 2 == 0 then 1 else -1 }
	local r, h = bodyOf(owner)
	if r then
		local ft = feetOf(r, h)
		local at = ft + spot(f, r)
		place(f, Vector3.new(at.X, floorAt(at, ft.Y) or ft.Y, at.Z), math.atan2(-r.CFrame.LookVector.X, -r.CFrame.LookVector.Z))
	end
	pets[owner] = f
	return f
end

local function sync(owner: Instance)
	local id = want(owner)
	local f = pets[owner]
	if f and f.id ~= id then drop(owner); f = nil end
	if id and not f then make(owner, id) end
end
local function watchOwner(owner: Instance)
	owner:GetAttributeChangedSignal("Pet"):Connect(function() sync(owner) end)
	sync(owner)
end
for _, p in Players:GetPlayers() do watchOwner(p) end
Players.PlayerAdded:Connect(watchOwner)
Players.PlayerRemoving:Connect(drop)
-- (Studio photos: a stand-in body that walks a pet like a player)
local function standIn(m: Instance)
	watchOwner(m)
	m.AncestryChanged:Connect(function() if not m:IsDescendantOf(workspace) then drop(m) end end)
end
for _, m in CollectionService:GetTagged("PetStandIn") do standIn(m) end
CollectionService:GetInstanceAddedSignal("PetStandIn"):Connect(standIn)
-- (the pets' models may come in after this script starts)
task.spawn(function()
	local kit = ReplicatedStorage:WaitForChild("JankfirePets", 120)
	if not kit then return end
	for owner in pairs(pets) do sync(owner) end
	for _, p in Players:GetPlayers() do sync(p) end
end)

local function angleTo(a: number, b: number, k: number): number
	local d = (b - a + math.pi) % (2 * math.pi) - math.pi
	return a + d * k
end

RunService.RenderStepped:Connect(function(dt: number)
	dt = math.min(dt, 0.1)
	local now = os.clock()
	if now - filterT > 1 then filterT = now; refreshFilter() end
	local cam = workspace.CurrentCamera
	if not cam then return end
	local camPos = cam.CFrame.Position
	local frozen = workspace:GetAttribute("PetFreeze") == true
	local myHead = me.Character and me.Character:FindFirstChild("Head") :: BasePart?
	local firstPerson = myHead ~= nil and (camPos - myHead.Position).Magnitude < 1.6
	for owner, f in pets do
		local r, h = bodyOf(owner)
		-- far from you: parked, not moved (it catches up the moment it's back in range: the snap below)
		local near = (f.pos - camPos).Magnitude
		if near > HIDE and (not r or (r.Position - camPos).Magnitude > HIDE) then
			if f.shown then f.shown = false; f.rig.model.Parent = nil end
			if r then f.lastRoot = nil end
			continue
		end
		if not f.shown and (near <= SHOW or (r and (r.Position - camPos).Magnitude <= SHOW)) then
			f.shown = true
			f.snap = true -- (back in range: it starts by its owner, wherever it was parked)
			f.rig.model.Parent = folder
		end
		if not f.shown then continue end
		if frozen then continue end
		if r then
			local ft = feetOf(r, h)
			local want = ft + spot(f, r)
			-- (a jump of the body itself is a teleport: a respawn, a pad to a room, the match's start)
			local tele = f.lastRoot ~= nil and (r.Position - (f.lastRoot :: Vector3)).Magnitude > 25
			f.lastRoot = r.Position
			local flat = Vector3.new(want.X - f.pos.X, 0, want.Z - f.pos.Z)
			local dist = flat.Magnitude
			if math.abs(ft.Y - f.pos.Y) > SNAP_UP then f.upT += dt else f.upT = 0 end
			if tele or dist > SNAP or f.upT > SNAP_T or f.snap then
				f.snap = false
				place(f, Vector3.new(want.X, floorAt(want, ft.Y) or ft.Y, want.Z), math.atan2(-r.CFrame.LookVector.X, -r.CFrame.LookVector.Z))
				f.upT = 0
				dist = 0
				flat = Vector3.zero
			end
			-- catch up: the further behind, the faster (as fast as the owner and then some)
			local speed = if dist > 0.7 then math.min((dist - 0.5) * 4.2, 70) else 0
			local goal = if dist > 1e-3 then flat.Unit * speed else Vector3.zero
			f.vel = f.vel:Lerp(goal, 1 - math.exp(-dt * 9))
			local step = f.vel * dt
			if step.Magnitude > dist and dist > 0 then step = flat end
			f.pos += step
			-- the floor under it, now and then (and its height eases to it: down fast, up with a little hop)
			if now - f.rayT > 0.09 or (f.pos - f.rayAt).Magnitude > 0.8 then
				f.rayT, f.rayAt = now, f.pos
				f.groundY = floorAt(f.pos, math.max(f.pos.Y, ft.Y)) or ft.Y
			end
			local dy = f.groundY - f.pos.Y
			f.pos = Vector3.new(f.pos.X, f.pos.Y + dy * (1 - math.exp(-dt * (if dy < 0 then 14 else 10))), f.pos.Z)
			-- face where it goes; standing, turn slowly to its owner
			local sp = f.vel.Magnitude
			if sp > 0.6 then
				f.yaw = angleTo(f.yaw, math.atan2(-f.vel.X, -f.vel.Z), 1 - math.exp(-dt * 10))
			else
				local to = r.Position - f.pos
				if Vector3.new(to.X, 0, to.Z).Magnitude > 1.5 then f.yaw = angleTo(f.yaw, math.atan2(-to.X, -to.Z), 1 - math.exp(-dt * 2.5)) end
			end
			local g = (Flair.pet(f.id) :: any).gait
			f.move += (math.clamp(sp / 5, 0, 1) - f.move) * (1 - math.exp(-dt * 8))
			f.phase = (f.phase + dt * math.min(sp / STRIDE[g], MAX_HZ[g]) * 2 * math.pi) % (2 * math.pi * 64)
		else
			f.vel = Vector3.zero
			f.move += (0 - f.move) * (1 - math.exp(-dt * 8))
			f.lastRoot = nil
		end
		local cf = CFrame.new(f.pos) * CFrame.Angles(0, f.yaw, 0)
		f.rig:pose(cf, f.phase, f.move, now)
		-- out of your way: your own in front of you in first person, and any right at the camera
		local v = f.pos + Vector3.new(0, 0.8, 0) - camPos
		local hide = v.Magnitude < 2.2
		if not hide and owner == me and firstPerson then
			hide = v.Magnitude < 14 and cam.CFrame.LookVector:Dot(v.Unit) > 0.25
		end
		f.rig:hide(hide)
	end
end)
