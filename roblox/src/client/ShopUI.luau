-- the SHOP screen (B, the SHOP button over the loadout button, or a hub hologram). what's on sale is Shared.Shop (the
-- catalog: containers, bundles, the daily rotation); what you own and every buy, claim and opening is the loot
-- server's (JankfireRemotes.Loot): this screen only shows and asks. free while we test (Shop.free()): prices are
-- shown struck through beside CLAIM; no Robux prompt is ever shown while Shop.ROBUX is false.
-- the look is Theme.luau's: dark plates and cards, white text, one amber accent (the active tab's mark, the one button
-- that does something). rarity colour only as a thin mark. built for a 720-tall screen and scaled to fit; a short
-- screen (a phone on its side) gets a 470-tall layout, so text and buttons stay big enough to read and press.
-- client API (other scripts, the hub's holograms): ShopUI.open(tab?, offerId?), ShopUI.close(), ShopUI.isOpen().
-- a ProximityPrompt with the attribute ShopOpen = "<offer id>" or "tab:<tab>" opens it too (ShopClient.client.luau)
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local GuiService = game:GetService("GuiService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Shop = require(Shared:WaitForChild("Shop"))
local Roster = require(Shared:WaitForChild("Roster"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local GunHats = require(Shared:WaitForChild("GunHats"))
local T = require(script.Parent:WaitForChild("Theme"))
local Hud = require(script.Parent:WaitForChild("Hud"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local new = T.new
local WHITE = Color3.new(1, 1, 1)
local ROBUX = utf8.char(0xE002) -- the Robux mark (Roblox's fonts draw it)

local ShopUI = {}
local TABS = { "featured", "bundles", "containers", "inventory" }
local TAB_NAMES = { featured = "FEATURED", bundles = "BUNDLES", containers = "CONTAINERS", inventory = "INVENTORY" }
local LINES = { "free while we test. the prices are for later.", "everything's on the house. for now.", "take what you like. we'll bill you later. not really." }

-- everything the screen knows, in one table (keeps the main chunk well under Luau's 200 locals)
local S = {
	open = false, tab = "featured", built = false, compact = false, scale = 1, W = 1280, H = 720,
	inv = { wrap = {}, hat = {}, containers = {} } :: any, invOk = false, busy = false,
	invFilter = "all", inspect = nil :: any, preview = nil :: any, hidden = {} :: { [ScreenGui]: boolean },
}
local UI: any = {} -- every built instance the layout pass touches
local spins: { any } = {} -- the 3D previews that turn (see V)

local function play(name: string) pcall(Sfx.play, name) end
local function commas(n: number): string
	local s = tostring(math.floor(n))
	local out = s:reverse():gsub("(%d%d%d)", "%1,"):reverse()
	return (out:gsub("^,", ""))
end
local function clock(sec: number): string
	sec = math.max(0, math.floor(sec))
	return string.format("%02d:%02d:%02d", sec // 3600, (sec % 3600) // 60, sec % 60)
end
local function rarityColor(r: string): Color3
	local e = Shop.RARITY[r]
	return if e then e.color else T.MUTED
end
local function rarityName(r: string): string
	local e = Shop.RARITY[r]
	return string.upper(if e then e.name else r)
end

-- ======================================================================== the till (the loot server)
local Till = {}
function Till.remote(): RemoteFunction?
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("Loot")
	return if r and r:IsA("RemoteFunction") then r else nil
end
function Till.ask(op: string, ...: any): any
	local r = Till.remote()
	if not r then return { ok = false, why = "the till isn't open yet. try again in a bit." } end
	local args = table.pack(...)
	local ok, res = pcall(function() return r:InvokeServer(op, table.unpack(args, 1, args.n)) end)
	if not ok then return { ok = false, why = "couldn't reach the till." } end
	if type(res) ~= "table" then return { ok = res == true, why = if type(res) == "string" then res else nil } end
	return res
end
-- the inventory, in one shape whatever the server sends: sets of ids per kind, a count per container
function Till.adopt(raw: any)
	local inv = { wrap = {}, hat = {}, containers = {} }
	local src = if type(raw) == "table" then (raw.inv or raw.inventory or raw) else {}
	local function set(kind: string, list: any)
		if type(list) ~= "table" then return end
		for k, v in list do
			if type(k) == "string" and v then inv[kind][k] = true
			elseif type(v) == "string" then inv[kind][v] = true end
		end
	end
	inv.skin = {}
	set("wrap", src.wrap or src.wraps or src.finish)
	set("hat", src.hat or src.hats)
	set("skin", src.skin or src.skins)
	S.restricted = type(raw) == "table" and raw.restricted == true
	local c = src.containers or src.stock or {}
	if type(c) == "table" then
		for k, v in c do if type(k) == "string" and type(v) == "number" then inv.containers[k] = v end end
	end
	for _, o in Shop.containers do
		if type(src[o.id]) == "number" then inv.containers[o.id] = src[o.id] end
	end
	S.inv = inv
end
function Till.refresh(): boolean
	local res = Till.ask("inventory")
	S.invOk = res.ok == true
	if res.ok then Till.adopt(res) end
	return S.invOk
end
-- wraps and hats are owned per weapon ("sakura@smg"); a plain "sakura" from an older save counts for every weapon
function Till.owns(kind: string, id: string, weapon: string?): boolean
	local _, r = Shop.itemInfo(kind, id)
	if r == "free" then return true end
	local set = S.inv[kind]
	if not set then return false end
	if set[id] == true then return true end
	return weapon ~= nil and set[Shop.key(kind, id, weapon)] == true
end
function Till.count(cid: string): number return S.inv.containers[cid] or 0 end
-- what you own as the loot module's odds want it ({ wrap = { [id] = true }, hat = ..., skin = ... })
function Till.ownedSets(): any return { wrap = S.inv.wrap, hat = S.inv.hat, skin = S.inv.skin or {} } end
-- a container that can't give you anything right now: "soon" (nothing in it on roblox yet), "empty" (you own it all)
function Till.boxState(cid: string): string?
	if Shop.soon(cid) then return "soon" end
	local _, o = Shop.odds(cid, Till.ownedSets())
	if o and o.empty then return "empty" end
	return nil
end
-- how many of an offer's items you don't have yet
function Till.missing(o: any): number
	local n = 0
	for _, it in Shop.contents(o) do if not Till.owns(it.kind, it.id, it.weapon) then n += 1 end end
	return n
end

-- ======================================================================== little builders
local function txt(parent: Instance, text: string, size: number, color: Color3?, font: Font?, align: Enum.TextXAlignment?): TextLabel
	local l = T.text(parent, "Text", text, size, color or T.TEXT, font or T.FONT, align or Enum.TextXAlignment.Left)
	l.TextTruncate = Enum.TextTruncate.AtEnd
	return l
end
-- a button. main = amber with dark text (the one that does something); dark = a card with a hairline; tab = bare
-- words with an amber line under the picked one
local function button(parent: Instance, text: string, kind: string, size: UDim2, pos: UDim2?): any
	local base = if kind == "main" then T.ACCENT else T.CARD
	local face = new("TextButton", {
		AutoButtonColor = false, BackgroundColor3 = base, BackgroundTransparency = if kind == "tab" then 1 else 0,
		BorderSizePixel = 0, Size = size, Position = pos or UDim2.new(), FontFace = T.FONT_BOLD, RichText = true,
		TextSize = 15, Text = text, TextColor3 = if kind == "main" then T.INK elseif kind == "tab" then T.MUTED else T.TEXT,
	}, parent)
	if kind ~= "tab" then T.corner(face) end
	if kind == "dark" then T.edge(face) end
	local mark = new("Frame", { Name = "Mark", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, 0), Size = UDim2.new(0.6, 0, 0, 3), Visible = false }, face)
	local b = { face = face, mark = mark, kind = kind, enabled = true, base = base }
	local function lit(c: Color3): Color3 return c:Lerp(WHITE, 0.14) end
	face.MouseEnter:Connect(function()
		if not b.enabled then return end
		if kind == "tab" then if not mark.Visible then face.TextColor3 = T.TEXT end else face.BackgroundColor3 = lit(b.base) end
	end)
	face.MouseLeave:Connect(function()
		if kind == "tab" then if not mark.Visible then face.TextColor3 = T.MUTED end else face.BackgroundColor3 = b.base end
	end)
	function b.set(t: string, enabled: boolean?)
		face.Text = t
		b.enabled = enabled ~= false
		if kind == "main" then
			b.base = if b.enabled then T.ACCENT else T.TRACK
			face.TextColor3 = if b.enabled then T.INK else T.MUTED
		elseif kind ~= "tab" then
			face.TextColor3 = if b.enabled then T.TEXT else T.DIM
		end
		if kind ~= "tab" then face.BackgroundColor3 = b.base end
	end
	function b.pick(on: boolean)
		mark.Visible = on
		face.TextColor3 = if on then T.TEXT else T.MUTED
	end
	return b
end
-- a card: the slightly lighter plate an offer sits on, with its rarity as a thin line along the bottom
local function card(parent: Instance, r: string?): (TextButton, Frame?)
	local c = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = T.CARD, BorderSizePixel = 0, ClipsDescendants = true }, parent)
	T.corner(c)
	local st = T.edge(c)
	c.MouseEnter:Connect(function() c.BackgroundColor3 = T.CARD_HI; st.Transparency = 0.7 end)
	c.MouseLeave:Connect(function() c.BackgroundColor3 = T.CARD; st.Transparency = T.EDGE_A end)
	local bar = nil
	if r then
		bar = new("Frame", { Name = "Rarity", BackgroundColor3 = rarityColor(r), BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0, 3), ZIndex = 4 }, c)
	end
	return c, bar
end
-- the small "rarity · kind" line: a dot in the rarity's colour, the words in grey
local function rarityLine(parent: Instance, r: string, kind: string, size: number, kindOnly: boolean?): Frame
	local f = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, size + 4) }, parent)
	local dot = new("Frame", { BackgroundColor3 = rarityColor(r), BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 0.5), Position = UDim2.new(0, 0, 0.5, 0), Size = UDim2.fromOffset(size * 0.5, size * 0.5) }, f)
	T.corner(dot, 99)
	-- (kindOnly: a narrow card on a phone keeps the dot and the kind; the rarity is the colour of the dot and the bar)
	local words = if kindOnly and kind ~= "" then string.upper(kind) else rarityName(r) .. (if kind ~= "" then "  ·  " .. string.upper(kind) else "")
	local l = txt(f, words, size, T.MUTED, T.FONT_BOLD)
	l.Position = UDim2.fromOffset(size * 0.5 + 6, 0); l.Size = UDim2.new(1, -(size * 0.5 + 6), 1, 0)
	return f
end
-- how many of a container to claim and open at once: x1 / x5 / x10 (the loot server opens a batch with no
-- repeats inside it). the pick is remembered per container; any change redraws the page
S.count = {} :: { [string]: number }
function ShopUI.countPicker(parent: Instance, cid: string, z: number): Frame
	local f = new("Frame", { Name = "Count", BackgroundTransparency = 1, ZIndex = z }, parent)
	new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, f)
	for i, n in { 1, 5, 10 } do
		local b = button(f, "x" .. n, "dark", UDim2.new(1 / 3, -4, 1, 0))
		b.face.LayoutOrder = i; b.face.ZIndex = z + 1; b.face.TextSize = 15
		b.mark.ZIndex = z + 2
		local on = (S.count[cid] or 1) == n
		b.mark.Visible = on
		b.base = if on then T.CARD_HI else T.CARD
		b.face.BackgroundColor3 = b.base
		b.face.MouseButton1Click:Connect(function()
			if (S.count[cid] or 1) == n then return end
			S.count[cid] = n
			play("click")
			ShopUI.refill()
		end)
	end
	return f
end
-- a price: the Robux mark and the number; struck through and grey while everything's free
local function priceText(robux: number): string
	if Shop.free() then return string.format('<s>%s %s</s>', ROBUX, commas(robux)) end
	return ROBUX .. " " .. commas(robux)
end

-- a paint chip for a wrap: a piece of its picture (JankfireWraps), or its palette as bands
local WRAPS = ReplicatedStorage:FindFirstChild("JankfireWraps")
local function paintChip(chip: GuiObject, wid: string)
	local wr = Roster.wrapById[wid]
	if not wr then return end
	WRAPS = WRAPS or ReplicatedStorage:FindFirstChild("JankfireWraps")
	local sa = WRAPS and WRAPS:FindFirstChild(wid)
	local img = sa and sa:GetAttribute("Swatch")
	if type(img) == "string" then
		chip.BackgroundColor3 = WHITE
		local im = new("ImageLabel", { Image = img, BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ImageRectSize = Vector2.new(384, 256), ZIndex = chip.ZIndex + 1 }, chip)
		T.corner(im, 4)
		return
	end
	local pal = wr.pal
	if #pal == 0 then chip.BackgroundColor3 = T.TRACK; return end
	if #pal == 1 then chip.BackgroundColor3 = pal[1]; return end
	chip.BackgroundColor3 = WHITE
	local kp = {}
	for i, c in pal do
		table.insert(kp, ColorSequenceKeypoint.new(if i == 1 then 0 else (i - 1) / #pal + 0.001, c))
		table.insert(kp, ColorSequenceKeypoint.new(if i == #pal then 1 else i / #pal, c))
	end
	new("UIGradient", { Rotation = 35, Color = ColorSequence.new(kp) }, chip)
end

-- ======================================================================== 3D previews
local V = {}
-- the weapon a single wrap is shown on: your primary (the Shredder is a Tool: the rifle stands in), else the rifle
function V.yourGun(): string
	local s = me:GetAttribute("LoadoutNext")
	local first = if type(s) == "string" then string.match(s, "^([^,]+)") else nil
	if first and first ~= "shredder" then
		local e = Roster.byId[first]
		if e and e.live and e.slot == "primary" then return first end
	end
	return "ar"
end
local function settle(m: Model)
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CastShadow = false end
	end
end
-- the Shredder is a Tool (JankfireTools.Shredder), not a built weapon: a copy of its visible parts (as the loadout does)
function V.shredder(): Model?
	local tools = ReplicatedStorage:FindFirstChild("JankfireTools")
	local src = tools and tools:FindFirstChild("Shredder")
	if not src then return nil end
	local m = Instance.new("Model")
	local big: BasePart? = nil
	for _, d in src:GetDescendants() do
		if d:IsA("BasePart") and d.Transparency < 0.99 and d.Name ~= "SuckField" then
			local c = d:Clone()
			for _, x in c:GetChildren() do
				if not (x:IsA("SurfaceAppearance") or x:IsA("SpecialMesh") or x:IsA("Decal") or x:IsA("Texture")) then x:Destroy() end
			end
			c.Anchored = true
			c.Parent = m
			if not big or c.Size.Magnitude > big.Size.Magnitude then big = c end
		end
	end
	m.PrimaryPart = big
	return m
end
-- a weapon wearing a wrap and a hat (all of it painted: "full"). boost = the hat drawn this much bigger (a small
-- card, where a true-size hat is a few pixels)
function V.gun(wid: string, wrap: string?, hat: string?, boost: number?): Model?
	local m = if wid == "shredder" then V.shredder() else WeaponModels.build(wid, 3)
	if not m then return nil end
	settle(m)
	if wrap and wrap ~= "default" then pcall(WeaponModels.wrap, m, wrap, "full") end
	if hat and hat ~= "none" then
		if wid == "shredder" then
			local tools = ReplicatedStorage:FindFirstChild("JankfireTools")
			local tool = tools and tools:FindFirstChild("Shredder")
			if tool then pcall(GunHats.attachToolCopy, m, tool, hat) end
		else
			pcall(GunHats.attach, m, wid, hat, 3, true, boost)
		end
	end
	settle(m)
	return m
end
-- a hat on its own (the template), big
function V.hat(id: string): Model?
	local t = GunHats.template(id)
	if not t then return nil end
	local m = t:Clone()
	settle(m)
	return m
end
-- the containers. the loot module's own models if it has them (ReplicatedStorage.JankfireLoot), else built here:
-- calm greys, one amber latch or band
function V.container(id: string): Model
	local lib = ReplicatedStorage:FindFirstChild("JankfireLoot")
	local t = lib and (lib:FindFirstChild(id) or lib:FindFirstChild("c_" .. id))
	-- (a container rests turned a little off its front: its latch / zip / band side to you)
	if t and t:IsA("Model") then local m = t:Clone(); settle(m); m:SetAttribute("ShopRest", math.pi - 0.55); return m end
	local m = Instance.new("Model")
	local function p(shape: Enum.PartType, size: Vector3, c: Color3, cf: CFrame, mat: Enum.Material?): Part
		return new("Part", { Shape = shape, Anchored = true, Size = size, Color = c, CFrame = cf, Material = mat or Enum.Material.SmoothPlastic, TopSurface = Enum.SurfaceType.Smooth, BottomSurface = Enum.SurfaceType.Smooth, CastShadow = false }, m)
	end
	local B, Cy = Enum.PartType.Block, Enum.PartType.Cylinder
	local slate, dark, steel, amber = Color3.fromRGB(70, 75, 86), Color3.fromRGB(38, 41, 49), Color3.fromRGB(150, 156, 166), T.ACCENT
	if id == "crate" then
		m.PrimaryPart = p(B, Vector3.new(3.4, 1.7, 2.2), slate, CFrame.identity)
		p(B, Vector3.new(3.46, 0.08, 2.26), dark, CFrame.new(0, 0.2, 0)) -- the lid's seam
		for _, x in { -1.66, 1.66 } do for _, z in { -1.06, 1.06 } do p(B, Vector3.new(0.22, 1.78, 0.22), dark, CFrame.new(x, 0, z)) end end
		for _, x in { -0.8, 0.8 } do p(B, Vector3.new(0.34, 0.42, 0.1), amber, CFrame.new(x, 0.22, -1.14), Enum.Material.Metal) end
		p(B, Vector3.new(1.2, 0.14, 0.3), dark, CFrame.new(0, 0.94, 0))
		p(B, Vector3.new(0.14, 0.24, 0.3), dark, CFrame.new(-0.55, 0.82, 0)); p(B, Vector3.new(0.14, 0.24, 0.3), dark, CFrame.new(0.55, 0.82, 0))
	elseif id == "bag" then
		m.PrimaryPart = p(Cy, Vector3.new(3.4, 1.7, 1.7), Color3.fromRGB(64, 68, 62), CFrame.identity, Enum.Material.Fabric)
		for _, x in { -1.66, 1.66 } do p(Cy, Vector3.new(0.12, 1.76, 1.76), dark, CFrame.new(x, 0, 0), Enum.Material.Fabric) end
		p(B, Vector3.new(3.0, 0.08, 0.16), steel, CFrame.new(0, 0.85, 0), Enum.Material.Metal) -- the zip
		p(B, Vector3.new(0.18, 0.3, 0.12), amber, CFrame.new(0.9, 0.86, -0.14), Enum.Material.Metal) -- its pull
		for _, x in { -0.5, 0.5 } do
			p(B, Vector3.new(0.14, 0.5, 0.16), dark, CFrame.new(x, 1.02, 0) * CFrame.Angles(0, 0, if x < 0 then -0.5 else 0.5))
		end
		p(B, Vector3.new(0.72, 0.14, 0.16), dark, CFrame.new(0, 1.24, 0))
		for _, x in { -1.1, 1.1 } do p(B, Vector3.new(0.16, 1.74, 1.74), dark, CFrame.new(x, 0, 0), Enum.Material.Fabric) end
	else -- the spray can
		local up = CFrame.Angles(0, 0, math.pi / 2)
		m.PrimaryPart = p(Cy, Vector3.new(2.6, 1.2, 1.2), Color3.fromRGB(214, 217, 222), up, Enum.Material.Metal)
		p(Cy, Vector3.new(0.7, 1.22, 1.22), amber, CFrame.new(0, 0.2, 0) * up)
		p(Enum.PartType.Ball, Vector3.new(1.2, 1.2, 1.2), Color3.fromRGB(190, 194, 200), CFrame.new(0, 1.3, 0), Enum.Material.Metal)
		p(Cy, Vector3.new(0.5, 0.62, 0.62), dark, CFrame.new(0, 1.85, 0) * up)
		p(B, Vector3.new(0.16, 0.16, 0.26), dark, CFrame.new(0, 1.98, -0.3))
		p(Cy, Vector3.new(0.08, 1.24, 1.24), dark, CFrame.new(0, -1.26, 0) * up)
	end
	-- (pivot upright at the origin: the can's body is a cylinder turned on end, and a turned PrimaryPart would lay
	-- the whole can down when the preview pivots it)
	m.PrimaryPart = nil
	m.WorldPivot = CFrame.identity
	m:SetAttribute("ShopRest", math.pi - 0.55)
	return m
end
-- an item on the weapon it's for: a wrap paints it, a hat sits on it (boost: the hat drawn bigger, for small cards).
-- an item with no weapon (an older save) goes on your primary
function V.item(it: any, boost: number?): Model?
	local w = it.weapon or V.yourGun()
	if it.kind == "hat" then return V.gun(w, nil, it.id, boost) end
	return V.gun(w, it.id, nil)
end
-- the model for any offer (a bundle shows its hero, or one of its items; a single its item on its weapon)
function V.offerModel(o: any, item: any?, boost: number?): Model?
	if o.type == "container" then return V.container(o.id) end
	if item then return V.item(item, boost) end
	if o.type == "bundle" then
		local h = o.hero or {}
		return V.gun(h.weapon or "ar", h.wrap, h.hat, boost)
	end
	return V.item({ kind = o.kind, id = o.item, weapon = o.weapon }, boost)
end
-- the camera backed off just enough for the model to fill its frame. a long thing (a gun) is fitted to the frame's
-- width, so a wide frame shows it big; anything else to its round bounds. zoom > 1 = a little more room round it
local REST = math.pi / 2 + 0.5 -- three-quarters: the barrel to the left, a little towards you
local function fitCam(s: any)
	local a = s.vp.AbsoluteSize
	local aspect = if a.Y > 1 and a.X > 1 then a.X / a.Y else 1
	local v = math.rad(s.cam.FieldOfView) / 2
	local h = math.atan(math.tan(v) * aspect)
	local dv, dh = s.r / math.sin(v), s.r / math.sin(h)
	local d = (if s.long then math.max(dh, dv * 0.5) else math.max(dh, dv)) * s.zoom
	s.cam.CFrame = CFrame.lookAt(Vector3.new(0, s.r * 0.22, d), Vector3.zero)
end
-- a viewport showing a model, turned three-quarters. spin = how it moves: "slow" (sways round the three-quarter view,
-- so a gun is never seen end-on), "hover" (sways while the mouse is on its card), "drag" (you turn it; left alone it
-- eases back and sways), "none"
function V.show(parent: GuiObject, m: Model?, spin: string, zoom: number?): any
	local old = parent:FindFirstChild("Preview")
	if old then
		for i = #spins, 1, -1 do if spins[i].vp == old then table.remove(spins, i) end end
		old:Destroy()
	end
	local vp = new("ViewportFrame", {
		Name = "Preview", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = parent.ZIndex + 1,
		Ambient = Color3.fromRGB(150, 153, 162), LightColor = Color3.fromRGB(255, 248, 240), LightDirection = Vector3.new(-0.5, -1, -0.7),
	}, parent)
	local cam = new("Camera", { FieldOfView = 30 }, vp)
	vp.CurrentCamera = cam
	if not m then return nil end
	local cf, size = m:GetBoundingBox()
	local r = math.max(size.Magnitude / 2, 0.05)
	local rel = m:GetPivot():ToObjectSpace(cf)
	m.Parent = vp
	-- (long: much longer than it is tall, measured in the model's own box, e.g. a gun lying along z)
	local long = math.max(size.X, size.Z) > 2.2 * size.Y
	local rest = m:GetAttribute("ShopRest")
	rest = if type(rest) == "number" then rest else REST
	local s = { vp = vp, cam = cam, r = r, long = long, zoom = zoom or 1.05, model = m, rel = rel, spin = spin, yaw = rest,
		rest = rest, vel = 0, hot = false, drag = false, dragT = -10, t0 = math.random() * 6 }
	fitCam(s)
	m:PivotTo(CFrame.Angles(0.12, s.yaw, 0) * rel:Inverse())
	table.insert(spins, s)
	if spin == "hover" then
		local host = parent:FindFirstAncestorWhichIsA("GuiButton") or parent
		host.MouseEnter:Connect(function() s.hot = true end)
		host.MouseLeave:Connect(function() s.hot = false end)
	elseif spin == "drag" then
		vp.Active = true
		vp.InputBegan:Connect(function(io)
			if io.UserInputType == Enum.UserInputType.MouseButton1 or io.UserInputType == Enum.UserInputType.Touch then
				s.drag, s.last = true, io.Position
			end
		end)
	end
	return s
end
UIS.InputChanged:Connect(function(io)
	if io.UserInputType ~= Enum.UserInputType.MouseMovement and io.UserInputType ~= Enum.UserInputType.Touch then return end
	for _, s in spins do
		if s.drag and s.last then
			local dx = io.Position.X - s.last.X
			s.last = io.Position
			s.yaw += dx * 0.012
			s.vel = dx * 0.6
			s.dragT = os.clock()
		end
	end
end)
UIS.InputEnded:Connect(function(io)
	if io.UserInputType == Enum.UserInputType.MouseButton1 or io.UserInputType == Enum.UserInputType.Touch then
		for _, s in spins do s.drag = false end
	end
end)
RunService.RenderStepped:Connect(function(dt)
	if not S.open then return end
	local now = os.clock()
	for i = #spins, 1, -1 do
		local s = spins[i]
		if not s.vp.Parent then table.remove(spins, i); continue end
		fitCam(s)
		if s.spin == "none" then continue end
		local function toward(target: number, rate: number)
			s.yaw += (((target - s.yaw + math.pi) % (2 * math.pi)) - math.pi) * math.min(1, dt * rate)
		end
		if s.spin == "drag" and s.drag then
			-- (you're turning it)
		elseif s.spin == "drag" and now - s.dragT < 1.5 then
			s.vel *= math.max(0, 1 - dt * 3); s.yaw += s.vel * dt * 0.02 -- a flick coasts
		elseif s.spin == "hover" and not s.hot then
			toward(s.rest, 3)
		else
			local fast = s.spin == "hover"
			toward(s.rest + math.sin((now + s.t0) * (if fast then 1.2 else 0.45)) * (if fast then 0.8 else 0.6), if fast then 4 else 1.5)
		end
		local bob = if s.spin == "hover" then 0 else math.sin(now * 1.1 + s.t0) * 0.03
		s.model:PivotTo(CFrame.new(0, bob, 0) * CFrame.Angles(0.12, s.yaw, 0) * s.rel:Inverse())
	end
end)

-- ======================================================================== the screen
local back = new("ScreenGui", { Name = "JankShopBack", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 40, Enabled = false }, pg)
-- a full-screen button under everything: Modal frees the mouse from first person, and it eats stray clicks
UI.catcher = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = Color3.fromRGB(8, 9, 12), BackgroundTransparency = 0.2, Size = UDim2.fromScale(1, 1), Modal = true }, back)
local gui = new("ScreenGui", { Name = "JankShop", ResetOnSpawn = false, DisplayOrder = 41, ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, pg)
pcall(function() gui.ScreenInsets = Enum.ScreenInsets.DeviceSafeInsets end)
-- the screen the shop lays itself out in: the whole window, or a phone-sized box for a test (ShopUI.fakeScreen)
UI.screen = new("Frame", { Name = "Screen", BackgroundTransparency = 1, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromScale(1, 1), ClipsDescendants = false }, gui)
UI.stage = new("Frame", { Name = "Stage", BackgroundTransparency = 1, Size = UDim2.fromOffset(1280, 720) }, UI.screen)
UI.scale = new("UIScale", {}, UI.stage)
UI.blur = new("BlurEffect", { Name = "JankShopBlur", Size = 0, Enabled = false })
UI.tint = new("ColorCorrectionEffect", { Name = "JankShopTint", Enabled = false })

-- the top: the title and its line, the tabs, the wallet, the close button
UI.top = new("Frame", { Name = "Top", BackgroundTransparency = 1 }, UI.stage)
UI.title = txt(UI.top, "SHOP", 34, T.TEXT, T.FONT_TITLE)
UI.rule = new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromOffset(40, 3) }, UI.top)
UI.sub = txt(UI.top, LINES[1], 14, T.MUTED)
UI.tabRow = new("Frame", { BackgroundTransparency = 1 }, UI.top)
new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder, VerticalAlignment = Enum.VerticalAlignment.Center }, UI.tabRow)
UI.tabs = {}
for i, t in TABS do
	local b = button(UI.tabRow, TAB_NAMES[t], "tab", UDim2.fromOffset(120, 40))
	b.face.LayoutOrder = i
	b.face.MouseButton1Click:Connect(function() ShopUI.tab(t) end)
	UI.tabs[t] = b
end
UI.wallet = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.1, BorderSizePixel = 0 }, UI.top)
T.corner(UI.wallet); T.edge(UI.wallet)
UI.walletTxt = txt(UI.wallet, "", 15, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center)
UI.walletTxt.RichText = true; UI.walletTxt.Size = UDim2.fromScale(1, 1)
UI.close = button(UI.top, "CLOSE", "dark", UDim2.fromOffset(110, 40))
UI.closeKey = T.key(UI.close.face, "B", UDim2.new(1, -30, 0.5, -11))
UI.close.face.TextXAlignment = Enum.TextXAlignment.Left
new("UIPadding", { PaddingLeft = UDim.new(0, 14) }, UI.close.face)
UI.close.face.MouseButton1Click:Connect(function() ShopUI.close() end)

-- the pages, one per tab, all in the same box under the top
UI.body = new("Frame", { Name = "Body", BackgroundTransparency = 1 }, UI.stage)
UI.pages = {}
for _, t in TABS do UI.pages[t] = new("Frame", { Name = t, BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Visible = false }, UI.body) end

local function header(parent: Instance, text: string, right: string?): (TextLabel, TextLabel)
	local l = txt(parent, text, 15, T.MUTED, T.FONT_BOLD)
	l.Size = UDim2.new(1, 0, 0, 22)
	local r = txt(parent, right or "", 14, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
	r.Size = UDim2.new(1, 0, 0, 22)
	return l, r
end

-- ------------------------------------------------------------------------ the offer cards
-- a single (a wrap or a hat): its preview on top, name, rarity line, price or OWNED
local function singleCard(parent: Instance, o: any, order: number): TextButton
	local c = card(parent, o.rarity)
	c.LayoutOrder = order
	-- (a hat is drawn half again its size on a card, or it's a few pixels on the gun; the inspect panel shows it true)
	local view = new("Frame", { Name = "View", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 4), Size = UDim2.new(1, 0, 1, -78) }, c)
	V.show(view, V.offerModel(o, nil, if o.kind == "hat" then 1.6 else nil), "hover", 1.08)
	local name = txt(c, o.name, 16, T.TEXT, T.FONT_BOLD)
	name.Position = UDim2.new(0, 12, 1, -74); name.Size = UDim2.new(1, -24, 0, 20)
	-- the weapon it's for: a wrap or a hat is owned for one weapon
	local wl = txt(c, "FOR " .. string.upper(Shop.weaponName(o.weapon)), 12, T.SOFT, T.FONT_BOLD)
	wl.Position = UDim2.new(0, 12, 1, -53); wl.Size = UDim2.new(1, -24, 0, 15)
	-- (on a phone the kind word goes: the rarity alone fits beside the price)
	local rl = rarityLine(c, o.rarity, Shop.KIND_NAMES[o.kind] or o.kind, if S.compact then 12 else 11, S.compact)
	rl.Position = UDim2.new(0, 12, 1, -32); rl.Size = UDim2.new(1, -96, 0, 15)
	local owned = Till.owns(o.kind, o.item, o.weapon)
	local pr = txt(c, if owned then "OWNED" else (if Shop.free() then "FREE" else priceText(o.robux)), 14, if owned then T.MUTED else T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Right)
	pr.RichText = true
	pr.Position = UDim2.new(1, -92, 1, -33); pr.Size = UDim2.new(0, 80, 0, 16)
	if owned then
		local tag = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.15, BorderSizePixel = 0, Position = UDim2.fromOffset(8, 8), Size = UDim2.fromOffset(64, 22), ZIndex = 5 }, c)
		T.corner(tag, 4)
		local l = txt(tag, "OWNED", 11, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center); l.Size = UDim2.fromScale(1, 1); l.ZIndex = 6
	end
	c.MouseButton1Click:Connect(function() ShopUI.inspect(o.id) end)
	return c
end
-- a bundle: the hero preview, the name, how many items, the price
local function bundleCard(parent: Instance, o: any, order: number): TextButton
	local c = card(parent, o.rarity)
	c.LayoutOrder = order
	local view = new("Frame", { Name = "View", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 26), Size = UDim2.new(1, 0, 1, -100) }, c)
	V.show(view, V.offerModel(o), "hover", 1.08)
	local eb = txt(c, "BUNDLE  ·  " .. #o.items .. " ITEMS", 11, T.MUTED, T.FONT_BOLD)
	eb.Position = UDim2.fromOffset(14, 12); eb.Size = UDim2.new(1, -28, 0, 14)
	local name = txt(c, string.upper(o.name), 20, T.TEXT, T.FONT_TITLE)
	name.Position = UDim2.new(0, 14, 1, -66); name.Size = UDim2.new(1, -28, 0, 24)
	local rl = rarityLine(c, o.rarity, "BUNDLE", 11)
	rl.Position = UDim2.new(0, 14, 1, -36); rl.Size = UDim2.new(0.5, 0, 0, 15)
	local miss = Till.missing(o)
	local pr = txt(c, if miss == 0 then "OWNED" elseif Shop.free() then priceText(o.robux) .. "   FREE" else priceText(o.robux), 14, if miss == 0 then T.MUTED else T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Right)
	pr.RichText = true
	pr.Position = UDim2.new(0.4, 0, 1, -37); pr.Size = UDim2.new(0.6, -14, 0, 16)
	c.MouseButton1Click:Connect(function() ShopUI.inspect(o.id) end)
	return c
end

-- ------------------------------------------------------------------------ FEATURED: today's bundle, big; the daily row
do
	local pg_ = UI.pages.featured
	UI.hero = card(pg_, nil)
	UI.hero.Name = "Hero"
	UI.heroView = new("Frame", { Name = "View", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, UI.hero)
	UI.heroEyebrow = txt(UI.hero, "FEATURED BUNDLE", 12, T.ACCENT, T.FONT_BOLD)
	UI.heroEyebrow.Position = UDim2.fromOffset(20, 18); UI.heroEyebrow.Size = UDim2.new(1, -40, 0, 16); UI.heroEyebrow.ZIndex = 5
	UI.heroName = txt(UI.hero, "", 34, T.TEXT, T.FONT_TITLE)
	UI.heroName.Position = UDim2.fromOffset(20, 36); UI.heroName.Size = UDim2.new(1, -40, 0, 40); UI.heroName.ZIndex = 5
	UI.heroBlurb = txt(UI.hero, "", 14, T.MUTED)
	UI.heroBlurb.Position = UDim2.fromOffset(20, 78); UI.heroBlurb.Size = UDim2.new(1, -40, 0, 18); UI.heroBlurb.ZIndex = 5
	UI.heroTimer = txt(UI.hero, "", 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
	UI.heroTimer.Position = UDim2.new(0, 20, 0, 18); UI.heroTimer.Size = UDim2.new(1, -40, 0, 16); UI.heroTimer.ZIndex = 5
	-- the strip along the bottom: what's in it (chips), the price and the button
	UI.heroStrip = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.25, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0, 74), ZIndex = 5 }, UI.hero)
	UI.heroChips = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(16, 0), Size = UDim2.new(1, -220, 1, 0), ZIndex = 5 }, UI.heroStrip)
	new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6), VerticalAlignment = Enum.VerticalAlignment.Center, SortOrder = Enum.SortOrder.LayoutOrder }, UI.heroChips)
	UI.heroBtn = button(UI.heroStrip, "VIEW", "main", UDim2.fromOffset(180, 46), UDim2.new(1, -196, 0.5, -23))
	UI.heroBtn.face.ZIndex = 6
	UI.heroBtn.face.MouseButton1Click:Connect(function() if S.heroId then ShopUI.inspect(S.heroId) end end)
	UI.hero.MouseButton1Click:Connect(function() if S.heroId then ShopUI.inspect(S.heroId) end end)

	UI.daily = new("Frame", { Name = "Daily", BackgroundTransparency = 1 }, pg_)
	UI.dailyHead, UI.dailyTimer = header(UI.daily, "DAILY", "")
	UI.dailyGrid = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 30), Size = UDim2.new(1, 0, 1, -30) }, UI.daily)
	UI.dailyLayout = new("UIGridLayout", { CellPadding = UDim2.fromOffset(12, 12), CellSize = UDim2.new(1 / 3, -8, 0.5, -6), SortOrder = Enum.SortOrder.LayoutOrder }, UI.dailyGrid)
end
-- a small chip in the hero strip: a wrap's paint or a hat's name, with its rarity under it
local function itemChip(parent: Instance, it: any, order: number)
	local name, r = Shop.itemInfo(it.kind, it.id)
	local f = new("Frame", { BackgroundColor3 = T.CARD, BorderSizePixel = 0, Size = UDim2.fromOffset(if S.compact then 40 else 46, if S.compact then 40 else 46), LayoutOrder = order, ZIndex = 6 }, parent)
	T.corner(f, 5)
	if it.kind == "wrap" then
		local chip = new("Frame", { BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(5, 5), Size = UDim2.new(1, -10, 1, -13), ZIndex = 7 }, f)
		T.corner(chip, 3)
		paintChip(chip, it.id)
	else
		local view = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 1, -4), ZIndex = 7 }, f)
		V.show(view, V.hat(it.id), "none", 1.1)
	end
	new("Frame", { BackgroundColor3 = rarityColor(r), BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -3), Size = UDim2.new(1, -14, 0, 2), ZIndex = 8 }, f)
end

function ShopUI.fillFeatured()
	local rot = Shop.rotation()
	local o = Shop.offer(rot.hero)
	S.heroId = rot.hero
	if o then
		UI.heroName.Text = string.upper(o.name)
		UI.heroBlurb.Text = o.blurb
		V.show(UI.heroView, V.offerModel(o), "slow", 1.08)
		for _, c in UI.heroChips:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
		for i, it in o.items do itemChip(UI.heroChips, it, i) end
		local miss = Till.missing(o)
		UI.heroBtn.set(if miss == 0 then "OWNED" elseif Shop.free() then "CLAIM  " .. priceText(o.robux) else priceText(o.robux), miss ~= 0)
	end
	for _, c in UI.dailyGrid:GetChildren() do if c:IsA("GuiButton") then c:Destroy() end end
	for i, id in rot.daily do
		local so = Shop.offer(id)
		if so then singleCard(UI.dailyGrid, so, i) end
	end
end

-- ------------------------------------------------------------------------ BUNDLES: every bundle, in a grid
do
	local pg_ = UI.pages.bundles
	UI.bundleScroll = new("ScrollingFrame", {
		BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 4, ScrollBarImageColor3 = T.MUTED, ScrollingDirection = Enum.ScrollingDirection.Y,
	}, pg_)
	UI.bundleLayout = new("UIGridLayout", { CellPadding = UDim2.fromOffset(14, 14), CellSize = UDim2.fromOffset(380, 300), SortOrder = Enum.SortOrder.LayoutOrder }, UI.bundleScroll)
	new("UIPadding", { PaddingRight = UDim.new(0, 8), PaddingBottom = UDim.new(0, 8) }, UI.bundleScroll)
end
function ShopUI.fillBundles()
	for _, c in UI.bundleScroll:GetChildren() do if c:IsA("GuiButton") then c:Destroy() end end
	local rot = Shop.rotation()
	local list = table.clone(Shop.bundles)
	-- today's featured one first, then dearest first
	table.sort(list, function(a, b)
		if (a.id == rot.hero) ~= (b.id == rot.hero) then return a.id == rot.hero end
		return a.robux > b.robux
	end)
	for i, o in list do bundleCard(UI.bundleScroll, o, i) end
end

-- ------------------------------------------------------------------------ CONTAINERS: the three, side by side
do
	local pg_ = UI.pages.containers
	UI.boxRow = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, pg_)
	new("UIGridLayout", { CellPadding = UDim2.fromOffset(14, 0), CellSize = UDim2.new(1 / 3, -10, 1, 0), SortOrder = Enum.SortOrder.LayoutOrder }, UI.boxRow)
end
function ShopUI.fillContainers()
	for _, c in UI.boxRow:GetChildren() do if c:IsA("GuiButton") then c:Destroy() end end
	local k = S.compact
	for i, o in Shop.containers do
		local c = card(UI.boxRow, nil)
		c.LayoutOrder = i
		-- (on a phone the words squeeze up so the preview keeps some room)
		local textH = if k then 162 else 236
		local view = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, if k then 26 else 40), Size = UDim2.new(1, 0, 1, -(textH + (if k then 26 else 40))) }, c)
		V.show(view, V.offerModel(o), "slow", 0.95)
		local eb = txt(c, "CONTAINER  ·  ONE RANDOM ITEM", 11, T.MUTED, T.FONT_BOLD)
		eb.Position = UDim2.fromOffset(if k then 12 else 18, if k then 10 else 16); eb.Size = UDim2.new(1, -36, 0, 14)
		local pad = if k then 12 else 18
		local name = txt(c, string.upper(o.name), if k then 20 else 26, T.TEXT, T.FONT_TITLE)
		name.Position = UDim2.new(0, pad, 1, if k then -158 else -188); name.Size = UDim2.new(1, -2 * pad, 0, if k then 24 else 30)
		local holds = txt(c, o.blurb, if k then 12 else 13, T.MUTED)
		holds.Position = UDim2.new(0, pad, 1, if k then -132 else -154); holds.Size = UDim2.new(1, -2 * pad, 0, if k then 28 else 34); holds.TextWrapped = true
		holds.TextTruncate = Enum.TextTruncate.None; holds.TextYAlignment = Enum.TextYAlignment.Top
		local have = Till.count(o.id)
		local hv = txt(c, if have > 0 then "YOU HAVE " .. have else "", 12, T.SOFT, T.FONT_BOLD)
		hv.Position = UDim2.new(0, pad, 1, if k then -100 else -116); hv.Size = UDim2.new(0.5, 0, 0, 16)
		hv.Visible = not k
		-- two rows of 44-tall buttons: ODDS and the x1 / x5 / x10 picker; then OPEN (only with some in stock) and CLAIM
		local bh = 44 -- (a touch target)
		local n = S.count[o.id] or 1
		local row1 = -(2 * bh + (if k then 12 else 6))
		local odds = button(c, "ODDS", "dark", UDim2.new(1 / 3, -(pad + 4), 0, bh), UDim2.new(0, pad, 1, row1))
		odds.face.MouseButton1Click:Connect(function() ShopUI.odds(o.id) end)
		local pick = ShopUI.countPicker(c, o.id, 1)
		pick.Position = UDim2.new(1 / 3, 4, 1, row1); pick.Size = UDim2.new(2 / 3, -(pad + 4), 0, bh)
		local row2 = -(bh + (if k then 8 else 2))
		local bs = Till.boxState(o.id)
		local open = button(c, "OPEN", "dark", UDim2.new(0.4, -(pad + 4), 0, bh), UDim2.new(0, pad, 1, row2))
		open.face.Visible = have > 0 and bs == nil
		open.set("OPEN  x" .. math.min(n, have), have > 0)
		open.face.MouseButton1Click:Connect(function() local h = Till.count(o.id); if h > 0 then ShopUI.openBox(o.id, math.min(S.count[o.id] or 1, h)) end end)
		local buy = button(c, "", "main", UDim2.new(1, -2 * pad, 0, bh), UDim2.new(0, pad, 1, row2))
		if open.face.Visible then buy.face.Position = UDim2.new(0.4, 4, 1, row2); buy.face.Size = UDim2.new(0.6, -(pad + 4), 0, bh) end
		local word = if n > 1 then "  x" .. n else ""
		if bs == "soon" then buy.set("COMING SOON", false)
		elseif bs == "empty" then buy.set("YOU HAVE IT ALL", false)
		elseif S.restricted and not Shop.free() then buy.set("NOT AVAILABLE HERE", false)
		else buy.set((if Shop.free() then "CLAIM" else "BUY") .. word .. "  " .. priceText(o.robux * n), true) end
		buy.face.MouseButton1Click:Connect(function() ShopUI.ask(o.id) end)
		c.MouseButton1Click:Connect(function() ShopUI.inspect(o.id) end)
	end
end

-- ------------------------------------------------------------------------ INVENTORY: what you own
do
	local pg_ = UI.pages.inventory
	UI.invFilters = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 36) }, pg_)
	new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder }, UI.invFilters)
	UI.invBtns = {}
	for i, f in { "all", "containers", "wrap", "hat" } do
		local b = button(UI.invFilters, ({ all = "ALL", containers = "CONTAINERS", wrap = "WRAPS", hat = "HATS" })[f], "dark", UDim2.fromOffset(120, 34))
		b.face.LayoutOrder = i; b.face.TextSize = 13
		b.face.MouseButton1Click:Connect(function() S.invFilter = f; ShopUI.fillInventory() end)
		UI.invBtns[f] = b
	end
	UI.invCount = txt(pg_, "", 13, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right)
	UI.invCount.Size = UDim2.new(1, 0, 0, 34)
	UI.invScroll = new("ScrollingFrame", {
		BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 48), Size = UDim2.new(1, 0, 1, -48), CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 4, ScrollBarImageColor3 = T.MUTED, ScrollingDirection = Enum.ScrollingDirection.Y,
	}, pg_)
	-- (one section per weapon, each a heading and a grid of cards: wraps and hats are owned per weapon)
	new("UIListLayout", { Padding = UDim.new(0, 14), SortOrder = Enum.SortOrder.LayoutOrder }, UI.invScroll)
	new("UIPadding", { PaddingRight = UDim.new(0, 8), PaddingBottom = UDim.new(0, 8) }, UI.invScroll)
	UI.invEmpty = txt(pg_, "", 16, T.MUTED, T.FONT, Enum.TextXAlignment.Center)
	UI.invEmpty.Position = UDim2.fromOffset(0, 120); UI.invEmpty.Size = UDim2.new(1, 0, 0, 24)
end
S.invCell = UDim2.fromOffset(170, 190)
-- a section of the inventory: a heading ("SMG  ·  3") over a grid of cards. returns the grid
local function invSection(title: string, count: number, order: number): Frame
	local sec = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, -8, 0, 0), AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = order }, UI.invScroll)
	new("UIListLayout", { Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder }, sec)
	local h = txt(sec, string.upper(title) .. "  ·  " .. count, 14, T.MUTED, T.FONT_BOLD)
	h.Size = UDim2.new(1, 0, 0, 22); h.LayoutOrder = 1
	local grid = new("Frame", { Name = "Grid", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 0), AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = 2 }, sec)
	new("UIGridLayout", { CellPadding = UDim2.fromOffset(10, 10), CellSize = S.invCell, SortOrder = Enum.SortOrder.LayoutOrder }, grid)
	return grid
end
function ShopUI.fillInventory()
	for _, c in UI.invScroll:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	for f, b in UI.invBtns do
		b.base = if f == S.invFilter then T.CARD_HI else T.CARD
		b.face.BackgroundColor3 = b.base
		b.mark.Visible = f == S.invFilter
	end
	local f, n, order = S.invFilter, 0, 0
	-- containers you haven't opened: a card each with an OPEN button
	local boxes = {}
	if f == "all" or f == "containers" then
		for _, o in Shop.containers do if Till.count(o.id) > 0 then table.insert(boxes, o) end end
	end
	if #boxes > 0 then
		local grid = invSection("containers", #boxes, 0)
		for _, o in boxes do
			local have = Till.count(o.id)
			do
				n += 1; order += 1
				local c = card(grid, nil)
				c.LayoutOrder = order
				local view = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 1, -78) }, c)
				V.show(view, V.container(o.id), "hover", 1.0)
				local name = txt(c, o.name, 15, T.TEXT, T.FONT_BOLD)
				name.Position = UDim2.new(0, 10, 1, -76); name.Size = UDim2.new(1, -20, 0, 18)
				local cnt = txt(c, "x" .. have, 13, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Right)
				cnt.Position = UDim2.new(0, 10, 1, -76); cnt.Size = UDim2.new(1, -20, 0, 18)
				local ob = button(c, "OPEN", "main", UDim2.new(1, -20, 0, 40), UDim2.new(0, 10, 1, -48))
				ob.face.TextSize = 14
				ob.face.MouseButton1Click:Connect(function() ShopUI.openBox(o.id) end)
			end
		end
	end
	-- wraps and hats, grouped by the weapon they're for (the loadout's order), rarest first in each
	local byWeapon: { [string]: { any } } = {}
	for _, kind in { "wrap", "hat" } do
		if f == "all" or f == kind then
			for key in S.inv[kind] do
				local id, w = Shop.unkey(key)
				if Shop.exists(kind, id, w) then
					local name, r = Shop.itemInfo(kind, id)
					local g = w or "_any"
					byWeapon[g] = byWeapon[g] or {}
					table.insert(byWeapon[g], { kind = kind, id = id, weapon = w, name = name, rarity = r })
				end
			end
		end
	end
	local groups = table.clone(Shop.WEAPONS)
	table.insert(groups, "_any") -- (things kept without a weapon, from an older save)
	for gi, g in groups do
		local items = byWeapon[g]
		if items and #items > 0 then
			table.sort(items, function(a, b)
				if a.kind ~= b.kind then return a.kind == "wrap" end
				if Shop.rank(a.rarity) ~= Shop.rank(b.rarity) then return Shop.rank(a.rarity) > Shop.rank(b.rarity) end
				return a.name < b.name
			end)
			local grid = invSection(if g == "_any" then "any weapon" else Shop.weaponName(g), #items, gi)
			for _, it in items do
				n += 1; order += 1
				local c = card(grid, it.rarity)
				c.LayoutOrder = order
				local view = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 1, -50) }, c)
				V.show(view, V.item(it, if it.kind == "hat" then 1.6 else nil), "hover", 1.08)
				local name = txt(c, it.name, 15, T.TEXT, T.FONT_BOLD)
				name.Position = UDim2.new(0, 10, 1, -46); name.Size = UDim2.new(1, -20, 0, 18)
				local rl = rarityLine(c, it.rarity, Shop.KIND_NAMES[it.kind], 10)
				rl.Position = UDim2.new(0, 10, 1, -24); rl.Size = UDim2.new(1, -20, 0, 14)
				local oid = it.kind .. ":" .. it.id .. "@" .. (it.weapon or V.yourGun())
				c.MouseButton1Click:Connect(function() ShopUI.inspect(oid) end)
			end
		end
	end
	UI.invCount.Text = if S.invOk then n .. " THINGS" else ""
	UI.invEmpty.Text = if not S.invOk then "can't see your inventory right now. the till isn't answering."
		elseif n == 0 then "nothing here yet. claim a bundle or open a container." else ""
end

-- ======================================================================== overlays: inspect, odds, confirm, toast
-- one dim layer over the body, then the panel
UI.dim = new("TextButton", { Name = "Dim", Text = "", AutoButtonColor = false, BackgroundColor3 = Color3.fromRGB(6, 7, 9), BackgroundTransparency = 0.35, Size = UDim2.fromScale(1, 1), Visible = false, ZIndex = 20 }, UI.stage)

-- INSPECT: the big turnable preview on the left, the words and the button on the right
UI.insp = new("Frame", { Name = "Inspect", BackgroundColor3 = T.BG, BackgroundTransparency = 0.04, BorderSizePixel = 0, Visible = false, ZIndex = 21 }, UI.stage)
T.corner(UI.insp, 8); T.edge(UI.insp)
do
	local I = UI.insp
	UI.inspView = new("Frame", { Name = "View", BackgroundColor3 = T.CARD, BorderSizePixel = 0, Position = UDim2.fromOffset(14, 14), Size = UDim2.new(0.58, -14, 1, -28), ZIndex = 22 }, I)
	T.corner(UI.inspView)
	UI.inspHint = txt(UI.inspView, "DRAG TO TURN", 11, T.DIM, T.FONT_BOLD, Enum.TextXAlignment.Center)
	UI.inspHint.AnchorPoint = Vector2.new(0, 1); UI.inspHint.Position = UDim2.new(0, 0, 1, -10); UI.inspHint.Size = UDim2.new(1, 0, 0, 14); UI.inspHint.ZIndex = 24
	UI.inspSide = new("Frame", { BackgroundTransparency = 1, Position = UDim2.new(0.58, 14, 0, 14), Size = UDim2.new(0.42, -28, 1, -28), ZIndex = 22 }, I)
	local Sd = UI.inspSide
	UI.inspBack = button(Sd, "BACK", "dark", UDim2.fromOffset(90, 34))
	UI.inspBack.face.TextSize = 13; UI.inspBack.face.ZIndex = 23
	UI.inspBack.face.MouseButton1Click:Connect(function() ShopUI.uninspect() end)
	UI.inspEyebrow = rarityLine(Sd, "common", "", 12)
	UI.inspEyebrow.Position = UDim2.fromOffset(0, 52)
	UI.inspName = txt(Sd, "", 30, T.TEXT, T.FONT_TITLE); UI.inspName.ZIndex = 23
	UI.inspName.Position = UDim2.fromOffset(0, 72); UI.inspName.Size = UDim2.new(1, 0, 0, 38)
	UI.inspBlurb = txt(Sd, "", 14, T.MUTED); UI.inspBlurb.ZIndex = 23
	UI.inspBlurb.Position = UDim2.fromOffset(0, 114); UI.inspBlurb.Size = UDim2.new(1, 0, 0, 38)
	UI.inspBlurb.TextWrapped = true; UI.inspBlurb.TextTruncate = Enum.TextTruncate.None; UI.inspBlurb.TextYAlignment = Enum.TextYAlignment.Top
	UI.inspList = new("ScrollingFrame", {
		BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(0, 160), Size = UDim2.new(1, 0, 1, -276), CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 3, ScrollBarImageColor3 = T.MUTED, ZIndex = 23,
	}, Sd)
	new("UIListLayout", { Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, UI.inspList)
	UI.inspNote = txt(Sd, "", 13, T.MUTED); UI.inspNote.ZIndex = 23; UI.inspNote.RichText = true
	UI.inspNote.AnchorPoint = Vector2.new(0, 1); UI.inspNote.Position = UDim2.new(0, 0, 1, -104); UI.inspNote.Size = UDim2.new(1, 0, 0, 18)
	UI.inspOdds = button(Sd, "ODDS", "dark", UDim2.new(0.5, -5, 0, 40), UDim2.new(0, 0, 1, -94))
	UI.inspOdds.face.ZIndex = 23
	UI.inspOdds.face.MouseButton1Click:Connect(function() if S.inspect then ShopUI.odds(S.inspect) end end)
	UI.inspOpen = button(Sd, "OPEN", "dark", UDim2.new(0.5, -5, 0, 40), UDim2.new(0.5, 5, 1, -94))
	UI.inspOpen.face.ZIndex = 23
	UI.inspOpen.face.MouseButton1Click:Connect(function()
		local h = if S.inspect then Till.count(S.inspect) else 0
		if h > 0 then ShopUI.openBox(S.inspect, math.min(S.count[S.inspect] or 1, h)) end
	end)
	UI.inspBuy = button(Sd, "", "main", UDim2.new(1, 0, 0, 48), UDim2.new(0, 0, 1, -48))
	UI.inspBuy.face.TextSize = 17; UI.inspBuy.face.ZIndex = 23
	UI.inspBuy.face.MouseButton1Click:Connect(function() if S.inspect then ShopUI.ask(S.inspect) end end)
end
-- one row in a bundle's list: its chip, name, kind and rarity; OWNED on the right. click = see it on the big preview
local function listRow(it: any, order: number, o: any)
	local name, r = Shop.itemInfo(it.kind, it.id)
	local row = new("TextButton", { Text = "", AutoButtonColor = false, BackgroundColor3 = T.CARD, BorderSizePixel = 0, Size = UDim2.new(1, -6, 0, 46), LayoutOrder = order, ZIndex = 24 }, UI.inspList)
	T.corner(row, 5)
	local st = T.edge(row, nil, 0.92)
	local chip = new("Frame", { BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(6, 6), Size = UDim2.fromOffset(52, 34), ZIndex = 25 }, row)
	T.corner(chip, 3)
	if it.kind == "wrap" then paintChip(chip, it.id) else
		chip.BackgroundColor3 = T.BG
		V.show(chip, V.hat(it.id), "none", 1.1)
	end
	-- "Sakura Storm · SMG": the item and the weapon it's for
	local nm = txt(row, Shop.itemLabel(it), 15, T.TEXT, T.FONT_BOLD); nm.ZIndex = 25
	nm.Position = UDim2.fromOffset(68, 5); nm.Size = UDim2.new(1, -150, 0, 20)
	local _ = name
	local rl = rarityLine(row, r, Shop.KIND_NAMES[it.kind] or it.kind, 10)
	rl.Position = UDim2.fromOffset(68, 26); rl.Size = UDim2.new(1, -150, 0, 14)
	for _, d in rl:GetDescendants() do if d:IsA("GuiObject") then d.ZIndex = 25 end end
	local own = Till.owns(it.kind, it.id, it.weapon)
	local tag = txt(row, if own then "OWNED" else "", 11, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Right); tag.ZIndex = 25
	tag.Position = UDim2.new(1, -86, 0, 0); tag.Size = UDim2.new(0, 76, 1, 0)
	row.MouseEnter:Connect(function() row.BackgroundColor3 = T.CARD_HI end)
	row.MouseLeave:Connect(function() if S.preview ~= it then row.BackgroundColor3 = T.CARD end end)
	row.MouseButton1Click:Connect(function()
		play("click")
		for _, x in UI.inspList:GetChildren() do
			if x:IsA("TextButton") then
				x.BackgroundColor3 = T.CARD
				local xs = x:FindFirstChildOfClass("UIStroke")
				if xs then xs.Color = T.EDGE; xs.Transparency = 0.92 end
			end
		end
		if S.preview == it then
			S.preview = nil
			V.show(UI.inspView, V.offerModel(o), "drag", 1.1)
		else
			S.preview = it
			row.BackgroundColor3 = T.CARD_HI; st.Color = T.ACCENT; st.Transparency = 0.3
			V.show(UI.inspView, V.offerModel(o, it), "drag", if it.kind == "hat" then 1.0 else 1.1)
		end
		UI.inspHint.Parent = UI.inspView
	end)
end
function ShopUI.fillInspect()
	local o = Shop.offer(S.inspect)
	if not o then return end
	S.preview = nil
	V.show(UI.inspView, V.offerModel(o), "drag", if o.type == "container" then 0.95 elseif o.kind == "hat" then 1.0 else 1.1)
	UI.inspHint.Parent = UI.inspView
	for _, c in UI.inspList:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	UI.inspEyebrow:Destroy()
	local kindWord = if o.type == "bundle" then "BUNDLE  ·  " .. #o.items .. " ITEMS" elseif o.type == "container" then "CONTAINER" else (Shop.KIND_NAMES[o.kind] or "") .. "  ·  FOR " .. string.upper(Shop.weaponName(o.weapon))
	UI.inspEyebrow = rarityLine(UI.inspSide, o.rarity, kindWord, 12)
	UI.inspEyebrow.Position = UDim2.fromOffset(0, 50)
	for _, d in UI.inspEyebrow:GetDescendants() do if d:IsA("GuiObject") then d.ZIndex = 23 end end
	UI.inspName.Text = string.upper(o.name)
	local isBox = o.type == "container"
	UI.inspOdds.face.Visible = isBox
	UI.inspOpen.face.Visible = isBox
	-- the buttons at the foot: a container has ODDS + the x1/x5/x10 picker over (OPEN +) CLAIM; the rest just CLAIM
	local oldPick = UI.inspSide:FindFirstChild("Count")
	if oldPick then oldPick:Destroy() end
	UI.inspBuy.face.Position = UDim2.new(0, 0, 1, -48); UI.inspBuy.face.Size = UDim2.new(1, 0, 0, 48)
	if isBox then
		UI.inspOdds.face.Position = UDim2.new(0, 0, 1, -100); UI.inspOdds.face.Size = UDim2.new(1 / 3, -4, 0, 44)
		local pick = ShopUI.countPicker(UI.inspSide, o.id, 23)
		pick.Position = UDim2.new(1 / 3, 4, 1, -100); pick.Size = UDim2.new(2 / 3, -4, 0, 44)
		UI.inspOpen.face.Position = UDim2.new(0, 0, 1, -48); UI.inspOpen.face.Size = UDim2.new(0.4, -4, 0, 48)
	end
	-- the side column, top to bottom: back, rarity line, name, blurb (not on a phone), the list, a note, the buttons
	local c = S.compact
	local nameY = if c then 66 else 72
	local listY = if c then 104 else 160
	local foot = if isBox then 104 else 56 -- what sits under the note: odds + open + buy, or just buy
	UI.inspEyebrow.Position = UDim2.fromOffset(0, if c then 46 else 50)
	UI.inspName.Position = UDim2.fromOffset(0, nameY)
	UI.inspName.TextSize = if c then 22 else 30
	UI.inspName.Size = UDim2.new(1, 0, 0, if c then 30 else 38)
	UI.inspBlurb.Visible = not c
	UI.inspNote.Position = UDim2.new(0, 0, 1, -foot)
	UI.inspList.Position = UDim2.fromOffset(0, listY)
	UI.inspList.Size = UDim2.new(1, 0, 1, -(listY + foot + 26))
	if o.type == "bundle" then
		UI.inspBlurb.Text = o.blurb
		for i, it in o.items do listRow(it, i, o) end
		local miss = Till.missing(o)
		UI.inspNote.Text = string.format("worth %s %s one by one%s", ROBUX, commas(Shop.worth(o)), if miss > 0 and miss < #o.items then ". you already have " .. (#o.items - miss) else "")
		UI.inspBuy.set(if miss == 0 then "OWNED" elseif Shop.free() then "CLAIM  " .. priceText(o.robux) else "BUY  " .. priceText(o.robux), miss > 0)
	elseif isBox then
		UI.inspBlurb.Text = o.blurb .. " holds " .. (o.pool or "items") .. "."
		local have = Till.count(o.id)
		local bs = Till.boxState(o.id)
		local n = S.count[o.id] or 1
		UI.inspNote.Text = if bs == "soon" then "no weapon skins on roblox yet" elseif have > 0 then "you have " .. have .. " to open" else "these are the odds for you, right now"
		UI.inspOpen.face.Visible = have > 0 and bs == nil
		UI.inspOpen.set("OPEN  x" .. math.min(n, math.max(have, 1)), have > 0 and bs == nil)
		if UI.inspOpen.face.Visible then UI.inspBuy.face.Position = UDim2.new(0.4, 4, 1, -48); UI.inspBuy.face.Size = UDim2.new(0.6, -4, 0, 48) end
		local word = if n > 1 then "  x" .. n else ""
		if bs == "soon" then UI.inspBuy.set("COMING SOON", false)
		elseif bs == "empty" then UI.inspBuy.set("YOU HAVE IT ALL", false)
		elseif S.restricted and not Shop.free() then UI.inspBuy.set("NOT AVAILABLE HERE", false)
		else UI.inspBuy.set((if Shop.free() then "CLAIM" else "BUY") .. word .. "  " .. priceText(o.robux * n), true) end
		ShopUI.oddsRows(UI.inspList, o.id, 24)
	else
		local own = Till.owns(o.kind, o.item, o.weapon)
		local onSale = Shop.onSale(o.id)
		local wn = Shop.weaponName(o.weapon)
		UI.inspBlurb.Text = if o.kind == "hat" then "a hat for your " .. wn .. ". it goes on that gun only. wear it from the loadout [L]."
			else "a wrap for your " .. wn .. ". it paints that gun only. pick how much it covers in the loadout [L]."
		UI.inspNote.Text = if own then "it's yours. wear it from the loadout [L]." elseif onSale then "in today's daily rotation" else "not in today's rotation"
		UI.inspBuy.set(if own then "OWNED" elseif not onSale then "NOT ON SALE TODAY" elseif Shop.free() then "CLAIM  " .. priceText(o.robux) else "BUY  " .. priceText(o.robux), not own and onSale)
	end
end
function ShopUI.inspect(id: string)
	if not Shop.offer(id) then return end
	play("click")
	S.inspect = id
	ShopUI.fillInspect()
	ShopUI.layer()
end
function ShopUI.uninspect()
	S.inspect = nil
	ShopUI.layer()
	V.show(UI.inspView, nil, "none")
end
-- which overlay shows: the odds or confirm panel on top hides the inspect panel under it (its list drew through the
-- panel above it in a test), and the dim layer is up while any of them is
function ShopUI.layer()
	local top = UI.confirm.Visible or UI.odds.Visible
	UI.insp.Visible = S.inspect ~= nil and not top
	UI.dim.Visible = top or S.inspect ~= nil
end
-- every overlay shut (a tab change, a new open, after an opening)
function ShopUI.shutOverlays()
	S.pending = nil
	UI.odds.Visible = false; UI.confirm.Visible = false
	if S.inspect then ShopUI.uninspect() else ShopUI.layer() end
end

-- ODDS: every rarity a container can give, its chance, how many things are in it
UI.odds = new("Frame", { Name = "Odds", BackgroundColor3 = T.BG, BackgroundTransparency = 0.02, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(440, 360), Visible = false, ZIndex = 30 }, UI.stage)
T.corner(UI.odds, 8); T.edge(UI.odds)
do
	UI.oddsTitle = txt(UI.odds, "", 22, T.TEXT, T.FONT_TITLE); UI.oddsTitle.ZIndex = 31
	UI.oddsTitle.Position = UDim2.fromOffset(22, 18); UI.oddsTitle.Size = UDim2.new(1, -44, 0, 28)
	new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Position = UDim2.fromOffset(22, 50), Size = UDim2.fromOffset(32, 3), ZIndex = 31 }, UI.odds)
	UI.oddsList = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(22, 66), Size = UDim2.new(1, -44, 1, -150), ZIndex = 31 }, UI.odds)
	new("UIListLayout", { Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, UI.oddsList)
	UI.oddsFoot = txt(UI.odds, "", 12, T.MUTED); UI.oddsFoot.ZIndex = 31
	UI.oddsFoot.TextWrapped = true; UI.oddsFoot.TextTruncate = Enum.TextTruncate.None
	UI.oddsFoot.Position = UDim2.new(0, 22, 1, -80); UI.oddsFoot.Size = UDim2.new(1, -44, 0, 30)
	UI.oddsOk = button(UI.odds, "GOT IT", "dark", UDim2.new(1, -44, 0, 38), UDim2.new(0, 22, 1, -50))
	UI.oddsOk.face.ZIndex = 31
	UI.oddsOk.face.MouseButton1Click:Connect(function() UI.odds.Visible = false; ShopUI.layer() end)
end
-- the odds rows into any list (the odds panel, the inspect panel, the confirm panel): a bar in the rarity's colour,
-- its name, the chance. nil from the loot module = say so rather than show numbers the server might not use
function ShopUI.oddsRows(list: Instance, cid: string, z: number, rowH: number?): boolean
	local rows, info = Shop.odds(cid, Till.ownedSets())
	if not rows or #rows == 0 or (info and (info.soon or info.empty)) then
		local why = if info and info.soon then "coming soon: nothing in it is on roblox yet."
			elseif info and info.empty then "you own everything that can come out of it."
			else "the odds come from the loot server, which isn't answering. nothing can be opened until it does."
		local l = txt(list, why, 13, T.MUTED)
		l.TextWrapped = true; l.TextTruncate = Enum.TextTruncate.None; l.Size = UDim2.new(1, 0, 0, 36); l.ZIndex = z + 1
		return false
	end
	local sorted = table.clone(rows)
	table.sort(sorted, function(a, b) return Shop.rank(a.rarity) > Shop.rank(b.rarity) end)
	-- (Roblox's rule for paid random items: every chance shown as a percentage, adding up to 100: a total row says so)
	local total = 0
	for _, r in sorted do total += r.pct or 0 end
	table.insert(sorted, { rarity = "", pct = total, isTotal = true })
	for i, r in sorted do
		local row = new("Frame", { BackgroundColor3 = T.CARD, BackgroundTransparency = if r.isTotal then 1 else 0, BorderSizePixel = 0, Size = UDim2.new(1, -6, 0, rowH or 30), LayoutOrder = i, ZIndex = z + 1 }, list)
		T.corner(row, 4)
		if not r.isTotal then new("Frame", { BackgroundColor3 = rarityColor(r.rarity), BorderSizePixel = 0, Position = UDim2.fromOffset(0, 0), Size = UDim2.new(0, 4, 1, 0), ZIndex = z + 2 }, row) end
		local n = txt(row, if r.isTotal then "TOTAL" else rarityName(r.rarity), 13, if r.isTotal then T.MUTED else T.TEXT, T.FONT_BOLD); n.ZIndex = z + 2
		n.Position = UDim2.fromOffset(14, 0); n.Size = UDim2.new(0.5, 0, 1, 0)
		local cnt = txt(row, if r.count then r.count .. " to get" else "", 12, T.MUTED, T.FONT, Enum.TextXAlignment.Right); cnt.ZIndex = z + 2
		cnt.Position = UDim2.new(0.35, 0, 0, 0); cnt.Size = UDim2.new(0.35, 0, 1, 0)
		local pct = r.pct or 0
		local p = txt(row, (if pct >= 1 then string.format("%.1f", pct) else string.format("%.2f", pct)) .. "%", 14, if r.isTotal then T.MUTED else T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Right); p.ZIndex = z + 2
		p.Position = UDim2.new(0.7, 0, 0, 0); p.Size = UDim2.new(0.3, -12, 1, 0)
	end
	return true
end
function ShopUI.odds(cid: string)
	local o = Shop.offer(cid)
	if not o then return end
	play("click")
	for _, c in UI.oddsList:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	UI.oddsTitle.Text = string.upper(o.name) .. "  ODDS"
	ShopUI.oddsRows(UI.oddsList, cid, 31)
	UI.oddsFoot.Text = "a rarity by these chances, then the gun is picked evenly, then an item for it. never one you already own, so the odds change as you collect."
	UI.odds.Visible = true
	ShopUI.layer()
end

-- CONFIRM: what you're about to get, before the till is asked. a container shows its odds here too
UI.confirm = new("Frame", { Name = "Confirm", BackgroundColor3 = T.BG, BackgroundTransparency = 0.02, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(460, 230), Visible = false, ZIndex = 40 }, UI.stage)
T.corner(UI.confirm, 8); T.edge(UI.confirm)
do
	UI.cTitle = txt(UI.confirm, "", 22, T.TEXT, T.FONT_TITLE); UI.cTitle.ZIndex = 41
	UI.cTitle.Position = UDim2.fromOffset(22, 18); UI.cTitle.Size = UDim2.new(1, -44, 0, 28)
	UI.cBody = txt(UI.confirm, "", 14, T.SOFT); UI.cBody.ZIndex = 41; UI.cBody.RichText = true
	UI.cBody.TextWrapped = true; UI.cBody.TextTruncate = Enum.TextTruncate.None; UI.cBody.TextYAlignment = Enum.TextYAlignment.Top
	UI.cBody.Position = UDim2.fromOffset(22, 56); UI.cBody.Size = UDim2.new(1, -44, 0, 44)
	UI.cOdds = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(22, 104), Size = UDim2.new(1, -44, 0, 0), ZIndex = 41 }, UI.confirm)
	new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, UI.cOdds)
	UI.cNo = button(UI.confirm, "CANCEL", "dark", UDim2.new(0.5, -27, 0, 44), UDim2.new(0, 22, 1, -62))
	UI.cNo.face.ZIndex = 41
	UI.cYes = button(UI.confirm, "CLAIM", "main", UDim2.new(0.5, -27, 0, 44), UDim2.new(0.5, 5, 1, -62))
	UI.cYes.face.ZIndex = 41
	UI.cNo.face.MouseButton1Click:Connect(function() ShopUI.unconfirm() end)
	UI.cYes.face.MouseButton1Click:Connect(function() ShopUI.commit() end)
end
function ShopUI.unconfirm()
	S.pending = nil
	UI.confirm.Visible = false
	ShopUI.layer()
end
-- step one of every buy: the confirm panel (with real Robux on, Roblox's own purchase prompt is the confirm instead)
function ShopUI.ask(id: string)
	local o = Shop.offer(id)
	if not o or S.busy then return end
	if o.type ~= "container" and Till.missing(o) == 0 then Hud.callout("ALREADY YOURS", 1); return end
	if o.type == "container" then
		local bs = Till.boxState(o.id)
		if bs == "soon" then Hud.callout("COMING SOON", 1); return end
		if bs == "empty" then Hud.callout("YOU HAVE EVERYTHING IN IT", 1.2); return end
		-- (where paid random items aren't allowed, a paid container isn't sold: PolicyService, the loot server's answer)
		if S.restricted and not Shop.free() then Hud.callout("NOT AVAILABLE WHERE YOU ARE", 1.2); return end
	end
	if not Shop.onSale(id) then Hud.callout("NOT ON SALE TODAY", 1); return end
	-- with real Robux on, Roblox's own prompt is the confirm for a fixed item. a container always comes here first:
	-- the odds of a paid random item must be on screen before anything is charged
	if not Shop.free() and Shop.ROBUX and o.type ~= "container" then ShopUI.prompt(o); return end
	play("click")
	S.pending = id
	-- (a container comes in x1 / x5 / x10: the card's pick)
	local n = if o.type == "container" then (S.count[o.id] or 1) else 1
	S.pendingN = n
	for _, c in UI.cOdds:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	local free = Shop.free()
	UI.cTitle.Text = (if free then "CLAIM " else "BUY ") .. (if n > 1 then n .. " " .. string.upper(o.name) .. "S" else string.upper(o.name)) .. "?"
	local h = if S.compact then 210 else 230
	local rh = if S.compact then 24 else 30
	local canGo = true
	if o.type == "container" then
		UI.cBody.Text = if n > 1 then n .. " " .. string.lower(o.name) .. "s, opened right away: each one item for one gun (picked evenly), never the same twice, at these odds:"
			else "one " .. string.lower(o.name) .. ", opened right away: one item for one gun (picked evenly), at these odds:"
		canGo = ShopUI.oddsRows(UI.cOdds, o.id, 41, rh) or free -- (never charge for a random item without its odds)
		local n = 0
		for _, c in UI.cOdds:GetChildren() do if c:IsA("GuiObject") then n += 1 end end
		UI.cOdds.Size = UDim2.new(1, -44, 0, n * (rh + 4))
		h += n * (rh + 4) + 8
	elseif o.type == "bundle" then
		local miss = Till.missing(o)
		UI.cBody.Text = string.format("%d item%s go%s into your inventory.", miss, if miss == 1 then "" else "s", if miss == 1 then "es" else "")
	else
		UI.cBody.Text = "this " .. string.lower(Shop.KIND_NAMES[o.kind] or "item") .. " goes into your inventory."
	end
	if free then UI.cBody.Text ..= string.format('<br/><font color="%s">free while we test. later: %s %s</font>', T.hex(T.MUTED), ROBUX, commas(o.robux * n)) end
	UI.cYes.set(if free then (if n > 1 then "CLAIM  x" .. n else "CLAIM") else "BUY  " .. ROBUX .. " " .. commas(o.robux * n), canGo)
	UI.confirm.Size = UDim2.fromOffset(460, h)
	UI.confirm.Visible = true
	ShopUI.layer()
end
-- step two: the till. a container is opened at once (the loot module plays the opening); the rest just lands
function ShopUI.commit()
	local id = S.pending
	local o = id and Shop.offer(id)
	local n = S.pendingN or 1
	if not UI.cYes.enabled then return end
	ShopUI.unconfirm()
	if not o or S.busy then return end
	if not Shop.free() and Shop.ROBUX then ShopUI.prompt(o); return end -- (a container, after its odds were shown)
	S.busy = true
	local res = if o.type == "container" and n > 1 then Till.ask("buy", id, n) else Till.ask("buy", id)
	S.busy = false
	if not res.ok then
		Hud.callout(string.upper(res.why or "the till said no"), 1.6)
		return
	end
	play("click")
	if o.type == "container" then
		Till.refresh()
		ShopUI.openBox(o.id, n)
		return
	end
	Till.refresh()
	ShopUI.toast(string.upper(if o.type == "single" then Shop.itemLabel({ kind = o.kind, id = o.item, weapon = o.weapon }) else o.name) .. " ADDED. WEAR IT FROM THE LOADOUT [L]")
	ShopUI.refill()
end

-- open a container you have: the till rolls it, the loot module's opening plays (the shop steps aside), then the
-- inventory shows what you got
-- (OPEN ANOTHER at the end of the opening: the next one from your stock, or a fresh free one while we test).
-- n = how many at once (1, 5 or 10): the loot server rolls them as one batch, the opening shows them all, and
-- OPEN ANOTHER opens the same number again
function ShopUI.openBox(cid: string, n: number?)
	if S.busy then return end
	S.busy = true
	local count = n or 1
	local mod = script.Parent:FindFirstChild("LootOpening")
	local Opening: any = nil
	if mod and mod:IsA("ModuleScript") then
		local ok, L = pcall(require, mod)
		if ok and type(L) == "table" and type((L :: any).play) == "function" then Opening = L end
	end
	local last: any = nil
	while true do
		local res = if count > 1 then Till.ask("open", cid, count) else Till.ask("open", cid)
		if not res.ok then Hud.callout(string.upper(res.why or "it won't open"), 1.6); break end
		last = res
		-- the shop steps aside (screen, blur and tint) while the opening plays (it takes the camera and the screen)
		gui.Enabled = false; back.Enabled = false
		UI.blur.Enabled = false; UI.tint.Enabled = false
		local how = "done"
		if Opening then
			local ok, out = pcall(Opening.play, cid, res, { again = true, n = count })
			how = if ok and type(out) == "string" then out else "done"
			if not ok then warn("[jankfire] shop: the opening broke: " .. tostring(out)) end
		else
			local it = res.item or res.prize
			if type(it) == "table" then Hud.callout(string.upper(it.name or Shop.itemInfo(it.kind or it.type, it.id)), 1.6) end
		end
		Till.refresh()
		if how ~= "again" or not S.open then break end
		-- another: from your stock, or claimed fresh while it's free
		if Till.count(cid) < count and not Shop.free() then break end
		if Till.boxState(cid) then break end
	end
	S.busy = false
	if S.open then
		gui.Enabled = true; back.Enabled = true
		UI.blur.Enabled = true; UI.tint.Enabled = true
		local it = last and (last.item or last.prize)
		local got = if last and type(last.items) == "table" then #last.items else 1
		if got > 1 then
			ShopUI.toast(got .. " THINGS ARE YOURS" .. (if last.short then " (ALL THAT WAS LEFT)" else "") .. ". WEAR THEM FROM THE LOADOUT [L]")
		elseif type(it) == "table" and it.id then
			local name = it.name or Shop.itemInfo(it.kind or it.type, it.id)
			if it.weapon then name ..= " · " .. Shop.weaponName(it.weapon) end
			ShopUI.toast(string.upper(name) .. " IS YOURS. WEAR IT FROM THE LOADOUT [L]")
		end
		S.invFilter = "all"
		ShopUI.shutOverlays()
		ShopUI.tab("inventory")
	end
end
-- the loot server says what you own changed (another screen, the opening's EQUIP, a receipt): refresh what's shown
for _, a in { "LootOwned", "LootStock" } do
	me:GetAttributeChangedSignal(a):Connect(function()
		if S.open and not S.busy then task.defer(function() Till.refresh(); ShopUI.refill() end) end
	end)
end

-- with real Robux on: the server checks the offer and shows Roblox's own purchase prompt; the receipt comes back
-- through ShopReceipts.server.luau, which has the loot server grant it
function ShopUI.prompt(o: any)
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("ShopBuy")
	if not Shop.ROBUX or not Shop.productFor(o) or not (r and r:IsA("RemoteEvent")) then Hud.callout("NOT FOR SALE YET", 1.2); return end
	(r :: RemoteEvent):FireServer(o.id)
end

-- with real Robux on, the prices shown are the developer products' own (Roblox can price a product differently by
-- region), read once; the catalog's `robux` numbers are only what to price the products at when making them
function ShopUI.livePrices()
	local MS = game:GetService("MarketplaceService")
	for key, pid in Shop.PRODUCTS do
		if type(pid) == "number" and pid > 0 then
			local ok, info = pcall(function() return MS:GetProductInfo(pid, Enum.InfoType.Product) end)
			local price = ok and type(info) == "table" and tonumber(info.PriceInRobux)
			if price then
				local o = Shop.byId[key]
				local kind, r = string.match(key, "^(%a+):(%a+)$")
				if o then o.robux = price
				elseif kind and (Shop.PRICE :: any)[kind] then (Shop.PRICE :: any)[kind][r] = price end
			end
		end
	end
	if S.open then ShopUI.refill() end
end

-- TOAST: one line low in the middle that fades
UI.toast = new("Frame", { Name = "Toast", BackgroundColor3 = T.BG, BackgroundTransparency = 0.05, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -24), Size = UDim2.fromOffset(520, 44), Visible = false, ZIndex = 50 }, UI.stage)
T.corner(UI.toast); T.edge(UI.toast, T.ACCENT, 0.4)
UI.toastTxt = txt(UI.toast, "", 15, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center); UI.toastTxt.Size = UDim2.fromScale(1, 1); UI.toastTxt.ZIndex = 51
function ShopUI.toast(text: string)
	UI.toastTxt.Text = text
	UI.toast.Size = UDim2.fromOffset(math.max(360, #text * 9 + 60), 44)
	UI.toast.Visible = true
	UI.toast.BackgroundTransparency = 0.05; UI.toastTxt.TextTransparency = 0
	local stamp = os.clock()
	S.toastAt = stamp
	task.delay(2.6, function()
		if S.toastAt ~= stamp then return end
		T.tween(UI.toast, 0.4, { BackgroundTransparency = 1 }); T.tween(UI.toastTxt, 0.4, { TextTransparency = 1 })
		task.delay(0.42, function() if S.toastAt == stamp then UI.toast.Visible = false end end)
	end)
end

-- ======================================================================== layout: the canvas fits any screen
-- a tall-enough screen is laid out 720 design pixels tall (wider screens just get more width); a short one (a phone
-- on its side, 375-430 points tall) 400 tall, so one design pixel is about one point there: the shop fills the whole
-- phone screen, words read at their design size and every button is at least 44 points (Apple's touch target)
function ShopUI.layout()
	local abs = if S.fake then S.fake else gui.AbsoluteSize
	if abs.X < 10 or abs.Y < 10 then return end
	local compact = abs.Y < 560
	local sc = if compact then math.min(abs.Y / 400, abs.X / 760) else math.min(abs.Y / 720, abs.X / 1180)
	sc = math.max(sc, 0.4)
	S.compact, S.scale = compact, sc
	local W, H = abs.X / sc, abs.Y / sc
	S.W, S.H = W, H
	UI.scale.Scale = sc
	UI.stage.Size = UDim2.fromOffset(W, H)
	-- the title row sits in Roblox's top bar, right of Roblox's own buttons (GuiService.TopbarInset is the bar's free
	-- stretch, in screen pixels; the gui's own top is at AbsolutePosition.Y + the gui inset)
	local ins = GuiService.TopbarInset
	local guiTop = gui.AbsolutePosition.Y + GuiService:GetGuiInset().Y
	local barL = if ins and ins.Height > 0 and guiTop < ins.Max.Y - 4 then ins.Min.X else 0
	if S.fake then barL = 120 end -- (a phone's Roblox buttons, roughly)
	local topY = if compact then 2 else 10
	local side = if compact then 12 else 32
	local topH = if compact then 48 else 78
	local topL = math.max(side, barL / sc + (if compact then 8 else 16))
	local topW = W - topL - side
	UI.top.Position = UDim2.fromOffset(topL, topY)
	UI.top.Size = UDim2.new(1, -(topL + side), 0, topH)
	-- the top row on a phone: title, tabs, the FREE pill, CLOSE, all 44 tall; where it's too narrow the pill goes, then
	-- the title (the tabs and CLOSE always stay)
	local tabW = if compact then 98 else 116
	local closeW = if compact then 84 else 112
	local walletW = if compact then 70 else 170
	local titleW = if compact then 78 else 190
	local tabsW = tabW * 4 + 18
	local showWallet = topW >= titleW + tabsW + walletW + closeW + 16
	local showTitle = topW >= titleW + tabsW + closeW + 8
	UI.title.Visible = showTitle; UI.rule.Visible = showTitle
	UI.title.TextSize = if compact then 22 else 34
	UI.title.Position = UDim2.fromOffset(0, 0); UI.title.Size = UDim2.fromOffset(160, if compact then 28 else 40)
	UI.rule.Position = UDim2.fromOffset(2, if compact then 31 else 44)
	UI.sub.Visible = not compact
	UI.sub.Position = UDim2.fromOffset(2, 54); UI.sub.Size = UDim2.fromOffset(420, 18)
	UI.tabRow.Position = UDim2.fromOffset(if showTitle then titleW else 0, 0)
	UI.tabRow.Size = UDim2.fromOffset(tabsW, 44)
	for _, b in UI.tabs do b.face.Size = UDim2.fromOffset(tabW, 44); b.face.TextSize = if compact then 14 else 15 end
	UI.close.face.AnchorPoint = Vector2.new(1, 0)
	UI.close.face.Position = UDim2.new(1, 0, 0, 0)
	UI.close.face.Size = UDim2.fromOffset(closeW, 44)
	UI.closeKey.Visible = (not UIS.TouchEnabled or UIS.KeyboardEnabled) and not compact
	UI.close.face.TextXAlignment = if UI.closeKey.Visible then Enum.TextXAlignment.Left else Enum.TextXAlignment.Center
	local cp = UI.close.face:FindFirstChildOfClass("UIPadding")
	if cp then cp.PaddingLeft = UDim.new(0, if UI.closeKey.Visible then 14 else 0) end
	UI.wallet.Visible = showWallet
	UI.wallet.AnchorPoint = Vector2.new(1, 0)
	UI.wallet.Position = UDim2.new(1, -(closeW + 8), 0, 0)
	UI.wallet.Size = UDim2.fromOffset(walletW, 44)
	-- the body
	local by = topY + topH + (if compact then 4 else 6)
	local bottom = if compact then 8 else 24
	UI.body.Position = UDim2.fromOffset(side, by)
	UI.body.Size = UDim2.new(1, -2 * side, 1, -(by + bottom))
	local bw, bh = W - 2 * side, H - by - bottom
	-- featured: hero on the left, the daily grid on the right
	local heroW = math.floor(bw * (if compact then 0.46 else 0.48))
	local gap = if compact then 10 else 14
	UI.hero.Size = UDim2.new(0, heroW, 1, 0)
	UI.daily.Position = UDim2.fromOffset(heroW + gap, 0)
	UI.daily.Size = UDim2.new(1, -(heroW + gap), 1, 0)
	UI.dailyLayout.CellPadding = UDim2.fromOffset(gap, gap)
	UI.dailyLayout.CellSize = UDim2.new(1 / 3, -math.ceil(gap * 2 / 3), 0.5, -math.ceil(gap / 2))
	UI.dailyGrid.Position = UDim2.fromOffset(0, if compact then 26 else 30)
	UI.dailyGrid.Size = UDim2.new(1, 0, 1, -(if compact then 26 else 30))
	UI.heroEyebrow.Position = UDim2.fromOffset(if compact then 14 else 20, if compact then 12 else 18)
	UI.heroTimer.Position = UDim2.new(0, if compact then 14 else 20, 0, if compact then 12 else 18)
	UI.heroName.Position = UDim2.fromOffset(if compact then 14 else 20, if compact then 28 else 36)
	UI.heroName.TextSize = if compact then 22 else 34
	UI.heroBlurb.Visible = not compact
	local strip = if compact then 60 else 74
	UI.heroStrip.Size = UDim2.new(1, 0, 0, strip)
	-- the preview between the words on top and the strip at the bottom
	local hy = if compact then 58 else 100
	UI.heroView.Position = UDim2.fromOffset(0, hy)
	UI.heroView.Size = UDim2.new(1, 0, 1, -(hy + strip))
	UI.heroBtn.face.Size = UDim2.fromOffset(if compact then 128 else 180, if compact then 44 else 46)
	UI.heroBtn.face.Position = UDim2.new(1, -(if compact then 138 else 196), 0.5, -(if compact then 22 else 23))
	UI.heroBtn.face.TextSize = if compact then 14 else 15
	UI.heroChips.Position = UDim2.fromOffset(if compact then 10 else 16, 0)
	UI.heroChips.Size = UDim2.new(1, -(if compact then 150 else 220), 1, 0)
	-- bundles: as many columns as fit cards ~340 wide (~270 on a phone)
	local cols = math.max(2, math.floor((bw + 14) / (if compact then 270 else 360)))
	local cw = math.floor((bw - 8 - (cols - 1) * 14) / cols)
	UI.bundleLayout.CellSize = UDim2.fromOffset(cw, math.floor(math.min(cw * 0.82, if compact then bh - 4 else 340)))
	-- inventory: small cards in each weapon's grid
	local icols = math.max(3, math.floor((bw + 10) / (if compact then 150 else 180)))
	local iw = math.floor((bw - 16 - (icols - 1) * 10) / icols)
	S.invCell = UDim2.fromOffset(iw, math.floor(iw * 1.12))
	for _, g in UI.invScroll:GetDescendants() do if g:IsA("UIGridLayout") then g.CellSize = S.invCell end end
	for _, b in UI.invBtns do b.face.Size = UDim2.fromOffset(if compact then 104 else 120, if compact then 44 else 40); b.face.TextSize = if compact then 14 else 13 end
	UI.invFilters.Size = UDim2.new(1, 0, 0, if compact then 44 else 40)
	UI.invCount.Size = UDim2.new(1, 0, 0, if compact then 44 else 40)
	UI.invScroll.Position = UDim2.fromOffset(0, if compact then 52 else 52)
	UI.invScroll.Size = UDim2.new(1, 0, 1, -52)
	-- the overlays: inspect fills the body on a phone
	local iw2, ih2 = math.min(bw, 1100), math.min(bh, 600)
	UI.dim.Size = UDim2.fromScale(1, 1)
	UI.insp.AnchorPoint = Vector2.new(0.5, 0)
	UI.insp.Position = UDim2.new(0.5, 0, 0, by)
	UI.insp.Size = UDim2.fromOffset(iw2, ih2)
	local ipad = if compact then 10 else 14
	local split = if compact then 0.5 else 0.58
	UI.inspView.Position = UDim2.fromOffset(ipad, ipad)
	UI.inspView.Size = UDim2.new(split, -ipad, 1, -2 * ipad)
	UI.inspSide.Position = UDim2.new(split, ipad, 0, ipad)
	UI.inspSide.Size = UDim2.new(1 - split, -2 * ipad, 1, -2 * ipad)
	UI.inspBack.face.Size = UDim2.fromOffset(if compact then 96 else 90, if compact then 44 else 38)
	UI.inspName.TextSize = if compact then 22 else 30
	UI.odds.Size = UDim2.fromOffset(if compact then 420 else 440, math.min(H - 16, 380))
	UI.oddsOk.face.Size = UDim2.new(1, -44, 0, 44); UI.oddsOk.face.Position = UDim2.new(0, 22, 1, -56)
	UI.oddsFoot.Position = UDim2.new(0, 22, 1, -90)
end
function ShopUI.wallet()
	UI.walletTxt.Text = if Shop.free() then string.format('%s  <font color="%s">FREE FOR NOW</font>', ROBUX, T.hex(T.ACCENT))
		else ROBUX .. "  ROBUX"
	if S.compact and Shop.free() then UI.walletTxt.Text = string.format('<font color="%s">FREE</font>', T.hex(T.ACCENT)) end
end

-- ======================================================================== tabs, refills, open / close
function ShopUI.tab(t: string)
	if not UI.pages[t] then return end
	if S.tab ~= t then play("click"); ShopUI.shutOverlays() end -- (a new tab: whatever panel was up goes)
	S.tab = t
	for k, b in UI.tabs do b.pick(k == t) end
	for k, p in UI.pages do p.Visible = k == t end
	if t == "featured" then ShopUI.fillFeatured()
	elseif t == "bundles" then ShopUI.fillBundles()
	elseif t == "containers" then ShopUI.fillContainers()
	elseif t == "inventory" then ShopUI.fillInventory() end
end
function ShopUI.refill()
	ShopUI.wallet()
	ShopUI.tab(S.tab)
	if S.inspect then ShopUI.fillInspect() end
end

function ShopUI.canOpen(): (boolean, string?)
	if me:GetAttribute("Zone") == "match" then return false, "NO SHOPPING MID-MATCH" end
	if ShopUI.loadoutUp() then return false, nil end
	return true, nil
end
-- the loadout screen is up (its ScreenGui is on)
function ShopUI.loadoutUp(): boolean
	local g = pg:FindFirstChild("JankLoadout")
	return g ~= nil and g:IsA("ScreenGui") and g.Enabled
end
-- while the shop is up it also raises LoadoutOpen: every script that holds still while a menu is up (no jumping,
-- shooting or items, the mouse arrow on: Move, Arsenal, Utility, ShredderSlot, JankSettings) reads that one flag
local controls: any = nil
task.spawn(function()
	pcall(function() controls = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls() end)
end)
local function hold(on: boolean)
	if on then
		me:SetAttribute("LoadoutOpen", true)
		if controls then pcall(function() controls:Disable() end) end
	else
		if not ShopUI.loadoutUp() then me:SetAttribute("LoadoutOpen", false) end
		if controls and not ShopUI.loadoutUp() then pcall(function() controls:Enable() end) end
	end
end
-- the loadout opened over the shop and then closed: it clears the flag; the shop is still up, so raise it again
me:GetAttributeChangedSignal("LoadoutOpen"):Connect(function()
	if S.open and not me:GetAttribute("LoadoutOpen") then task.defer(function() if S.open then hold(true) end end) end
end)

-- open the shop, on a tab (featured / bundles / containers / inventory), and on an offer's inspect panel if given.
-- what the hub's holograms call: ShopUI.open("bundles", "bundle_nightshift")
function ShopUI.open(tab: string?, id: string?)
	local ok, why = ShopUI.canOpen()
	if not ok then if why then Hud.callout(why, 1.2) end; return end
	if id and not tab then
		local o = Shop.offer(id)
		tab = if o and o.type == "container" then "containers" elseif o and o.type == "bundle" then "bundles" else "featured"
	end
	if not S.open then
		S.open = true
		me:SetAttribute("ShopOpen", true)
		hold(true)
		UI.sub.Text = LINES[math.random(#LINES)]
		table.clear(S.hidden)
		for _, g in pg:GetChildren() do
			if g:IsA("ScreenGui") and g ~= gui and g ~= back and g.Enabled and g.Name ~= "JankShopButton" then S.hidden[g] = true; g.Enabled = false end
		end
		local cam = workspace.CurrentCamera
		UI.blur.Parent = cam; UI.tint.Parent = cam
		UI.blur.Enabled = true; UI.tint.Enabled = true
		T.tween(UI.blur, 0.35, { Size = 20 })
		T.tween(UI.tint, 0.35, { Brightness = -0.06, Saturation = -0.7 })
		back.Enabled = true; gui.Enabled = true
		UI.catcher.BackgroundTransparency = 1
		T.tween(UI.catcher, 0.3, { BackgroundTransparency = 0.2 })
		ShopUI.layout()
		UI.stage.Position = UDim2.fromOffset(0, 14)
		T.tween(UI.stage, 0.22, { Position = UDim2.fromOffset(0, 0) })
		play("click")
		Till.refresh()
		ShopUI.wallet()
		if Shop.ROBUX and not S.priced then S.priced = true; task.spawn(ShopUI.livePrices) end
	end
	ShopUI.shutOverlays() -- (opened on something new: a hologram, the key on an open shop's tab)
	ShopUI.tab(tab or S.tab or "featured")
	if id then ShopUI.inspect(id) end
end
function ShopUI.close()
	if not S.open then return end
	S.open = false
	me:SetAttribute("ShopOpen", false)
	hold(false)
	S.inspect, S.pending = nil, nil
	UI.insp.Visible = false; UI.odds.Visible = false; UI.confirm.Visible = false; UI.dim.Visible = false
	gui.Enabled = false; back.Enabled = false
	for g in S.hidden do if g.Parent then g.Enabled = true end end
	table.clear(S.hidden)
	T.tween(UI.blur, 0.25, { Size = 0 })
	T.tween(UI.tint, 0.25, { Brightness = 0, Saturation = 0 })
	task.delay(0.27, function() if not S.open then UI.blur.Enabled = false; UI.tint.Enabled = false end end)
	-- the previews go with the screen (they're rebuilt on the next open)
	for _, p in UI.pages do for _, d in p:GetDescendants() do if d:IsA("ViewportFrame") then d:Destroy() end end end
	table.clear(spins)
	play("click")
end
function ShopUI.isOpen(): boolean return S.open end
-- a test: lay the shop out in a box the size of a phone's screen (points, e.g. Vector2.new(844, 390)) in the middle
-- of the window, with a hairline round it. nil = back to the whole window
function ShopUI.fakeScreen(size: Vector2?)
	S.fake = size
	UI.screen.Size = if size then UDim2.fromOffset(size.X, size.Y) else UDim2.fromScale(1, 1)
	UI.screen.ClipsDescendants = size ~= nil
	local st = UI.screen:FindFirstChildOfClass("UIStroke")
	if size and not st then T.edge(UI.screen, T.ACCENT, 0.2, 2) elseif not size and st then st:Destroy() end
	if S.open then ShopUI.layout(); ShopUI.refill() end
end
function ShopUI.toggle()
	if ShopUI.loadoutUp() then return end -- (the loadout is on top: it goes first)
	if S.open then ShopUI.close() else ShopUI.open() end
end
-- another screen that hid ours while it was up turns ours back on when it goes: only if the shop is still open
for _, g in { gui, back } do
	g:GetPropertyChangedSignal("Enabled"):Connect(function()
		if g.Enabled and not S.open then g.Enabled = false end
	end)
end

-- the timers tick once a second while it's up
task.spawn(function()
	while true do
		task.wait(1)
		if S.open then
			local left = clock(Shop.secondsLeft())
			UI.heroTimer.Text = "NEW IN " .. left
			UI.dailyTimer.Text = "NEW IN " .. left
			if Shop.secondsLeft() <= 1 then task.delay(2, function() if S.open then ShopUI.refill() end end) end
		end
	end
end)
gui:GetPropertyChangedSignal("AbsoluteSize"):Connect(function() if S.open then ShopUI.layout() end end)
-- a match grabbing you, a death: the shop shuts
me:GetAttributeChangedSignal("Zone"):Connect(function() if me:GetAttribute("Zone") == "match" then ShopUI.close() end end)

ShopUI.S = S
ShopUI.UI = UI
ShopUI.Till = Till
return ShopUI
