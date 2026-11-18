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
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
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
local TABS = { "featured", "deals", "bundles", "containers", "weapons", "coins", "inventory" }
local TAB_NAMES = { featured = "FEATURED", deals = "DEALS", bundles = "BUNDLES", containers = "CONTAINERS", weapons = "WEAPONS", coins = "COINS", inventory = "INVENTORY" }
local LINE = "Free while we test. The prices are for later."

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
	if r == "vip" then return Shop.VIP_COLOR end
	local e = Shop.RARITY[r]
	return if e then e.color else T.MUTED
end
local function rarityName(r: string): string
	local e = Shop.RARITY[r]
	return string.upper(if e then e.name else r)
end
-- VIP (the server's Vip.luau decides; the player attribute VIP is its word for the screen)
local function isVip(): boolean return me:GetAttribute("VIP") == true end

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
	inv.skin = {}; inv.border = {}; inv.banner = {}; inv.title = {}; inv.kill = {}; inv.emote = {}
	set("wrap", src.wrap or src.wraps or src.finish)
	set("hat", src.hat or src.hats)
	set("skin", src.skin or src.skins)
	-- the player card's looks, the kill effects and the emotes: bare ids
	for _, k in { "border", "banner", "title", "kill", "emote" } do set(k, src[k] or (type(raw) == "table" and raw.owned and raw.owned[k])) end
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
	-- (a VIP wrap or hat is worn on every gun: owned on one gun is owned)
	if (kind == "wrap" or kind == "hat") and Shop.vipOnly(kind, id) then
		for k in set do if Shop.unkey(k) == id then return true end end
		return false
	end
	return weapon ~= nil and set[Shop.key(kind, id, weapon)] == true
end
function Till.count(cid: string): number return S.inv.containers[cid] or 0 end
-- what you own as the loot module's odds want it ({ wrap = { [id] = true }, hat = ..., skin = ... })
function Till.ownedSets(): any
	local o = { wrap = S.inv.wrap, hat = S.inv.hat, skin = S.inv.skin or {} }
	-- (the Duffel Bag's gun-less things too, so its odds count what you have of them)
	for _, k in { "border", "banner", "title", "kill", "emote" } do if S.inv[k] then o[k] = S.inv[k] end end
	return o
end
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
-- what a bundle costs you now: a skin set you have some of costs only the share you're missing (Shop.setPrice)
local function bundlePrice(o: any, miss: number): number
	return if o.set then Shop.setPrice(o, miss) else o.robux
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
-- card, where a true-size hat is a few pixels). skin = a weapon skin's id: its body instead of the plain gun's
function V.gun(wid: string, wrap: string?, hat: string?, boost: number?, skin: string?): Model?
	-- (a gadget, 18 Nov: its own model or its skin's, GunPreview's; wraps yes, hats no)
	local re = Roster.byId[wid]
	if re and re.slot == "utility" then
		local okG, GP = pcall(require, script.Parent:WaitForChild("GunPreview"))
		local g = if okG and type(GP) == "table" then (GP :: any).itemModel(wid, skin) else nil
		if not g then return nil end
		settle(g)
		if wrap and wrap ~= "default" then pcall(WeaponModels.wrap, g, wrap, "full") end
		return g
	end
	local m = if skin then WeaponModels.build(wid, 3, skin) else nil
	if not m then m = if wid == "shredder" then V.shredder() else WeaponModels.build(wid, 3) end
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
	if Shop.isCard(it.kind) or Shop.isFlair(it.kind) then return nil end -- (no gun: drawn as tiles, V.put)
	if it.kind == "skin" then
		local sw = it.weapon or Shop.skinWeapon(it.id)
		return if sw then V.gun(sw, nil, nil, nil, it.id) else nil
	end
	local w = it.weapon or V.yourGun()
	if it.kind == "hat" then return V.gun(w, nil, it.id, boost) end
	return V.gun(w, it.id, nil)
end
-- the model for any offer (a bundle shows its hero, or one of its items; a single its item on its weapon)
function V.offerModel(o: any, item: any?, boost: number?): Model?
	if o.type == "container" then return V.container(o.id) end
	if item then return V.item(item, boost) end
	if o.type == "pass" then
		local h = Shop.vipHero()
		return if h then V.gun(h.weapon, h.wrap, h.hat, boost, h.skin) else nil
	end
	if o.type == "bundle" then
		local h = o.hero or {}
		return V.gun(h.weapon or "ar", h.wrap, h.hat, boost, h.skin)
	end
	return V.item({ kind = o.kind, id = o.item, weapon = o.weapon }, boost)
end

-- the player card's looks have no 3D model: a card-shaped tile drawn by CardStyles (its own frames and gradients)
local function clearPreview(parent: Instance)
	local old = parent:FindFirstChild("Preview")
	if old then
		for i = #spins, 1, -1 do if spins[i].vp == old then table.remove(spins, i) end end
		old:Destroy()
	end
end
local function cardFrame(parent: GuiObject): Frame
	clearPreview(parent)
	local holder = new("Frame", { Name = "Preview", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = parent.ZIndex + 1 }, parent)
	-- (a size before drawing: CardStyles reads AbsoluteSize, and redraws when it changes)
	local f = new("Frame", { Name = "Card", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromScale(0.86, 0.8), ZIndex = parent.ZIndex + 2 }, holder)
	new("UIAspectRatioConstraint", { AspectRatio = 2.4 }, f)
	return f
end
function V.card(parent: GuiObject, kind: string, id: string)
	local CS = Shop.CardStyles :: any
	local f = cardFrame(parent)
	if CS then pcall(CS.preview, kind, id, f) end
end
-- a kill effect or an emote: no 3D model either, a square tile drawn by Flair (a figure in the effect's colour, or
-- doing the move). anim: a looping preview over it (FlairAnim: the effect's flipbook, or you doing the emote), for
-- cards and the inspect panel; a small chip in a list stays still
function V.flair(parent: GuiObject, kind: string, id: string, anim: boolean?)
	local F = Shop.Flair :: any
	clearPreview(parent)
	local holder = new("Frame", { Name = "Preview", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = parent.ZIndex + 1 }, parent)
	local f = new("Frame", { Name = "Tile", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromScale(0.92, 0.92), ZIndex = parent.ZIndex + 2 }, holder)
	new("UIAspectRatioConstraint", { AspectRatio = 1 }, f)
	if F and type(F.picture) == "function" then pcall(F.picture, kind, id, f) end
	if anim then
		local m = script.Parent:FindFirstChild("FlairAnim")
		local ok, FA = false, nil
		if m and m:IsA("ModuleScript") then ok, FA = pcall(require, m) end
		if ok and type(FA) == "table" and type((FA :: any).attach) == "function" then pcall((FA :: any).attach, f, kind, id) end
	end
end
-- a whole card dressed in a set's background, border and title (the Head Office bundle's picture)
function V.cardSet(parent: GuiObject, items: { any })
	local CS = Shop.CardStyles :: any
	local f = cardFrame(parent)
	if not CS then return end
	local pick = {}
	for _, it in items do if Shop.isCard(it.kind) then pick[it.kind] = it.id end end
	pcall(CS.paintBanner, f, pick.banner or "slate", 6)
	pcall(CS.paintBorder, f, pick.border or "hairline", 6)
	if pick.title then
		local ok, words = pcall(CS.titleText, pick.title)
		local okc, col = pcall(CS.titleColor, pick.title)
		local l = new("TextLabel", { Name = "Title", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
			Size = UDim2.new(1, -24, 0.4, 0), ZIndex = f.ZIndex + 4, Text = if ok then words else "", TextColor3 = if okc then col else T.TEXT,
			TextScaled = true, FontFace = T.FONT_BOLD }, f)
		new("UITextSizeConstraint", { MaxTextSize = 28 }, l)
	end
end
-- what a single is for, in words: "FOR SMG", "FOR YOUR PLAYER CARD" ("FOR YOUR CARD" short), "FOR EVERY KILL" (a kill
-- effect plays on every kill, any gun), "FOR YOUR EMOTE WHEEL"
function V.forWords(kind: string, weapon: string?, short: boolean?): string
	if Shop.isCard(kind) then return if short then "FOR YOUR CARD" else "FOR YOUR PLAYER CARD" end
	if kind == "kill" then return "FOR EVERY KILL" end
	if kind == "emote" then return "FOR YOUR EMOTE WHEEL" end
	return "FOR " .. string.upper(Shop.weaponName(weapon))
end
-- FINISHERS (the finishers session's, roblox/docs/FINISHERS.md: a short cinematic when a high-tier skin that owns one
-- lands a round's or the match's winning kill). Shared.Finishers.forSkin(skinId) -> id, row { name, colour }; the
-- client's Finisher.preview(id, { skin = skinId }) plays the full cut in front of you, taking the camera and the screen,
-- and gives both back. a skin with one gets a FINISHER pill on its cards, and PREVIEW FINISHER in its inspect panel
local Fin = {}
function Fin.of(skin: string?): (string?, any)
	if type(skin) ~= "string" then return nil, nil end
	local m = Shared:FindFirstChild("Finishers")
	if not (m and m:IsA("ModuleScript")) then return nil, nil end
	local ok, F = pcall(require, m)
	if not ok or type(F) ~= "table" or type((F :: any).forSkin) ~= "function" then return nil, nil end
	local ok2, id, row = pcall((F :: any).forSkin, skin)
	if not ok2 or type(id) ~= "string" then return nil, nil end
	return id, row
end
-- the pill, in the finisher's own colour (anchored by its top-right corner at `pos`)
function Fin.badge(parent: Instance, skin: string?, pos: UDim2, z: number?): Frame?
	local id, row = Fin.of(skin)
	if not id then return nil end
	local col = if type(row) == "table" and typeof(row.colour) == "Color3" then row.colour else T.ACCENT
	local zz = z or 6
	local f = new("Frame", { Name = "Finisher", BackgroundColor3 = T.BG, BackgroundTransparency = 0.1, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0),
		Position = pos, Size = UDim2.fromOffset(0, 22), AutomaticSize = Enum.AutomaticSize.X, ZIndex = zz }, parent)
	T.corner(f, 4)
	T.edge(f, col, 0.35)
	new("UIPadding", { PaddingLeft = UDim.new(0, 8), PaddingRight = UDim.new(0, 8) }, f)
	local l = txt(f, "FINISHER", 11, col, T.FONT_BOLD, Enum.TextXAlignment.Center)
	l.AutomaticSize = Enum.AutomaticSize.X; l.Size = UDim2.fromOffset(0, 22); l.ZIndex = zz + 1; l.TextTruncate = Enum.TextTruncate.None
	return f
end
function Fin.preview(skin: string?)
	local id = Fin.of(skin)
	local m = script.Parent:FindFirstChild("Finisher")
	if not id or not (m and m:IsA("ModuleScript")) then return end
	local ok, F = pcall(require, m)
	if ok and type(F) == "table" and type((F :: any).preview) == "function" then
		play("click")
		-- (the shop's blur and grey tint would sit over the cut: off while it plays, back after if the shop is still up)
		UI.blur.Enabled = false; UI.tint.Enabled = false
		task.spawn(function()
			pcall((F :: any).preview, id, { skin = skin })
			local t0 = os.clock()
			repeat task.wait(0.1) until os.clock() - t0 > 10 or type((F :: any).isPlaying) ~= "function" or not (F :: any).isPlaying()
			if S.open then UI.blur.Enabled = true; UI.tint.Enabled = true end
		end)
	end
end
-- a kill effect played for real on a copy of you (FlairAnim.showcase), the shop's blur and tint off while it plays
function Fin.showcase(id: string)
	local m = script.Parent:FindFirstChild("FlairAnim")
	if not (m and m:IsA("ModuleScript")) then return end
	local ok, FA = pcall(require, m)
	if not ok or type(FA) ~= "table" or type((FA :: any).showcase) ~= "function" then return end
	if type((FA :: any).isShowing) == "function" and (FA :: any).isShowing() then return end
	play("click")
	UI.blur.Enabled = false; UI.tint.Enabled = false
	task.spawn(function()
		pcall((FA :: any).showcase, id)
		if S.open then UI.blur.Enabled = true; UI.tint.Enabled = true end
	end)
end
-- a small still picture of one item (a chip in a list or a strip): a hat on its own, a skin's whole gun, a card tile
function V.chip(parent: GuiObject, it: any)
	if Shop.isCard(it.kind) then V.card(parent, it.kind, it.id)
	elseif Shop.isFlair(it.kind) then V.flair(parent, it.kind, it.id)
	elseif it.kind == "skin" then V.show(parent, V.item(it), "none", 1.0)
	else V.show(parent, V.hat(it.id), "none", 1.1) end
end
-- show any offer or item in a frame: a card look as a 2D tile, a card set as a whole card, everything else in 3D
function V.put(parent: GuiObject, o: any?, item: any?, spin: string, zoom: number?, boost: number?)
	local it = item or (if o and o.type == "single" then { kind = o.kind, id = o.item, weapon = o.weapon } else nil)
	if it and Shop.isCard(it.kind) then V.card(parent, it.kind, it.id); return end
	if it and Shop.isFlair(it.kind) then V.flair(parent, it.kind, it.id, true); return end
	if o and o.type == "bundle" and not o.hero then V.cardSet(parent, o.items); return end
	V.show(parent, if o then V.offerModel(o, item, boost) else V.item(it, boost), spin, zoom)
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
UI.sub = txt(UI.top, LINE, 14, T.MUTED)
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

-- the quests' wallet (the quests session's Brass and Crate Tickets, roblox/docs/QUESTS.md section 6): the player
-- attributes Brass and CrateTickets, which its server keeps. shown in the header (under the pill on a computer, in its
-- place on a phone), with its icons (QuestUI.icon, drawn from frames). a container can be redeemed with them
-- (Shop.redeemPrice; JankfireRemotes.Quests "redeem" puts one in stock, then it opens as usual)
local Purse = {}
function Purse.has(): boolean return me:GetAttribute("Brass") ~= nil or me:GetAttribute("CrateTickets") ~= nil end
function Purse.of(cur: string): number return tonumber(me:GetAttribute(if cur == "tix" then "CrateTickets" else "Brass")) or 0 end
function Purse.remote(): RemoteFunction?
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("Quests")
	return if r and r:IsA("RemoteFunction") then r else nil
end
-- a container can be redeemed here: it has a price in tickets or Brass and the quests server is up
function Purse.price(cid: string): { tix: number?, brass: number? }?
	if not Purse.remote() or not Purse.has() then return nil end
	local p = Shop.redeemPrice(cid)
	-- (where Roblox's policy keeps a player from paid random items, coins don't redeem a container: coins can be bought
	-- with Robux. tickets are only ever earned, so they still do. the server refuses it too: Quests "redeem". 18 Nov)
	if p and (S.restricted or (Shop.coinsOnly() and not Shop.free())) then p = if p.tix then { tix = p.tix } else nil end -- (coins-only: BUY is the coins)
	return p
end
-- "12 TICKETS" / "1 TICKET" / "2,500 COINS" (Brass in the code is Coins on screen, 18 Nov)
function Purse.words(cur: string, n: number): string
	if cur == "tix" then return commas(n) .. (if n == 1 then " TICKET" else " TICKETS") end
	return commas(n) .. (if n == 1 then " COIN" else " COINS")
end
-- the coins-only shop (Shop.coinsOnly, 18 Nov): what an offer costs in coins (n containers), or nil when it's Robux
function Purse.coins(o: any, n: number?): number?
	if not o or Shop.free() or not Shop.coinsOnly() then return nil end
	return Shop.coinPrice(o, n)
end
-- what an offer costs, in words: coins in the coins-only shop, else Robux
function Purse.cost(o: any, n: number?): string
	local c = Purse.coins(o, n)
	if c then return Purse.words("brass", c) end
	return priceText((o.robux or 0) * (n or 1))
end
-- the quests' icon for "brass" / "tix" in a frame (false: QuestUI isn't there, the words say it instead)
function Purse.icon(kind: string, parent: GuiObject, size: number): boolean
	local m = script.Parent:FindFirstChild("QuestUI")
	if not (m and m:IsA("ModuleScript")) then return false end
	local ok, Q = pcall(require, m)
	if not ok or type(Q) ~= "table" or type((Q :: any).icon) ~= "function" then return false end
	return (pcall((Q :: any).icon, kind, parent, size))
end
function Purse.draw()
	if not UI.purse then
		UI.purse = new("Frame", { Name = "Purse", BackgroundColor3 = T.BG, BackgroundTransparency = 1, BorderSizePixel = 0, AutomaticSize = Enum.AutomaticSize.X,
			Size = UDim2.fromOffset(0, 22), Visible = false }, UI.top)
		T.corner(UI.purse)
		UI.purseEdge = T.edge(UI.purse)
		new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 5), VerticalAlignment = Enum.VerticalAlignment.Center,
			SortOrder = Enum.SortOrder.LayoutOrder }, UI.purse)
		UI.pursePad = new("UIPadding", {}, UI.purse)
		UI.purseBits = {}
		for i, cur in { "brass", "tix" } do
			if i == 2 then new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromOffset(6, 1), LayoutOrder = 2 }, UI.purse) end
			local ic = new("Frame", { Name = cur, BackgroundTransparency = 1, Size = UDim2.fromOffset(18, 18), LayoutOrder = i * 3 - 2 }, UI.purse)
			local drawn = Purse.icon(cur, ic, 18)
			ic.Visible = drawn
			local l = txt(UI.purse, "", 14, T.TEXT, T.FONT_BOLD)
			l.TextTruncate = Enum.TextTruncate.None; l.AutomaticSize = Enum.AutomaticSize.X
			l.Size = UDim2.fromOffset(0, 22); l.LayoutOrder = i * 3 - 1
			UI.purseBits[cur] = { label = l, drawn = drawn }
		end
	end
	for cur, b in UI.purseBits do
		local n = Purse.of(cur)
		b.label.Text = if b.drawn then commas(n) else Purse.words(cur, n)
	end
end
-- its width on a phone's top row (a guess before it's drawn: the numbers' lengths)
function Purse.width(): number
	if UI.purse and UI.purse.AbsoluteSize.X > 4 then return UI.purse.AbsoluteSize.X / S.scale end
	return 150
end

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
	V.put(view, o, nil, "hover", 1.08, if o.kind == "hat" then 1.6 else nil)
	local name = txt(c, o.name, 16, T.TEXT, T.FONT_BOLD)
	name.Position = UDim2.new(0, 12, 1, -74); name.Size = UDim2.new(1, -24, 0, 20)
	-- the weapon it's for: a wrap or a hat is owned for one weapon
	local wl = txt(c, V.forWords(o.kind, o.weapon), 12, T.SOFT, T.FONT_BOLD)
	wl.Position = UDim2.new(0, 12, 1, -53); wl.Size = UDim2.new(1, -24, 0, 15)
	-- (on a phone the kind word goes: the rarity alone fits beside the price)
	local rl = rarityLine(c, o.rarity, Shop.KIND_NAMES[o.kind] or o.kind, if S.compact then 12 else 11, S.compact)
	rl.Position = UDim2.new(0, 12, 1, -32); rl.Size = UDim2.new(1, -96, 0, 15)
	local owned = Till.owns(o.kind, o.item, o.weapon)
	local pr = txt(c, if owned then "OWNED" else (if Shop.free() then "FREE" else Purse.cost(o)), 14, if owned then T.MUTED else T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Right)
	pr.RichText = true
	local wide = Purse.coins(o) ~= nil -- (a coin price is longer: "1,200 COINS")
	pr.Position = UDim2.new(1, if wide then -122 else -92, 1, -33); pr.Size = UDim2.new(0, if wide then 110 else 80, 0, 16)
	if owned then
		local tag = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.15, BorderSizePixel = 0, Position = UDim2.fromOffset(8, 8), Size = UDim2.fromOffset(64, 22), ZIndex = 5 }, c)
		T.corner(tag, 4)
		local l = txt(tag, "OWNED", 11, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center); l.Size = UDim2.fromScale(1, 1); l.ZIndex = 6
	end
	if o.kind == "skin" then Fin.badge(c, o.item, UDim2.new(1, -8, 0, 8)) end
	c.MouseButton1Click:Connect(function() ShopUI.inspect(o.id) end)
	return c
end
-- a bundle: the hero preview, the name, how many items, the price
local function bundleCard(parent: Instance, o: any, order: number): TextButton
	local c = card(parent, o.rarity)
	c.LayoutOrder = order
	local view = new("Frame", { Name = "View", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 26), Size = UDim2.new(1, 0, 1, -100) }, c)
	V.put(view, o, nil, "hover", 1.08)
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
		V.chip(view, it)
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
		V.put(UI.heroView, o, nil, "slow", 1.08)
		for _, c in UI.heroChips:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
		for i, it in o.items do itemChip(UI.heroChips, it, i) end
		local miss = Till.missing(o)
		UI.heroEyebrow.Text = if o.set then "FEATURED SKIN SET" else "FEATURED BUNDLE"
		local pr = bundlePrice(o, miss)
		UI.heroBtn.set(if miss == 0 then "OWNED" elseif Shop.free() then "CLAIM  " .. priceText(pr) else priceText(pr), miss ~= 0)
	end
	for _, c in UI.dailyGrid:GetChildren() do if c:IsA("GuiButton") then c:Destroy() end end
	for i, id in rot.daily do
		local so = Shop.offer(id)
		if so then singleCard(UI.dailyGrid, so, i) end
	end
end

-- ------------------------------------------------------------------------ BUNDLES: the skin sets' banners, then every bundle in a grid
do
	local pg_ = UI.pages.bundles
	UI.bundleScroll = new("ScrollingFrame", {
		BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y,
		ScrollBarThickness = 4, ScrollBarImageColor3 = T.MUTED, ScrollingDirection = Enum.ScrollingDirection.Y,
	}, pg_)
	new("UIListLayout", { Padding = UDim.new(0, 10), SortOrder = Enum.SortOrder.LayoutOrder }, UI.bundleScroll)
	new("UIPadding", { PaddingRight = UDim.new(0, 8), PaddingBottom = UDim.new(0, 8) }, UI.bundleScroll)
	-- VIP first: one wide tile (ShopUI.fillVip)
	UI.vipHolder = new("Frame", { Name = "Vip", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 230), LayoutOrder = 0 }, UI.bundleScroll)
	-- (a section's heading: one label, so the list has nothing empty in it)
	UI.setsHead = txt(UI.bundleScroll, "SKIN SETS", 15, T.MUTED, T.FONT_BOLD)
	UI.setsHead.Size = UDim2.new(1, 0, 0, 22); UI.setsHead.LayoutOrder = 1
	UI.setRows = new("Frame", { Name = "Sets", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 0), AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = 2 }, UI.bundleScroll)
	new("UIListLayout", { Padding = UDim.new(0, 14), SortOrder = Enum.SortOrder.LayoutOrder }, UI.setRows)
	UI.bundlesHead = txt(UI.bundleScroll, "BUNDLES", 15, T.MUTED, T.FONT_BOLD)
	UI.bundlesHead.Size = UDim2.new(1, 0, 0, 22); UI.bundlesHead.LayoutOrder = 3
	UI.bundleGrid = new("Frame", { Name = "Grid", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 0), AutomaticSize = Enum.AutomaticSize.Y, LayoutOrder = 4 }, UI.bundleScroll)
	UI.bundleLayout = new("UIGridLayout", { CellPadding = UDim2.fromOffset(14, 14), CellSize = UDim2.fromOffset(380, 300), SortOrder = Enum.SortOrder.LayoutOrder }, UI.bundleGrid)
end
S.setH = 250
-- one thing of the VIP pack as a small square: a wrap's paint, anything else its still picture
function V.packChip(cell: Frame, it: any)
	if it.kind == "wrap" then
		local chip = new("Frame", { BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(6, 6), Size = UDim2.new(1, -12, 1, -12), ZIndex = cell.ZIndex + 1 }, cell)
		T.corner(chip, 3)
		paintChip(chip, it.id)
	else
		local cv = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = cell.ZIndex + 1 }, cell)
		V.chip(cv, it)
	end
end
-- VIP: the game pass. a wide tile at the top of BUNDLES: the pack's top skin wearing the VIP hat, what's in the pack,
-- the perks, and GET VIP (free while we test: the server's Vip.luau keeps the claim). click = the inspect panel
function ShopUI.fillVip()
	for _, c in UI.vipHolder:GetChildren() do c:Destroy() end
	local o = Shop.vip
	local k = S.compact
	local vip = isVip()
	local c = new("TextButton", { Name = "VipTile", Text = "", AutoButtonColor = false, BackgroundColor3 = T.CARD, BorderSizePixel = 0, ClipsDescendants = true, Size = UDim2.fromScale(1, 1) }, UI.vipHolder)
	T.corner(c)
	local st = T.edge(c, Shop.VIP_COLOR, 0.55)
	c.MouseEnter:Connect(function() c.BackgroundColor3 = T.CARD_HI; st.Transparency = 0.35 end)
	c.MouseLeave:Connect(function() c.BackgroundColor3 = T.CARD; st.Transparency = 0.55 end)
	local wash = new("Frame", { BackgroundColor3 = Shop.VIP_COLOR, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 1 }, c)
	T.corner(wash)
	new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.45, 0.95), NumberSequenceKeypoint.new(1, 0.82) }) }, wash)
	new("Frame", { Name = "Line", BackgroundColor3 = Shop.VIP_COLOR, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0, 3), ZIndex = 6 }, c)
	local pad = if k then 12 else 20
	-- the words and the button on the left
	local eb = txt(c, "GAME PASS", 11, Shop.VIP_COLOR, T.FONT_BOLD); eb.ZIndex = 3
	eb.Position = UDim2.fromOffset(pad, if k then 10 else 16); eb.Size = UDim2.new(0.4, 0, 0, 14)
	local name = txt(c, "VIP", if k then 26 else 36, T.TEXT, T.FONT_TITLE); name.ZIndex = 3
	name.Position = UDim2.fromOffset(pad, if k then 26 else 34); name.Size = UDim2.new(0.4, 0, 0, if k then 30 else 42)
	local y = if k then 60 else 84
	for i, line in o.perks do
		local dot = new("Frame", { BackgroundColor3 = Shop.VIP_COLOR, BorderSizePixel = 0, Position = UDim2.fromOffset(pad, y + (i - 1) * (if k then 22 else 26) + 6), Size = UDim2.fromOffset(5, 5), ZIndex = 3 }, c)
		T.corner(dot, 99)
		local l = txt(c, line, if k then 12 else 13, T.SOFT, T.FONT); l.ZIndex = 3
		l.Position = UDim2.fromOffset(pad + 12, y + (i - 1) * (if k then 22 else 26)); l.Size = UDim2.new(0.42, -12, 0, 18)
	end
	local b = button(c, "", "main", UDim2.new(0.38, 0, 0, 44), UDim2.new(0, pad, 1, -(44 + (if k then 12 else 18))))
	b.face.ZIndex = 4; b.face.TextSize = if k then 13 else 15
	if vip then b.set("YOU'RE VIP", false)
	elseif Shop.free() then b.set("GET VIP  ·  FREE WHILE TESTING", true)
	else b.set("GET VIP  " .. ROBUX .. " " .. commas(o.robux), Shop.ROBUX and (tonumber(Shop.VIP_PASS) or 0) > 0) end
	b.face.MouseButton1Click:Connect(function() ShopUI.getVip() end)
	-- the pack on the right: its top piece big, everything in it along the bottom
	local items = Shop.vipItems()
	local chipsH = if k then 44 else 58
	local hero = Shop.vipHero()
	local view = new("Frame", { Name = "View", BackgroundTransparency = 1, Position = UDim2.new(0.44, 0, 0, 4), Size = UDim2.new(0.56, -8, 1, -(chipsH + 20)), ZIndex = 2 }, c)
	if hero then V.show(view, V.gun(hero.weapon, hero.wrap, hero.hat, 1.4, hero.skin), "slow", 1.0) end
	local row = new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0.44, 0, 1, -(if k then 9 else 12)), Size = UDim2.new(0.56, -pad, 0, chipsH), ZIndex = 3 }, c)
	new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder, HorizontalAlignment = Enum.HorizontalAlignment.Right }, row)
	local n = math.max(#items, 5)
	for i, it in items do
		local cell = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.35, BorderSizePixel = 0, Size = UDim2.new(1 / n, -6 + 6 / n, 1, 0), LayoutOrder = i, ZIndex = 3 }, row)
		T.corner(cell, 4)
		V.packChip(cell, it)
		if vip then new("Frame", { BackgroundColor3 = Shop.VIP_COLOR, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -2), Size = UDim2.new(1, -12, 0, 2), ZIndex = 6 }, cell) end
	end
	c.MouseButton1Click:Connect(function() ShopUI.inspect("vip") end)
end
-- GET VIP: free while we test (the server keeps the claim), else Roblox's game pass prompt (the server's call)
function ShopUI.getVip()
	if isVip() or S.busy then return end
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("Vip")
	if not (r and r:IsA("RemoteFunction")) then Hud.callout("VIP ISN'T READY YET", 1.2); return end
	play("click")
	S.busy = true
	local ok, res = pcall(function() return (r :: RemoteFunction):InvokeServer(if Shop.free() then "claim" else "buy") end)
	S.busy = false
	if not ok or type(res) ~= "table" or not res.ok then
		Hud.callout(string.upper(if ok and type(res) == "table" and res.why then res.why else "couldn't reach the server"), 1.4)
		return
	end
	if res.vip then ShopUI.toast("YOU'RE VIP. THE DUCKY PACK IS IN YOUR INVENTORY") end
end
-- one skin set's banner: its colour washed in behind its top piece, its name, how much of it you own (a bar in the
-- set's glow colour) and its five skins along the bottom (the ones you own lit, the rest dimmed). click = its
-- "complete the set" panel (inspect)
local function setBanner(parent: Instance, o: any, pos: UDim2, size: UDim2)
	local k = S.compact
	local c = new("TextButton", { Name = o.id, Text = "", AutoButtonColor = false, BackgroundColor3 = T.CARD, BorderSizePixel = 0, ClipsDescendants = true, Position = pos, Size = size }, parent)
	T.corner(c)
	local st = T.edge(c)
	c.MouseEnter:Connect(function() c.BackgroundColor3 = T.CARD_HI; st.Transparency = 0.7 end)
	c.MouseLeave:Connect(function() c.BackgroundColor3 = T.CARD; st.Transparency = T.EDGE_A end)
	local col, acc = o.colour or T.CARD_HI, o.accent or T.ACCENT
	-- (the wash: the set's colour from the right, where its gun is; its glow low in that corner)
	local wash = new("Frame", { BackgroundColor3 = col, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 1 }, c)
	T.corner(wash)
	new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.4, 0.92), NumberSequenceKeypoint.new(1, 0.7) }) }, wash)
	local glow = new("Frame", { BackgroundColor3 = acc, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 1 }, c)
	T.corner(glow)
	new("UIGradient", { Rotation = -35, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.55, 1), NumberSequenceKeypoint.new(1, 0.82) }) }, glow)
	new("Frame", { Name = "Line", BackgroundColor3 = acc, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1), Size = UDim2.new(1, 0, 0, 3), ZIndex = 6 }, c)
	local pad = if k then 12 else 18
	local chipsH = if k then 46 else 62
	-- the top piece, big, on the right
	local view = new("Frame", { Name = "View", BackgroundTransparency = 1, Position = UDim2.new(0.4, 0, 0, 4), Size = UDim2.new(0.6, -6, 1, -(chipsH + 18)), ZIndex = 2 }, c)
	if o.hero then V.show(view, V.gun(o.hero.weapon, nil, nil, nil, o.hero.skin), "slow", 1.0) end
	-- the words on the left
	local eb = txt(c, "SKIN SET  ·  " .. #o.items .. " WEAPON SKINS", 11, T.MUTED, T.FONT_BOLD); eb.ZIndex = 3
	eb.Position = UDim2.fromOffset(pad, if k then 10 else 16); eb.Size = UDim2.new(0.5, 0, 0, 14)
	local name = txt(c, string.upper(o.name), if k then 24 else 32, T.TEXT, T.FONT_TITLE); name.ZIndex = 3
	name.Position = UDim2.fromOffset(pad, if k then 26 else 34); name.Size = UDim2.new(0.45, 0, 0, if k then 28 else 38)
	local miss = Till.missing(o)
	local have = #o.items - miss
	local pl = txt(c, have .. " / " .. #o.items .. " OWNED", 12, T.SOFT, T.FONT_BOLD); pl.ZIndex = 3
	pl.Position = UDim2.fromOffset(pad, if k then 58 else 78); pl.Size = UDim2.new(0.4, 0, 0, 16)
	local track = new("Frame", { BackgroundColor3 = T.TRACK, BorderSizePixel = 0, Position = UDim2.fromOffset(pad, if k then 78 else 100), Size = UDim2.new(0.34, 0, 0, 4), ZIndex = 3 }, c)
	T.corner(track, 2)
	local fill = new("Frame", { BackgroundColor3 = acc, BorderSizePixel = 0, Size = UDim2.fromScale(if #o.items > 0 then have / #o.items else 0, 1), ZIndex = 4 }, track)
	T.corner(fill, 2)
	local price = bundlePrice(o, miss)
	local word = if miss == 0 then "SET COMPLETE" elseif miss == #o.items then (if Shop.free() then "CLAIM  " else "") .. priceText(price)
		else miss .. " LEFT  ·  " .. priceText(price)
	local pr = txt(c, word, if k then 13 else 15, if miss == 0 then T.MUTED else T.TEXT, T.FONT_BOLD); pr.ZIndex = 3; pr.RichText = true
	pr.Position = UDim2.new(0, pad, 1, -(chipsH + (if k then 34 else 44))); pr.Size = UDim2.new(0.42, 0, 0, 18)
	-- the five along the bottom
	local row = new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, pad, 1, -(if k then 9 else 12)), Size = UDim2.new(1, -2 * pad, 0, chipsH), ZIndex = 3 }, c)
	new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 6), SortOrder = Enum.SortOrder.LayoutOrder }, row)
	for i, it in o.items do
		local own = Till.owns(it.kind, it.id, it.weapon)
		local cell = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.35, BorderSizePixel = 0, Size = UDim2.new(1 / #o.items, -6 + 6 / #o.items, 1, 0), LayoutOrder = i, ZIndex = 3 }, row)
		T.corner(cell, 4)
		local cv = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 1, -3), ZIndex = 4 }, cell)
		V.chip(cv, it)
		local vp = cv:FindFirstChild("Preview")
		if vp and vp:IsA("ViewportFrame") and not own then vp.ImageTransparency = 0.6 end
		if own then new("Frame", { BackgroundColor3 = acc, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -2), Size = UDim2.new(1, -12, 0, 2), ZIndex = 5 }, cell) end
	end
	c.MouseButton1Click:Connect(function() ShopUI.inspect(o.id) end)
end
-- one row of banners: a pair of sets side by side, joined (Seraph | Infernal), or two lone sets with a gap
local function setRow(r: { any }, order: number)
	local f = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, S.setH), LayoutOrder = order }, UI.setRows)
	local gap = if r.pair then 3 else 14
	for i, o in r do
		if type(i) == "number" then
			setBanner(f, o, UDim2.new((i - 1) * 0.5, if i == 2 then math.ceil(gap / 2) else 0, 0, 0), UDim2.new(0.5, -math.ceil(gap / 2), 1, 0))
		end
	end
end
function ShopUI.fillBundles()
	ShopUI.fillVip()
	for _, c in UI.bundleGrid:GetChildren() do if c:IsA("GuiButton") then c:Destroy() end end
	for _, c in UI.setRows:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
	-- the skin sets on sale: a pair on one row, the lone sets two to a row
	local rows, used, lone = {}, {}, nil
	for _, o in Shop.sets do
		if Shop.ready(o) and not used[o.id] then
			used[o.id] = true
			local mate = if o.pair then Shop.offer(o.pair) else nil
			if mate and mate.set and not used[mate.id] then
				used[mate.id] = true
				table.insert(rows, { o, mate, pair = true })
			elseif lone then
				table.insert(rows, { lone, o }); lone = nil
			else
				lone = o
			end
		end
	end
	if lone then table.insert(rows, { lone }) end
	for i, r in rows do setRow(r, i) end
	UI.setsHead.Visible = #rows > 0; UI.setRows.Visible = #rows > 0; UI.bundlesHead.Visible = #rows > 0
	local rot = Shop.rotation()
	local list = Shop.shown()
	-- today's featured one first, then dearest first
	table.sort(list, function(a, b)
		if (a.id == rot.hero) ~= (b.id == rot.hero) then return a.id == rot.hero end
		return a.robux > b.robux
	end)
	for i, o in list do bundleCard(UI.bundleGrid, o, i) end
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
		-- (what it redeems for with the quests' wallet, on the same line, right: "OR 6 TICKETS · 2,500 BRASS")
		local rp = Purse.price(o.id)
		if rp and not k then
			local bits = {}
			if rp.tix then table.insert(bits, Purse.words("tix", rp.tix)) end
			if rp.brass then table.insert(bits, Purse.words("brass", rp.brass)) end
			local rl = txt(c, "OR " .. table.concat(bits, "  ·  "), 12, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Right)
			rl.Position = UDim2.new(0.3, 0, 1, -116); rl.Size = UDim2.new(0.7, -pad, 0, 16)
		end
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
		elseif S.restricted and not Shop.free() then if Purse.price(o.id) then buy.set("REDEEM", true) else buy.set("NOT AVAILABLE HERE", false) end
		else buy.set((if Shop.free() then "CLAIM" else "BUY") .. word .. "  " .. Purse.cost(o, n), true) end
		buy.face.MouseButton1Click:Connect(function() ShopUI.ask(o.id) end)
		c.MouseButton1Click:Connect(function() ShopUI.inspect(o.id) end)
	end
end

-- ------------------------------------------------------------------------ WEAPONS and COINS (18 Nov)
-- (the owner: "buying weapons with coins make sure thats a thing", "we then also need a shop page for coins yea".
-- Coins are the one soft currency, Brass in the code: earned from quests and the weekly track, bought here.)
-- WEAPONS: the Robux-exclusive weapons (Unlocks.ROBUX), each for Robux or for Coins (Shop.MONEY.weapons). a Coins buy
-- is the server's (JankfireRemotes.Purchases "brass", after a second press); a Robux one the usual prompt. while they're
-- free for everyone (Unlocks.robuxFree) the cards say so and sell nothing. not enough coins: the COINS tab opens.
-- COINS: the balance with the coin, and the four coin packs (Shop.MONEY.coins) with their pictures; a prompt once Robux
-- is on, else the price struck through, NOT FOR SALE YET. the HUD's wallet opens it too (QuestClient). docs/MONEY.md
local Money = {} -- (the two pages' state and helpers, one local)
Money.arm = nil :: string?
Money.armT = 0
do
	local pg_ = UI.pages.weapons
	UI.gunScroll = new("ScrollingFrame", { BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), CanvasSize = UDim2.new(),
		ScrollBarThickness = 4, ScrollingDirection = Enum.ScrollingDirection.Y }, pg_)
	UI.gunBar = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, -8, 0, 22) }, UI.gunScroll)
	UI.gunHead, UI.gunNote = header(UI.gunBar, "WEAPONS", "ROBUX OR COINS")
	UI.gunRow = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 30), Size = UDim2.new(1, -8, 0, 300) }, UI.gunScroll)
	new("UIGridLayout", { CellPadding = UDim2.fromOffset(14, 0), CellSize = UDim2.new(0.25, -11, 1, 0), SortOrder = Enum.SortOrder.LayoutOrder }, UI.gunRow)
	local pc = UI.pages.coins
	UI.coinScroll = new("ScrollingFrame", { BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), CanvasSize = UDim2.new(),
		ScrollBarThickness = 4, ScrollingDirection = Enum.ScrollingDirection.Y }, pc)
	UI.coinBar = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, -8, 0, 30) }, UI.coinScroll)
	UI.coinHead, UI.coinNote = header(UI.coinBar, "COINS", "")
	UI.coinNote.Position = UDim2.fromOffset(0, 26)
	-- the balance, top right: the coin and the number
	UI.coinHave = new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, 0, 0, 0), Size = UDim2.fromOffset(0, 30),
		AutomaticSize = Enum.AutomaticSize.X }, UI.coinBar)
	new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center, HorizontalAlignment = Enum.HorizontalAlignment.Right,
		SortOrder = Enum.SortOrder.LayoutOrder, Padding = UDim.new(0, 8) }, UI.coinHave)
	local ic = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromOffset(26, 26), LayoutOrder = 1 }, UI.coinHave)
	Purse.icon("brass", ic, 26)
	UI.coinAmt = txt(UI.coinHave, "0", 22, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Right)
	UI.coinAmt.AutomaticSize = Enum.AutomaticSize.X; UI.coinAmt.Size = UDim2.fromOffset(0, 30); UI.coinAmt.LayoutOrder = 2
	UI.coinRow = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 52), Size = UDim2.new(1, -8, 0, 320) }, UI.coinScroll)
	new("UIGridLayout", { CellPadding = UDim2.fromOffset(14, 0), CellSize = UDim2.new(0.25, -11, 1, 0), SortOrder = Enum.SortOrder.LayoutOrder }, UI.coinRow)
end
function Money.ask(op: string, a: any?, b: any?): any
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("Purchases")
	if not (r and r:IsA("RemoteFunction")) then return { ok = false, why = "the till isn't open yet" } end
	local ok, res = pcall(function() return (r :: RemoteFunction):InvokeServer(op, a, b) end)
	if not ok or type(res) ~= "table" then return { ok = false, why = "couldn't reach the shop" } end
	return res
end
-- a chance as a percentage, rounded four places past its first digit (Roblox's rule for long decimals): 12.346, 0.0083333
function Money.pct(p: number): string
	if p <= 0 then return "0" end
	local first = math.floor(math.log10(p))
	local places = math.clamp(4 - first, 2, 12)
	return (string.format("%." .. places .. "f", p):gsub("0+$", ""):gsub("%.$", ""))
end
-- the coins-only shop's till: a single, n containers or a deal ("deal:<skin>") for coins, taken by the server
-- (Purchases "coins"); a container opens at once, as a bought one does. not enough coins: the COINS tab
function ShopUI.coinTill(o: any, n: number?): boolean
	local cost = if o.id and string.sub(o.id, 1, 5) == "deal:" then o.coins else Purse.coins(o, n)
	if not cost then return false end
	if Purse.of("brass") < cost then play("empty"); ShopUI.toast("NOT ENOUGH COINS"); ShopUI.tab("coins"); return false end
	S.busy = true
	local res = Money.ask("coins", o.id, n)
	S.busy = false
	if not res.ok then Hud.callout(string.upper(tostring(res.why or "the shop said no")), 1.6); return false end
	play("click")
	Till.refresh()
	if o.type == "container" then ShopUI.openBox(o.id, n or 1); return true end
	ShopUI.toast(string.upper(o.name or "it") .. " ADDED. WEAR IT FROM THE LOADOUT [L]")
	ShopUI.refill()
	return true
end
function Money.owns(wid: string): boolean
	local s = me:GetAttribute("RobuxOwned")
	return type(s) == "string" and table.find(string.split(s, ","), wid) ~= nil
end
function Money.coinBuy(wid: string)
	local o = Shop.weaponOffer(wid)
	if not o then return end
	if Purse.of("brass") < o.coins then play("empty"); ShopUI.toast("NOT ENOUGH COINS"); ShopUI.tab("coins"); return end
	if Money.arm ~= wid or os.clock() - Money.armT > 4 then
		Money.arm, Money.armT = wid, os.clock()
		play("click"); ShopUI.fillWeapons()
		task.delay(4.1, function() if Money.arm == wid then Money.arm = nil; if S.open and S.tab == "weapons" then ShopUI.fillWeapons() end end end)
		return
	end
	Money.arm = nil
	local res = Money.ask("brass", wid)
	if res.ok then play("ting"); ShopUI.toast(string.upper(o.name) .. " IS YOURS")
	else play("empty"); ShopUI.toast(string.upper(tostring(res.why or "that didn't work"))) end
	ShopUI.fillWeapons()
end
function ShopUI.fillWeapons()
	for _, c in UI.gunRow:GetChildren() do if c:IsA("GuiButton") then c:Destroy() end end
	local U = require(Shared:WaitForChild("Unlocks")) :: any
	local free = U.robuxFree()
	local k = S.compact
	local pad = if k then 10 else 14
	-- (the page's own height; on a phone it scrolls)
	local H = UI.gunScroll.AbsoluteSize.Y
	local gunH = math.max(if k then 230 else 300, H - 40)
	UI.gunRow.Size = UDim2.new(1, -8, 0, gunH)
	UI.gunScroll.CanvasSize = UDim2.fromOffset(0, 30 + gunH)
	UI.gunNote.Text = if free then "FREE FOR NOW" else "ROBUX OR COINS"
	for i, wid in Shop.WEAPON_IDS do
		local o = Shop.weaponOffer(wid)
		if not o then continue end
		local c = card(UI.gunRow, "legendary")
		c.LayoutOrder = i
		local view = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 6), Size = UDim2.new(1, 0, 1, -(if k then 100 else 112)) }, c)
		V.show(view, V.gun(wid), "hover", 1.0)
		local name = txt(c, string.upper(o.name), if k then 15 else 18, T.TEXT, T.FONT_TITLE)
		name.Position = UDim2.new(0, pad, 1, if k then -96 else -106); name.Size = UDim2.new(1, -2 * pad, 0, 22)
		local own = Money.owns(wid)
		local line = txt(c, if own then "YOURS" elseif free then "FREE FOR NOW" else "", 11, if own then T.ACCENT else T.SOFT, T.FONT_BOLD)
		line.Position = UDim2.new(0, pad, 1, if k then -72 else -80); line.Size = UDim2.new(1, -2 * pad, 0, 14)
		local bh = 44
		local y = -(bh + (if k then 8 else 12))
		local rb = button(c, "", "main", UDim2.new(0.5, -(pad + 4), 0, bh), UDim2.new(0, pad, 1, y))
		local bb = button(c, "", "dark", UDim2.new(0.5, -(pad + 4), 0, bh), UDim2.new(0.5, 4, 1, y))
		if own or free then
			rb.face.Size = UDim2.new(1, -2 * pad, 0, bh)
			bb.face.Visible = false
			rb.set(if own then "OWNED" else "FREE FOR NOW", false)
		else
			rb.set(priceText(o.robux), Shop.ROBUX == true and Shop.productFor(o) ~= nil)
			local armed = Money.arm == wid and os.clock() - Money.armT < 4
			bb.set(if armed then "SURE? " .. commas(o.coins) else Purse.words("brass", o.coins), true)
		end
		rb.face.MouseButton1Click:Connect(function() if not own and not free then ShopUI.prompt(o) end end)
		bb.face.MouseButton1Click:Connect(function() if not own and not free then Money.coinBuy(wid) end end)
	end
end
function ShopUI.fillCoins()
	for _, c in UI.coinRow:GetChildren() do if c:IsA("GuiButton") then c:Destroy() end end
	local k = S.compact
	local pad = if k then 10 else 14
	local H = UI.coinScroll.AbsoluteSize.Y
	local rowH = math.max(if k then 240 else 320, H - 60)
	UI.coinRow.Size = UDim2.new(1, -8, 0, rowH)
	UI.coinScroll.CanvasSize = UDim2.fromOffset(0, 52 + rowH)
	UI.coinAmt.Text = commas(Purse.of("brass"))
	local sell = Shop.ROBUX == true and not Shop.free()
	UI.coinNote.Text = if sell then "" else "NOT FOR SALE YET"
	for i, o in Shop.coinPacks() do
		local c = card(UI.coinRow, nil)
		c.LayoutOrder = i
		new("ImageLabel", { Name = "Picture", BackgroundTransparency = 1, Image = o.image or "", ScaleType = Enum.ScaleType.Fit,
			Position = UDim2.fromOffset(pad, pad), Size = UDim2.new(1, -2 * pad, 1, -(if k then 118 else 140)) }, c)
		local amt = txt(c, commas(o.amount), if k then 24 else 32, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Center)
		amt.Position = UDim2.new(0, 0, 1, if k then -112 else -128); amt.Size = UDim2.new(1, 0, 0, if k then 28 else 36)
		local sub = txt(c, "COINS", 12, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center)
		sub.Position = UDim2.new(0, 0, 1, if k then -84 else -92); sub.Size = UDim2.new(1, 0, 0, 14)
		if o.bonus > 0 then -- (the bonus: a small "+N" chip on the picture)
			local chip = new("Frame", { Name = "Bonus", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0),
				Position = UDim2.new(1, -pad, 0, pad), Size = UDim2.fromOffset(0, 24), AutomaticSize = Enum.AutomaticSize.X, ZIndex = 5 }, c)
			T.corner(chip, 4)
			new("UIPadding", { PaddingLeft = UDim.new(0, 8), PaddingRight = UDim.new(0, 8) }, chip)
			local cl = txt(chip, "+" .. commas(o.bonus), 13, T.INK, T.FONT_BOLD, Enum.TextXAlignment.Center)
			cl.AutomaticSize = Enum.AutomaticSize.X; cl.Size = UDim2.fromOffset(0, 24); cl.ZIndex = 6
		end
		local b = button(c, "", "main", UDim2.new(1, -2 * pad, 0, 44), UDim2.new(0, pad, 1, -(44 + pad)))
		b.set(priceText(o.robux), sell and Shop.productFor(o) ~= nil)
		b.face.MouseButton1Click:Connect(function() if sell then ShopUI.prompt(o) end end)
	end
end
for _, a in { "RobuxOwned", "Brass" } do
	me:GetAttributeChangedSignal(a):Connect(function()
		if S.open and S.tab == "weapons" then ShopUI.fillWeapons() elseif S.open and S.tab == "coins" then ShopUI.fillCoins() end
	end)
end
ReplicatedStorage:GetAttributeChangedSignal("MoneyTest"):Connect(function() if S.open then ShopUI.refill() end end)

-- ------------------------------------------------------------------------ DEALS: the owner's three picks for you today
-- (the owner, 17 Nov: "I give players 3 special discounts on random skins if you talk to me!". the server picks and
-- keeps them: Deals.luau, JankfireRemotes.Deals "get" / "buy"; the rules are Shop.DEAL_*. the owner's shopkeeper in the
-- training area's gun shop opens the shop here: its prompt has ShopOpen = "tab:deals")
local Deal = {} -- (the deals' state and helpers, one local for the lot)
Deal.list = nil :: any
Deal.gen = 0
function Deal.ask(op: string, a: any?): any
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("Deals")
	if not (r and r:IsA("RemoteFunction")) then return { ok = false, why = "the deals aren't open yet" } end
	local ok, res = pcall(function() return (r :: RemoteFunction):InvokeServer(op, a) end)
	if not ok or type(res) ~= "table" then return { ok = false, why = "couldn't reach the shop" } end
	return res
end
function Deal.find(skin: string): any?
	for _, d in (if Deal.list then Deal.list.deals else {}) :: { any } do if d.skin == skin then return d end end
	return nil
end
do
	local pg_ = UI.pages.deals
	UI.dealsHead, UI.dealsTimer = header(pg_, "OWNER'S PICKS", "")
	UI.dealsRow = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 30), Size = UDim2.new(1, 0, 1, -30) }, pg_)
	new("UIGridLayout", { CellPadding = UDim2.fromOffset(14, 0), CellSize = UDim2.new(1 / 3, -10, 1, 0), SortOrder = Enum.SortOrder.LayoutOrder }, UI.dealsRow)
	UI.dealsNote = txt(pg_, "", 16, T.MUTED, T.FONT, Enum.TextXAlignment.Center)
	UI.dealsNote.Position = UDim2.fromOffset(0, 140); UI.dealsNote.Size = UDim2.new(1, 0, 0, 24)
end
-- one deal: the skin big, "OWNER'S PICK · 30% OFF", its name and gun, the deal's price with the normal one struck
-- through, and CLAIM / BUY (YOURS once had, OWNED if you got it another way). a thin amber edge marks the owner's picks
local function dealCard(parent: Instance, d: any, order: number): TextButton
	local k = S.compact
	local c = card(parent, d.rarity)
	c.LayoutOrder = order
	local pick = new("Frame", { Name = "Pick", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = 5 }, c)
	T.corner(pick)
	T.edge(pick, T.ACCENT, 0.5)
	local wash = new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 1 }, c)
	T.corner(wash)
	new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.9), NumberSequenceKeypoint.new(0.4, 1), NumberSequenceKeypoint.new(1, 1) }) }, wash)
	local pad = if k then 12 else 18
	local eb = txt(c, "OWNER'S PICK  ·  " .. tostring(d.pct) .. "% OFF", 11, T.ACCENT, T.FONT_BOLD); eb.ZIndex = 3
	eb.Position = UDim2.fromOffset(pad, if k then 10 else 16); eb.Size = UDim2.new(1, -2 * pad, 0, 14)
	Fin.badge(c, d.skin, UDim2.new(1, -pad, 0, if k then 6 else 11))
	local textH = if k then 150 else 196
	local view = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, if k then 26 else 36), Size = UDim2.new(1, 0, 1, -(textH + (if k then 26 else 36))), ZIndex = 2 }, c)
	V.show(view, V.gun(d.weapon, nil, nil, nil, d.skin), "hover", 1.0)
	local name = txt(c, string.upper(tostring(d.name)), if k then 20 else 26, T.TEXT, T.FONT_TITLE); name.ZIndex = 3
	name.Position = UDim2.new(0, pad, 1, if k then -146 else -190); name.Size = UDim2.new(1, -2 * pad, 0, if k then 24 else 30)
	local wl = txt(c, "FOR " .. string.upper(Shop.weaponName(d.weapon)), 12, T.SOFT, T.FONT_BOLD); wl.ZIndex = 3
	wl.Position = UDim2.new(0, pad, 1, if k then -120 else -156); wl.Size = UDim2.new(1, -2 * pad, 0, 15)
	local rl = rarityLine(c, d.rarity, "SKIN", 11)
	rl.Position = UDim2.new(0, pad, 1, if k then -102 else -134); rl.Size = UDim2.new(1, -2 * pad, 0, 15)
	local coinsD = Shop.coinsOnly() and not Shop.free() -- (the coins-only shop: a deal in coins, 18 Nov)
	local pr = txt(c, if coinsD then string.format('%s   <font size="%d" color="%s"><s>%s</s></font>', Purse.words("brass", Shop.coinDealPrice(d.skin, d.pct)),
			if k then 13 else 15, T.hex(T.MUTED), commas(Shop.coinPrice({ type = "single", kind = "skin", rarity = d.rarity }) or 0))
		else string.format('%s %s   <font size="%d" color="%s"><s>%s %s</s></font>', ROBUX, commas(d.price),
		if k then 13 else 15, T.hex(T.MUTED), ROBUX, commas(d.was)), if k then 18 else 22, T.TEXT, T.FONT_BOLD)
	pr.RichText = true; pr.ZIndex = 3
	pr.Position = UDim2.new(0, pad, 1, if k then -80 else -108); pr.Size = UDim2.new(1, -2 * pad, 0, if k then 22 else 28)
	local bh = 44 -- (a touch target)
	local buy = button(c, "", "main", UDim2.new(1, -2 * pad, 0, bh), UDim2.new(0, pad, 1, -(bh + (if k then 10 else 16))))
	buy.face.ZIndex = 6
	if d.bought then buy.set("YOURS", false)
	elseif d.owned then buy.set("OWNED", false)
	elseif Shop.free() then buy.set("CLAIM", true)
	elseif coinsD then buy.set("BUY  " .. Purse.words("brass", Shop.coinDealPrice(d.skin, d.pct)), true)
	else buy.set("BUY  " .. ROBUX .. " " .. commas(d.price), Shop.ROBUX == true) end
	buy.face.MouseButton1Click:Connect(function() if buy.enabled then ShopUI.askDeal(d.skin) end end)
	c.MouseButton1Click:Connect(function() if buy.enabled then ShopUI.askDeal(d.skin) end end)
	return c
end
function Deal.draw()
	for _, c in UI.dealsRow:GetChildren() do if c:IsA("GuiButton") then c:Destroy() end end
	local list = if Deal.list then Deal.list.deals else {}
	UI.dealsNote.Text = if #list == 0 then "you have every skin that's on sale" else ""
	for i, d in list do dealCard(UI.dealsRow, d, i) end
end
-- the tab: what's known at once, then the server's word (the same three all day; new at 00:00 UTC)
function ShopUI.fillDeals()
	Deal.gen += 1
	local gen = Deal.gen
	if Deal.list then Deal.draw() else
		for _, c in UI.dealsRow:GetChildren() do if c:IsA("GuiButton") then c:Destroy() end end
		UI.dealsNote.Text = "loading the owner's picks"
	end
	task.spawn(function()
		local res = Deal.ask("get")
		if gen ~= Deal.gen or not S.open or S.tab ~= "deals" then return end
		if not res.ok then
			if not Deal.list then UI.dealsNote.Text = string.lower(tostring(res.why or "can't load the deals right now")) end
			return
		end
		Deal.list = res
		Deal.draw()
	end)
end
-- step one: the confirm panel (with Robux on, Roblox's own prompt is the confirm: ShopReceipts checks it's yours)
function ShopUI.askDeal(skin: string)
	local d = Deal.find(skin)
	if not d or S.busy then return end
	if d.bought or d.owned then Hud.callout("ALREADY YOURS", 1); return end
	-- (the coins-only shop: the confirm panel, then the coins till)
	local coinsD = Shop.coinsOnly() and not Shop.free()
	if not Shop.free() and not coinsD then
		if not Shop.ROBUX then Hud.callout("THE SHOP IS SHUT", 1); return end
		local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
		local r = f and f:FindFirstChild("ShopBuy")
		if r and r:IsA("RemoteEvent") then play("click"); r:FireServer("deal:" .. skin) end
		return
	end
	play("click")
	S.pending = "deal:" .. skin
	S.pendingN = 1
	for _, c in UI.cOdds:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	UI.cOdds.Size = UDim2.new(1, -44, 0, 0)
	UI.cTitle.Text = (if coinsD then "BUY " else "CLAIM ") .. string.upper(tostring(d.name)) .. "?"
	UI.cBody.Text = string.format("this weapon skin for the %s goes into your inventory. the owner's pick: %d%% off.", Shop.weaponName(d.weapon), d.pct)
		.. (if coinsD then "" else string.format('<br/><font color="%s">free while we test. later: %s %s (normally %s %s)</font>', T.hex(T.MUTED), ROBUX, commas(d.price), ROBUX, commas(d.was)))
	Purse.row("", 1)
	UI.cYes.set(if coinsD then "BUY  " .. Purse.words("brass", Shop.coinDealPrice(d.skin, d.pct)) else "CLAIM", true)
	UI.confirm.Size = UDim2.fromOffset(460, if S.compact then 210 else 230)
	UI.confirm.Visible = true
	ShopUI.layer()
end
-- step two: the server gives it (one of today's, not had yet: it checks)
function ShopUI.commitDeal(skin: string)
	if not UI.cYes.enabled then return end
	ShopUI.unconfirm()
	if S.busy then return end
	if Shop.coinsOnly() and not Shop.free() then
		local dd = Deal.find(skin)
		if dd and ShopUI.coinTill({ id = "deal:" .. skin, type = "deal", name = dd.name, coins = Shop.coinDealPrice(skin, dd.pct) }) then dd.bought = true; ShopUI.refill() end
		return
	end
	S.busy = true
	local res = Deal.ask("buy", skin)
	S.busy = false
	if not res.ok then Hud.callout(string.upper(tostring(res.why or "the shop said no")), 1.6); return end
	play("click")
	local d = Deal.find(skin)
	if d then d.bought = true end
	Till.refresh()
	ShopUI.toast(string.upper(Shop.itemLabel({ kind = "skin", id = skin })) .. " ADDED. WEAR IT FROM THE LOADOUT [L]")
	ShopUI.refill()
end

-- ------------------------------------------------------------------------ INVENTORY: what you own
do
	local pg_ = UI.pages.inventory
	-- (the filters scroll sideways when they don't all fit, on a phone; the count sits to their right)
	UI.invFilters = new("ScrollingFrame", { BackgroundTransparency = 1, BorderSizePixel = 0, Size = UDim2.new(1, -120, 0, 36), CanvasSize = UDim2.new(),
		AutomaticCanvasSize = Enum.AutomaticSize.X, ScrollingDirection = Enum.ScrollingDirection.X, ScrollBarThickness = 0, ScrollBarImageTransparency = 1 }, pg_)
	new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder }, UI.invFilters)
	new("UIPadding", { PaddingLeft = UDim.new(0, 1), PaddingRight = UDim.new(0, 1), PaddingTop = UDim.new(0, 1), PaddingBottom = UDim.new(0, 1) }, UI.invFilters)
	UI.invBtns = {}
	UI.invMins = {} :: { UISizeConstraint }
	local FILTER_WORDS = { all = "ALL", containers = "CONTAINERS", skin = "SKINS", wrap = "WRAPS", hat = "HATS", card = "CARD", kill = "KILL EFFECTS", emote = "EMOTES" }
	for i, f in { "all", "containers", "skin", "wrap", "hat", "card", "kill", "emote" } do
		if Shop.isFlair(f) and not Shop.Flair then continue end
		local b = button(UI.invFilters, FILTER_WORDS[f], "dark", UDim2.fromOffset(0, 34))
		b.face.AutomaticSize = Enum.AutomaticSize.X
		new("UIPadding", { PaddingLeft = UDim.new(0, 16), PaddingRight = UDim.new(0, 16) }, b.face)
		table.insert(UI.invMins, new("UISizeConstraint", { MinSize = Vector2.new(120, 0) }, b.face))
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
	-- skins, wraps and hats, grouped by the weapon they're for (the loadout's order), rarest first in each
	local byWeapon: { [string]: { any } } = {}
	local KORDER = { skin = 1, wrap = 2, hat = 3 }
	local seenVip: { [string]: boolean } = {}
	for _, kind in { "skin", "wrap", "hat", "border", "banner", "title", "kill", "emote" } do
		if f == "all" or f == kind or (f == "card" and Shop.isCard(kind)) then
			for key in S.inv[kind] or {} do
				local id, w = Shop.unkey(key)
				if kind == "skin" then w = Shop.skinWeapon(id) end
				-- (the VIP pack in a section of its own, each thing once: a VIP wrap or hat is on every gun)
				local vipThing = Shop.vipOnly(kind, id)
				if vipThing and kind ~= "skin" then w = nil end
				local dupe = vipThing and seenVip[kind .. ":" .. id]
				if not dupe and Shop.exists(kind, id, w) then
					if vipThing then seenVip[kind .. ":" .. id] = true end
					local name, r = Shop.itemInfo(kind, id)
					local g = if vipThing then "_vip" elseif Shop.isCard(kind) then "_card" elseif Shop.isFlair(kind) then "_" .. kind
						elseif w and Shop.WEAPON_SET[w] then w else "_any"
					byWeapon[g] = byWeapon[g] or {}
					table.insert(byWeapon[g], { kind = kind, id = id, weapon = w, name = name, rarity = r, vip = vipThing })
				end
			end
		end
	end
	local groups = table.clone(Shop.WEAPONS)
	table.insert(groups, 1, "_vip") -- (the VIP pack, first)
	table.insert(groups, "_any") -- (things kept without a weapon, from an older save)
	table.insert(groups, "_card") -- (the player card's looks)
	table.insert(groups, "_kill"); table.insert(groups, "_emote") -- (kill effects, emotes)
	local GROUP_WORDS = { _vip = "VIP", _any = "any weapon", _card = "player card", _kill = "kill effects", _emote = "emotes" }
	for gi, g in groups do
		local items = byWeapon[g]
		if items and #items > 0 then
			table.sort(items, function(a, b)
				if a.kind ~= b.kind then return (KORDER[a.kind] or 9) < (KORDER[b.kind] or 9) end
				if Shop.rank(a.rarity) ~= Shop.rank(b.rarity) then return Shop.rank(a.rarity) > Shop.rank(b.rarity) end
				return a.name < b.name
			end)
			local grid = invSection(GROUP_WORDS[g] or Shop.weaponName(g), #items, gi)
			for _, it in items do
				n += 1; order += 1
				local c = card(grid, it.rarity)
				c.LayoutOrder = order
				local view = new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 1, -50) }, c)
				V.put(view, nil, it, "hover", 1.08, if it.kind == "hat" then 1.6 else nil)
				local name = txt(c, it.name, 15, T.TEXT, T.FONT_BOLD)
				name.Position = UDim2.new(0, 10, 1, -46); name.Size = UDim2.new(1, -20, 0, 18)
				local rl = rarityLine(c, it.rarity, Shop.KIND_NAMES[it.kind], 10)
				if it.kind == "skin" then Fin.badge(c, it.id, UDim2.new(1, -6, 0, 6)) end
				rl.Position = UDim2.new(0, 10, 1, -24); rl.Size = UDim2.new(1, -20, 0, 14)
				local oid = if it.vip then "vip" else Shop.singleId({ kind = it.kind, id = it.id, weapon = it.weapon or (if Shop.gunless(it.kind) then nil else V.yourGun()) })
				c.MouseButton1Click:Connect(function() ShopUI.inspect(oid) end)
			end
		end
	end
	UI.invCount.Text = if S.invOk then n .. (if n == 1 then " THING" else " THINGS") else ""
	-- (on a phone the filters scroll: keep the picked one in view)
	local sel = UI.invBtns[S.invFilter]
	if sel then
		local fr = UI.invFilters
		local x0 = sel.face.AbsolutePosition.X - fr.AbsolutePosition.X + fr.CanvasPosition.X
		local w, view = sel.face.AbsoluteSize.X, fr.AbsoluteSize.X
		if x0 < fr.CanvasPosition.X then fr.CanvasPosition = Vector2.new(math.max(0, x0 - 8), 0)
		elseif x0 + w > fr.CanvasPosition.X + view then fr.CanvasPosition = Vector2.new(x0 + w - view + 8, 0) end
	end
	UI.invEmpty.Text = if not S.invOk then "can't load your inventory right now."
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
	UI.inspBack.face.MouseButton1Click:Connect(function() ShopUI.back() end)
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
	-- (a skin set's progress: a bar in the set's glow colour, right of the "2 / 5 OWNED" note)
	UI.inspBar = new("Frame", { BackgroundColor3 = T.TRACK, BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 1), Size = UDim2.new(0.45, 0, 0, 5), Visible = false, ZIndex = 23 }, Sd)
	T.corner(UI.inspBar, 2)
	UI.inspFill = new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, Size = UDim2.fromScale(0, 1), ZIndex = 24 }, UI.inspBar)
	T.corner(UI.inspFill, 2)
	-- (a skin with a finisher, or a set or the VIP pack with one: its cinematic, played in front of you)
	UI.inspFin = button(Sd, "PREVIEW FINISHER", "dark", UDim2.new(1, 0, 0, 44), UDim2.new(0, 0, 1, -100))
	UI.inspFin.face.ZIndex = 23; UI.inspFin.face.Visible = false
	UI.inspFin.face.MouseButton1Click:Connect(function()
		if S.showKill then Fin.showcase(S.showKill) elseif S.finSkin then Fin.preview(S.finSkin) end
	end)
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
-- "DRAG TO TURN" on the big preview, only when it's a 3D model (a card look, kill effect or emote is a flat tile)
function V.hint()
	UI.inspHint.Parent = UI.inspView
	local p = UI.inspView:FindFirstChild("Preview")
	UI.inspHint.Visible = p ~= nil and p:IsA("ViewportFrame")
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
		V.chip(chip, it)
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
	if it.kind == "skin" then Fin.badge(row, it.id, UDim2.new(1, -(if own then 70 else 10), 0.5, -11), 25) end
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
			V.put(UI.inspView, o, nil, "drag", 1.1)
		else
			S.preview = it
			row.BackgroundColor3 = T.CARD_HI; st.Color = T.ACCENT; st.Transparency = 0.3
			V.put(UI.inspView, o, it, "drag", if it.kind == "hat" then 1.0 else 1.1)
		end
		V.hint()
	end)
end
function ShopUI.fillInspect()
	local o = Shop.offer(S.inspect)
	if not o then return end
	S.preview = nil
	V.put(UI.inspView, o, nil, "drag", if o.type == "container" then 0.95 elseif o.kind == "hat" then 1.0 else 1.1)
	V.hint()
	for _, c in UI.inspList:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	UI.inspEyebrow:Destroy()
	local kindWord = if o.type == "pass" then "GAME PASS  ·  " .. #Shop.vipItems() .. " ITEMS + THE VIP ROOM" elseif o.set then "SKIN SET  ·  " .. #o.items .. " WEAPON SKINS" elseif o.type == "bundle" then "BUNDLE  ·  " .. #o.items .. " ITEMS" elseif o.type == "container" then "CONTAINER" else string.upper(Shop.KIND_NAMES[o.kind] or "") .. "  ·  " .. V.forWords(o.kind, o.weapon, true)
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
	-- (the finisher to preview: a skin's own, or for a set or the VIP pack the first of its skins that has one)
	S.finSkin = nil
	if o.type == "single" and o.kind == "skin" then
		if Fin.of(o.item) then S.finSkin = o.item end
	elseif o.type == "pass" or o.set then
		for _, it in Shop.contents(o) do if it.kind == "skin" and Fin.of(it.id) then S.finSkin = it.id; break end end
	end
	-- (a kill effect: PREVIEW ON YOU, the real effect on a copy of you on a set off the map, full screen: FlairAnim)
	S.showKill = if o.type == "single" and o.kind == "kill" then o.item else nil
	UI.inspFin.face.Visible = S.finSkin ~= nil or S.showKill ~= nil
	UI.inspFin.set(if S.showKill then "PREVIEW ON YOU" else "PREVIEW FINISHER", true)
	local oldFin = UI.inspView:FindFirstChild("Finisher")
	if oldFin then oldFin:Destroy() end
	if S.finSkin and o.type == "single" then Fin.badge(UI.inspView, S.finSkin, UDim2.new(1, -10, 0, 10), 24) end
	local foot = if isBox or S.finSkin or S.showKill then 104 else 56 -- what sits under the note: odds + open + buy, or just buy
	UI.inspEyebrow.Position = UDim2.fromOffset(0, if c then 46 else 50)
	UI.inspName.Position = UDim2.fromOffset(0, nameY)
	UI.inspName.TextSize = if c then 22 else 30
	UI.inspName.Size = UDim2.new(1, 0, 0, if c then 30 else 38)
	UI.inspBlurb.Visible = not c
	-- (the blurb grows to fit its words, a finisher's long one too: AutomaticSize Y from a one-line floor)
	UI.inspBlurb.AutomaticSize = Enum.AutomaticSize.Y
	UI.inspBlurb.Size = UDim2.new(1, 0, 0, 18)
	UI.inspNote.Position = UDim2.new(0, 0, 1, -foot)
	UI.inspList.Position = UDim2.fromOffset(0, listY)
	UI.inspList.Size = UDim2.new(1, 0, 1, -(listY + foot + 26))
	UI.inspBar.Visible = false
	if o.type == "pass" then
		-- VIP: what's in the pack (each OWNED once you're VIP), the VIP room, and GET VIP
		UI.inspBlurb.Text = o.blurb
		for i, it in Shop.vipItems() do listRow(it, i, o) end
		local vip = isVip()
		UI.inspNote.Text = if vip then "you're VIP. the VIP room in the hub is open to you: see Trisangle daily" else "and the VIP room in the hub, with a daily reward"
		UI.inspBuy.set(if vip then "YOU'RE VIP"
			elseif Shop.free() then "GET VIP  ·  FREE WHILE TESTING"
			else "GET VIP  " .. ROBUX .. " " .. commas(o.robux), not vip and (Shop.free() or (Shop.ROBUX and (tonumber(Shop.VIP_PASS) or 0) > 0)))
	elseif o.type == "bundle" and o.set then
		-- a skin set: "complete the set". its five, each OWNED or not; how many you have; one button for the rest
		UI.inspBlurb.Text = o.blurb
		for i, it in o.items do listRow(it, i, o) end
		local miss = Till.missing(o)
		local have = #o.items - miss
		UI.inspNote.Text = have .. " / " .. #o.items .. " OWNED"
		UI.inspBar.Visible = true
		UI.inspBar.Position = UDim2.new(1, 0, 1, -(foot + 6))
		UI.inspFill.BackgroundColor3 = o.accent or T.ACCENT
		UI.inspFill.Size = UDim2.fromScale(if #o.items > 0 then have / #o.items else 0, 1)
		local price = bundlePrice(o, miss)
		local verb = if Shop.free() then "CLAIM" else "BUY"
		UI.inspBuy.set(if miss == 0 then "SET COMPLETE"
			elseif miss == #o.items then verb .. " THE SET  " .. priceText(price)
			else "COMPLETE THE SET  ·  " .. miss .. " LEFT  " .. priceText(price), miss > 0)
	elseif o.type == "bundle" then
		UI.inspBlurb.Text = o.blurb
		for i, it in o.items do listRow(it, i, o) end
		local miss = Till.missing(o)
		UI.inspNote.Text = string.format("worth %s %s one by one%s", ROBUX, commas(Shop.worth(o)), if miss > 0 and miss < #o.items then ". you already have " .. (#o.items - miss) else "")
		UI.inspBuy.set(if miss == 0 then "OWNED" elseif Shop.free() then "CLAIM  " .. priceText(o.robux) else "BUY  " .. priceText(o.robux), miss > 0)
	elseif isBox then
		UI.inspBlurb.Text = o.blurb
		local have = Till.count(o.id)
		local bs = Till.boxState(o.id)
		local n = S.count[o.id] or 1
		UI.inspNote.Text = if bs == "soon" then "nothing in it is on roblox yet" elseif have > 0 then "you have " .. have .. " to open" else "these are the odds for you, right now"
		UI.inspOpen.face.Visible = have > 0 and bs == nil
		UI.inspOpen.set("OPEN  x" .. math.min(n, math.max(have, 1)), have > 0 and bs == nil)
		if UI.inspOpen.face.Visible then UI.inspBuy.face.Position = UDim2.new(0.4, 4, 1, -48); UI.inspBuy.face.Size = UDim2.new(0.6, -4, 0, 48) end
		local word = if n > 1 then "  x" .. n else ""
		if bs == "soon" then UI.inspBuy.set("COMING SOON", false)
		elseif bs == "empty" then UI.inspBuy.set("YOU HAVE IT ALL", false)
		elseif S.restricted and not Shop.free() then if Purse.price(o.id) then UI.inspBuy.set("REDEEM", true) else UI.inspBuy.set("NOT AVAILABLE HERE", false) end
		else UI.inspBuy.set((if Shop.free() then "CLAIM" else "BUY") .. word .. "  " .. Purse.cost(o, n), true) end
		ShopUI.oddsRows(UI.inspList, o.id, 24)
	else
		local own = Till.owns(o.kind, o.item, o.weapon)
		local onSale = Shop.onSale(o.id)
		local wn = Shop.weaponName(o.weapon)
		local card = Shop.isCard(o.kind)
		local setName = nil
		if o.kind == "skin" then
			for _, so in Shop.sets do for _, it in so.items do if it.id == o.item then setName = so.name end end end
		end
		UI.inspBlurb.Text = if card then "a " .. string.lower(Shop.KIND_NAMES[o.kind] or "look") .. " for your player card. everyone who sees your card sees it."
			elseif o.kind == "kill" then "a kill effect: it plays on the body when you get a kill, with any gun. pick it in the loadout [L]."
			elseif o.kind == "emote" then "an emote for your wheel (hold T). put it on the wheel in the loadout [L]."
			elseif o.kind == "skin" then "a weapon skin for your " .. wn .. (if setName then ", from the " .. setName .. " set" else "") .. ". wear it from the loadout [L]."
			elseif o.kind == "hat" then "a hat for your " .. wn .. ". it goes on that gun only. wear it from the loadout [L]."
			else "a wrap for your " .. wn .. ". it paints that gun only. pick how much it covers in the loadout [L]."
		-- (the training hall's loadout lets you wear anything for a try: Loadout.luau's try layer)
		if not own and not card and not Shop.isFlair(o.kind) then UI.inspBlurb.Text ..= " try it on in the training hall first." end
		if S.finSkin then
			local _, row = Fin.of(S.finSkin)
			local fname = if type(row) == "table" and type(row.name) == "string" then row.name else "its own"
			UI.inspBlurb.Text ..= " it comes with a finisher, " .. fname .. ": a short cinematic when it lands the kill that wins a round or the match."
		end
		UI.inspNote.Text = if own then (if card then "it's yours. wear it on your player card."
				elseif Shop.isFlair(o.kind) then "it's yours. pick it in the loadout [L]."
				else "it's yours. wear it from the loadout [L].")
			elseif onSale then "in today's daily rotation" else "not in today's rotation"
		UI.inspBuy.set(if own then "OWNED" elseif not onSale then "NOT ON SALE TODAY" elseif Shop.free() then "CLAIM  " .. priceText(o.robux) else "BUY  " .. Purse.cost(o), not own and onSale)
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
-- BACK on the inspect panel. the shop opened straight onto this offer (a hub hologram, a link from another screen:
-- S.deep) goes away whole and you're back in the game (the owner, 16 Nov: "can it just take you back to the game?");
-- an offer you went into from the shop's own lists goes back to the list
function ShopUI.back()
	if S.deep and S.inspect == S.deep then ShopUI.close(); return end
	ShopUI.uninspect()
end
-- which overlay shows: the odds or confirm panel on top hides the inspect panel under it (its list drew through the
-- panel above it in a test), and the dim layer is up while any of them is
function ShopUI.layer()
	local top = UI.confirm.Visible or UI.odds.Visible
	UI.insp.Visible = S.inspect ~= nil and not top
	UI.dim.Visible = top or S.inspect ~= nil
	-- (and the page itself goes while a panel is up: a page's scrolling grid drew through the panel over it)
	UI.body.Visible = not UI.dim.Visible
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
	-- (it scrolls: the rarities, then every item with its chance)
	UI.oddsList = new("ScrollingFrame", { BackgroundTransparency = 1, BorderSizePixel = 0, Position = UDim2.fromOffset(22, 66), Size = UDim2.new(1, -44, 1, -162), ZIndex = 31,
		CanvasSize = UDim2.new(), AutomaticCanvasSize = Enum.AutomaticSize.Y, ScrollBarThickness = 4, ScrollingDirection = Enum.ScrollingDirection.Y }, UI.odds)
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
	-- every final outcome with its own chance, below the rarities (Roblox's rule for paid random items: all outcomes and
	-- their numerical odds, before anything is bought; one line per rarity and gun, whose items share a chance). 18 Nov
	local det = Shop.oddsDetail(cid, Till.ownedSets())
	if det and #det > 0 then
		local head = txt(UI.oddsList, "EVERY ITEM", 13, T.MUTED, T.FONT_BOLD)
		head.Size = UDim2.new(1, -6, 0, 26); head.LayoutOrder = 1000; head.ZIndex = 32
		for i, g in det do
			local where = if g.gun == "card" then "PLAYER CARD" elseif g.gun == "kill" then "KILL EFFECT" elseif g.gun == "emote" then "EMOTE"
				else string.upper(Shop.weaponName(g.gun))
			local l = txt(UI.oddsList, ("%s  ·  %s  ·  each item below: %s%%"):format(string.upper(g.name), where, Money.pct(g.each * 100)), 12, rarityColor(g.rarity), T.FONT_BOLD)
			l.Size = UDim2.new(1, -6, 0, 18); l.LayoutOrder = 1000 + i * 2; l.ZIndex = 32
			local b = txt(UI.oddsList, table.concat(g.items, ", "), 12, T.SOFT)
			b.TextWrapped = true; b.TextTruncate = Enum.TextTruncate.None; b.AutomaticSize = Enum.AutomaticSize.Y
			b.Size = UDim2.new(1, -6, 0, 0); b.LayoutOrder = 1001 + i * 2; b.ZIndex = 32
		end
		local note = txt(UI.oddsList, "Probabilities are rounded; the total of the displayed individual probabilities may not equal 100%.", 11, T.MUTED)
		note.TextWrapped = true; note.Size = UDim2.new(1, -6, 0, 30); note.LayoutOrder = 9999; note.ZIndex = 32
	end
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
	-- a container: REDEEM with Crate Tickets / Brass, a row over CANCEL and BUY (only with the quests' wallet)
	UI.cRedeem = {}
	for _, cur in { "tix", "brass" } do
		local b = button(UI.confirm, "", "dark", UDim2.new(0.5, -27, 0, 44), UDim2.new(0, 22, 1, -114))
		b.face.ZIndex = 41; b.face.TextSize = 14; b.face.Visible = false
		b.face.MouseButton1Click:Connect(function() if b.enabled then ShopUI.redeem(cur) end end)
		UI.cRedeem[cur] = b
	end
end
-- the REDEEM row for the container being confirmed: its prices, greyed where you're short. returns the height it adds
function Purse.row(cid: string, n: number): number
	local p = Purse.price(cid)
	local shown = {}
	-- (coins, where Roblox's policy keeps a player from paid random items: the option shows, greyed. 18 Nov)
	local all = if cid ~= "" and S.restricted and not Shop.coinsOnly() and Purse.remote() and Purse.has() then Shop.redeemPrice(cid) else nil
	for _, cur in { "tix", "brass" } do
		local b = UI.cRedeem[cur]
		local cost = p and (p :: any)[cur]
		local barred = cost == nil and cur == "brass" and all ~= nil and all.brass ~= nil
		b.face.Visible = cost ~= nil or barred
		if cost then
			b.set((if n > 1 then "REDEEM 1  ·  " else "REDEEM  ·  ") .. Purse.words(cur, cost), Purse.of(cur) >= cost)
			table.insert(shown, b)
		elseif barred then
			b.set("COINS  ·  NOT AVAILABLE HERE", false)
			table.insert(shown, b)
		end
	end
	for i, b in shown do
		if #shown == 1 then b.face.Position = UDim2.new(0, 22, 1, -114); b.face.Size = UDim2.new(1, -44, 0, 44)
		else b.face.Position = if i == 1 then UDim2.new(0, 22, 1, -114) else UDim2.new(0.5, 5, 1, -114); b.face.Size = UDim2.new(0.5, -27, 0, 44) end
	end
	return if #shown > 0 then 52 else 0
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
	if o.type == "pass" then ShopUI.getVip(); return end -- (VIP: its own claim, not the till)
	if o.type ~= "container" and Till.missing(o) == 0 then Hud.callout("ALREADY YOURS", 1); return end
	if o.type == "container" then
		local bs = Till.boxState(o.id)
		if bs == "soon" then Hud.callout("COMING SOON", 1); return end
		if bs == "empty" then Hud.callout("YOU HAVE EVERYTHING IN IT", 1.2); return end
		-- (where paid random items aren't allowed, a paid container isn't sold: PolicyService, the loot server's answer.
		-- it can still be redeemed with tickets, which are only earned; not with coins, which can be bought. 18 Nov)
		if S.restricted and not Shop.free() and not Purse.price(o.id) then Hud.callout("NOT AVAILABLE WHERE YOU ARE", 1.2); return end
	end
	if not Shop.onSale(id) then Hud.callout("NOT ON SALE TODAY", 1); return end
	-- with real Robux on, Roblox's own prompt is the confirm for a fixed item. a container always comes here first:
	-- the odds of a paid random item must be on screen before anything is charged
	if not Shop.free() and Shop.ROBUX and o.type ~= "container" and not Purse.coins(o) then ShopUI.prompt(o); return end
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
		local what = if o.set then (if miss == 1 then "weapon skin" else "weapon skins") else (if miss == 1 then "item" else "items")
		UI.cBody.Text = string.format("%d %s go%s into your inventory.", miss, what, if miss == 1 then "es" else "")
	else
		UI.cBody.Text = "this " .. string.lower(Shop.KIND_NAMES[o.kind] or "item") .. " goes into your inventory."
	end
	local price = if o.type == "bundle" then bundlePrice(o, Till.missing(o)) else o.robux * n
	if free then UI.cBody.Text ..= string.format('<br/><font color="%s">free while we test. later: %s %s</font>', T.hex(T.MUTED), ROBUX, commas(price)) end
	-- (a container: the REDEEM row, with the quests' wallet)
	h += Purse.row(if o.type == "container" then o.id else "", n)
	if o.type == "container" and S.restricted and not free then UI.cYes.set("NOT AVAILABLE HERE", false)
	elseif Purse.coins(o, n) then UI.cYes.set("BUY  " .. Purse.cost(o, n), canGo) -- (the coins-only shop)
	else UI.cYes.set(if free then (if n > 1 then "CLAIM  x" .. n else "CLAIM") else "BUY  " .. ROBUX .. " " .. commas(price), canGo) end
	UI.confirm.Size = UDim2.fromOffset(460, h)
	UI.confirm.Visible = true
	ShopUI.layer()
end
-- step two: the till. a container is opened at once (the loot module plays the opening); the rest just lands
function ShopUI.commit()
	local id = S.pending
	if type(id) == "string" and string.sub(id, 1, 5) == "deal:" then ShopUI.commitDeal(string.sub(id, 6)); return end -- (the owner's deals)
	local o = id and Shop.offer(id)
	local n = S.pendingN or 1
	if not UI.cYes.enabled then return end
	ShopUI.unconfirm()
	if not o or S.busy then return end
	if Purse.coins(o, n) then ShopUI.coinTill(o, n); return end -- (the coins-only shop: the server takes the coins)
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
	local cardOnly, flairOnly = true, true
	for _, it in Shop.contents(o) do
		if not Shop.isCard(it.kind) then cardOnly = false end
		if not Shop.isFlair(it.kind) then flairOnly = false end
	end
	ShopUI.toast(string.upper(if o.type == "single" then Shop.itemLabel({ kind = o.kind, id = o.item, weapon = o.weapon }) else o.name)
		.. (if cardOnly then " ADDED. WEAR IT ON YOUR PLAYER CARD" elseif flairOnly then " ADDED. PICK IT IN THE LOADOUT [L]" else " ADDED. WEAR IT FROM THE LOADOUT [L]"))
	ShopUI.refill()
end

-- REDEEM (from the confirm panel): the quests server takes the tickets or Brass and puts one container in stock
-- (Loot.grant, its own receipt id), then it opens from stock like any other
function ShopUI.redeem(cur: string)
	local id = S.pending
	local o = id and Shop.offer(id)
	if not o or o.type ~= "container" or S.busy then return end
	local p = Purse.price(o.id)
	local cost = p and (p :: any)[cur]
	local r = Purse.remote()
	if not cost or not r or Purse.of(cur) < cost then return end
	ShopUI.unconfirm()
	S.busy = true
	local ok, res = pcall(function() return (r :: RemoteFunction):InvokeServer("redeem", o.id, cur) end)
	S.busy = false
	if not ok or type(res) ~= "table" or res.ok ~= true then
		local why = if ok and type(res) == "table" and type(res.why) == "string" then res.why else "couldn't redeem it. try again"
		Hud.callout(string.upper(why), 1.6)
		return
	end
	play("click")
	Till.refresh()
	ShopUI.openBox(o.id, 1)
end

-- open a container you have: the till rolls it, the loot module's opening plays (the shop steps aside), and closing
-- the reveal goes straight back to the game (the owner, 17 Nov: "after opening chests it shouldnt take you back to your
-- inventory just back to the game"), wherever it was opened from
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
		local function ask(): any return if count > 1 then Till.ask("open", cid, count) else Till.ask("open", cid) end
		local res = ask()
		-- (the loot server takes a new open 1.2 s after the last at the soonest: OPEN ANOTHER can be quicker than that)
		if not res.ok and type(res.why) == "string" and string.find(res.why, "slow down", 1, true) then task.wait(1.3); res = ask() end
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
	-- (the opening has shown what you got: closing it takes you back to the game, not into the shop's inventory. only
	-- an open that never started (refused, nothing in stock) leaves you in the shop with its reason)
	if S.open and last then ShopUI.close() end
end
-- the loot server says what you own changed (another screen, the opening's EQUIP, a receipt): refresh what's shown
for _, a in { "LootOwned", "LootStock", "VIP" } do
	me:GetAttributeChangedSignal(a):Connect(function()
		if S.open and not S.busy then task.defer(function() Till.refresh(); ShopUI.refill() end) end
	end)
end
-- the quests' wallet changed: the header's numbers, the REDEEM buttons' grey, and the cards' prices when it first shows
for _, a in { "Brass", "CrateTickets" } do
	me:GetAttributeChangedSignal(a):Connect(function()
		if not S.open then return end
		task.defer(function()
			local was = UI.purse ~= nil and UI.purse.Visible
			Purse.draw()
			if not was then ShopUI.layout(); if S.tab == "containers" then ShopUI.refill() end end
			if UI.confirm.Visible and S.pending then
				local o = Shop.offer(S.pending)
				if o and o.type == "container" then Purse.row(o.id, S.pendingN or 1) end
			end
		end)
	end)
end

-- with real Robux on: the server checks the offer and shows Roblox's own purchase prompt; the receipt comes back
-- through ShopReceipts.server.luau, which has the loot server grant it
function ShopUI.prompt(o: any)
	local f = ReplicatedStorage:FindFirstChild("JankfireRemotes")
	local r = f and f:FindFirstChild("ShopBuy")
	if not Shop.ROBUX or not Shop.productFor(o, if o.set then Till.missing(o) else nil) or not (r and r:IsA("RemoteEvent")) then Hud.callout("NOT FOR SALE YET", 1.2); return end
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
				local wid = string.match(key, "^weapon:([%w_]+)$")
				local bid = string.match(key, "^coins:([%w_]+)$")
				if wid and (Shop.MONEY.weapons :: any)[wid] then (Shop.MONEY.weapons :: any)[wid].robux = price
				elseif bid then for _, b in Shop.MONEY.coins do if b.id == bid then b.robux = price end end
				elseif o then o.robux = price
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
	-- (five tabs since the owner's DEALS: a little narrower, so the FREE pill and CLOSE still fit beside them)
	local tabW = if compact then (if #TABS > 4 then 86 else 98) else (if #TABS > 4 then 108 else 116)
	local closeW = if compact then 84 else 112
	local walletW = if compact then 70 else 170
	local titleW = if compact then 78 else 190
	local tabsW = tabW * #TABS + 6 * (#TABS - 1)
	-- (the quests' Brass and tickets: on a phone they take the FREE pill's place, then the title goes if it must)
	local purse = Purse.has()
	if purse then Purse.draw() end
	local purseW = if compact and purse then Purse.width() + 4 else 0
	local showWallet = topW >= titleW + tabsW + walletW + closeW + 16 and not (compact and purse)
	local showPurse = purse and (not compact or topW >= tabsW + purseW + closeW + 16)
	local showTitle = topW >= titleW + tabsW + closeW + 8 + (if showPurse and compact then purseW + 8 else 0)
	UI.title.Visible = showTitle; UI.rule.Visible = showTitle
	UI.title.TextSize = if compact then 22 else 34
	UI.title.Position = UDim2.fromOffset(0, 0); UI.title.Size = UDim2.fromOffset(160, if compact then 28 else 40)
	UI.rule.Position = UDim2.fromOffset(2, if compact then 31 else 44)
	UI.sub.Visible = not compact
	UI.sub.Position = UDim2.fromOffset(2, 54); UI.sub.Size = UDim2.fromOffset(420, 18)
	UI.tabRow.Position = UDim2.fromOffset(if showTitle then titleW else 0, 0)
	UI.tabRow.Size = UDim2.fromOffset(tabsW, 44)
	for _, b in UI.tabs do b.face.Size = UDim2.fromOffset(tabW, 44); b.face.TextSize = if compact then (if #TABS > 4 then 13 else 14) else 15 end
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
	if UI.purse then
		UI.purse.Visible = showPurse
		UI.purse.AnchorPoint = Vector2.new(1, 0)
		if compact then
			-- (a pill like the FREE one, left of CLOSE)
			UI.purse.Position = UDim2.new(1, -(closeW + 8), 0, 0)
			UI.purse.Size = UDim2.fromOffset(0, 44)
			UI.purse.BackgroundTransparency = 0.1; UI.purseEdge.Enabled = true
			UI.pursePad.PaddingLeft = UDim.new(0, 12); UI.pursePad.PaddingRight = UDim.new(0, 12)
		else
			-- (a line under the pill and CLOSE, right-aligned)
			UI.purse.Position = UDim2.new(1, -2, 0, 52)
			UI.purse.Size = UDim2.fromOffset(0, 22)
			UI.purse.BackgroundTransparency = 1; UI.purseEdge.Enabled = false
			UI.pursePad.PaddingLeft = UDim.new(0, 0); UI.pursePad.PaddingRight = UDim.new(0, 0)
		end
	end
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
	-- the skin sets' banners: a row of two, as tall as fits the page (a phone shows one row and the start of the next)
	S.setH = if compact then math.min(196, bh - 40) else 250
	for _, r in UI.setRows:GetChildren() do if r:IsA("Frame") then r.Size = UDim2.new(1, 0, 0, S.setH) end end
	UI.vipHolder.Size = UDim2.new(1, 0, 0, if compact then math.min(184, bh - 40) else 230)
	-- inventory: small cards in each weapon's grid
	local icols = math.max(3, math.floor((bw + 10) / (if compact then 150 else 180)))
	local iw = math.floor((bw - 16 - (icols - 1) * 10) / icols)
	S.invCell = UDim2.fromOffset(iw, math.floor(iw * 1.12))
	for _, g in UI.invScroll:GetDescendants() do if g:IsA("UIGridLayout") then g.CellSize = S.invCell end end
	for _, b in UI.invBtns do b.face.Size = UDim2.fromOffset(0, if compact then 44 else 40); b.face.TextSize = if compact then 14 else 13 end
	for _, m in UI.invMins do m.MinSize = Vector2.new(if compact then 96 else 120, 0) end
	UI.invFilters.Size = UDim2.new(1, -120, 0, if compact then 46 else 42)
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
	UI.odds.Size = UDim2.fromOffset(if compact then 420 else 520, math.min(H - 16, 560))
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
	if not UI.pages[t] then t = "featured" end -- (a tab this shop doesn't have: a prompt made for a newer one)
	if S.tab ~= t then play("click"); ShopUI.shutOverlays() end -- (a new tab: whatever panel was up goes)
	S.tab = t
	for k, b in UI.tabs do b.pick(k == t) end
	for k, p in UI.pages do p.Visible = k == t end
	if t == "featured" then ShopUI.fillFeatured()
	elseif t == "bundles" then ShopUI.fillBundles()
	elseif t == "containers" then ShopUI.fillContainers()
	elseif t == "weapons" then ShopUI.fillWeapons()
	elseif t == "coins" then ShopUI.fillCoins()
	elseif t == "deals" then ShopUI.fillDeals()
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
	if MenuCursor.has("loadout") then return true end -- (the shop hides its screen while it's over it)
	local g = pg:FindFirstChild("JankLoadout")
	return g ~= nil and g:IsA("ScreenGui") and g.Enabled
end
-- while the shop is up it also raises LoadoutOpen: every script that holds still while a menu is up (no jumping,
-- shooting or items: Move, Arsenal, Utility, ShredderSlot) reads that one flag. the mouse is MenuCursor's ("shop")
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
	if not require(script.Parent:WaitForChild("MenuGate")).allowed("shop") then return end -- (no hub menus in a match or a map room: MenuGate, play-party-ranked's)
	local ok, why = ShopUI.canOpen()
	if not ok then if why then Hud.callout(why, 1.2) end; return end
	if id and not tab then
		local o = Shop.offer(id)
		tab = if o and o.type == "container" then "containers" elseif o and (o.type == "bundle" or o.type == "pass") then "bundles" else "featured"
	end
	-- (opened straight onto one offer from outside the shop: BACK and the end of an opening take you back to the
	-- game, not into the shop's lists. ShopUI.back, ShopUI.openBox)
	S.deep = if not S.open and id and Shop.offer(id) then id else nil
	if not S.open then
		S.open = true
		me:SetAttribute("ShopOpen", true)
		hold(true)
		MenuCursor.set("shop", true, function() return S.open end)
		UI.sub.Text = if Shop.free() then LINE else ""
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
	MenuCursor.set("shop", false)
	hold(false)
	S.inspect, S.pending, S.deep = nil, nil, nil
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
			if UI.dealsTimer then UI.dealsTimer.Text = "NEW IN " .. left end
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
