--!strict
-- THE HUB EGG (18 Nov 2026). The owner: "Can there be a secret Easter egg hidden somewhere in the hub a backfire
-- manaqueen player?? With the exact crusty look" (backfire: JANKFIRE). Hidden in Hub v3 (the spot is the hub session's
-- nook, PolishBackup.HubEgg.SPOT) stands the web game's player as it was. It is built by the web's own buildCharacter and
-- clothes.js in the default look (Sash + Shorts, pink) on the character screen's plinth, outlined in its colour the
-- way everyone else saw a player (tools/roblox/hub_egg_dump.mjs + hub_egg_mannequin.py; PolishBackup.HubEgg places it).
-- FINDING IT: touch it (walk into it) or use its prompt. The first time, the OG title is yours (CardStyles, rarity
-- "secret": never sold, never rolled, hidden in the card's picker until you have it). It is kept in your loot save
-- (Loot.grant "egg:title:og"; one receipt per player, so it is given once). A small line says so ("NEW TITLE · OG",
-- Hud's small kind) and a short recording plays for you alone. After that the prompt only plays the recording again.
-- The map is data: workspace.Map.Hub.HubEgg (Folder, PolishBackup.HubEgg):
--   Mannequin (Model) the mannequin, its plinth and its outline
--   Touch     (Part, unseen, no collisions) round the plinth: a body part touching it finds it. a ProximityPrompt in it
--   Found     (Sound) in Touch: the recording
-- Nothing happens while the folder isn't there: it looks again every few seconds.
-- HIDDEN UNTIL ITS CODE (18 Nov 2026, lore-npcs, the owner's code panel): the mannequin is hidden for you until you type
-- its code at the code panel (LoreNPCs.server checks it; LoreLife.client hides the mannequin, its outline and its prompt
-- for anyone whose LoreSeen doesn't list "egg"). Touching it or its prompt does nothing until then. The code itself is
-- the find: LoreNPCs calls ServerStorage.HubEggFind (BindableFunction, made here): (player) -> find(player, anywhere).
-- Studio play tests: ServerStorage.HubEggTest (a BindableFunction, Studio only) answers "state" (where it is, the
-- first player's distance, whether their save is ready and whether they own the title) and "find" (the first player
-- finds it now, wherever they stand). To lose the title again in a test, put your loot back with the Loot remote's
-- dev "set" (Studio saves go to the _studio stores).
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local Loot = require(script.Parent:WaitForChild("Loot")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local CalloutR = Remotes:WaitForChild("Callout") :: RemoteEvent

local TYPE, ID = "title", "og"
local OFFER = "egg:" .. TYPE .. ":" .. ID -- (Shared.Shop.offer: a pass, so the loot server's "buy" refuses it)
local NOTE = "NEW TITLE · OG"
local REACH = 12 -- studs from the plinth's middle: a body further off than this isn't touching it
local AGAIN = 2.5 -- seconds between replays of the recording from the prompt
local STUDIO = RunService:IsStudio()

local busy: { [Player]: boolean } = {}
local lastPlay: { [Player]: number } = {}

local function egg(): Folder?
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	local e = hub and hub:FindFirstChild("HubEgg")
	return if e and e:IsA("Folder") then e else nil
end
local function touchOf(e: Folder): BasePart?
	local t = e:FindFirstChild("Touch")
	return if t and t:IsA("BasePart") then t else nil
end
local function rootOf(p: Player): BasePart?
	local ch = p.Character
	local r = ch and ch:FindFirstChild("HumanoidRootPart")
	return if r and r:IsA("BasePart") then r else nil
end
-- has p's code revealed the mannequin? (LoreNPCs' LoreSeen: the server's own attribute)
local function known(p: Player): boolean
	local s = p:GetAttribute("LoreSeen")
	return type(s) == "string" and string.find("," .. s .. ",", ",egg,", 1, true) ~= nil
end
local function near(p: Player, t: BasePart): boolean
	local r = rootOf(p)
	return r ~= nil and (r.Position - t.Position).Magnitude <= REACH
end

-- the recording, on the finder's screen only (a copy in their PlayerGui: nobody else hears it)
local function playFor(p: Player, t: BasePart)
	local s = t:FindFirstChild("Found")
	local pg = p:FindFirstChildOfClass("PlayerGui")
	if not (s and s:IsA("Sound") and pg) then return end
	lastPlay[p] = os.clock()
	local c = s:Clone()
	c.Parent = pg
	c:Play()
	local len = if c.PlaybackRegionsEnabled then c.PlaybackRegion.Max - c.PlaybackRegion.Min else c.TimeLength
	task.delay(math.max(2, len + 0.5), function() c:Destroy() end)
end

-- p found it. -> "found", "owned", "busy", "no egg", "too far", "not saved"
local function find(p: Player, anywhere: boolean?): string
	local e = egg()
	local t = e and touchOf(e)
	if not t then return "no egg" end
	if not anywhere and not near(p, t) then return "too far" end
	if busy[p] then return "busy" end
	if Loot.ready(p) and Loot.owns(p, TYPE, ID) then return "owned" end
	busy[p] = true
	local t0 = os.clock()
	while p.Parent and not Loot.ready(p) and os.clock() - t0 < 20 do task.wait(0.5) end -- (their save is still loading)
	local got = false
	if p.Parent and Loot.ready(p) then
		if Loot.owns(p, TYPE, ID) then
			busy[p] = nil
			return "owned"
		end
		-- (one receipt per player: given once, whatever happens. in Studio a fresh one, so a test can find it again)
		local rid = "hubegg-" .. p.UserId .. (if STUDIO then "-" .. math.floor(os.clock() * 1000) else "")
		local ok, res = pcall(Loot.grant, p, OFFER, rid)
		if not ok then warn("[jankfire] hub egg: Loot.grant: " .. tostring(res)) end
		got = ok and res == true and Loot.owns(p, TYPE, ID)
	end
	if got then
		CalloutR:FireClient(p, NOTE, 2.6)
		playFor(p, t)
		busy[p] = nil
		return "found"
	end
	task.delay(5, function() busy[p] = nil end) -- (not written: a save was down. touching it again tries again)
	return "not saved"
end

-- ------------------------------------------------------------------ wiring (the folder may be built after start)
local wired: { [BasePart]: boolean } = {}
local function wire(t: BasePart)
	if wired[t] then return end
	wired[t] = true
	t.Touched:Connect(function(hit: BasePart)
		local ch = hit.Parent
		local p = ch and Players:GetPlayerFromCharacter(ch)
		if not p or busy[p] or not known(p) then return end
		if Loot.ready(p) and Loot.owns(p, TYPE, ID) then return end
		task.spawn(find, p)
	end)
	local pr = t:FindFirstChildOfClass("ProximityPrompt")
	if pr then
		pr.Triggered:Connect(function(p: Player)
			if not known(p) then return end
			if Loot.ready(p) and Loot.owns(p, TYPE, ID) then
				if near(p, t) and os.clock() - (lastPlay[p] or 0) > AGAIN then playFor(p, t) end
				return
			end
			task.spawn(find, p)
		end)
	end
	t.Destroying:Connect(function() wired[t] = nil end)
end
task.spawn(function()
	while true do
		local e = egg()
		local t = e and touchOf(e)
		if t then wire(t) end
		task.wait(3)
	end
end)
Players.PlayerRemoving:Connect(function(p)
	busy[p] = nil
	lastPlay[p] = nil
end)

-- the code panel's find (LoreNPCs.server, a right code for the mannequin): wherever they stand
do
	local f = ServerStorage:FindFirstChild("HubEggFind") or Instance.new("BindableFunction")
	f.Name = "HubEggFind"
	f.Parent = ServerStorage;
	(f :: BindableFunction).OnInvoke = function(p: any): string
		if typeof(p) ~= "Instance" or not p:IsA("Player") then return "no player" end
		return find(p, true)
	end
end

-- ------------------------------------------------------------------ Studio play tests
if STUDIO then
	local f = ServerStorage:FindFirstChild("HubEggTest") :: BindableFunction?
	if not f then
		local nf = Instance.new("BindableFunction")
		nf.Name = "HubEggTest"
		nf.Parent = ServerStorage
		f = nf
	end
	(f :: BindableFunction).OnInvoke = function(op: any): any
		local p = Players:GetPlayers()[1]
		local e = egg()
		local t = e and touchOf(e)
		if op == "state" then
			local r = p and rootOf(p)
			return {
				egg = e ~= nil, at = if t then tostring(t.Position) else nil,
				player = if p then p.Name else nil,
				dist = if t and r then math.floor((r.Position - t.Position).Magnitude * 10) / 10 else nil,
				ready = if p then Loot.ready(p) else nil,
				owns = if p and Loot.ready(p) then Loot.owns(p, TYPE, ID) else nil,
				wired = if t then wired[t] == true else false,
			}
		elseif op == "find" then
			return if p then find(p, true) else "no player"
		end
		return "state or find"
	end
end
