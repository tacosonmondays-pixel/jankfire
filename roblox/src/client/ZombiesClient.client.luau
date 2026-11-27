--!strict
-- ZOMBIES, your side (the server runs the mode: server/Zombies.luau). while you're in a zombies game (attribute ZmOn):
-- your credits with the +N for each hit and kill, the round number and what's left, the break's countdown, your spare
-- rounds, what a buy said, the down screen (bleeding out, with how long), and the end. plain labels only (the owner:
-- no flavour text). the game's state is on the arena model (Round, St, Left, BreakUntil); yours is on you (ZmC, ZmDown,
-- ZmOut, ZmRes_<weapon>, Loadout)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local ProximityPromptService = game:GetService("ProximityPromptService")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Weapons = require(Shared:WaitForChild("Weapons"))
local ZM = require(Shared:WaitForChild("ZM"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local T = require(script.Parent:WaitForChild("Theme")) :: any
local Body = require(script.Parent:WaitForChild("Body")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local okSfx, Sfx = pcall(require, script.Parent:WaitForChild("Sfx"))
local me = Players.LocalPlayer
local W = Weapons.list
local GREEN = Color3.fromHex("8fd14f")

-- a bought shutter rolls up into its housing (26 Nov 2026, the owner: "doors dont have animations the ones you buy"):
-- the shutter is hidden here and drawn as slats that rise together, each one gone as it passes into the housing (or
-- the wall over the door), with the recorded rattle (zm_door) from the door. local parts only, a few writes a frame for
-- ZM.R.doorRoll s. the server hides the real shutter itself once the roll is over
local rolled: { [Instance]: boolean } = setmetatable({}, { __mode = "k" }) :: any
local function rollUp(sh: BasePart)
	if rolled[sh] or not sh.Parent then return end
	rolled[sh] = true
	local cf, size = sh.CFrame, sh.Size
	local thinX = size.X <= size.Z
	local wide, thick, H = if thinX then size.Z else size.X, math.min(size.X, size.Z), size.Y
	local N = math.max(4, math.floor(H / 1.15 + 0.5))
	local h = H / N
	local holder = Instance.new("Folder")
	holder.Name = "ZmRoll"
	local slats: { BasePart } = {}
	local dark = sh.Color:Lerp(Color3.new(0, 0, 0), 0.18)
	for k = 1, N do
		local p = Instance.new("Part")
		p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch = true, false, false, false
		p.Material = sh.Material
		p.Color = if k == 1 then sh.Color:Lerp(Color3.new(0, 0, 0), 0.45) elseif k % 2 == 0 then sh.Color else dark -- (the bottom rail darker)
		p.TopSurface, p.BottomSurface = Enum.SurfaceType.Smooth, Enum.SurfaceType.Smooth
		local t = if k == 1 then thick * 1.05 else thick * 0.82
		p.Size = if thinX then Vector3.new(t, h - 0.08, wide) else Vector3.new(wide, h - 0.08, t)
		p.CFrame = cf * CFrame.new(0, -H / 2 + (k - 0.5) * h, 0)
		p.Parent = holder
		slats[k] = p
	end
	holder.Parent = workspace
	sh.Transparency = 1 -- (here only: the server's copy follows when the roll is done)
	if okSfx and Sfx then pcall((Sfx :: any).play, "zm_door", cf.Position + Vector3.new(0, H * 0.3, 0)) end
	local dur = ZM.R.doorRoll
	local t0 = os.clock()
	local conn: RBXScriptConnection? = nil
	conn = RunService.RenderStepped:Connect(function()
		local a = math.clamp((os.clock() - t0) / dur, 0, 1)
		-- a motor's roll: a slow start, steady, eased into the top
		local e = if a < 0.15 then (a / 0.15) ^ 2 * 0.075 elseif a > 0.85 then 1 - ((1 - a) / 0.15) ^ 2 * 0.075 else 0.075 + (a - 0.15) / 0.7 * 0.85
		local rise = H * e
		for k, p in slats do
			local y = -H / 2 + (k - 0.5) * h + rise
			if y - h / 2 >= H / 2 - 0.05 then
				if p.Parent then p.Parent = nil end -- (wound into the housing)
			else
				p.CFrame = cf * CFrame.new(0, y, 0)
			end
		end
		if a >= 1 then
			if conn then conn:Disconnect() end
			holder:Destroy()
		end
	end)
end

local gui = T.new("ScreenGui", { Name = "JankZombies", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6, Enabled = false }, me:WaitForChild("PlayerGui"))
local root = T.scaled(gui)

-- credits (top left, under the level bar)
local cPlate = T.plate(root, "Credits", UDim2.fromOffset(16, 104), UDim2.fromOffset(170, 44))
local cLabel = T.text(cPlate, "Label", "CREDITS", 12, T.MUTED, T.FONT_BOLD)
cLabel.Position = UDim2.fromOffset(12, 4); cLabel.Size = UDim2.fromOffset(100, 14)
local cNum = T.text(cPlate, "Num", "500", 22, T.ACCENT, T.FONT_HEAVY)
cNum.Position = UDim2.fromOffset(12, 17); cNum.Size = UDim2.fromOffset(150, 24)
local pops = T.new("Frame", { Name = "Pops", BackgroundTransparency = 1, Position = UDim2.fromOffset(192, 104), Size = UDim2.fromOffset(120, 44) }, root)
local chips = T.new("Frame", { Name = "Chips", BackgroundTransparency = 1, Position = UDim2.fromOffset(16, 152), Size = UDim2.fromOffset(420, 120) }, root)
T.new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, chips)
local chipList: { Frame } = {}
local function setChips(rows: { { text: string, color: Color3 } })
	for i, r in rows do
		local c = chipList[i]
		if not c then
			c = T.plate(chips, "Chip", UDim2.new(), UDim2.fromOffset(170, 22))
			local l = T.text(c, "Text", "", 12, T.TEXT, T.FONT_BOLD)
			l.Position = UDim2.fromOffset(16, 0); l.Size = UDim2.new(1, -20, 1, 0)
			local dot = T.new("Frame", { Name = "Dot", BorderSizePixel = 0, Position = UDim2.fromOffset(6, 7), Size = UDim2.fromOffset(6, 8) }, c)
			T.corner(dot, 2)
			chipList[i] = c
		end
		c.LayoutOrder = i
		c.Visible = true
		;(c:FindFirstChild("Text") :: TextLabel).Text = r.text
		;(c:FindFirstChild("Dot") :: Frame).BackgroundColor3 = r.color
	end
	for i = #rows + 1, #chipList do chipList[i].Visible = false end
end

-- the round (bottom left, over the HP card): the number, what's left
local rPlate = T.plate(root, "Round", UDim2.new(0, 16, 1, -206), UDim2.fromOffset(170, 66))
local rLabel = T.text(rPlate, "Label", "ROUND", 12, T.MUTED, T.FONT_BOLD)
rLabel.Position = UDim2.fromOffset(12, 6); rLabel.Size = UDim2.fromOffset(80, 14)
local rNum = T.text(rPlate, "Num", "0", 34, Color3.fromHex("ff5a3a"), T.FONT_TITLE)
rNum.Position = UDim2.fromOffset(12, 20); rNum.Size = UDim2.fromOffset(70, 40)
local rLeft = T.text(rPlate, "Left", "", 13, T.SOFT, T.FONT, Enum.TextXAlignment.Right)
rLeft.Position = UDim2.fromOffset(80, 36); rLeft.Size = UDim2.fromOffset(80, 18)

-- your spare rounds (bottom right, over the ammo card)
local aPlate = T.plate(root, "Spare", UDim2.new(1, -260, 1, -196), UDim2.fromOffset(244, 30)) -- (over the item card)
local aText = T.text(aPlate, "Text", "", 13, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Right)
aText.Position = UDim2.fromOffset(10, 0); aText.Size = UDim2.new(1, -20, 1, 0)

-- the middle: a banner (ROUND 3, the break's countdown), what a buy said
local banner = T.text(root, "Banner", "", 34, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
banner.AnchorPoint = Vector2.new(0.5, 0); banner.Position = UDim2.new(0.5, 0, 0, 120); banner.Size = UDim2.fromOffset(600, 44)
local sub = T.text(root, "Sub", "", 16, T.SOFT, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
sub.AnchorPoint = Vector2.new(0.5, 0); sub.Position = UDim2.new(0.5, 0, 0, 164); sub.Size = UDim2.fromOffset(600, 22)
local toast = T.text(root, "Toast", "", 15, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
toast.AnchorPoint = Vector2.new(0.5, 0); toast.Position = UDim2.new(0.5, 0, 0.5, 46); toast.Size = UDim2.fromOffset(500, 20)
local toastT = 0
local bannerT = 0

-- a boss: its name and HP, top middle
local bossF = T.plate(root, "Boss", UDim2.new(0.5, -200, 0, 70), UDim2.fromOffset(400, 40))
bossF.Visible = false
local bossName = T.text(bossF, "Name", "", 13, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
bossName.Position = UDim2.fromOffset(0, 3); bossName.Size = UDim2.new(1, 0, 0, 16)
local bossTrack = T.new("Frame", { Name = "Track", BorderSizePixel = 0, BackgroundColor3 = T.TRACK, Position = UDim2.fromOffset(12, 24), Size = UDim2.new(1, -24, 0, 8) }, bossF)
T.corner(bossTrack, 3)
local bossFill = T.new("Frame", { Name = "Fill", BorderSizePixel = 0, BackgroundColor3 = T.DANGER, Size = UDim2.fromScale(1, 1) }, bossTrack)
T.corner(bossFill, 3)

-- down: a red edge, how long you have
local downF = T.new("Frame", { Name = "Down", BackgroundColor3 = Color3.fromRGB(120, 0, 0), BackgroundTransparency = 0.65, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), Visible = false }, gui)
local downT = T.text(downF, "Text", "DOWN", 40, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center, true)
downT.AnchorPoint = Vector2.new(0.5, 0.5); downT.Position = UDim2.fromScale(0.5, 0.42); downT.Size = UDim2.fromOffset(600, 50)
local downS = T.text(downF, "Sub", "", 18, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center, true)
downS.AnchorPoint = Vector2.new(0.5, 0.5); downS.Position = UDim2.fromScale(0.5, 0.42 + 0.06); downS.Size = UDim2.fromOffset(600, 24)

-- the end: how far the squad got, everyone's numbers
local over = T.plate(root, "Over", UDim2.new(0.5, -260, 0.5, -150), UDim2.fromOffset(520, 300))
over.Visible = false
over.AnchorPoint = Vector2.new(0, 0)
local oTitle = T.text(over, "Title", "", 28, T.TEXT, T.FONT_SHOUT, Enum.TextXAlignment.Center)
oTitle.Position = UDim2.fromOffset(0, 14); oTitle.Size = UDim2.new(1, 0, 0, 34)
local oRows = T.new("Frame", { Name = "Rows", BackgroundTransparency = 1, Position = UDim2.fromOffset(20, 62), Size = UDim2.new(1, -40, 1, -76) }, over)
T.new("UIListLayout", { Padding = UDim.new(0, 4), SortOrder = Enum.SortOrder.LayoutOrder }, oRows)

local function arena(): Instance?
	local n = me:GetAttribute("ZmArena")
	return if type(n) == "string" then workspace:FindFirstChild(n) else nil
end
local function pop(d: number, why: string)
	local col = if d < 0 then T.DANGER elseif why == "head" or why == "melee" then T.ACCENT else GREEN
	local l = T.text(pops, "Pop", (if d > 0 then "+" else "") .. tostring(d), 16, col, T.FONT_HEAVY, Enum.TextXAlignment.Left, true)
	l.Position = UDim2.fromOffset(0, 12); l.Size = UDim2.fromOffset(120, 20)
	T.tween(l, 0.9, { Position = UDim2.fromOffset(0, -10), TextTransparency = 1, TextStrokeTransparency = 1 })
	task.delay(1, function() l:Destroy() end)
end
local function say(text: string, ok: boolean?)
	toast.Text = text
	toast.TextColor3 = if ok == false then T.DANGER else T.TEXT
	toastT = os.clock() + 1.8
end
local function show(text: string, s: string?, dur: number?)
	banner.Text = text
	sub.Text = s or ""
	bannerT = os.clock() + (dur or 2.5)
end
local function row(cells: { string }, bold: boolean, order: number)
	local f = T.new("Frame", { BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 22), LayoutOrder = order }, oRows)
	local xs = { 0, 0.42, 0.55, 0.68, 0.81 }
	for i, c in cells do
		local l = T.text(f, "C" .. i, c, 14, if bold then T.MUTED else T.TEXT, if bold then T.FONT_BOLD else T.FONT, if i == 1 then Enum.TextXAlignment.Left else Enum.TextXAlignment.Right)
		l.Position = UDim2.fromScale(xs[i], 0)
		l.Size = UDim2.new(if i == 1 then 0.4 else 0.12, 0, 1, 0)
	end
end

local zr = Remotes:WaitForChild("Zm") :: RemoteEvent
zr.OnClientEvent:Connect(function(x: any)
	if type(x) ~= "table" then return end
	if x.k == "c" then
		cNum.Text = tostring(x.c)
		if type(x.d) == "number" and x.d ~= 0 and x.why ~= "test" then pop(x.d, tostring(x.why)) end
	elseif x.k == "buy" then
		say(tostring(x.m or ""), x.ok == true)
	elseif x.k == "round" then
		if x.st == "start" then show("ROUND " .. tostring(x.n), nil, 3) else show("ROUND " .. tostring(x.n) .. " CLEARED", nil, 3) end
	elseif x.k == "door" then
		say(if x.by then tostring(x.by) .. " opened " .. tostring(x.label) else tostring(x.label) .. " open", true)
		if typeof(x.sh) == "Instance" and x.sh:IsA("BasePart") then rollUp(x.sh) end
	elseif x.k == "down" then
		if x.st == "down" then say(tostring(x.who) .. " is down", false)
		elseif x.st == "up" then say(tostring(x.who) .. " is back up", true)
		elseif x.st == "out" then say(tostring(x.who) .. " is out", false) end
	elseif x.k == "power" then
		show("POWER ON", nil, 2.5)
	elseif x.k == "mach" then
		if x.st == "win" then
			local def = ZM.MODS[tostring(x.mod)]
			show(tostring(x.name or ""), if def then def.desc else nil, 3)
		end
	elseif x.k == "drop" then
		local def = nil
		for _, d in ZM.DROPS do if d.name == x.name then def = d end end
		show(tostring(x.name), if def then def.desc else nil, 2.5)
	elseif x.k == "boss" then
		if x.st == "warn" then show(tostring(x.name), "on the way", 3)
		elseif x.st == "meeting" then say(tostring(x.name) .. " called a meeting", false)
		elseif x.st == "dead" then show(tostring(x.name) .. " DOWN", nil, 3) end
	elseif x.k == "over" then
		for _, c in oRows:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
		oTitle.Text = "GAME OVER  ·  ROUND " .. tostring(x.n)
		row({ "PLAYER", "KILLS", "HEADS", "DOWNS", "REVIVES" }, true, 0)
		for i, r in (x.rows or {}) :: { any } do row({ tostring(r[1]), tostring(r[2]), tostring(r[3]), tostring(r[4]), tostring(r[5]) }, false, i) end
		over.Visible = true
	end
end)

-- your own revive prompt is for the others
ProximityPromptService.PromptShown:Connect(function(pr: ProximityPrompt)
	if pr:GetAttribute("Downed") == me.UserId then pr.Enabled = false end
end)

local CRATE_IDS = {}
for id in ZM.CRATE do if W[id] then table.insert(CRATE_IDS, id) end end
local spinModel: Model? = nil
local spinId = ""
local spinNext = 0
local built: { [string]: Model } = {} -- (each gun built once, shown and hidden)
local function showWeapon(id: string, at: CFrame)
	if spinId ~= id or not spinModel then
		if spinModel then spinModel.Parent = nil end
		spinModel = nil
		spinId = id
		local m = built[id]
		if not m then
			local ok, b = pcall(WeaponModels.build, id, 3)
			if ok and b then
				for _, d in (b :: Model):GetDescendants() do
					if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
				end
				m = b :: Model
				built[id] = m
			end
		end
		if m then m.Parent = workspace; spinModel = m end
	end
	if spinModel then spinModel:PivotTo(at * CFrame.Angles(0, os.clock() * 1.6, 0)) end
end
local function crateTick(a: Instance?)
	local cm = a and a:FindFirstChild("ZMExtra") and (a :: any).ZMExtra:FindFirstChild("Crate")
	local spin, offer = cm and cm:GetAttribute("Spin"), cm and cm:GetAttribute("Offer")
	local t = workspace:GetServerTimeNow()
	local body = cm and cm:FindFirstChild("Body") :: BasePart?
	if body and type(spin) == "number" and t < spin then
		if os.clock() >= spinNext then spinNext = os.clock() + 0.12; spinId = "" end
		local id = if spinId ~= "" then spinId else CRATE_IDS[math.random(1, #CRATE_IDS)]
		showWeapon(id, body.CFrame * CFrame.new(0, 3.2, 0))
	elseif body and type(offer) == "number" and t < offer then
		showWeapon(tostring(cm:GetAttribute("W")), body.CFrame * CFrame.new(0, 3.2, 0))
	elseif spinModel then
		spinModel.Parent = nil; spinModel = nil; spinId = ""
	end
end

-- the wall guns (26 Nov 2026: a map's WallBuys were bare markers, only a prompt up close): each gets a chalk outline on
-- the wall, its gun hung inside it, and a small lamp over it so a buy reads from across a dark room. built here, once per
-- game, from the arena copy's ZM/WallBuys (the markers: 4 x 2 on the wall, LookVector out of it)
local buyArt: Folder? = nil
local buyFor: Instance? = nil
local CHALK = Color3.fromRGB(222, 226, 232)
local function buildBuys(a: Instance?)
	if buyFor == a then return end
	buyFor = a
	if buyArt then buyArt:Destroy(); buyArt = nil end
	local zf = a and a:FindFirstChild("ZM")
	local wb = zf and zf:FindFirstChild("WallBuys")
	if not wb then return end
	local f = Instance.new("Folder")
	f.Name = "ZmBuyArt"
	local function bar(cf: CFrame, size: Vector3)
		local p = Instance.new("Part")
		p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
		p.Material = Enum.Material.SmoothPlastic
		p.Color = CHALK
		p.Transparency = 0.12
		p.Size = size
		p.CFrame = cf
		p.Parent = f
	end
	for _, m in wb:GetChildren() do
		if not m:IsA("BasePart") then continue end
		local wid = tostring(m:GetAttribute("Weapon") or "")
		local cf = m.CFrame -- (LookVector out of the wall)
		local face = cf * CFrame.new(0, 0, -0.07)
		local w, h, t = 5.2, 2.6, 0.12
		bar(face * CFrame.new(0, h / 2, 0), Vector3.new(w + t, t, 0.05))
		bar(face * CFrame.new(0, -h / 2, 0), Vector3.new(w + t, t, 0.05))
		bar(face * CFrame.new(-w / 2, 0, 0), Vector3.new(t, h + t, 0.05))
		bar(face * CFrame.new(w / 2, 0, 0), Vector3.new(t, h + t, 0.05))
		local ok, g = pcall(WeaponModels.build, wid, 3)
		if ok and g then
			for _, d in (g :: Model):GetDescendants() do
				if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
			end
			local at = cf.Position + cf.LookVector * 0.45
			;(g :: Model):PivotTo(CFrame.lookAt(at, at + cf.RightVector)) -- (lying along the wall, side on)
			local _, size = (g :: Model):GetBoundingBox()
			if size.Magnitude > 7 then (g :: Model):ScaleTo(math.max(0.3, 6.5 / size.Magnitude)) end -- (a long gun fits the outline)
			;(g :: Model).Parent = f
		end
		local lampPart = Instance.new("Part")
		lampPart.Anchored, lampPart.CanCollide, lampPart.CanQuery, lampPart.CanTouch = true, false, false, false
		lampPart.Transparency = 1
		lampPart.Size = Vector3.new(0.2, 0.2, 0.2)
		lampPart.CFrame = cf * CFrame.new(0, 2.6, -1.6)
		local l = Instance.new("PointLight")
		l.Brightness, l.Range, l.Color, l.Shadows = 0.9, 9, Color3.fromRGB(226, 234, 255), false
		l.Parent = lampPart
		lampPart.Parent = f
	end
	f.Parent = workspace
	buyArt = f
end

RunService.RenderStepped:Connect(function()
	local on = me:GetAttribute("ZmOn") == true
	local spd = me:GetAttribute("ZmSpeed")
	Body.zm = if on and type(spd) == "number" then spd else 1
	local show = on and me:GetAttribute("ZmFilm") ~= true -- (27 Nov: ZombieCine's films have the screen; the HUD waits)
	if gui.Enabled ~= show then
		gui.Enabled = show
		if not on then over.Visible = false; banner.Text = ""; toast.Text = "" end
	end
	if not on then
		if spinModel then spinModel.Parent = nil; spinModel = nil end
		if buyFor then buildBuys(nil) end
		return
	end
	local a = arena()
	crateTick(a)
	if a ~= buyFor then buildBuys(a) end
	-- the chips: no power yet, the modifiers running (time left), your colas
	local rows = {}
	if a and a:GetAttribute("Power") == false then table.insert(rows, { text = "NO POWER", color = T.DIM }) end
	local mods = a and a:GetAttribute("Mods")
	if type(mods) == "string" then
		for _, e in string.split(mods, ",") do
			local bits = string.split(e, ":")
			local def = ZM.MODS[bits[1]]
			local who = tonumber(bits[3]) or 0
			if def and (def.team or who == me.UserId) then
				local left = math.max(0, math.ceil((tonumber(bits[2]) or 0) - workspace:GetServerTimeNow()))
				table.insert(rows, { text = def.name .. "  " .. left, color = def.color })
			end
		end
	end
	local colas = me:GetAttribute("ZmColas")
	if type(colas) == "string" then
		for _, id in string.split(colas, ",") do
			local def = ZM.COLAS[id]
			if def then table.insert(rows, { text = def.name, color = def.color }) end
		end
	end
	setChips(rows)
	-- the boss bar
	local bn = a and a:GetAttribute("BossName")
	local bh, bm = a and a:GetAttribute("BossHp"), a and a:GetAttribute("BossMax")
	bossF.Visible = type(bn) == "string" and type(bh) == "number" and type(bm) == "number" and bm > 0
	if bossF.Visible then
		bossName.Text = tostring(bn)
		bossFill.Size = UDim2.fromScale(math.clamp((bh :: number) / (bm :: number), 0, 1), 1)
	end
	local st = a and a:GetAttribute("St")
	rNum.Text = tostring(a and a:GetAttribute("Round") or 0)
	local left = a and a:GetAttribute("Left")
	rLeft.Text = if st == "live" and type(left) == "number" then left .. " left" else ""
	local bu = a and a:GetAttribute("BreakUntil")
	if type(bu) == "number" and (st == "pre" or st == "break") then
		local s = math.max(0, math.ceil(bu - workspace:GetServerTimeNow()))
		banner.Text = "ROUND " .. tostring((tonumber(a and a:GetAttribute("Round")) or 0) + 1)
		sub.Text = "in " .. s
		bannerT = os.clock() + 0.2
	end
	if os.clock() > bannerT then banner.Text = ""; sub.Text = "" end
	if os.clock() > toastT then toast.Text = "" end
	local c = me:GetAttribute("ZmC")
	if type(c) == "number" then cNum.Text = tostring(c) end
	-- spare rounds, gun by gun (in your keys' order)
	local lo = me:GetAttribute("Loadout")
	local bits = {}
	if type(lo) == "string" then
		for _, wid in string.split(lo, ",") do
			local r = me:GetAttribute("ZmRes_" .. wid)
			if type(r) == "number" then table.insert(bits, ((W[wid] and W[wid].name) or wid) .. "  +" .. r) end
		end
	end
	aText.Text = table.concat(bits, "     ")
	aPlate.Visible = #bits > 0
	-- down
	local dn = me:GetAttribute("ZmDown")
	local out = me:GetAttribute("ZmOut") == true
	downF.Visible = (type(dn) == "number" or out) and not over.Visible -- (the results take over at the end)
	if type(dn) == "number" then
		downT.Text = "DOWN"
		downS.Text = "bleeding out  " .. math.max(0, math.ceil(dn - workspace:GetServerTimeNow()))
	elseif out then
		downT.Text = "OUT"
		downS.Text = "back next round"
	end
end)
