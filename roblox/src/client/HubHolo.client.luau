--!nonstrict
-- the hub's holograms, drawn on your screen only (the server has nothing but their places: invisible drums tagged
-- "HubHolo" that HubRotunda builds, the size of the space a hologram may fill, which its check tests the sight
-- lines against). owner, 16 Nov 2026: "in the hub can the center gun thingy cycle your loadout but hologram style? we
-- also need holograms like in rivals with bundle sets that float and people can look at and interact with"
--   Holo = "loadout"  the ring over the platform: YOUR loadout, primary, secondary, melee, utility in turn, each in your
--                     wrap with your hat, turning slowly; the old one fades, a scan line builds the next from the bottom
--   Holo = "bundle"   the showroom's plinths (attribute Slot 1..4): one bundle from the shop's catalogue on each, its
--                     pieces in turn; its name on the plate over it; walk up and a card says what's in it; the prompt
--                     (E, or a click on it) opens the shop on that bundle
-- the look: the real model, see-through, a soft fill and outline in the palette's accent (attribute Color on the
-- place), a faint beam up from the lens under it, a little light. calm: no flicker, no glitches
local CollectionService = game:GetService("CollectionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Roster = require(Shared:WaitForChild("Roster"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local GunHats = require(Shared:WaitForChild("GunHats"))
local Items = require(Shared:WaitForChild("Items"))
local me = Players.LocalPlayer

local TAG = "HubHolo"
local SEE = 0.3 -- how see-through a hologram's pieces are (on top of their own transparency)
local FILL, EDGE = 0.8, 0.4 -- the Highlight's fill and outline transparency when fully shown
local SHOW = { loadout = 5, bundle = 3.6 } -- seconds each piece stays
local OUT, IN = 0.45, 1.5 -- the fade out, the scan line's build (from the lens up through the whole piece)
local SPIN = 0.32 -- rad/s
local FAR = 220 -- studs: nothing moves past this
local NEAR = 13 -- studs from a plinth: its card shows
local FONT = "rbxasset://fonts/families/Montserrat.json"
local SLOT_WORD = { primary = "PRIMARY", secondary = "SECONDARY", melee = "MELEE", utility = "UTILITY" }

-- ---------------------------------------------------------------- the models (as the loadout screen builds its previews)
local Tools = ReplicatedStorage:WaitForChild("JankfireTools", 10)
local ITEM = { frag = "x_frag", smoke = "x_smoke", medkit = "x_medkit", bubble = "x_bubble", popper = "x_popper", reverse = "x_reverse",
	duck = "x_duck", quiz = "x_calc", laptop = "x_laptop", nvg = "x_nvg", radar = "x_radar", camera = "x_camera", wand = "x_wand" }
local function itemModel(id: string): Model?
	local lib = ReplicatedStorage:FindFirstChild("JankfireItems")
	local t = lib and lib:FindFirstChild(ITEM[id] or ("x_" .. id))
	return if t and t:IsA("Model") then t:Clone() else nil
end
local function shredderModel(): Model?
	local src = Tools and Tools:FindFirstChild("Shredder")
	if not src then return nil end
	local m = Instance.new("Model")
	local big: BasePart? = nil
	for _, d in src:GetDescendants() do
		if d:IsA("BasePart") and d.Transparency < 0.99 and d.Name ~= "SuckField" then
			local c = d:Clone()
			for _, x in c:GetChildren() do
				if not (x:IsA("SurfaceAppearance") or x:IsA("SpecialMesh") or x:IsA("Decal") or x:IsA("Texture")) then x:Destroy() end
			end
			c.Parent = m
			if not big or c.Size.Magnitude > big.Size.Magnitude then big = c end
		end
	end
	m.PrimaryPart = big
	return m
end
local QUIET = { "Sound", "ParticleEmitter", "Light", "Beam", "Trail", "LuaSourceContainer", "ProximityPrompt", "BillboardGui", "ClickDetector", "Smoke", "Fire", "Sparkles" }

-- one piece as a model fitted into the hologram's space (r across from its axis, h tall), its box's middle at the
-- origin: { model, rel (pivot -> box middle) } or nil. piece = { w = weapon or item id, wrap, mode, hat }
local function build(piece, r: number, h: number): (Model?, CFrame)
	local id = piece.w
	local e = Roster.byId[id]
	if not e or not e.live then return nil, CFrame.identity end
	local m: Model?
	if e.slot == "utility" then m = itemModel(id)
	elseif id == "shredder" then
		m = shredderModel()
		-- (the Tool may still be waiting for its pieces: then the weapon's own model, then the racks' template)
		if not m or not m:FindFirstChildWhichIsA("BasePart", true) then
			if m then m:Destroy() end
			m = WeaponModels.build(id, 3)
			if not m then
				local lib = ReplicatedStorage:FindFirstChild("JankfireWeapons")
				local t = lib and lib:FindFirstChild("w_shredder")
				m = if t and t:IsA("Model") then t:Clone() else nil
			end
		end
	else m = WeaponModels.build(id, 3, piece.skin) end -- (a set bundle's hero may wear a weapon skin: its own body instead of the plain gun)
	if not m then return nil, CFrame.identity end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false; d.Massless = true
		else
			for _, c in QUIET do if d:IsA(c) then d:Destroy(); break end end
		end
	end
	-- its hat goes on after it is measured, so a hat never shrinks the weapon or moves it off the axis
	local hat = piece.hat
	local hm = nil
	if hat and hat ~= "none" and e.slot ~= "utility" and GunHats.valid(hat) then
		local ok, res = pcall(function()
			return if id == "shredder" then GunHats.attachToolCopy(m, Tools:FindFirstChild("Shredder") :: Instance, hat) else GunHats.attach(m, id, hat, 3, true)
		end)
		if ok then hm = res end
	end
	if hm then hm.Parent = nil end
	-- (it is shown in its own box's frame, as the loadout screen shows it: the box's Y is up, and it turns about that;
	-- what it fills is the circle its plan's corners sweep, and its height. a first try kept the turn it was built in,
	-- and the bundles' guns stood on end)
	local _, size = m:GetBoundingBox()
	local tall, plan = size.Y, math.sqrt(size.X * size.X + size.Z * size.Z)
	local k = math.min((2 * r) / math.max(plan, 1e-3), h / math.max(tall, 1e-3))
	if math.abs(k - 1) > 1e-3 then pcall(function() m:ScaleTo(m:GetScale() * k) end) end
	local bcf = m:GetBoundingBox()
	if hm then hm.Parent = m end
	if piece.wrap and piece.wrap ~= "default" then pcall(WeaponModels.wrap, m, piece.wrap, piece.mode or "normal") end
	return m, m:GetPivot():ToObjectSpace(bcf)
end

-- ---------------------------------------------------------------- names
local function nameOf(id: string): string
	local e = Roster.byId[id]
	return string.upper(if e then e.name else id)
end
local function wrapName(id: string?): string?
	if not id or id == "default" then return nil end
	local w = Roster.wrapById[id]
	return w and w.name or nil
end
local function hatName(id: string?): string?
	if not id or id == "none" then return nil end
	local h = GunHats.HATS[id]
	return h and h.name or nil
end
local function detail(p: any): string
	local bits = {}
	local wn = wrapName(p.wrap)
	if wn then table.insert(bits, wn .. " wrap") end
	local hn = hatName(p.hat)
	if hn then table.insert(bits, hn) end
	if #bits == 0 and Roster.byId[p.w] and Roster.byId[p.w].slot == "utility" then
		local it = Items.list[p.w]
		if it then table.insert(bits, ("%d %s"):format(it.charges, if it.charges == 1 then "charge" else "charges")) end
	end
	return table.concat(bits, "  ·  ")
end

-- ---------------------------------------------------------------- the shop's catalogue and its door
-- the shop session's catalogue (a ModuleScript: ShopCatalog or Shop with .bundles) gives the bundles; until it is there
-- four stand-in sets made of what the game has. a bundle: { id, name, pieces = { { w, wrap, mode, hat } }, price }
local STAND_IN = {
	{ id = "standin_night", name = "NIGHT SHIFT", pieces = { { w = "ar", wrap = "galaxy", hat = "tophat" }, { w = "pistol", wrap = "galaxy" }, { w = "katana", wrap = "matte" } } },
	{ id = "standin_tiger", name = "BIG CAT", pieces = { { w = "smg", wrap = "tiger", hat = "crown" }, { w = "revolver", wrap = "tiger" }, { w = "frag" } } },
	{ id = "standin_steel", name = "COLD STEEL", pieces = { { w = "sniper", wrap = "damascus", hat = "halo" }, { w = "katana", wrap = "damascus" }, { w = "sawnoff", wrap = "brushed" } } },
	{ id = "standin_garden", name = "KOI GARDEN", pieces = { { w = "redline", wrap = "koi", hat = "duck" }, { w = "marbles", wrap = "jade" }, { w = "duck" } } },
}
local function shopModule(names: { string }): any
	for _, where in { Shared, ReplicatedStorage } do
		for _, n in names do
			local m = where:FindFirstChild(n)
			if m and m:IsA("ModuleScript") then
				local ok, api = pcall(require, m)
				if ok and type(api) == "table" then return api end
			end
		end
	end
	return nil
end
-- a piece from whatever shape the catalogue gives (tolerant: weapon / w / id, wrap, mode, hat)
local function pieceOf(x: any): any
	if type(x) ~= "table" then return nil end
	local w = x.w or x.weapon or x.wid or (if x.kind == "item" or x.kind == "utility" or x.kind == "weapon" then x.id else nil)
	if type(w) ~= "string" or not Roster.byId[w] then return nil end
	return { w = w, wrap = x.wrap, mode = x.mode or x.wrapMode, hat = x.hat }
end
-- the shop's catalogue (the shop session, 16 Nov: ReplicatedStorage.Jankfire.Shop): Shop.bundles = { { id, name, rarity,
-- blurb, robux, items = { { kind = "wrap" | "hat", id } }, hero = { weapon, wrap, hat } } }; Shop.rotation().hero = today's
-- featured bundle (on plinth 1); Shop.itemInfo(kind, id) -> name, rarity; Shop.RARITY[r].color; Shop.free() = prices off.
-- a hologram shows the hero (its weapon in its wrap with its hat), then each item on the hero's weapon
local function rarityColor(cat: any, r: any): Color3?
	local row = cat and cat.RARITY and cat.RARITY[r]
	local c = row and row.color
	if typeof(c) == "Color3" then return c end
	if type(c) == "string" then local ok, v = pcall(Color3.fromHex, c); if ok then return v end end
	return nil
end
local function fromShop(cat: any, b: any): any
	local hero = type(b.hero) == "table" and b.hero or {}
	local w = hero.weapon
	if type(w) ~= "string" or not Roster.byId[w] then w = "ar" end
	local skin = if type(hero.skin) == "string" then hero.skin else nil -- (the shop's weapon skin sets, 16 Nov)
	local pieces = { { w = w, wrap = hero.wrap, mode = "full", hat = hero.hat, skin = skin } }
	local rows = {}
	for _, it in (if type(b.items) == "table" then b.items else {}) do
		if type(it) ~= "table" or type(it.id) ~= "string" then continue end
		local name, rar = nil, nil
		if type(cat.itemInfo) == "function" then
			local ok, n, r = pcall(cat.itemInfo, it.kind, it.id)
			if ok then name, rar = n, r end
		end
		name = name or (if it.kind == "wrap" then wrapName(it.id) elseif it.kind == "hat" then hatName(it.id) else nil) or it.id
		local kindWord = if it.kind == "hat" then "WEAPON HAT" elseif it.kind == "wrap" then "WRAP" else string.upper(tostring(it.kind))
		-- (wraps and hats are owned per weapon since 16 Nov: an item may name its own weapon; else it goes on the hero's)
		local iw = if type(it.weapon) == "string" and Roster.byId[it.weapon] then it.weapon else w
		local on = if iw ~= w then "  ·  " .. nameOf(iw) else ""
		table.insert(rows, { title = string.upper(tostring(name)), sub = kindWord .. (if rar then "  ·  " .. string.upper(tostring(rar)) else "") .. on, color = rarityColor(cat, rar) })
		local row = #rows
		local heroIt = iw == w and ((it.kind == "wrap" and it.id == hero.wrap) or (it.kind == "hat" and it.id == hero.hat))
		if heroIt then pieces[1].rows = pieces[1].rows or {}; table.insert(pieces[1].rows, row)
		elseif it.kind == "wrap" then table.insert(pieces, { w = iw, wrap = it.id, mode = "full", rows = { row } })
		elseif it.kind == "hat" then table.insert(pieces, { w = iw, wrap = if iw == w then hero.wrap else nil, skin = if iw == w then skin else nil, mode = "full", hat = it.id, rows = { row } }) end
	end
	local free = false
	if type(cat.free) == "function" then local ok, f = pcall(cat.free); free = ok and f == true end
	local price = if free then "FREE" elseif type(b.robux) == "number" then ("%d ROBUX"):format(b.robux) else nil
	return { id = b.id, name = string.upper(tostring(b.name or b.id)), blurb = b.blurb, pieces = pieces, rows = rows, price = price }
end
-- the VIP pack, for the VIP room's plinths (an anchor with Offer = "vip"): the pack's skins that are in the place, each
-- on its own weapon, then its wrap and its hat on the AR. nil while the pack has nothing in the place yet
local function vipBundle(cat: any): any
	if not cat or type(cat.vipItems) ~= "function" then return nil end
	local ok, items = pcall(cat.vipItems)
	if not ok or type(items) ~= "table" then return nil end
	local pieces, rows = {}, {}
	for _, it in items do
		if type(it) ~= "table" or type(it.id) ~= "string" then continue end
		local p = nil
		if it.kind == "skin" and type(it.weapon) == "string" and Roster.byId[it.weapon] then p = { w = it.weapon, skin = it.id, mode = "full" }
		elseif it.kind == "wrap" then p = { w = "ar", wrap = it.id, mode = "full" }
		elseif it.kind == "hat" then p = { w = "ar", hat = it.id, mode = "full" } end
		if not p then continue end
		local name, rar = nil, nil
		if type(cat.itemInfo) == "function" then local ok2, n, r = pcall(cat.itemInfo, it.kind, it.id); if ok2 then name, rar = n, r end end
		name = name or (if it.kind == "wrap" then wrapName(it.id) elseif it.kind == "hat" then hatName(it.id) else nil) or it.id
		local kindWord = if it.kind == "skin" then "WEAPON SKIN  ·  " .. nameOf(p.w) elseif it.kind == "hat" then "WEAPON HAT" else "WRAP"
		table.insert(rows, { title = string.upper(tostring(name)), sub = kindWord, color = rarityColor(cat, rar) })
		p.rows = { #rows }
		table.insert(pieces, p)
	end
	if #pieces == 0 then return nil end
	local vip = (type(cat.byId) == "table" and cat.byId.vip) or {}
	return { id = "vip", name = "THE DUCKY PACK", pieces = pieces, rows = rows, price = "VIP" .. (if type(vip.robux) == "number" then ("  ·  %d ROBUX"):format(vip.robux) else "") }
end
local function bundles(): { any }
	local cat = shopModule({ "Shop", "ShopCatalog" })
	-- (the bundles on show, skin sets with them once every skin in a set is in the place: the shop session, 16 Nov.
	-- an older catalogue without shown(): its whole list, less what ready() turns down)
	local list = nil
	if cat and type(cat.shown) == "function" then
		local ok, l = pcall(cat.shown, true)
		if ok and type(l) == "table" then list = l end
	end
	if not list and cat and type(cat.bundles) == "table" then
		list = {}
		for _, b in cat.bundles do
			local ok, r = true, true
			if type(cat.ready) == "function" then ok, r = pcall(cat.ready, b) end
			if not ok or r ~= false then table.insert(list, b) end
		end
	end
	local out = {}
	if type(list) == "table" then
		local first = nil
		if type(cat.rotation) == "function" then
			local ok, rot = pcall(cat.rotation)
			if ok and type(rot) == "table" then first = rot.hero end
		end
		local order = {}
		for _, b in list do if type(b) == "table" and b.id == first then table.insert(order, b) end end
		for _, b in list do if type(b) == "table" and b.id ~= first and type(b.id) == "string" then table.insert(order, b) end end
		for _, b in order do
			local ok, x = pcall(fromShop, cat, b)
			if ok and x and #x.pieces > 0 then table.insert(out, x) end
		end
	end
	if #out == 0 then
		for _, b in STAND_IN do
			local pieces, rows = {}, {}
			for _, x in b.pieces do
				local p = pieceOf(x)
				if p then
					table.insert(pieces, p)
					table.insert(rows, { title = nameOf(p.w), sub = detail(p) })
					p.rows = { #rows }
				end
			end
			if #pieces > 0 then table.insert(out, { id = b.id, name = b.name, pieces = pieces, rows = rows, standIn = true }) end
		end
	end
	return out
end
local toast: (string) -> () -- (the card's last line, for a moment)
-- the shop's own client (ShopClient) opens it from the prompt's ShopOpen attribute; this only covers a stand-in set or
-- a shop that isn't in the place yet
local function openShop(b: any)
	local ps = me:FindFirstChild("PlayerScripts")
	local ui = ps and ps:FindFirstChild("Jankfire") and ps.Jankfire:FindFirstChild("ShopUI")
	if b.standIn or not ui then toast("THE SHOP OPENS SOON") end
end

-- ---------------------------------------------------------------- one hologram
type Piece = { p: BasePart, t0: number, y: number }
type Shown = { key: string, model: Model, rel: CFrame, parts: { Piece }, hl: Highlight, piece: any, lo: number, hi: number }
type Holo = {
	anchor: BasePart, kind: string, r: number, h: number, base: number, color: Color3,
	rig: Part, disc: Part, beam: Beam, light: PointLight, label: BillboardGui?, card: BillboardGui?,
	list: { any }, idx: number, cur: Shown?, cache: { [string]: Shown }, failed: { [string]: boolean }, phase: string, t: number, spin: number, alpha: number,
	bundle: any, sig: string,
}
local holos: { [BasePart]: Holo } = {}

local function new(class: string, props: { [string]: any }, parent: Instance?): any
	local i = Instance.new(class)
	for k, v in props do (i :: any)[k] = v end
	if parent then i.Parent = parent end
	return i
end
local function text(parent: Instance, props: { [string]: any }): TextLabel
	local t = new("TextLabel", { BackgroundTransparency = 1, TextScaled = true, TextColor3 = Color3.fromRGB(236, 240, 242),
		FontFace = Font.new(FONT, Enum.FontWeight.SemiBold), TextXAlignment = Enum.TextXAlignment.Center }, parent)
	for k, v in props do (t :: any)[k] = v end
	return t
end

local function keyOf(p: any): string return ("%s|%s|%s|%s|%s"):format(p.w, tostring(p.wrap), tostring(p.mode), tostring(p.hat), tostring(p.skin)) end

local function dress(h: Holo, piece: any): Shown?
	local key = keyOf(piece)
	local have = h.cache[key]
	if have then return have end
	if h.failed[key] then return nil end
	local ok, m, rel = pcall(build, piece, h.r, h.h)
	if not ok or not m then
		h.failed[key] = true -- (once: the cycle skips it from then on)
		warn("[jankfire] hologram: no model for " .. key .. (if ok then "" else ": " .. tostring(m)))
		return nil
	end
	m.Name = "Holo_" .. piece.w
	local parts: { Piece } = {}
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") and d.Transparency < 0.99 then table.insert(parts, { p = d, t0 = d.Transparency, y = 0 }) end
	end
	local hl = new("Highlight", { Adornee = m, FillColor = h.color, OutlineColor = h.color:Lerp(Color3.new(1, 1, 1), 0.35),
		FillTransparency = 1, OutlineTransparency = 1, DepthMode = Enum.HighlightDepthMode.Occluded }, m)
	-- (heights in its own upright frame, measured once: it only ever turns about up)
	m:PivotTo(CFrame.new() * rel:Inverse())
	for _, q in parts do q.y = q.p.Position.Y; q.p.Transparency = 1 end
	local _, bsz = m:GetBoundingBox() -- (its bottom and top, from its middle: where the scan line starts showing it and ends)
	local s: Shown = { key = key, model = m, rel = rel, parts = parts, hl = hl, piece = piece, lo = -bsz.Y / 2, hi = bsz.Y / 2 }
	h.cache[key] = s
	return s
end

-- how shown a piece is: a = everything (fades), scan = the build line's height (nil = all built)
local function paint(h: Holo, s: Shown, a: number, scan: number?)
	for _, q in s.parts do
		local f = a
		if scan then f *= math.clamp((scan - q.y) / 0.45 + 0.5, 0, 1) end
		q.p.Transparency = 1 - (1 - q.t0) * (1 - SEE) * f
	end
	local g = if scan then math.clamp((scan - s.lo) / math.max(s.hi - s.lo, 0.1), 0, 1) * a else a
	s.hl.FillTransparency = 1 - (1 - FILL) * g
	s.hl.OutlineTransparency = 1 - (1 - EDGE) * g
end

local function setLabel(h: Holo, piece: any?, a: number)
	local lb = h.label
	if not lb then return end
	local slot, title, sub = lb:FindFirstChild("Slot") :: TextLabel, lb:FindFirstChild("Title") :: TextLabel, lb:FindFirstChild("Sub") :: TextLabel
	if piece then
		local e = Roster.byId[piece.w]
		slot.Text = (if e then SLOT_WORD[e.slot] else nil) or ""
		title.Text = nameOf(piece.w)
		sub.Text = detail(piece)
	end
	for _, t in { slot, title, sub } do t.TextTransparency = 1 - a end
end

local function myLoadout(): { any }
	local s = me:GetAttribute("LoadoutNext")
	local pick = { primary = "redline", secondary = "marbles", melee = "katana", utility = "frag" }
	if type(s) == "string" then
		local i = 0
		for id in string.gmatch(s, "[^,]+") do
			i += 1
			local slot = Roster.SLOTS[i]
			if slot and Roster.byId[id] then pick[slot] = id end
		end
	end
	local out = {}
	for _, slot in Roster.SLOTS do
		local id = pick[slot]
		local wrap, mode = WeaponModels.wrapFor(me, id)
		table.insert(out, { w = id, wrap = wrap, mode = mode, hat = GunHats.hatFor(me, id) })
	end
	return out
end

-- the bundle card: what's in it, shown when you stand near its plinth
local function footOf(b: any): string
	return if b.standIn then "COMING TO THE SHOP" elseif b.price then ("%s  ·  E TO VIEW"):format(tostring(b.price)) else "E TO VIEW IN THE SHOP"
end
local function makeCard(h: Holo)
	local rows = h.bundle.rows or {}
	local n = #rows
	-- (0.68 of the first try: at 6.4 studs wide it covered the hologram from a few steps away)
	local CS = 0.68
	local card = new("BillboardGui", { Name = "BundleCard", Size = UDim2.new(6.4 * CS, 0, (2.5 + 0.62 * n) * CS, 0), StudsOffset = Vector3.new(h.r + 2.4, 0.5, 0),
		LightInfluence = 0, MaxDistance = 40, AlwaysOnTop = true, ResetOnSpawn = false, Enabled = false }, h.rig) -- (on top: a pier cut it off)
	local bg = new("Frame", { Name = "Bg", BackgroundColor3 = Color3.fromRGB(22, 25, 31), BackgroundTransparency = 0.12, Size = UDim2.fromScale(1, 1), BorderSizePixel = 0 }, card)
	new("UICorner", { CornerRadius = UDim.new(0.04, 0) }, bg)
	new("UIStroke", { Color = h.color, Thickness = 1.5, Transparency = 0.35 }, bg)
	local total = 2.5 + 0.62 * n
	text(bg, { Name = "Kind", Text = "BUNDLE", TextColor3 = h.color, TextXAlignment = Enum.TextXAlignment.Left, Position = UDim2.fromScale(0.07, 0.22 / total), Size = UDim2.fromScale(0.86, 0.34 / total) })
	text(bg, { Name = "Title", Text = h.bundle.name, FontFace = Font.new(FONT, Enum.FontWeight.Heavy), TextXAlignment = Enum.TextXAlignment.Left, Position = UDim2.fromScale(0.07, 0.6 / total), Size = UDim2.fromScale(0.86, 0.6 / total) })
	new("Frame", { Name = "Rule", BackgroundColor3 = h.color, BackgroundTransparency = 0.4, BorderSizePixel = 0, Position = UDim2.fromScale(0.07, 1.38 / total), Size = UDim2.new(0.86, 0, 0, 2) }, bg)
	for i, row in rows do
		local y = 1.55 + 0.62 * (i - 1)
		local r = new("Frame", { Name = "Row" .. i, BackgroundTransparency = 1, Position = UDim2.fromScale(0.07, y / total), Size = UDim2.fromScale(0.86, 0.56 / total) }, bg)
		-- (the rarity only as a thin mark at the row's start: the shop's look rule)
		if row.color then new("Frame", { Name = "Rarity", BackgroundColor3 = row.color, BorderSizePixel = 0, Position = UDim2.fromScale(-0.045, 0.08), Size = UDim2.new(0, 3, 0.84, 0) }, r) end
		text(r, { Name = "What", Text = row.title, FontFace = Font.new(FONT, Enum.FontWeight.Bold), TextXAlignment = Enum.TextXAlignment.Left, Size = UDim2.fromScale(1, 0.56) })
		text(r, { Name = "How", Text = row.sub or "", TextColor3 = Color3.fromRGB(170, 178, 186), TextXAlignment = Enum.TextXAlignment.Left, Position = UDim2.fromScale(0, 0.56), Size = UDim2.fromScale(1, 0.4) })
	end
	local foot = footOf(h.bundle)
	text(bg, { Name = "Foot", Text = foot, TextColor3 = Color3.fromRGB(196, 204, 210), TextXAlignment = Enum.TextXAlignment.Left, Position = UDim2.fromScale(0.07, (total - 0.72) / total), Size = UDim2.fromScale(0.86, 0.38 / total) })
	h.card = card
end

local function forget(h: Holo)
	for _, s in h.cache do s.model:Destroy() end
	h.cache = {}
	h.cur = nil
end

local function applyBundle(h: Holo)
	local slot = tonumber(h.anchor:GetAttribute("Slot")) or 1
	local want = h.anchor:GetAttribute("Offer")
	local b
	if want == "vip" then
		local ok, v = pcall(vipBundle, shopModule({ "Shop", "ShopCatalog" }))
		b = if ok then v else nil
	else
		local all = bundles()
		b = if #all > 0 then all[(slot - 1) % #all + 1] else nil
	end
	local sig = if b then b.id .. "#" .. #b.pieces .. "#" .. tostring(b.price) else "none"
	if sig == h.sig then return end
	-- (a new bundle on this plinth: start it fresh)
	if h.sig ~= "" then forget(h); h.phase = "idle"; h.disc.Transparency = 1 end
	h.sig = sig
	h.bundle = b
	h.list = if b then b.pieces else {}
	h.idx = if want == "vip" and b then (slot - 1) % #b.pieces else 0 -- (the VIP room's two plinths start on different pieces)
	if h.card then h.card:Destroy(); h.card = nil end
	if b then makeCard(h) end
	-- the plate over the plinth and the prompt carry its name
	local plate = h.anchor.Parent and h.anchor.Parent:FindFirstChild("ShowName" .. slot)
	local gui = plate and plate:FindFirstChild("Gui")
	local line = gui and gui:FindFirstChild("Line2")
	if line then line.Text = if b then b.name else "" end
	-- (27 Nov, main: no COMING SOON placeholders: with nothing on the plinth its plate shows nothing at all)
	if plate and plate:IsA("BasePart") then plate.LocalTransparencyModifier = if b then 0 else 1 end
	if gui and gui:IsA("SurfaceGui") then gui.Enabled = b ~= nil end
	-- (the shop's ShopClient opens whatever a triggered prompt's ShopOpen names: a stand-in set names nothing)
	local pr = h.anchor:FindFirstChildWhichIsA("ProximityPrompt", true)
	if pr then
		pr.ObjectText = if b then b.name else ""; pr.Enabled = b ~= nil
		pr:SetAttribute("ShopOpen", if b and not b.standIn then b.id else nil)
	end
end

local function add(anchor: Instance)
	if not anchor:IsA("BasePart") or holos[anchor] then return end
	local kind = anchor:GetAttribute("Holo")
	if kind ~= "loadout" and kind ~= "bundle" then return end
	local r = tonumber(anchor:GetAttribute("Radius")) or 3
	local hh = tonumber(anchor:GetAttribute("Height")) or 3
	local hex = anchor:GetAttribute("Color")
	local color = if type(hex) == "string" then Color3.fromHex(hex) else Color3.fromRGB(111, 201, 201)
	local base = tonumber(anchor:GetAttribute("Base")) or 0
	-- the rig: one invisible part at the middle holding the light, the beam's ends and the words
	local rig = new("Part", { Name = "HoloRig", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = false,
		Transparency = 1, Size = Vector3.one * 0.2, CFrame = CFrame.new(anchor.Position) }, nil)
	local light = new("PointLight", { Color = color, Brightness = 0.7, Range = r * 2 + 4, Shadows = false }, rig)
	local a0 = new("Attachment", { Name = "Lens", Position = Vector3.new(0, -base, 0) }, rig)
	local a1 = new("Attachment", { Name = "Top", Position = Vector3.new(0, -hh * 0.15, 0) }, rig)
	local beam = new("Beam", { Attachment0 = a0, Attachment1 = a1, Color = ColorSequence.new(color), LightEmission = 1, LightInfluence = 0,
		Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.8), NumberSequenceKeypoint.new(0.75, 0.93), NumberSequenceKeypoint.new(1, 1) }),
		Width0 = math.min(r * 0.45, 1.6), Width1 = r * 1.5, FaceCamera = true, Segments = 1, Enabled = base > 0.5 }, rig)
	local disc = new("Part", { Name = "ScanLine", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = false,
		Shape = Enum.PartType.Cylinder, Material = Enum.Material.Neon, Color = color, Transparency = 1,
		Size = Vector3.new(0.04, r * 2 + 0.6, r * 2 + 0.6) }, rig)
	local h: Holo = { anchor = anchor, kind = kind, r = r, h = hh, base = base, color = color, rig = rig, disc = disc, beam = beam, light = light,
		label = nil, card = nil, list = {}, idx = 0, cur = nil, cache = {}, failed = {}, phase = "idle", t = 0, spin = math.random() * 6, alpha = 0, bundle = nil, sig = "" }
	if kind == "loadout" then
		-- (MaxDistance 30, was 150: the owner, 20 Nov, saw "UTILITY / LAPTOP / Neon Hex wrap" floating in front of the 4V4
		-- sign from across the round hall; it shows only once you are near the dais now)
		local lb = new("BillboardGui", { Name = "HoloLabel", Size = UDim2.new(6.6, 0, 1.4, 0), StudsOffsetWorldSpace = Vector3.new(0, hh / 2 + 0.9, 0),
			LightInfluence = 0, MaxDistance = 30, ResetOnSpawn = false }, rig)
		text(lb, { Name = "Slot", TextColor3 = color, Size = UDim2.fromScale(1, 0.26) })
		text(lb, { Name = "Title", FontFace = Font.new(FONT, Enum.FontWeight.Heavy), Position = UDim2.fromScale(0, 0.27), Size = UDim2.fromScale(1, 0.45) })
		text(lb, { Name = "Sub", TextColor3 = Color3.fromRGB(176, 186, 192), Position = UDim2.fromScale(0, 0.74), Size = UDim2.fromScale(1, 0.26) })
		h.label = lb
		setLabel(h, nil, 0)
		h.list = myLoadout()
		h.sig = (function() local k = {} for _, p in h.list do table.insert(k, keyOf(p)) end return table.concat(k, ";") end)()
	else
		applyBundle(h)
		local pr = anchor:FindFirstChildWhichIsA("ProximityPrompt", true)
		if pr then pr.Triggered:Connect(function() if h.bundle then openShop(h.bundle) end end) end
	end
	rig.Parent = workspace
	holos[anchor] = h
end

local function remove(anchor: Instance)
	local h = holos[anchor :: BasePart]
	if not h then return end
	forget(h)
	h.rig:Destroy()
	holos[anchor :: BasePart] = nil
end

CollectionService:GetInstanceAddedSignal(TAG):Connect(add)
CollectionService:GetInstanceRemovedSignal(TAG):Connect(remove)
for _, a in CollectionService:GetTagged(TAG) do add(a) end

-- your loadout changed (a pick, a wrap, a hat): the centre starts over on the new set
local function relist()
	for _, h in holos do
		if h.kind ~= "loadout" then continue end
		local list = myLoadout()
		local k = {} for _, p in list do table.insert(k, keyOf(p)) end
		local sig = table.concat(k, ";")
		if sig == h.sig then continue end
		h.sig = sig
		h.list = list
		-- (keep what's showing if it's still in the set; drop the rest so a new wrap is built fresh)
		local keep = h.cur and h.cur.key
		for key, s in h.cache do if key ~= keep then s.model:Destroy(); h.cache[key] = nil end end
		if h.cur and not table.find(k, h.cur.key) then h.phase = "out"; h.t = 0 end
		h.idx = 0
		if h.cur then for i, key in k do if key == h.cur.key then h.idx = i end end end
	end
end
for _, a in { "LoadoutNext", "Wraps", "Hats" } do me:GetAttributeChangedSignal(a):Connect(relist) end
-- (the shop's catalogue may arrive after the hub: look again now and then)
task.spawn(function()
	while true do
		task.wait(8)
		for _, h in holos do if h.kind == "bundle" then applyBundle(h) end end
	end
end)

local toastUntil, toastText = 0, ""
toast = function(s: string)
	toastText = s; toastUntil = os.clock() + 2.5
end

-- ---------------------------------------------------------------- every frame
local camera = workspace.CurrentCamera
local function smooth(x: number): number x = math.clamp(x, 0, 1); return x * x * (3 - 2 * x) end

local function nextPiece(h: Holo): Shown?
	local n = #h.list
	for _ = 1, n do
		h.idx = h.idx % n + 1
		local s = dress(h, h.list[h.idx])
		if s then return s end
	end
	return nil
end

local function place(h: Holo, s: Shown)
	local bob = math.sin(os.clock() * 1.1 + h.spin) * 0.12
	s.model:PivotTo(CFrame.new(h.anchor.Position + Vector3.new(0, bob, 0)) * CFrame.Angles(0, h.spin, 0) * s.rel:Inverse())
end

local function inHub(): boolean
	local z = me:GetAttribute("Zone")
	return z == nil or z == "hub"
end

RunService.RenderStepped:Connect(function(dt: number)
	local cam = camera.CFrame.Position
	local here = inHub()
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	local nearest, nd = nil, NEAR
	for _, h in holos do
		local on = here and h.anchor.Parent ~= nil and (h.anchor.Position - cam).Magnitude < FAR
		if not on then
			if h.cur then h.cur.model.Parent = nil end
			h.rig.Parent = nil
			continue
		end
		if h.rig.Parent ~= workspace then h.rig.Parent = workspace end
		h.rig.CFrame = CFrame.new(h.anchor.Position)
		h.spin += dt * SPIN
		h.t += dt
		if #h.list == 0 then
			h.disc.Transparency = 1
			if h.cur then h.cur.model.Parent = nil; h.cur = nil end
			continue
		end
		if h.phase == "idle" then
			h.cur = nextPiece(h)
			if not h.cur then continue end
			h.phase, h.t = "in", 0
			setLabel(h, h.cur.piece, 0)
		end
		local s = h.cur
		if not s then h.phase = "idle"; continue end
		if s.model.Parent ~= workspace then s.model.Parent = workspace end
		place(h, s)
		-- the scan line (owner, 16 Nov: "can the sweep start lower, like at the base of the hologram cone?"): it starts at the
		-- lens, the foot of the light cone, as narrow as the cone is there, widens with the cone up to the piece's foot, then
		-- builds the piece from its foot to its top and fades out over it. it shows from the first moment, not halfway up
		local y0 = if h.base > 0.5 then -h.base else s.lo - 0.3
		if h.phase == "in" then
			local f = math.clamp(h.t / IN, 0, 1)
			local top = s.hi + 0.25
			local scan = y0 + (top - y0) * (1 - (1 - f) ^ 1.6) -- (quick off the lens, slower through the piece)
			paint(h, s, 1, scan)
			local w0, w1 = math.min(h.r * 0.45, 1.6), h.r * 2 + 0.6
			local w = w0 + (w1 - w0) * math.clamp((scan - y0) / math.max(s.lo - y0, 0.1), 0, 1)
			h.disc.Size = Vector3.new(0.04, w, w)
			h.disc.CFrame = CFrame.new(h.anchor.Position + Vector3.new(0, scan, 0)) * CFrame.Angles(0, 0, math.pi / 2)
			h.disc.Transparency = 1 - 0.5 * smooth(f / 0.05) * (1 - smooth((f - 0.82) / 0.18))
			setLabel(h, nil, smooth(f))
			if h.t >= IN then h.phase, h.t = "show", 0; paint(h, s, 1, nil); h.disc.Transparency = 1 end
		elseif h.phase == "show" then
			if h.t >= (SHOW[h.kind] or 4) and #h.list > 1 then h.phase, h.t = "out", 0 end
		elseif h.phase == "out" then
			local f = 1 - smooth(h.t / OUT)
			paint(h, s, f, nil)
			setLabel(h, nil, f)
			if h.t >= OUT then
				s.model.Parent = nil
				h.cur = nextPiece(h)
				h.phase, h.t = "in", 0
				if h.cur then setLabel(h, h.cur.piece, 0); paint(h, h.cur, 1, h.cur.lo - 1) end
			end
		end
		-- the beam breathes with the build; the light too
		local glow = if h.phase == "in" then 0.12 * math.sin(math.pi * math.clamp(h.t / IN, 0, 1)) else 0
		h.light.Brightness = 0.7 + glow * 3
		if h.kind == "bundle" and root and h.card then
			local d = (Vector3.new(root.Position.X, h.anchor.Position.Y, root.Position.Z) - h.anchor.Position).Magnitude
			if d < nd then nearest, nd = h, d end
		end
	end
	-- the nearest plinth's card, and the row of the piece on show
	for _, h in holos do
		local card = h.card
		if not card then continue end
		local show = h == nearest
		card.Enabled = show
		if show then
			local bg = card:FindFirstChild("Bg")
			local lit = (h.cur and h.cur.piece.rows) or {}
			for i in (h.bundle.rows or {}) do
				local r = bg and bg:FindFirstChild("Row" .. i)
				if r then
					local on = table.find(lit, i) ~= nil
					(r:FindFirstChild("What") :: TextLabel).TextColor3 = if on then h.color:Lerp(Color3.new(1, 1, 1), 0.45) else Color3.fromRGB(236, 240, 242)
				end
			end
			local foot = bg and bg:FindFirstChild("Foot")
			if foot and os.clock() < toastUntil then foot.Text = toastText
			elseif foot and toastUntil > 0 then
				toastUntil = 0
				foot.Text = footOf(h.bundle)
			end
		end
	end
end)
