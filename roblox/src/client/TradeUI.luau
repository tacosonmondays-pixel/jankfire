--!strict
-- TRADE: the trade window, the request pop-up and the TRADES history (roblox/docs/TRADING.md; 18 Nov 2026, the owner:
-- "we need trading"). the server decides everything (server/Trading.luau); this draws it and sends the buttons.
--   * the window: YOUR THINGS (the picker: everything you own, what can't go marked NOT TRADEABLE and why), YOU GIVE,
--     <NAME> GIVES, each side's LOCKED / CONFIRMED mark, and the big button: LOCK, UNLOCK, then (both locked) the FINAL
--     LOOK with CONFIRM after a 3 s count, WAITING once you have. a phone shows the picker and the trade as two tabs
--   * the pop-up: <NAME> WANTS TO TRADE, ACCEPT / DECLINE, the time left as a bar
--   * TRADES: your last 50 trades (from your save), opened from your own card (ProfileUI) or TradeUI.history()
-- short labels only. a controller: PadNav moves through the buttons (Pad.MENUS.trade / tradehistory, the pop-up on
-- VIEW); B backs out (the picker tab on a phone, else CANCEL). MenuGate keeps it in the hub.
-- Studio: the LocalPlayer attribute TradeTest ("open" / "history" / "close" / "fake:844x390" / "real") and TradeUI.S
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme")) :: any
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local LootTable = require(Shared:WaitForChild("LootTable")) :: any
local TradeRules = require(Shared:WaitForChild("TradeRules")) :: any

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local new, text = T.new, T.text
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local Remote = Remotes:WaitForChild("Trade") :: RemoteFunction

local TradeUI = {}
local S: any = { open = false, hist = false, state = nil, view = nil, filter = "all", tab = "trade", asks = {}, fake = nil, list = nil }
TradeUI.S = S

local playUI: any = false
local function notice(s: string)
	if playUI == false then
		playUI = nil
		local m = script.Parent:FindFirstChild("PlayUI")
		if m then local ok, r = pcall(require, m); if ok then playUI = r end end
	end
	if playUI and playUI.notice then pcall(playUI.notice, s) end
end
local function ask(op: string, ...: any): any
	local ok, r = pcall(function(...) return Remote:InvokeServer(op, ...) end, ...)
	if not ok or type(r) ~= "table" then return { ok = false, why = "NO ANSWER" } end
	if not r.ok and type(r.why) == "string" and op ~= "state" and op ~= "history" then notice(string.lower(r.why)) end
	return r
end
function TradeUI.on(): boolean return Remote:GetAttribute("On") == true end
local function gateOk(): boolean
	local m = script.Parent:FindFirstChild("MenuGate")
	if not m then return true end
	local ok, G = pcall(require, m)
	return not ok or (G :: any).allowed("trade")
end
local function rcol(r: string): Color3
	local x = LootTable.RARITY[r]
	return if x then x.color else T.DIM
end

-- ------------------------------------------------------------------ bits
local function button(parent: Instance, name: string, label: string, kind: string, w: number, h: number): TextButton
	-- kind: "accent" | "plain" | "off"
	local accent, off = kind == "accent", kind == "off"
	local b = new("TextButton", { Name = name, AutoButtonColor = false, BorderSizePixel = 0, Size = UDim2.fromOffset(w, h),
		BackgroundColor3 = if accent then T.ACCENT else T.CARD_HI, BackgroundTransparency = if off then 0.6 else 0, FontFace = T.FONT_HEAVY,
		TextSize = if h >= 40 then 16 else 12, Text = label, TextColor3 = if accent then T.INK elseif off then T.DIM else T.TEXT }, parent)
	T.corner(b, 5)
	if not accent then T.edge(b, nil, if off then 0.92 else 0.8) end
	if not off then
		b.MouseEnter:Connect(function() b.BackgroundColor3 = if accent then T.ACCENT:Lerp(Color3.new(1, 1, 1), 0.18) else T.CARD_HI:Lerp(Color3.new(1, 1, 1), 0.08) end)
		b.MouseLeave:Connect(function() b.BackgroundColor3 = if accent then T.ACCENT else T.CARD_HI end)
	end
	return b
end
local function at(o: GuiObject, x: number, y: number, w: number, h: number)
	o.Position = UDim2.fromOffset(x, y); o.Size = UDim2.fromOffset(w, h)
end
local KIND_NAMES = { crate = "CRATE", bag = "DUFFEL BAG", spray = "SPRAY CAN" }
local KIND_PLURAL = { crate = "CRATES", bag = "DUFFEL BAGS", spray = "SPRAY CANS" }
for _, k in TradeRules.KINDS do -- (the spray sets, 20 Nov: their names from the loot module)
	local c = LootTable.CONTAINERS[k]
	if c and not KIND_NAMES[k] then KIND_NAMES[k] = string.upper(c.name); KIND_PLURAL[k] = string.upper(c.plural) end
end
local function stockLine(stock: any): string
	local parts = {}
	for _, k in TradeRules.KINDS do
		local n = tonumber(stock and stock[k]) or 0
		if n > 0 then table.insert(parts, ("%d %s"):format(n, if n == 1 then KIND_NAMES[k] else KIND_PLURAL[k])) end
	end
	return table.concat(parts, "  ·  ")
end
-- one item: a rarity bar, its name, "Wrap · Assault Rifle" (or why it can't go)
local function itemCard(parent: Instance, c: any, w: number, h: number, state: string?): TextButton
	-- state: nil | "in" (already in your offer) | "no" (not tradeable)
	local no = state == "no"
	local b = new("TextButton", { Name = "Item_" .. tostring(c.t) .. "_" .. tostring(c.k), AutoButtonColor = false, BorderSizePixel = 0, Text = "",
		BackgroundColor3 = T.CARD, BackgroundTransparency = if no then 0.55 else 0.1, Size = UDim2.fromOffset(w, h) }, parent)
	T.corner(b, 5)
	if state == "in" then T.edge(b, T.ACCENT, 0.35, 1) end
	local bar = new("Frame", { Name = "Rarity", BorderSizePixel = 0, BackgroundColor3 = rcol(c.rarity), BackgroundTransparency = if no then 0.6 else 0,
		Position = UDim2.fromOffset(0, 6), Size = UDim2.new(0, 3, 1, -12) }, b)
	T.corner(bar, 2)
	local nm = text(b, "Name", c.name or "?", if h >= 44 then 13 else 12, if no then T.DIM else T.TEXT, T.FONT_BOLD)
	at(nm, 10, 5, w - 16, 16); nm.TextTruncate = Enum.TextTruncate.AtEnd
	local sub = if no then ("NOT TRADEABLE  ·  %s"):format(c.no or "") else (tostring(c.type or c.t) .. (if c.gun then "  ·  " .. c.gun else ""))
	if state == "in" then sub = "IN THE TRADE" end
	local s2 = text(b, "Sub", sub, 10, if no then T.DIM elseif state == "in" then T.ACCENT else T.MUTED, T.FONT_BOLD)
	at(s2, 10, h - 18, w - 16, 13); s2.TextTruncate = Enum.TextTruncate.AtEnd
	return b
end

-- ------------------------------------------------------------------ the window
local gui = new("ScreenGui", { Name = "JankTrade", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 24,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, pg)
local scaled = T.scaled(gui)
new("TextButton", { Name = "Shade", AutoButtonColor = false, Text = "", BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0),
	BackgroundTransparency = 0.45, Size = UDim2.fromScale(1, 1), Modal = true, Selectable = false }, scaled)
local panel = T.plate(scaled, "Panel", UDim2.fromScale(0.5, 0.5), UDim2.fromOffset(880, 560))
panel.AnchorPoint = Vector2.new(0.5, 0.5)
panel.BackgroundTransparency = 0.06

local FILTERS = { { "all", "ALL" }, { "wrap", "WRAPS" }, { "hat", "HATS" }, { "skin", "SKINS" }, { "flair", "FLAIR" }, { "card", "CARD" }, { "boxes", "BOXES" } }
local FILTER_TYPES = { flair = { kill = true, emote = true }, card = { border = true, banner = true, title = true } }
local function inFilter(c: any): boolean
	local f = S.filter
	if f == "all" then return true end
	local set = FILTER_TYPES[f]
	if set then return set[c.t] == true end
	return c.t == f
end
local function offered(t: string, k: string): boolean
	local v = S.view
	if not v then return false end
	for _, it in v.me.items do if it.t == t and it.k == k then return true end end
	return false
end

-- the picker: filters, then your things (BOXES: the containers with - / +)
local function picker(parent: Instance, x: number, y: number, w: number, h: number)
	local hd = text(parent, "YoursHead", "YOUR THINGS", 11, T.MUTED, T.FONT_HEAVY)
	at(hd, x, y, w, 14)
	y += 20
	local fx = x
	local fw = math.floor((w - 6 * 4) / #FILTERS)
	for _, f in FILTERS do
		local b = button(parent, "Filter_" .. f[1], f[2], if S.filter == f[1] then "accent" else "plain", fw, 26)
		b.TextSize = 10
		b.Position = UDim2.fromOffset(fx, y)
		b.MouseButton1Click:Connect(function() S.filter = f[1]; TradeUI.refresh() end)
		fx += fw + 4
	end
	y += 34
	local sc = new("ScrollingFrame", { Name = "Picker", BackgroundTransparency = 1, BorderSizePixel = 0, ScrollBarThickness = 4,
		ScrollBarImageColor3 = T.DIM, ScrollingDirection = Enum.ScrollingDirection.Y, CanvasSize = UDim2.new() }, parent)
	at(sc, x, y, w + 6, math.max(60, h - 54))
	local st = S.state
	local cy = 0
	if S.filter == "boxes" or S.filter == "all" then
		for _, kind in TradeRules.KINDS do
			local have = tonumber(st and st.stock and st.stock[kind]) or 0
			if have <= 0 and S.filter == "all" then continue end
			local put = tonumber(S.view and S.view.me.stock[kind]) or 0
			local row = new("Frame", { Name = "Box_" .. kind, BorderSizePixel = 0, BackgroundColor3 = T.CARD, BackgroundTransparency = 0.1 }, sc)
			at(row, 0, cy, w, 40)
			T.corner(row, 5)
			local l = text(row, "Name", KIND_PLURAL[kind], 13, if have > 0 then T.TEXT else T.DIM, T.FONT_BOLD)
			at(l, 10, 4, w - 140, 16)
			local l2 = text(row, "Have", ("%d OWNED  ·  %d IN THE TRADE"):format(have, put), 10, T.MUTED, T.FONT_BOLD)
			at(l2, 10, 22, w - 140, 13)
			local minus = button(row, "Minus", "-", if put > 0 then "plain" else "off", 30, 28)
			minus.Position = UDim2.fromOffset(w - 104, 6)
			local num = text(row, "N", tostring(put), 14, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
			at(num, w - 70, 6, 30, 28)
			local plus = button(row, "Plus", "+", if put < have then "plain" else "off", 30, 28)
			plus.Position = UDim2.fromOffset(w - 38, 6)
			minus.MouseButton1Click:Connect(function() if put > 0 then task.spawn(ask, "stock", kind, put - 1) end end)
			plus.MouseButton1Click:Connect(function() if put < have then task.spawn(ask, "stock", kind, put + 1) end end)
			cy += 46
		end
	end
	if S.filter ~= "boxes" then
		local cols = if w >= 330 then 2 else 1
		local cw = math.floor((w - (cols - 1) * 6) / cols)
		local i = 0
		for _, c in (st and st.inv or {}) do
			if not inFilter(c) then continue end
			local isIn = offered(c.t, c.k)
			local b = itemCard(sc, c, cw, 44, if c.no then "no" elseif isIn then "in" else nil)
			b.Position = UDim2.fromOffset((i % cols) * (cw + 6), cy + (i // cols) * 50)
			b.MouseButton1Click:Connect(function()
				if c.no then notice("not tradeable: " .. string.lower(c.no)); return end
				task.spawn(ask, if isIn then "remove" else "add", c.t, c.k)
			end)
			i += 1
		end
		cy += math.ceil(i / cols) * 50
		if i == 0 and cy == 0 then
			local e = text(sc, "Empty", "nothing here", 12, T.MUTED, T.FONT)
			at(e, 0, 0, w, 22)
			cy = 24
		end
	end
	sc.CanvasSize = UDim2.fromOffset(0, cy)
end

-- one side's offer: its head (YOU GIVE / NAME GIVES, LOCKED / CONFIRMED), its items, its containers
local function offerBox(parent: Instance, x: number, y: number, w: number, h: number, o: any, title: string, mine: boolean): number
	local box = new("Frame", { Name = if mine then "Mine" else "Theirs", BorderSizePixel = 0, BackgroundColor3 = T.BG, BackgroundTransparency = 0.35 }, parent)
	at(box, x, y, w, h)
	T.corner(box, 6)
	if o.locked then T.edge(box, if o.confirmed then T.ACCENT else T.SOFT, if o.confirmed then 0.3 else 0.6, 1) end
	local hd = text(box, "Head", title, 12, T.TEXT, T.FONT_HEAVY)
	at(hd, 10, 8, w - 130, 16); hd.TextTruncate = Enum.TextTruncate.AtEnd
	local mark = if o.confirmed then "CONFIRMED" elseif o.locked then "LOCKED" else "ADDING"
	local mk = text(box, "Mark", mark, 11, if o.confirmed then T.ACCENT elseif o.locked then T.SOFT else T.DIM, T.FONT_HEAVY, Enum.TextXAlignment.Right)
	at(mk, w - 130, 8, 120, 16)
	local sc = new("ScrollingFrame", { Name = "Items", BackgroundTransparency = 1, BorderSizePixel = 0, ScrollBarThickness = 3,
		ScrollBarImageColor3 = T.DIM, ScrollingDirection = Enum.ScrollingDirection.Y, CanvasSize = UDim2.new() }, box)
	local sl = stockLine(o.stock)
	local listH = h - 34 - (if sl ~= "" then 20 else 0) - 6
	at(sc, 8, 30, w - 12, listH)
	local cols = if w >= 420 then 3 elseif w >= 280 then 2 else 1
	local cw = math.floor((w - 16 - (cols - 1) * 6) / cols)
	for i, c in o.items do
		local b = itemCard(sc, c, cw, 40, nil)
		b.Position = UDim2.fromOffset(((i - 1) % cols) * (cw + 6), ((i - 1) // cols) * 46)
		if mine then
			b.MouseButton1Click:Connect(function() task.spawn(ask, "remove", c.t, c.k) end)
		else
			b.Selectable = false
		end
	end
	sc.CanvasSize = UDim2.fromOffset(0, math.ceil(#o.items / cols) * 46)
	if #o.items == 0 and sl == "" then
		local e = text(sc, "Empty", if mine then "nothing yet: pick from your things" else "nothing yet", 12, T.DIM, T.FONT)
		at(e, 2, 2, w - 20, 20)
	end
	if sl ~= "" then
		local s = text(box, "Stock", sl, 11, T.SOFT, T.FONT_BOLD)
		at(s, 10, h - 24, w - 20, 16); s.TextTruncate = Enum.TextTruncate.AtEnd
	end
	return y + h
end

-- the final look: exactly what goes each way, in plain rows
local function finalLook(parent: Instance, x: number, y: number, w: number, h: number)
	local v = S.view
	local hd = text(parent, "FinalHead", "FINAL LOOK", 11, T.ACCENT, T.FONT_HEAVY)
	at(hd, x, y, w, 14)
	local sc = new("ScrollingFrame", { Name = "Final", BackgroundTransparency = 1, BorderSizePixel = 0, ScrollBarThickness = 4,
		ScrollBarImageColor3 = T.DIM, ScrollingDirection = Enum.ScrollingDirection.Y, CanvasSize = UDim2.new() }, parent)
	at(sc, x, y + 20, w + 6, h - 20)
	local cy = 0
	local function block(title: string, o: any)
		local t = text(sc, "H_" .. title, title, 12, T.TEXT, T.FONT_HEAVY)
		at(t, 0, cy, w, 16)
		cy += 20
		local n = 0
		for _, c in o.items do
			local r = text(sc, "Row", ("%s  ·  %s%s"):format(c.name, c.type or c.t, if c.gun then "  ·  " .. c.gun else ""), 12, T.SOFT, T.FONT_BOLD)
			at(r, 8, cy, w - 8, 16); r.TextTruncate = Enum.TextTruncate.AtEnd
			new("Frame", { BorderSizePixel = 0, BackgroundColor3 = rcol(c.rarity), Position = UDim2.fromOffset(0, cy + 3), Size = UDim2.fromOffset(3, 11) }, sc)
			cy += 18
			n += 1
		end
		local sl = stockLine(o.stock)
		if sl ~= "" then
			local r = text(sc, "RowStock", sl, 12, T.SOFT, T.FONT_BOLD)
			at(r, 8, cy, w - 8, 16)
			cy += 18
			n += 1
		end
		if n == 0 then
			local r = text(sc, "RowNone", "nothing", 12, T.DIM, T.FONT)
			at(r, 8, cy, w - 8, 16)
			cy += 18
		end
		cy += 10
	end
	block("YOU GIVE", v.me)
	block("YOU GET", v.them)
	sc.CanvasSize = UDim2.fromOffset(0, cy)
end

local countdown: TextButton? = nil
function TradeUI.refresh()
	countdown = nil
	for _, c in panel:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	if not S.open or not S.view then return end
	local v = S.view
	local cam = workspace.CurrentCamera
	local sz = S.fake or (if cam then cam.ViewportSize / T.scaleNow() else Vector2.new(1280, 720))
	local compact = sz.X < 760
	local W = math.min(880, sz.X - 16)
	local H = math.min(560, sz.Y - 16)
	panel.Size = UDim2.fromOffset(W, H)
	local pad = if compact then 10 else 16
	local title = text(panel, "Title", "TRADE", if compact then 18 else 22, T.TEXT, T.FONT_TITLE)
	at(title, pad, 10, 120, 28)
	local with = text(panel, "With", "WITH " .. string.upper(v.them.name or "?"), 12, T.MUTED, T.FONT_HEAVY)
	at(with, pad + (if compact then 84 else 100), 18, W - 260, 16); with.TextTruncate = Enum.TextTruncate.AtEnd
	local cancel = button(panel, "Cancel", "CANCEL", if v.phase == "swap" then "off" else "plain", if compact then 76 else 90, 30)
	cancel.AnchorPoint = Vector2.new(1, 0); cancel.Position = UDim2.new(1, -pad, 0, 10)
	cancel.MouseButton1Click:Connect(function() if v.phase ~= "swap" then task.spawn(ask, "cancel") end end)
	local y = 50
	local barH = if compact then 48 else 56
	local bodyH = H - y - barH - pad - 10
	if compact then
		-- a phone: two tabs, TRADE (the offers, or the final look) and YOUR THINGS
		local tw = math.floor((W - pad * 2 - 6) / 2)
		local review = v.phase == "review" or v.phase == "swap"
		for i, tb in { { "trade", if review then "FINAL LOOK" else "TRADE" }, { "things", "YOUR THINGS" } } do
			local b = button(panel, "Tab_" .. tb[1], tb[2], if S.tab == tb[1] then "accent" else "plain", tw, 28)
			b.Position = UDim2.fromOffset(pad + (i - 1) * (tw + 6), y)
			b.MouseButton1Click:Connect(function() S.tab = tb[1]; TradeUI.refresh() end)
		end
		y += 36
		bodyH -= 36
		local inner = W - pad * 2
		if S.tab == "things" and not review then
			picker(panel, pad, y, inner, bodyH)
		elseif review then
			finalLook(panel, pad, y, inner, bodyH)
		else
			local half = math.floor((bodyH - 8) / 2)
			offerBox(panel, pad, y, inner, half, v.me, "YOU GIVE", true)
			offerBox(panel, pad, y + half + 8, inner, half, v.them, string.upper(v.them.name or "?") .. " GIVES", false)
		end
	else
		local lw = 360
		local rx = pad + lw + 16
		local rw = W - rx - pad
		if v.phase == "review" or v.phase == "swap" then
			finalLook(panel, pad, y, lw, bodyH)
		else
			picker(panel, pad, y, lw, bodyH)
		end
		local half = math.floor((bodyH - 10) / 2)
		offerBox(panel, rx, y, rw, half, v.me, "YOU GIVE", true)
		offerBox(panel, rx, y + half + 10, rw, half, v.them, string.upper(v.them.name or "?") .. " GIVES", false)
	end
	-- the big button and its line
	local bw = if compact then W - pad * 2 else 320
	local by = H - pad - barH + (if compact then 0 else 6)
	local line = text(panel, "Line", "", 11, T.MUTED, T.FONT_BOLD, if compact then Enum.TextXAlignment.Center else Enum.TextXAlignment.Left)
	local main: TextButton
	if v.phase == "swap" then
		main = button(panel, "Main", "SWAPPING", "off", bw, barH - 8)
		line.Text = "the server is swapping the items"
	elseif v.phase == "review" then
		if v.me.confirmed then
			main = button(panel, "Main", "WAITING FOR " .. string.upper(v.them.name or "?"), "off", bw, barH - 8)
			line.Text = "you confirmed. any change starts again"
		else
			main = button(panel, "Main", "CONFIRM", "accent", bw, barH - 8)
			countdown = main
			main.MouseButton1Click:Connect(function()
				if (S.view and S.view.confirmAt or 0) > workspace:GetServerTimeNow() then return end
				task.spawn(ask, "confirm")
			end)
			line.Text = "both must confirm. any change starts again"
		end
	elseif v.me.locked then
		main = button(panel, "Main", "UNLOCK", "plain", bw, barH - 8)
		main.MouseButton1Click:Connect(function() task.spawn(ask, "unlock") end)
		line.Text = "waiting for " .. (v.them.name or "?") .. " to lock"
	else
		main = button(panel, "Main", "LOCK", "accent", bw, barH - 8)
		main.MouseButton1Click:Connect(function() task.spawn(ask, "lock") end)
		line.Text = "lock when your side is ready. a change unlocks both"
	end
	main.FontFace = T.FONT_SHOUT
	main.TextSize = if compact then 15 else 18
	if compact then
		main.Position = UDim2.fromOffset(pad, by - 14)
		at(line, pad, H - pad - 12, W - pad * 2, 12)
	else
		main.AnchorPoint = Vector2.new(1, 0)
		main.Position = UDim2.new(1, -pad, 0, by)
		at(line, pad, by + 10, W - bw - pad * 3, 30); line.TextWrapped = true
	end
end

-- ------------------------------------------------------------------ open / close
local saved: any = nil
local function controls(on: boolean)
	pcall(function()
		local c = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		if on then c:Enable() else c:Disable() end
	end)
end
local function hold(on: boolean)
	if on then
		saved = me:GetAttribute("LoadoutOpen")
		me:SetAttribute("LoadoutOpen", true) -- (a menu is up: hands and movement hold still, the mouse is free)
		controls(false)
	else
		me:SetAttribute("LoadoutOpen", if saved == true then true else false)
		controls(true)
	end
end
local function fetch()
	local r = ask("state")
	if r.ok then
		S.state = r
		if r.trade then S.view = r.trade end
	end
	TradeUI.refresh()
end
local function showWindow()
	if S.open then TradeUI.refresh(); return end
	if not gateOk() then return end
	S.open = true
	S.tab = "trade"
	gui.Enabled = true
	hold(true)
	MenuCursor.set("trade", true, function() return S.open end)
	TradeUI.refresh()
	task.spawn(fetch)
end
local function hideWindow()
	if not S.open then return end
	S.open = false
	gui.Enabled = false
	MenuCursor.set("trade", false)
	hold(false)
end
function TradeUI.isOpen(): boolean return S.open end
-- (a menu closing everything: MapRoomHud going into a match or a map room. the server ends the trade itself there)
function TradeUI.close()
	if S.open then task.spawn(ask, "cancel") end
	hideWindow()
	TradeUI.closeHistory()
end
-- B on a controller: the picker tab first (a phone), then CANCEL
function TradeUI.backOut()
	if S.tab == "things" then S.tab = "trade"; TradeUI.refresh(); return end
	TradeUI.close()
end
-- TRADE on the PARTY panel or a card
function TradeUI.request(userId: number)
	if not TradeUI.on() then notice("trading isn't open yet"); return end
	if not gateOk() then return end
	task.spawn(function()
		local r = ask("request", userId)
		if r.ok then notice("trade request sent") end
	end)
end

-- ------------------------------------------------------------------ the request pop-up
local askGui = new("ScreenGui", { Name = "JankTradeAsk", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 23,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, pg)
local askScaled = T.scaled(askGui)
local pop = T.plate(askScaled, "Ask", UDim2.new(0.5, 0, 0, 112), UDim2.fromOffset(440, 78))
pop.AnchorPoint = Vector2.new(0.5, 0)
T.edge(pop, T.ACCENT, 0.5, 1)
local pHead = text(pop, "Head", "", 15, T.TEXT, T.FONT_HEAVY)
at(pHead, 16, 10, 250, 20); pHead.TextTruncate = Enum.TextTruncate.AtEnd
local pSub = text(pop, "Sub", "TRADE REQUEST", 12, T.MUTED, T.FONT_BOLD)
at(pSub, 16, 34, 250, 16)
local pYes = button(pop, "Accept", "ACCEPT", "accent", 78, 34)
pYes.Position = UDim2.new(1, -172, 0, 14)
local pNo = button(pop, "Decline", "DECLINE", "plain", 78, 34)
pNo.Position = UDim2.new(1, -88, 0, 14)
local pTrack = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Position = UDim2.new(0, 16, 1, -12), Size = UDim2.new(1, -32, 0, 3) }, pop)
T.corner(pTrack, 2)
local pFill = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Size = UDim2.fromScale(1, 1) }, pTrack)
T.corner(pFill, 2)
local function topAsk(): any
	local best = nil
	for _, a in S.asks do if not best or a.ends < best.ends then best = a end end
	return best
end
local function answer(yes: boolean)
	local a = topAsk()
	if not a then return end
	for i, x in S.asks do if x == a then table.remove(S.asks, i); break end end
	task.spawn(ask, "answer", a.from, yes)
end
pYes.MouseButton1Click:Connect(function() answer(true) end)
pNo.MouseButton1Click:Connect(function() answer(false) end)

-- ------------------------------------------------------------------ TRADES (history)
local hGui = new("ScreenGui", { Name = "JankTradeHistory", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 25,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, pg)
local hScaled = T.scaled(hGui)
local hShade = new("TextButton", { Name = "Shade", AutoButtonColor = false, Text = "", BorderSizePixel = 0, BackgroundColor3 = Color3.new(0, 0, 0),
	BackgroundTransparency = 0.45, Size = UDim2.fromScale(1, 1), Modal = true, Selectable = false }, hScaled)
local hPanel = T.plate(hScaled, "Panel", UDim2.fromScale(0.5, 0.5), UDim2.fromOffset(560, 520))
hPanel.AnchorPoint = Vector2.new(0.5, 0.5)
hPanel.BackgroundTransparency = 0.06
hShade.MouseButton1Click:Connect(function() TradeUI.closeHistory() end)
local function names(items: any, stock: any): string
	local parts = {}
	for _, c in items or {} do table.insert(parts, c.name .. (if c.gun then " (" .. c.gun .. ")" else "")) end
	local sl = stockLine(stock)
	if sl ~= "" then table.insert(parts, sl) end
	return if #parts > 0 then table.concat(parts, ", ") else "nothing"
end
local function drawHistory()
	for _, c in hPanel:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	local cam = workspace.CurrentCamera
	local sz = S.fake or (if cam then cam.ViewportSize / T.scaleNow() else Vector2.new(1280, 720))
	local W = math.min(560, sz.X - 16)
	local H = math.min(520, sz.Y - 16)
	hPanel.Size = UDim2.fromOffset(W, H)
	local pad = 16
	local title = text(hPanel, "Title", "TRADES", 22, T.TEXT, T.FONT_TITLE)
	at(title, pad, 12, 200, 28)
	local close = button(hPanel, "Close", "CLOSE", "plain", 86, 30)
	close.AnchorPoint = Vector2.new(1, 0); close.Position = UDim2.new(1, -pad, 0, 12)
	close.MouseButton1Click:Connect(function() TradeUI.closeHistory() end)
	local sc = new("ScrollingFrame", { Name = "List", BackgroundTransparency = 1, BorderSizePixel = 0, ScrollBarThickness = 4,
		ScrollBarImageColor3 = T.DIM, ScrollingDirection = Enum.ScrollingDirection.Y, CanvasSize = UDim2.new() }, hPanel)
	at(sc, pad, 54, W - pad * 2 + 6, H - 54 - pad)
	local inner = W - pad * 2
	local list = S.list
	if not list then
		local l = text(sc, "Loading", "LOADING", 14, T.MUTED, T.FONT_TITLE, Enum.TextXAlignment.Center)
		at(l, 0, 0, inner, 40)
		return
	end
	if #list == 0 then
		local l = text(sc, "Empty", "no trades yet", 12, T.MUTED, T.FONT)
		at(l, 0, 0, inner, 22)
		return
	end
	local y = 0
	for i, x in list do
		local when = if type(x.t) == "number" then string.upper(os.date("!%d %b %H:%M", x.t)) .. " UTC" else ""
		local row = new("Frame", { Name = "Trade" .. i, BorderSizePixel = 0, BackgroundColor3 = T.CARD, BackgroundTransparency = 0.15 }, sc)
		T.corner(row, 5)
		local hd = text(row, "Head", "WITH " .. string.upper(tostring(x.withName or "?")), 13, T.TEXT, T.FONT_HEAVY)
		at(hd, 10, 6, inner - 160, 16); hd.TextTruncate = Enum.TextTruncate.AtEnd
		local tm = text(row, "When", when, 11, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
		at(tm, inner - 160, 7, 150, 14)
		local g = text(row, "Gave", "GAVE  " .. names(x.gave, x.gaveStock), 11, T.SOFT, T.FONT_BOLD)
		g.TextWrapped = true
		local gotT = text(row, "Got", "GOT  " .. names(x.got, x.gotStock), 11, T.SOFT, T.FONT_BOLD)
		gotT.TextWrapped = true
		local function lines(s: string): number return math.max(1, math.ceil(#s * 6.2 / (inner - 20))) end
		local gh, oh = lines(g.Text) * 14, lines(gotT.Text) * 14
		at(g, 10, 26, inner - 20, gh)
		at(gotT, 10, 30 + gh, inner - 20, oh)
		local h = 38 + gh + oh
		at(row, 0, y, inner, h)
		y += h + 6
	end
	sc.CanvasSize = UDim2.fromOffset(0, y)
end
function TradeUI.history()
	if S.hist then return end
	if not gateOk() then return end
	S.hist = true
	S.list = nil
	hGui.Enabled = true
	if not S.open then hold(true) end
	MenuCursor.set("tradehistory", true, function() return S.hist end)
	drawHistory()
	task.spawn(function()
		local r = ask("history")
		S.list = if r.ok and type(r.list) == "table" then r.list else {}
		if S.hist then drawHistory() end
	end)
end
function TradeUI.closeHistory()
	if not S.hist then return end
	S.hist = false
	hGui.Enabled = false
	MenuCursor.set("tradehistory", false)
	if not S.open then hold(false) end
end

-- ------------------------------------------------------------------ the server's pushes
function TradeUI.onPush(msg: any)
	if type(msg) ~= "table" then return end
	if msg.t == "trade" then
		S.view = msg.view
		if msg.view then
			if not S.open then showWindow() else
				if msg.view.phase == "review" then S.tab = "trade" end
				TradeUI.refresh()
			end
		else
			hideWindow()
		end
	elseif msg.t == "ask" then
		for i, a in S.asks do if a.from == msg.from then table.remove(S.asks, i); break end end
		table.insert(S.asks, { from = msg.from, name = msg.name, ends = msg.ends, len = math.max(1, (msg.ends or 0) - workspace:GetServerTimeNow()) })
	elseif msg.t == "askgone" then
		for i, a in S.asks do if a.from == msg.from then table.remove(S.asks, i); break end end
	elseif msg.t == "note" then
		notice(tostring(msg.text))
	elseif msg.t == "done" then
		S.view = nil
		hideWindow()
		local n1, n2 = #(msg.gave or {}), #(msg.got or {})
		for _, n in (msg.gaveStock or {}) do n1 += n end
		for _, n in (msg.gotStock or {}) do n2 += n end
		notice(("traded with %s: gave %d, got %d"):format(tostring(msg.with), n1, n2))
	end
end

RunService.RenderStepped:Connect(function()
	-- the pop-up: the soonest-ending request, in the hub only
	local a = topAsk()
	local tnow = workspace:GetServerTimeNow()
	if a and a.ends <= tnow then
		for i, x in S.asks do if x == a then table.remove(S.asks, i); break end end
		a = topAsk()
	end
	local zone = me:GetAttribute("Zone")
	local showAsk = a ~= nil and not S.open and (zone == nil or zone == "hub")
	askGui.Enabled = showAsk
	if showAsk then
		pHead.Text = string.upper(a.name or "?") .. " WANTS TO TRADE"
		pFill.Size = UDim2.fromScale(math.clamp((a.ends - tnow) / (a.len or 20), 0, 1), 1)
	end
	-- the CONFIRM count
	local cb = countdown
	if cb and cb.Parent and S.view then
		local left = (S.view.confirmAt or 0) - tnow
		local txt = if left > 0 then ("CONFIRM  %d"):format(math.ceil(left)) else "CONFIRM"
		if cb.Text ~= txt then cb.Text = txt end
		cb.BackgroundTransparency = if left > 0 then 0.45 else 0
	end
	if S.open or S.hist then UIS.MouseBehavior = Enum.MouseBehavior.Default end
	if S.open and (zone == "match" or zone == "staging") then hideWindow() end
end)

-- (Studio: a phone-sized layout to look at)
function TradeUI.fakeScreen(v: Vector2?) S.fake = v; TradeUI.refresh(); if S.hist then drawHistory() end end

return TradeUI
