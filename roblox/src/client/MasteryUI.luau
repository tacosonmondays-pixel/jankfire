--!strict
-- WEAPON MASTERY's bars (Shared.Mastery; docs/MASTERY.md): what a weapon's level looks like on screen.
--   panel(info, words): one slim bar on the loadout's weapon card (the info panel, under its name): LV n, the XP into
--     the level and what it takes, and the next camo as a small locked swatch with its level. LoadoutUI calls it once
--     and calls the setter it returns with the focused weapon on every refresh
--   card(btn, entry): LV n and a hairline bar along the bottom of an armory card. LoadoutUI calls it for each card
--   paint(chip, camoId): a camo's swatch on a frame (its picture once the wraps session's art is in, else its colours);
--     MasteryClient uses it on the unlock toast
-- they all read the player attribute Mastery (XP per weapon) and redraw when it changes. nothing here takes input: a
-- pad's selection, a click or a tap goes through to what's under it
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local M = require(Shared:WaitForChild("Mastery")) :: any
local Roster = require(Shared:WaitForChild("Roster")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any

local me = Players.LocalPlayer
local MUI = {}

local function new(class: string, props: { [string]: any }, parent: Instance?): any
	local o = Instance.new(class)
	for k, v in props do (o :: any)[k] = v end
	if parent then o.Parent = parent end
	return o
end
local function text(parent: Instance, name: string, s: string, size: number, color: Color3, font: Font, align: Enum.TextXAlignment?): TextLabel
	return new("TextLabel", { Name = name, BackgroundTransparency = 1, Text = s, TextSize = size, TextColor3 = color, FontFace = font,
		TextXAlignment = align or Enum.TextXAlignment.Left, TextYAlignment = Enum.TextYAlignment.Center, TextWrapped = false, Active = false }, parent)
end
-- 12,345
function MUI.num(n: number): string
	local s = tostring(math.floor(n))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	return (out:gsub("^,", ""))
end

-- a camo's swatch: its picture (the wraps session's JankfireWraps.<id>, attribute Swatch) or its colours
function MUI.paint(chip: Frame, id: string)
	for _, d in chip:GetChildren() do if d:IsA("UIGradient") or d.Name == "Pic" then d:Destroy() end end
	local wr = Roster.wrapById[id]
	local lib = ReplicatedStorage:FindFirstChild("JankfireWraps")
	local sa = lib and lib:FindFirstChild(id)
	local img = sa and sa:GetAttribute("Swatch")
	if type(img) == "string" then
		chip.BackgroundColor3 = Color3.new(1, 1, 1)
		local im = new("ImageLabel", { Name = "Pic", Image = img, BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1),
			ImageRectSize = Vector2.new(384, 256), ZIndex = chip.ZIndex }, chip)
		T.corner(im, 3)
		return
	end
	local pal = if wr then wr.pal else {}
	if #pal == 0 then chip.BackgroundColor3 = T.TRACK; return end
	chip.BackgroundColor3 = Color3.new(1, 1, 1)
	local kp = {}
	for i, c in pal do table.insert(kp, ColorSequenceKeypoint.new(if #pal == 1 then 0 else (i - 1) / (#pal - 1), c)) end
	if #pal == 1 then table.insert(kp, ColorSequenceKeypoint.new(1, pal[1])) end
	new("UIGradient", { Rotation = 35, Color = ColorSequence.new(kp) }, chip)
end

local function xpMap(): { [string]: number } return M.decode(me:GetAttribute("Mastery")) end

-- ------------------------------------------------------------------ the weapon card's bar
function MUI.panel(info: Frame, words: Frame?): (any) -> ()
	-- (room for it under the name and chips: the words column moves down 34 and its gaps close from 18 to 12, so its
	-- five gaps give the room back and its bottom stays where it was)
	if words then
		words.Position = words.Position + UDim2.fromOffset(0, 34)
		local lay = words:FindFirstChildOfClass("UIListLayout")
		if lay then lay.Padding = UDim.new(0, 12) end
	end
	local box = new("Frame", { Name = "Mastery", BackgroundTransparency = 1, Position = UDim2.fromOffset(22, 108), Size = UDim2.fromOffset(376, 34), Active = false }, info)
	local lv = text(box, "Level", "", 15, T.TEXT, T.FONT_HEAVY)
	lv.Position = UDim2.fromOffset(0, 0); lv.Size = UDim2.fromOffset(64, 20)
	local xp = text(box, "Xp", "", 13, T.MUTED, T.FONT_BOLD)
	xp.Position = UDim2.fromOffset(64, 0); xp.Size = UDim2.fromOffset(170, 20)
	-- the next camo: a small swatch, dimmed, a lock over it, and its name and level beside
	local nextL = text(box, "Next", "", 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
	nextL.Position = UDim2.fromOffset(176, 0); nextL.Size = UDim2.fromOffset(160, 20)
	local chip = new("Frame", { Name = "Camo", BorderSizePixel = 0, Position = UDim2.fromOffset(342, 0), Size = UDim2.fromOffset(34, 20), Active = false }, box)
	T.corner(chip, 3)
	T.edge(chip, nil, 0.75)
	local shade = new("Frame", { Name = "Shade", BackgroundColor3 = Color3.fromRGB(8, 9, 12), BackgroundTransparency = 0.45, BorderSizePixel = 0,
		Size = UDim2.fromScale(1, 1), ZIndex = 3 }, chip)
	T.corner(shade, 3)
	local lock = text(shade, "Lock", "\u{1F512}", 11, Color3.new(1, 1, 1), T.FONT_BOLD, Enum.TextXAlignment.Center)
	lock.Size = UDim2.fromScale(1, 1); lock.ZIndex = 4
	local track = new("Frame", { Name = "Track", BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 26), Size = UDim2.new(1, 0, 0, 4) }, box)
	T.corner(track, 2)
	local fill = new("Frame", { Name = "Fill", BackgroundColor3 = T.TEXT, BorderSizePixel = 0, Size = UDim2.fromScale(0, 1) }, track)
	T.corner(fill, 2)
	local cur: any = nil
	local shownCamo = ""
	local function draw()
		local e = cur
		box.Visible = e ~= nil and e.live == true
		if not box.Visible then return end
		local level, into, need, frac = M.progress(xpMap()[e.id] or 0)
		lv.Text = "LV " .. level
		xp.Text = if level >= M.MAX then "MAX" else ("%s / %s XP"):format(MUI.num(into), MUI.num(need))
		fill.Size = UDim2.fromScale(frac, 1)
		fill.BackgroundColor3 = if level >= M.MAX then T.ACCENT else T.TEXT
		local nc = M.nextLive(level)
		chip.Visible = nc ~= nil
		nextL.Visible = nc ~= nil
		if nc then
			nextL.Text = ("%s AT LV %d"):format(nc.name, nc.level)
			if shownCamo ~= nc.id then shownCamo = nc.id; MUI.paint(chip, nc.id) end
		end
	end
	me:GetAttributeChangedSignal("Mastery"):Connect(draw)
	ReplicatedStorage:GetAttributeChangedSignal("MasteryLive"):Connect(draw)
	return function(e: any)
		cur = e
		draw()
	end
end

-- ------------------------------------------------------------------ the armory cards
type CardBar = { btn: GuiObject, id: string, lv: TextLabel, fill: Frame }
local cards: { CardBar } = {}
local function drawCards()
	local map = xpMap()
	for i = #cards, 1, -1 do
		local c = cards[i]
		if not c.btn.Parent then table.remove(cards, i); continue end
		local level, _, _, frac = M.progress(map[c.id] or 0)
		c.lv.Text = "LV " .. level
		c.lv.TextColor3 = if level >= M.MAX then T.ACCENT elseif level > 1 then T.SOFT else T.DIM
		c.fill.Size = UDim2.fromScale(frac, 1)
		c.fill.BackgroundColor3 = if level >= M.MAX then T.ACCENT else T.MUTED
	end
end
function MUI.card(btn: GuiObject, e: any)
	if not e or not e.live then return end
	local z = btn.ZIndex + 1
	local track = new("Frame", { Name = "MasteryTrack", BackgroundColor3 = T.TRACK, BackgroundTransparency = 0.2, BorderSizePixel = 0,
		Position = UDim2.fromOffset(26, 75), Size = UDim2.fromOffset(150, 3), ZIndex = z, Active = false }, btn)
	T.corner(track, 2)
	local fill = new("Frame", { Name = "Fill", BackgroundColor3 = T.MUTED, BorderSizePixel = 0, Size = UDim2.fromScale(0, 1), ZIndex = z }, track)
	T.corner(fill, 2)
	local lv = text(btn, "MasteryLevel", "", 12, T.DIM, T.FONT_BOLD, Enum.TextXAlignment.Right)
	lv.Position = UDim2.fromOffset(180, 69); lv.Size = UDim2.fromOffset(42, 14); lv.ZIndex = z
	table.insert(cards, { btn = btn, id = e.id, lv = lv, fill = fill })
	drawCards()
end
me:GetAttributeChangedSignal("Mastery"):Connect(drawCards)

return MUI
