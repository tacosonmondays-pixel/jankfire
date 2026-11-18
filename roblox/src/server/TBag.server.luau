--!strict
-- T-BAG (18 Nov 2026, the owner: "bring back tbagging explosion"; the web's crouchTap, player.js:26-52, and room.js
-- case 'tbag'): crouch 14 times within 4 s and your knees explode. You die (your own death, "T-Bag"), and everyone near
-- takes the blast like a frag's: the same falloff, knock, look, sound and close-up shake (the client draws the "boom"
-- the frag sends), the kills yours via T-Bag. From the 9th press your legs glow and throw sparks, getting hotter
-- (TBagHeat on you, 0..1: every client draws it, TBag.client). No text.
--   * the count is the server's: a client only says "I crouched" (TBag remote), counted while you're alive, at most
--     15 a second, and 3 s between two blasts (web), so a script gets nothing a hand doesn't
--   * the blast hurts only who you may hurt (Fight.hurt asks Fight.allow): enemies in a match, the training dummies.
--     in the hub nobody else is touched, but you still blow yourself up (and respawn)
--   * the knock goes through Fight.knock (inside Fight.hurt), so the anti-cheat knows it
-- (the blast is the frag's explode() in Utility.luau, mirrored here: that file had another session's open work)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Items = require(Shared:WaitForChild("Items")) :: any
local Weapons = require(Shared:WaitForChild("Weapons"))
local Fight = require(script.Parent:WaitForChild("Fight")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local ItemFx = Remotes:WaitForChild("ItemFx") :: RemoteEvent
local S = Weapons.S

local remote = Remotes:FindFirstChild("TBag") :: RemoteEvent?
if not remote then
	local r = Instance.new("RemoteEvent")
	r.Name = "TBag"
	r.Parent = Remotes
	remote = r
end

local WINDOW, WARN, BOOM, COOL, MIN_GAP = 4, 9, 14, 3, 1 / 15 -- (web tbagWindow 4000, tbagWarn 9, tbagBoom 14; 3 s room.js)
-- the blast (web room.js: 6 m, 70 * f + 10 damage, a 34 m/s shove + 10 up), in the frag's terms (Utility explode():
-- damage dmg * (0.3 + 0.7 f), shove kb * (0.4 + 0.6 f) out + kbUp * f up)
local BLAST = { radius = 6 * S, dmg = 80, kb = 34 * S, kbUp = 10 * S }

local taps: { [Player]: { number } } = {}
local lastBoom: { [Player]: number } = {}

local function heatOf(n: number): number?
	if n < WARN then return nil end
	return math.min(1, (n - WARN + 1) / (BOOM - WARN + 1))
end
local function setHeat(p: Player, h: number?)
	if p:GetAttribute("TBagHeat") ~= h then p:SetAttribute("TBagHeat", h) end
end

-- the frag's blast: everyone whose centre is in the radius (walls or not, the web rule), hurt by the one who went off
local function blast(at: Vector3, owner: any)
	ItemFx:FireAllClients({ k = "boom", w = "tbag", p = at, r = BLAST.radius })
	for _, t in table.clone(Fight.all) do
		if not t.alive or t == owner then continue end
		local feet = Fight.feet(t)
		if not feet then continue end
		local c = feet + Vector3.new(0, Items.CENTRE, 0)
		local to = c - at
		local dist = to.Magnitude
		if dist > BLAST.radius then continue end
		local f = 1 - dist / BLAST.radius
		local dir = if dist > 0.1 * S then to.Unit else Vector3.yAxis
		local kb = dir * (BLAST.kb * (0.4 + 0.6 * f)) + Vector3.new(0, BLAST.kbUp * f, 0)
		Fight.hurt(t, BLAST.dmg * (0.3 + 0.7 * f), owner, "tbag", false, kb, c)
	end
end

local function boom(p: Player, f: any)
	local feet = Fight.feet(f)
	if not feet then return end
	local at = feet + Vector3.new(0, Items.CENTRE, 0)
	blast(at, f)
	-- and your knees: your own death, the blast flinging you (plain: a dome or a reverse card can't stop your knees)
	Fight.hurt(f, 1e4, nil, "tbag", false, Vector3.new(0, 20 * S, 0), at, nil, true)
end

-- (web: no t-bag sealed in a bubble, in a pop quiz or a cage, nor before a match's round is live)
local function blocked(p: Player): boolean
	if p:GetAttribute("Trap") or p:GetAttribute("Quiz") or p:GetAttribute("Jail") then return true end
	if p:GetAttribute("Arena") ~= nil and (p:GetAttribute("RoundEnds") == nil or p:GetAttribute("LoadoutWindow") ~= nil) then return true end
	return false
end

;(remote :: RemoteEvent).OnServerEvent:Connect(function(p: Player)
	local f = Fight.byPlayer[p]
	if not f or not f.alive or blocked(p) then return end
	local t = os.clock()
	if t - (lastBoom[p] or -math.huge) < COOL then return end
	local list = taps[p]
	if not list then list = {}; taps[p] = list end
	if #list > 0 and t - list[#list] < MIN_GAP then return end
	while #list > 0 and t - list[1] > WINDOW do table.remove(list, 1) end
	table.insert(list, t)
	if #list >= BOOM then
		table.clear(list)
		lastBoom[p] = t
		setHeat(p, nil)
		boom(p, f)
	else
		setHeat(p, heatOf(#list))
	end
end)

-- the heat cools as the presses age out of the window; a death or a new body clears it
task.spawn(function()
	while true do
		task.wait(0.25)
		local t = os.clock()
		for p, list in taps do
			if not p.Parent then taps[p] = nil; continue end
			while #list > 0 and t - list[1] > WINDOW do table.remove(list, 1) end
			local f = Fight.byPlayer[p]
			if not f or not f.alive then table.clear(list) end
			setHeat(p, heatOf(#list))
			if #list == 0 then taps[p] = nil end
		end
	end
end)
Players.PlayerRemoving:Connect(function(p: Player) taps[p] = nil; lastBoom[p] = nil end)
