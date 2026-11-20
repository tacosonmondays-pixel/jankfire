-- THE OPENING (client): a Crate, Duffel Bag or Spray Can drops in front of you onto the ground with a weighty bounce
-- and the camera eases round to it; it rattles, the lid / zip / cap pops; a reel of cards spins over the blurred world
-- (CS:GO-style, ours: our cards, our timing), slows with a tick per card and lands on what you got; then the prize
-- rises out of the open container and turns in front of you, on your own gun for a wrap or a hat, with EQUIP, OPEN
-- ANOTHER and DONE. SKIP (space) jumps ahead: the drop and pop are cut, the reel lands at once.
-- the server rolls (Loot.luau); this only shows what it said. the shop calls it:
--   local res = Loot:InvokeServer("open", kind)        -- kind = "crate" | "bag" | "spray"
--   if res.ok then local how = LootOpening.play(kind, res, { quick = false, again = true }) end
-- play() YIELDS until the player closes the reveal and returns "done" or "again" (OPEN ANOTHER). LootOpening.busy().
-- several at once (Loot "open", kind, 5 or 10: res.prizes): they drop round you at full size (a half ring in front for
-- five, a ring all round for ten: Shared.LootFloor.layout), the camera backs up and off to see them all, each pops in
-- turn with a quick reel and its prize comes up over it; then a grid of everything, rarest first, each with EQUIP.
-- Opening.show(data) draws someone ELSE's opening for a bystander (the LootShow event: the same ring, the pops, every
-- prize over its container with a sign; no reel).
-- it takes the camera and hides every other ScreenGui while it runs, and gives both back as they were.
-- the containers are ReplicatedStorage.JankfireLoot.<kind> (Blender, tools/roblox/loot_models.py, PolishBackup.LootImport);
-- a plain stand-in is built here if they aren't there. look: Theme.luau (dark cards, one amber accent), rarity colours
-- from Shared.LootTable (muted).
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UIS = game:GetService("UserInputService")
local ContextActionService = game:GetService("ContextActionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local LootTable = require(Shared:WaitForChild("LootTable"))
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor")) :: any
local LootFloor = require(Shared:WaitForChild("LootFloor"))
local Roster = require(Shared:WaitForChild("Roster"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local GunHats = require(Shared:WaitForChild("GunHats"))
local GunHatData = require(Shared:WaitForChild("GunHatData")) :: any
local T = require(script.Parent:WaitForChild("Theme"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local me = Players.LocalPlayer
local new = T.new
local WHITE = Color3.new(1, 1, 1)

local Opening = {}
local running = false
local current: any = nil -- (the opening that is playing: finish() reaches it)
function Opening.busy(): boolean return running end
-- (play() takes a function that asks the server instead of its answer: the container drops at once, 19 Nov)
Opening.ASYNC = true
-- (19 Nov: how long each part of an opening takes, from the OPEN press, for the owner's "opening crates and stuff is
-- still really slow": marks on the player's attribute LootTiming, "name=seconds" each, as they happen)
local Timing = { t0 = 0, list = {} :: { string } }
function Timing.start(t0: number?)
	Timing.t0 = t0 or os.clock()
	table.clear(Timing.list)
end
function Timing.mark(name: string)
	table.insert(Timing.list, ("%s=%.2f"):format(name, os.clock() - Timing.t0))
	me:SetAttribute("LootTiming", table.concat(Timing.list, " "))
end
Opening.Timing = Timing
-- end the opening from outside (the shop closing, a test): it skips to the end and play() returns `answer` ("done")
function Opening.finish(answer: string?)
	if current then current.result = answer or "done"; current.skip = true end
end
-- SKIP from outside (a test): what SPACE does
function Opening.skip()
	if current then current.skip = true end
end

-- ---------------------------------------------------------------- timing (seconds)
-- (19 Nov, the owner: "opening crates and stuff is still really slow": about 3.5 s from the press to the landing, was
-- about 10. the container drops the moment you press, while the server decides)
local TIME = {
	fall = 0.3, bounce = 0.32, rattle = 0.25, pop = 0.3, -- the container (the rattle: at least this, and while the answer comes)
	spin = 2.4, spinQuick = 1.0, -- the reel
	land = 0.45, -- the winning card's moment before the reveal
	rise = 0.5, -- the prize coming up out of the container
	camIn = 0.45, -- the camera coming round to the container
	wait = 10, -- the longest the rattle waits for the server's answer
	prep = 0.6, -- the longest it waits for the reel's pictures to load once they are built
}
local ContentProvider = game:GetService("ContentProvider")
-- QUICK OPEN (the opening screen's switch, remembered in your settings as "loot.quick"): no reel, the prize comes
-- straight up with its rarity's flash
local settingsMod: any = false
local function settings(): any
	if settingsMod == false then
		settingsMod = nil
		local m = script.Parent:FindFirstChild("Settings")
		if m and m:IsA("ModuleScript") then
			local ok, s = pcall(require, m)
			if ok and type(s) == "table" and type(s.get) == "function" then settingsMod = s end
		end
	end
	return settingsMod
end
local function quickOn(): boolean
	local s = settings()
	return s ~= nil and s.get("loot.quick") == true
end
local CARD_W, CARD_H, GAP = 176, 212, 12
local STEP = CARD_W + GAP

-- ---------------------------------------------------------------- little helpers
local function tw(o: Instance, t: number, props: { [string]: any }, style: Enum.EasingStyle?, dir: Enum.EasingDirection?): Tween
	local x = TweenService:Create(o, TweenInfo.new(t, style or Enum.EasingStyle.Quad, dir or Enum.EasingDirection.Out), props)
	x:Play()
	return x
end
local function rcol(r: string): Color3
	local e = LootTable.RARITY[r]
	return if e then e.color else T.MUTED
end
local function rname(r: string): string
	local e = LootTable.RARITY[r]
	return string.upper(if e then e.name else r)
end
-- the first of these sounds that has been uploaded (new loot sounds first, old ones as stand-ins)
local function snd(names: { string }, at: Vector3?, vol: number?, pitch: number?)
	local lib = ReplicatedStorage:FindFirstChild("JankfireSounds")
	for _, n in names do
		local s = lib and lib:FindFirstChild(n)
		if s and s:IsA("Sound") and s.SoundId ~= "" then pcall(Sfx.play, n, at, vol, pitch); return end
	end
end
local function easeOut(u: number, p: number): number u = math.clamp(u, 0, 1); return 1 - (1 - u) ^ p end
local function smooth(u: number): number u = math.clamp(u, 0, 1); return u * u * (3 - 2 * u) end

-- ---------------------------------------------------------------- the container (the Blender model, or a stand-in)
local STAND_IN = {
	crate = { size = Vector3.new(3.6, 2.2, 2.4), body = Color3.fromRGB(70, 75, 86), trim = Color3.fromRGB(46, 50, 58), accent = T.ACCENT },
	bag = { size = Vector3.new(3.8, 1.7, 1.8), body = Color3.fromRGB(86, 90, 74), trim = Color3.fromRGB(44, 46, 40), accent = T.ACCENT },
	spray = { size = Vector3.new(1.4, 3.2, 1.4), body = Color3.fromRGB(214, 218, 224), trim = Color3.fromRGB(60, 64, 72), accent = T.ACCENT },
}
local function part(m: Instance, name: string, size: Vector3, cf: CFrame, color: Color3, mat: Enum.Material?): Part
	return new("Part", { Name = name, Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = true,
		Size = size, CFrame = cf, Color = color, Material = mat or Enum.Material.SmoothPlastic,
		TopSurface = Enum.SurfaceType.Smooth, BottomSurface = Enum.SurfaceType.Smooth }, m)
end
local function standIn(kind: string): Model
	local d = STAND_IN[kind] or STAND_IN.crate
	local m = Instance.new("Model")
	m.Name = kind
	local s = d.size
	local lidH = if kind == "spray" then 0.7 else 0.35
	local body = part(m, "body", Vector3.new(s.X, s.Y - lidH, s.Z), CFrame.new(0, (s.Y - lidH) / 2, 0), d.body)
	part(m, "band", Vector3.new(s.X + 0.06, 0.22, s.Z + 0.06), CFrame.new(0, (s.Y - lidH) * 0.45, 0), d.trim)
	local lid = Instance.new("Model")
	lid.Name = if kind == "spray" then "Cap" elseif kind == "bag" then "Flap" else "Lid"
	local lp = part(lid, "lid", Vector3.new(s.X + 0.08, lidH, s.Z + 0.08), CFrame.new(0, s.Y - lidH / 2, 0), d.trim)
	part(lid, "latch", Vector3.new(0.5, 0.18, 0.12), CFrame.new(0, s.Y - lidH - 0.05, -s.Z / 2 - 0.08), d.accent)
	lid.PrimaryPart = lp
	lid:SetAttribute("Hinge", CFrame.new(0, s.Y - lidH / 2, s.Z / 2 + 0.04))
	lid.Parent = m
	local glow = part(m, "glow", Vector3.new(s.X * 0.9, 0.06, s.Z * 0.9), CFrame.new(0, s.Y - lidH - 0.02, 0), WHITE, Enum.Material.Neon)
	glow.Transparency = 1
	m.PrimaryPart = body
	m.WorldPivot = CFrame.identity
	m:SetAttribute("Height", s.Y)
	m:SetAttribute("Open", if kind == "spray" then "pop" elseif kind == "bag" then "flap" else "hinge")
	return m
end
-- a copy of the container, its pivot at the middle of its bottom face, every part quiet, at its shown size
-- (Shared.LootFloor.SIZE: bigger than the model, the owner's "can the bags be larger?") times k
local function container(kind: string, k: number?): Model
	local lib = ReplicatedStorage:FindFirstChild("JankfireLoot")
	local t = lib and lib:FindFirstChild(kind)
	local m = if t and t:IsA("Model") then t:Clone() else standIn(kind)
	local low = math.huge
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false
			if d.Name == "glow" then d.Transparency = 1 end -- (the light inside: on at the pop)
			local cf, sz = d.CFrame, d.Size
			low = math.min(low, cf.Position.Y - (math.abs(cf.RightVector.Y) * sz.X + math.abs(cf.UpVector.Y) * sz.Y + math.abs(cf.LookVector.Y) * sz.Z) / 2)
		end
	end
	-- the pivot is the middle of the bottom face (where it stands on the floor), set here on every copy: a Model's
	-- WorldPivot doesn't stick once it has a PrimaryPart, and the templates' pivots were their body's centre (the crate's
	-- ~1 stud up), so every container used to stand that far INTO the floor. (the template sits at its file's origin:
	-- x and z of the pivot are 0 there; the hinges in openBox are written in that frame)
	if low < math.huge then
		local cf = m:GetBoundingBox()
		local x = if math.abs(cf.Position.X) < 0.5 then 0 else cf.Position.X
		local z = if math.abs(cf.Position.Z) < 0.5 then 0 else cf.Position.Z
		local bottom = CFrame.new(x, low, z)
		local pp = m.PrimaryPart
		if pp then pp.PivotOffset = pp.CFrame:ToObjectSpace(bottom) else m.WorldPivot = bottom end
	end
	local size = (LootFloor.SIZE[kind] or 1) * (k or 1)
	if math.abs(size - 1) > 1e-3 then pcall(function() m:ScaleTo(m:GetScale() * size) end) end
	return m
end
-- how tall a container stands, shut (its Height at size 1, times the size it's shown at)
local function heightOf(m: Model): number
	return ((m:GetAttribute("Height") :: number?) or 2.4) * m:GetScale()
end

-- ---------------------------------------------------------------- the prize models
-- which of your weapons wears the prize in the reveal: the one in your hands, else your primary (a hat: one that has a
-- seat for it)
local function loadoutIds(): { string }
	local out = {}
	for _, a in { "Loadout", "LoadoutNext" } do
		local s = me:GetAttribute(a)
		if type(s) == "string" then for id in string.gmatch(s, "[^,]+") do if not table.find(out, id) then table.insert(out, id) end end end
	end
	for _, id in { "ar", "redline", "katana" } do if not table.find(out, id) then table.insert(out, id) end end
	return out
end
local function showWeapon(item: any): string?
	-- (a wrap or a hat is won for one gun: that's the one it's shown on)
	local own = item.weapon and Roster.byId[item.weapon]
	if own and own.live and own.slot ~= "utility" then return item.weapon end
	local held = me:GetAttribute("Held")
	local list = loadoutIds()
	if type(held) == "string" then table.insert(list, 1, held) end
	for _, id in list do
		local e = Roster.byId[id]
		if e and e.live and e.slot ~= "utility" and id ~= "shredder" then
			if item.type ~= "hat" or GunHatData.SPOTS == nil or GunHatData.SPOTS[id] ~= nil then return id end
		end
	end
	return "ar"
end
-- ONE SCALE FOR EVERY GUN (the owner, 16 Nov: "when opening chests, make sure the weapons are scaled properly when
-- displayed!"): a gun shown in an opening is built at its true size, like in the game, and every gun is then shown at
-- the same scale, so a pistol reads smaller than a sniper. the scale puts the assault rifle at 4.6 studs long (what
-- every prize used to be fitted to); a ring of them may all be smaller together, never one alone
local displayK: number? = nil
local function gunScale(): number -- (studs per metre for show)
	if displayK then return displayK end
	local k = 5
	local ok, m = pcall(WeaponModels.build, "ar", 1)
	if ok and m then
		local _, size = m:GetBoundingBox()
		local long = math.max(size.X, size.Y, size.Z)
		if long > 0.05 then k = 4.6 / long end
		m:Destroy()
	end
	displayK = k
	return k
end
-- a prize model (built at 3 studs a metre) shown at k studs a metre
local function showAt(m: Model, k: number)
	pcall(function() m:ScaleTo(m:GetScale() * (k / 3)) end)
end
-- the Shredder isn't a built gun: it's its tool (ReplicatedStorage.JankfireTools.Shredder, or "Shredder@<skin>"), made
-- at the hands' scale (TOOL_K studs a metre, as a gun in third person: 3 x 1.5); copied without its suck field
local TOOL_K = 4.5
local QUIET = { "Sound", "ParticleEmitter", "Light", "Beam", "Trail", "LuaSourceContainer", "ProximityPrompt", "BillboardGui",
	"SurfaceGui", "ClickDetector", "Smoke", "Fire", "Sparkles", "Weld", "WeldConstraint", "Motor6D", "Attachment" }
local function toolGun(skin: string?): Model?
	local tools = ReplicatedStorage:FindFirstChild("JankfireTools")
	local src = tools and ((skin and tools:FindFirstChild("Shredder@" .. skin)) or tools:FindFirstChild("Shredder"))
	if not src then return nil end
	local m = Instance.new("Model")
	m.Name = "shredder"
	local big: BasePart? = nil
	for _, d in src:GetDescendants() do
		if d:IsA("BasePart") and d.Transparency < 0.99 and d.Name ~= "SuckField" then
			local c = d:Clone()
			for _, x in c:GetChildren() do
				for _, q in QUIET do if x:IsA(q) then x:Destroy(); break end end
			end
			c.Parent = m
			if not big or c.Size.Magnitude > big.Size.Magnitude then big = c end
		end
	end
	if not big then m:Destroy(); return nil end
	m.PrimaryPart = big
	pcall(function() m:ScaleTo(3 / TOOL_K) end) -- (to 3 studs a metre, like the built guns)
	return m
end
-- a gun-less prize (a kill effect, an emote, a player card's look): a flat dark tile with its module's picture on both
-- faces, built at 3 studs a metre like the guns, 0.6 m wide and 0.75 m tall (half a rifle's length: at 1 m it filled
-- the bag's mouth). its faces are its X sides: it turns to the camera as a gun turned side-on does
local TILE_M = Vector2.new(0.6, 0.75)
local function tileModel(item: any): Model
	local cm = LootTable.hookFor(item.type)
	local m = Instance.new("Model")
	m.Name = "PrizeTile"
	local p = new("Part", { Name = "Tile", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = false,
		Material = Enum.Material.SmoothPlastic, Color = T.CARD, Size = Vector3.new(0.18, TILE_M.Y * 3, TILE_M.X * 3) }, m)
	m.PrimaryPart = p
	for _, face in { Enum.NormalId.Right, Enum.NormalId.Left } do
		local sg = new("SurfaceGui", { Face = face, SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud, PixelsPerStud = 64,
			LightInfluence = 0, Brightness = 1.1, ClipsDescendants = true }, p)
		local f = new("Frame", { BackgroundColor3 = T.CARD, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, sg)
		if cm and type(cm.picture) == "function" then pcall(cm.picture, item.type, item.id, f) end
	end
	return m
end
-- the weapon wearing the prize, at its true size (3 studs a metre: call showAt to show it), pivot at its middle;
-- returns the model, the weapon id and its length in metres (a gun-less prize: its tile, no weapon)
local function prizeModel(item: any): (Model?, string?, number)
	local wid: string?
	local m: Model?
	if LootTable.hookFor(item.type) then
		local tm = tileModel(item)
		local cf, sz = tm:GetBoundingBox()
		tm.WorldPivot = cf
		return tm, nil, math.max(sz.X, sz.Y, sz.Z) / 3
	end
	if item.type == "skin" then
		wid = (LootTable.SKINS[item.id] or {})[3]
		if wid == "shredder" then m = toolGun(item.id)
		elseif wid then m = WeaponModels.build(wid, 3, item.id) end
		-- (a high-tier skin wears its own effects here too: SkinSets.FX, played by Fx.skinIdle)
		local spec = LootTable.skinFx(item.id)
		local fxm = script.Parent:FindFirstChild("Fx")
		if m and spec and fxm then
			local okF, Fx = pcall(require, fxm)
			if okF and type(Fx) == "table" and type((Fx :: any).skinIdle) == "function" then pcall((Fx :: any).skinIdle, m, 3, spec) end
		end
		if not m then
			-- (no build for it: its template, at its true length (its file bounds are in metres))
			local lib = ReplicatedStorage:FindFirstChild("JankfireSkins")
			local t = lib and lib:FindFirstChild(item.id)
			local lo, hi = t and t:GetAttribute("FileLo"), t and t:GetAttribute("FileHi")
			if t and t:IsA("Model") and typeof(lo) == "Vector3" and typeof(hi) == "Vector3" then
				local c = t:Clone()
				local _, ts = c:GetBoundingBox()
				local long = math.max(ts.X, ts.Y, ts.Z)
				local d = hi - lo
				local want = math.max(d.X, d.Y, d.Z) * 3
				if long > 1e-3 and want > 1e-3 then
					pcall(function() c:ScaleTo(c:GetScale() * (want / long)) end)
					m = c
				else
					c:Destroy()
				end
			end
		end
	else
		wid = showWeapon(item)
		m = if wid == "shredder" then toolGun(nil) else WeaponModels.build(wid :: string, 3)
	end
	if not m then return nil, wid, 1 end
	local parts = 0
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false
			parts += 1
		elseif d:IsA("Trail") or d:IsA("Beam") then
			d:Destroy() -- (a swing's trail on a blade that turns draws a big smear)
		end
	end
	if parts == 0 then m:Destroy(); return nil, wid, 1 end
	if item.type == "wrap" then
		pcall(WeaponModels.wrap, m, item.id, "full")
	end
	local _, size = m:GetBoundingBox()
	if item.type == "hat" and wid then
		-- (bigger than in the hand: it's the star here)
		if wid == "shredder" then
			local tools = ReplicatedStorage:FindFirstChild("JankfireTools")
			local tool = tools and tools:FindFirstChild("Shredder")
			if tool and type((GunHats :: any).attachToolCopy) == "function" then pcall((GunHats :: any).attachToolCopy, m, tool, item.id) end
		else
			pcall(GunHats.attach, m, wid, item.id, 3, true, 2.4)
		end
	end
	local long = math.max(size.X, size.Y, size.Z)
	local cf = m:GetBoundingBox()
	m.WorldPivot = cf
	return m, wid, long / 3
end

-- ---------------------------------------------------------------- card pictures
local function wrapPicture(parent: GuiObject, id: string)
	local lib = ReplicatedStorage:FindFirstChild("JankfireWraps")
	local sa = lib and lib:FindFirstChild(id)
	local img = nil
	if sa and sa:IsA("SurfaceAppearance") then
		local ok, v = pcall(function() return (sa :: any).ColorMap end)
		if ok and type(v) == "string" and v ~= "" then img = v end
	end
	if img then
		new("ImageLabel", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Image = img, ScaleType = Enum.ScaleType.Tile,
			TileSize = UDim2.fromOffset(120, 120) }, parent)
		return
	end
	-- a colour wrap: its palette as bands (as the loadout's chips draw it)
	local w = Roster.wrapById[id]
	local pal = if w and #w.pal > 0 then w.pal else { Color3.fromRGB(120, 124, 132) }
	local f = new("Frame", { BackgroundColor3 = WHITE, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, parent)
	if #pal == 1 then f.BackgroundColor3 = pal[1]; return end
	local kp = {}
	local n = if w and w.pat == "fade" then #pal else 6
	for i = 1, n do
		local c = pal[(i - 1) % #pal + 1]
		if w and w.pat == "fade" then
			table.insert(kp, ColorSequenceKeypoint.new((i - 1) / (n - 1), c))
		else
			local a, b = (i - 1) / n, i / n
			table.insert(kp, ColorSequenceKeypoint.new(if i == 1 then 0 else a + 0.001, c))
			table.insert(kp, ColorSequenceKeypoint.new(if i == n then 1 else b, c))
		end
	end
	new("UIGradient", { Color = ColorSequence.new(kp), Rotation = if w and w.pat == "fade" then 0 else 55 }, f)
end
local function modelPicture(parent: GuiObject, m: Model?, fixedR: number?)
	if not m then return end
	local vp = new("ViewportFrame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Ambient = Color3.fromRGB(150, 153, 162),
		LightColor = Color3.fromRGB(255, 248, 240), LightDirection = Vector3.new(-0.5, -1, -0.7) }, parent)
	local cam = new("Camera", { FieldOfView = 30 }, vp)
	vp.CurrentCamera = cam
	for _, d in m:GetDescendants() do if d:IsA("BasePart") then d.Anchored = true end end
	m.Parent = vp
	local cf, size = m:GetBoundingBox()
	-- (fixedR: every gun seen from one distance; one bigger than that is seen whole)
	local r = if fixedR then math.max(fixedR, size.Magnitude / 2 * 0.92) else size.Magnitude / 2
	local dir = (Vector3.new(0.8, 0.5, -1)).Unit
	cam.CFrame = CFrame.lookAt(cf.Position + dir * (r / math.tan(math.rad(15)) * 1.05), cf.Position)
end
-- Brass (the quests session's currency): its own icon (QuestUI.icon), else a plain brass disc. size in the card's pixels
local questUi: any = false
local function brassPicture(parent: GuiObject, size: number)
	if questUi == false then
		questUi = nil
		local m = script.Parent:FindFirstChild("QuestUI")
		if m and m:IsA("ModuleScript") then
			local ok, q = pcall(require, m)
			if ok and type(q) == "table" and type(q.icon) == "function" then questUi = q end
		end
	end
	local ok, f = false, nil
	if questUi then ok, f = pcall(questUi.icon, "brass", parent, size) end
	if ok and typeof(f) == "Instance" and f:IsA("GuiObject") then
		f.AnchorPoint = Vector2.new(0.5, 0.5)
		f.Position = UDim2.fromScale(0.5, 0.5)
		f.Parent = parent
	else
		local c = new("Frame", { BackgroundColor3 = Color3.fromRGB(196, 156, 82), BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
			Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(size, size) }, parent)
		T.corner(c, 999)
	end
end
-- a container (a reward can be one): its model, the same one that drops in an opening
local boxPics: { [string]: Model } = {}
local function containerPicture(parent: GuiObject, kind: string)
	if not LootTable.CONTAINERS[kind] then return end
	local t = boxPics[kind]
	if not t then t = container(kind); boxPics[kind] = t end
	modelPicture(parent, t:Clone())
end
local skinPics: { [string]: any } = {}
local function cardPicture(parent: GuiObject, item: any)
	if item.type == "brass" then brassPicture(parent, math.floor(math.min(CARD_W - 16, CARD_H - 72) * 0.58))
	elseif item.type == "container" then containerPicture(parent, item.id)
	elseif item.type == "wrap" then wrapPicture(parent, item.id)
	elseif item.type == "hat" then
		local t = GunHats.template(item.id)
		modelPicture(parent, if t then t:Clone() else nil)
	elseif item.type == "skin" then
		-- (built at its true size, 1 stud a metre, once per skin; every gun from the same distance, so a pistol is small
		-- in its card and a sniper fills it)
		local m = skinPics[item.id]
		local wid = (LootTable.SKINS[item.id] or {})[3]
		if m == nil and wid == "shredder" then
			-- (the Shredder is its tool: at 3 studs a metre from toolGun, made 1 here like the rest)
			local okT, tg = pcall(toolGun, item.id)
			if okT and tg then pcall(function() tg:ScaleTo(tg:GetScale() / 3) end) end
			m = if okT and tg then tg else nil
			skinPics[item.id] = m or false
		end
		if m == nil and wid then
			local ok, b = pcall(WeaponModels.build, wid, 1, item.id)
			if ok and b and b:GetAttribute("Skin") == item.id then
				for _, d in b:GetDescendants() do
					if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
					if d:IsA("ParticleEmitter") or d:IsA("Light") then d:Destroy() end
				end
				m = b
			elseif ok and b then
				b:Destroy()
			end
			skinPics[item.id] = m or false
		end
		if m then
			modelPicture(parent, (m :: Model):Clone(), 0.78)
		else
			local lib = ReplicatedStorage:FindFirstChild("JankfireSkins")
			local t = lib and lib:FindFirstChild(item.id)
			modelPicture(parent, if t and t:IsA("Model") then t:Clone() else nil)
		end
	else
		-- (a player card's look, a kill effect, an emote: its own module draws it, if it can)
		local cm = LootTable.hookFor(item.type)
		if cm and type(cm.picture) == "function" then pcall(cm.picture, item.type, item.id, parent) end
	end
end

-- one card of the reel: a dark plate, the picture, a soft wash of the rarity colour from the bottom, the name, a bar
local function card(parent: Instance, item: any, x: number): Frame
	local c = new("Frame", { Name = "Card", BackgroundColor3 = T.CARD, BorderSizePixel = 0, Position = UDim2.fromOffset(x, 0),
		Size = UDim2.fromOffset(CARD_W, CARD_H) }, parent)
	T.corner(c, 6)
	T.edge(c)
	local col = rcol(item.rarity)
	local pic = new("Frame", { Name = "Pic", BackgroundColor3 = Color3.fromRGB(20, 22, 27), BorderSizePixel = 0, Position = UDim2.fromOffset(8, 8),
		Size = UDim2.fromOffset(CARD_W - 16, CARD_H - 72), ClipsDescendants = true }, c)
	T.corner(pic, 4)
	local wash = new("Frame", { Name = "Wash", BackgroundColor3 = col, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = 3 }, pic)
	new("UIGradient", { Rotation = -90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(0.45, 1), NumberSequenceKeypoint.new(1, 1) }) }, wash)
	cardPicture(pic, item)
	if item.type == "skin" then
		local tier, tname = LootTable.tier(item.id)
		if tier then
			local badge = new("TextLabel", { Name = "Tier", BackgroundColor3 = T.BG, BackgroundTransparency = 0.15, BorderSizePixel = 0,
				Position = UDim2.fromOffset(14, 14), Size = UDim2.fromOffset(0, 18), AutomaticSize = Enum.AutomaticSize.X,
				FontFace = T.FONT_BOLD, TextSize = 11, Text = string.upper(tname :: string) .. " TIER",
				TextColor3 = if tier == "high" then T.ACCENT else T.SOFT, ZIndex = 7 }, c)
			new("UIPadding", { PaddingLeft = UDim.new(0, 6), PaddingRight = UDim.new(0, 6) }, badge)
			T.corner(badge, 4)
		end
	end
	local nm = new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromOffset(10, CARD_H - 60), Size = UDim2.fromOffset(CARD_W - 20, 24),
		FontFace = T.FONT_BOLD, TextSize = 17, Text = item.name or item.id, TextColor3 = T.TEXT, TextXAlignment = Enum.TextXAlignment.Left,
		TextTruncate = Enum.TextTruncate.AtEnd }, c)
	nm.Name = "Name"
	new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromOffset(10, CARD_H - 36), Size = UDim2.fromOffset(CARD_W - 20, 18),
		FontFace = T.FONT, TextSize = 13, TextTruncate = Enum.TextTruncate.AtEnd,
		Text = (if item.weapon and Roster.byId[item.weapon] then string.upper(Roster.byId[item.weapon].name)
			elseif LootTable.cardLook(item.type) then "PLAYER CARD"
			else string.upper(LootTable.TYPE_NAMES[item.type] or item.type)) .. "  ·  " .. rname(item.rarity),
		TextColor3 = T.MUTED, TextXAlignment = Enum.TextXAlignment.Left }, c)
	local bar = new("Frame", { Name = "Bar", BackgroundColor3 = col, BorderSizePixel = 0, AnchorPoint = Vector2.new(0, 1),
		Position = UDim2.new(0, 0, 1, 0), Size = UDim2.new(1, 0, 0, 5), ZIndex = 2 }, c)
	T.corner(bar, 2)
	new("Frame", { Name = "Dim", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 1, BorderSizePixel = 0,
		Size = UDim2.fromScale(1, 1), ZIndex = 8 }, c)
	return c
end

-- ---------------------------------------------------------------- the screen
local function button(parent: Instance, text: string, main: boolean, pos: UDim2, size: UDim2): TextButton
	local b = new("TextButton", { AutoButtonColor = false, BackgroundColor3 = if main then T.ACCENT else T.CARD, BorderSizePixel = 0,
		Position = pos, Size = size, FontFace = T.FONT_BOLD, TextSize = math.floor(size.Y.Offset * 0.36), Text = text,
		TextColor3 = if main then T.INK else T.TEXT, ZIndex = 20 }, parent)
	T.corner(b)
	if not main then T.edge(b) end
	local base = b.BackgroundColor3
	b.MouseEnter:Connect(function() b.BackgroundColor3 = base:Lerp(WHITE, 0.14) end)
	b.MouseLeave:Connect(function() b.BackgroundColor3 = base end)
	return b
end

type Ui = { gui: ScreenGui, box: Frame, stage: Frame, scale: UIScale, head: Frame, headScale: UIScale, title: TextLabel,
	odds: TextLabel, skip: TextButton, skipScale: UIScale, reel: CanvasGroup, reelScale: UIScale, reelLow: number, strip: Frame,
	marker: Frame, flash: Frame, reveal: Frame, revealScale: UIScale, rName: TextLabel, rKind: TextLabel, rOn: TextLabel,
	equip: TextButton, again: TextButton, done: TextButton, s: number, b: number, wide: number, quick: TextButton, quickScale: UIScale }
-- a legendary prize's fire along the bottom of the screen, under the reveal (UiParticles.fireStrip in its rarity colour;
-- the VFX session, 20 Nov: main for the owner, "2D fire, smoke and embers" on the best reveals). nil when the module is
-- missing; the caller stops it as the reveal goes away
local UiP: any = nil
do
	local m = script.Parent:FindFirstChild("UiParticles")
	if m and m:IsA("ModuleScript") then
		local ok, M = pcall(require, m)
		if ok then UiP = M end
	end
end
local function revealFire(gui: ScreenGui, col: Color3): any
	if not UiP then return nil end
	local fr = gui:FindFirstChild("RevealFire") :: Frame?
	if not fr then
		fr = new("Frame", { Name = "RevealFire", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0, 1), Position = UDim2.fromScale(0, 1),
			Size = UDim2.fromScale(1, 0.34), ZIndex = 1 }, gui)
	end
	local ok, h = pcall(UiP.fireStrip, fr, col)
	return if ok then h else nil
end
local function fireOut(h: any)
	if h then pcall(function() h:stop() end); task.delay(2.6, function() pcall(function() h:destroy() end) end) end
end
local function buildUi(): Ui
	local pg = me:WaitForChild("PlayerGui")
	-- (the stage keeps to the device's safe area, away from a phone's notch and corners; the dark bands, the flash and
	-- the click catcher reach past it to the screen's edges)
	local gui = new("ScreenGui", { Name = "JankLootOpening", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 60,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = true, ScreenInsets = Enum.ScreenInsets.DeviceSafeInsets,
		ClipToDeviceSafeArea = false }, pg)
	local PAST = 400 -- (pixels of screen past the safe area on every side: more than any notch)
	-- (Modal frees the mouse from first person while it's up, and the button eats clicks on the world)
	new("TextButton", { Name = "Catcher", Text = "", AutoButtonColor = false, BackgroundTransparency = 1, Position = UDim2.fromOffset(-PAST, -PAST),
		Size = UDim2.new(1, PAST * 2, 1, PAST * 2), Modal = true }, gui)
	local flash = new("Frame", { Name = "Flash", BackgroundColor3 = WHITE, BackgroundTransparency = 1, BorderSizePixel = 0,
		Position = UDim2.fromOffset(-PAST, -PAST), Size = UDim2.new(1, PAST * 2, 1, PAST * 2), ZIndex = 1 }, gui)
	-- (a soft dark band at the top and the bottom so the words read over any room)
	local shadeTop = new("Frame", { Name = "ShadeTop", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0, BorderSizePixel = 0,
		Position = UDim2.fromOffset(-PAST, -PAST), Size = UDim2.new(1, PAST * 2, 0.22, PAST), ZIndex = 1 }, gui)
	new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.35), NumberSequenceKeypoint.new(1, 1) }) }, shadeTop)
	local shadeBot = new("Frame", { Name = "ShadeBot", BackgroundColor3 = Color3.new(0, 0, 0), BackgroundTransparency = 0, BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0, 1), Position = UDim2.new(0, -PAST, 1, PAST), Size = UDim2.new(1, PAST * 2, 0.38, PAST), ZIndex = 1 }, gui)
	new("UIGradient", { Rotation = 270, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) }) }, shadeBot)
	-- the box the stage fits in: the safe area (or Opening.testBox, a phone-sized test box in the middle)
	local box = new("Frame", { Name = "Box", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromScale(1, 1), ZIndex = 2 }, gui)
	local stage = new("Frame", { Name = "Stage", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
		Size = UDim2.fromOffset(1920, 1080), ZIndex = 2 }, box)
	local scale = new("UIScale", {}, stage)
	-- the title and the line under it (boosted together on a phone, from their top middle)
	local head = new("Frame", { Name = "Head", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromOffset(960, 62),
		Size = UDim2.fromOffset(1200, 96) }, stage)
	local headScale = new("UIScale", {}, head)
	local title = new("TextLabel", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromOffset(600, 8),
		Size = UDim2.fromOffset(1200, 44), FontFace = T.FONT_TITLE, TextSize = 34, Text = "", TextColor3 = T.TEXT, TextTransparency = 1 }, head)
	new("UIStroke", { Thickness = 1, Transparency = 0.7, Color = Color3.new(0, 0, 0), ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual }, title)
	local odds = new("TextLabel", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromOffset(600, 56),
		Size = UDim2.fromOffset(1200, 24), FontFace = T.FONT, TextSize = 17, Text = "", TextColor3 = T.SOFT, TextTransparency = 1 }, head)
	-- (SKIP: bottom right; on a phone top right, out of the low reel's way. a touch screen has no SPACE)
	local touch = UIS.TouchEnabled and not UIS.KeyboardEnabled
	local skip = button(stage, if touch then "SKIP" else "SKIP  [SPACE]", false, UDim2.fromOffset(1870, 1026), UDim2.fromOffset(170, 46))
	skip.AnchorPoint = Vector2.new(1, 1)
	local skipScale = new("UIScale", {}, skip)
	-- QUICK OPEN: on or off for every opening after this one (remembered); placed beside SKIP by fit()
	local quickB = button(stage, "QUICK OPEN", false, UDim2.fromOffset(1686, 1026), UDim2.fromOffset(220, 46))
	quickB.Name = "Quick"
	quickB.AnchorPoint = Vector2.new(1, 1)
	quickB.TextSize = 15
	local quickScale = new("UIScale", {}, quickB)
	local function paintQuick()
		local on = quickOn()
		quickB.Text = if on then "QUICK OPEN  ON" else "QUICK OPEN  OFF"
		quickB.TextColor3 = if on then T.ACCENT else T.SOFT
	end
	paintQuick()
	quickB.MouseButton1Click:Connect(function()
		local s = settings()
		if s and type(s.set) == "function" then pcall(s.set, "loot.quick", not quickOn()) end
		paintQuick()
		pcall(Sfx.play, "click")
	end)
	-- the reel: a band across the middle, cards on a strip that slides left under a fixed marker
	-- (a CanvasGroup, so the gradient fades the cards themselves out at both ends, not just the band behind them)
	local reel = new("CanvasGroup", { Name = "Reel", BackgroundColor3 = T.BG, BackgroundTransparency = 0.25, BorderSizePixel = 0,
		AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(960, 540), Size = UDim2.fromOffset(1920, CARD_H + 56), ClipsDescendants = true, Visible = false }, stage)
	new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.18, 0), NumberSequenceKeypoint.new(0.82, 0), NumberSequenceKeypoint.new(1, 1) }) }, reel)
	local reelScale = new("UIScale", { Name = "Low", Scale = 1 }, reel)
	local strip = new("Frame", { Name = "Strip", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 28), Size = UDim2.fromOffset(STEP * 60, CARD_H) }, reel)
	local marker = new("Frame", { Name = "Marker", BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0),
		Position = UDim2.fromOffset(960, 6), Size = UDim2.fromOffset(4, CARD_H + 44), ZIndex = 10 }, reel)
	for _, y in { 0, 1 } do
		local tri = new("Frame", { BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5), Rotation = 45,
			Position = UDim2.new(0.5, 0, y, 0), Size = UDim2.fromOffset(14, 14), ZIndex = 10 }, marker)
		local _ = tri
	end
	-- the reveal: bottom centre, under the turning prize
	local reveal = new("Frame", { Name = "Reveal", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.fromOffset(960, 1030),
		Size = UDim2.fromOffset(900, 250), Visible = false }, stage)
	local revealScale = new("UIScale", {}, reveal)
	local rKind = new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 0), Size = UDim2.new(1, 0, 0, 26),
		FontFace = T.FONT_BOLD, TextSize = 20, Text = "", TextColor3 = T.TEXT }, reveal)
	local rName = new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 28), Size = UDim2.new(1, 0, 0, 70),
		FontFace = T.FONT_TITLE, TextSize = 60, Text = "", TextColor3 = T.TEXT }, reveal)
	new("UIStroke", { Thickness = 1.5, Transparency = 0.6, Color = Color3.new(0, 0, 0), ApplyStrokeMode = Enum.ApplyStrokeMode.Contextual }, rName)
	local rOn = new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 100), Size = UDim2.new(1, 0, 0, 24),
		FontFace = T.FONT, TextSize = 18, Text = "", TextColor3 = T.SOFT }, reveal)
	local equip = button(reveal, "EQUIP", true, UDim2.fromOffset(120, 160), UDim2.fromOffset(250, 56))
	local again = button(reveal, "OPEN ANOTHER", false, UDim2.fromOffset(390, 160), UDim2.fromOffset(220, 56))
	local done = button(reveal, "DONE", false, UDim2.fromOffset(630, 160), UDim2.fromOffset(150, 56))
	return { gui = gui, box = box, stage = stage, scale = scale, head = head, headScale = headScale, title = title, odds = odds,
		skip = skip, skipScale = skipScale, quick = quickB, quickScale = quickScale, reel = reel, reelScale = reelScale, reelLow = 1, strip = strip, marker = marker, flash = flash,
		reveal = reveal, revealScale = revealScale, rName = rName, rKind = rKind, rOn = rOn, equip = equip, again = again, done = done,
		s = 1, b = 1, wide = 1920 }
end

-- ---------------------------------------------------------------- phones
-- (the mobile-controls session, 17 Nov: the 1920 x 1080 stage scaled to fit a phone made the buttons about 18 points.)
-- the stage still fits the safe area, but where it gets small (a stage scale under PHONE) the title, the reel and the
-- reveal are boosted up to 2x round their own anchors, SKIP goes to the top right, and every button is at least TAP
-- points tall. ui.s = the stage's scale, ui.b = the boost, ui.wide = the stage-pixel width you can see (more than 1920
-- on a wide phone). a test: Opening.setTestBox(Vector2.new(844, 390)) lays it out in a box that size mid-screen
local PHONE, TAP = 0.62, 44
local testBox: Vector2? = nil
function Opening.setTestBox(v: Vector2?) testBox = v end
local function fit(ui: Ui)
	local a: Vector2
	if testBox then
		ui.box.Size = UDim2.fromOffset(testBox.X, testBox.Y)
		a = testBox
	else
		ui.box.Size = UDim2.fromScale(1, 1)
		a = ui.box.AbsoluteSize
	end
	local edge = ui.box:FindFirstChild("TestEdge")
	if testBox and not edge then new("UIStroke", { Name = "TestEdge", Color = T.ACCENT, Thickness = 2 }, ui.box)
	elseif edge and not testBox then edge:Destroy() end
	if a.X < 2 or a.Y < 2 then return end
	local s = math.min(a.X / 1920, a.Y / 1080)
	local b = if s < PHONE then math.min(PHONE / s, 2) else 1
	ui.s, ui.b, ui.wide = s, b, a.X / s
	ui.scale.Scale = s
	ui.headScale.Scale = b
	ui.revealScale.Scale = b
	ui.reelScale.Scale = ui.reelLow * b
	ui.skipScale.Scale = math.max(b, TAP / (46 * s))
	local right = 960 + ui.wide / 2 - 50
	if b > 1 then
		ui.skip.AnchorPoint = Vector2.new(1, 0)
		ui.skip.Position = UDim2.fromOffset(right, 40)
	else
		ui.skip.AnchorPoint = Vector2.new(1, 1)
		ui.skip.Position = UDim2.fromOffset(right, 1026)
	end
	-- (QUICK OPEN to the left of SKIP, the same size on a phone)
	local k = ui.skipScale.Scale
	ui.quickScale.Scale = k
	ui.quick.AnchorPoint = ui.skip.AnchorPoint
	ui.quick.Position = UDim2.fromOffset(right - 170 * k - 14, ui.skip.Position.Y.Offset)
end
-- a button's height in stage pixels: `base`, or taller to make TAP points under this boost
local function tapH(ui: Ui, base: number, boost: number?): number
	return math.max(base, math.ceil(TAP / (ui.s * (boost or 1))))
end
-- the reveal's row of buttons, in the middle, each at least TAP points tall
local function layRow(ui: Ui, row: { TextButton })
	local h = tapH(ui, 56, ui.b)
	local width = 0
	for _, b in row do
		b.Size = UDim2.fromOffset(b.Size.X.Offset, h)
		b.TextSize = math.floor(math.min(h, 80) * 0.36)
		width += b.Size.X.Offset
	end
	width += (#row - 1) * 16
	local x = 450 - width / 2
	for _, b in row do b.Position = UDim2.fromOffset(x, 160); x += b.Size.X.Offset + 16 end
end
-- where the space between the title and the reveal is (stage y): for something big in the middle
local function middle(ui: Ui): (number, number)
	return 62 + 100 * ui.b, 1030 - 250 * ui.b
end

-- ---------------------------------------------------------------- the world: where it lands, the camera
-- ---------------------------------------------------------------- the floor (nothing goes through it)
-- (the owner, 16 Nov: "make sure the stuff doesnt clip through the ground".) the rules: Shared.LootFloor (your feet
-- from the foot parts, a ray trusted only near them, the highest visible piece rays can't see on top of it)
-- (the floor rules live in Shared.LootFloor: the server's spot for others uses the same ones)
local function feetOf(ch: Model?): number? return LootFloor.feet(ch) end
local function floorY(at: Vector3, feetY: number, ignore: { Instance }): number return LootFloor.at(at, feetY, ignore) end

-- where they stand: Shared.LootFloor.layout (one ahead of you, turned a little so it reads as a solid thing; five in a
-- half ring in front; ten in a ring all round; every spot clear of walls and on a floor). the server uses the same for
-- what others see
local function ground(kind: string, n: number): (CFrame?, Vector3, any)
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not ch or not root then return nil, Vector3.zero, nil end
	local look = (workspace.CurrentCamera :: Camera).CFrame.LookVector
	local flat = Vector3.new(look.X, 0, look.Z)
	flat = if flat.Magnitude > 1e-3 then flat.Unit else Vector3.new(0, 0, -1)
	local ok, lay = pcall(LootFloor.layout, ch, flat, kind, n)
	if not ok or type(lay) ~= "table" or #lay.cfs == 0 then
		warn("[jankfire] loot layout: " .. tostring(lay))
		local g = Vector3.new(root.Position.X, (feetOf(ch) :: number), root.Position.Z) + flat * 7.5
		lay = { cfs = { CFrame.lookAt(g, g - flat) * CFrame.Angles(0, math.rad(-20), 0) }, k = 1 }
	end
	if n == 1 then
		-- (one alone may have moved round from straight ahead (a wall there): the camera works from where it really is)
		local d = lay.cfs[1].Position - root.Position
		d = Vector3.new(d.X, 0, d.Z)
		if d.Magnitude > 0.5 then flat = d.Unit end
	end
	return lay.cfs[1], flat, lay
end

-- what's over your head: the height of the lowest solid thing up to 60 studs over `from` (nil: open sky)
local function ceilingOver(from: Vector3): number?
	local ignore = {}
	for _, pl in Players:GetPlayers() do if pl.Character then table.insert(ignore, pl.Character) end end
	local hit = LootFloor.ray(from, from + Vector3.new(0, 60, 0), ignore)
	return if hit then hit.Position.Y else nil
end

-- a camera that sees every one of these points, from behind (along -flat), looking down `pitch` degrees or more, as
-- near as it can: under the ceiling over your head, nothing between your head and it, and nothing (a wall, a beam)
-- between it and most of the `look` points. returns nil when there's no such view (a low ceiling over a wide ring)
local function frameAll(points: { Vector3 }, look: { Vector3 }, flat: Vector3, pitch: number, fov: number, from: Vector3): CFrame?
	local cam = workspace.CurrentCamera :: Camera
	local v = cam.ViewportSize
	local aspect = if v.Y > 1 then v.X / v.Y else 16 / 9
	local ignore = {}
	for _, pl in Players:GetPlayers() do if pl.Character then table.insert(ignore, pl.Character) end end
	-- (under the ceiling over your head and over every container, and never more than 16 studs over your head: a ring
	-- of ten needs more than that, so it gets the camera that turns instead of a far view through the hub's beams)
	local ceil = ceilingOver(from)
	local capY = math.min(if ceil then ceil - 1.2 else math.huge, from.Y + 16)
	for _, q in look do
		local c2 = ceilingOver(q)
		if c2 then capY = math.min(capY, c2 - 1.2) end
	end
	local tv = math.tan(math.rad(fov) / 2) * 0.8 -- (room at the top for the title, at the bottom for the reel)
	local th = math.tan(math.rad(fov) / 2) * aspect * 0.9
	for p = pitch, 88, 8 do
		local fwd = (flat * math.cos(math.rad(p)) - Vector3.yAxis * math.sin(math.rad(p))).Unit
		local basis = CFrame.lookAt(Vector3.zero, fwd)
		local r, u = basis.RightVector, basis.UpVector
		local x0, x1, y0, y1, z = math.huge, -math.huge, math.huge, -math.huge, 0
		for _, q in points do
			x0 = math.min(x0, q:Dot(r)); x1 = math.max(x1, q:Dot(r))
			y0 = math.min(y0, q:Dot(u)); y1 = math.max(y1, q:Dot(u))
			z += q:Dot(fwd)
		end
		local c = r * (x0 + x1) / 2 + u * (y0 + y1) / 2 + fwd * (z / #points)
		local d = 4
		for _, q in points do
			local o = q - c
			d = math.max(d, math.abs(o:Dot(r)) / th - o:Dot(fwd), math.abs(o:Dot(u)) / tv - o:Dot(fwd))
		end
		local eye = c - fwd * (d + 0.6)
		if eye.Y <= capY and not LootFloor.ray(from, eye, ignore) then
			local seen = 0
			for _, q in look do if not LootFloor.ray(eye, q, ignore) then seen += 1 end end
			if seen >= #look * 0.85 then return CFrame.lookAt(eye, c) end
		end
	end
	return nil
end

-- ---------------------------------------------------------------- one opening
type Run = { ui: Ui, kind: string, res: any, opts: any, skip: boolean, skipAt: number, result: string?,
	box: Model?, prize: Model?, base: CFrame, flat: Vector3, height: number, light: PointLight?, rim: PointLight?,
	cam: { from: CFrame, to: CFrame, t0: number, dur: number, shake: number, shakeT: number, fov: number },
	blur: BlurEffect, tint: ColorCorrectionEffect, dof: DepthOfFieldEffect, hidden: { [ScreenGui]: boolean },
	saved: { cf: CFrame, type: Enum.CameraType, fov: number, loadoutOpen: any }, conns: { RBXScriptConnection },
	spin: number, prizeY: number, prizeFrom: number?, wid: string?, boxes: { any }?, layout: any,
	-- (19 Nov: fast = QUICK OPEN; prepped = the reel's cards and the prize are made and loaded; count = how many were
	-- asked for; refused = the server's no; cards / prizeM / built = what prep() made)
	fast: boolean?, prepped: boolean?, count: number?, refused: any, cards: { Frame }?, prizeM: Model?, prizeWid: string?,
	prizeTried: boolean?, built: { [number]: Model }? }

local function camTo(R: Run, to: CFrame, dur: number)
	local c = workspace.CurrentCamera :: Camera
	R.cam.from, R.cam.to, R.cam.t0, R.cam.dur = c.CFrame, to, os.clock(), dur
end
local function shake(R: Run, amp: number) R.cam.shake, R.cam.shakeT = amp, os.clock() end

-- wait t seconds, or less once SKIP is pressed (returns at once then)
local function hold(R: Run, t: number)
	local t0 = os.clock()
	while os.clock() - t0 < t and not R.skip do RunService.RenderStepped:Wait() end
end

local function particles(at: Vector3, color: Color3, kind: string): Part
	local p = new("Part", { Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
		Size = Vector3.new(0.2, 0.2, 0.2), CFrame = CFrame.new(at) }, workspace)
	local e: ParticleEmitter
	if kind == "dust" then
		e = new("ParticleEmitter", { Texture = "rbxasset://textures/particles/smoke_main.dds", Rate = 0, Lifetime = NumberRange.new(0.6, 1.1),
			Speed = NumberRange.new(5, 9), SpreadAngle = Vector2.new(80, 8), Drag = 4, Acceleration = Vector3.new(0, 1.5, 0),
			Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.8), NumberSequenceKeypoint.new(1, 2.4) }),
			Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.55), NumberSequenceKeypoint.new(1, 1) }),
			Color = ColorSequence.new(Color3.fromRGB(196, 192, 184)), LightEmission = 0, EmissionDirection = Enum.NormalId.Top,
			Rotation = NumberRange.new(0, 360), RotSpeed = NumberRange.new(-40, 40) }, p)
		e:Emit(16)
	else
		e = new("ParticleEmitter", { Texture = "rbxasset://textures/particles/sparkles_main.dds", Rate = 0, Lifetime = NumberRange.new(0.5, 1.0),
			Speed = NumberRange.new(8, 16), SpreadAngle = Vector2.new(55, 55), Drag = 3, Acceleration = Vector3.new(0, -12, 0),
			Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.5), NumberSequenceKeypoint.new(1, 0) }),
			Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(1, 1) }),
			Color = ColorSequence.new(color), LightEmission = 0.8, EmissionDirection = Enum.NormalId.Top }, p)
		e:Emit(if kind == "big" then 60 else 26)
	end
	task.delay(2.5, function() p:Destroy() end)
	return p
end

-- the lid / zip / cap of a container, at u = 0 (shut) .. 1 (open). works on a scaled copy too (a batch, a bystander's)
local function openBox(box: Model?, u: number)
	if not box then return end
	local how = box:GetAttribute("Open") or "hinge"
	local bp = box:GetPivot()
	local k = box:GetScale()
	for _, m in box:GetChildren() do
		if m:IsA("Model") and (m.Name == "Lid" or m.Name == "Cap" or m.Name == "Flap" or m.Name == "FlapL" or m.Name == "FlapR" or m.Name == "Zip") then
			local rest = m:GetAttribute("Rest") :: CFrame?
			if not rest then rest = bp:ToObjectSpace(m:GetPivot()); m:SetAttribute("Rest", rest) end
			local hinge = m:GetAttribute("Hinge")
			-- (the hinge is written in the container's own frame at full size: scale it with the container)
			local h: CFrame = if typeof(hinge) == "CFrame" then CFrame.new(hinge.Position * k) * hinge.Rotation else (rest :: CFrame)
			local cf: CFrame
			if m.Name == "Zip" then
				-- the zip pull runs along the top from one end to the other
				local run = ((m:GetAttribute("Run") :: number?) or 2.4) * k
				cf = bp * CFrame.new(run * u, 0, 0) * (rest :: CFrame)
			elseif how == "pop" then
				-- the cap: up off the can, over, and down onto the floor beside it, landing on its side
				local v = math.clamp(u, 0, 1)
				local drop = math.max(0, h.Position.Y - 0.72 * k) -- (its middle ends one radius off the floor)
				local up = 2.0 * k * math.sin(math.pi * v) - drop * v * v
				cf = bp * CFrame.new(1.9 * k * v, up, 0.6 * k * v) * h * CFrame.Angles(0, v * 3.2, -v * math.pi / 2) * h:Inverse() * (rest :: CFrame)
			else
				-- (Angle is signed: + lifts a lid hinged at its back edge (+z), - one hinged at its front edge)
				local ang = (m:GetAttribute("Angle") :: number?) or (if how == "flap" then 75 else 108)
				cf = bp * h * CFrame.Angles(math.rad(ang) * u, 0, 0) * h:Inverse() * (rest :: CFrame)
			end
			m:PivotTo(cf)
		end
	end
end
local function openPose(R: Run, u: number) openBox(R.box, u) end

-- ---------------------------------------------------------------- nothing goes through the floor
-- (the owner, 16 Nov: "make sure the stuff doesnt clip through the ground".) a container's pivot is the middle of its
-- bottom face. tipped by ax about its own x and az about its z, its edges would dip under the floor by half its depth
-- (width) times the sine, so every pose is lifted by exactly that; nothing is ever put below its floor spot; the exits
-- shrink and fade into the container's own footprint instead of sinking
local LIFT = 0.04 -- (a hair over the floor, so the bottom face never flickers against it)
local function halves(box: Model): (number, number)
	local hx, hz = box:GetAttribute("HalfX"), box:GetAttribute("HalfZ")
	if type(hx) ~= "number" or type(hz) ~= "number" then
		local cf, size = box:GetBoundingBox()
		local c = box:GetPivot():PointToObjectSpace(cf.Position)
		hx, hz = math.abs(c.X) + size.X / 2, math.abs(c.Z) + size.Z / 2
		box:SetAttribute("HalfX", hx); box:SetAttribute("HalfZ", hz)
	end
	return hx :: number, hz :: number
end
-- the box on its floor spot `at`, y studs up, tipped (ax, ay, az), shifted (dx, dz): never under the floor
local function place(box: Model, at: CFrame, y: number, ax: number?, ay: number?, az: number?, dx: number?, dz: number?)
	local hx, hz = halves(box)
	local a, c = ax or 0, az or 0
	local dip = hz * math.abs(math.sin(a)) + hx * math.abs(math.sin(c))
	box:PivotTo(at * CFrame.new(dx or 0, math.max(0, y) + dip + LIFT, dz or 0) * CFrame.Angles(a, ay or 0, c))
end
-- a prize (a gun model) as it rises out of a container: its lowest point, measured once, so it starts above the top
local function halfHeight(m: Model): number
	local _, size = m:GetBoundingBox()
	return size.Y / 2 + math.max(size.X, size.Z) * 0.06 -- (+ what its little tilt adds)
end
-- leaving: everything shrinks into its own footprint and fades; lights go out with it
local function fadeOut(models: { Model? }, dur: number)
	local list = {}
	for _, m in models do
		if m and m.Parent then
			local parts, lights = {}, {}
			for _, d in m:GetDescendants() do
				if d:IsA("BasePart") then parts[d] = d.Transparency
				elseif d:IsA("Light") then lights[d] = d.Brightness end
			end
			table.insert(list, { m = m, k = m:GetScale(), parts = parts, lights = lights })
		end
	end
	local t0 = os.clock()
	while true do
		local u = math.min(1, (os.clock() - t0) / dur)
		local e = smooth(u)
		for _, o in list do
			if o.m.Parent then
				pcall(function() o.m:ScaleTo(o.k * (1 - 0.75 * e)) end) -- (about its pivot: a container's sits on the floor)
				for p, tr in o.parts do p.Transparency = tr + (1 - tr) * e end
				for l, b in o.lights do l.Brightness = b * (1 - e) end
			end
		end
		if u >= 1 then break end
		RunService.RenderStepped:Wait()
	end
end

-- the reel: build the cards, spin, land. returns the winning card
local function spinReel(R: Run, items: { any }, stop: number, dur: number, low: boolean?): Frame
	local ui = R.ui
	-- (the low reel of a ring is smaller; on a phone both are boosted: fit() keeps reelScale = reelLow x boost)
	ui.reelLow = if low then 0.68 else 1
	ui.reelScale.Scale = ui.reelLow * ui.b
	local y = if low then 905 else 540
	local cards = R.cards -- (made during the drop by prep())
	R.cards = nil
	if not cards or #cards ~= #items then
		for _, c in ui.strip:GetChildren() do c:Destroy() end
		cards = {}
		for i, it in items do cards[i] = card(ui.strip, it, (i - 1) * STEP) end
	end
	Timing.mark("built" .. #items)
	-- (only the cards over the band are drawn: 46 pictures sliding under it cost frames)
	local function cull(x: number)
		for i, c in cards do
			local cx = (i - 1) * STEP + x
			local v = cx + CARD_W > -STEP and cx < 1920 + STEP
			if c.Visible ~= v then c.Visible = v end
		end
	end
	local rng = Random.new()
	local mid = 960
	-- where the strip ends: the prize card under the marker, somewhere across its width (never right on an edge)
	local within = rng:NextNumber(-0.38, 0.38) * CARD_W
	local xEnd = mid - ((stop - 1) * STEP + CARD_W / 2) - within
	local xStart = mid - (2 * STEP + CARD_W / 2) - rng:NextNumber(0, STEP)
	ui.strip.Position = UDim2.fromOffset(xStart, 28)
	cull(xStart)
	ui.reel.Visible = true
	ui.reel.Position = UDim2.fromOffset(960, y + 40)
	ui.reel.BackgroundTransparency = 1
	tw(ui.reel, 0.3, { Position = UDim2.fromOffset(960, y), BackgroundTransparency = 0.25 })
	local t0 = os.clock()
	local lastIdx = math.floor((mid - xStart) / STEP)
	local lastTick = 0
	local p = if dur > 3 then 4 else 3 -- (quart out: fast, then a long slow crawl past the last few cards)
	while true do
		local u = (os.clock() - t0) / dur
		if R.skip then u = 1 end
		local x = xStart + (xEnd - xStart) * easeOut(u, p)
		ui.strip.Position = UDim2.fromOffset(x, 28)
		cull(x)
		local idx = math.floor((mid - x) / STEP)
		if idx ~= lastIdx and not R.skip then
			lastIdx = idx
			local now = os.clock()
			if now - lastTick > 0.03 then
				lastTick = now
				local slow = 1 - easeOut(u, 1.5)
				snd({ "loot_tick", "click" }, nil, 0.55 + 0.25 * (1 - slow), 1.0 + 0.06 * (1 - slow))
				-- (the marker nods with each card going by)
				ui.marker.Size = UDim2.fromOffset(6, CARD_H + 44)
				task.delay(0.04, function() ui.marker.Size = UDim2.fromOffset(4, CARD_H + 44) end)
			end
		end
		if u >= 1 then break end
		RunService.RenderStepped:Wait()
	end
	return cards[stop]
end

-- the world as it was when we're done: camera, HUD, controls, effects
-- (OPEN ANOTHER, 19 Nov: the next opening takes over the camera where it is and the screens still hidden, so it
-- drops straight away: held. none within 1.5 s, or Opening.release(): everything goes back)
local held: any = nil
local function giveBack(saved: any, hidden: { [ScreenGui]: boolean })
	local c = workspace.CurrentCamera :: Camera
	c.CameraType = saved.type
	c.FieldOfView = saved.fov
	for g in hidden do if g.Parent then g.Enabled = true end end
	-- (the mouse goes back to whoever else still has it: the shop between two openings, the loadout under it)
	MenuCursor.set("loot", false)
	me:SetAttribute("LoadoutOpen", saved.loadoutOpen == true or MenuCursor.menu()) -- (a real menu: not Toggle Cursor)
	me:SetAttribute("LootOpening", nil)
	pcall(function()
		local controls = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		controls:Enable()
	end)
end
local function restore(R: Run, keep: boolean?)
	for _, c in R.conns do c:Disconnect() end
	pcall(function() RunService:UnbindFromRenderStep("JankLootCam") end)
	pcall(function() ContextActionService:UnbindAction("JankLootSink") end)
	R.blur:Destroy(); R.tint:Destroy(); R.dof:Destroy()
	if R.box then R.box:Destroy() end
	for _, b in R.boxes or {} do
		if b.m then b.m:Destroy() end
		if b.prize then b.prize:Destroy() end
	end
	if R.prize then R.prize:Destroy() end
	if R.prizeM then R.prizeM:Destroy() end
	for _, m in R.built or {} do m:Destroy() end
	R.ui.gui:Destroy()
	if keep then
		local h = { saved = R.saved, hidden = R.hidden }
		held = h
		task.delay(1.5, function()
			if held == h and not running then held = nil; giveBack(h.saved, h.hidden) end
		end)
		return
	end
	giveBack(R.saved, R.hidden)
end
-- the shop isn't opening another after all: the camera and the screens back now
function Opening.release()
	local h = held
	held = nil
	if h and not running then giveBack(h.saved, h.hidden) end
end

-- ---------------------------------------------------------------- equipping a prize (the loadout's own ops)
local RANK = { common = 1, rare = 2, epic = 3, legendary = 4 }
-- the gun a prize goes on: its own (a wrap or hat is won for one gun; a skin is one gun's)
local function gunOf(item: any): string?
	local w = item.weapon or (item.type == "skin" and (LootTable.SKINS[item.id] or {})[3]) or nil
	local e = w and Roster.byId[w]
	return if e and e.live and e.slot ~= "utility" then w else nil
end
local function canEquip(item: any): boolean
	return (item.type == "wrap" or item.type == "hat" or item.type == "skin") and gunOf(item) ~= nil
end
local function equipItem(item: any): (boolean, string?)
	local lo = Remotes:FindFirstChild("Loadout") :: RemoteFunction?
	local wid = gunOf(item)
	if not lo or not wid then return false, "can't go on anything yet" end
	local ok, r = pcall(function()
		if item.type == "wrap" then
			local _, mode = WeaponModels.wrapFor(me, wid :: string)
			return (lo :: RemoteFunction):InvokeServer("wrap", wid, item.id, if mode and mode ~= "" then mode else "full")
		elseif item.type == "hat" then
			return (lo :: RemoteFunction):InvokeServer("hat", wid, item.id)
		end
		return (lo :: RemoteFunction):InvokeServer("skin", wid, item.id)
	end)
	if ok and type(r) == "table" and r.ok then return true, nil end
	return false, if ok and type(r) == "table" and type(r.why) == "string" then r.why else "couldn't equip"
end

-- the odds line this open was rolled with (what you owned before it: the prizes are taken back out). it comes in
-- when both the inventory and the server's answer are in: the drop never waits for it (19 Nov)
local function oddsLater(R: Run)
	task.spawn(function()
		local okInv, inv = pcall(function() return (Remotes:FindFirstChild("Loot") :: RemoteFunction):InvokeServer("inventory") end)
		Timing.mark("inv")
		local t0 = os.clock()
		while R.res == nil and R.ui.gui.Parent and os.clock() - t0 < TIME.wait do task.wait() end
		local res = R.res
		if not R.ui.gui.Parent or type(res) ~= "table" or res.ok ~= true then return end
		local prizes = if type(res.prizes) == "table" and #res.prizes > 0 then res.prizes else { res.prize or res.item }
		local owned = {}
		if okInv and type(inv) == "table" and type(inv.owned) == "table" then
			for t, ids in inv.owned do owned[t] = {}; for _, id in ids do owned[t][id] = true end end
			for _, q in prizes do
				local t = type(q) == "table" and (q.type or q.kind)
				if t and owned[t] then owned[t][q.key or q.id] = nil end
			end
		end
		R.ui.odds.Text = "ODDS  " .. LootTable.oddsLine(LootTable.odds(R.kind, owned))
		tw(R.ui.odds, 0.3, { TextTransparency = 0.1 })
	end)
end

-- ---------------------------------------------------------------- a prize's sign (a ring's prizes, others' openings)
-- a small dark plate over a prize: its name in its rarity's colour, then its gun and rarity; `header` (someone else's
-- opening: who opened what) goes on top
local function prizeSign(parent: Instance, at: Vector3, item: any, header: string?, big: boolean?): BillboardGui
	local anchor = new("Part", { Name = "PrizeSign", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
		Size = Vector3.new(0.2, 0.2, 0.2), CFrame = CFrame.new(at) }, parent)
	local col = rcol(item.rarity)
	-- (a fixed size on screen: a sign sized in studs filled the screen over a container right under the camera. the small
	-- ones only near; the one that says who opened what from further off)
	-- (big: someone else's opening, read from where you stand, 19 Nov)
	local bb = new("BillboardGui", { Size = if header then UDim2.fromOffset(if big then 340 else 250, if big then 100 else 76)
			else UDim2.fromOffset(if big then 236 else 176, if big then 60 else 46),
		MaxDistance = if header then 160 elseif big then 110 else 70, LightInfluence = 0, AlwaysOnTop = false, ResetOnSpawn = false,
		SizeOffset = if big then Vector2.new(0, 0.5) else Vector2.zero }, anchor) -- (big: it stands on the anchor, clear of the prize)
	local plate = new("Frame", { BackgroundColor3 = T.BG, BackgroundTransparency = 0.2, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1) }, bb)
	T.corner(plate, 6)
	new("UIStroke", { Color = col, Thickness = 1.5, Transparency = 0.2 }, plate)
	local function line(y: number, h: number, text: string, color: Color3, font: Font)
		new("TextLabel", { BackgroundTransparency = 1, Position = UDim2.fromScale(0.05, y), Size = UDim2.fromScale(0.9, h), Text = text,
			TextColor3 = color, FontFace = font, TextScaled = true, TextWrapped = true, TextXAlignment = Enum.TextXAlignment.Center }, plate)
	end
	local gun = item.weapon and Roster.byId[item.weapon]
	local what = if gun then string.upper(gun.name) elseif LootTable.hookFor(item.type) then string.upper(LootTable.TYPE_NAMES[item.type] or item.type) else nil
	local under = (if what then what .. "  ·  " else "") .. rname(item.rarity)
	if header then
		line(0.07, 0.24, header, T.SOFT, T.FONT)
		line(0.34, 0.36, string.upper(item.name or item.id or ""), col, T.FONT_BOLD)
		line(0.73, 0.2, under, T.MUTED, T.FONT)
	else
		line(0.1, 0.48, string.upper(item.name or item.id or ""), col, T.FONT_BOLD)
		line(0.62, 0.28, under, T.MUTED, T.FONT)
	end
	return bb
end

-- the prizes of a ring, built (true size) and all shown at ONE scale: the game's display scale, or smaller for all of
-- them together if the longest would touch its neighbour's as they turn. returns the models (by index) and the scale
local function ringPrizes(items: { any }, cfs: { CFrame }, slice: boolean?): ({ [number]: Model }, number)
	local near = math.huge
	for i, a in cfs do
		for j = i + 1, #cfs do near = math.min(near, (a.Position - cfs[j].Position).Magnitude) end
	end
	local models, longest = {}, 0.2
	local f0 = os.clock()
	for i, item in items do
		if cfs[i] then
			local ok, m, _, metres = pcall(prizeModel, item)
			if ok and m then models[i] = m; longest = math.max(longest, metres) end
			-- (slice: a few a frame, so the frames keep coming while they fall)
			if slice and os.clock() - f0 > 0.008 then RunService.RenderStepped:Wait(); f0 = os.clock() end
		end
	end
	local k = math.min(gunScale(), near * 0.85 / longest)
	for _, m in models do
		showAt(m, k)
		-- (never in anyone's way: the ring's floor tests and the camera's rays look through it. 19 Nov, the owner:
		-- "opening containers doesn't always work when there's multiple people": someone else's prizes turning near you
		-- were solid to your own opening's ring and camera)
		for _, d in m:GetDescendants() do
			if d:IsA("BasePart") then d.CanQuery = false; d.CanCollide = false; d.CanTouch = false end
		end
	end
	return models, k
end

-- ---------------------------------------------------------------- several at once (x5, x10)
-- the owner: "make sure you can open multiple", then "could they open around you": they drop round you at full size
-- (five in a half ring in front, ten in a ring all round: Shared.LootFloor.layout keeps them off walls and off each
-- other), one after another, while the camera backs up and off to see them all; then each pops in turn with a quick
-- reel (low on the screen, the ring stays in view) and its prize comes up over it with a small sign; a moment to look
-- round them all, then a grid of everything you got, rarest first, each with EQUIP; OPEN n MORE opens as many again.
-- SKIP: everything left pops and shows at once
local function runMany(R: Run): string
	local ui, kind = R.ui, R.kind
	local info = LootTable.CONTAINERS[kind] or LootTable.CONTAINERS.crate
	local n = math.max(1, R.count or 1) -- (as many as were asked for: the answer can bring fewer)
	local cam = workspace.CurrentCamera :: Camera
	ui.title.Text = ("%s  x%d"):format(string.upper(info.name), n)
	tw(ui.title, 0.3, { TextTransparency = 0 })
	oddsLater(R)

	-- 1. the ring
	local ch = me.Character
	local lay = R.layout
	if type(lay) ~= "table" or type(lay.cfs) ~= "table" or #lay.cfs < 1 then
		local _, _, l2 = ground(kind, n)
		lay = l2
	end
	local k = lay.k or 1
	local w, front, back = LootFloor.room(kind, k)
	local DROP = 12
	local boxes = {}
	R.boxes = boxes
	for i = 1, n do
		local at: CFrame = lay.cfs[i] or lay.cfs[#lay.cfs]
		local b = container(kind, k)
		local hgt = heightOf(b)
		local lp = new("Part", { Name = "Light", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
			Size = Vector3.new(0.2, 0.2, 0.2) }, b)
		lp.CFrame = b:GetPivot() * CFrame.new(0, hgt + 0.6, 0)
		local light = new("PointLight", { Color = WHITE, Brightness = 0, Range = 11, Shadows = false }, lp)
		place(b, at, DROP)
		b.Parent = workspace
		openBox(b, 0)
		boxes[i] = { m = b, at = at, h = hgt, t0 = os.clock() + 0.08 + (i - 1) * 0.04, light = light, landed = false }
	end
	R.height = boxes[1].h
	local cfs = {}
	for i, b in boxes do cfs[i] = b.at end
	-- (the prizes: built by prep() while they fall, once the answer is in, all at one scale)
	-- the camera: back and up until it sees every container and what will come out of it
	local pts = {}
	for _, b in boxes do
		for _, o in { Vector3.new(-w / 2, 0, -front), Vector3.new(w / 2, 0, -front), Vector3.new(-w / 2, 0, back), Vector3.new(w / 2, 0, back),
			Vector3.new(0, b.h + 3.4, 0) } do
			table.insert(pts, b.at:PointToWorldSpace(o))
		end
	end
	local head = ch and ch:FindFirstChild("Head") :: BasePart?
	local from = if head then head.Position else R.base.Position + Vector3.new(0, 4, 0)
	local looks = {}
	for _, b in boxes do table.insert(looks, b.at.Position + Vector3.new(0, b.h * 0.6, 0)) end
	local FOV = 62
	local camCf = frameAll(pts, looks, R.flat, if n > 5 then 56 else 34, FOV, from)
	-- (no overview, under a ceiling: the camera stands over you, as high as the ceiling lets it, and turns to each
	-- container as it opens, then once all the way round)
	local mid = Vector3.zero
	for _, b in boxes do mid += b.at.Position end
	mid /= n
	local rootP = (ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?)
	local centre = if rootP then Vector3.new(rootP.Position.X, R.base.Position.Y, rootP.Position.Z) else mid
	local ceil = ceilingOver(from)
	local eyeH = math.clamp((if ceil then ceil - 1.4 else from.Y + 12) - centre.Y, 5.5, 10)
	local ringR = 0
	for _, b in boxes do ringR += (Vector3.new(b.at.X, 0, b.at.Z) - Vector3.new(centre.X, 0, centre.Z)).Magnitude end
	ringR /= n
	local function aimAt(dir: Vector3, hgt: number): CFrame
		dir = Vector3.new(dir.X, 0, dir.Z)
		dir = if dir.Magnitude > 1e-3 then dir.Unit else R.flat
		local eye = centre - dir * 3.5 + Vector3.new(0, eyeH, 0)
		return CFrame.lookAt(eye, centre + dir * ringR + Vector3.new(0, hgt + 0.8, 0))
	end
	local function aimBox(i: number): CFrame
		local b = boxes[i]
		return aimAt(b.at.Position - centre, b.h)
	end
	local orbit = camCf == nil
	R.cam.fov = if orbit then 68 else FOV
	camTo(R, if orbit then aimBox(1) else camCf :: CFrame, 0.9)
	-- they fall one after another round you, land (a thud at the first and the last: no rattle of ten), hop and settle
	local firstLand, lastLand = false, false
	while true do
		local now = os.clock()
		local done = true
		for i, b in boxes do
			local u = (now - b.t0) / 0.38
			if R.skip then u = 3 end
			if u < 1 then
				done = false
				place(b.m, b.at, DROP * (1 - math.max(0, u) ^ 2), 0.1 * (1 - math.max(0, u)))
			else
				if not b.landed then
					b.landed = true
					if not R.skip then particles(b.at.Position + Vector3.new(0, 0.2, 0), WHITE, "dust") end
				end
				local v = (u - 1) * 0.38 / 0.4
				if v < 1 then
					done = false
					place(b.m, b.at, 0.45 * math.sin(v * math.pi) * (1 - v))
				else
					place(b.m, b.at, 0)
				end
				if i == 1 and not firstLand then firstLand = true; snd({ "loot_land", "bonk" }, b.at.Position, 1, 0.7); shake(R, 0.15) end
				if i == n and not lastLand then lastLand = true; snd({ "loot_land", "bonk" }, b.at.Position, 0.8, 0.8) end
			end
			openBox(b.m, 0)
		end
		if done then break end
		RunService.RenderStepped:Wait()
	end
	if not R.skip then hold(R, 0.1) end
	-- the answer (nearly always in by now: it was asked for as they began to fall) and the prizes made from it
	local w0 = os.clock()
	while true do
		local r = R.res
		if r ~= nil and (r.ok ~= true or R.prepped) then break end
		if r == nil and os.clock() - w0 > TIME.wait then break end
		RunService.RenderStepped:Wait()
	end
	local res = R.res
	if type(res) ~= "table" or res.ok ~= true or type(res.prizes) ~= "table" or #res.prizes < 1 then
		-- (the server said no, or never answered: they go, and the shop says why)
		R.refused = if type(res) == "table" then res else { ok = false, why = "the till didn't answer. try again" }
		local ms = {}
		for _, b in boxes do table.insert(ms, b.m) end
		fadeOut(ms, 0.25)
		return "refused"
	end
	local prizes = res.prizes :: { any }
	if #prizes < n then
		-- (fewer left in them for you than you asked for: the ones over go)
		local extra = {}
		for i = n, #prizes + 1, -1 do
			table.insert(extra, boxes[i].m)
			table.remove(boxes, i)
			table.remove(cfs, i)
		end
		fadeOut(extra, 0.25)
		for _, m in extra do m:Destroy() end
		n = #prizes
		ui.title.Text = ("%s  x%d"):format(string.upper(info.name), n)
	end
	local built = R.built or ringPrizes(prizes, cfs) -- (all at one scale: a pistol stays smaller than a sniper)
	R.built = nil

	-- 2. they all pop: each prize comes up over its container with its sign
	tw(R.blur, 0.4, { Size = 2 })
	tw(R.tint, 0.4, { Brightness = -0.04, Saturation = -0.3, Contrast = 0.05 })
	local spinT = 0
	table.insert(R.conns, RunService.RenderStepped:Connect(function(dt)
		spinT += dt
		local now = os.clock()
		for i, b in boxes do
			if b.popT and not b.opened then
				local u = math.clamp((now - b.popT) / b.pt, 0, 1)
				local s = 1.70158
				openBox(b.m, if b.arc then u else 1 + (s + 1) * (u - 1) ^ 3 + s * (u - 1) ^ 2)
				b.light.Brightness = (b.glowTo or 2) + 3 * (1 - u)
				if u >= 1 then b.opened = true end
			end
			local pm = b.prize
			if pm and pm.Parent then
				local u = easeOut((now - b.riseT) / 0.55, 3)
				local y = b.from + (b.top - b.from) * u + math.sin(now * 1.3 + i) * 0.06 * u
				pm:PivotTo(CFrame.new(b.at.Position + Vector3.new(0, y, 0)) * b.at.Rotation * CFrame.Angles(0, math.pi / 2 + spinT * 0.6 + i * 0.7, 0))
			end
		end
	end))
	local function pop(i: number)
		local b = boxes[i]
		if b.popT then return end
		b.arc = b.m:GetAttribute("Open") == "pop"
		b.pt = if R.skip then 0.25 elseif b.arc then 0.7 else 0.45
		b.popT = os.clock()
		for _, d in b.m:GetDescendants() do
			if d:IsA("BasePart") and d.Name == "glow" then d.Transparency = 0; d.Material = Enum.Material.Neon end
		end
		if not R.skip then
			snd({ "loot_pop", "bigpop", "pop" }, b.at.Position, 0.7, 1 + (i - 1) * 0.02)
			particles(b.at.Position + Vector3.new(0, b.h, 0), Color3.fromRGB(255, 236, 200), "pop")
		end
	end
	local function show(i: number, item: any)
		local b = boxes[i]
		if b.shown then return end
		b.shown = true
		local col = rcol(item.rarity)
		local rank = RANK[item.rarity] or 1
		b.light.Color = col
		b.glowTo = 2 + rank
		if b.opened then b.light.Brightness = b.glowTo end
		local m = built[i]
		b.from, b.top = b.h, b.h + 2.4
		if m then
			b.from = b.h + LIFT + halfHeight(m) + 0.1 -- (up from just over the open top: never through it)
			b.top = math.max(b.h + 2.2, b.from + 0.6)
			b.riseT = os.clock()
			m:PivotTo(CFrame.new(b.at.Position + Vector3.new(0, b.from, 0)) * b.at.Rotation)
			m.Parent = workspace
			b.prize = m
		end
		b.sign = prizeSign(b.m, b.at.Position + Vector3.new(0, b.top + 1.9, 0), item)
		if rank >= 3 then particles(b.at.Position + Vector3.new(0, b.h + 0.5, 0), col, if rank == 4 then "big" else "pop") end
	end
	-- (19 Nov, the owner: "opening crates and stuff is still really slow": no reel for each one any more. they pop in
	-- a quick ripple, each prize up over its container with its sign, the best one's sting and flash, a moment to see
	-- them, then the grid. SKIP: all at once and straight to the grid)
	for i, prize in prizes do
		pop(i); show(i, prize)
		if i < n then hold(R, if R.fast then 0.03 else 0.05) end
	end
	local best, bestQ = 1, prizes[1]
	for _, q in prizes do
		local r = RANK[q.rarity] or 1
		if r > best then best, bestQ = r, q end
	end
	local stings = ({ { "loot_win_common", "ting" }, { "loot_win_rare", "ting" }, { "loot_win_epic", "round_start" }, { "loot_win_legendary", "round_end", "round_start" } })[best]
	snd(stings, nil, 0.9, 1)
	if best >= 2 then
		ui.flash.BackgroundColor3 = rcol(bestQ.rarity)
		ui.flash.BackgroundTransparency = if best >= 3 then 0.7 else 0.82
		tw(ui.flash, 0.6, { BackgroundTransparency = 1 })
	end
	if best >= 3 then shake(R, 0.1 * best) end
	tw(R.blur, 0.4, { Size = 0 })
	ui.title.Text = ("YOU GOT %d"):format(n)
	Timing.mark("popped")
	-- a moment to see what came out; under a ceiling the camera turns part way round the ring meanwhile
	local look = if R.fast then 0.6 else 1.4
	if orbit then
		local d0 = boxes[1].at.Position - centre
		local a0 = math.atan2(-d0.X, -d0.Z)
		local turn = if n > 5 then math.pi * 0.9 else math.pi * 0.45
		local t0 = os.clock()
		while os.clock() - t0 < look and not R.skip do
			local u = smooth((os.clock() - t0) / look)
			local a = a0 + turn * u
			camTo(R, aimAt(Vector3.new(-math.sin(a), 0, -math.cos(a)), R.height), 0.01)
			RunService.RenderStepped:Wait()
		end
	else
		hold(R, look)
	end
	ui.skip.Visible = false
	tw(R.blur, 0.4, { Size = 10 })
	tw(R.tint, 0.4, { Brightness = -0.12, Saturation = -0.35, Contrast = 0.04 })
	for _, b in boxes do if b.sign then b.sign.Enabled = false end end

	Timing.mark("grid")
	-- 3. everything you got, rarest first, each with EQUIP
	local order = table.clone(prizes)
	table.sort(order, function(a, b)
		local ra, rb = RANK[a.rarity] or 0, RANK[b.rarity] or 0
		if ra ~= rb then return ra > rb end
		return (a.name or "") < (b.name or "")
	end)
	local grid = new("Frame", { Name = "Summary", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 0), Size = UDim2.fromOffset(1920, 1080), ZIndex = 5 }, ui.stage)
	local rows = math.ceil(n / 5)
	-- (a phone: the whole card is its EQUIP button (a tag on its corner says which), the list as big as fits between
	-- the title and the buttons; a computer: a button under each card, as before)
	local phone = ui.b > 1
	local CW, CH, GY, GX = CARD_W, CARD_H, 26, 22
	local BH = if phone then 0 else 38
	local cols = math.min(5, n)
	local gw, gh = cols * CW + (cols - 1) * GX, rows * (CH + BH + 8) + (rows - 1) * GY
	local bh = tapH(ui, 56) -- (the buttons under it: TAP points tall)
	local gTop, gBot = 62 + 100 * ui.b + 20, 1080 - 40 - bh - 24
	local g = if phone then math.min(ui.b, (gBot - gTop) / gh, (ui.wide - 120) / gw) else 1
	local cards = new("Frame", { Name = "Cards", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromOffset(960, if phone then (gTop + gBot) / 2 else 580), Size = UDim2.fromOffset(gw, gh) }, grid)
	new("UIScale", { Scale = g }, cards)
	for i, item in order do
		local r, c = math.floor((i - 1) / 5), (i - 1) % 5
		local inRow = math.min(5, n - r * 5)
		local xr = (gw - (inRow * CW + (inRow - 1) * GX)) / 2 -- (a short last row sits in the middle)
		local holder = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromOffset(xr + c * (CW + GX), r * (CH + BH + 8 + GY)),
			Size = UDim2.fromOffset(CW, CH + BH + 8) }, cards)
		local cd = card(holder, item, 0)
		local stroke = cd:FindFirstChildOfClass("UIStroke")
		if stroke and (RANK[item.rarity] or 0) >= 3 then stroke.Color = rcol(item.rarity); stroke.Transparency = 0.1; stroke.Thickness = 2 end
		local eq = canEquip(item)
		local b: TextButton
		local say: (string) -> ()
		if phone then
			b = new("TextButton", { Name = "Tap", Text = "", AutoButtonColor = false, BackgroundTransparency = 1, Size = UDim2.fromOffset(CW, CH), ZIndex = 9 }, holder)
			local tag = new("TextLabel", { Name = "Tag", BackgroundColor3 = if eq then T.ACCENT else T.BG, BackgroundTransparency = if eq then 0 else 0.15,
				BorderSizePixel = 0, AnchorPoint = Vector2.new(1, 0), Position = UDim2.fromOffset(CW - 12, 12), Size = UDim2.fromOffset(0, 26),
				AutomaticSize = Enum.AutomaticSize.X, FontFace = T.FONT_BOLD, TextSize = 15, Text = if eq then "EQUIP" else "OWNED",
				TextColor3 = if eq then T.INK else T.SOFT, ZIndex = 8 }, holder)
			new("UIPadding", { PaddingLeft = UDim.new(0, 8), PaddingRight = UDim.new(0, 8) }, tag)
			T.corner(tag, 4)
			say = function(s: string) tag.Text = s end
		else
			b = button(holder, if eq then "EQUIP" else "IN YOUR INVENTORY", false, UDim2.fromOffset(0, CH + 8), UDim2.fromOffset(CW, BH))
			b.TextSize = 14
			if not eq then b.TextColor3 = T.MUTED end
			say = function(s: string) b.Text = s end
		end
		if eq then
			local busy, done = false, false
			b.MouseButton1Click:Connect(function()
				if busy or done then return end
				busy = true
				say("...")
				local ok, why = equipItem(item)
				busy, done = false, ok
				say(if ok then "EQUIPPED" else string.upper(why or "couldn't"))
				if ok then pcall(Sfx.play, "click") end
			end)
		end
		holder.Position += UDim2.fromOffset(0, 24)
		cd.BackgroundTransparency = 1
		tw(holder, 0.3 + i * 0.03, { Position = holder.Position - UDim2.fromOffset(0, 24) })
		tw(cd, 0.3 + i * 0.03, { BackgroundTransparency = 0 })
	end
	if res.short then
		local note = new("TextLabel", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromOffset(960, 62 + 92 * ui.b),
			Size = UDim2.fromOffset(1000, 24), FontFace = T.FONT, TextSize = 17, TextColor3 = T.SOFT, ZIndex = 6,
			Text = "that was everything left in them for you" }, grid)
		new("UIScale", { Scale = ui.b }, note)
	end
	local again = R.opts.again ~= false and (type(R.opts.canAgain) ~= "function" or R.opts.canAgain() ~= false)
	-- (the two buttons, TAP points tall, wider in step)
	local bw = bh / 56
	local by = if phone then 1080 - 40 - bh else 960
	local x0 = 960 - (440 * bw + 20) / 2
	local bAgain = button(grid, ("OPEN %d MORE"):format(n), true, UDim2.fromOffset(x0, by), UDim2.fromOffset(250 * bw, bh))
	local bDone = button(grid, "DONE", false, UDim2.fromOffset(x0 + 250 * bw + 20, by), UDim2.fromOffset(190 * bw, bh))
	bAgain.Visible = again
	if not again then bDone.Position = UDim2.fromOffset(960 - 95 * bw, by) end
	local answer: string? = nil
	bDone.MouseButton1Click:Connect(function() answer = "done" end)
	bAgain.MouseButton1Click:Connect(function() answer = "again" end)
	while not answer do
		if R.result then answer = R.result end
		RunService.RenderStepped:Wait()
	end

	-- 4. away: the containers and the prizes shrink into their own footprints and fade, the camera goes home
	grid:Destroy()
	tw(R.tint, 0.3, { Brightness = 0, Saturation = 0, Contrast = 0 })
	tw(R.blur, 0.3, { Size = 0 })
	local st = os.clock()
	local sv = R.saved.cf
	local chain = answer == "again" and R.opts.chain == true -- (OPEN n MORE: the camera stays for the next drop)
	if not chain then
		R.cam.from, R.cam.t0, R.cam.dur = cam.CFrame, os.clock(), 0.45
		local h = ch and ch:FindFirstChild("Head") :: BasePart?
		R.cam.to = if h then CFrame.new(h.Position + Vector3.new(0, 0.1, 0)) * sv.Rotation else sv
		R.cam.fov = R.saved.fov
	end
	local all = {}
	for _, b in boxes do
		table.insert(all, b.m)
		if b.prize then table.insert(all, b.prize) end
	end
	for i, m in built do if not boxes[i] or boxes[i].prize ~= m then m:Destroy() end end
	local away = if chain then 0.25 else 0.45
	fadeOut(all, away)
	while os.clock() - st < away do RunService.RenderStepped:Wait() end
	return answer :: string
end

-- ---------------------------------------------------------------- what others see (LootShow.client.luau)
-- someone near you opened something: their containers drop where they stand for them (the same ring as theirs: the
-- server works it out with Shared.LootFloor.layout), pop one after another, and every prize comes up over its
-- container and turns, with a small sign; the best one's sign says who opened what. no reel, one quiet sound, about
-- seven seconds. at most four openings drawn at a time; far away (more than 170 studs) is not drawn
local showing = 0
local function showOne(d: any)
	local kind = if LootTable.CONTAINERS[d.kind] then d.kind else "crate"
	local info = LootTable.CONTAINERS[kind]
	local cfs: { CFrame } = {}
	if type(d.cfs) == "table" then for _, c in d.cfs do if typeof(c) == "CFrame" then table.insert(cfs, c) end end end
	if #cfs == 0 then cfs = { d.cf } end
	local count = math.min(#cfs, #d.prizes, 10)
	local k = math.clamp(tonumber(d.k) or 1, 0.4, 1)
	local bestI = 1
	for i = 1, count do
		if (RANK[d.prizes[i].rarity] or 0) > (RANK[d.prizes[bestI].rarity] or 0) then bestI = i end
	end
	local quiet = showing > 2 -- (a crowd of openings: no sound from the extra ones)
	local nOpened = math.max(count, tonumber(d.n) or 1)
	local header = ("%s opened %s"):format(tostring(d.who or "someone"),
		if nOpened > 1 then ("%d %s"):format(nOpened, string.lower(info.plural)) else "a " .. string.lower(info.name))
	local used, items = {}, {}
	for i = 1, count do used[i] = cfs[i]; items[i] = d.prizes[i] end
	local built = ringPrizes(items, used)
	-- (seen from where you stand, not over their shoulder: bigger than the opener's own. the owner, 19 Nov: "the items are
	-- small if you look at someone else opening them". in a ring every other prize rides higher, so big ones don't touch)
	local grow = if count == 1 then 2.0 else 1.6
	for _, m in built do pcall(function() m:ScaleTo(m:GetScale() * grow) end) end
	local boxes = {}
	for i = 1, count do
		local box = container(kind, k)
		local hgt = heightOf(box)
		local lp = new("Part", { Name = "ShowLight", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
			Size = Vector3.new(0.2, 0.2, 0.2) }, box)
		lp.CFrame = box:GetPivot() * CFrame.new(0, hgt + 0.6, 0) -- (before the first move: it goes where the box goes)
		local light = new("PointLight", { Color = WHITE, Brightness = 0, Range = 10, Shadows = false }, lp)
		place(box, cfs[i], 9)
		box.Parent = workspace
		openBox(box, 0)
		boxes[i] = { m = box, at = cfs[i], h = hgt, light = light, t0 = os.clock() + (i - 1) * 0.07, landed = false }
	end
	-- the drop and the hop
	local thud = false
	while true do
		local done = true
		for _, b in boxes do
			local u = (os.clock() - b.t0) / 0.38
			if u < 1 then
				done = false
				place(b.m, b.at, 9 * (1 - math.max(0, u) ^ 2))
			else
				if not b.landed then
					b.landed = true
					particles(b.at.Position + Vector3.new(0, 0.2, 0), WHITE, "dust")
					if not thud and not quiet then thud = true; snd({ "loot_land", "bonk" }, b.at.Position, 0.45, 0.75) end
				end
				local v = (u - 1) * 0.38 / 0.35
				if v < 1 then
					done = false
					place(b.m, b.at, 0.5 * math.sin(v * math.pi) * (1 - v))
				else
					place(b.m, b.at, 0)
				end
			end
			openBox(b.m, 0)
		end
		if done then break end
		RunService.RenderStepped:Wait()
	end
	task.wait(0.3)
	-- the pops, one after another, and every prize over its container, turning
	local t0 = os.clock()
	for i, b in boxes do b.popT = t0 + (i - 1) * 0.2 end
	local endT = t0 + (count - 1) * 0.2 + 4.6
	while os.clock() < endT do
		local now = os.clock()
		for i, b in boxes do
			if now >= b.popT then
				local item = d.prizes[i]
				local col = rcol(item.rarity)
				if not b.popped then
					b.popped = true
					for _, x in b.m:GetDescendants() do
						if x:IsA("BasePart") and x.Name == "glow" then x.Transparency = 0; x.Material = Enum.Material.Neon end
					end
					particles(b.at.Position + Vector3.new(0, b.h, 0), col, if (RANK[item.rarity] or 0) >= 4 then "big" else "pop")
					b.arc = b.m:GetAttribute("Open") == "pop"
					b.light.Color = col
					local m = built[i]
					b.from, b.top = b.h, b.h + 2.4
					if m then
						b.from = b.h + LIFT + halfHeight(m) + 0.1
						b.top = math.max(b.h + 2.2, b.from + 0.9) + (if count > 1 and i % 2 == 0 then 1.8 else 0)
						m.Parent = workspace
						b.prize = m
					end
					-- (the sign clear over the prize, however big it's shown)
					local over = if m then halfHeight(m) + 1.1 else 1.9
					b.sign = prizeSign(b.m, b.at.Position + Vector3.new(0, b.top + over + (if i == bestI then 0.4 else 0), 0), item, if i == bestI then header else nil, true)
				end
				local u = math.min(1, (now - b.popT) / (if b.arc then 0.8 else 0.45))
				if not b.opened then
					local s = 1.70158
					openBox(b.m, if b.arc then u else 1 + (s + 1) * (u - 1) ^ 3 + s * (u - 1) ^ 2)
					if u >= 1 then b.opened = true end
				end
				b.light.Brightness = 5 * (1 - u) + 2.5 * u
				local pm = b.prize
				if pm and pm.Parent then
					local r = easeOut((now - b.popT) / 0.6, 3)
					local y = b.from + (b.top - b.from) * r + math.sin(now * 1.3 + i) * 0.06
					pm:PivotTo(CFrame.new(b.at.Position + Vector3.new(0, y, 0)) * b.at.Rotation * CFrame.Angles(0, math.pi / 2 + (now - b.popT) * 0.8 + i * 0.7, 0))
				end
			end
		end
		RunService.RenderStepped:Wait()
	end
	local all = {}
	for _, b in boxes do
		if b.sign then b.sign.Enabled = false end
		table.insert(all, b.m)
		if b.prize then table.insert(all, b.prize) end
	end
	fadeOut(all, 0.5)
	for _, m in all do m:Destroy() end
end
function Opening.show(d: any)
	if type(d) ~= "table" or typeof(d.cf) ~= "CFrame" or type(d.prizes) ~= "table" or #d.prizes == 0 then return end
	if showing >= 4 or running then return end -- (not while your own opening plays: it has the screen)
	local c = workspace.CurrentCamera
	if c and (c.CFrame.Position - (d.cf :: CFrame).Position).Magnitude > 170 then return end
	showing += 1
	task.spawn(function()
		local ok, err = pcall(showOne, d)
		showing -= 1
		if not ok then warn("[jankfire] someone's opening didn't draw: " .. tostring(err)) end
	end)
end

-- what the reel and the reveal need, made while the container drops and rattles (19 Nov): the reel's cards (a few a
-- frame), the prize's model (or the ring's prizes), then their pictures and meshes loaded (ContentProvider) for at
-- most TIME.prep. R.prepped says it's done; the rattle waits for it
local function stripOf(res: any, prize: any): ({ any }, number)
	local items, stop = res.strip, res.stop
	if type(items) ~= "table" or #items == 0 or type(stop) ~= "number" or not items[stop] then
		items, stop = {}, 40
		for i = 1, 46 do items[i] = prize end
	end
	return items, stop
end
local function prep(R: Run)
	local res = R.res
	if type(res) ~= "table" or res.ok ~= true then R.prepped = true; return end
	local ok, err = pcall(function()
		local load = {}
		if type(res.prizes) == "table" and #res.prizes > 1 then
			-- (several: the ring's prizes at their one scale, a few a frame)
			local boxes = R.boxes
			if boxes then
				local cfs = {}
				for i = 1, math.min(#boxes, #res.prizes) do cfs[i] = boxes[i].at end
				local built = ringPrizes(res.prizes, cfs, true)
				if not R.ui.gui.Parent then for _, m in built do m:Destroy() end; return end
				R.built = built
				for _, m in built do table.insert(load, m) end
			end
		else
			local prize = res.prize or res.item
			if type(prize) ~= "table" then return end
			prize.type = prize.type or prize.kind
			if not R.fast then
				local items = stripOf(res, prize)
				for _, c in R.ui.strip:GetChildren() do c:Destroy() end
				local cards = {}
				local f0 = os.clock()
				for i, it in items do
					cards[i] = card(R.ui.strip, it, (i - 1) * STEP)
					cards[i].Visible = false
					if os.clock() - f0 > 0.008 then RunService.RenderStepped:Wait(); f0 = os.clock() end
					if not R.ui.gui.Parent then return end
				end
				R.cards = cards
				table.insert(load, R.ui.strip)
			end
			local okM, m, wid = pcall(prizeModel, prize)
			R.prizeTried = true
			if okM then R.prizeM, R.prizeWid = m, wid end
			if okM and m then table.insert(load, m) end
		end
		Timing.mark("made")
		if #load > 0 then
			local done = false
			task.spawn(function()
				pcall(function() ContentProvider:PreloadAsync(load) end)
				done = true
			end)
			local t0 = os.clock()
			while not done and os.clock() - t0 < TIME.prep do task.wait() end
			Timing.mark(if done then "loaded" else "loadcap")
		end
	end)
	if not ok then warn("[jankfire] the opening's prep: " .. tostring(err)) end
	R.prepped = true
end

local function run(R: Run): string
	local ui, kind = R.ui, R.kind
	local info = LootTable.CONTAINERS[kind] or LootTable.CONTAINERS.crate
	local quick = R.fast == true -- (QUICK OPEN: a short drop, no reel)
	local cam = workspace.CurrentCamera :: Camera

	-- title + the odds this open was rolled with (the odds come in their own time: oddsLater)
	ui.title.Text = string.upper(info.name)
	tw(ui.title, 0.3, { TextTransparency = 0 })
	oddsLater(R)

	-- 1. the drop: from high up, onto the ground, a heavy bounce, dust; the camera comes round to look
	local base = R.base
	local box = container(kind)
	R.box = box
	R.height = heightOf(box)
	local glow = Instance.new("PointLight")
	glow.Color = WHITE; glow.Brightness = 0; glow.Range = 12; glow.Shadows = false
	local lightPart = new("Part", { Name = "Light", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
		Size = Vector3.new(0.2, 0.2, 0.2), CFrame = base * CFrame.new(0, R.height + 0.6, 0) }, box)
	glow.Parent = lightPart
	R.light = glow
	local drop = if quick then 6 else 15
	place(box, base, drop, 0.12, 0.5, -0.08)
	box.Parent = workspace
	openPose(R, 0)
	local flat = R.flat
	local right = flat:Cross(Vector3.yAxis)
	local look = base.Position + Vector3.new(0, R.height * 0.5, 0)
	-- (the camera stands a couple of studs in front of you, a little to the side: your own body stays behind it)
	local eye = base.Position - flat * (3.9 + R.height * 0.62) + right * 1.3 + Vector3.new(0, 2.9 + R.height * 0.4, 0)
	camTo(R, CFrame.lookAt(eye, look), if quick then 0.35 else TIME.camIn)
	Timing.mark("drop")
	R.cam.fov = R.saved.fov -- (your own field of view: the framing was made at it)
	local fall = if quick then 0.28 else TIME.fall
	local t0 = os.clock()
	while true do
		local u = math.min(1, (os.clock() - t0) / fall)
		local y = drop * (1 - u * u)
		local a = 1 - u
		place(box, base, y, 0.12 * a, 0.5 * a * a, -0.08 * a)
		openPose(R, 0)
		if u >= 1 then break end
		RunService.RenderStepped:Wait()
	end
	snd({ "loot_land", "bonk" }, base.Position, 1.2, 0.62)
	shake(R, if quick then 0.15 else 0.35)
	particles(base.Position + Vector3.new(0, 0.2, 0), WHITE, "dust")
	-- the bounce: two hops that die away, with a rock forward and back
	local bt = if quick then 0.3 else TIME.bounce
	t0 = os.clock()
	while true do
		local u = math.min(1, (os.clock() - t0) / bt)
		local hop = if u < 0.62 then 0.9 * math.sin(u / 0.62 * math.pi) else 0.22 * math.sin((u - 0.62) / 0.38 * math.pi)
		local rock = math.sin(u * math.pi * 3) * (1 - u) * 0.09
		place(box, base, hop * (if quick then 0.5 else 1), rock, 0, rock * 0.4)
		openPose(R, 0)
		if u >= 1 then break end
		RunService.RenderStepped:Wait()
	end
	place(box, base, 0)
	if not quick then hold(R, 0.05) end

	-- 2. the rattle, then the pop: light leaks out of the seam, the lid / zip / cap goes
	-- (19 Nov: at least TIME.rattle (none for QUICK OPEN or after a SKIP), and for as long as the server's answer and
	-- the reel's pictures take to come in)
	t0 = os.clock()
	local need = if quick or R.skip then 0 else TIME.rattle
	while true do
		local el = os.clock() - t0
		local r = R.res
		if r ~= nil and (r.ok ~= true or R.prepped) and (el >= need or R.skip) then break end
		if r == nil and el > TIME.wait then break end
		local u = math.min(1, el / 0.8)
		local amp = 0.02 + 0.07 * u * u
		place(box, base, 0, math.sin(os.clock() * 47) * amp, 0, math.sin(os.clock() * 59) * amp,
			math.sin(os.clock() * 61) * amp * 0.4, math.cos(os.clock() * 53) * amp * 0.3)
		openPose(R, 0)
		glow.Brightness = 2.2 * u
		RunService.RenderStepped:Wait()
	end
	place(box, base, 0)
	Timing.mark("rattled")
	local res = R.res
	if type(res) ~= "table" or res.ok ~= true or type(res.prize or res.item) ~= "table" then
		-- (the server said no, or never answered: the container goes, and the shop says why)
		R.refused = if type(res) == "table" then res else { ok = false, why = "the till didn't answer. try again" }
		fadeOut({ box }, 0.25)
		return "refused"
	end
	local prize = res.prize or res.item
	prize.type = prize.type or prize.kind
	snd({ "loot_pop", "bigpop", "pop" }, base.Position, 1, 1)
	shake(R, 0.18)
	particles(base.Position + Vector3.new(0, R.height, 0), Color3.fromRGB(255, 236, 200), "pop")
	for _, d in box:GetDescendants() do
		if d:IsA("BasePart") and d.Name == "glow" then d.Transparency = 0; d.Material = Enum.Material.Neon end
	end
	local arc = box:GetAttribute("Open") == "pop"
	local pt = if quick or R.skip then 0.25 elseif arc then 0.55 else TIME.pop
	t0 = os.clock()
	while true do
		local u = math.min(1, (os.clock() - t0) / pt)
		-- (back-out: a lid or flap swings past open and settles; a cap flies on its arc)
		local s = 1.70158
		local e = if arc then u else 1 + (s + 1) * (u - 1) ^ 3 + s * (u - 1) ^ 2
		openPose(R, e)
		glow.Brightness = 6 * (1 - u) + 2.4 * u
		if u >= 1 then break end
		RunService.RenderStepped:Wait()
	end
	Timing.mark("popped")

	-- 3. the reel over the soft world (QUICK OPEN: no reel, the flash says what it is). a SKIP, now or during the
	-- drop, lands it at once
	local win: Frame? = nil
	if not quick then
		tw(R.blur, 0.3, { Size = 18 })
		tw(R.tint, 0.3, { Brightness = -0.06, Saturation = -0.5, Contrast = 0.05 })
		local items, stop = stripOf(res, prize)
		win = spinReel(R, items, stop, TIME.spin)
	end
	Timing.mark("landed")

	-- 4. it lands: the winner grows, the rest go dark, the screen breathes its colour
	local col = rcol(prize.rarity)
	if win then
		for _, c in ui.strip:GetChildren() do
			if c:IsA("Frame") and c ~= win then
				local dim = c:FindFirstChild("Dim")
				if dim then tw(dim :: Frame, 0.3, { BackgroundTransparency = 0.5 }) end
			end
		end
		local sc = new("UIScale", { Scale = 1 }, win)
		tw(sc, 0.35, { Scale = 1.1 }, Enum.EasingStyle.Back)
		local stroke = win:FindFirstChildOfClass("UIStroke")
		if stroke then stroke.Color = col; stroke.Transparency = 0; stroke.Thickness = 3 end
	end
	ui.flash.BackgroundColor3 = col
	ui.flash.BackgroundTransparency = if quick then 0.55 else 0.72
	tw(ui.flash, 0.8, { BackgroundTransparency = 1 })
	local rank = ({ common = 1, rare = 2, epic = 3, legendary = 4 })[prize.rarity] or 1
	local stings = ({ { "loot_win_common", "ting" }, { "loot_win_rare", "ting" }, { "loot_win_epic", "round_start" }, { "loot_win_legendary", "round_end", "round_start" } })[rank]
	snd(stings, nil, 1, 1)
	glow.Color = col
	glow.Brightness = 2 + rank
	if rank >= 3 then
		shake(R, 0.12 * rank)
		particles(base.Position + Vector3.new(0, R.height, 0), col, if rank == 4 then "big" else "pop")
	end
	if not R.result then R.skip = false end
	hold(R, if quick then 0.35 else TIME.land)

	-- 5. the reveal: the reel goes, the prize comes up out of the container and turns; the camera leans in
	tw(ui.reel, 0.3, { Position = UDim2.fromOffset(960, 600), BackgroundTransparency = 1 })
	task.delay(0.3, function() ui.reel.Visible = false end)
	tw(R.blur, 0.5, { Size = 0 }) -- (the depth of field below keeps the room soft, not the prize)
	tw(R.tint, 0.5, { Brightness = -0.06, Saturation = -0.3, Contrast = 0.06 })
	ui.skip.Visible = false
	tw(ui.title, 0.3, { TextTransparency = 1 }); tw(ui.odds, 0.3, { TextTransparency = 1 })
	local m, wid -- (made by prep() during the drop; built now if it couldn't be)
	if R.prizeTried then m, wid = R.prizeM, R.prizeWid; R.prizeM = nil else m, wid = prizeModel(prize) end
	local shownLen = 4.6
	if m then
		showAt(m, gunScale())
		local _, sz = m:GetBoundingBox()
		shownLen = math.max(sz.X, sz.Y, sz.Z)
	end
	R.wid = wid
	R.prizeY = math.min(R.height, 2.6) + 3.0
	if m then
		R.prize = m
		R.prizeFrom = R.height + LIFT + halfHeight(m) + 0.1 -- (it comes up from just over the open top: never through it)
		R.prizeY = math.max(R.prizeY, R.prizeFrom + 0.6)
		m:PivotTo(base * CFrame.new(0, R.prizeFrom, 0))
		m.Parent = workspace
		local rim = Instance.new("PointLight")
		rim.Color = col; rim.Brightness = 1.6; rim.Range = 9; rim.Shadows = false
		local key = Instance.new("SpotLight")
		key.Color = Color3.fromRGB(255, 250, 244); key.Brightness = 2.2; key.Range = 16; key.Angle = 50; key.Face = Enum.NormalId.Front
		local lp = new("Part", { Name = "PrizeLight", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
			Size = Vector3.new(0.2, 0.2, 0.2) }, m)
		lp.CFrame = CFrame.lookAt(base.Position - flat * 4 + Vector3.new(0, R.prizeY + 2.5, 0), base.Position + Vector3.new(0, R.prizeY, 0))
		key.Parent = lp
		local lp2 = new("Part", { Name = "PrizeRim", Anchored = true, CanCollide = false, CanQuery = false, CanTouch = false, Transparency = 1,
			Size = Vector3.new(0.2, 0.2, 0.2), CFrame = base * CFrame.new(0, R.height + 0.3, 1.2) }, m)
		rim.Parent = lp2
		R.rim = rim
	end
	local riseT0 = os.clock()
	local focus = base.Position + Vector3.new(0, R.prizeY, 0)
	local eye2 = base.Position - flat * (5.6 + math.max(0, R.height - 2.4) * 0.5 + math.max(0, shownLen - 5) * 0.7) + right * 0.9 + Vector3.new(0, R.prizeY + (if prize.type == "hat" then 1.4 else 0.7), 0)
	camTo(R, CFrame.lookAt(eye2, focus - Vector3.new(0, 0.25, 0)), 0.8)
	R.dof.Enabled = true
	R.dof.FocusDistance = (eye2 - focus).Magnitude
	-- the turn (and the rise) run every frame from here until the end
	table.insert(R.conns, RunService.RenderStepped:Connect(function(dt)
		local pm = R.prize
		if not pm or not pm.Parent then return end
		R.spin += dt * 0.7
		local u = easeOut((os.clock() - riseT0) / TIME.rise, 3)
		local y0 = R.prizeFrom or R.height
		local y = y0 + (R.prizeY - y0) * u + math.sin(os.clock() * 1.3) * 0.08 * u
		local face = CFrame.lookAt(Vector3.zero, -flat)
		pm:PivotTo(CFrame.new(base.Position + Vector3.new(0, y, 0)) * face * CFrame.Angles(0, math.pi / 2 + 0.5 + math.sin(R.spin) * 0.55, 0) * CFrame.Angles(0.1, 0, 0))
	end))

	-- the words and the buttons
	local tname = LootTable.TYPE_NAMES[prize.type] or "Item"
	local tierName: string? = nil
	if prize.type == "skin" then
		local _, tn = LootTable.tier(prize.id)
		tierName = tn
	end
	ui.rKind.Text = rname(prize.rarity) .. "  ·  " .. string.upper(tname) .. (if tierName then "  ·  " .. string.upper(tierName) .. " TIER" else "")
	ui.rKind.TextColor3 = col
	ui.rName.Text = string.upper(prize.name or prize.id or "")
	local we = wid and Roster.byId[wid]
	ui.rOn.Text = if prize.type == "skin" then "a new look for your " .. (if we then we.name else "weapon")
		elseif LootTable.cardLook(prize.type) then "for your player card"
		elseif we and prize.weapon then "for your " .. we.name .. " only" elseif we then "shown on your " .. we.name else ""
	local can = canEquip(prize)
	local eqGun = gunOf(prize)
	ui.equip.Visible = can
	ui.equip.Text = if can and eqGun then "EQUIP ON " .. string.upper(Roster.byId[eqGun].name) else "EQUIP"
	ui.equip.Size = UDim2.fromOffset(math.max(250, #ui.equip.Text * 13 + 40), 56)
	local again = R.opts.again ~= false and (type(R.opts.canAgain) ~= "function" or R.opts.canAgain() ~= false)
	ui.again.Visible = again
	-- lay the row out in the middle
	local row = {}
	for _, b in { ui.equip, ui.again, ui.done } do if b.Visible then table.insert(row, b) end end
	layRow(ui, row)
	ui.reveal.Visible = true
	ui.reveal.Position = UDim2.fromOffset(960, 1060)
	tw(ui.reveal, 0.4, { Position = UDim2.fromOffset(960, 1030) })
	local fire = if prize.rarity == "legendary" then revealFire(ui.gui, col) else nil

	local answer: string? = nil
	ui.done.MouseButton1Click:Connect(function() answer = "done" end)
	ui.again.MouseButton1Click:Connect(function() answer = "again" end)
	ui.equip.MouseButton1Click:Connect(function()
		if not can or ui.equip.Text == "EQUIPPED" or ui.equip.Text == "..." then return end
		ui.equip.Text = "..."
		local ok, why = equipItem(prize)
		if ok then
			ui.equip.Text = "EQUIPPED"
			ui.equip.BackgroundColor3 = T.CARD
			ui.equip.TextColor3 = T.TEXT
			pcall(Sfx.play, "click")
		else
			ui.equip.Text = string.upper(why or "couldn't equip")
		end
	end)
	Timing.mark("reveal")
	while not answer do
		if R.result then answer = R.result end
		RunService.RenderStepped:Wait()
	end
	Timing.mark("answer")

	-- 6. away: the prize and the container sink, the camera goes home
	fireOut(fire)
	tw(ui.reveal, 0.25, { Position = UDim2.fromOffset(960, 1100) })
	tw(R.dof, 0.3, { FarIntensity = 0, NearIntensity = 0 })
	tw(R.tint, 0.3, { Brightness = 0, Saturation = 0, Contrast = 0 })
	if R.prize then R.prize:Destroy(); R.prize = nil end
	if answer == "again" and R.opts.chain == true then
		-- (OPEN ANOTHER: the camera stays where it is, the next one drops straight into the same spot)
		fadeOut({ R.box }, 0.2)
		return answer
	end
	local st = os.clock()
	local sv = R.saved.cf
	R.cam.from, R.cam.t0, R.cam.dur = cam.CFrame, os.clock(), 0.45
	local ch = me.Character
	local h = ch and ch:FindFirstChild("Head") :: BasePart?
	R.cam.to = if h then CFrame.new(h.Position + Vector3.new(0, 0.1, 0)) * sv.Rotation else sv
	R.cam.fov = R.saved.fov
	fadeOut({ R.box }, 0.45)
	while os.clock() - st < 0.45 do RunService.RenderStepped:Wait() end
	return answer :: string
end

-- ---------------------------------------------------------------- the one entry point
function Opening.play(kind: string, res: any, opts: any?): string
	if running then return "busy" end
	-- (res: the server's answer, or a function that asks for it: then the container drops at once and the answer is
	-- waited for while it rattles. opts.n = how many were asked for. 19 Nov)
	local ask: any = if type(res) == "function" then res else nil
	if ask then res = nil
	elseif type(res) ~= "table" or not res.ok or type(res.prize or res.item) ~= "table" then Opening.release(); return "done" end
	if not LootTable.CONTAINERS[kind] then kind = "crate" end
	Timing.start(type(opts) == "table" and opts.pressT or nil)
	if type(opts) == "table" and opts.replyT then table.insert(Timing.list, ("reply=%.2f"):format(opts.replyT - Timing.t0)) end
	Timing.mark("play")
	local want = if type(opts) == "table" and type(opts.n) == "number" then math.clamp(math.floor(opts.n), 1, 10) else 1
	local count = if ask then want elseif type(res.prizes) == "table" and #res.prizes > 1 then #res.prizes else 1
	local base, flat, lay = ground(kind, count)
	if not base then Opening.release(); return "done" end
	running = true
	local h = held -- (OPEN ANOTHER: the last one's camera and hidden screens)
	held = nil
	local cam = workspace.CurrentCamera :: Camera
	local ui = buildUi()
	local R: Run = {
		ui = ui, kind = kind, res = res, opts = opts or {}, skip = false, skipAt = 0, result = nil,
		box = nil, prize = nil, base = base, flat = flat, height = 2.4, light = nil, rim = nil,
		cam = { from = cam.CFrame, to = cam.CFrame, t0 = os.clock(), dur = 0.01, shake = 0, shakeT = 0, fov = cam.FieldOfView },
		blur = new("BlurEffect", { Name = "JankLootBlur", Size = 0 }, cam),
		tint = new("ColorCorrectionEffect", { Name = "JankLootTint" }, cam),
		dof = new("DepthOfFieldEffect", { Name = "JankLootDof", Enabled = false, FarIntensity = 0.75, NearIntensity = 0, InFocusRadius = 4, FocusDistance = 8 }, cam),
		hidden = if h then h.hidden else {},
		saved = if h then h.saved else { cf = cam.CFrame, type = cam.CameraType, fov = cam.FieldOfView, loadoutOpen = me:GetAttribute("LoadoutOpen") },
		conns = {}, spin = 0, prizeY = 4, wid = nil, boxes = nil, layout = lay,
		fast = (type(opts) == "table" and opts.quick == true) or quickOn(), prepped = false, count = count,
	}
	-- everything else steps aside: the HUD and menus, your hands (LoadoutOpen = a menu is up: Arsenal, Utility and
	-- Move hold still), the keys that would open other screens
	for _, g in (me:WaitForChild("PlayerGui")):GetChildren() do
		if g:IsA("ScreenGui") and g ~= ui.gui and g.Enabled then R.hidden[g] = true; g.Enabled = false end
	end
	me:SetAttribute("LoadoutOpen", true)
	me:SetAttribute("LootOpening", kind)
	MenuCursor.set("loot", true, function() return running or held ~= nil end) -- (the mouse is free and shows to the end: DONE, OPEN ANOTHER)
	pcall(function()
		local controls = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		controls:Disable()
	end)
	ContextActionService:BindActionAtPriority("JankLootSink", function(_, state, io)
		if state == Enum.UserInputState.Begin and (io.KeyCode == Enum.KeyCode.Space or io.KeyCode == Enum.KeyCode.ButtonA) then
			R.skip = true
		end
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.Space, Enum.KeyCode.ButtonA, Enum.KeyCode.L, Enum.KeyCode.B, Enum.KeyCode.G, Enum.KeyCode.Q,
		Enum.KeyCode.E, Enum.KeyCode.R, Enum.KeyCode.F, Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three, Enum.KeyCode.Four, Enum.KeyCode.Tab)
	ui.skip.MouseButton1Click:Connect(function() R.skip = true end)
	-- (the camera's field of view is the opening's while it runs: the settings' FOV and the guns' zoom set it every
	-- frame, so any change from them is put straight back)
	local fovNow = cam.FieldOfView
	table.insert(R.conns, cam:GetPropertyChangedSignal("FieldOfView"):Connect(function()
		if math.abs(cam.FieldOfView - fovNow) > 0.01 then cam.FieldOfView = fovNow end
	end))
	-- the camera: eased moves plus a little shake, every frame after Roblox's own camera
	RunService:BindToRenderStep("JankLootCam", Enum.RenderPriority.Camera.Value + 6, function()
		local c = workspace.CurrentCamera :: Camera
		c.CameraType = Enum.CameraType.Scriptable
		local u = easeOut((os.clock() - R.cam.t0) / math.max(0.01, R.cam.dur), 3)
		local cf = R.cam.from:Lerp(R.cam.to, u)
		local k = math.max(0, 1 - (os.clock() - R.cam.shakeT) / 0.35) * R.cam.shake
		if k > 0 then
			local t = os.clock()
			cf *= CFrame.new(math.sin(t * 71) * k * 0.3, math.sin(t * 83) * k * 0.3, 0) * CFrame.Angles(math.sin(t * 57) * k * 0.02, 0, math.sin(t * 61) * k * 0.02)
		end
		c.CFrame = cf
		fovNow += (R.cam.fov - fovNow) * 0.12
		c.FieldOfView = fovNow
		fit(ui)
	end)
	-- a death or a match grabbing you ends it
	local function bail() R.result = "done"; R.skip = true end
	table.insert(R.conns, me:GetAttributeChangedSignal("Zone"):Connect(function() if me:GetAttribute("Zone") == "match" then bail() end end))
	local hum = me.Character and me.Character:FindFirstChildOfClass("Humanoid")
	if hum then table.insert(R.conns, hum.Died:Connect(bail)) end

	-- the answer: asked for now (the container is already on its way down), then what it needs made while it rattles
	if ask then
		task.spawn(function()
			local okA, r = pcall(ask)
			Timing.mark("reply")
			R.res = if okA and type(r) == "table" then r else { ok = false, why = "couldn't reach the till." }
			prep(R)
		end)
	else
		task.defer(prep, R) -- (after runMany has put its containers down: the ring's prizes go over them)
	end
	current = R
	local many = count > 1
	local ok, out = pcall(if many then runMany else run, R)
	current = nil
	restore(R, ok and out == "again" and R.opts.chain == true)
	running = false
	Timing.mark("closed")
	if not ok then
		warn("[jankfire] the opening broke: " .. tostring(out))
		return "done"
	end
	return out
end

-- ---------------------------------------------------------------- a reward that isn't from a container
-- (the shop session's VIP daily reward, 17 Nov: a VIP talks to Trisangle in the VIP room once a day and gets a random
-- prize, shown in the openings' style.) no container and no camera move: the reel over the blurred world, landing on
-- the prize; then the prize big in the middle with its name, EQUIP (an item that goes on a gun) and DONE.
-- spec = { title = "DAILY REWARD", who = "Trisangle"?, line = "Here."?, prize = P, reel = { P, ... } } where
-- P = { kind = "brass" | "container" | "wrap" | "hat" | "skin" (or a hook's type), id, n?, name, rarity, weapon? }
-- (id: "brass", a container's kind, or the item's id). the prize goes on the landing card. it gives nothing: the
-- caller grants first. yields until DONE and returns "done" ("busy" while an opening runs)
local function rewardItem(x: any): any
	if type(x) ~= "table" then return nil end
	local kind = if type(x.kind) == "string" then x.kind elseif type(x.type) == "string" then x.type else nil
	if not kind or type(x.id) ~= "string" then return nil end
	local rarity = if type(x.rarity) == "string" and LootTable.RARITY[x.rarity] then x.rarity else "common"
	local name: string? = if type(x.name) == "string" and x.name ~= "" then x.name else nil
	if not name then
		local i = LootTable.info(kind, x.id)
		local c = LootTable.CONTAINERS[x.id]
		name = if i then i.name elseif kind == "container" and c then c.name else x.id
	end
	return { type = kind, id = x.id, key = x.id, name = name, rarity = rarity, n = tonumber(x.n) or 1,
		weapon = if type(x.weapon) == "string" then x.weapon else nil }
end
local KIND_WORD = { brass = "Coins", container = "Container" } -- (Brass in the code is Coins on screen, 18 Nov)

local function rewardRun(R: Run, spec: any, prize: any, items: { any }, stop: number): string
	local ui = R.ui
	ui.title.Text = string.upper(if type(spec.title) == "string" and spec.title ~= "" then spec.title else "REWARD")
	local sub = {}
	if type(spec.who) == "string" and spec.who ~= "" then table.insert(sub, "FROM " .. string.upper(spec.who)) end
	if type(spec.line) == "string" and spec.line ~= "" then table.insert(sub, spec.line) end
	ui.odds.Text = table.concat(sub, "  ·  ")
	tw(ui.title, 0.4, { TextTransparency = 0 }); tw(ui.odds, 0.4, { TextTransparency = 0.1 })
	tw(R.blur, 0.4, { Size = 18 })
	tw(R.tint, 0.4, { Brightness = -0.06, Saturation = -0.5, Contrast = 0.05 })
	hold(R, 0.3)

	-- the reel, as an opening's
	local win = spinReel(R, items, stop, if R.skip then TIME.spinQuick else TIME.spin)
	local col = rcol(prize.rarity)
	for _, c in ui.strip:GetChildren() do
		if c:IsA("Frame") and c ~= win then
			local dim = c:FindFirstChild("Dim")
			if dim then tw(dim :: Frame, 0.3, { BackgroundTransparency = 0.5 }) end
		end
	end
	local sc = new("UIScale", { Scale = 1 }, win)
	tw(sc, 0.35, { Scale = 1.1 }, Enum.EasingStyle.Back)
	local stroke = win:FindFirstChildOfClass("UIStroke")
	if stroke then stroke.Color = col; stroke.Transparency = 0; stroke.Thickness = 3 end
	ui.flash.BackgroundColor3 = col
	ui.flash.BackgroundTransparency = 0.72
	tw(ui.flash, 0.8, { BackgroundTransparency = 1 })
	local rank = RANK[prize.rarity] or 1
	local stings = ({ { "loot_win_common", "ting" }, { "loot_win_rare", "ting" }, { "loot_win_epic", "round_start" }, { "loot_win_legendary", "round_end", "round_start" } })[rank]
	snd(stings, nil, 1, 1)
	if not R.result then R.skip = false end
	hold(R, TIME.land)

	-- the prize: its card big in the middle, the rarity's colour soft behind it
	tw(ui.reel, 0.3, { Position = UDim2.fromOffset(960, 600), BackgroundTransparency = 1 })
	task.delay(0.3, function() ui.reel.Visible = false end)
	ui.skip.Visible = false
	-- (in the space between the title and the reveal: on a phone both are boosted, so the card is a little smaller)
	local top, bot = middle(ui)
	local bigK = math.min(1.65, (bot - top - 30) / (CARD_H + 44))
	local holder = new("Frame", { Name = "Prize", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromOffset(960, (top + bot) / 2),
		Size = UDim2.fromOffset(CARD_W, CARD_H), ZIndex = 5 }, ui.stage)
	local halo = new("Frame", { Name = "Halo", BackgroundColor3 = col, BackgroundTransparency = 1, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.new(1, 44, 1, 44) }, holder)
	T.corner(halo, 18)
	local big = card(holder, prize, 0)
	local bst = big:FindFirstChildOfClass("UIStroke")
	if bst then bst.Color = col; bst.Transparency = 0; bst.Thickness = 2 end
	local hs = new("UIScale", { Scale = bigK * 0.66 }, holder)
	tw(hs, 0.5, { Scale = bigK }, Enum.EasingStyle.Back)
	tw(halo, 0.5, { BackgroundTransparency = 0.82 })

	-- the words and the buttons
	local word = KIND_WORD[prize.type] or LootTable.TYPE_NAMES[prize.type] or "Item"
	ui.rKind.Text = rname(prize.rarity) .. "  ·  " .. string.upper(word)
	ui.rKind.TextColor3 = col
	ui.rName.Text = string.upper(prize.name or prize.id or "")
	local wid = gunOf(prize)
	local we = wid and Roster.byId[wid]
	ui.rOn.Text = if prize.type == "skin" and we then "a new look for your " .. we.name
		elseif we and prize.weapon then "for your " .. we.name .. " only"
		elseif LootTable.cardLook(prize.type) then "for your player card" else ""
	local can = canEquip(prize)
	ui.equip.Visible = can
	ui.equip.Text = if can and wid then "EQUIP ON " .. string.upper(Roster.byId[wid].name) else "EQUIP"
	ui.equip.Size = UDim2.fromOffset(math.max(250, #ui.equip.Text * 13 + 40), 56)
	ui.again.Visible = false
	local row = {}
	for _, b in { ui.equip, ui.done } do if b.Visible then table.insert(row, b) end end
	layRow(ui, row)
	ui.reveal.Visible = true
	ui.reveal.Position = UDim2.fromOffset(960, 1060)
	tw(ui.reveal, 0.4, { Position = UDim2.fromOffset(960, 1030) })
	local fire = if prize.rarity == "legendary" then revealFire(ui.gui, col) else nil

	local answer: string? = nil
	ui.done.MouseButton1Click:Connect(function() answer = "done" end)
	ui.equip.MouseButton1Click:Connect(function()
		if not can or ui.equip.Text == "EQUIPPED" or ui.equip.Text == "..." then return end
		ui.equip.Text = "..."
		local ok, why = equipItem(prize)
		if ok then
			ui.equip.Text = "EQUIPPED"
			ui.equip.BackgroundColor3 = T.CARD
			ui.equip.TextColor3 = T.TEXT
			pcall(Sfx.play, "click")
		else
			ui.equip.Text = string.upper(why or "couldn't equip")
		end
	end)
	while not answer do
		if R.result then answer = R.result end
		RunService.RenderStepped:Wait()
	end

	-- away
	fireOut(fire)
	tw(ui.reveal, 0.25, { Position = UDim2.fromOffset(960, 1100) })
	tw(hs, 0.25, { Scale = bigK * 0.75 })
	for _, d in holder:GetDescendants() do
		if d:IsA("Frame") then tw(d, 0.25, { BackgroundTransparency = 1 })
		elseif d:IsA("TextLabel") then tw(d, 0.25, { TextTransparency = 1 }) end
	end
	tw(R.blur, 0.3, { Size = 0 })
	tw(R.tint, 0.3, { Brightness = 0, Saturation = 0, Contrast = 0 })
	tw(ui.title, 0.25, { TextTransparency = 1 }); tw(ui.odds, 0.25, { TextTransparency = 1 })
	local t0 = os.clock()
	while os.clock() - t0 < 0.3 do RunService.RenderStepped:Wait() end
	return answer :: string
end

function Opening.reward(spec: any): string
	if running then return "busy" end
	if type(spec) ~= "table" then return "done" end
	local prize = rewardItem(spec.prize)
	if not prize then return "done" end
	-- the reel: the entries given, round again till it's long enough to spin, the prize on the landing card
	local given = {}
	for _, x in (if type(spec.reel) == "table" then spec.reel else {}) do
		local it = rewardItem(x)
		if it then table.insert(given, it) end
	end
	if #given == 0 then given = { prize } end
	local rng = Random.new()
	local items = {}
	local N = math.max(#given, 36)
	for i = 1, N do items[i] = given[(i - 1) % #given + 1] end
	for i = #items, 2, -1 do local j = rng:NextInteger(1, i); items[i], items[j] = items[j], items[i] end
	local stop = N - rng:NextInteger(5, 8)
	items[stop] = prize

	running = true
	local cam = workspace.CurrentCamera :: Camera
	local ui = buildUi()
	ui.quick.Visible = false -- (a reward: QUICK OPEN is the containers')
	local R: Run = {
		ui = ui, kind = "reward", res = { ok = true, prize = prize }, opts = {}, skip = false, skipAt = 0, result = nil,
		box = nil, prize = nil, base = cam.CFrame, flat = cam.CFrame.LookVector, height = 0, light = nil, rim = nil,
		cam = { from = cam.CFrame, to = cam.CFrame, t0 = os.clock(), dur = 0.01, shake = 0, shakeT = 0, fov = cam.FieldOfView },
		blur = new("BlurEffect", { Name = "JankLootBlur", Size = 0 }, cam),
		tint = new("ColorCorrectionEffect", { Name = "JankLootTint" }, cam),
		dof = new("DepthOfFieldEffect", { Name = "JankLootDof", Enabled = false }, cam),
		hidden = {}, saved = { cf = cam.CFrame, type = cam.CameraType, fov = cam.FieldOfView, loadoutOpen = me:GetAttribute("LoadoutOpen") },
		conns = {}, spin = 0, prizeY = 0, wid = nil, boxes = nil, layout = nil,
	}
	-- (as an opening: the HUD and menus step aside, your hands and the other screens' keys hold still; the camera stays
	-- where it was, only the world goes soft)
	for _, g in (me:WaitForChild("PlayerGui")):GetChildren() do
		if g:IsA("ScreenGui") and g ~= ui.gui and g.Enabled then R.hidden[g] = true; g.Enabled = false end
	end
	me:SetAttribute("LoadoutOpen", true)
	me:SetAttribute("LootOpening", "reward")
	MenuCursor.set("loot", true, function() return running end)
	pcall(function()
		local controls = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls()
		controls:Disable()
	end)
	ContextActionService:BindActionAtPriority("JankLootSink", function(_, state, io)
		if state == Enum.UserInputState.Begin and (io.KeyCode == Enum.KeyCode.Space or io.KeyCode == Enum.KeyCode.ButtonA) then
			R.skip = true
		end
		return Enum.ContextActionResult.Sink
	end, false, 3000, Enum.KeyCode.Space, Enum.KeyCode.ButtonA, Enum.KeyCode.L, Enum.KeyCode.B, Enum.KeyCode.G, Enum.KeyCode.Q,
		Enum.KeyCode.E, Enum.KeyCode.R, Enum.KeyCode.F, Enum.KeyCode.T, Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three, Enum.KeyCode.Four, Enum.KeyCode.Tab)
	ui.skip.MouseButton1Click:Connect(function() R.skip = true end)
	table.insert(R.conns, RunService.RenderStepped:Connect(function() fit(ui) end))
	local function bail() R.result = "done"; R.skip = true end
	table.insert(R.conns, me:GetAttributeChangedSignal("Zone"):Connect(function() if me:GetAttribute("Zone") == "match" then bail() end end))
	local hum = me.Character and me.Character:FindFirstChildOfClass("Humanoid")
	if hum then table.insert(R.conns, hum.Died:Connect(bail)) end

	current = R
	local ok, out = pcall(rewardRun, R, spec, prize, items, stop)
	current = nil
	-- (restore puts the camera's type and field of view back as they were: unchanged here)
	restore(R)
	running = false
	if not ok then
		warn("[jankfire] the reward didn't draw: " .. tostring(out))
		return "done"
	end
	return out
end

-- (for others: the shop's previews, LootShow.client.luau; the gift present's reveal, GiftReveal.client: card + its size)
Opening.card = card
Opening.CARD = { w = CARD_W, h = CARD_H }
Opening.container = container
Opening.openBox = openBox
Opening.prizeModel = prizeModel

return Opening
