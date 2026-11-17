--!strict
-- FLAIR on the client (Shared.Flair; doc FLAIR.md): the kill effects the server sends (FlairKill -> KillFx.luau), the
-- emote wheel and playing an emote.
--   * the wheel: hold T (Rivals' key), point at a slot, let go to play it (or click one). on a phone, the EMOTE
--     button opens it and a tap plays. 8 slots, set on the equip screen (FlairUI.luau: the loadout's KILL EFFECT ·
--     EMOTES button). on a phone the EMOTE button (top right) opens it. while it's up the mouse is free and everything else holds still (LoadoutOpen).
--   * an emote: the server says yes (owned, on your wheel, alive, not too soon) and puts your weapon away; this plays
--     the clip on your own character (it replicates to everyone) and swings the camera out behind you (third person:
--     the mouse turns it round you). moving, jumping, a weapon key, a click, T again, dying or the server ending it
--     stops it. in a match, while you emote, enemies you couldn't see from your own eyes are hidden from you (Rivals
--     does the same: the camera can't be used to look round corners).
-- test hook (Play tests driven from Studio): the local player's attribute FlairTest = "wheel" | "close" | "pick:<slot>"
--   | "emote:<id>" | "stop" | "ui" | "ui:emote" | "ui:kill" | "uiclose" | "preview:<id>" (the equip screen's preview)
local Players = game:GetService("Players")
local UIS = game:GetService("UserInputService")
local RunService = game:GetService("RunService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Flair = require(Shared:WaitForChild("Flair")) :: any
local KillFx = require(script.Parent:WaitForChild("KillFx")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")

local FlairUI: any = nil
local function ui(): any
	if FlairUI == nil then
		local m = script.Parent:FindFirstChild("FlairUI")
		local ok, r = false, nil
		if m then ok, r = pcall(require, m) end
		FlairUI = if ok then r else false
	end
	return if FlairUI then FlairUI else nil
end

-- ------------------------------------------------------------------ kill effects
task.spawn(function()
	local ev = Remotes:WaitForChild("FlairKill", 60) :: RemoteEvent?
	if not ev then return end
	ev.OnClientEvent:Connect(function(msg: any)
		if type(msg) ~= "table" or typeof(msg.m) ~= "Instance" or not msg.m:IsA("Model") or type(msg.fx) ~= "string" then return end
		-- (the settings page's GRAPHICS row OTHERS' KILL EFFECTS: off = someone else's kills just hide the body; yours always play)
		local quiet = msg.k ~= me.UserId and KillFx.setting("gfx.othersKill", true) == false
		KillFx.play(msg.m, msg.fx, { from = if typeof(msg.from) == "Vector3" then msg.from else nil, quiet = quiet })
	end)
end)

local function remote(): RemoteFunction?
	return Remotes:FindFirstChild("Flair") :: RemoteFunction?
end
local function ask(...: any): any
	local r = remote()
	if not r then return { ok = false, why = "no server" } end
	local ok, res = pcall(r.InvokeServer, r, ...)
	return if ok and type(res) == "table" then res else { ok = false, why = "no answer" }
end

-- ------------------------------------------------------------------ playing an emote
local E = {
	id = nil :: string?, track = nil :: AnimationTrack?, t0 = 0, len = 0, loop = false,
	cam = nil :: { yaw: number, pitch: number, dist: number, saved: CFrame, savedType: Enum.CameraType, t0: number, out: number?, from: CFrame? }?,
	hidden = {} :: { [Instance]: number }, hideT = 0, starting = false, rootAt = Vector3.zero,
	-- (your own body: first person hides it, and that hiding stays when the camera turns Scriptable. while the camera
	-- is out it's shown; each part's own value goes back when the camera is home, so first person stays clean)
	shown = {} :: { [Instance]: number },
}
local tracks: { [string]: AnimationTrack } = {}
local tracksFor: Model? = nil

local function myChar(): (Model?, Humanoid?, BasePart?)
	local ch = me.Character
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not ch or not hum or not root or hum.Health <= 0 then return nil, nil, nil end
	return ch, hum, root
end

local function trackFor(hum: Humanoid, id: string): AnimationTrack?
	local e = Flair.info("emote", id)
	if not e then return nil end
	if tracksFor ~= hum.Parent then table.clear(tracks); tracksFor = hum.Parent :: Model end
	local tr = tracks[id]
	if tr then return tr end
	local an = hum:FindFirstChildOfClass("Animator")
	if not an then return nil end
	local a = Instance.new("Animation")
	a.AnimationId = e.anim
	local ok, t = pcall(an.LoadAnimation, an, a)
	if not ok or not t then return nil end
	t.Priority = Enum.AnimationPriority.Action4
	tracks[id] = t
	return t
end

-- enemies you can't see are hidden from you while you emote in a match
local mapParams = RaycastParams.new()
mapParams.FilterType = Enum.RaycastFilterType.Include
local function unhideAll()
	for o, v in E.hidden do
		if o.Parent then (o :: any).LocalTransparencyModifier = v end
	end
	table.clear(E.hidden)
end
local function hideStep(root: BasePart)
	if me:GetAttribute("Zone") ~= "match" then if next(E.hidden) then unhideAll() end; return end
	local map = workspace:FindFirstChild("Map")
	if not map then return end
	mapParams.FilterDescendantsInstances = { map }
	local eye = root.Position + Vector3.new(0, 1.5, 0)
	local myTeam = me:GetAttribute("Team")
	for _, p in Players:GetPlayers() do
		local ch = p.Character
		if p == me or not ch then continue end
		local friend = myTeam ~= nil and p:GetAttribute("Team") == myTeam
		local seen = friend
		if not seen then
			local r = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
			if not r then continue end
			for _, up in { 1.6, 0.4, -1.4 } do
				local to = r.Position + Vector3.new(0, up, 0)
				if not workspace:Raycast(eye, to - eye, mapParams) then seen = true; break end
			end
		end
		for _, d in ch:GetDescendants() do
			if d:IsA("BasePart") or d:IsA("Decal") then
				local o = d :: any
				if seen then
					local v = E.hidden[d]
					if v ~= nil then o.LocalTransparencyModifier = v; E.hidden[d] = nil end
				elseif E.hidden[d] == nil then
					E.hidden[d] = o.LocalTransparencyModifier
					o.LocalTransparencyModifier = 1
				end
			end
		end
	end
end

local function stopEmote(tellServer: boolean)
	local id = E.id
	if not id then return end
	E.id = nil
	if E.track then E.track:Stop(0.25) end
	E.track = nil
	unhideAll()
	local c = E.cam
	if c then
		local cam = workspace.CurrentCamera
		c.out, c.from = os.clock(), cam.CFrame
	end
	if tellServer then task.spawn(ask, "stop") end
end

local function startEmote(id: string)
	if E.starting or id == "" then return end
	local ch, hum, root = myChar()
	if not ch or not hum or not root then return end
	if E.id == id and E.track and E.track.IsPlaying then return end
	E.starting = true
	local res = ask("emote", id)
	E.starting = false
	if not res.ok then
		if res.why == "too soon" then pcall(function() (require(script.Parent:WaitForChild("Hud")) :: any).note("WAIT", 0.8) end) end
		return
	end
	if E.id then
		if E.track then E.track:Stop(0.15) end
		E.track = nil
	end
	local e = Flair.info("emote", id)
	local tr = trackFor(hum, id)
	if not e or not tr then task.spawn(ask, "stop"); return end
	tr.Looped = e.loop
	tr:Play(0.2, 1, 1)
	E.id, E.track, E.t0, E.len, E.loop = id, tr, os.clock(), e.len, e.loop
	E.rootAt = root.Position
	-- the camera swings out behind you (or keeps going if it's already out)
	local cam = workspace.CurrentCamera
	if not E.cam or E.cam.out then
		local look = cam.CFrame.LookVector
		local saved = if E.cam and E.cam.out then E.cam.saved else cam.CFrame
		local savedType = if E.cam and E.cam.out then E.cam.savedType else cam.CameraType
		E.cam = { yaw = math.atan2(-look.X, -look.Z), pitch = math.clamp(math.asin(look.Y), -0.6, 0.5) - 0.18, dist = 0,
			saved = saved, savedType = savedType, t0 = os.clock(), out = nil, from = nil }
	end
end

-- the camera while emoting: round you at 9 studs, the mouse turns it; walls pull it in. after: back where it was
local camParams = RaycastParams.new()
camParams.FilterType = Enum.RaycastFilterType.Exclude
camParams.RespectCanCollide = true
camParams.IgnoreWater = true
RunService:BindToRenderStep("JankFlairEmoteCam", Enum.RenderPriority.Camera.Value + 6, function(dt: number)
	local c = E.cam
	if not c then return end
	local cam = workspace.CurrentCamera
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if c.out then
		-- back: a short glide to the look you had, then the camera is yours again
		local u = math.clamp((os.clock() - c.out) / 0.25, 0, 1)
		u = u * u * (3 - 2 * u)
		local h = ch and ch:FindFirstChild("Head") :: BasePart?
		local back = c.saved
		if h and c.savedType ~= Enum.CameraType.Scriptable then back = c.saved.Rotation + h.Position + Vector3.new(0, 0.2, 0) end
		if c.from then cam.CFrame = c.from:Lerp(back, u) end
		if u >= 1 then
			cam.CFrame = back
			cam.CameraType = if c.savedType == Enum.CameraType.Scriptable then Enum.CameraType.Custom else c.savedType
			E.cam = nil
			for o, v in E.shown do if o.Parent then (o :: any).LocalTransparencyModifier = v end end
			table.clear(E.shown)
		end
		return
	end
	if not root then return end
	if cam.CameraType ~= Enum.CameraType.Scriptable then cam.CameraType = Enum.CameraType.Scriptable end
	if me:GetAttribute("LoadoutOpen") ~= true then
		UIS.MouseBehavior = Enum.MouseBehavior.LockCenter
		local d = UIS:GetMouseDelta()
		c.yaw -= d.X * math.rad(0.4)
		c.pitch = math.clamp(c.pitch - d.Y * math.rad(0.3), -1.1, 0.9)
	end
	local want = 9 * (1 - (1 - math.clamp((os.clock() - c.t0) / 0.35, 0, 1)) ^ 3)
	local focus = root.Position + Vector3.new(0, 1.4, 0)
	local rot = CFrame.fromOrientation(c.pitch, c.yaw, 0)
	local dir = rot.LookVector * -1
	camParams.FilterDescendantsInstances = { ch :: Instance, workspace:FindFirstChild("JankKillFx") :: Instance }
	local hit = if want > 0.5 then workspace:Spherecast(focus, 0.4, dir * want, camParams) else nil
	local dist = if hit then math.max(0.5, hit.Distance - 0.1) else want
	cam.CFrame = CFrame.new(focus + dir * dist) * rot
	if dist > 2.5 and ch then
		for _, d in ch:GetDescendants() do
			if d:IsA("BasePart") or d:IsA("Decal") then
				local o = d :: any
				if E.shown[d] == nil then E.shown[d] = o.LocalTransparencyModifier end
				if o.LocalTransparencyModifier ~= 0 and d.Name ~= "HumanoidRootPart" then o.LocalTransparencyModifier = 0 end
			end
		end
	end
end)

-- what ends it
RunService.Heartbeat:Connect(function(dt: number)
	if not E.id then return end
	local ch, hum, root = myChar()
	if not ch or not hum or not root then stopEmote(false); return end
	local el = os.clock() - E.t0
	local moved = hum.MoveDirection.Magnitude > 0.1 or hum.Jump
		or (Vector3.new(root.Position.X, 0, root.Position.Z) - Vector3.new(E.rootAt.X, 0, E.rootAt.Z)).Magnitude > 1.5
	if (el > 0.25 and moved) or (not E.loop and el > E.len - 0.05) or me:GetAttribute("Emote") == nil and el > 1 then
		stopEmote(me:GetAttribute("Emote") ~= nil)
		return
	end
	if os.clock() - E.hideT > 0.15 then
		E.hideT = os.clock()
		hideStep(root)
	end
end)
me:GetAttributeChangedSignal("Emote"):Connect(function()
	if me:GetAttribute("Emote") == nil and E.id and os.clock() - E.t0 > 0.3 then stopEmote(false) end
end)
me.CharacterAdded:Connect(function() stopEmote(false); table.clear(tracks); table.clear(E.shown) end)

-- ------------------------------------------------------------------ the wheel
local W = { open = false, hover = 0, held = false, touch = false, savedOpen = false, t0 = 0, slots = {} :: { any } }
local gui = T.new("ScreenGui", { Name = "JankEmoteWheel", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 40,
	ZIndexBehavior = Enum.ZIndexBehavior.Sibling, Enabled = false }, pg)
local catcher = T.new("TextButton", { Text = "", AutoButtonColor = false, BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), Modal = true }, gui)
local wroot = T.scaled(gui) -- (the HUD's own scale: 1 at 1080 p)
local RING, CELL = 196, 112
local disc = T.new("Frame", { Name = "Disc", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
	Size = UDim2.fromOffset(RING * 2 + CELL + 40, RING * 2 + CELL + 40), BackgroundColor3 = T.BG, BackgroundTransparency = 0.3, BorderSizePixel = 0 }, wroot)
T.corner(disc, 999)
T.edge(disc)
local hub = T.new("Frame", { Name = "Centre", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5),
	Size = UDim2.fromOffset(176, 176), BackgroundColor3 = T.CARD, BackgroundTransparency = 0.15, BorderSizePixel = 0, ZIndex = 2 }, disc)
T.corner(hub, 999)
local hubName = T.text(hub, "Name", "", 22, T.TEXT, T.FONT_TITLE, Enum.TextXAlignment.Center)
hubName.AnchorPoint = Vector2.new(0.5, 0.5); hubName.Position = UDim2.fromScale(0.5, 0.46); hubName.Size = UDim2.fromOffset(160, 30)
hubName.ZIndex = 3; hubName.TextScaled = true
T.new("UITextSizeConstraint", { MaxTextSize = 22 }, hubName)
local hubBar = T.new("Frame", { AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0.62), Size = UDim2.fromOffset(40, 3),
	BackgroundColor3 = T.ACCENT, BorderSizePixel = 0, ZIndex = 3 }, hub)

for i = 1, Flair.SLOTS do
	local a = math.rad(-90 + (i - 1) * 360 / Flair.SLOTS)
	local cell = T.new("TextButton", { Name = "Slot" .. i, Text = "", AutoButtonColor = false, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.new(0.5, math.cos(a) * RING, 0.5, math.sin(a) * RING), Size = UDim2.fromOffset(CELL, CELL),
		BackgroundColor3 = T.CARD, BackgroundTransparency = 0.1, BorderSizePixel = 0, ZIndex = 3 }, disc)
	T.corner(cell, 10)
	local st = T.edge(cell)
	local pic = T.new("Frame", { Name = "Pic", BackgroundTransparency = 1, Position = UDim2.fromOffset(6, 6), Size = UDim2.new(1, -12, 1, -12), ZIndex = 4 }, cell)
	local empty = T.new("Frame", { Name = "Empty", AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(26, 26),
		BackgroundTransparency = 1, ZIndex = 4 }, cell)
	T.corner(empty, 999)
	T.edge(empty, T.DIM, 0.4, 2)
	W.slots[i] = { cell = cell, st = st, pic = pic, empty = empty, id = "" }
	cell.MouseEnter:Connect(function() W.hover = i end)
	cell.MouseButton1Click:Connect(function()
		local id = W.slots[i].id
		if id ~= "" then
			task.spawn(startEmote, id)
			W.close()
		end
	end)
end

local function fill()
	local s = Flair.slotsOf(me:GetAttribute("Emotes"))
	for i, sl in W.slots do
		if sl.id ~= s[i] then
			sl.id = s[i]
			for _, c in sl.pic:GetChildren() do c:Destroy() end
			if sl.id ~= "" then Flair.picture("emote", sl.id, sl.pic) end
			sl.empty.Visible = sl.id == ""
		end
	end
end
local function show()
	for i, sl in W.slots do
		local on = i == W.hover and sl.id ~= ""
		sl.st.Color = if on then T.ACCENT else T.EDGE
		sl.st.Transparency = if on then 0 else T.EDGE_A
		sl.st.Thickness = if on then 2 else 1
		sl.cell.BackgroundColor3 = if on then T.CARD_HI else T.CARD
	end
	local id = if W.hover > 0 then W.slots[W.hover].id else ""
	local e = Flair.info("emote", id)
	hubName.Text = if e then string.upper(e.name) else ""
	hubBar.Visible = e ~= nil
	if e then hubBar.BackgroundColor3 = Flair.RARITY_COLOR[e.rarity] or T.ACCENT end
end

function W.openWheel(touch: boolean)
	if W.open then return end
	local ch = myChar()
	if not ch then return end
	if me:GetAttribute("LoadoutOpen") == true then return end -- (another menu is up)
	W.open, W.touch, W.hover, W.t0 = true, touch, 0, os.clock()
	W.savedOpen = me:GetAttribute("LoadoutOpen") == true
	me:SetAttribute("LoadoutOpen", true) -- (a menu is up: hands, weapons and the other screens hold still; the mouse is free)
	fill()
	show()
	gui.Enabled = true
	disc.Size = UDim2.fromOffset((RING * 2 + CELL + 40) * 0.92, (RING * 2 + CELL + 40) * 0.92)
	T.tween(disc, 0.12, { Size = UDim2.fromOffset(RING * 2 + CELL + 40, RING * 2 + CELL + 40) })
	UIS.MouseBehavior = Enum.MouseBehavior.Default
end
function W.close()
	if not W.open then return end
	W.open = false
	gui.Enabled = false
	me:SetAttribute("LoadoutOpen", W.savedOpen)
end
-- the slot the mouse points at: by its angle from the middle (a dead zone in the middle)
RunService.RenderStepped:Connect(function()
	if not W.open then return end
	if not myChar() then W.close(); return end
	local m = UIS:GetMouseLocation()
	local c = disc.AbsolutePosition + disc.AbsoluteSize / 2
	local d = m - c
	local sc = disc.AbsoluteSize.X / (RING * 2 + CELL + 40)
	if d.Magnitude > 70 * sc and not W.touch then
		local a = math.deg(math.atan2(d.Y, d.X)) + 90
		W.hover = math.floor(((a + 360 / Flair.SLOTS / 2) % 360) / (360 / Flair.SLOTS)) + 1
	elseif not W.touch then
		W.hover = 0
	end
	show()
end)
catcher.MouseButton1Click:Connect(function()
	-- a click on the ring's empty space: the pointed slot plays (mouse); a tap outside closes (phone)
	if not W.touch and W.hover > 0 and W.slots[W.hover].id ~= "" then task.spawn(startEmote, W.slots[W.hover].id) end
	W.close()
end)
me:GetAttributeChangedSignal("Emotes"):Connect(function() if W.open then fill(); show() end end)

-- the emote key: the settings page's rebinding (StarterPlayerScripts.Jankfire.Binds, "emote"; the settings session's) when
-- it's in, else T and D-pad right
local BindsMod: any = nil
local function emoteKey(io: InputObject): boolean
	if BindsMod == nil then
		local m = script.Parent:FindFirstChild("Binds")
		local ok, res = false, nil
		if m and m:IsA("ModuleScript") then ok, res = pcall(require, m) end
		BindsMod = if ok and type(res) == "table" and type(res.is) == "function" then res else false
	end
	if BindsMod then
		local ok, yes = pcall(BindsMod.is, "emote", io)
		if ok then return yes == true end
	end
	return io.KeyCode == Enum.KeyCode.T or io.KeyCode == Enum.KeyCode.DPadRight
end
local WEAPON_KEYS = { [Enum.KeyCode.One] = true, [Enum.KeyCode.Two] = true, [Enum.KeyCode.Three] = true, [Enum.KeyCode.Four] = true,
	[Enum.KeyCode.G] = true, [Enum.KeyCode.R] = true, [Enum.KeyCode.E] = true, [Enum.KeyCode.Space] = true, [Enum.KeyCode.C] = true }
UIS.InputBegan:Connect(function(io, gp)
	if UIS:GetFocusedTextBox() then return end
	if emoteKey(io) then
		if W.open then W.close(); return end
		if gp then return end
		W.held = true
		W.openWheel(false)
		return
	end
	if io.KeyCode == Enum.KeyCode.Escape and W.open then W.close(); return end
	if gp then return end
	if E.id and (WEAPON_KEYS[io.KeyCode] or io.UserInputType == Enum.UserInputType.MouseButton1
		or io.UserInputType == Enum.UserInputType.MouseButton2) then
		stopEmote(true)
	end
end)
UIS.InputEnded:Connect(function(io)
	if not emoteKey(io) then return end
	if not W.held then return end
	W.held = false
	if not W.open then return end
	-- let go: the pointed slot plays. a quick tap with nothing pointed leaves the wheel up for a click
	local id = if W.hover > 0 then W.slots[W.hover].id else ""
	if id ~= "" then
		task.spawn(startEmote, id)
		W.close()
	elseif os.clock() - W.t0 > 0.35 then
		W.close()
	end
end)

-- ------------------------------------------------------------------ the phone's button
do
	local bgui = T.new("ScreenGui", { Name = "JankEmoteButton", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6,
		ZIndexBehavior = Enum.ZIndexBehavior.Sibling }, pg)
	local face = T.new("TextButton", {
		Name = "Emote", AutoButtonColor = false, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A, BorderSizePixel = 0,
		-- (top right, under the settings button: the left-hand stack is PLAY, PARTY, PROFILE, SHOP, LOADOUT)
		Position = UDim2.new(1, -160, 0, 72), Size = UDim2.fromOffset(136, 36), FontFace = T.FONT_BOLD, TextSize = 13, Text = "EMOTE",
		TextColor3 = T.TEXT, Visible = false,
	}, T.scaled(bgui))
	T.corner(face); T.edge(face)
	face.MouseButton1Click:Connect(function() if W.open then W.close() else W.openWheel(true) end end)
	RunService.Heartbeat:Connect(function()
		local show = UIS.TouchEnabled and not UIS.KeyboardEnabled and (me:GetAttribute("LoadoutOpen") ~= true or W.open) and myChar() ~= nil
		if face.Visible ~= show then face.Visible = show end
	end)
end

-- ------------------------------------------------------------------ test hook
me:GetAttributeChangedSignal("FlairTest"):Connect(function()
	local v = me:GetAttribute("FlairTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("FlairTest", nil)
	local cmd, rest = string.match(v, "^(%a+):?(.*)$")
	if cmd == "wheel" then W.openWheel(rest == "touch")
	elseif cmd == "close" then W.close()
	elseif cmd == "hover" then W.hover = tonumber(rest) or 0; show()
	elseif cmd == "pick" then
		local i = tonumber(rest) or 1
		W.close()
		local id = Flair.slotsOf(me:GetAttribute("Emotes"))[i]
		if id and id ~= "" then task.spawn(startEmote, id) end
	elseif cmd == "emote" then task.spawn(startEmote, rest)
	elseif cmd == "stop" then stopEmote(true)
	elseif cmd == "ui" then local U = ui(); if U then U.open(if rest ~= "" then rest else nil) end
	elseif cmd == "uiclose" then local U = ui(); if U then U.close() end
	elseif cmd == "preview" then local U = ui(); if U then U.preview(rest) end
	end
end)
