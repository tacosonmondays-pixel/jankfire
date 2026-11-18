--!strict
-- PET SECRETS (18 Nov 2026): how the three secret pets are found (Shared.Flair PETS; worn and saved by FlairServer, asked
-- through its PetOps). nothing on screen ever hints at any of them: the first you know is "NEW PET · <NAME>".
--   mannequin  find the hub egg (the hidden mannequin, HubEgg.server). whoever owns its OG title has the mini mannequin:
--              checked when the loot save is in and whenever it changes, so anyone who found it before pets existed
--              gets theirs too. (agreed with the training session: HubEgg itself is untouched)
--   slug       be down on THE GUT's platform when the train passes behind the glass, three times (any matches, saved:
--              FlairServer's d.seen.train). GutTrain.server writes TrainAt (the server time its face reaches the
--              station) on every Gut arena; a run counts for whoever stands on that arena's platform then
--   dog        a little kennel in the Gut subway's south-west corner, by the glass, behind the last column: walk up to
--              its door. placed here, at run time, in every Gut arena (workspace.Map.Gut and its copies, which are
--              clones of it): ServerStorage.JankfirePetKit.Kennel (PolishBackup.PetImport builds it from its upload)
-- Studio play tests: ServerStorage.PetTest (BindableFunction) answers, for the first player:
--   "state"         what they have, the train count, the kennels and how far the nearest door is
--   "train"         a train passes now in every Gut arena (TrainAt = now + 0.2: the same path as a real run)
--   "kennel"        stand them at the first kennel's door (the find itself is the real path)
--   "grant", id     give a pet (the real grant: the callout and the sound)
--   "forget", id    lose one again ("all": every pet and the train count). Studio saves are the _studio stores
--   "platform"      stand them on Map.Gut's platform, facing the glass
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")
local RunService = game:GetService("RunService")

local Jankfire = script.Parent
local Loot = require(Jankfire:WaitForChild("Loot")) :: any
local PetOps = Jankfire:WaitForChild("FlairServer"):WaitForChild("PetOps") :: BindableFunction

-- THE GUT's frame (gut_layout.py, the arena's pivot at its site's middle on the street; copies only move): the platform
-- (its top y -30, x -100..100, z 18..46; the glass at 46), and where the kennel stands: its back to the end wall
-- (x -100), its side to the glass, its door facing east along the platform (the kennel's own front is -Z)
local PLATFORM_MIN, PLATFORM_MAX = Vector3.new(-100, -31, 18), Vector3.new(100, -12, 46)
local KENNEL_AT = CFrame.new(-98.15, -29.99, 43.9) * CFrame.Angles(0, -math.pi / 2, 0) -- (its roof's back edge 1.8 behind its middle, its bowl 2.4 ahead)
local DOOR = Vector3.new(0, 0, -1.9)  -- (in the kennel's frame: just in front of the doorway)
local DOOR_REACH = 4.2                -- studs (flat) from that point to a player's middle
local TRAIN_NEED = 3                  -- train runs seen from the platform

local function rootOf(p: Player): BasePart?
	local ch = p.Character
	local r = ch and ch:FindFirstChild("HumanoidRootPart")
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	return if r and r:IsA("BasePart") and hum and hum.Health > 0 then r else nil
end

-- (a grant waits for the flair save: it may still be loading when you join)
local pending: { [string]: boolean } = {}
local function grant(p: Player, id: string)
	local key = p.UserId .. ":" .. id
	if pending[key] then return end
	pending[key] = true
	task.spawn(function()
		local t0 = os.clock()
		while p.Parent and os.clock() - t0 < 60 do
			local ok, res = pcall(PetOps.Invoke, PetOps, "grant", p, id)
			if ok and res ~= "loading" then break end
			task.wait(1)
		end
		pending[key] = nil
	end)
end
local function has(p: Player, id: string): boolean
	local ok, res = pcall(PetOps.Invoke, PetOps, "owns", p, id)
	return ok and res == true
end

-- ------------------------------------------------------------------ the mini mannequin: the hub egg's OG title
local function checkEgg(p: Player)
	if not p.Parent or not Loot.ready(p) then return end
	local ok, yes = pcall(Loot.owns, p, "title", "og")
	if ok and yes == true and not has(p, "mannequin") then grant(p, "mannequin") end
end
Loot.changed:Connect(function(p: Player) task.defer(checkEgg, p) end)
local function joined(p: Player)
	task.spawn(function()
		local t0 = os.clock()
		while p.Parent and not Loot.ready(p) and os.clock() - t0 < 60 do task.wait(1) end
		task.wait(2) -- (and the flair save)
		checkEgg(p)
	end)
end
for _, p in Players:GetPlayers() do joined(p) end
Players.PlayerAdded:Connect(joined)

-- ------------------------------------------------------------------ THE GUT: its arenas, the train, the kennel
local guts: { [Model]: boolean } = {}
local kennels: { [Model]: Model } = {} -- (arena -> its kennel)

local function kit(): Model?
	local f = ServerStorage:FindFirstChild("JankfirePetKit")
	local k = f and f:FindFirstChild("Kennel")
	return if k and k:IsA("Model") then k else nil
end
local function placeKennel(root: Model)
	local have = root:FindFirstChild("PetKennel")
	if have and have:IsA("Model") then kennels[root] = have; return end
	local k = kit()
	if not k then return end
	local c = k:Clone()
	c.Name = "PetKennel"
	c:PivotTo(root:GetPivot() * KENNEL_AT)
	c.Parent = root
	kennels[root] = c
end

-- who stands on this arena's platform now
local function onPlatform(root: Model): { Player }
	local out = {}
	local pv = root:GetPivot()
	for _, p in Players:GetPlayers() do
		local r = rootOf(p)
		if r then
			local v = pv:PointToObjectSpace(r.Position)
			if v.X >= PLATFORM_MIN.X and v.X <= PLATFORM_MAX.X and v.Y >= PLATFORM_MIN.Y and v.Y <= PLATFORM_MAX.Y
				and v.Z >= PLATFORM_MIN.Z and v.Z <= PLATFORM_MAX.Z then
				table.insert(out, p)
			end
		end
	end
	return out
end
local counted: { [Model]: number } = {} -- (the TrainAt each arena's last run was counted for)
local function trainRun(root: Model)
	local at = root:GetAttribute("TrainAt")
	if type(at) ~= "number" or counted[root] == at then return end
	counted[root] = at
	task.delay(math.max(0, at - workspace:GetServerTimeNow()) + 0.4, function()
		if not root.Parent or root:GetAttribute("TrainAt") ~= at then return end
		for _, p in onPlatform(root) do
			if not has(p, "slug") then
				local ok, n = pcall(PetOps.Invoke, PetOps, "bump", p, "train")
				if ok and type(n) == "number" and n >= TRAIN_NEED then grant(p, "slug") end
			end
		end
	end)
end

local function addGut(root: Model)
	if guts[root] then return end
	guts[root] = true
	placeKennel(root)
	root:GetAttributeChangedSignal("TrainAt"):Connect(function() trainRun(root) end)
	root.AncestryChanged:Connect(function()
		if not root:IsDescendantOf(workspace) then guts[root] = nil; kennels[root] = nil; counted[root] = nil end
	end)
end
local function watch(folder: Instance)
	local function try(m: Instance)
		if m:IsA("Model") and m:GetAttribute("MapId") == "gut" then addGut(m) end
	end
	for _, m in folder:GetChildren() do try(m) end
	folder.ChildAdded:Connect(try)
end
task.spawn(function()
	local map = workspace:WaitForChild("Map")
	watch(map)
	local copies = map:FindFirstChild("ArenaCopies")
	if copies then watch(copies) end
	map.ChildAdded:Connect(function(c) if c.Name == "ArenaCopies" then watch(c) end end)
	-- (the kit may come in after the arenas: place what's missing once it's there)
	while not kit() do task.wait(5) end
	for root in guts do placeKennel(root) end
end)

-- the kennel's door: anyone who walks up to it (a few times a second; nobody else is near a Gut kennel outside a match)
local function doorOf(k: Model): Vector3
	return k:GetPivot():PointToWorldSpace(DOOR)
end
local acc = 0
RunService.Heartbeat:Connect(function(dt: number)
	acc += dt
	if acc < 0.3 then return end
	acc = 0
	if next(kennels) == nil then return end
	for _, p in Players:GetPlayers() do
		local r = rootOf(p)
		if r then
			for _, k in kennels do
				if k.Parent then
					local d = doorOf(k) - r.Position
					if math.abs(d.Y) < 6 and Vector3.new(d.X, 0, d.Z).Magnitude <= DOOR_REACH then
						if not has(p, "dog") then grant(p, "dog") end
					end
				end
			end
		end
	end
end)

Players.PlayerRemoving:Connect(function(p)
	for key in pending do if string.find(key, "^" .. p.UserId .. ":") then pending[key] = nil end end
end)

-- ------------------------------------------------------------------ Studio play tests
if RunService:IsStudio() then
	local old = ServerStorage:FindFirstChild("PetTest")
	if old then old:Destroy() end
	local f = Instance.new("BindableFunction")
	f.Name = "PetTest"
	f.OnInvoke = function(op: any, a: any): any
		local p = Players:GetPlayers()[1]
		if not p then return "no player" end
		local r = rootOf(p)
		if op == "state" then
			local have = {}
			for _, id in { "mannequin", "slug", "dog" } do if has(p, id) then table.insert(have, id) end end
			local ok, n = pcall(PetOps.Invoke, PetOps, "count", p, "train")
			local near, nk = math.huge, 0
			for _, k in kennels do
				nk += 1
				if r then near = math.min(near, (doorOf(k) - r.Position).Magnitude) end
			end
			local gs = 0
			for _ in guts do gs += 1 end
			return ("pets [%s] worn=%s train=%s guts=%d kennels=%d door=%.1f og=%s"):format(table.concat(have, ","),
				tostring(p:GetAttribute("Pet")), tostring(ok and n), gs, nk, near, tostring(Loot.ready(p) and Loot.owns(p, "title", "og")))
		elseif op == "train" then
			local n = 0
			for root in guts do root:SetAttribute("TrainAt", workspace:GetServerTimeNow() + 0.2); n += 1 end
			return "train in " .. n .. " arenas"
		elseif op == "kennel" then
			local g = workspace.Map:FindFirstChild("Gut")
			local k: Model? = if g and g:IsA("Model") then kennels[g] else nil
			if not k then for _, kk in kennels do k = kk; break end end
			if not k or not r then return "no kennel or no body" end
			local at = doorOf(k) + k:GetPivot().LookVector * 1.5 + Vector3.new(0, 3, 0)
			p:SetAttribute("TeleportT", workspace:GetServerTimeNow())
			p.Character:PivotTo(CFrame.lookAt(at, doorOf(k) + Vector3.new(0, 3, 0)))
			return "at the kennel's door"
		elseif op == "platform" then
			local g = workspace.Map:FindFirstChild("Gut") :: Model?
			if not g or not r then return "no Gut or no body" end
			local at = g:GetPivot():PointToWorldSpace(Vector3.new(-40, -27, 38))
			p:SetAttribute("TeleportT", workspace:GetServerTimeNow())
			p.Character:PivotTo(CFrame.lookAt(at, at + g:GetPivot():VectorToWorldSpace(Vector3.new(0, 0, 1))))
			return "on the platform"
		elseif op == "grant" then
			return PetOps:Invoke("grant", p, a)
		elseif op == "forget" then
			return PetOps:Invoke("forget", p, a)
		end
		return "ops: state, train, kennel, grant id, forget id|all, platform"
	end
	f.Parent = ServerStorage
end
