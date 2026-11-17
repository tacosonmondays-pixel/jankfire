--!strict
-- the classic modes on your screen (server/Modes.luau; the numbers in Shared.ModeConfig, the web HUD in
-- roblox/docs/MODES.md). requiring ModeConfig puts the modes' cards on the Play screen's MODES tab. in a mode's match:
--   * a strip under the scoreboard: GUN GAME your weapon, the next one and a pip per rung (the leader's marked);
--     ONE IN THE CHAMBER your bullets and lives; DUCK RAIN / RANDOMIZER the leader
--   * the end screen's two number columns named for the mode (RUNG / LIVES, KILLS)
--   * one in the chamber: out of lives, you watch the others from over their shoulder (click, Space or the arrows for
--     the next); the Reset button is off (a reset would cost a life)
--   * duck rain: each sky duck's shadow and blinking ring where it lands, the duck falling, LOOK UP when it's yours
--   * randomizer: what you rolled, for a moment, on every spawn
-- everything comes from the server: player attributes (ModeId, ModeMatch, ModeLadder, ModeRung, ModeLead, ModeLives,
-- ModeBullets, ModeOut, ModeLeft) and ItemFx { k = "skyduck" }
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StarterGui = game:GetService("StarterGui")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local ModeConfig = require(Shared:WaitForChild("ModeConfig")) -- (this fills PlayConfig.EXTRA: the MODES tab's cards)
local Weapons = require(Shared:WaitForChild("Weapons"))
local T = require(script.Parent:WaitForChild("Theme"))
local Hud = require(script.Parent:WaitForChild("Hud"))
local Sfx = require(script.Parent:WaitForChild("Sfx"))
local Replay: any = nil
pcall(function() Replay = require(script.Parent:WaitForChild("Replay", 10)) end)
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local me = Players.LocalPlayer
local W = Weapons.list
local S = Weapons.S

local gui = Instance.new("ScreenGui")
gui.Name = "JankfireModes"; gui.ResetOnSpawn = false; gui.IgnoreGuiInset = true; gui.DisplayOrder = 1
gui.Parent = me:WaitForChild("PlayerGui")
local hud = T.scaled(gui)

local function mode(): string? local v = me:GetAttribute("ModeId"); return if type(v) == "string" then v else nil end
local function kind(): string? local d = mode() and ModeConfig.byId[mode() :: string]; return if d then d.kind else nil end

-- ------------------------------------------------------------------ the strip under the scoreboard
local strip = T.new("Frame", {
	Name = "ModeStrip", AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 64), Size = UDim2.fromOffset(0, 30),
	AutomaticSize = Enum.AutomaticSize.X, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0, Visible = false,
}, hud)
T.corner(strip); T.edge(strip)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 16), PaddingRight = UDim.new(0, 16) }, strip)
local line = T.text(strip, "Line", "", 15, T.TEXT, T.FONT_BOLD, Enum.TextXAlignment.Center)
line.RichText = true; line.AutomaticSize = Enum.AutomaticSize.X; line.Size = UDim2.fromOffset(0, 30)
-- gun game's pips (one per rung) and one in the chamber's bullets and lives: a row under the line
local pips = T.new("Frame", { Name = "Pips", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 30),
	Size = UDim2.fromOffset(0, 14), AutomaticSize = Enum.AutomaticSize.X, Visible = false }, strip)
T.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center,
	Padding = UDim.new(0, 3), SortOrder = Enum.SortOrder.LayoutOrder }, pips)

local function hex(c: Color3): string return T.hex(c) end
local function quiet(s: string): string return ('<font color="%s">%s</font>'):format(hex(T.MUTED), s) end
local function pip(order: number, w: number, h: number, color: Color3, alpha: number): Frame
	local f = T.new("Frame", { Name = "Pip", LayoutOrder = order, BorderSizePixel = 0, BackgroundColor3 = color, BackgroundTransparency = alpha,
		Size = UDim2.fromOffset(w, h) }, pips)
	T.corner(f, 2)
	return f
end
local function gap(order: number, w: number) T.new("Frame", { Name = "Gap", LayoutOrder = order, BackgroundTransparency = 1, Size = UDim2.fromOffset(w, 1) }, pips) end
local function label(order: number, text: string)
	local l = T.text(pips, "Label", text, 11, T.MUTED, T.FONT_BOLD)
	l.LayoutOrder = order; l.AutomaticSize = Enum.AutomaticSize.X; l.Size = UDim2.fromOffset(0, 14)
end
local function lead(): (string?, number?)
	local v = me:GetAttribute("ModeLead")
	if type(v) ~= "string" then return nil, nil end
	local n, x = string.match(v, "^(.*)|(%-?%d+)$")
	return n, tonumber(x)
end

local lastKey = ""
local function draw()
	local k = kind()
	local inMatch = k ~= nil and type(me:GetAttribute("MatchHud")) == "string"
	strip.Visible = inMatch
	if not inMatch then lastKey = ""; return end
	local key = table.concat({ tostring(k), tostring(me:GetAttribute("ModeRung")), tostring(me:GetAttribute("ModeLead")), tostring(me:GetAttribute("ModeLives")),
		tostring(me:GetAttribute("ModeBullets")), tostring(me:GetAttribute("ModeOut")), tostring(me:GetAttribute("ModeLadder")) }, "/")
	if key == lastKey then return end
	lastKey = key
	for _, c in pips:GetChildren() do if c:IsA("GuiObject") then c:Destroy() end end
	local ln, lv = lead()
	if k == "gun" then
		local ladder = string.split(tostring(me:GetAttribute("ModeLadder") or ""), ",")
		local rung = tonumber(me:GetAttribute("ModeRung")) or 1
		local cur, nxt = W[ladder[rung]], W[ladder[rung + 1]]
		local name = if cur then ('<font color="%s">%s</font>'):format(hex(cur.color), string.upper(cur.name)) else "?"
		local tail = if rung >= #ladder then ('<font color="%s">LAST RUNG</font>'):format(hex(T.ACCENT))
			elseif nxt then quiet("NEXT") .. "  " .. string.upper(nxt.name) else ""
		line.Text = name .. "      " .. tail
		pips.Visible = true
		strip.Size = UDim2.fromOffset(0, 50)
		for i = 1, #ladder do
			local done, now = i < rung, i == rung
			local p = pip(i, if now then 12 else 8, if now then 8 else 5, if now then T.ACCENT elseif done then T.SOFT else T.TRACK, if done then 0.15 else 0)
			-- the leader's rung (when it isn't you): a white tick over it
			if lv == i and ln ~= me.DisplayName and not now then
				T.new("Frame", { Name = "Lead", BorderSizePixel = 0, BackgroundColor3 = T.TEXT, AnchorPoint = Vector2.new(0.5, 1),
					Position = UDim2.new(0.5, 0, 0, -2), Size = UDim2.fromOffset(2, 5) }, p)
			end
		end
	elseif k == "oitc" then
		local b = tonumber(me:GetAttribute("ModeBullets")) or 0
		local lives = tonumber(me:GetAttribute("ModeLives")) or 0
		line.Text = if me:GetAttribute("ModeOut") then ('<font color="%s">OUT OF LIVES</font>'):format(hex(T.DANGER))
			elseif ln then quiet("MOST LIVES") .. "  " .. ln else ""
		pips.Visible = true
		strip.Size = UDim2.fromOffset(0, 50)
		label(1, "BULLETS")
		gap(2, 4)
		for i = 1, ModeConfig.OITC.maxBullets do pip(2 + i, 6, 13, if i <= b then T.ACCENT else T.TRACK, 0) end
		gap(10, 14)
		label(11, "LIVES")
		gap(12, 4)
		for i = 1, ModeConfig.OITC.lives do pip(12 + i, 10, 10, if i <= lives then T.TEXT else T.TRACK, 0) end
	else
		pips.Visible = false
		strip.Size = UDim2.fromOffset(0, 30)
		local place = tonumber(me:GetAttribute("ModePlace")) or 1
		line.Text = if ln and lv then (quiet("LEADER") .. "  " .. ln .. "  " .. ('<font color="%s">%d</font>'):format(hex(T.ACCENT), lv)
			.. "      " .. quiet("YOU") .. "  " .. (if place == 1 then "1ST" elseif place == 2 then "2ND" elseif place == 3 then "3RD" else place .. "TH")) else ""
	end
end
RunService.Heartbeat:Connect(draw)

-- ------------------------------------------------------------------ the end screen's columns
local function endHead(): Instance?
	local fg = me.PlayerGui:FindFirstChild("JankfireFight")
	local e = fg and fg:FindFirstChild("End", true)
	return e and e:FindFirstChild("Head")
end
Remotes:WaitForChild("Round").OnClientEvent:Connect(function(r: any)
	if type(r) ~= "table" or not r.over then return end
	local head = endHead()
	if not head then return end
	local cols = if type(r.cols) == "table" then r.cols else { "KILLS", "DEATHS" }
	local c3, c4 = head:FindFirstChild("Cell3"), head:FindFirstChild("Cell4")
	if c3 and c3:IsA("TextLabel") then c3.Text = tostring(cols[1] or "KILLS") end
	if c4 and c4:IsA("TextLabel") then c4.Text = tostring(cols[2] or "DEATHS") end
	-- (a mode's final score under the result: the scoreboard's last line, which can land a frame after this message)
	if r.mode then
		task.delay(0.1, function()
			local mh = me:GetAttribute("MatchHud")
			local sc = head.Parent and head.Parent:FindFirstChild("Score")
			local parts = if type(mh) == "string" then string.split(mh, " · ") else {}
			if sc and sc:IsA("TextLabel") and parts[3] then sc.Text = parts[3] end
		end)
	end
end)

-- ------------------------------------------------------------------ one in the chamber: watching, no reset
local cam = workspace.CurrentCamera
local watch: Player? = nil
local watching = false
local function others(): { Player }
	local out = {}
	local mine = me:GetAttribute("ModeMatch")
	for _, p in Players:GetPlayers() do
		if p ~= me and p:GetAttribute("ModeMatch") == mine and not p:GetAttribute("ModeOut") then
			local hum = p.Character and p.Character:FindFirstChildOfClass("Humanoid")
			if hum and hum.Health > 0 then table.insert(out, p) end
		end
	end
	table.sort(out, function(a, b) return a.UserId < b.UserId end)
	return out
end
local function step(d: number)
	local list = others()
	if #list == 0 then watch = nil; return end
	local i = (watch and table.find(list, watch)) or 0
	watch = list[(i - 1 + d) % #list + 1]
end
local bar = T.new("TextLabel", {
	Name = "Watching", AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -110), Size = UDim2.fromOffset(0, 36),
	AutomaticSize = Enum.AutomaticSize.X, BackgroundColor3 = T.BG, BackgroundTransparency = 0.14, BorderSizePixel = 0, Visible = false,
	FontFace = T.FONT_BOLD, TextSize = 16, TextColor3 = T.TEXT, RichText = true, Text = "",
}, hud)
T.corner(bar); T.edge(bar)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 18), PaddingRight = UDim.new(0, 18) }, bar)
UserInputService.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp or not watching then return end
	if io.UserInputType == Enum.UserInputType.MouseButton1 or io.KeyCode == Enum.KeyCode.Space or io.KeyCode == Enum.KeyCode.Right then step(1)
	elseif io.KeyCode == Enum.KeyCode.Left then step(-1) end
end)
local camAt: CFrame? = nil
RunService:BindToRenderStep("JankModeWatch", Enum.RenderPriority.Camera.Value + 2, function(dt: number)
	local out = kind() == "oitc" and me:GetAttribute("ModeOut") == true and type(me:GetAttribute("MatchHud")) == "string"
	if not out or (Replay and Replay.isPlaying and Replay.isPlaying()) then
		if watching then
			watching = false
			bar.Visible = false
			camAt = nil
			if not (Replay and Replay.isPlaying and Replay.isPlaying()) then
				cam.CameraType = Enum.CameraType.Custom
				local hum = me.Character and me.Character:FindFirstChildOfClass("Humanoid")
				if hum then cam.CameraSubject = hum end
			end
		end
		return
	end
	if not watch or not table.find(others(), watch) then watch = nil; step(1) end
	local w = watch
	local root = w and w.Character and w.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
	watching = true
	bar.Visible = true
	bar.Text = if w then ('<font color="%s">OUT OF LIVES</font>    %s  %s    %s'):format(hex(T.DANGER), quiet("WATCHING"), w.DisplayName, quiet("click for the next"))
		else ('<font color="%s">OUT OF LIVES</font>'):format(hex(T.DANGER))
	if not root then return end
	-- over their shoulder: behind, up and to the right, looking where they look
	local r = root :: BasePart
	local look = Vector3.new(r.CFrame.LookVector.X, 0, r.CFrame.LookVector.Z)
	look = if look.Magnitude > 1e-3 then look.Unit else Vector3.zAxis
	local right = look:Cross(Vector3.yAxis)
	local want = CFrame.lookAt(r.Position - look * 9 + Vector3.new(0, 3.2, 0) + right * 2.2, r.Position + look * 24 + Vector3.new(0, 1.5, 0))
	camAt = if camAt then (camAt :: CFrame):Lerp(want, math.min(1, dt * 10)) else want
	cam.CameraType = Enum.CameraType.Scriptable
	cam.CFrame = camAt :: CFrame
end)
local resetOff = false
RunService.Heartbeat:Connect(function()
	local want = kind() == "oitc" and type(me:GetAttribute("MatchHud")) == "string"
	if want ~= resetOff then
		if pcall(function() StarterGui:SetCore("ResetButtonCallback", not want) end) then resetOff = want end
	end
end)

-- ------------------------------------------------------------------ randomizer: what you rolled
me:GetAttributeChangedSignal("ArmT"):Connect(function()
	if mode() ~= "rand" then return end
	local s = me:GetAttribute("Loadout")
	if type(s) ~= "string" then return end
	local names = {}
	for id in string.gmatch(s, "[^,]+") do table.insert(names, if W[id] then string.upper(W[id].name) else id) end
	Hud.note(table.concat(names, "  ·  "), 2.5)
end)

-- ------------------------------------------------------------------ duck rain: sky ducks
local items = ReplicatedStorage:FindFirstChild("JankfireItems")
local function duckModel(): Model
	local src = items and items:FindFirstChild("duck")
	local m: Model
	if src and src:IsA("Model") then
		m = src:Clone()
		m:ScaleTo(m:GetScale() * 1.6)
	else
		m = Instance.new("Model")
		local b = Instance.new("Part")
		b.Shape = Enum.PartType.Ball; b.Size = Vector3.new(1.4, 1.4, 1.4); b.Color = Color3.fromRGB(255, 214, 64); b.Material = Enum.Material.SmoothPlastic
		b.Parent = m
		m.PrimaryPart = b
	end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.CastShadow = false end
	end
	return m
end
local function disc(name: string, d: number, color: Color3, mat: Enum.Material, alpha: number): Part
	local p = Instance.new("Part")
	p.Name = name; p.Shape = Enum.PartType.Cylinder; p.Size = Vector3.new(0.08, d, d)
	p.Color = color; p.Material = mat; p.Transparency = alpha
	p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
	return p
end
local fxFolder = Instance.new("Folder")
fxFolder.Name = "JankfireSkyDucks"
fxFolder.Parent = workspace
local function skyDuck(m: any)
	local at, top = m.p :: Vector3, (tonumber(m.top) or (m.p :: Vector3).Y + 138) :: number
	local dur = math.max(0.1, (tonumber(m.ms) or 1500) / 1000)
	local v0, g = tonumber(m.v0) or 6 * S, tonumber(m.g) or 22 * S
	local flat = CFrame.new(at + Vector3.new(0, 0.06, 0)) * CFrame.Angles(0, 0, math.pi / 2)
	-- the shadow (black, darker as it nears) on a blinking red ring, both growing over the fall
	local ring = disc("Ring", 2, Color3.fromRGB(235, 77, 75), Enum.Material.Neon, 0.3)
	local shadow = disc("Shadow", 1.6, Color3.fromRGB(8, 8, 10), Enum.Material.SmoothPlastic, 0.6)
	ring.CFrame = flat; shadow.CFrame = flat + Vector3.new(0, 0.02, 0)
	ring.Parent = fxFolder; shadow.Parent = fxFolder
	local duck = duckModel()
	duck.Parent = fxFolder
	Sfx.play("whistle", at)
	-- LOOK UP: it lands on you (within 3.5 m flat and 4 m up or down)
	local root = me.Character and me.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
	if root then
		local d = root.Position - at
		if Vector3.new(d.X, 0, d.Z).Magnitude <= ModeConfig.DUCKRAIN.lookR and math.abs(d.Y) <= ModeConfig.DUCKRAIN.lookY + 3 then Hud.callout("LOOK UP", 1) end
	end
	local t0 = os.clock()
	local conn: RBXScriptConnection
	conn = RunService.RenderStepped:Connect(function()
		local t = os.clock() - t0
		local k = math.clamp(t / dur, 0, 1)
		local y = math.max(at.Y, top - (v0 * t + 0.5 * g * t * t))
		duck:PivotTo(CFrame.new(at.X, y, at.Z) * CFrame.Angles(0, t * 2, 0))
		local dd = 1.6 + 3.4 * k
		shadow.Size = Vector3.new(0.08, dd, dd); shadow.Transparency = 0.6 - 0.35 * k
		ring.Size = Vector3.new(0.08, dd + 0.9, dd + 0.9)
		ring.Transparency = if math.floor(t * (5 + 7 * k)) % 2 == 0 then 0.2 else 0.85
		if t >= dur + 0.05 then
			conn:Disconnect()
			ring:Destroy(); shadow:Destroy(); duck:Destroy()
		end
	end)
end
Remotes:WaitForChild("ItemFx").OnClientEvent:Connect(function(m: any)
	if type(m) == "table" and m.k == "skyduck" and typeof(m.p) == "Vector3" then skyDuck(m) end
end)
