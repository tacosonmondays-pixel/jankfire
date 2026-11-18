--!strict
-- PARTY UI: the PARTY panel (17 Nov, the owner: "a party button that displays everyone in the lobby, if you invite
-- them and perhaps even trade and you can view their card"). opened by the PARTY button (under PLAY, key J) in the hub
-- and by PARTY on the Play screen. your party first (LEADER / MEMBER, the leader's LEAD and KICK, VIEW CARD, LEAVE
-- PARTY), then everyone else in this server: their rank badge, INVITE, VIEW CARD (the player-cards session's
-- ProfileUI) and TRADE, a disabled slot until trading is built (its own system, a later session).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme"))
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
local PlayUI = require(script.Parent:WaitForChild("PlayUI"))
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local PlayConfig = require(Shared:WaitForChild("PlayConfig"))
local RankedStyle = require(Shared:WaitForChild("RankedStyle"))

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local new, text = T.new, T.text
local ask, notice = PlayUI.ask, PlayUI.notice

local PartyUI = {}
local S: any = { open = false, list = {}, fake = nil }

local profileUI: any = false
local function viewCard(id: number)
	if id < 0 then notice("a stand-in has no card"); return end -- (Studio tests)
	if profileUI == false then
		profileUI = nil
		local m = script.Parent:FindFirstChild("ProfileUI")
		if m then local ok, r = pcall(require, m); if ok then profileUI = r end end
	end
	if not profileUI then notice("player cards aren't here"); return end
	pcall(profileUI.open, id, "profile")
end
-- TRADE (client/TradeUI.luau, server/Trading.luau: docs/TRADING.md). a live button while trading is open
local tradeUI: any = false
local function trading(): any
	if tradeUI == false then
		tradeUI = nil
		local m = script.Parent:FindFirstChild("TradeUI")
		if m then local ok, r = pcall(require, m); if ok then tradeUI = r end end
	end
	return tradeUI
end

-- ------------------------------------------------------------------ the panel
local gui = new("ScreenGui", { Name = "JankParty", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 22,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, pg)
local scaled = T.scaled(gui)
local shade = new("TextButton", { Name = "Shade", AutoButtonColor = false, Text = "", BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0),
	BackgroundTransparency = 0.45, Size = UDim2.fromScale(1, 1), Modal = true }, scaled) -- (Modal: the mouse is free in first person)
local panel = T.plate(scaled, "Panel", UDim2.fromScale(0.5, 0.5), UDim2.fromOffset(580, 520))
panel.AnchorPoint = Vector2.new(0.5, 0.5)
panel.BackgroundTransparency = 0.08
shade.MouseButton1Click:Connect(function() PartyUI.close() end)

local function button(parent: Instance, name: string, label: string, kind: string, w: number, h: number): TextButton
	-- kind: "accent" | "plain" | "off" (a disabled slot)
	local accent, off = kind == "accent", kind == "off"
	local b = new("TextButton", { Name = name, AutoButtonColor = false, BorderSizePixel = 0, Size = UDim2.fromOffset(w, h),
		BackgroundColor3 = if accent then T.ACCENT else T.CARD_HI, BackgroundTransparency = if off then 0.6 else 0, FontFace = T.FONT_HEAVY,
		TextSize = 11, Text = label, TextColor3 = if accent then T.INK elseif off then T.DIM else T.TEXT, LayoutOrder = 0 }, parent)
	T.corner(b, 5)
	if not accent then T.edge(b, nil, if off then 0.92 else 0.8) end
	if not off then
		b.MouseEnter:Connect(function() b.BackgroundColor3 = if accent then T.ACCENT:Lerp(Color3.new(1, 1, 1), 0.18) else T.CARD_HI:Lerp(Color3.new(1, 1, 1), 0.08) end)
		b.MouseLeave:Connect(function() b.BackgroundColor3 = if accent then T.ACCENT else T.CARD_HI end)
	end
	return b
end

-- REPORT (the anti-cheat's client/ReportUI.luau -> server/Reports.luau): on every row but yours and the stand-ins'
-- (negative ids). no ReportUI in the place: no button, the panel works as before
local function reportButton(parent: Instance, id: number): TextButton?
	-- (Studio layout checks: the LocalPlayer attribute PartyReportTest = true shows it on stand-ins too)
	if id == me.UserId or (id <= 0 and not (RunService:IsStudio() and me:GetAttribute("PartyReportTest") == true)) then return nil end
	local m = script.Parent:FindFirstChild("ReportUI")
	if not m or not m:IsA("ModuleScript") then return nil end
	local b = button(parent, "Report", "REPORT", "plain", 64, 26)
	b.MouseButton1Click:Connect(function()
		local ok, RU = pcall(require, m :: ModuleScript)
		if ok and type(RU) == "table" and type((RU :: any).open) == "function" then (RU :: any).open(id, "party") end
	end)
	return b
end

local thumbs: { [number]: string } = {}
local function headshot(parent: Instance, id: number, name: string, size: number): Frame
	local holder = new("Frame", { Name = "Head", BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Size = UDim2.fromOffset(size, size) }, parent)
	T.corner(holder, size // 2)
	local i = text(holder, "Initial", string.upper(string.sub(name, 1, 1)), math.floor(size * 0.45), T.SOFT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
	i.Size = UDim2.fromScale(1, 1)
	if id > 0 then
		local img = new("ImageLabel", { Name = "Img", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Image = thumbs[id] or "" }, holder)
		T.corner(img, size // 2)
		if not thumbs[id] then
			task.spawn(function()
				local ok, url = pcall(function() return Players:GetUserThumbnailAsync(id, Enum.ThumbnailType.HeadShot, Enum.ThumbnailSize.Size100x100) end)
				if ok and type(url) == "string" then thumbs[id] = url; if img.Parent then img.Image = url end end
			end)
		end
	end
	return holder
end

-- one row: headshot, name, a line under it (tag or rank), the badge, then the buttons from the right
local function row(parent: Instance, y: number, W: number, who: any, line: string, lineColor: Color3, buttons: { TextButton }?): Frame
	local h = 52
	local r = new("Frame", { Name = "Row" .. tostring(who.id), BorderSizePixel = 0, BackgroundColor3 = if who.id == me.UserId then T.CARD_HI else T.CARD,
		BackgroundTransparency = 0.15, Position = UDim2.fromOffset(0, y), Size = UDim2.fromOffset(W, h - 6) }, parent)
	T.corner(r, 5)
	local hs = headshot(r, who.id, who.display or who.name or "?", 34)
	hs.Position = UDim2.fromOffset(7, 6)
	if who.leader then
		local d = new("Frame", { Name = "Lead", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Rotation = 45, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromOffset(38, 9), Size = UDim2.fromOffset(9, 9), ZIndex = 3 }, r)
		T.corner(d, 2)
	end
	-- the buttons take their room first; the badge and the name give way on a row with many (REPORT made four)
	local bw = 0
	for _, b in buttons or {} do bw += b.Size.X.Offset + 6 end
	local left = W - 8 - bw
	local badgeX = math.min(224, left - 40)
	local nameW = math.max(60, math.min(170, (if who.rank then badgeX else left) - 54))
	local nm = text(r, "Name", who.display or who.name or "?", 14, T.TEXT, T.FONT_BOLD)
	nm.Position = UDim2.fromOffset(50, 6); nm.Size = UDim2.fromOffset(nameW, 18); nm.TextTruncate = Enum.TextTruncate.AtEnd
	local ln = text(r, "Line", line, 11, lineColor, T.FONT_BOLD)
	ln.Position = UDim2.fromOffset(50, 25); ln.Size = UDim2.fromOffset(nameW, 14); ln.TextTruncate = Enum.TextTruncate.AtEnd
	if who.rank then
		local b = RankedStyle.badge(r, 34, who.rank)
		b.Position = UDim2.fromOffset(badgeX, 6)
	end
	local x = W - 8
	for _, b in buttons or {} do
		b.Parent = r
		b.AnchorPoint = Vector2.new(1, 0.5)
		b.Position = UDim2.new(0, x, 0.5, 0)
		x -= b.Size.X.Offset + 6
	end
	return r
end

function PartyUI.refresh()
	if not S.open then return end
	for _, c in panel:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	local cam = workspace.CurrentCamera
	local sz = S.fake or (if cam then cam.ViewportSize / T.scaleNow() else Vector2.new(1280, 720))
	local W = math.min(580, sz.X - 24)
	local Hmax = math.min(560, sz.Y - 24)
	local pad = 16
	local inner = W - pad * 2
	local pt = PlayUI.S.party
	local lead = pt ~= nil and pt.leader == me.UserId
	-- the header
	local title = text(panel, "Title", "PARTY", 22, T.TEXT, T.FONT_TITLE)
	title.Position = UDim2.fromOffset(pad, 12); title.Size = UDim2.fromOffset(200, 28)
	local count = text(panel, "Count", ("%d/%d"):format(if pt then #pt.members else 1, PlayConfig.PARTY_MAX), 14, T.MUTED, T.FONT_HEAVY)
	count.Position = UDim2.fromOffset(pad + 96, 19); count.Size = UDim2.fromOffset(60, 18)
	local close = button(panel, "Close", "CLOSE", "plain", 86, 30)
	close.AnchorPoint = Vector2.new(1, 0); close.Position = UDim2.new(1, -pad, 0, 12)
	close.MouseButton1Click:Connect(function() PartyUI.close() end)
	local y = 54
	-- your party
	local h1 = text(panel, "Yours", "YOUR PARTY", 11, T.MUTED, T.FONT_HEAVY)
	h1.Position = UDim2.fromOffset(pad, y); h1.Size = UDim2.fromOffset(200, 14)
	y += 20
	local mine = new("Frame", { Name = "Mine", BackgroundTransparency = 1, Position = UDim2.fromOffset(pad, y), Size = UDim2.fromOffset(inner, 10) }, panel)
	local my = 0
	if pt then
		for _, m in pt.members do
			local bs: { TextButton } = {}
			if m.id ~= me.UserId then
				local vc = button(mine, "Card", "VIEW CARD", "plain", 84, 26)
				vc.MouseButton1Click:Connect(function() viewCard(m.id) end)
				table.insert(bs, vc)
				local rb = reportButton(mine, m.id)
				if rb then table.insert(bs, rb) end
			end
			if lead and m.id ~= me.UserId then
				local k = button(mine, "Kick", "KICK", "plain", 50, 26)
				k.MouseButton1Click:Connect(function() task.spawn(ask, "kick", m.id) end)
				table.insert(bs, k)
				if not m.standIn then
					local l = button(mine, "Lead", "LEAD", "plain", 50, 26)
					l.MouseButton1Click:Connect(function() task.spawn(ask, "promote", m.id) end)
					table.insert(bs, l)
				end
			end
			local where = if m.inMatch then "IN A MATCH" elseif m.inRoom then "IN THE LOBBY" else "IN THE HUB"
			row(mine, my, inner, m, (if m.leader then "LEADER" else "MEMBER") .. "  ·  " .. where, if m.leader then T.ACCENT else T.MUTED, bs)
			my += 52
		end
	else
		local e = text(mine, "Solo", "just you. invite someone below", 12, T.MUTED, T.FONT)
		e.Size = UDim2.fromOffset(inner, 22)
		my += 26
	end
	mine.Size = UDim2.fromOffset(inner, my)
	y += my + 2
	if pt then
		local lv = button(panel, "LeaveParty", "LEAVE PARTY", "plain", 120, 28)
		lv.Position = UDim2.fromOffset(pad, y)
		lv.MouseButton1Click:Connect(function() task.spawn(ask, "leaveparty") end)
		y += 38
	end
	-- everyone else here
	local h2 = text(panel, "Others", "IN THIS SERVER", 11, T.MUTED, T.FONT_HEAVY)
	h2.Position = UDim2.fromOffset(pad, y); h2.Size = UDim2.fromOffset(200, 14)
	y += 20
	local others = {}
	for _, o in S.list do if not o.mine then table.insert(others, o) end end
	local listH = math.max(60, math.min(#others * 52, Hmax - y - pad))
	local sc = new("ScrollingFrame", { Name = "List", BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(pad, y),
		Size = UDim2.fromOffset(inner + 6, listH), CanvasSize = UDim2.fromOffset(0, #others * 52), ScrollBarThickness = 4,
		ScrollBarImageColor3 = T.DIM, ScrollingDirection = Enum.ScrollingDirection.Y }, panel)
	if #others == 0 then
		local e = text(sc, "Empty", "nobody else is in this server yet", 12, T.MUTED, T.FONT)
		e.Size = UDim2.fromOffset(inner, 22)
	end
	for i, o in others do
		local bs: { TextButton } = {}
		local TU = trading()
		local tradeOn = TU ~= nil and TU.on()
		local tr = button(sc, "Trade", "TRADE", if tradeOn then "plain" else "off", 60, 26)
		tr.MouseButton1Click:Connect(function()
			if not tradeOn then notice("trading is not open yet"); return end
			PartyUI.close()
			TU.request(o.id)
		end)
		table.insert(bs, tr)
		local vc = button(sc, "Card", "VIEW CARD", "plain", 84, 26)
		vc.MouseButton1Click:Connect(function() viewCard(o.id) end)
		table.insert(bs, vc)
		local rb = reportButton(sc, o.id)
		if rb then table.insert(bs, rb) end
		local tag = if o.invited then "INVITED" elseif o.inMatch then "IN A MATCH" else nil
		if tag then
			local t = button(sc, "Tag", tag, "off", 74, 26)
			table.insert(bs, t)
		else
			local iv = button(sc, "Invite", "INVITE", "accent", 74, 26)
			iv.MouseButton1Click:Connect(function()
				task.spawn(function()
					local r = ask("invite", o.id)
					if r.ok then o.invited = true; notice("invite sent to " .. (o.display or o.name)); PartyUI.refresh() end
				end)
			end)
			table.insert(bs, iv)
		end
		local line = if o.rank then RankedStyle.label(o.rank) else ""
		if o.party then line = line .. (if line ~= "" then "  ·  " else "") .. "IN A PARTY" end
		row(sc, (i - 1) * 52, inner, o, line, if o.rank then RankedStyle.color(o.rank) else T.MUTED, bs)
	end
	y += listH + pad
	panel.Size = UDim2.fromOffset(W, y)
end

local function fetch()
	local r = ask("players")
	S.list = if r.ok and type(r.list) == "table" then r.list else {}
	PartyUI.refresh()
end

-- ------------------------------------------------------------------ open / close
local saved: any = nil
local function controls(on: boolean)
	pcall(function()
		local c = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		if on then c:Enable() else c:Disable() end
	end)
end
function PartyUI.isOpen(): boolean return S.open end
function PartyUI.open()
	if not require(script.Parent:WaitForChild("MenuGate")).allowed("party") then return end -- (no hub menus in a match or a map room: MenuGate, play-party-ranked's)
	if S.open or me:GetAttribute("Zone") == "match" then return end
	S.open = true
	saved = me:GetAttribute("LoadoutOpen")
	me:SetAttribute("LoadoutOpen", true) -- (a menu is up: hands and movement hold still, the mouse is free)
	if not PlayUI.isOpen() then controls(false) end
	gui.Enabled = true
	MenuCursor.set("party", true, function() return S.open end)
	PartyUI.refresh()
	task.spawn(fetch)
end
function PartyUI.close()
	if not S.open then return end
	S.open = false
	gui.Enabled = false
	MenuCursor.set("party", false)
	if not PlayUI.isOpen() then
		me:SetAttribute("LoadoutOpen", if saved == true then true else false)
		controls(true)
	end
end
function PartyUI.toggle() if S.open then PartyUI.close() else PartyUI.open() end end
function PartyUI.fakeScreen(v: Vector2?) S.fake = v; PartyUI.refresh() end
-- the server pushed a new party view (PlayClient): the list's "in party" marks change too
function PartyUI.changed()
	if S.open then task.spawn(fetch) end
end

RunService.RenderStepped:Connect(function()
	if not S.open then return end
	UIS.MouseBehavior = Enum.MouseBehavior.Default
	if me:GetAttribute("Zone") == "match" then PartyUI.close() end
end)

return PartyUI
