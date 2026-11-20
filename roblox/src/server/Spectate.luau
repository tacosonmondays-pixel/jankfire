--!strict
-- the SPECTATE BOARD (20 Nov 2026, the owner: "can there be a board where you can specate current games?"; main's spec;
-- docs/MATCHMAKING.md "Watching matches"). every match running on THIS server is listed on a board in each hub (parts
-- tagged SpectateBoard, the hub session's markers: the client draws the list on its front face) and in the PLAY
-- screen's WATCH tab. WATCH puts your camera in that match:
--   * your body stays where it stood, anchored, with the attribute Watching = the match id. nothing in the match knows
--     you're there: you're not in it, so no hits, zones, ranked, stats or quests; the anti-cheat sees a body standing
--     still. the camera, the arena's look and the culling are the client's (client/SpectateClient.client.luau)
--   * the server streams the arena to you (ReplicationFocus) while you watch
--   * it ends on LEAVE, when the match ends (rounds and their breaks carry on), or when you leave the server
-- not while you're in a match, a map room, a ZOMBIES game, or your party is searching; and your party can't search
-- while you watch (Party.find). RANKED matches are listed but not watchable (Spectate.RANKED): a friend watching could
-- call out where everyone is (ghosting). matches on other servers (cross-server) aren't on the board at all
--   remote JankfireRemotes.Spectate (RemoteFunction): "list" -> { ok, matches }, "watch" id -> { ok, why?, watch },
--   "leave", "info" -> { ok, watch } (the watched match's players now: the client asks every few s)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")
local RunService = game:GetService("RunService")

local Spectate = {}
Spectate.ON = true
Spectate.RANKED = false -- (ranked matches listed, not watchable. final: the owner, "Can't spectate ranked since you have to match make for it")

local Matches: any, Party: any
type W = { id: any, anchored: boolean? }
local watching: { [Player]: W } = {}

local function rootOf(p: Player): BasePart?
	local ch = p.Character
	return ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
end

-- why p can't watch now, or nil
local function blocked(p: Player): string?
	if Matches.matchOf(p) then return "you're in a match" end
	local z = p:GetAttribute("Zone")
	if z == "staging" then return "you're in a map room" end
	if p:GetAttribute("ZmOn") then return "you're in a ZOMBIES game" end
	local busy = Party.busy and Party.busy(p)
	if busy then return busy end
	local ch = p.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if not hum or hum.Health <= 0 or not rootOf(p) then return "not now" end
	return nil
end

function Spectate.stop(p: Player)
	local w = watching[p]
	if not w then return end
	watching[p] = nil
	local root = rootOf(p)
	if root and w.anchored == false then root.Anchored = false end -- (only what we anchored: a lobby plinth stays)
	if p.Parent then
		p:SetAttribute("Watching", nil)
		p:SetAttribute("WatchArena", nil)
		pcall(function() p.ReplicationFocus = nil end)
	end
end

local function watch(p: Player, id: any): any
	if not Spectate.ON then return { ok = false, why = "watching is off" } end
	local info = Matches.watchInfo(tonumber(id) or id)
	if not info then return { ok = false, why = "that match is over" } end
	if info.ranked and not Spectate.RANKED then return { ok = false, why = "ranked matches can't be watched" } end
	if not watching[p] then
		local why = blocked(p)
		if why then return { ok = false, why = why } end
	end
	local root = rootOf(p) :: BasePart
	local w: W? = watching[p]
	if not w then
		local nw: W = { id = info.id, anchored = root.Anchored }
		watching[p] = nw
		w = nw
		root.AssemblyLinearVelocity = Vector3.zero
		root.Anchored = true
	end
	local ww = w :: W
	ww.id = info.id
	p:SetAttribute("WatchArena", info.arena)
	p:SetAttribute("Watching", info.id)
	if info.focus then pcall(function() p.ReplicationFocus = info.focus end) end
	if workspace.StreamingEnabled then task.spawn(function() pcall(function() p:RequestStreamAroundAsync(info.centre, 8) end) end) end
	return { ok = true, watch = { id = info.id, mode = info.mode, arena = info.arena, title = info.title, users = info.users, centre = info.centre } }
end

local function handle(p: Player, op: unknown, a: unknown): any
	if op == "list" then
		local list = Matches.liveInfo()
		for _, m in list do m.watch = Spectate.ON and (not m.ranked or Spectate.RANKED) end
		return { ok = true, matches = list }
	elseif op == "watch" then
		return watch(p, a)
	elseif op == "leave" then
		Spectate.stop(p)
		return { ok = true }
	elseif op == "info" then
		local w = watching[p]
		local info = w and Matches.watchInfo(w.id)
		if not info then return { ok = false } end
		return { ok = true, watch = { id = info.id, mode = info.mode, arena = info.arena, title = info.title, users = info.users, centre = info.centre } }
	end
	return { ok = false }
end

-- the boards: a prompt on each (the client draws the list and opens the WATCH panel on SpectateOpen)
local function board(part: Instance)
	if not part:IsA("BasePart") or part:FindFirstChild("SpectatePrompt") then return end
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "SpectatePrompt"
	pr.ActionText = "Watch"
	pr.ObjectText = "Matches"
	pr.KeyboardKeyCode = Enum.KeyCode.E
	pr.HoldDuration = 0
	pr.MaxActivationDistance = 28 -- (boards hang high: the hubs' about 20 studs over the floor)
	pr.RequiresLineOfSight = false
	pr:SetAttribute("SpectateOpen", true)
	pr.Parent = part
end

function Spectate.init(matches: any, party: any, remotes: Instance)
	Matches, Party = matches, party
	local found = remotes:FindFirstChild("Spectate")
	local fn: RemoteFunction
	if found and found:IsA("RemoteFunction") then fn = found else
		fn = Instance.new("RemoteFunction")
		fn.Name = "Spectate"
		fn.Parent = remotes
	end
	fn.OnServerInvoke = function(p: Player, op: unknown, a: unknown): any
		local ok, res = pcall(handle, p, op, a)
		if not ok then warn("[jankfire] spectate: " .. tostring(res)); return { ok = false, why = "something went wrong" } end
		return res
	end
	-- (the match ended: its watchers stay through a finisher's scene and the end screen, and come back with its players,
	-- when it goes off: the 2 s check below. a new round of the same match is still it)
	-- a new body (respawned, reset): not watching any more
	Players.PlayerAdded:Connect(function(p)
		p.CharacterAdded:Connect(function() if watching[p] then watching[p] = nil; p:SetAttribute("Watching", nil); p:SetAttribute("WatchArena", nil) end end)
	end)
	for _, p in Players:GetPlayers() do
		p.CharacterAdded:Connect(function() if watching[p] then watching[p] = nil; p:SetAttribute("Watching", nil); p:SetAttribute("WatchArena", nil) end end)
	end
	Players.PlayerRemoving:Connect(function(p) watching[p] = nil end)
	for _, part in CollectionService:GetTagged("SpectateBoard") do board(part) end
	CollectionService:GetInstanceAddedSignal("SpectateBoard"):Connect(board)
	-- a match gone without its end (a test stopped it, a site cleared): its watchers come back too
	task.spawn(function()
		while true do
			task.wait(2)
			for p, w in watching do
				if not Matches.watchInfo(w.id) then Spectate.stop(p) end
			end
		end
	end)
	if RunService:IsStudio() then Spectate.watching = watching end
end
Spectate.watching = nil :: any

return Spectate
