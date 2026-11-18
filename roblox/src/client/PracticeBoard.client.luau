--!strict
-- the practice lane's numbers (18 Nov 2026, the owner: "can the training hub be like the overwatch training one to an
-- extent"): the board on the side hall's deck (Hub.TrainingGround.Practice.Board, TrainingV2) shows, on your screen only,
-- your own hits on the training's dummies: DAMAGE (this burst: hits less than GAP s apart), DPS (that burst's damage over
-- its time, from the second hit on) and TIME TO KILL (from your first hit on a dummy's life to its fall). numbers only;
-- the board's labels are TrainingV2's. the server's Dmg event says who hit what for how much (Fight.hurt)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local me = Players.LocalPlayer
local Dmg = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Dmg") :: RemoteEvent

local GAP = 2
local burst = { t0 = 0, last = -math.huge, dmg = 0 }
local firstHit: { [Instance]: number } = setmetatable({}, { __mode = "k" }) :: any
local shown: { dmg: number, dps: number?, ttk: number? } = { dmg = 0, dps = nil, ttk = nil }

local function boardGui(): Instance?
	local map = workspace:FindFirstChild("Map")
	local hub = map and map:FindFirstChild("Hub")
	local tg = hub and hub:FindFirstChild("TrainingGround")
	local pr = tg and tg:FindFirstChild("Practice")
	local b = pr and pr:FindFirstChild("Board")
	return b and b:FindFirstChild("Gui")
end

local function paint()
	local g = boardGui()
	if not g then return end
	local function set(name: string, text: string)
		local l = g:FindFirstChild(name, true)
		if l and l:IsA("TextLabel") then l.Text = text end
	end
	set("DamageValue", tostring(shown.dmg))
	set("DpsValue", if shown.dps then tostring(shown.dps) else "-")
	set("TtkValue", if shown.ttk then string.format("%.2f s", shown.ttk) else "-")
end

Dmg.OnClientEvent:Connect(function(d: any)
	if type(d) ~= "table" or d.from ~= me.UserId then return end
	local m = d.model
	if typeof(m) ~= "Instance" or not m:GetAttribute("Dummy") then return end
	local now = os.clock()
	local a = tonumber(d.a) or 0
	if now - burst.last > GAP then burst.t0 = now; burst.dmg = 0 end
	burst.dmg += a
	burst.last = now
	shown.dmg = burst.dmg
	local span = now - burst.t0
	shown.dps = if span > 0.05 then math.floor(burst.dmg / span + 0.5) else nil
	if not firstHit[m] then firstHit[m] = now end
	if d.ko then
		shown.ttk = now - firstHit[m]
		firstHit[m] = nil
	end
	paint()
end)

-- (the training ground can be rebuilt or come back after ZoneCull: paint again now and then)
task.spawn(function()
	while true do
		task.wait(3)
		paint()
	end
end)
