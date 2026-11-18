--!strict
-- PETS on screen (18 Nov 2026; Shared.Flair PETS, doc FLAIR.md "Pets"): every player's worn pet (the player attribute
-- Pet, FlairServer's) follows them, drawn on each screen by this script alone. nothing about it is on the server: no
-- parts there, no per-frame writes anywhere but these few anchored pieces (one BulkMoveTo per pet, PetRig), and a pet
-- far from your camera isn't moved at all (it waits, parked out of the world, till you come near).
--   * where: everywhere its owner goes (the hub, training, the playground, matches). it can't be shot or stood on and
--     blocks nothing (no collisions, no queries, no touches). you see your own in first person as in third (look down
--     or round at it); only a pet right at the camera hides
--   * how: it walks where its owner walked: a trail of the owner's footing (only while they stand on something), and the
--     pet heads for the point a few studs back along it, off to one side when there's room. so it goes round corners and
--     up the same stairs, never through a wall the owner went round. it trots, crawls or waddles to catch up (the faster
--     the owner, the faster it goes), sits still when they stop, and jumps straight back to them when it falls far
--     behind, is stuck, or they teleport
--   * the floor (18 Nov, the owner: "also the pet clips through too"): every frame one ray down from the pet's own height
--     (not the owner's: under a balcony that found the floor above and lifted the pet through it), and one a step ahead
--     so it rises as a stair comes instead of sinking into it. its feet are never below the floor under it; it eases
--     down steps and slopes. over a gap it keeps its height (then takes its owner's trail's). a wall in its way stops it
--     and it slides along it
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
	groundY: number, missT: number, upT: number, lastRoot: Vector3?, shown: boolean, side: number, snap: boolean,
	stuckT: number, best: number, hideT: number? }
local pets: { [Instance]: F } = {}
-- each owner's trail: where they stood, newest last (points 0.5 studs apart, the last 48)
local trails: { [Instance]: { Vector3 } } = {}
local TRAIL_STEP, TRAIL_MAX = 0.5, 48
local STEP_UP = 2.4     -- the floor is looked for from this far over the pet's feet (stairs, kerbs, a ramp's lip)
local AHEAD = 0.14      -- seconds of its speed it looks ahead for the floor to come

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
local function floorAt(p: Vector3, fromY: number, depth: number?): number?
	local o = Vector3.new(p.X, fromY + STEP_UP, p.Z)
	local hit = workspace:Raycast(o, Vector3.new(0, -(STEP_UP + (depth or 10)), 0), params)
	return if hit then hit.Position.Y else nil
end
-- a wall between two points a pet's height over the floor (nil: clear)
local function wallBetween(a: Vector3, b: Vector3): RaycastResult?
	local o = a + Vector3.new(0, 0.9, 0)
	local d = (b + Vector3.new(0, 0.9, 0)) - o
	if d.Magnitude < 1e-3 then return nil end
	local hit = workspace:Raycast(o, d, params)
	return if hit and math.abs(hit.Normal.Y) < 0.6 then hit else nil
end

local function drop(owner: Instance)
	local f = pets[owner]
	if not f then return end
	pets[owner] = nil
	f.rig:destroy()
end
local function want(owner: Instance): string?
	if owner ~= Players.LocalPlayer and owner:GetAttribute("DevInvisible") == true then return nil end -- (the owner gone invisible: OwnerDev.server)
	local id = owner:GetAttribute("Pet")
	return if type(id) == "string" and Flair.pet(id) then id else nil
end

-- where it wants to be: `keep` studs back along its owner's trail (the slug and the dog a little further: they're longer),
-- off to its side when nothing's there. before there's a trail: straight behind them, short of any wall
local function spot(f: F, r: BasePart, ft: Vector3): Vector3
	local keep = (Flair.pet(f.id) :: any).keep
	local tr = trails[f.owner]
	local at, dir = nil :: Vector3?, nil :: Vector3?
	if tr and #tr >= 2 then
		local left, prev = keep, ft
		for i = #tr, 1, -1 do
			local q = tr[i]
			local d = (q - prev).Magnitude
			if d >= left then
				at = prev + (q - prev).Unit * left
				dir = (prev - q)
				break
			end
			left -= d
			prev = q
		end
		if not at then at = tr[1]; dir = ft - tr[1] end
	end
	if not at then
		local look = r.CFrame.LookVector
		local flat = Vector3.new(look.X, 0, look.Z)
		flat = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(0, 0, -1)
		at = ft - flat * keep
		dir = flat
		local w = wallBetween(ft, at :: Vector3)
		if w then at = Vector3.new(w.Position.X, ft.Y, w.Position.Z) + w.Normal * 0.8 end
	end
	local fl = Vector3.new((dir :: Vector3).X, 0, (dir :: Vector3).Z)
	if fl.Magnitude > 1e-3 then
		local right = Vector3.new(-fl.Unit.Z, 0, fl.Unit.X) * f.side * 1.0
		if not wallBetween(at :: Vector3, (at :: Vector3) + right * 1.4) then at = (at :: Vector3) + right end
	end
	return at :: Vector3
end
-- the owner's trail grows while they stand on something (not mid-jump, not on a pad's flight)
local function track(owner: Instance, ft: Vector3, h: Humanoid?)
	local tr = trails[owner]
	if not tr then tr = {}; trails[owner] = tr end
	if h and h.FloorMaterial == Enum.Material.Air then return end
	local last = tr[#tr]
	if not last or (ft - last).Magnitude >= TRAIL_STEP then
		table.insert(tr, ft)
		if #tr > TRAIL_MAX then table.remove(tr, 1) end
	end
end

local function place(f: F, at: Vector3, yaw: number)
	f.pos, f.yaw, f.vel = at, yaw, Vector3.zero
	f.groundY = at.Y
	f.missT, f.stuckT, f.best = 0, 0, math.huge
end

local function make(owner: Instance, id: string): F?
	local rig = PetRig.new(id)
	if not rig then return nil end
	local f: F = { owner = owner, id = id, rig = rig, pos = Vector3.zero, yaw = 0, vel = Vector3.zero, phase = 0, move = 0,
		groundY = 0, missT = 0, upT = 0, lastRoot = nil, shown = false, snap = true, stuckT = 0, best = math.huge,
		side = if (if owner:IsA("Player") then owner.UserId else #owner.Name) % 2 == 0 then 1 else -1 }
	local r, h = bodyOf(owner)
	pets[owner] = f
	if r then
		local ft = feetOf(r, h)
		local at = spot(f, r, ft)
		place(f, Vector3.new(at.X, floorAt(at, ft.Y) or ft.Y, at.Z), math.atan2(-r.CFrame.LookVector.X, -r.CFrame.LookVector.Z))
	end
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
	owner:GetAttributeChangedSignal("DevInvisible"):Connect(function() sync(owner) end)
	sync(owner)
end
for _, p in Players:GetPlayers() do watchOwner(p) end
Players.PlayerAdded:Connect(watchOwner)
Players.PlayerRemoving:Connect(function(p) drop(p); trails[p] = nil end)
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
			-- (a jump of the body itself is a teleport: a respawn, a pad to a room, the match's start)
			local tele = f.lastRoot ~= nil and (r.Position - (f.lastRoot :: Vector3)).Magnitude > 25
			f.lastRoot = r.Position
			if tele then trails[owner] = {} end
			track(owner, ft, h)
			local want = spot(f, r, ft)
			local flat = Vector3.new(want.X - f.pos.X, 0, want.Z - f.pos.Z)
			local dist = flat.Magnitude
			if math.abs(want.Y - f.pos.Y) > SNAP_UP then f.upT += dt else f.upT = 0 end
			-- stuck: barely moving for a second while well behind (held by a wall the trail doesn't explain)
			if dist > 3 and f.vel.Magnitude < 1.5 then f.stuckT += dt else f.stuckT = 0 end
			if tele or dist > SNAP or f.upT > SNAP_T or f.stuckT > 1.0 or f.snap then
				f.snap = false
				place(f, Vector3.new(want.X, floorAt(want, want.Y) or want.Y, want.Z), math.atan2(-r.CFrame.LookVector.X, -r.CFrame.LookVector.Z))
				f.upT = 0
				dist = 0
				flat = Vector3.zero
			end
			-- catch up: the further behind, the faster (as fast as the owner and then some)
			local speed = if dist > 0.5 then math.min((dist - 0.35) * 4.2, 70) else 0
			local goal = if dist > 1e-3 then flat.Unit * speed else Vector3.zero
			f.vel = f.vel:Lerp(goal, 1 - math.exp(-dt * 9))
			local step = f.vel * dt
			if step.Magnitude > dist and dist > 0 then step = flat end
			-- a wall in the way: no going into it, slide along it
			if step.Magnitude > 1e-4 then
				local w = wallBetween(f.pos, f.pos + step + step.Unit * 0.45)
				if w then
					local n = Vector3.new(w.Normal.X, 0, w.Normal.Z)
					n = if n.Magnitude > 1e-3 then n.Unit else n
					step -= n * math.min(0, step:Dot(n)) -- (only the part that goes into the wall)
					f.vel -= n * math.min(0, f.vel:Dot(n))
				end
			end
			f.pos += step
			-- the floor: under it and a step ahead, every frame, from its own height. the feet never go below the floor;
			-- up a step it rises as the step comes (the look-ahead), down it eases; over a gap it keeps its height, then
			-- takes the trail's
			local here = floorAt(f.pos, f.pos.Y)
			local ahead = if f.vel.Magnitude > 0.5 then floorAt(f.pos + Vector3.new(f.vel.X, 0, f.vel.Z) * AHEAD, f.pos.Y) else nil
			if here then
				f.missT = 0
				f.groundY = here
				local aim = if ahead and ahead > here and ahead - here < STEP_UP then ahead else here
				local dy = aim - f.pos.Y
				local y = f.pos.Y + dy * (1 - math.exp(-dt * (if dy > 0 then 22 else 12)))
				f.pos = Vector3.new(f.pos.X, math.max(y, here), f.pos.Z)
			else
				f.missT += dt
				if f.missT > 0.6 then
					local dy = want.Y - f.pos.Y
					f.pos = Vector3.new(f.pos.X, f.pos.Y + dy * (1 - math.exp(-dt * 8)), f.pos.Z)
				end
			end
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
		-- shown to you as in third person, your own included: only a pet right at the camera hides (the camera inside it).
		-- (18 Nov, the owner: "when in first person your pet doesn't always show up". take 1 hid your own pet whenever it
		-- was in front of you in first person, as the first spec asked; looking at it, or down at it, it was gone)
		local v = f.pos + Vector3.new(0, 0.8, 0) - camPos
		f.rig:hide(v.Magnitude < 1.3, now - (f.hideT or 0) > 0.5)
		if now - (f.hideT or 0) > 0.5 then f.hideT = now end
	end
end)
