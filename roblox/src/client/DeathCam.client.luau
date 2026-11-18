--!strict
-- the camera while you're dead (17 Nov 2026). the owner: dying in first person left the camera stuck where your head
-- was, and only V, third person, let you look round; then "when you die let it spectate the someone else team or in
-- 1v1v1 a random someone". from the moment you die until your new body comes, this script has the camera:
--   in a match (the player attributes Arena / Team that Matches sets): once the killcam is over (or straight away with
--   it off), it SPECTATES. a camera behind a living teammate's shoulder, looking where they look; with no teammate
--   alive (a 1v1, a free-for-all, the last of your side) any living player in your match, picked at random. click or
--   <- / -> (the shoulder buttons on a pad, the arrows on the bar on a phone) go to the next one, and the bar at the
--   bottom says who. someone you watch dies: on to the next. nobody alive to watch: the orbit below.
--   everywhere else (the hub, training) and as the fallback: it pulls back out of your eyes to a free orbit round your
--   body, turned at first so your killer is in the picture past it, yours to turn with the mouse, a finger dragged
--   anywhere on a phone or the right stick; the wheel goes nearer and further.
-- walls pull the camera in, never through. nothing new is sent for this: a dead player's client already has every
-- body in the match, and only that client moves its own camera to them, so a living player learns nothing.
-- it steps aside for anything else that has the camera on your death, and takes over again when that ends if you're
-- still dead:
--   the killcam and the play of the match (Replay.luau, from server/Recorder.luau; Settings > HUD: KILLCAM turns the
--   killcam off), a finisher (Finisher.luau: Finishing / LoadoutOpen), One in the Chamber's watching once you're out
--   of lives (ModeHud.client: ModeOut), menus (LoadoutOpen), an emote.
-- your new body (a respawn, the next round): the camera goes straight back to Roblox's own (first person, or the
-- shoulder camera if V had it), and Body.luau's Spawn turns it the way the spawn faces.
-- test hooks (Studio Play tests): the LocalPlayer attribute DeathCamTest = "x,y" turns the orbit as if the mouse moved
-- that many pixels, "next" / "prev" step the spectating; DeathCamState (read) = "on|off|aside|watch, dist, yaw, pitch,
-- killer, watched name". Studio only: Models in workspace.JankSpectateTest (attributes Team, Arena, Name) count as
-- players of your match, so one tester can watch stand-in bodies
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Replay = require(script.Parent:WaitForChild("Replay"))
local Settings = require(script.Parent:WaitForChild("Settings"))
local T = require(script.Parent:WaitForChild("Theme"))
local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")

local me = Players.LocalPlayer

local C = {
	dist = 11, near = 5, far = 20, -- studs from your body (the wheel moves it between near and far)
	up = 1.2, -- the point it turns about: this far over your body
	turnX = math.rad(0.5), turnY = math.rad(0.5) * 0.77, -- radians per mouse pixel (Roblox's own camera's, as ShoulderCam)
	touch = 0.0088, -- radians per finger pixel (the touch controls' rate)
	pad = math.rad(200), -- radians a second at a full right stick
	pitchLo = math.rad(-75), pitchHi = math.rad(60),
	radius = 0.5, -- the camera's own size against walls
	outTime = 0.45, -- the pull back out of your eyes (seconds)
	turnRate = 3, -- the turn to frame your killer, until you turn it yourself (per second)
	leash = 18, -- your body flung further than this: the camera stays round where you fell
	-- spectating: behind the one you watch, over their right shoulder, looking where they look
	watchBack = 9, watchUp = 2.6, watchRight = 1.6, watchAhead = 30, watchRate = 8,
}

type State = { on: boolean, owned: boolean, at: Vector3, focus: Vector3, yaw: number, pitch: number, dist: number,
	from: CFrame?, t0: number, killer: string?, kid: number?, touched: boolean, ch: Model?, watch: any?, camAt: CFrame? }
local S: State = { on = false, owned = false, at = Vector3.zero, focus = Vector3.zero, yaw = 0, pitch = 0, dist = C.dist,
	from = nil, t0 = 0, killer = nil, kid = nil, touched = false, ch = nil, watch = nil, camAt = nil }

-- the last kill that was yours to suffer (the Kill remote reaches everyone): who did it
local lastKill: { t: number, k: string?, kid: number? }? = nil
Remotes:WaitForChild("Kill").OnClientEvent:Connect(function(k: any)
	if type(k) ~= "table" or k.vid ~= me.UserId then return end
	lastKill = { t = os.clock(), k = if type(k.k) == "string" then k.k else nil, kid = if type(k.kid) == "number" then k.kid else nil }
	if S.on and not S.killer then S.killer, S.kid = lastKill.k, lastKill.kid end
end)

-- someone else has the camera on your death
local function aside(): boolean
	if Replay.isPlaying() then return true end
	if me:GetAttribute("Finishing") or me:GetAttribute("LoadoutOpen") == true then return true end
	if me:GetAttribute("ModeOut") == true and type(me:GetAttribute("MatchHud")) == "string" then return true end -- (ModeHud watches)
	if me:GetAttribute("Emote") ~= nil then return true end
	return false
end

local function bodyPoint(ch: Model?): Vector3?
	if not ch then return nil end
	for _, n in { "UpperTorso", "Torso", "HumanoidRootPart", "Head" } do
		local p = ch:FindFirstChild(n)
		if p and p:IsA("BasePart") then return p.Position end
	end
	return nil
end
local function alive(m: Model?): BasePart?
	if not m or not m.Parent then return nil end
	local hum = m:FindFirstChildOfClass("Humanoid")
	local root = m:FindFirstChild("HumanoidRootPart")
	if hum and hum.Health > 0 and root and root:IsA("BasePart") then return root end
	return nil
end

local function killerPoint(): Vector3?
	if S.kid then
		local p = Players:GetPlayerByUserId(S.kid)
		local pt = p and bodyPoint(p.Character)
		if pt then return pt end
	end
	if S.killer then
		local d = workspace:FindFirstChild("Dummies")
		local m = (d and d:FindFirstChild(S.killer)) or workspace:FindFirstChild(S.killer)
		if m and m:IsA("Model") then return bodyPoint(m) end
	end
	return nil
end

-- ------------------------------------------------------------------ spectating: who there is to watch
type Target = { key: any, name: string, model: Model, team: any }
local function teamOf(x: Instance): any return x:GetAttribute("ModeTeam") or x:GetAttribute("Team") end
local function myArena(): string?
	local a = me:GetAttribute("Arena")
	return if type(a) == "string" and a ~= "" then a else nil
end
-- the living players of your match, your own side first (if any of them is alive, only them), sorted so the next
-- one is always the same next one
local function watchable(): { Target }
	local arena = myArena()
	if not arena then return {} end
	local all: { Target } = {}
	-- (the attribute is the arena's name, and a copy of it shares that: a copy is Arena.GAP = 7,000 studs off, so
	-- only bodies within 3,000 studs of where you fell are in your match)
	local function near(r: BasePart?): boolean return r ~= nil and (r.Position - S.at).Magnitude < 3000 end
	for _, p in Players:GetPlayers() do
		if p ~= me and p:GetAttribute("Arena") == arena and p.Character and near(alive(p.Character)) then
			table.insert(all, { key = p.UserId, name = p.DisplayName, model = p.Character, team = teamOf(p) })
		end
	end
	if RunService:IsStudio() then
		local f = workspace:FindFirstChild("JankSpectateTest")
		if f then
			for _, m in f:GetChildren() do
				if m:IsA("Model") and m:GetAttribute("Arena") == arena and near(alive(m)) then
					table.insert(all, { key = m.Name, name = tostring(m:GetAttribute("Name") or m.Name), model = m, team = m:GetAttribute("Team") })
				end
			end
		end
	end
	local mine = teamOf(me)
	local side: { Target } = {}
	if mine ~= nil then for _, t in all do if t.team == mine then table.insert(side, t) end end end
	local list = if #side > 0 then side else all
	table.sort(list, function(a, b) return tostring(a.key) < tostring(b.key) end)
	return list
end
local function findIn(list: { Target }, key: any): number?
	for i, t in list do if t.key == key then return i end end
	return nil
end
-- (d = 0: keep the one you watch if they're still there, else a random one)
local function pick(d: number)
	local list = watchable()
	if #list == 0 then S.watch = nil; return end
	local i = if S.watch then findIn(list, S.watch.key) else nil
	if i and d == 0 then S.watch = list[i]; return end
	if not i then S.watch = list[math.random(#list)]; return end
	S.watch = list[(i - 1 + d) % #list + 1]
end

-- ------------------------------------------------------------------ the bar: SPECTATING  NAME
local gui = T.new("ScreenGui", { Name = "JankSpectate", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 6, Enabled = false },
	me:WaitForChild("PlayerGui"))
local hud = T.scaled(gui)
local bar = T.new("Frame", { Name = "Bar", AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -118), Size = UDim2.fromOffset(0, 40),
	AutomaticSize = Enum.AutomaticSize.X, BackgroundColor3 = T.BG, BackgroundTransparency = 0.14, BorderSizePixel = 0 }, hud)
T.corner(bar); T.edge(bar)
T.new("UIPadding", { PaddingLeft = UDim.new(0, 16), PaddingRight = UDim.new(0, 16) }, bar)
T.new("UIListLayout", { FillDirection = Enum.FillDirection.Horizontal, VerticalAlignment = Enum.VerticalAlignment.Center,
	Padding = UDim.new(0, 12), SortOrder = Enum.SortOrder.LayoutOrder }, bar)
local function label(name: string, order: number, size: number, color: Color3, font: Font): TextLabel
	local l = T.text(bar, name, "", size, color, font)
	l.LayoutOrder = order
	l.AutomaticSize = Enum.AutomaticSize.X
	l.Size = UDim2.fromOffset(0, 40)
	return l
end
local function arrowBtn(name: string, order: number, glyph: string, d: number): TextButton
	local b = T.new("TextButton", { Name = name, LayoutOrder = order, AutoButtonColor = false, BorderSizePixel = 0, Text = glyph,
		BackgroundColor3 = T.CARD, BackgroundTransparency = 0.05, Size = UDim2.fromOffset(52, 34), FontFace = T.FONT_HEAVY,
		TextSize = 16, TextColor3 = T.TEXT, Visible = false }, bar)
	T.corner(b, 4)
	b.Activated:Connect(function() pick(d) end)
	return b
end
local prevB = arrowBtn("Prev", 0, "<", -1)
local tag = label("Tag", 1, 13, T.MUTED, T.FONT_BOLD)
tag.Text = "SPECTATING"
local who = label("Name", 2, 17, T.TEXT, T.FONT_HEAVY)
local hint = label("Hint", 3, 12, T.DIM, T.FONT_BOLD)
local nextB = arrowBtn("Next", 4, ">", 1)
local function drawBar(on: boolean)
	if gui.Enabled ~= on then gui.Enabled = on end
	if not on or not S.watch then return end
	local name = string.upper((S.watch :: any).name)
	if who.Text ~= name then who.Text = name end
	local touch = UIS.TouchEnabled and not UIS.MouseEnabled
	local n = #watchable()
	prevB.Visible = touch and n > 1
	nextB.Visible = touch and n > 1
	hint.Visible = not touch and n > 1
	if hint.Visible then hint.Text = "\u{2190} \u{2192}  OR CLICK" end
end

-- walls: a ball the camera's size out to where it wants to be. bodies, see-through parts and anything you walk through
-- don't stop it (ShoulderCam's rules)
local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Exclude
params.RespectCanCollide = true
params.IgnoreWater = true
local function refilter()
	local list: { Instance } = { workspace.CurrentCamera }
	for _, p in Players:GetPlayers() do if p.Character then table.insert(list, p.Character) end end
	for _, n in { "Dummies", "JankSpectateTest" } do
		local d = workspace:FindFirstChild(n)
		if d then table.insert(list, d) end
	end
	if S.ch then table.insert(list, S.ch) end
	params.FilterDescendantsInstances = list
end
local function clear(from: Vector3, dir: Vector3, want: number): number
	for _ = 1, 8 do
		local hit = workspace:Spherecast(from, C.radius, dir * want, params)
		if not hit then return want end
		local p = hit.Instance
		local m = p:FindFirstAncestorOfClass("Model")
		if p:IsA("BasePart") and (p.Transparency >= 0.25 or p:IsA("TrussPart") or (m ~= nil and m:FindFirstChildOfClass("Humanoid") ~= nil)) then
			params:AddToFilter(p)
		else
			return math.max(0.5, hit.Distance)
		end
	end
	return want
end

local function lookOf(cf: CFrame): (number, number)
	local l = cf.LookVector
	return math.atan2(-l.X, -l.Z), math.asin(math.clamp(l.Y, -1, 1))
end

-- a body shows (first person's camera had hidden yours; the one you watch, the same)
local function show(ch: Model?)
	if not ch then return end
	for _, d in ch:GetDescendants() do
		if (d:IsA("BasePart") or d:IsA("Decal")) and d.LocalTransparencyModifier ~= 0 then d.LocalTransparencyModifier = 0 end
	end
end

-- ------------------------------------------------------------------ input while it's on
local touches: { [InputObject]: Vector2 } = {}
local turn = Vector2.zero -- this frame's turn from touches and the test hook, radians (yaw, pitch)
local stick = Vector2.zero
UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if not S.on then return end
	if io.UserInputType == Enum.UserInputType.Touch and not gp then touches[io] = Vector2.new(io.Position.X, io.Position.Y) end
	if gp or not S.watch or not S.owned then return end
	local k = io.KeyCode
	if io.UserInputType == Enum.UserInputType.MouseButton1 or k == Enum.KeyCode.Right or k == Enum.KeyCode.ButtonR1 or k == Enum.KeyCode.DPadRight then pick(1)
	elseif k == Enum.KeyCode.Left or k == Enum.KeyCode.ButtonL1 or k == Enum.KeyCode.DPadLeft then pick(-1) end
end)
UIS.InputChanged:Connect(function(io: InputObject, gp: boolean)
	if not S.on then return end
	local t = io.UserInputType
	if t == Enum.UserInputType.Touch then
		local last = touches[io]
		if not last then return end
		local pos = Vector2.new(io.Position.X, io.Position.Y)
		local k = C.touch * ((tonumber(Settings.get("touch.sens")) or 1))
		turn += Vector2.new(-(pos.X - last.X) * k, -(pos.Y - last.Y) * k)
		touches[io] = pos
	elseif t == Enum.UserInputType.MouseWheel and not gp then
		S.dist = math.clamp(S.dist - io.Position.Z * 1.5, C.near, C.far)
	elseif io.KeyCode == Enum.KeyCode.Thumbstick2 then
		stick = Vector2.new(io.Position.X, io.Position.Y)
	end
end)
UIS.InputEnded:Connect(function(io: InputObject)
	touches[io] = nil
	if io.KeyCode == Enum.KeyCode.Thumbstick2 then stick = Vector2.zero end
end)

-- ------------------------------------------------------------------ on and off
local mouseWas: Enum.MouseBehavior? = nil
local function letGo()
	if not S.owned then return end
	S.owned = false
	if mouseWas then UIS.MouseBehavior = Enum.MouseBehavior.Default; mouseWas = nil end
	drawBar(false)
end

-- you, alive: your own current body with life in it (18 Nov 2026, the owner, alive in the next round with SPECTATING
-- DUNE still up and first person stuck, then the bar still up back in the hub: a fresh body can die for a moment while
-- the server puts it in place, its Died started this on a body that then lived, and only a respawn turned it off. now
-- it never starts on a living body, turns off the moment yours is alive, and the bar shows only while it watches)
local function living(ch: Model?): Humanoid?
	local hum = ch and ch:FindFirstChildOfClass("Humanoid")
	if hum and hum.Health > 0 and hum:GetState() ~= Enum.HumanoidStateType.Dead then return hum end
	return nil
end

local function start(ch: Model)
	if S.on and S.ch == ch then return end
	if living(ch) then return end
	local cam = workspace.CurrentCamera
	drawBar(false)
	S.on, S.owned, S.ch = true, false, ch
	S.at = bodyPoint(ch) or cam.CFrame.Position
	S.focus = S.at
	S.yaw, S.pitch = lookOf(cam.CFrame)
	S.pitch = math.clamp(S.pitch, C.pitchLo, C.pitchHi)
	S.dist, S.touched, S.from, S.t0, S.watch, S.camAt = C.dist, false, nil, os.clock(), nil, nil
	local lk = lastKill
	if lk and os.clock() - lk.t < 2 then S.killer, S.kid = lk.k, lk.kid else S.killer, S.kid = nil, nil end
	table.clear(touches)
	turn, stick = Vector2.zero, Vector2.zero
	refilter()
end

local function stop()
	if not S.on then return end
	local owned = S.owned
	letGo()
	S.on, S.ch, S.watch, S.camAt = false, nil, nil, nil
	table.clear(touches)
	drawBar(false)
	-- the camera back on you: your body is its subject, and if this had it (or nothing else does and no shoulder camera
	-- is coming), Roblox's own camera has it again
	local cam = workspace.CurrentCamera
	local hum = me.Character and me.Character:FindFirstChildOfClass("Humanoid")
	if hum and cam.CameraSubject ~= hum then cam.CameraSubject = hum end
	if owned or (cam.CameraType == Enum.CameraType.Scriptable and not aside() and me:GetAttribute("ThirdPerson") ~= true) then
		cam.CameraType = Enum.CameraType.Custom
	end
end

local function watch(ch: Model)
	local hum = ch:WaitForChild("Humanoid", 10) :: Humanoid?
	if not hum then return end
	hum.Died:Connect(function() if me.Character == ch then start(ch) end end)
	if hum.Health <= 0 and me.Character == ch then start(ch) end
end
me.CharacterAdded:Connect(function(ch)
	stop()
	task.spawn(watch, ch)
end)
if me.Character then task.spawn(watch, me.Character) end

-- ------------------------------------------------------------------ every frame
local filterT = 0
RunService:BindToRenderStep("JankDeathCam", Enum.RenderPriority.Last.Value + 65, function(dt: number)
	if S.on and living(me.Character) then stop() end -- (alive again, however you came back)
	if not S.on then
		if gui.Enabled then drawBar(false) end
		return
	end
	local cam = workspace.CurrentCamera
	if aside() then
		if S.owned then letGo() end
		drawBar(false)
		turn = Vector2.zero
		return
	end
	if not S.owned then
		-- (taking it, or taking it back after a killcam / finisher: from wherever the camera is now)
		S.owned = true
		S.from, S.t0, S.camAt = cam.CFrame, os.clock(), nil
		refilter()
	end
	if os.clock() - filterT > 1 then filterT = os.clock(); refilter() end -- (bodies come and go)
	if cam.CameraType ~= Enum.CameraType.Scriptable then cam.CameraType = Enum.CameraType.Scriptable end

	-- the turn: the mouse (locked to the middle, as first person had it), fingers, the stick, the test hook
	local dyaw, dpitch = turn.X, turn.Y
	turn = Vector2.zero
	if UIS.MouseEnabled then
		-- (a menu needs the cursor: the settings panel, MenuCursor's menus such as the match's loadout picker)
		if me:GetAttribute("SettingsOpen") == true or me:GetAttribute("MenuCursor") == true then
			if UIS.MouseBehavior ~= Enum.MouseBehavior.Default then UIS.MouseBehavior = Enum.MouseBehavior.Default end
		else
			if UIS.MouseBehavior ~= Enum.MouseBehavior.LockCenter then
				mouseWas = mouseWas or UIS.MouseBehavior
				UIS.MouseBehavior = Enum.MouseBehavior.LockCenter
			end
			local d = UIS:GetMouseDelta()
			dyaw -= d.X * C.turnX
			dpitch -= d.Y * C.turnY * ((me:GetAttribute("LookY") :: number?) or 1)
		end
	end
	if stick.Magnitude > 0.15 then
		dyaw -= stick.X * C.pad * dt
		dpitch += stick.Y * C.pad * 0.6 * dt
	end

	-- in a match: watch someone (the one you watch gone or dead: the next)
	if myArena() then
		if not S.watch or not alive((S.watch :: any).model) then pick(0) end
	elseif S.watch then
		S.watch = nil
	end
	local w = S.watch
	local wroot = w and alive(w.model)
	if wroot then
		local r = wroot :: BasePart
		local look = Vector3.new(r.CFrame.LookVector.X, 0, r.CFrame.LookVector.Z)
		look = if look.Magnitude > 1e-3 then look.Unit else Vector3.zAxis
		local right = look:Cross(Vector3.yAxis)
		local focus = r.Position + Vector3.new(0, 1.6, 0)
		local off = -look * C.watchBack + Vector3.new(0, C.watchUp, 0) + right * C.watchRight
		local free = clear(focus, off.Unit, off.Magnitude)
		local pos = focus + off.Unit * free
		local want = CFrame.lookAt(pos, r.Position + look * C.watchAhead + Vector3.new(0, 1.5, 0))
		-- (smooth: easing from the camera's last place, so a switch glides across instead of cutting)
		local k = 1 - math.exp(-dt * C.watchRate)
		local from = S.camAt or S.from or cam.CFrame
		S.camAt = from:Lerp(want, k)
		S.from = nil
		cam.CFrame = S.camAt :: CFrame
		cam.Focus = CFrame.new(focus)
		show(w.model)
		drawBar(true)
		return
	end
	drawBar(false)

	-- the orbit: your body, yours to turn
	if math.abs(dyaw) + math.abs(dpitch) > 1e-4 then S.touched = true end
	if S.camAt then
		-- (back from watching someone: from where that left the camera)
		S.from, S.t0 = S.camAt, os.clock()
		S.yaw, S.pitch = lookOf(S.camAt :: CFrame)
		S.pitch = math.clamp(S.pitch, C.pitchLo, C.pitchHi)
		S.camAt = nil
	end
	S.yaw += dyaw
	S.pitch = math.clamp(S.pitch + dpitch, C.pitchLo, C.pitchHi)

	-- where it turns about: your body, smoothly, on a leash from where you fell
	local b = bodyPoint(S.ch)
	if b and (b - S.at).Magnitude <= C.leash then
		S.focus = S.focus:Lerp(b, 1 - math.exp(-dt * 6))
	end
	local focus = S.focus + Vector3.new(0, C.up, 0)

	-- until you turn it yourself: round to frame your killer past your body, looking a little down
	if not S.touched then
		local kp = killerPoint()
		local k = 1 - math.exp(-dt * C.turnRate)
		if kp then
			local d = Vector3.new(kp.X - focus.X, 0, kp.Z - focus.Z)
			if d.Magnitude > 1 then
				local want = math.atan2(-d.X, -d.Z)
				local diff = (want - S.yaw + math.pi) % (2 * math.pi) - math.pi
				S.yaw += diff * k
			end
		end
		S.pitch += (math.rad(-18) - S.pitch) * k
	end

	local rot = CFrame.fromOrientation(S.pitch, S.yaw, 0)
	local back = rot.LookVector * -1
	local free = clear(focus, back, S.dist)
	local want = CFrame.new(focus + back * free) * rot
	local u = math.clamp((os.clock() - S.t0) / C.outTime, 0, 1)
	if S.from and u < 1 then
		local e = u * u * (3 - 2 * u)
		cam.CFrame = (S.from :: CFrame):Lerp(want, e)
	else
		S.from = nil
		cam.CFrame = want
	end
	cam.Focus = CFrame.new(focus)
	show(S.ch)
end)

-- ------------------------------------------------------------------ test hooks
me:GetAttributeChangedSignal("DeathCamTest"):Connect(function()
	local v = me:GetAttribute("DeathCamTest")
	if type(v) ~= "string" or v == "" then return end
	me:SetAttribute("DeathCamTest", nil)
	if v == "next" then pick(1); return end
	if v == "prev" then pick(-1); return end
	local x, y = string.match(v, "^(-?[%d%.]+),(-?[%d%.]+)$")
	if x then turn += Vector2.new(-(tonumber(x) or 0) * C.turnX, -(tonumber(y) or 0) * C.turnY) end
end)
RunService.Heartbeat:Connect(function()
	if not RunService:IsStudio() then return end
	local st = if not S.on then "off" elseif not S.owned then "aside" elseif S.watch then "watch" else "on"
	local v = ("%s|%.1f|%.2f|%.2f|%s|%s"):format(st, S.dist, S.yaw, S.pitch, tostring(S.killer), if S.watch then (S.watch :: any).name else "-")
	if me:GetAttribute("DeathCamState") ~= v then me:SetAttribute("DeathCamState", v) end
end)
