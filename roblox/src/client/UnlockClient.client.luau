-- your level on the HUD, and the moment it goes up (18 Nov 2026, the owner: "weapons are unlocked via level
-- progression"). docs/PROGRESSION.md.
--   top left: LV n and a thin bar to the next level (Stats' Xp; Ranks.of has the maths). hidden while a menu is up.
--   a level up: a quiet plate at the top in the middle for 5 s, LEVEL n and the weapons that opened on the way
--   (Unlocks.at), with the recorded reward sting. the first level read once your stats load is not a level up.
-- (Studio tests: the LocalPlayer attribute LevelTest = "toast:<from>:<to>" shows that toast)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local me = Players.LocalPlayer
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Ranks = require(Shared:WaitForChild("Ranks")) :: any
local Unlocks = require(Shared:WaitForChild("Unlocks")) :: any
local Roster = require(Shared:WaitForChild("Roster")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any
local okS, Sfx = pcall(function() return require(script.Parent:WaitForChild("Sfx", 10) :: ModuleScript) :: any end)

local gui = T.new("ScreenGui", { Name = "JankLevel", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 7,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, me:WaitForChild("PlayerGui"))
local sc = T.scaled(gui)

-- the chip
-- (27 Nov 2026, the owner's pick, A PLATE: bare on the world, no plate: LV n, a bone bar, the XP to the next level)
local chip = T.new("Frame", { Name = "Level", BackgroundTransparency = 1, Position = UDim2.fromOffset(28, 54), Size = UDim2.fromOffset(260, 30) }, sc)
local lvText = T.text(chip, "Lv", "LV 1", 15, T.TEXT, T.FONT_HEAVY)
lvText.Position = UDim2.fromOffset(0, 0); lvText.Size = UDim2.new(0, 50, 0, 18); lvText.TextStrokeTransparency = 0.75
local track = T.new("Frame", { Name = "Track", BorderSizePixel = 0, BackgroundColor3 = Color3.fromRGB(20, 20, 24), BackgroundTransparency = 0.45,
	Position = UDim2.fromOffset(50, 6), Size = UDim2.fromOffset(120, 6) }, chip)
T.corner(track, 3)
local fill = T.new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = Color3.fromRGB(229, 226, 219), Size = UDim2.fromScale(0, 1) }, track)
T.corner(fill, 3)
local xpText = T.text(chip, "Xp", "", 11, T.TEXT, T.FONT_BOLD)
xpText.Position = UDim2.fromOffset(184, 0); xpText.Size = UDim2.new(0, 90, 0, 18); xpText.TextTransparency = 0.2; xpText.TextStrokeTransparency = 0.8
local function drawChip()
	local r = Ranks.of(me:GetAttribute("Xp"))
	local lv = me:GetAttribute("Level")
	lvText.Text = "LV " .. (if type(lv) == "number" then lv else r.level)
	fill.Size = UDim2.fromScale(r.progress, 1)
	xpText.Text = ("%d / %d XP"):format(r.into, r.need)
	chip.Visible = me:GetAttribute("LoadoutOpen") ~= true and me:GetAttribute("Zone") ~= "match" -- (not mid-match)
end

-- the toast
local toast = T.plate(sc, "LevelUp", UDim2.new(0.5, 0, 0, 104), UDim2.fromOffset(300, 54))
toast.AnchorPoint = Vector2.new(0.5, 0)
toast.Visible = false
local tTitle = T.text(toast, "Title", "", 15, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
tTitle.Position = UDim2.fromOffset(12, 7); tTitle.Size = UDim2.new(1, -24, 0, 20)
local tList = T.text(toast, "List", "", 11, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
tList.Position = UDim2.fromOffset(12, 29); tList.Size = UDim2.new(1, -24, 0, 16)
local tok = 0
local function showToast(from: number, to: number)
	local names = {}
	for l = from + 1, to do
		for _, e in Unlocks.at(l, Roster) do table.insert(names, string.upper(e.name)) end
	end
	tTitle.Text = "LEVEL " .. to
	tList.Text = if #names > 0 then "UNLOCKED  " .. table.concat(names, "  ·  ") else ""
	-- (a long list wraps: about 6 px a letter at 11)
	local w = if #names > 0 then math.clamp(#tList.Text * 6 + 48, 220, 560) else 220
	local lines = if #names > 0 then math.ceil(#tList.Text * 6 / (w - 24)) else 0
	tList.TextWrapped = true
	tList.Size = UDim2.new(1, -24, 0, 14 * lines)
	toast.Size = UDim2.fromOffset(w, 36 + 14 * lines)
	toast.Visible = true
	tok += 1
	local my = tok
	if okS and type(Sfx) == "table" and Sfx.play then pcall(Sfx.play, "loot_win_rare") end
	task.delay(5, function() if tok == my then toast.Visible = false end end)
end

-- a level up is a Level higher than the last one read with your stats loaded
local last: number? = nil
local function onLevel()
	drawChip()
	if me:GetAttribute("StatsSave") == "loading" then return end
	local l = me:GetAttribute("Level")
	if type(l) ~= "number" then return end
	if last and l > last then showToast(last, l) end
	last = l
end
for _, a in { "Level", "Xp", "StatsSave" } do me:GetAttributeChangedSignal(a):Connect(onLevel) end
me:GetAttributeChangedSignal("LoadoutOpen"):Connect(drawChip)
me:GetAttributeChangedSignal("Zone"):Connect(drawChip) -- (hidden mid-match)
onLevel()

me:GetAttributeChangedSignal("LevelTest"):Connect(function()
	local v = me:GetAttribute("LevelTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("LevelTest", nil)
	local a, b = string.match(v, "^toast:(%d+):(%d+)$")
	if a and b then showToast(tonumber(a) :: number, tonumber(b) :: number) end
end)
