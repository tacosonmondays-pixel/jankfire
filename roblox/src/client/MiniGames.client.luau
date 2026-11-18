--!strict
-- THE HUB'S MINI-GAMES, your side (shared/MiniGames.luau says what they are; server/MiniGames.server builds them).
-- two jobs:
--   * the world, for everyone: every game model in the map gets its look kept up by its module's world() (the arm
--     wrestlers' clasped hands, the pieces on the board, the cabinet's screen), from the model's attributes
--   * your game: when the server sits you down (your attributes MiniGame / MiniGameId / MiniSide) the game's screen
--     opens (ScreenGui JankMiniGame), the camera goes where that game wants it, the mouse is free (MenuCursor
--     "minigame") and you hold still (LoadoutOpen, the PlayerModule's controls off), till you leave
-- leaving: Backspace, a pad's B (PadNav calls back), the LEAVE button; Space too where the game has no use for it.
-- a game mid-play asks twice ("press again: you forfeit")
-- the modules (MiniArmUI, MiniBoardUI, MiniArcadeUI) each have:
--   world(model, api) -> (dt) -> ()?   the look for everyone; returns a per-frame step (or nil)
--   open(api, model, side) / close()  your screen
--   remote(data)                       the server's message to you
--   space(down, io) -> boolean        Space / pad A: true = used
--   back() -> boolean                 B / Backspace: true = used (a panel closed), else the core leaves
--   confirmLeave() -> string?          a line to show before leaving needs a second press
-- test hooks (Studio): player attribute MiniTest = "leave" | "space" | "back" ; MiniState (read) = JSON of the screen
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local CollectionService = game:GetService("CollectionService")
local HttpService = game:GetService("HttpService")
local ProximityPromptService = game:GetService("ProximityPromptService")

local me = Players.LocalPlayer
local J = script.Parent
local T = require(J:WaitForChild("Theme")) :: any
local MenuCursor = require(J:WaitForChild("MenuCursor")) :: any
local MenuGate = require(J:WaitForChild("MenuGate")) :: any
local Keys = require(J:WaitForChild("Keys")) :: any
local Pad = require(J:WaitForChild("Pad")) :: any
local Sfx = require(J:WaitForChild("Sfx")) :: any
local MG = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("MiniGames")) :: any
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("MiniGame") :: RemoteEvent

local MODS: { [string]: any } = {}
for kind, name in { arm = "MiniArmUI", board = "MiniBoardUI", arcade = "MiniArcadeUI", box = "MiniBoxUI" } do
	local ok, m = pcall(require, J:WaitForChild(name) :: ModuleScript)
	if ok then MODS[kind] = m else warn("[MiniGames] " .. name .. ": " .. tostring(m)) end
end

-- ------------------------------------------------------------------ the screen
local pg = me:WaitForChild("PlayerGui") :: PlayerGui
local gui = T.new("ScreenGui", { Name = "JankMiniGame", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 30,
	Enabled = false, ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
local root = T.scaled(gui)

local api: { [string]: any } = { T = T, MG = MG, Keys = Keys, Pad = Pad, Sfx = Sfx, gui = gui, me = me }
api.camera = nil :: (() -> CFrame?)?
api.fov = nil :: number?
function api.send(data: any)
	if api.kind then Remote:FireServer(api.kind, data) end
end
function api.isTouch(): boolean return Keys.isTouch() end
function api.padOn(): boolean return Pad.on() end
-- a button the way every screen makes them: a card, words in caps, an optional key cap on its left
function api.button(parent: Instance, name: string, text: string, pos: UDim2, size: UDim2, accent: boolean?): TextButton
	local b = T.new("TextButton", { Name = name, AutoButtonColor = false, BorderSizePixel = 0, Position = pos, Size = size,
		BackgroundColor3 = if accent then T.ACCENT else T.CARD, Text = text, FontFace = T.FONT_BOLD, TextSize = 15,
		TextColor3 = if accent then T.INK else T.TEXT, Selectable = true }, parent)
	T.corner(b)
	T.edge(b, nil, if accent then 1 else T.EDGE_A)
	b.MouseEnter:Connect(function() if not accent then b.BackgroundColor3 = T.CARD_HI end end)
	b.MouseLeave:Connect(function() if not accent then b.BackgroundColor3 = T.CARD end end)
	b.Activated:Connect(function() Sfx.play("click", nil, 0.5) end)
	return b
end
function api.shake(amount: number, len: number?)
	api.shakeAmt = math.max(api.shakeAmt or 0, amount)
	api.shakeLen = len or 0.25
	api.shakeT = os.clock()
end
function api.playAny(names: { string }, at: Vector3?, vol: number?): Sound?
	for _, n in names do
		local s = Sfx.play(n, at, vol)
		if s then return s end
	end
	return nil
end

-- the shell: the game's name and LEAVE (top right), the hint line under it
local top = T.plate(root, "Top", UDim2.new(1, -18, 0, 18), UDim2.fromOffset(270, 44))
top.AnchorPoint = Vector2.new(1, 0)
local title = T.text(top, "Title", "", 13, T.MUTED, T.FONT_TITLE)
title.Position = UDim2.fromOffset(14, 0); title.Size = UDim2.new(1, -120, 1, 0)
local leaveB = api.button(top, "Leave", "LEAVE", UDim2.new(1, -6, 0.5, 0), UDim2.fromOffset(112, 32))
leaveB.AnchorPoint = Vector2.new(1, 0.5)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 44) }, leaveB)
local cap = T.key(leaveB, "BKSP", UDim2.new(0, -40, 0.5, -11))
cap.Size = UDim2.fromOffset(36, 22)
local capL = cap:FindFirstChild("Letter") :: TextLabel?
if capL then capL.TextSize = 10 end
cap:SetAttribute("Pad", "ButtonB")
local confirmL = T.text(root, "Confirm", "", 14, T.ACCENT, T.FONT_BOLD, Enum.TextXAlignment.Right, true)
confirmL.AnchorPoint = Vector2.new(1, 0); confirmL.Position = UDim2.new(1, -20, 0, 68); confirmL.Size = UDim2.fromOffset(400, 20)
api.root = T.new("Frame", { Name = "Game", BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1) }, root)
top.ZIndex = 5

-- ------------------------------------------------------------------ in and out
local cur: { kind: string, model: Model, side: string, mod: any }? = nil
local savedOpen: any = nil
local controls: any = nil
pcall(function() controls = require(me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule") :: any):GetControls() end)
local confirmT = 0

local function modelOf(id: string): Model?
	for _, m in CollectionService:GetTagged("MiniGame") do
		if m:IsA("Model") and m:GetAttribute("Id") == id then return m end
	end
	return nil
end

local cam = { on = false, saved = nil :: CFrame?, savedType = nil :: Enum.CameraType?, out = nil :: number?, from = nil :: CFrame?, shown = {} :: { [Instance]: number }, savedFov = 70,
	blockT = 0, blocking = nil :: { [Instance]: boolean }? }

local function close()
	local c = cur
	if not c then return end
	cur = nil
	api.kind = nil
	pcall(c.mod.close)
	for _, ch in api.root:GetChildren() do ch:Destroy() end
	gui.Enabled = false
	confirmL.Text = ""
	MenuCursor.set("minigame", false)
	me:SetAttribute("LoadoutOpen", savedOpen == true)
	if controls then pcall(function() controls:Enable() end) end
	ProximityPromptService.Enabled = true
	api.camera = nil
	api.viewPoints = nil
	cam.blocking = nil
	if cam.on then
		cam.out = os.clock()
		cam.from = workspace.CurrentCamera.CFrame
	end
end

local function open(kind: string, model: Model, side: string)
	if cur then close() end
	local mod = MODS[kind]
	if not mod then Remote:FireServer("leave"); return end
	if not MenuGate.allowed("minigame") then Remote:FireServer("leave"); return end
	cur = { kind = kind, model = model, side = side, mod = mod }
	api.kind = kind
	api.model = model
	api.side = side
	title.Text = MG.TITLE[kind] or ""
	savedOpen = me:GetAttribute("LoadoutOpen")
	me:SetAttribute("LoadoutOpen", true)
	MenuCursor.set("minigame", true, function() return cur ~= nil end)
	if controls then pcall(function() controls:Disable() end) end
	ProximityPromptService.Enabled = false -- (no other seat's prompt while you play)
	gui.Enabled = true
	local ok, err = pcall(mod.open, api, model, side)
	if not ok then warn("[MiniGames] open " .. kind .. ": " .. tostring(err)) end
end

local function sync()
	local kind = me:GetAttribute("MiniGame")
	local id = me:GetAttribute("MiniGameId")
	local side = me:GetAttribute("MiniSide")
	if type(kind) ~= "string" or type(id) ~= "string" or type(side) ~= "string" then close(); return end
	if cur and cur.kind == kind and cur.model:GetAttribute("Id") == id and cur.side == side then return end
	local m = modelOf(id)
	if not m then
		task.delay(0.5, function() if me:GetAttribute("MiniGameId") == id and not cur then local m2 = modelOf(id); if m2 then open(kind, m2, side) end end end)
		return
	end
	open(kind, m, side)
end
me:GetAttributeChangedSignal("MiniGame"):Connect(sync)
me:GetAttributeChangedSignal("MiniGameId"):Connect(sync)
me:GetAttributeChangedSignal("MiniSide"):Connect(sync)
task.defer(sync)

function api.leave()
	if not cur then return end
	local why = nil
	local ok, r = pcall(cur.mod.confirmLeave)
	if ok then why = r end
	if why and os.clock() - confirmT > 3 then
		confirmT = os.clock()
		confirmL.Text = why
		task.delay(3, function() if os.clock() - confirmT >= 2.9 then confirmL.Text = "" end end)
		return
	end
	confirmL.Text = ""
	if cur.mod.beforeLeave then pcall(cur.mod.beforeLeave) end
	Remote:FireServer("leave")
end
function api.back()
	if not cur then return end
	local ok, used = pcall(cur.mod.back)
	if ok and used then return end
	api.leave()
end
leaveB.Activated:Connect(api.leave)

-- the controller: B is PadNav's back; the selection lives in this screen while a game says nav (api.nav)
Pad.MENUS = Pad.MENUS or {}
Pad.MENUS.minigame = { gui = "JankMiniGame", back = function() api.back() end, nav = false }
function api.nav(on: boolean, first: GuiObject?)
	local spec = Pad.MENUS and Pad.MENUS.minigame
	if spec then
		spec.nav = on
		spec.first = if first then function() return first end else nil
	end
	if not on then pcall(function() game:GetService("GuiService").SelectedObject = nil end) end
end

Keys.began(function(io: any, gp: boolean)
	if not cur or gp then return end
	local k = io.KeyCode
	if k == Enum.KeyCode.Backspace then api.back(); return end
	if k == Enum.KeyCode.Space or k == Enum.KeyCode.ButtonA then
		-- (a pad's A on a selected button presses the button: that's Roblox's, not ours)
		if k == Enum.KeyCode.ButtonA and game:GetService("GuiService").SelectedObject ~= nil then return end
		local ok, used = pcall(cur.mod.space, true, io)
		if ok and used then return end
		if k == Enum.KeyCode.Space then api.leave() end
	end
end)
Keys.ended(function(io: any)
	if not cur then return end
	local k = io.KeyCode
	if k == Enum.KeyCode.Space or k == Enum.KeyCode.ButtonA then pcall(cur.mod.space, false, io) end
end)

Remote.OnClientEvent:Connect(function(kind: string, data: any)
	if cur and cur.kind == kind then
		local ok, err = pcall(cur.mod.remote, data)
		if not ok then warn("[MiniGames] remote " .. kind .. ": " .. tostring(err)) end
	end
end)

-- ------------------------------------------------------------------ the camera (after the emote camera's Camera + 6)
-- which of your accessories stand between the camera and the game: a line from the camera to each of the game's
-- view points (api.viewPoints: the board's corners and middle, the clasped hands and the pin pads) tested against each
-- part's own box (in the part's frame: no CanQuery or collision shape needed). hair is never counted
local FADE = 0.6
local function segHitsBox(a: Vector3, b: Vector3, part: BasePart): boolean
	local p0 = part.CFrame:PointToObjectSpace(a)
	local p1 = part.CFrame:PointToObjectSpace(b)
	local h = part.Size / 2
	local t0, t1 = 0, 1
	local d = p1 - p0
	for _, ax in { "X", "Y", "Z" } do
		local o, v, e = (p0 :: any)[ax], (d :: any)[ax], (h :: any)[ax]
		if math.abs(v) < 1e-6 then
			if o < -e or o > e then return false end
		else
			local u0, u1 = (-e - o) / v, (e - o) / v
			if u0 > u1 then u0, u1 = u1, u0 end
			t0, t1 = math.max(t0, u0), math.min(t1, u1)
			if t0 > t1 then return false end
		end
	end
	return true
end
local function blockers(ch: Model, eye: Vector3): { [Instance]: boolean }
	local out = {}
	local pts = api.viewPoints and api.viewPoints() or {}
	if #pts == 0 then return out end
	for _, acc in ch:GetChildren() do
		if not acc:IsA("Accessory") then continue end
		if (acc :: Accessory).AccessoryType == Enum.AccessoryType.Hair then continue end
		for _, part in acc:GetDescendants() do
			if not part:IsA("BasePart") then continue end
			for _, pt in pts do
				if segHitsBox(eye, pt, part) then out[acc] = true; break end
			end
			if out[acc] then break end
		end
	end
	return out
end
RunService:BindToRenderStep("JankMiniCam", Enum.RenderPriority.Camera.Value + 7, function(dt: number)
	local c = workspace.CurrentCamera
	local ch = me.Character
	local want = api.camera and api.camera()
	if want then
		if not cam.on then
			cam.on = true
			cam.saved = c.CFrame
			cam.savedType = c.CameraType
			cam.savedFov = c.FieldOfView
			cam.out = nil
		end
		if c.CameraType ~= Enum.CameraType.Scriptable then c.CameraType = Enum.CameraType.Scriptable end
		local k = 1 - math.exp(-dt * 7)
		local cf = c.CFrame:Lerp(want, k)
		-- a shake (a slam, a hit taken): a quick jitter that dies away
		local amt = api.shakeAmt or 0
		if amt > 0 then
			local u = (os.clock() - (api.shakeT or 0)) / (api.shakeLen or 0.25)
			if u >= 1 then api.shakeAmt = 0
			else
				local a = amt * (1 - u) ^ 2
				cf *= CFrame.Angles(math.noise(os.clock() * 31, 1) * a, math.noise(os.clock() * 29, 2) * a, 0)
			end
		end
		c.CFrame = cf
		if api.fov then c.FieldOfView += (api.fov - c.FieldOfView) * k end
		-- your own body: first person hides it; while the camera is out it's shown, and put back after. your whole look
		-- stays: hair and accessories are never hidden wholesale (the owner, 19 Nov: "when I sit down at the table all
		-- my accessories come off and im bald"). the cameras look past your head (MiniGames.L.<game>.cam); only an
		-- accessory that really stands between the camera and what you're playing (a line from the camera to one of the
		-- game's api.viewPoints crosses its parts' boxes) fades, to FADE, and only while it does. hair never fades.
		-- your title over your head stays hidden on your screen while you sit
		if ch then
			local clear = api.kind == "arm" or api.kind == "board"
			if clear and os.clock() - (cam.blockT or 0) > 0.1 then
				cam.blockT = os.clock()
				cam.blocking = blockers(ch, c.CFrame.Position)
			end
			for _, d in ch:GetDescendants() do
				if d:IsA("BasePart") or d:IsA("Decal") then
					local o = d :: any
					if cam.shown[d] == nil then cam.shown[d] = o.LocalTransparencyModifier end
					local acc = d:FindFirstAncestorOfClass("Accessory")
					local want = if clear and acc and cam.blocking and cam.blocking[acc] then FADE else 0
					if o.LocalTransparencyModifier ~= want and d.Name ~= "HumanoidRootPart" then o.LocalTransparencyModifier = want end
				elseif clear and d:IsA("BillboardGui") and string.sub(d.Name, 1, 6) == "Title_" and d.Enabled then
					d.Enabled = false -- (OverheadTitles turns it back on in its Heartbeat: after this frame is drawn)
				end
			end
		end
		return
	end
	if not cam.on then return end
	-- back: a short glide to where your head looks, then the camera is yours again
	local u = math.clamp((os.clock() - (cam.out or os.clock())) / 0.3, 0, 1)
	u = u * u * (3 - 2 * u)
	local head = ch and ch:FindFirstChild("Head") :: BasePart?
	local back = cam.saved or c.CFrame
	if head then back = (cam.saved :: CFrame).Rotation + head.Position + Vector3.new(0, 0.2, 0) end
	if cam.from then c.CFrame = (cam.from :: CFrame):Lerp(back, u) end
	c.FieldOfView += (cam.savedFov - c.FieldOfView) * math.min(1, u * 1.5)
	if u >= 1 then
		c.FieldOfView = cam.savedFov
		c.CameraType = if cam.savedType == Enum.CameraType.Scriptable or cam.savedType == nil then Enum.CameraType.Custom else cam.savedType :: Enum.CameraType
		cam.on = false
		for o, v in cam.shown do if o.Parent then (o :: any).LocalTransparencyModifier = v end end
		table.clear(cam.shown)
	end
end)

-- ------------------------------------------------------------------ the world, for everyone
local steps: { [Model]: (number) -> () } = {}
local function adopt(m: Instance)
	if not m:IsA("Model") or steps[m] then return end
	local kind = m:GetAttribute("Kind")
	local mod = kind and MODS[kind :: string]
	if not mod or not mod.world then return end
	local ok, fn = pcall(mod.world, m, api)
	if ok and type(fn) == "function" then steps[m] = fn
	elseif not ok then warn("[MiniGames] world " .. tostring(kind) .. ": " .. tostring(fn)) end
end
for _, m in CollectionService:GetTagged("MiniGame") do task.spawn(adopt, m) end
CollectionService:GetInstanceAddedSignal("MiniGame"):Connect(function(m: Instance) task.spawn(adopt, m) end)
CollectionService:GetInstanceRemovedSignal("MiniGame"):Connect(function(m: Instance)
	if m:IsA("Model") and not m.Parent then steps[m] = nil end
end)
RunService.RenderStepped:Connect(function(dt: number)
	for m, fn in steps do
		if not m:IsDescendantOf(workspace) then continue end -- (put aside by ZoneCull: nothing to draw)
		local ok, err = pcall(fn, dt)
		if not ok then warn("[MiniGames] step: " .. tostring(err)); steps[m] = nil end
	end
	if cur and not cur.model:IsDescendantOf(game) then Remote:FireServer("leave"); close() end
end)

-- ------------------------------------------------------------------ test hooks
if RunService:IsStudio() then
	me:GetAttributeChangedSignal("MiniTest"):Connect(function()
		local v = me:GetAttribute("MiniTest")
		if v == nil then return end
		me:SetAttribute("MiniTest", nil)
		if v == "leave" then api.leave()
		elseif v == "back" then api.back()
		elseif v == "space" then if cur then pcall(cur.mod.space, true, { KeyCode = Enum.KeyCode.Space }); pcall(cur.mod.space, false, { KeyCode = Enum.KeyCode.Space }) end
		elseif type(v) == "string" and cur and cur.mod.test then
			local ok, r = pcall(cur.mod.test, v)
			me:SetAttribute("MiniState", if ok then r else ("error " .. tostring(r)))
			return
		end
		me:SetAttribute("MiniState", HttpService:JSONEncode({ open = cur ~= nil, kind = cur and cur.kind, side = cur and cur.side,
			cam = cam.on, cursor = MenuCursor.list(), loadoutOpen = me:GetAttribute("LoadoutOpen") }))
	end)
end
