--!strict
-- ZOMBIES, your side (the server runs the mode: server/Zombies.luau). while you're in a zombies game (attribute ZmOn):
-- your credits with the +N for each hit and kill, the round number and what's left, the break's countdown, your spare
-- rounds, what a buy said, the down screen (bleeding out, with how long), and the end. plain labels only (the owner:
-- no flavour text). the game's state is on the arena model (Round, St, Left, BreakUntil); yours is on you (ZmC, ZmDown,
-- ZmOut, ZmRes_<weapon>, Loadout)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ProximityPromptService = game:GetService("ProximityPromptService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local T = require(script.Parent:WaitForChild("Theme")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local me = Players.LocalPlayer
local W = Weapons.list
local GREEN = Color3.fromHex("8fd14f")

local gui = T.new("ScreenGui", { Name = "JankZombies", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6, Enabled = false }, me:WaitForChild("PlayerGui"))
local root = T.scaled(gui)

-- credits (top left, under the level bar)
local cPlate = T.plate(root, "Credits", UDim2.fromOffset(16, 104), UDim2.fromOffset(170, 44))
local cLabel = T.text(cPlate, "Label", "CREDITS", 12, T.MUTED, T.FONT_BOLD)
cLabel.Position = UDim2.fromOffset(12, 4); cLabel.Size = UDim2.fromOffset(100, 14)
local cNum = T.text(cPlate, "Num", "500", 22, T.ACCENT, T.FONT_HEAVY)
cNum.Position = UDim2.fromOffset(12, 17); cNum.Size = UDim2.fromOffset(150, 24)
local pops = T.new("Frame", { Name = "Pops", BackgroundTransparency = 1, Position = UDim2.fromOffset(192, 104), Size = UDim2.fromOffset(120, 44) }, root)

-- the round (bottom left, over the HP card): the number, what's left
local rPlate = T.plate(root, "Round", UDim2.new(0, 16, 1, -206), UDim2.fromOffset(170, 66))
local rLabel = T.text(rPlate, "Label", "ROUND", 12, T.MUTED, T.FONT_BOLD)
rLabel.Position = UDim2.fromOffset(12, 6); rLabel.Size = UDim2.fromOffset(80, 14)
local rNum = T.text(rPlate, "Num", "0", 34, Color3.fromHex("ff5a3a"), T.FONT_TITLE)
rNum.Position = UDim2.fromOffset(12, 20); rNum.Size = UDim2.fromOffset(70, 40)
local rLeft = T.text(rPlate, "Left", "", 13, T.SOFT, T.FONT, Enum.TextXAlignment.Right)
rLeft.Position = UDim2.fromOffset(80, 36); rLeft.Size = UDim2.fromOffset(80, 18)

-- your spare rounds (bottom right, over the ammo card)
local aPlate = T.plate(root, "Spare", UDim2.new(1, -260, 1, -196), UDim2.fromOffset(244, 30)) -- (over the item card)
local aText = T.text(aPlate, "Text", "", 13, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Right)
aText.Position = UDim2.fromOffset(10, 0); aText.Size = UDim2.new(1, -20, 1, 0)

-- the middle: a banner (ROUND 3, the break's countdown), what a buy said
local banner = T.text(root, "Banner", "", 34, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
banner.AnchorPoint = Vector2.new(0.5, 0); banner.Position = UDim2.new(0.5, 0, 0, 120); banner.Size = UDim2.fromOffset(600, 44)
local sub = T.text(root, "Sub", "", 16, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
sub.AnchorPoint = Vector2.new(0.5, 0); sub.Position = UDim2.new(0.5, 0, 0, 164); sub.Size = UDim2.fromOffset(600, 22)
local toast = T.text(root, "Toast", "", 15, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
toast.AnchorPoint = Vector2.new(0.5, 0); toast.Position = UDim2.new(0.5, 0, 0.5, 46); toast.Size = UDim2.fromOffset(500, 20)
local toastT = 0
local bannerT = 0

-- down: a red edge, how long you have
local downF = T.new("Frame", { Name = "Down", BackgroundColor3 = Color3.fromRGB(120, 0, 0), BackgroundTransparency = 0.65, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), Visible = false }, gui)
local downT = T.text(downF, "Text", "DOWN", 40, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
downT.AnchorPoint = Vector2.new(0.5, 0.5); downT.Position = UDim2.fromScale(0.5, 0.42); downT.Size = UDim2.fromOffset(600, 50)
local downS = T.text(downF, "Sub", "", 18, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
downS.AnchorPoint = Vector2.new(0.5, 0.5); downS.Position = UDim2.fromScale(0.5, 0.42 + 0.06); downS.Size = UDim2.fromOffset(600, 24)

-- the end: how far the squad got, everyone's numbers
local over = T.plate(root, "Over", UDim2.new(0.5, -260, 0.5, -150), UDim2.fromOffset(520, 300))
over.Visible = false
over.AnchorPoint = Vector2.new(0, 0)
local oTitle = T.text(over, "Title", "", 28, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center)
oTitle.Position = UDim2.fromOffset(0, 14); oTitle.Size = UDim2.new(1, 0, 0, 34)
local oRows = T.new("Frame", { Name = "Rows", BackgroundTransparency = 1, Position = UDim2.fromOffset(20, 62), Size = UDim2.new(1, -40, 1, -76) }, over)
T.new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, oRows)

local function arena(): Instance?
	local n = me:GetAttribute("ZmArena")
	return if type(n) == "string" then workspace:FindFirstChild(n) else nil
end
local function pop(d: number, why: string)
	local col = if d < 0 then T.DANGER elseif why == "head" or why == "melee" then T.ACCENT else GREEN
	local l = T.text(pops, "Pop", (if d > 0 then "+" else "") .. tostring(d), 16, col, T.FONT_HEAVY, Enum.TextXAlignment.Left, true)
	l.Position = UDim2.fromOffset(0, 12); l.Size = UDim2.fromOffset(120, 20)
	T.tween(l, 0.9, { Position = UDim2.fromOffset(0, -10), TextTransparency = 1, TextStrokeTransparency = 1 })
	task.delay(1, function() l:Destroy() end)
end
local function say(text: string, ok: boolean?)
	toast.Text = text
	toast.TextColor3 = if ok == false then T.DANGER else T.TEXT
	toastT = os.clock() + 1.8
end
local function show(text: string, s: string?, dur: number?)
	banner.Text = text
	sub.Text = s or ""
	bannerT = os.clock() + (dur or 2.5)
end
local function row(cells: { string }, bold: boolean, order: number)
	local f = T.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 22), LayoutOrder = order }, oRows)
	local xs = { 0, 0.42, 0.55, 0.68, 0.81 }
	for i, c in cells do
		local l = T.text(f, "C" .. i, c, 14, if bold then T.MUTED else T.TEXT, if bold then T.FONT_BOLD else T.FONT, if i == 1 then Enum.TextXAlignment.Left else Enum.TextXAlignment.Right)
		l.Position = UDim2.fromScale(xs[i], 0)
		l.Size = UDim2.new(if i == 1 then 0.4 else 0.12, 0, 1, 0)
	end
end

local zr = Remotes:WaitForChild("Zm") :: RemoteEvent
zr.OnClientEvent:Connect(function(x: any)
	if type(x) ~= "table" then return end
	if x.k == "c" then
		cNum.Text = tostring(x.c)
		if type(x.d) == "number" and x.d ~= 0 and x.why ~= "test" then pop(x.d, tostring(x.why)) end
	elseif x.k == "buy" then
		say(tostring(x.m or ""), x.ok == true)
	elseif x.k == "round" then
		if x.st == "start" then show("ROUND " .. tostring(x.n), nil, 3) else show("ROUND " .. tostring(x.n) .. " CLEARED", nil, 3) end
	elseif x.k == "door" then
		say(if x.by then tostring(x.by) .. " opened " .. tostring(x.label) else tostring(x.label) .. " open", true)
	elseif x.k == "down" then
		if x.st == "down" then say(tostring(x.who) .. " is down", false)
		elseif x.st == "up" then say(tostring(x.who) .. " is back up", true)
		elseif x.st == "out" then say(tostring(x.who) .. " is out", false) end
	elseif x.k == "over" then
		for _, c in oRows:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
		oTitle.Text = "GAME OVER  ·  ROUND " .. tostring(x.n)
		row({ "PLAYER", "KILLS", "HEADS", "DOWNS", "REVIVES" }, true, 0)
		for i, r in (x.rows or {}) :: { any } do row({ tostring(r[1]), tostring(r[2]), tostring(r[3]), tostring(r[4]), tostring(r[5]) }, false, i) end
		over.Visible = true
	end
end)

-- your own revive prompt is for the others
ProximityPromptService.PromptShown:Connect(function(pr: ProximityPrompt)
	if pr:GetAttribute("Downed") == me.UserId then pr.Enabled = false end
end)

RunService.RenderStepped:Connect(function()
	local on = me:GetAttribute("ZmOn") == true
	if gui.Enabled ~= on then
		gui.Enabled = on
		if not on then over.Visible = false; banner.Text = ""; toast.Text = "" end
	end
	if not on then return end
	local a = arena()
	local st = a and a:GetAttribute("St")
	rNum.Text = tostring(a and a:GetAttribute("Round") or 0)
	local left = a and a:GetAttribute("Left")
	rLeft.Text = if st == "live" and type(left) == "number" then left .. " left" else ""
	local bu = a and a:GetAttribute("BreakUntil")
	if type(bu) == "number" and (st == "pre" or st == "break") then
		local s = math.max(0, math.ceil(bu - workspace:GetServerTimeNow()))
		banner.Text = "ROUND " .. tostring((tonumber(a and a:GetAttribute("Round")) or 0) + 1)
		sub.Text = "in " .. s
		bannerT = os.clock() + 0.2
	end
	if os.clock() > bannerT then banner.Text = ""; sub.Text = "" end
	if os.clock() > toastT then toast.Text = "" end
	local c = me:GetAttribute("ZmC")
	if type(c) == "number" then cNum.Text = tostring(c) end
	-- spare rounds, gun by gun (in your keys' order)
	local lo = me:GetAttribute("Loadout")
	local bits = {}
	if type(lo) == "string" then
		for _, wid in string.split(lo, ",") do
			local r = me:GetAttribute("ZmRes_" .. wid)
			if type(r) == "number" then table.insert(bits, ((W[wid] and W[wid].name) or wid) .. "  +" .. r) end
		end
	end
	aText.Text = table.concat(bits, "     ")
	aPlate.Visible = #bits > 0
	-- down
	local dn = me:GetAttribute("ZmDown")
	local out = me:GetAttribute("ZmOut") == true
	downF.Visible = (type(dn) == "number" or out) and not over.Visible -- (the results take over at the end)
	if type(dn) == "number" then
		downT.Text = "DOWN"
		downS.Text = "bleeding out  " .. math.max(0, math.ceil(dn - workspace:GetServerTimeNow()))
	elseif out then
		downT.Text = "OUT"
		downS.Text = "back next round"
	end
end)
