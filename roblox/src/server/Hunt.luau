--!strict
-- HOLDOUT, the one-gunman hunt mode (26 Nov 2026; roblox/docs/HUNT.md): who is in it and what that changes.
-- THE HOUSE is the mode's lobby. Anyone alive inside the house's lot (its Hunt.Zone box) is in the lobby:
--   * player attribute Hunt = "lobby" (HuntMoves.client wakes up: punch, push, super push, lie down; HuntAnims swaps
--     in the hider's mocap), NoGrapple = true (no grapple anywhere in this mode: Move.client and Main.server refuse)
--   * you respawn in the house (Fight.spawnAt, chained), and nobody can hurt anybody there (the house is Zone "hub" to
--     the rest of the game: weapons holstered, Matches.allow says no; the moves only shove)
--   * ReplicatedStorage attribute HuntPlayers: how many are in the house (the PLAY screen's HOLDOUT card, the board)
-- With 2+ in the house the board counts down HuntConfig.ROUND.lobby seconds and HuntRound starts a round with everyone
-- in the house then (HuntPhase: "lobby" -> "starting" -> "round"; HuntNext = when it starts, server time).
-- Parts tagged HuntPortal (a hub builder's doorway) get a prompt that takes you to the house.
-- The hooks into the rest of the game are chained AND re-asserted every tick: Matches sets Fight.allow / spawnAt /
-- holdRespawn without chaining, and Zombies sets Matches.zoneHook without chaining, whenever they start; whatever is
-- there becomes our "previous".
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local CollectionService = game:GetService("CollectionService")

local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HuntConfig")) :: any
local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local HuntTravel = require(script.Parent:WaitForChild("HuntTravel")) :: any
local HuntRound = require(script.Parent:WaitForChild("HuntRound")) :: any
local HuntMoves = require(script.Parent:WaitForChild("HuntMoves")) :: any

type Fighter = any
local Hunt = {}
Hunt.inHouse = {} :: { [Player]: boolean }

local function house(): Instance?
	local map = workspace:FindFirstChild("Map")
	return map and map:FindFirstChild(HC.HOUSE)
end
local zonePart: BasePart? = nil
local function zone(): BasePart?
	if zonePart and zonePart.Parent then return zonePart end
	local h = house()
	local hf = h and h:FindFirstChild("Hunt")
	local z = hf and hf:FindFirstChild("Zone")
	zonePart = if z and z:IsA("BasePart") then z else nil
	return zonePart
end
local function inside(z: BasePart, p: Vector3): boolean
	local rel = z.CFrame:PointToObjectSpace(p)
	return math.abs(rel.X) <= z.Size.X / 2 and math.abs(rel.Y) <= z.Size.Y / 2 and math.abs(rel.Z) <= z.Size.Z / 2
end

local function setIn(p: Player, on: boolean)
	if (Hunt.inHouse[p] == true) == on then return end
	Hunt.inHouse[p] = if on then true else nil
	p:SetAttribute("Hunt", if on then "lobby" else nil)
	p:SetAttribute("NoGrapple", if on then true else nil)
	p:SetAttribute("HuntLie", nil)
end

-- ------------------------------------------------------------------ the hooks (re-asserted every tick)
type Slot = { mine: any }
local slots: { [string]: Slot } = {}
local function wrap(owner: any, key: string, make: (any) -> any)
	local s = slots[key]
	if not s then s = { mine = nil }; slots[key] = s end
	if owner[key] == s.mine and s.mine ~= nil then return end
	s.mine = make(owner[key])
	owner[key] = s.mine
end
local Matches: any = nil
local function hooks()
	wrap(Fight, "spawnAt", function(prevAt: any)
		return function(f: Fighter): (Vector3, Vector3?)
			local cf = HuntRound.spawnFor(f)
			if not cf and f.kind == "player" then
				local p = f.ref :: Player
				if Hunt.inHouse[p] or HuntRound.returning[p] then cf = HuntTravel.spawnAt() end
			end
			if cf then return cf.Position, cf.LookVector end
			if prevAt then return prevAt(f) end
			return Fight.pickSpawn(f), nil
		end
	end)
	wrap(Fight, "allow", HuntRound.allow)
	wrap(Fight, "modDamage", HuntRound.modDamage)
	wrap(Fight, "holdRespawn", HuntRound.holdRespawn)
	wrap(Fight, "noItems", HuntRound.noItems)
	if not Matches then
		local m = script.Parent:FindFirstChild("Matches")
		if m then local ok, r = pcall(require, m); if ok then Matches = r end end
	end
	if Matches then
		wrap(Matches, "zoneHook", function(prev: any)
			return function(p: Player): string?
				if HuntRound.memberOf(p) then return "match" end -- (a round is a match to every menu: hub buttons hidden, loadouts locked)
				if prev then return prev(p) end
				return nil
			end
		end)
	end
end
HuntMoves.canShove = HuntRound.canShove
HuntMoves.knockScale = HuntRound.knockScale
local HuntItems = require(script.Parent:WaitForChild("HuntItems")) :: any
HuntMoves.weaponOf = HuntItems.weaponOf
HuntMoves.landed = function(p: Player, f: any, kind: string)
	local m = HuntRound.member(f)
	if m and m.role == "gunman" then
		HuntItems.score(p, if kind == "push" or kind == "superpush" then HC.POINTS.push else HC.POINTS.punch)
	end
end
HuntMoves.extra = function(p: Player): { any }
	local g = HuntRound.G
	if not g or g.phase ~= "hunt" or not HuntRound.memberOf(p) then return {} end
	local out = {}
	for _, m in g.members do if not m.p and m.f.alive then table.insert(out, m.f) end end
	return out
end

-- ------------------------------------------------------------------ portals in the hubs (any part tagged HuntPortal)
local function prompt(at: Instance, text: string): ProximityPrompt
	local pr = Instance.new("ProximityPrompt")
	pr.ActionText = text; pr.ObjectText = ""
	pr.KeyboardKeyCode = Enum.KeyCode.F; pr.GamepadKeyCode = Enum.KeyCode.ButtonX
	pr.HoldDuration = 0.3; pr.MaxActivationDistance = 10; pr.RequiresLineOfSight = false
	pr.Parent = at
	return pr
end
local function portal(p: Instance)
	if not p:IsA("BasePart") or p:FindFirstChild("HuntPortalPrompt") then return end
	local pr = prompt(p, HC.TITLE)
	pr.Name = "HuntPortalPrompt"
	pr.Triggered:Connect(function(who) HuntTravel.go(who) end)
end

-- ------------------------------------------------------------------ the lobby's count to a round
local startAt: number? = nil
local function pub(k: string, v: any) if ReplicatedStorage:GetAttribute(k) ~= v then ReplicatedStorage:SetAttribute(k, v) end end
local function lobbyTick(lobby: { Player })
	if HuntRound.busy() then startAt = nil; return end
	local need = tonumber(ReplicatedStorage:GetAttribute("HuntTestMin")) or HC.ROUND.minPlayers
	if #lobby >= need then
		if not startAt then
			startAt = os.clock() + HC.ROUND.lobby
			pub("HuntNext", workspace:GetServerTimeNow() + HC.ROUND.lobby)
			pub("HuntPhase", "starting")
		elseif os.clock() >= startAt then
			startAt = nil
			pub("HuntNext", nil)
			local ok, why = HuntRound.start(lobby)
			if not ok then warn("[hunt] round didn't start: " .. tostring(why)); pub("HuntPhase", "lobby") end
		end
	else
		if startAt then startAt = nil; pub("HuntNext", nil) end
		pub("HuntPhase", "lobby")
	end
end

function Hunt.start()
	hooks()
	for _, p in CollectionService:GetTagged("HuntPortal") do portal(p) end
	CollectionService:GetInstanceAddedSignal("HuntPortal"):Connect(portal)
	-- the house's front door: BACK TO HUB
	task.spawn(function()
		local h = house() or (workspace:WaitForChild("Map"):WaitForChild(HC.HOUSE, 30))
		local hf = h and h:WaitForChild("Hunt", 30)
		local ex = hf and hf:FindFirstChild("Exit")
		if ex and ex:IsA("BasePart") then
			prompt(ex, "BACK TO HUB").Triggered:Connect(function(who) HuntTravel.back(who) end)
		end
	end)
	pub("HuntPhase", "lobby")
	-- who is in the house, the lobby's count, the round: 4 times a second
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < 0.25 then return end
		acc = 0
		hooks()
		local z = zone()
		local lobby = {}
		for _, p in Players:GetPlayers() do
			local ch = p.Character
			local hum = ch and ch:FindFirstChildOfClass("Humanoid")
			local r = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
			if HuntRound.memberOf(p) then
				Hunt.inHouse[p] = nil -- (in a round: the round owns your attributes till it ends)
			elseif r and hum and hum.Health > 0 then
				local inn = z ~= nil and inside(z, r.Position)
				if inn then HuntRound.returning[p] = nil end
				if not HuntRound.returning[p] then setIn(p, inn) end
			end
			if Hunt.inHouse[p] and hum and hum.Health > 0 then table.insert(lobby, p) end
		end
		pub("HuntPlayers", #lobby)
		lobbyTick(lobby)
		HuntRound.tick()
	end)
	Players.PlayerRemoving:Connect(function(p) Hunt.inHouse[p] = nil end)
end

return Hunt
