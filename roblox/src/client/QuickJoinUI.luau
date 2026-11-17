--!strict
-- QUICK JOIN's pop-up (server/QuickJoin.luau; 17 Nov 2026, the owner: "also when someone steps on a pad, make a pop up
-- to quick join and itll teleport them to one of the pad sides"). the server pushes { t = "quick", id, who, more, mode,
-- party, show, counts, size } and { t = "quickGone", id }; PlayClient hands them here. it sits top centre in the invite
-- toast's look (just under the toast when an invite is up; under the touch buttons' top row on a phone), with a bar
-- that runs out over `show` s.
-- QUICK JOIN: the button (a tap on a phone; a click when the mouse is free) or the key, which is the "quickjoin" bind
-- when the settings page has one, else F. the server moves you onto the pad's side with room.
-- not shown: while a menu is up (LoadoutOpen: shop, loadout, Play screen, party panel), outside the hub zone, or with
-- the setting hud.quickJoin off (Settings > HUD, QUICK JOIN POP-UPS)
--   QuickJoinUI.show(msg) / QuickJoinUI.gone(id) / QuickJoinUI.press() / QuickJoinUI.current()
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local T = require(script.Parent:WaitForChild("Theme"))
local PlayUI = require(script.Parent:WaitForChild("PlayUI"))
local Keys = require(script.Parent:WaitForChild("Keys"))
local Settings = require(script.Parent:WaitForChild("Settings")) :: any
local Binds = require(script.Parent:WaitForChild("Binds")) :: any

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local new, text = T.new, T.text

local QuickJoinUI = {}
local cur: any = nil -- the pop-up up now: the server's message plus at (os.clock when it came)

local gui = new("ScreenGui", { Name = "JankQuick", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 19,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = true }, pg)
local scaled = T.scaled(gui)
local card = T.plate(scaled, "Quick", UDim2.new(0.5, 0, 0, 24), UDim2.fromOffset(440, 78))
card.AnchorPoint = Vector2.new(0.5, 0)
card.Visible = false
do
	local s = card:FindFirstChildOfClass("UIStroke")
	if s then s.Color = T.ACCENT; s.Transparency = 0.5 end
end
local head = text(card, "Head", "", 15, T.TEXT, T.FONT_HEAVY)
head.Position = UDim2.fromOffset(16, 10); head.Size = UDim2.new(1, -176, 0, 20); head.TextTruncate = Enum.TextTruncate.AtEnd
local sub = text(card, "Sub", "", 12, T.MUTED, T.FONT_BOLD)
sub.Position = UDim2.fromOffset(16, 34); sub.Size = UDim2.new(1, -176, 0, 16); sub.TextTruncate = Enum.TextTruncate.AtEnd
local join = new("TextButton", { Name = "Join", AutoButtonColor = false, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0),
	Position = UDim2.new(1, -14, 0, 12), Size = UDim2.fromOffset(144, 40), BackgroundColor3 = T.ACCENT, FontFace = T.FONT_HEAVY,
	TextSize = 13, Text = "QUICK JOIN", TextColor3 = T.INK, TextXAlignment = Enum.TextXAlignment.Left }, card)
T.corner(join, 5)
new("UIPadding", { PaddingLeft = UDim.new(0, 40) }, join)
local function keyName(): string
	if Binds.byId and Binds.byId.quickjoin then
		local ok, l = pcall(Binds.label, "quickjoin")
		if ok and type(l) == "string" and l ~= "" then return l end
	end
	return "F"
end
local cap = T.key(join, keyName(), UDim2.fromOffset(9, 9)) -- (T.key: no cap on a phone, the words centre instead)
join.MouseEnter:Connect(function() join.BackgroundColor3 = T.ACCENT:Lerp(Color3.new(1, 1, 1), 0.18) end)
join.MouseLeave:Connect(function() join.BackgroundColor3 = T.ACCENT end)
local track = new("Frame", { Name = "Track", BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Position = UDim2.new(0, 16, 1, -12),
	Size = UDim2.new(1, -32, 0, 3) }, card)
T.corner(track, 2)
local fill = new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Size = UDim2.fromScale(1, 1) }, track)
T.corner(fill, 2)

local function hide()
	cur = nil
	card.Visible = false
end
local function allowed(): boolean
	if Settings.get("hud.quickJoin") == false then return false end
	if me:GetAttribute("Zone") ~= "hub" or me:GetAttribute("LoadoutOpen") == true or me:GetAttribute("Lobby") ~= nil then return false end
	return true
end

function QuickJoinUI.show(msg: any)
	if type(msg) ~= "table" or type(msg.id) ~= "number" or not allowed() then return end
	cur = { id = msg.id, show = tonumber(msg.show) or 6, at = os.clock() }
	local who = string.upper(tostring(msg.who or "someone"))
	local more = tonumber(msg.more) or 0
	head.Text = if more > 0 then ("%s AND %d MORE WAITING"):format(who, more) else who .. " IS WAITING"
	local open = 0
	for _, n in (if type(msg.counts) == "table" then msg.counts else {}) do open += math.max(0, (tonumber(msg.size) or 1) - n) end
	local party = tonumber(msg.party) or 1
	sub.Text = ("%s  ·  %d %s OPEN%s"):format(tostring(msg.mode or "?"), open, if open == 1 then "SPOT" else "SPOTS",
		if party > 1 then ("  ·  YOUR PARTY OF %d"):format(party) else "")
	local l = cap:FindFirstChild("Letter")
	if l and l:IsA("TextLabel") then l.Text = keyName() end
	fill.Size = UDim2.fromScale(1, 1)
	card.Visible = true
	card.BackgroundTransparency = 1
	T.tween(card, 0.18, { BackgroundTransparency = T.BG_A })
end
function QuickJoinUI.gone(id: any)
	if cur and cur.id == id then hide() end
end
function QuickJoinUI.current(): any return cur end
function QuickJoinUI.press()
	local c = cur
	if not c then return end
	hide()
	task.spawn(function()
		local r = PlayUI.ask("quickjoin", c.id)
		if type(r) == "table" and not r.ok and type(r.why) == "string" then PlayUI.notice(r.why) end
	end)
end

join.MouseButton1Click:Connect(QuickJoinUI.press)
Keys.began(function(io: any, gp: boolean)
	if gp or not cur then return end
	local hit = false
	if Binds.byId and Binds.byId.quickjoin then
		local ok, yes = pcall(Binds.is, "quickjoin", io)
		hit = ok and yes == true
	else
		hit = io.KeyCode == Enum.KeyCode.F
	end
	if hit then QuickJoinUI.press() end
end)

-- the bar runs out; a menu opening, leaving the hub or the setting going off takes it away. under the invite toast
-- when one is up
local inviteF: GuiObject? = nil
RunService.Heartbeat:Connect(function()
	local c = cur
	if not c then return end
	local left = c.show - (os.clock() - c.at)
	if left <= 0 or not allowed() then hide(); return end
	fill.Size = UDim2.fromScale(math.clamp(left / c.show, 0, 1), 1)
	if not inviteF or not inviteF.Parent then
		local play = pg:FindFirstChild("JankPlay")
		local f = play and play:FindFirstChild("Invite", true)
		inviteF = if f and f:IsA("GuiObject") then f else nil
	end
	-- (a phone's touch buttons have a row along the top right, y 12 to 46: the card goes under it there)
	local y = if inviteF and inviteF.Visible then 24 + 78 + 8 elseif Keys.isTouch() then 64 else 24
	if card.Position.Y.Offset ~= y then card.Position = UDim2.new(0.5, 0, 0, y) end
end)

return QuickJoinUI
