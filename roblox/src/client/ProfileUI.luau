--!strict
-- the PLAYER CARD screen (ProfileClient opens it: the PROFILE button, K, or a click on
-- someone in the hub). three tabs:
--   PROFILE    anyone's card: the background and border they wear, their headshot, name, title, rank badge and XP
--              bar, the headline numbers (K/D, win %, headshot %, accuracy, kills, best streak), their three most
--              used weapons, their last matches and the loadout they carry. a private player shows only the top.
--   CUSTOMIZE  your own: pick a border, a background and a title (free ones and ones you own: Duffel Bags, the shop),
--              and the switch that hides your numbers from everyone else
--   PLAYERS    everyone in this server, as small cards: tap one to open theirs
-- the numbers are the server's (Stats.luau, the remote JankfireRemotes.Profile); the loadout is read off the player's
-- own attributes (LoadoutNext, Wraps, Hats). built from Theme; on a short or narrow screen (a phone) it fills the
-- screen, the body scrolls and every button is at least 44 px.
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local GuiService = game:GetService("GuiService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local T = require(script.Parent:WaitForChild("Theme"))
local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Ranks = require(Shared:WaitForChild("Ranks"))
local CardStyles = require(Shared:WaitForChild("CardStyles"))
local Roster = require(Shared:WaitForChild("Roster"))
local Arena = require(Shared:WaitForChild("Arena"))
local GunHats = require(Shared:WaitForChild("GunHats"))
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Profile") :: RemoteFunction

local me = Players.LocalPlayer
local UI = {}

local WIN = Color3.fromRGB(122, 196, 128)
local LOSS = Color3.fromRGB(214, 98, 92)

-- ------------------------------------------------------------------ small helpers
local new = T.new
local function txt(parent: Instance, s: string, size: number, color: Color3?, font: Font?, align: Enum.TextXAlignment?): TextLabel
	local l = T.text(parent, "Text", s, size, color, font, align)
	l.TextTruncate = Enum.TextTruncate.AtEnd
	return l
end
local function at(o: GuiObject, x: number, y: number, w: number, h: number): GuiObject
	o.Position = UDim2.fromOffset(x, y)
	o.Size = UDim2.fromOffset(w, h)
	return o
end
local function comma(n: number): string
	local s = tostring(math.floor(n + 0.5))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	return (out:gsub("^,", ""))
end
local function pct(a: number, b: number): string
	if b <= 0 then return "—" end
	return ("%d%%"):format(math.floor(a / b * 100 + 0.5))
end
local function ago(t: number?): string
	if not t then return "" end
	local d = os.time() - t
	if d < 60 then return "just now" end
	if d < 3600 then return ("%dm ago"):format(d // 60) end
	if d < 86400 then return ("%dh ago"):format(d // 3600) end
	return ("%dd ago"):format(d // 86400)
end
local function playtime(s: number): string
	if s < 60 then return ("%ds"):format(s) end
	if s < 3600 then return ("%dm"):format(s // 60) end
	return ("%dh %dm"):format(s // 3600, (s % 3600) // 60)
end
local function weaponName(id: string?): string
	local e = if id then Roster.byId[id] else nil
	return if e then e.name else (id or "—")
end
local function weaponColor(id: string?): Color3
	local e = if id then Roster.byId[id] else nil
	return (if e then e.color else T.DIM):Lerp(T.CARD, 0.35)
end
local function headshot(id: number): string
	return ("rbxthumb://type=AvatarHeadShot&id=%d&w=150&h=150"):format(id)
end

-- the ranked session's look for a rank: ReplicatedStorage.Jankfire.RankedStyle (badge(parent, size, ranked),
-- label(ranked), color(ranked)) when it is in the place; the card's `ranked` field is theirs (Stats.cardExtra)
local rankedMod: any = false
local function rankedStyle(): any
	if rankedMod == false then
		rankedMod = nil
		local m = Shared:FindFirstChild("RankedStyle")
		if m and m:IsA("ModuleScript") then
			local ok, r = pcall(require, m)
			if ok and type(r) == "table" and type(r.badge) == "function" then rankedMod = r end
		end
	end
	return rankedMod
end
-- the mark on the right of a card or a row (16 Nov, agreed with the ranked session: "rank" means ranked, the XP side
-- is a level): the ranked badge and its line, or with no ranked data a quiet plate with the level number.
-- returns the mark, the line under it and that line's colour
local function rankMark(parent: Instance, x: number, y: number, size: number, c: any): (GuiObject, string, Color3)
	local RS = rankedStyle()
	if RS and c.ranked ~= nil then
		local ok, f = pcall(RS.badge, parent, size, c.ranked)
		if ok and typeof(f) == "Instance" and f:IsA("GuiObject") then
			f.Position = UDim2.fromOffset(x, y)
			f.ZIndex = 3
			local okL, lab = pcall(RS.label, c.ranked)
			local okC, col = pcall(RS.color, c.ranked)
			return f, if okL and type(lab) == "string" then lab else "", if okC and typeof(col) == "Color3" then col else T.SOFT
		end
	end
	local lvl = Ranks.levelOf(tonumber(c.xp) or 0)
	local plate = new("Frame", { Name = "LevelMark", BackgroundColor3 = T.CARD_HI, BackgroundTransparency = 0.15, BorderSizePixel = 0, ZIndex = 3,
		Position = UDim2.fromOffset(x + math.floor(size * 0.12), y + math.floor(size * 0.12)), Size = UDim2.fromOffset(math.floor(size * 0.76), math.floor(size * 0.76)) }, parent)
	T.corner(plate, math.floor(size * 0.18))
	T.edge(plate, T.ACCENT, 0.55, 1.5)
	local n = T.text(plate, "Level", tostring(lvl), math.max(12, math.floor(size * 0.34)), T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
	n.Size = UDim2.fromScale(1, 1)
	n.ZIndex = 4
	return plate, "LEVEL " .. lvl, T.MUTED
end

-- ------------------------------------------------------------------ the screen
local gui = new("ScreenGui", { Name = "JankProfile", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 24,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, me:WaitForChild("PlayerGui"))
local scrim = new("TextButton", { Name = "Scrim", Text = "", AutoButtonColor = false, Modal = true, BackgroundColor3 = Color3.fromRGB(6, 7, 9),
	BackgroundTransparency = 0.35, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, gui)
local holder = new("Frame", { Name = "Holder", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, gui)
local panel = new("Frame", { Name = "Panel", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), BackgroundColor3 = T.BG,
	BorderSizePixel = 0, ClipsDescendants = false, Active = true }, holder) -- (Active: a click on the card never reaches the scrim, which closes it)
local panelCorner = T.corner(panel, 10)
local scale = new("UIScale", {}, panel)

type View = { tab: string, who: number, card: any?, owned: any?, list: { any }?, loading: boolean, why: string? }
local view: View = { tab = "profile", who = me.UserId, card = nil, owned = nil, list = nil, loading = false }
local isOpen = false
local fake: Vector2? = nil -- (a test: lay out as if the screen were this size)
local L = { compact = false, s = 1, W = 960, H = 640, btn = 36, pad = 22, hdr = 168, two = true }
local setFlag = false

local function screenSize(): Vector2
	if fake then return fake :: Vector2 end
	local cam = workspace.CurrentCamera
	return if cam then cam.ViewportSize else Vector2.new(1280, 720)
end

local function measure()
	local vs = screenSize()
	local top = GuiService.TopbarInset.Height
	if fake then top = 0 end
	local w, h = vs.X, vs.Y - top
	holder.Position = UDim2.fromOffset(0, top)
	holder.Size = UDim2.new(1, 0, 1, -top)
	if fake then
		holder.Size = UDim2.fromOffset(vs.X, vs.Y)
		holder.Position = UDim2.fromScale(0, 0)
	end
	L.compact = h < 600 or w < 760
	if L.compact then
		L.s = math.clamp(math.min(w / 520, h / 420), 0.7, 1.3)
		L.W, L.H = math.floor(w / L.s), math.floor(h / L.s)
		L.btn = math.max(36, math.ceil(46 / L.s))
		L.pad = 14
		L.hdr = 132
		panelCorner.CornerRadius = UDim.new(0, 0)
	else
		L.s = math.clamp(math.min(w / 1040, h / 700), 0.75, 2)
		L.W, L.H = 960, 640
		L.btn = 36
		L.pad = 22
		L.hdr = 168
		panelCorner.CornerRadius = UDim.new(0, 10)
	end
	L.two = L.W - L.pad * 2 >= 820
	scale.Scale = L.s
	panel.Size = UDim2.fromOffset(L.W, L.H)
end

local function invoke(...: any): any
	local ok, res = pcall(function(...) return Remote:InvokeServer(...) end, ...)
	if not ok or type(res) ~= "table" then return { ok = false, why = "no answer from the server" } end
	return res
end

-- ------------------------------------------------------------------ pieces
local function sectionTitle(parent: Instance, s: string, x: number, y: number, w: number): TextLabel
	local l = txt(parent, s, 12, T.MUTED, T.FONT_BOLD)
	at(l, x, y, w, 16)
	return l
end
local function card(parent: Instance, x: number, y: number, w: number, h: number, name: string?): Frame
	local f = new("Frame", { Name = name or "Card", BackgroundColor3 = T.CARD, BorderSizePixel = 0 }, parent)
	at(f, x, y, w, h)
	T.corner(f)
	return f
end
-- a flat button: text, optional selected look; returns the button
local function button(parent: Instance, s: string, x: number, y: number, w: number, h: number, selected: boolean?): TextButton
	local b = new("TextButton", { Name = "Button", AutoButtonColor = false, Text = s, FontFace = T.FONT_BOLD, TextSize = 13,
		TextColor3 = if selected then T.INK else T.TEXT, BackgroundColor3 = if selected then T.ACCENT else T.CARD, BorderSizePixel = 0 }, parent)
	at(b, x, y, w, h)
	T.corner(b)
	if not selected then
		b.MouseEnter:Connect(function() b.BackgroundColor3 = T.CARD_HI end)
		b.MouseLeave:Connect(function() b.BackgroundColor3 = T.CARD end)
	end
	return b
end
-- a drawn padlock (no glyph fonts): a body and a shackle
local function lock(parent: Instance, cx: number, cy: number, s: number, color: Color3)
	local body = new("Frame", { BorderSizePixel = 0, BackgroundColor3 = color, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromOffset(cx, cy - s * 0.05),
		Size = UDim2.fromOffset(s * 0.8, s * 0.6), ZIndex = 30 }, parent)
	T.corner(body, math.max(2, math.floor(s * 0.1)))
	local sh = new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.fromOffset(cx, cy + s * 0.05),
		Size = UDim2.fromOffset(s * 0.52, s * 0.5), ZIndex = 30 }, parent)
	new("UICorner", { CornerRadius = UDim.new(0.5, 0) }, sh)
	new("UIStroke", { Color = color, Thickness = math.max(2, math.floor(s * 0.11)) }, sh)
end

-- ------------------------------------------------------------------ the header (anyone's card top)
local function header(parent: Instance, c: any)
	local W = L.W
	local H = L.hdr
	local hdr = new("Frame", { Name = "Header", BackgroundColor3 = T.CARD, BorderSizePixel = 0, Size = UDim2.fromOffset(W, H) }, parent)
	if not L.compact then T.corner(hdr, 10) end
	CardStyles.paintBanner(hdr, c.look and c.look.banner, if L.compact then 0 else 10)
	-- a dark wash from the left and the bottom so the words read on a bright background
	local wash = new("Frame", { Name = "Wash", BackgroundColor3 = Color3.new(0, 0, 0), BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 2 }, hdr)
	if not L.compact then T.corner(wash, 10) end
	new("UIGradient", { Rotation = 0, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.25), NumberSequenceKeypoint.new(0.55, 0.62), NumberSequenceKeypoint.new(1, 0.85) }) }, wash)
	local pad = L.pad
	local av = if L.compact then 84 else 112
	local avBox = new("Frame", { Name = "Avatar", BackgroundColor3 = Color3.fromRGB(10, 11, 14), BackgroundTransparency = 0.2, BorderSizePixel = 0, ZIndex = 3 }, hdr)
	at(avBox, pad, (H - av) // 2 - (if L.compact then 4 else 6), av, av)
	T.corner(avBox, 10)
	T.edge(avBox, nil, 0.75)
	local img = new("ImageLabel", { BackgroundTransparency = 1, Image = headshot(c.id), Size = UDim2.fromScale(1, 1), ZIndex = 4 }, avBox)
	T.corner(img, 10)
	local rank = Ranks.of(c.xp)
	local bs = if L.compact then 76 else 96
	local right = W - L.btn - 22 - bs -- (left of the close button)
	local x = pad + av + (if L.compact then 14 else 20)
	local nameW = right - x - 12
	local name = txt(hdr, string.upper(c.display or c.name or "?"), if L.compact then 24 else 32, T.TEXT, T.FONT_TITLE)
	at(name, x, (H - av) // 2 - (if L.compact then 4 else 6), nameW, if L.compact then 28 else 36)
	name.ZIndex = 3
	-- @name, then the title (on a phone only one of them fits: the title if there is one)
	local lineY = name.Position.Y.Offset + name.Size.Y.Offset + 2
	local tt = CardStyles.titleText(c.look and c.look.title)
	if not L.compact or tt == "" then
		local sub = txt(hdr, "@" .. tostring(c.name or ""), 14, T.SOFT, T.FONT_BOLD)
		at(sub, x, lineY, nameW, 18)
		sub.ZIndex = 3
		lineY += 22
	end
	if tt ~= "" then
		local tl = txt(hdr, tt, 14, CardStyles.titleColor(c.look.title), T.FONT_HEAVY)
		at(tl, x, lineY, nameW, 18)
		tl.ZIndex = 3
	end
	-- the XP bar under the name
	local barY = (H - av) // 2 - (if L.compact then 4 else 6) + av - 10
	local lv = txt(hdr, ("LV %d"):format(rank.level), 13, T.TEXT, T.FONT_HEAVY)
	at(lv, x, barY - 18, 80, 16)
	lv.ZIndex = 3
	local xpl = txt(hdr, ("%s / %s XP"):format(comma(rank.into), comma(rank.need)), 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
	at(xpl, x, barY - 18, math.min(nameW, 360), 16)
	xpl.ZIndex = 3
	local track = new("Frame", { Name = "XpTrack", BackgroundColor3 = T.TRACK, BorderSizePixel = 0, ZIndex = 3 }, hdr)
	at(track, x, barY, math.min(nameW, 360), 6)
	T.corner(track, 3)
	local fill = new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromScale(math.max(0.02, rank.progress), 1), ZIndex = 4 }, track)
	T.corner(fill, 3)
	-- on the right: the ranked badge and its line (or the level), the line under it
	local mark, line, col = rankMark(hdr, right, (H - bs) // 2 - 12, bs, c)
	for _, d in mark:GetDescendants() do if d:IsA("GuiObject") then d.ZIndex += 3 end end
	local rn = txt(hdr, line, if L.compact then 12 else 14, col, T.FONT_TITLE, Enum.TextXAlignment.Center)
	at(rn, right - 50, (H - bs) // 2 - 12 + bs - 6, bs + 100, 18)
	rn.ZIndex = 3
	return hdr
end

-- ------------------------------------------------------------------ PROFILE: the numbers
local function privatePlate(parent: Instance, y: number, W: number): number
	local f = card(parent, 0, y, W, 120, "Private")
	lock(f, W / 2, 34, 30, T.MUTED)
	local a = txt(f, "STATS HIDDEN", 16, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Center)
	at(a, 0, 62, W, 20)
	local b = txt(f, "this player keeps their numbers to themselves", 13, T.MUTED, T.FONT, Enum.TextXAlignment.Center)
	at(b, 0, 86, W, 18)
	return y + 120
end

local function statsBlock(parent: Instance, y: number, W: number, s: any): number
	local tiles = {
		{ "K/D", if s.d > 0 then ("%.2f"):format(s.k / s.d) else (if s.k > 0 then ("%.2f"):format(s.k) else "—") },
		{ "WIN RATE", pct(s.w, s.m) },
		{ "HEADSHOT %", pct(s.hs, s.hc) },
		{ "ACCURACY", pct(s.hi, s.sh) },
		{ "KILLS", comma(s.k) },
		{ "BEST STREAK", tostring(s.best) },
	}
	local cols = if W >= 760 then 6 else 3
	local gap = 10
	local tw = (W - gap * (cols - 1)) / cols
	local th = if L.compact then 70 else 84
	for i, t in tiles do
		local col, row = (i - 1) % cols, (i - 1) // cols
		local f = card(parent, col * (tw + gap), y + row * (th + gap), tw, th, "Tile")
		local v = txt(f, t[2], if L.compact then 24 else 30, T.TEXT, T.FONT_HEAVY)
		at(v, 14, 10, tw - 24, if L.compact then 30 else 36)
		local l = txt(f, t[1], 11, T.MUTED, T.FONT_BOLD)
		at(l, 14, th - 26, tw - 24, 14)
	end
	local rows = math.ceil(#tiles / cols)
	y += rows * (th + gap)
	-- the smaller facts in one plate
	local facts = {
		{ "MATCHES", comma(s.m) }, { "WINS", comma(s.w) }, { "DEATHS", comma(s.d) }, { "ROUNDS WON", comma(s.rw) },
		{ "DAMAGE", comma(s.dmg) }, { "TIME IN MATCHES", playtime(s.time) },
	}
	local fc = if W >= 760 then 6 else 3
	local fh = 46
	local fw = W / fc
	local plate = card(parent, 0, y, W, fh * math.ceil(#facts / fc), "Facts")
	plate.BackgroundTransparency = 0.4
	for i, f in facts do
		local col, row = (i - 1) % fc, (i - 1) // fc
		local a = txt(plate, f[1], 10, T.DIM, T.FONT_BOLD)
		at(a, col * fw + 14, row * fh + 7, fw - 20, 12)
		local b = txt(plate, f[2], 16, T.SOFT, T.FONT_BOLD)
		at(b, col * fw + 14, row * fh + 21, fw - 20, 18)
	end
	return y + plate.Size.Y.Offset
end

local function weaponsBlock(parent: Instance, y: number, x: number, W: number, list: { any }?): number
	sectionTitle(parent, "MOST USED", x, y, W)
	y += 24
	local rows = list or {}
	if #rows == 0 then
		local f = card(parent, x, y, W, 64, "Empty")
		local l = txt(f, "no matches yet: play one from a pad in the hub", 13, T.MUTED, T.FONT, Enum.TextXAlignment.Center)
		at(l, 0, 0, W, 64)
		return y + 64
	end
	local rh = if L.compact then 66 else 70
	for i = 1, math.min(3, #rows) do
		local w = rows[i]
		local f = card(parent, x, y, W, rh, "Weapon")
		local num = txt(f, tostring(i), 20, T.DIM, T.FONT_HEAVY, Enum.TextXAlignment.Center)
		at(num, 6, 0, 30, rh)
		local chip = new("Frame", { BackgroundColor3 = weaponColor(w.id), BorderSizePixel = 0 }, f)
		at(chip, 40, 14, 4, rh - 28)
		T.corner(chip, 2)
		local n = txt(f, string.upper(weaponName(w.id)), 15, T.TEXT, T.FONT_BOLD)
		at(n, 54, 10, W - 140, 20)
		local share = txt(f, ("%d%%"):format(math.floor((w.share or 0) * 100 + 0.5)), 15, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
		at(share, W - 80, 10, 66, 20)
		local track = new("Frame", { BackgroundColor3 = T.TRACK, BorderSizePixel = 0 }, f)
		at(track, 54, 34, W - 68, 5)
		T.corner(track, 3)
		local fill = new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromScale(math.max(0.02, w.share or 0), 1) }, track)
		T.corner(fill, 3)
		local sub = txt(f, ("%s kills  ·  %s hit rate  ·  %s"):format(comma(w.k), pct(w.h, w.s), playtime(w.t)), 12, T.MUTED, T.FONT)
		at(sub, 54, 44, W - 68, 16)
		y += rh + 8
	end
	return y - 8
end

local function recentBlock(parent: Instance, y: number, x: number, W: number, list: { any }?): number
	sectionTitle(parent, "RECENT MATCHES", x, y, W)
	y += 24
	local rows = list or {}
	if #rows == 0 then
		local f = card(parent, x, y, W, 64, "Empty")
		local l = txt(f, "nothing played yet", 13, T.MUTED, T.FONT, Enum.TextXAlignment.Center)
		at(l, 0, 0, W, 64)
		return y + 64
	end
	local rh = if L.compact then 44 else 40
	for i, r in rows do
		if i > 10 then break end
		local f = card(parent, x, y, W, rh, "Match")
		f.BackgroundTransparency = if i % 2 == 0 then 0.25 else 0
		local won = r.r == "W"
		local bar = new("Frame", { BackgroundColor3 = if won then WIN else LOSS, BorderSizePixel = 0 }, f)
		at(bar, 0, 0, 4, rh)
		local res = txt(f, if won then "WIN" else "LOSS", 13, if won then WIN else LOSS, T.FONT_HEAVY)
		at(res, 14, 0, 46, rh)
		local sc = txt(f, tostring(r.sc or ""), 13, T.TEXT, T.FONT_BOLD)
		at(sc, 58, 0, 40, rh)
		local mapW = math.max(80, W - 98 - 200)
		local where = txt(f, ("%s  ·  %s"):format(Arena.title(r.map), string.upper(tostring(r.mode or ""))), 12, T.SOFT, T.FONT_BOLD)
		at(where, 100, 0, mapW, rh)
		local kd = txt(f, ("%d / %d"):format(r.k or 0, r.d or 0), 13, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
		at(kd, W - 196, 0, 50, rh)
		local wn = txt(f, string.upper(weaponName(r.w)), 11, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
		at(wn, W - 142, 0, 84, rh)
		local when = txt(f, ago(r.t), 11, T.DIM, T.FONT, Enum.TextXAlignment.Right)
		at(when, W - 60, 0, 50, rh)
		y += rh + 4
	end
	return y - 4
end

-- what they carry: keys 1 2 3 and G, with each gun's wrap and hat (the player's own attributes)
local function loadoutBlock(parent: Instance, y: number, W: number, who: Player?): number
	sectionTitle(parent, "LOADOUT", 0, y, W)
	y += 24
	local picks = if who then string.split(tostring(who:GetAttribute("LoadoutNext") or ""), ",") else {}
	local wraps, hats = {}, {}
	if who then
		for part in string.gmatch(tostring(who:GetAttribute("Wraps") or ""), "[^;]+") do
			local w, id = string.match(part, "^([%w_]+)=([%w_]+)")
			if w then wraps[w] = id end
		end
		for part in string.gmatch(tostring(who:GetAttribute("Hats") or ""), "[^;]+") do
			local w, id = string.match(part, "^([%w_]+)=([%w_]+)")
			if w then hats[w] = id end
		end
	end
	if #picks < 4 or picks[1] == "" then
		local f = card(parent, 0, y, W, 56, "Empty")
		local l = txt(f, if who then "loadout still loading" else "they've left the server", 13, T.MUTED, T.FONT, Enum.TextXAlignment.Center)
		at(l, 0, 0, W, 56)
		return y + 56
	end
	local cols = if W >= 640 then 4 else 2
	local gap = 10
	local tw = (W - gap * (cols - 1)) / cols
	local th = 72
	for i, slot in Roster.SLOTS do
		local wid = picks[i]
		local col, row = (i - 1) % cols, (i - 1) // cols
		local f = card(parent, col * (tw + gap), y + row * (th + gap), tw, th, "Slot")
		local chip = new("Frame", { BackgroundColor3 = weaponColor(wid), BorderSizePixel = 0 }, f)
		at(chip, 0, 0, 4, th)
		local s = txt(f, Roster.SLOT_NAMES[slot] or slot, 10, T.DIM, T.FONT_BOLD)
		at(s, 14, 9, tw - 24, 12)
		local n = txt(f, string.upper(weaponName(wid)), 14, T.TEXT, T.FONT_BOLD)
		at(n, 14, 24, tw - 24, 18)
		local bits = {}
		local wr = wraps[wid]
		if wr and Roster.wrapById[wr] then table.insert(bits, Roster.wrapById[wr].name) end
		local h = hats[wid]
		if h and GunHats.HATS[h] then table.insert(bits, GunHats.HATS[h].name) end
		local d = txt(f, if #bits > 0 then table.concat(bits, "  ·  ") else (if slot == "utility" then "item" else "no wrap"), 12, T.MUTED, T.FONT)
		at(d, 14, 46, tw - 24, 16)
	end
	return y + math.ceil(4 / cols) * (th + gap) - gap
end

-- ------------------------------------------------------------------ CUSTOMIZE: your border, background, title
local function customizeBlock(parent: Instance, y: number, W: number, c: any, owned: any?): number
	-- the privacy switch first: it decides what the rest of the server sees
	local row = card(parent, 0, y, W, math.max(64, L.btn + 20), "Privacy")
	local a = txt(row, "HIDE MY STATS", 14, T.TEXT, T.FONT_BOLD)
	at(a, 16, 12, W - 140, 18)
	local b = txt(row, "others see your name, rank and card, not your numbers", 12, T.MUTED, T.FONT)
	at(b, 16, 32, W - 140, 16)
	local on = c.private == true
	local sw = new("TextButton", { Name = "Switch", AutoButtonColor = false, Text = "", BackgroundColor3 = if on then T.ACCENT else T.TRACK, BorderSizePixel = 0 }, row)
	local sh = math.max(30, L.btn - 8)
	at(sw, W - 16 - sh * 1.9, (row.Size.Y.Offset - sh) / 2, sh * 1.9, sh)
	T.corner(sw, sh // 2)
	local knob = new("Frame", { BackgroundColor3 = T.TEXT, BorderSizePixel = 0, Size = UDim2.fromOffset(sh - 8, sh - 8),
		Position = if on then UDim2.new(1, -(sh - 4), 0, 4) else UDim2.fromOffset(4, 4) }, sw)
	T.corner(knob, (sh - 8) // 2)
	sw.MouseButton1Click:Connect(function()
		local res = invoke("private", not on)
		if res.ok and view.card then view.card.private = res.private; UI.refresh() end
	end)
	y += row.Size.Y.Offset + 16
	local look = c.look or CardStyles.DEFAULT
	for _, t in CardStyles.TYPES do
		sectionTitle(parent, string.upper(CardStyles.TYPE_NAMES[t]) .. "S", 0, y, W)
		y += 24
		local ids = CardStyles.ORDER[t]
		local tw = if L.compact then 150 else 168
		local th = if t == "title" then math.max(52, L.btn + 8) else 92
		local gap = 10
		local cols = math.max(2, math.floor((W + gap) / (tw + gap)))
		tw = (W - gap * (cols - 1)) / cols
		for i, id in ids do
			local info = CardStyles.info(t, id)
			if not info then continue end
			local col, r = (i - 1) % cols, (i - 1) // cols
			local has = info.rarity == "free" or (owned ~= nil and owned[t] ~= nil and owned[t][id] == true)
			local picked = look[t] == id
			local tile = new("TextButton", { Name = "Tile_" .. id, AutoButtonColor = false, Text = "", BackgroundColor3 = T.CARD, BorderSizePixel = 0 }, parent)
			at(tile, col * (tw + gap), y + r * (th + gap + 18), tw, th)
			T.corner(tile, 6)
			local sample = new("Frame", { Name = "Sample", BackgroundColor3 = T.CARD, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, tile)
			T.corner(sample, 6)
			CardStyles.preview(t, id, sample)
			if picked then
				-- (an amber ring just outside the tile, over the sample's own border, and a tick in its corner)
				local ring = new("Frame", { Name = "Picked", BackgroundTransparency = 1, Position = UDim2.fromOffset(-4, -4), Size = UDim2.new(1, 8, 1, 8), ZIndex = 40 }, tile)
				T.corner(ring, 9)
				new("UIStroke", { Color = T.ACCENT, Thickness = 2 }, ring)
				local tick = new("Frame", { Name = "Tick", AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -6, 0, 6), Size = UDim2.fromOffset(18, 18),
					BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, ZIndex = 41 }, tile)
				T.corner(tick, 9)
				-- (a drawn check: two bars)
				new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(7, 10), Size = UDim2.fromOffset(6, 2), Rotation = 45, BackgroundColor3 = T.INK, BorderSizePixel = 0, ZIndex = 42 }, tick)
				new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(11, 8.5), Size = UDim2.fromOffset(9, 2), Rotation = -50, BackgroundColor3 = T.INK, BorderSizePixel = 0, ZIndex = 42 }, tick)
			end
			if not has then
				local dim = new("Frame", { BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0.45, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 29 }, tile)
				T.corner(dim, 6)
				lock(tile, tw / 2, th / 2 - 4, 22, T.SOFT)
			end
			local rc = CardStyles.RARITY_COLOR[info.rarity] or T.DIM
			local cap = txt(parent, string.upper(info.name), 11, if has then T.SOFT else T.DIM, T.FONT_BOLD)
			at(cap, col * (tw + gap) + 2, y + r * (th + gap + 18) + th + 2, tw - 50, 14)
			local rar = txt(parent, string.upper(info.rarity), 10, rc, T.FONT_BOLD, Enum.TextXAlignment.Right)
			at(rar, col * (tw + gap) + tw - 70, y + r * (th + gap + 18) + th + 2, 68, 14)
			tile.MouseButton1Click:Connect(function()
				if not has then
					view.why = if info.rarity == CardStyles.VIP_ONLY then ("%s: VIP pack only"):format(info.name)
						else ("%s: from Duffel Bags or the shop"):format(info.name)
					UI.refresh()
					return
				end
				if picked then return end
				local res = invoke("look", t, id)
				if res.ok and view.card then view.card.look = res.look; view.why = nil else view.why = res.why end
				UI.refresh()
			end)
		end
		y += math.ceil(#ids / cols) * (th + gap + 18) + 8
	end
	return y
end

-- ------------------------------------------------------------------ PLAYERS: everyone here
local function playersBlock(parent: Instance, y: number, W: number, list: { any }?): number
	local rows = list or {}
	table.sort(rows, function(a, b)
		if a.id == me.UserId then return true end
		if b.id == me.UserId then return false end
		return (a.xp or 0) > (b.xp or 0)
	end)
	sectionTitle(parent, ("IN THIS SERVER  ·  %d"):format(#rows), 0, y, W)
	y += 24
	local rh = math.max(68, L.btn + 20)
	local cols = if W >= 820 then 2 else 1
	local gap = 10
	local rw = (W - gap * (cols - 1)) / cols
	for i, r in rows do
		local col, row = (i - 1) % cols, (i - 1) // cols
		local b = new("TextButton", { Name = "Player_" .. r.id, AutoButtonColor = false, Text = "", BackgroundColor3 = T.CARD, BorderSizePixel = 0, ClipsDescendants = false }, parent)
		at(b, col * (rw + gap), y + row * (rh + gap), rw, rh)
		T.corner(b, 8)
		CardStyles.paintBanner(b, r.look and r.look.banner, 8)
		CardStyles.paintBorder(b, r.look and r.look.border, 8)
		local wash = new("Frame", { BackgroundColor3 = Color3.new(0, 0, 0), BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 2 }, b)
		T.corner(wash, 8)
		new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.3), NumberSequenceKeypoint.new(1, 0.75) }) }, wash)
		local av = rh - 20
		local img = new("ImageLabel", { BackgroundColor3 = Color3.fromRGB(10, 11, 14), BackgroundTransparency = 0.3, Image = headshot(r.id), ZIndex = 3 }, b)
		at(img, 10, 10, av, av)
		T.corner(img, 6)
		local rank = Ranks.of(r.xp)
		local n = txt(b, string.upper(r.display or r.name), 16, T.TEXT, T.FONT_TITLE)
		at(n, 20 + av, 12, rw - av - 170, 20)
		n.ZIndex = 3
		local tt = CardStyles.titleText(r.look and r.look.title)
		local s2 = txt(b, if tt ~= "" then tt else ("@" .. r.name), 12, if tt ~= "" then CardStyles.titleColor(r.look.title) else T.MUTED, T.FONT_BOLD)
		at(s2, 20 + av, 34, rw - av - 170, 16)
		s2.ZIndex = 3
		local bs = rh - 22
		local mark = rankMark(b, rw - bs - 54, 6, bs, r)
		for _, d in mark:GetDescendants() do if d:IsA("GuiObject") then d.ZIndex += 3 end end
		local lv = txt(b, ("LV %d"):format(rank.level), 13, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
		at(lv, rw - 58, 0, 46, rh)
		lv.ZIndex = 3
		if r.id == me.UserId then
			local you = txt(b, "YOU", 10, T.INK, T.FONT_HEAVY, Enum.TextXAlignment.Center)
			you.BackgroundTransparency = 0
			you.BackgroundColor3 = T.ACCENT
			at(you, rw - bs - 54 - 44, (rh - 15) // 2, 34, 15) -- (left of the badge, clear of the name and title)
			you.ZIndex = 3
			T.corner(you, 3)
		end
		b.MouseButton1Click:Connect(function() UI.open(r.id, "profile") end)
	end
	return y + math.ceil(#rows / cols) * (rh + gap) - gap
end

-- ------------------------------------------------------------------ drawing the whole screen
local body: ScrollingFrame? = nil
local function draw()
	measure()
	for _, c in panel:GetChildren() do
		if c:IsA("GuiObject") then c:Destroy() end
		if c.Name == "Banner" or c.Name == "Border" then c:Destroy() end
	end
	local c = view.card
	local own = view.who == me.UserId
	panel.BackgroundColor3 = T.BG
	-- the header (the card's top) and the border round the whole card
	local hdrH = L.hdr
	if c then
		header(panel, c)
		CardStyles.paintBorder(panel, c.look and c.look.border, if L.compact then 0 else 10)
	else
		local h = new("Frame", { Name = "Header", BackgroundColor3 = T.CARD, BorderSizePixel = 0, Size = UDim2.fromOffset(L.W, hdrH) }, panel)
		if not L.compact then T.corner(h, 10) end
		local l = txt(h, if view.loading then "LOADING" else (view.why or ""), 16, T.MUTED, T.FONT_TITLE, Enum.TextXAlignment.Center)
		at(l, 0, 0, L.W, hdrH)
		CardStyles.paintBorder(panel, "hairline", if L.compact then 0 else 10)
	end
	-- close, top right over the header
	local cs = L.btn
	local close = new("TextButton", { Name = "Close", AutoButtonColor = false, Text = "", BackgroundColor3 = T.BG, BackgroundTransparency = 0.2, BorderSizePixel = 0, ZIndex = 40 }, panel)
	at(close, L.W - cs - 10, 10, cs, cs)
	T.corner(close, 6)
	for _, rot in { 45, -45 } do
		new("Frame", { AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(math.floor(cs * 0.45), 2), Rotation = rot,
			BackgroundColor3 = T.TEXT, BorderSizePixel = 0, ZIndex = 41 }, close)
	end
	close.MouseButton1Click:Connect(function() UI.close() end)
	-- the tabs
	local ty = hdrH + 10
	local tabs = { { "profile", "PROFILE" }, { "customize", "CUSTOMIZE" }, { "players", "PLAYERS" } }
	local tx = L.pad
	local tw = if L.compact then 118 else 128
	for _, t in tabs do
		local b = button(panel, t[2], tx, ty, tw, L.btn, view.tab == t[1])
		b.Name = "Tab_" .. t[1]
		b.MouseButton1Click:Connect(function()
			if t[1] == "customize" and not own then UI.open(me.UserId, "customize") else UI.tab(t[1]) end
		end)
		tx += tw + 8
	end
	if view.why and view.tab ~= "players" then
		local w = txt(panel, view.why, 12, T.ACCENT, T.FONT_BOLD, Enum.TextXAlignment.Right)
		at(w, tx, ty, L.W - tx - L.pad, L.btn)
	end
	-- the body: one scrolling column
	local by = ty + L.btn + 12
	local sf = new("ScrollingFrame", { Name = "Body", BackgroundTransparency = 1, BorderSizePixel = 0, ScrollBarThickness = if L.compact then 4 else 6,
		ScrollBarImageColor3 = T.DIM, CanvasSize = UDim2.new(), ScrollingDirection = Enum.ScrollingDirection.Y, ElasticBehavior = Enum.ElasticBehavior.WhenScrollable }, panel)
	at(sf, L.pad, by, L.W - L.pad * 2 + (if L.compact then 0 else 8), L.H - by - L.pad)
	body = sf
	local W = L.W - L.pad * 2
	local y = 0
	if view.tab == "players" then
		if view.list then y = playersBlock(sf, y, W, view.list)
		else at(txt(sf, "LOADING", 14, T.MUTED, T.FONT_TITLE, Enum.TextXAlignment.Center), 0, 0, W, 60); y = 60 end
	elseif c and view.tab == "customize" and own then
		y = customizeBlock(sf, y, W, c, view.owned)
	elseif c then
		if c.stats then
			y = statsBlock(sf, y, W, c.stats) + 18
			if L.two then
				local half = (W - 18) / 2
				local y1 = weaponsBlock(sf, y, 0, half, c.weapons)
				local y2 = recentBlock(sf, y, half + 18, half, c.recent)
				y = math.max(y1, y2) + 18
			else
				y = weaponsBlock(sf, y, 0, W, c.weapons) + 18
				y = recentBlock(sf, y, 0, W, c.recent) + 18
			end
		else
			y = privatePlate(sf, y, W) + 18
		end
		y = loadoutBlock(sf, y, W, Players:GetPlayerByUserId(view.who))
	end
	sf.CanvasSize = UDim2.fromOffset(0, y + 12)
end

-- ------------------------------------------------------------------ opening and closing
local fetchId = 0
local function fetch()
	fetchId += 1
	local id = fetchId
	view.loading = true
	task.spawn(function()
		if view.tab == "players" then
			local res = invoke("list")
			if id ~= fetchId then return end
			view.list = if res.ok then res.players else {}
			if not view.card then
				local r2 = invoke("card", view.who)
				if id ~= fetchId then return end
				view.card = if r2.ok then r2.card else nil
			end
		else
			local res = invoke("card", view.who)
			if id ~= fetchId then return end
			view.card = if res.ok then res.card else nil
			if not res.ok then view.why = res.why end
			if view.who == me.UserId then
				local o = invoke("owned")
				if id ~= fetchId then return end
				view.owned = if o.ok then o.owned else nil
			end
		end
		view.loading = false
		if isOpen then draw() end
	end)
end

local function setMenuFlag(on: boolean)
	if on then
		if not me:GetAttribute("LoadoutOpen") then me:SetAttribute("LoadoutOpen", true); setFlag = true end
	elseif setFlag then
		setFlag = false
		me:SetAttribute("LoadoutOpen", false)
	end
	me:SetAttribute("ProfileOpen", on)
end

-- open a card: userId (nil = yours), tab "profile" | "customize" | "players"
function UI.open(userId: number?, tab: string?)
	local who = userId or me.UserId
	if who ~= view.who then view.card = nil end
	view.who = who
	view.tab = tab or "profile"
	if view.tab == "customize" and who ~= me.UserId then view.tab = "profile" end
	view.why = nil
	if not isOpen then
		isOpen = true
		gui.Enabled = true
		setMenuFlag(true)
	end
	draw()
	fetch()
end
function UI.tab(t: string)
	if t == "customize" and view.who ~= me.UserId then UI.open(me.UserId, "customize"); return end
	view.tab = t
	view.why = nil
	draw()
	fetch()
end
function UI.refresh() if isOpen then draw() end end
function UI.close()
	if not isOpen then return end
	isOpen = false
	gui.Enabled = false
	setMenuFlag(false)
	body = nil
	for _, c in panel:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
end
function UI.isOpen(): boolean return isOpen end
function UI.toggle(tab: string?)
	if isOpen and (tab == nil or view.tab == tab) then UI.close() else UI.open(if tab == "customize" then me.UserId else (if isOpen then view.who else me.UserId), tab) end
end
-- (tests: lay out for a screen of this size, nil = the real one)
function UI.fakeScreen(v: Vector2?)
	fake = v
	if isOpen then draw() end
end
function UI.scrollTo(y: number) if body then body.CanvasPosition = Vector2.new(0, y) end end

scrim.MouseButton1Click:Connect(function() UI.close() end)
local cam = workspace.CurrentCamera
if cam then
	cam:GetPropertyChangedSignal("ViewportSize"):Connect(function() if isOpen and not fake then task.defer(draw) end end)
end
UIS.InputBegan:Connect(function(io)
	if isOpen and io.KeyCode == Enum.KeyCode.Escape then UI.close() end
end)

return UI
