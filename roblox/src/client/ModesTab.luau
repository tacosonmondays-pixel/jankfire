--!strict
-- the Play screen's MODES tab, under PARTY RANKED (17 Nov 2026, the owner: "also modes should be quickplay or party
-- choosing individual modes would be impossible to fill up with proper matches! maybe"; PlayConfig QUICKPLAY). two
-- cards in the Play panel's look:
--   QUICKPLAY  one public queue for every classic mode; the match votes on its mode (client/QuickVoteUI.luau). the
--              modes in rotation along its foot
--   PARTY      the leader picks one mode for the party (a two-column list; on a small screen a < MODE > row), and
--              FILL FROM QUICKPLAY tops the party up from the quickplay queue. without it the party plays alone
--              (never rated), so a mode that needs more players than the party says so
-- PlayUI's modeList calls ModesTab.draw with its panel and helpers; it returns the panel's next free y
local T = require(script.Parent:WaitForChild("Theme"))
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local PlayConfig = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("PlayConfig"))

local new, text = T.new, T.text
local ModesTab = {}
local lastPick: string? = nil -- (the leader's last party pick, so the PARTY card goes back to it from quickplay)

-- ctx: left, y, W, c (compact), cardH, pt (party view), n (party size), lead, pon (party ranked on), ask, notice, leaderName
function ModesTab.draw(ctx: any): number
	local left, W, c, pt, lead = ctx.left, ctx.W, ctx.c, ctx.pt, ctx.lead
	local y = ctx.y
	local classic = PlayConfig.classic()
	local mode = pt and pt.mode
	local quickOn = mode == PlayConfig.QUICKPLAY
	local picked: any = mode and PlayConfig.byId[mode]
	local partyOn = picked ~= nil and picked.ladder == "party" and not picked.quick
	if partyOn then lastPick = mode end
	local function onlyLeader(): boolean
		if lead then return true end
		ctx.notice("only the leader (" .. ctx.leaderName() .. ") picks the mode")
		return false
	end
	local function pickMode(id: string)
		if not onlyLeader() then return end
		local m: any = PlayConfig.byId[id]
		task.spawn(ctx.ask, "mode", id, ctx.pon and m ~= nil and m.ranked == true)
	end
	local function frame(card: GuiObject, on: boolean)
		T.corner(card, 5)
		if on then
			T.edge(card, T.ACCENT, 0.35, 1)
			local pb = new("Frame", { Name = "Picked", BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Position = UDim2.fromOffset(0, 8),
				Size = UDim2.new(0, 3, 1, -16), ZIndex = 3 }, card)
			T.corner(pb, 2)
		end
	end

	-- QUICKPLAY
	local qH = if c then 64 else 102
	local q = new("TextButton", { Name = "Quickplay", AutoButtonColor = false, BorderSizePixel = 0, Text = "", ZIndex = 2,
		BackgroundColor3 = if quickOn then T.CARD_HI else T.CARD, BackgroundTransparency = if quickOn then 0.05 else 0.2,
		Position = UDim2.fromOffset(12, y), Size = UDim2.fromOffset(W - 24, qH) }, left)
	frame(q, quickOn)
	local qn = text(q, "Name", "QUICKPLAY", if c then 16 else 21, T.TEXT, T.FONT_TITLE); qn.ZIndex = 3
	qn.Position = UDim2.fromOffset(14, if c then 5 else 9); qn.Size = UDim2.new(1, -90, 0, if c then 20 else 26)
	local qc = text(q, "Count", "2-8 PLAYERS", if c then 9 else 11, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right); qc.ZIndex = 3
	qc.AnchorPoint = Vector2.new(1, 0); qc.Position = UDim2.new(1, -12, 0, if c then 9 else 15); qc.Size = UDim2.fromOffset(90, 14)
	local qs = text(q, "Sub", "every mode · the match votes on its mode", if c then 10 else 12, T.MUTED, T.FONT); qs.ZIndex = 3
	qs.Position = UDim2.fromOffset(14, if c then 25 else 36); qs.Size = UDim2.new(1, -24, 0, 16); qs.TextTruncate = Enum.TextTruncate.AtEnd
	local names = {}
	for _, m in classic do table.insert(names, m.name) end
	local rot = text(q, "Rotation", "IN ROTATION  " .. table.concat(names, "  ·  "), if c then 8 else 10, T.DIM, T.FONT_BOLD); rot.ZIndex = 3
	rot.Position = UDim2.fromOffset(14, if c then 43 else 56); rot.Size = UDim2.new(1, -24, 0, if c then 12 else 38)
	rot.TextWrapped = not c; rot.TextYAlignment = Enum.TextYAlignment.Top
	if c then rot.TextTruncate = Enum.TextTruncate.AtEnd end
	q.MouseButton1Click:Connect(function() pickMode(PlayConfig.QUICKPLAY) end)
	y += qH + 8

	-- PARTY
	local chipH, gap = if c then 26 else 28, 6
	local rows = math.ceil(#classic / 2)
	local listH = if c then chipH else rows * chipH + (rows - 1) * gap
	-- (the MAP row: a party's own pick plays on the leader's map. ranked has no pick: the rotation's)
	local mapOn = partyOn and not ctx.pon and pt ~= nil and type(pt.maps) == "table" and #pt.maps > 0
	local mapH = if c then 40 else 46
	local pH = (if c then 44 else 58) + listH + 8 + (if mapOn then mapH + 8 else 0) + (if c then 26 else 30) + (if c then 20 else 24)
	local p = new("TextButton", { Name = "Party", AutoButtonColor = false, BorderSizePixel = 0, Text = "", ZIndex = 2,
		BackgroundColor3 = if partyOn then T.CARD_HI else T.CARD, BackgroundTransparency = if partyOn then 0.05 else 0.2,
		Position = UDim2.fromOffset(12, y), Size = UDim2.fromOffset(W - 24, pH) }, left)
	frame(p, partyOn)
	local pn = text(p, "Name", "PARTY", if c then 16 else 21, T.TEXT, T.FONT_TITLE); pn.ZIndex = 3
	pn.Position = UDim2.fromOffset(14, if c then 5 else 9); pn.Size = UDim2.new(1, -24, 0, if c then 20 else 26)
	local ps = text(p, "Sub", if lead then "your party plays the mode you pick" else "the leader picks the mode", if c then 10 else 12, T.MUTED, T.FONT); ps.ZIndex = 3
	ps.Position = UDim2.fromOffset(14, if c then 25 else 36); ps.Size = UDim2.new(1, -24, 0, 16); ps.TextTruncate = Enum.TextTruncate.AtEnd
	p.MouseButton1Click:Connect(function()
		if partyOn then return end
		pickMode(lastPick or (classic[1] and classic[1].id) or PlayConfig.QUICKPLAY)
	end)
	local ly = if c then 44 else 58
	local iw = (W - 24) - 28
	local function chip(parent: Instance, name: string, label: string, on: boolean, x: number, yy: number, w: number): TextButton
		local b = new("TextButton", { Name = name, AutoButtonColor = false, BorderSizePixel = 0, ZIndex = 3, Text = label,
			BackgroundColor3 = if on then T.CARD_HI else T.BG, BackgroundTransparency = if on then 0 else 0.35,
			Position = UDim2.fromOffset(x, yy), Size = UDim2.fromOffset(w, chipH), FontFace = T.FONT_HEAVY,
			TextSize = if c then 10 else 11, TextColor3 = if on then T.TEXT else T.MUTED, TextTruncate = Enum.TextTruncate.AtEnd }, parent)
		T.corner(b, 4)
		if on then T.edge(b, T.ACCENT, 0.3, 1) end
		-- (a long name shrinks to fit the button rather than being cut: the phone's < MODE > row is narrow)
		b.TextScaled = true
		new("UITextSizeConstraint", { MaxTextSize = if c then 10 else 11, MinTextSize = 7 }, b)
		new("UIPadding", { PaddingLeft = UDim.new(0, 4), PaddingRight = UDim.new(0, 4), PaddingTop = UDim.new(0, 5), PaddingBottom = UDim.new(0, 5) }, b)
		return b
	end
	if c then
		-- (a small screen: < MODE > through the list)
		local cur = if partyOn then mode else lastPick
		local idx = 1
		for i, m in classic do if m.id == cur then idx = i end end
		local m = classic[idx]
		local prev = chip(p, "Prev", "<", false, 14, ly, 30)
		local mid = chip(p, "Pick", if m then m.name else "-", partyOn, 14 + 36, ly, iw - 72)
		local nxt = chip(p, "Next", ">", false, 14 + iw - 30, ly, 30)
		prev.MouseButton1Click:Connect(function() if #classic > 0 then pickMode(classic[(idx - 2) % #classic + 1].id) end end)
		nxt.MouseButton1Click:Connect(function() if #classic > 0 then pickMode(classic[idx % #classic + 1].id) end end)
		mid.MouseButton1Click:Connect(function() if m then pickMode(m.id) end end)
	else
		local cw = (iw - gap) / 2
		for i, m in classic do
			local col, row = (i - 1) % 2, (i - 1) // 2
			local b = chip(p, m.id, m.name, partyOn and mode == m.id, 14 + col * (cw + gap), ly + row * (chipH + gap), cw)
			b.MouseButton1Click:Connect(function() pickMode(m.id) end)
		end
	end
	ly += listH + 8
	-- MAP: a picture of it, its name, < > through RANDOM and the rotation's maps (the leader's; the others see it)
	if mapOn then
		local maps = pt.maps :: { any }
		local list: { any } = { { id = "random", title = "RANDOM", thumb = "" } }
		for _, m in maps do table.insert(list, m) end
		local idx = 1
		for i, m in list do if m.id == pt.map then idx = i end end
		local cur = list[idx]
		local row = new("Frame", { Name = "Map", BorderSizePixel = 0, BackgroundColor3 = T.BG, BackgroundTransparency = 0.35, ZIndex = 3,
			Position = UDim2.fromOffset(14, ly), Size = UDim2.fromOffset(iw, mapH) }, p)
		T.corner(row, 4)
		local th = mapH - 8
		local pic = new("ImageLabel", { Name = "Thumb", BorderSizePixel = 0, BackgroundColor3 = T.CARD, BackgroundTransparency = 0, ZIndex = 4,
			Image = cur.thumb or "", ScaleType = Enum.ScaleType.Crop, Position = UDim2.fromOffset(4, 4), Size = UDim2.fromOffset(math.floor(th * 16 / 9), th) }, row)
		T.corner(pic, 3)
		local tx = 4 + math.floor(th * 16 / 9) + 10
		local aw = if lead then (if c then 40 else 34) else 0
		local lab = text(row, "Label", "MAP", if c then 8 else 9, T.MUTED, T.FONT_BOLD); lab.ZIndex = 4
		lab.Position = UDim2.fromOffset(tx, if c then 5 else 7); lab.Size = UDim2.fromOffset(iw - tx - aw * 2 - 12, 12)
		local nm = text(row, "Title", cur.title or cur.id, if c then 11 else 13, T.TEXT, T.FONT_HEAVY); nm.ZIndex = 4
		nm.Position = UDim2.fromOffset(tx, if c then 17 else 21); nm.Size = UDim2.fromOffset(iw - tx - aw * 2 - 12, if c then 16 else 18)
		nm.TextScaled = true
		new("UITextSizeConstraint", { MaxTextSize = if c then 11 else 13, MinTextSize = 7 }, nm)
		if lead then
			local function arrow(name: string, label: string, x: number, step: number)
				local b = new("TextButton", { Name = name, AutoButtonColor = false, BorderSizePixel = 0, ZIndex = 4, Text = label,
					BackgroundColor3 = T.CARD, BackgroundTransparency = 0.1, AnchorPoint = Vector2.new(0, 0.5),
					Position = UDim2.new(0, x, 0.5, 0), Size = UDim2.fromOffset(aw, mapH - 8), FontFace = T.FONT_HEAVY,
					TextSize = if c then 14 else 13, TextColor3 = T.TEXT }, row)
				T.corner(b, 4)
				b.MouseButton1Click:Connect(function()
					local nx = list[(idx - 1 + step) % #list + 1]
					task.spawn(ctx.ask, "map", nx.id)
				end)
			end
			arrow("Prev", "<", iw - aw * 2 - 8, -1)
			arrow("Next", ">", iw - aw - 4, 1)
		end
		ly += mapH + 8
	end
	-- FILL FROM QUICKPLAY
	local fillOn = pt ~= nil and pt.fill == true
	local sw = new("TextButton", { Name = "Fill", AutoButtonColor = false, BorderSizePixel = 0, Text = "", ZIndex = 3,
		BackgroundColor3 = T.BG, BackgroundTransparency = 0.35, Position = UDim2.fromOffset(14, ly), Size = UDim2.fromOffset(iw, if c then 26 else 30) }, p)
	T.corner(sw, 4)
	local fl = text(sw, "Label", "FILL FROM QUICKPLAY", if c then 10 else 11, if fillOn then T.ACCENT else T.TEXT, T.FONT_HEAVY); fl.ZIndex = 4
	fl.Position = UDim2.fromOffset(10, 0); fl.Size = UDim2.new(1, -60, 1, 0)
	local pill = new("Frame", { Name = "Pill", BorderSizePixel = 0, BackgroundColor3 = if fillOn then T.ACCENT else T.TRACK, ZIndex = 4,
		AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -8, 0.5, 0), Size = UDim2.fromOffset(if c then 32 else 38, if c then 16 else 18) }, sw)
	T.corner(pill, 10)
	local kn = if c then 10 else 12
	local knob = new("Frame", { Name = "Knob", BorderSizePixel = 0, BackgroundColor3 = if fillOn then T.INK else T.SOFT, ZIndex = 5, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(if fillOn then 1 else 0, if fillOn then -(kn // 2 + 3) else kn // 2 + 3, 0.5, 0), Size = UDim2.fromOffset(kn, kn) }, pill)
	T.corner(knob, kn)
	sw.MouseButton1Click:Connect(function()
		if not lead then ctx.notice("only the leader (" .. ctx.leaderName() .. ") switches it"); return end
		task.spawn(ctx.ask, "fill", not fillOn)
	end)
	ly += (if c then 26 else 30) + 4
	-- the head-count line: what the picked mode takes, and what stops the party playing it alone
	local note = ""
	local warn = false
	if partyOn then
		local lo, hi = PlayConfig.counts(mode)
		note = ("%s · %d to %d players"):format(picked.name, lo, hi)
		if not fillOn and ctx.pon then
			note, warn = "PARTY RANKED needs other players: turn on fill", true
		elseif not fillOn and ctx.n < lo then
			note, warn = ("needs %d players, your party is %d: turn on fill"):format(lo, ctx.n), true
		elseif not fillOn then
			note = note .. " · your party alone"
		end
	end
	local nt = text(p, "Note", note, if c then 9 else 11, if warn then T.ACCENT else T.MUTED, T.FONT_BOLD); nt.ZIndex = 3
	nt.Position = UDim2.fromOffset(14, ly); nt.Size = UDim2.fromOffset(iw, 14); nt.TextTruncate = Enum.TextTruncate.AtEnd
	y += pH + 8
	-- ZOMBIES (19 Nov 2026, PlayConfig.ZOMBIES): co-op waves, a squad of up to 4 (bots fill the rest). never ranked, so
	-- not under PARTY RANKED. SOON till the server opens it (ReplicatedStorage's ZombiesOn)
	if not ctx.pon then
		local zm: any = PlayConfig.byId[PlayConfig.ZOMBIES]
		local open = ReplicatedStorage:GetAttribute("ZombiesOn") == true
		local zOn = mode == PlayConfig.ZOMBIES
		local zH = if c then 50 else 66
		local z = new("TextButton", { Name = "Zombies", AutoButtonColor = false, BorderSizePixel = 0, Text = "", ZIndex = 2,
			BackgroundColor3 = if zOn then T.CARD_HI else T.CARD, BackgroundTransparency = if zOn then 0.05 elseif open then 0.2 else 0.45,
			Position = UDim2.fromOffset(12, y), Size = UDim2.fromOffset(W - 24, zH) }, left)
		frame(z, zOn)
		local zn = text(z, "Name", "ZOMBIES", if c then 16 else 21, if open then T.TEXT else T.MUTED, T.FONT_TITLE); zn.ZIndex = 3
		zn.Position = UDim2.fromOffset(14, if c then 5 else 9); zn.Size = UDim2.new(1, -110, 0, if c then 20 else 26)
		local zc = text(z, "Count", if open then "1-4 PLAYERS" else "SOON", if c then 9 else 11, if open then T.MUTED else T.ACCENT, T.FONT_BOLD, Enum.TextXAlignment.Right); zc.ZIndex = 3
		zc.AnchorPoint = Vector2.new(1, 0); zc.Position = UDim2.new(1, -12, 0, if c then 9 else 15); zc.Size = UDim2.fromOffset(100, 14)
		local zs = text(z, "Sub", "co-op waves · bots fill the empty slots", if c then 10 else 12, T.MUTED, T.FONT); zs.ZIndex = 3
		zs.Position = UDim2.fromOffset(14, if c then 25 else 36); zs.Size = UDim2.new(1, -24, 0, 16); zs.TextTruncate = Enum.TextTruncate.AtEnd
		z.MouseButton1Click:Connect(function()
			if not open then ctx.notice("ZOMBIES isn't open yet"); return end
			if zm and ctx.n > zm.size then ctx.notice(("ZOMBIES is a squad of %d: your party is %d"):format(zm.size, ctx.n)); return end
			pickMode(PlayConfig.ZOMBIES)
		end)
		y += zH + 8
	end
	-- (PARTY RANKED's one rule of its own: the grapple's charges, shared/HookCharges.luau)
	if ctx.pon then
		local HC = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("HookCharges")) :: any
		local g = text(left, "Grapple", ("ranked: grapple %d charges, one back every %d s"):format(HC.CHARGES, HC.CD), if c then 9 else 11, T.MUTED, T.FONT_BOLD)
		g.Position = UDim2.fromOffset(16, y - 2); g.Size = UDim2.fromOffset(W - 32, 14); g.ZIndex = 3; g.TextTruncate = Enum.TextTruncate.AtEnd
		y += 16
		-- (and the map: no pick, no vote, a fair draw from the rotation)
		local mp = text(left, "Maps", "ranked: maps in a random rotation, no vote", if c then 9 else 11, T.MUTED, T.FONT_BOLD)
		mp.Position = UDim2.fromOffset(16, y - 2); mp.Size = UDim2.fromOffset(W - 32, 14); mp.ZIndex = 3; mp.TextTruncate = Enum.TextTruncate.AtEnd
		y += 16
	end
	return y
end

return ModesTab
