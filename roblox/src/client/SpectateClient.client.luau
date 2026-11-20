--!strict
-- the SPECTATE BOARD on this client (20 Nov 2026, the owner: "can there be a board where you can specate current
-- games?"; the server's side and the rules: server/Spectate.luau; docs/MATCHMAKING.md "Watching matches").
--   * THE BOARDS: every part tagged SpectateBoard (the hub session's, one a hub) gets this server's live matches drawn on
--     its front face: mode, map, score, round, time, the players. its prompt (SpectateOpen) opens the WATCH panel
--   * THE PANEL: the same matches with a WATCH button each (ranked: listed, not watchable). also the PLAY screen's
--     WATCH tab (PlayUI.openWatch)
--   * WATCHING (the server's Watching attribute on you): your body stays put, the camera goes to the match and follows a
--     player. PREV / NEXT cycle (Q / E, arrows, a pad's D-Left / D-Right), FREE CAM (F, a pad's Y: WASD, Space and
--     Ctrl, look with the right mouse button or the right stick), LEAVE (Backspace, a pad's B, the button). the arena's
--     look and life: this client sets its own Zone and Arena attributes while watching (HubLife, ZoneCull and the
--     arena scripts read them; the server's values are put back after). the other screens hide (the Play panel's way)
-- no flavour text: short labels only
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local CollectionService = game:GetService("CollectionService")

local T = require(script.Parent:WaitForChild("Theme"))
local MenuCursor = require(script.Parent:WaitForChild("MenuCursor"))
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Spectate") :: RemoteFunction

local me = Players.LocalPlayer
local pg = me:WaitForChild("PlayerGui")
local camera = workspace.CurrentCamera
local new, text = T.new, T.text
local TeamColors = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("TeamColors")) :: any
local TEAM_COLORS = { TeamColors.color(1), TeamColors.color(2), TeamColors.color(3), TeamColors.color(4) }

local function ask(op: string, a: any?): any
	local ok, res = pcall(function() return Remote:InvokeServer(op, a) end)
	if not ok or type(res) ~= "table" then return { ok = false } end
	return res
end
local function clock(ends: number?): string
	if type(ends) ~= "number" then return "" end
	local s = math.max(0, math.floor(ends - workspace:GetServerTimeNow()))
	return ("%d:%02d"):format(s // 60, s % 60)
end
local function scoreOf(m: any): string
	local out = {}
	for _, w in m.wins or {} do table.insert(out, tostring(w)) end
	return table.concat(out, " – ")
end
local function namesOf(m: any): string
	local sides = {}
	for _, names in m.teams or {} do table.insert(sides, if #names > 0 then table.concat(names, ", ") else "-") end
	return table.concat(sides, "  vs  ")
end
local function stateOf(m: any): string
	if m.phase == "live" then return ("ROUND %d · %s"):format(m.round or 1, clock(m.ends)) end
	if m.phase == "over" then return "ENDING" end
	return ("ROUND %d · GETTING READY"):format(m.round or 1)
end

local matches: { any } = {}
local lastList = 0
local function refreshList()
	local r = ask("list")
	if r.ok and type(r.matches) == "table" then matches = r.matches end
	lastList = os.clock()
end

-- ------------------------------------------------------------------ the boards (SurfaceGuis on the hub's markers)
type Board = { part: BasePart, gui: SurfaceGui, list: Frame }
local boards: { [BasePart]: Board } = {}
local function drawBoard(b: Board)
	for _, c in b.list:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
	if #matches == 0 then
		local f = new("Frame", { Name = "Empty", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 80) }, b.list)
		local e = text(f, "Text", "NO MATCHES RIGHT NOW", 34, T.MUTED, T.FONT_HEAVY, Enum.TextXAlignment.Center)
		e.Size = UDim2.fromScale(1, 1)
		return
	end
	for i, m in matches do
		if i > 6 then break end
		local row = new("Frame", { Name = "Row" .. i, BorderSizePixel = 0, BackgroundColor3 = T.CARD, BackgroundTransparency = 0.1,
			Size = UDim2.new(1, 0, 0, 104), LayoutOrder = i }, b.list)
		T.corner(row, 8)
		local top = text(row, "Mode", string.upper(tostring(m.mode)) .. "  ·  " .. string.upper(tostring(m.title or m.arena)) .. (if m.ranked then "  ·  RANKED" else ""), 34, T.TEXT, T.FONT_HEAVY)
		top.Position = UDim2.fromOffset(22, 10); top.Size = UDim2.new(1, -260, 0, 42)
		top.TextTruncate = Enum.TextTruncate.AtEnd
		local sc = text(row, "Score", scoreOf(m), 40, T.ACCENT, T.FONT_TITLE, Enum.TextXAlignment.Right)
		sc.AnchorPoint = Vector2.new(1, 0); sc.Position = UDim2.new(1, -22, 0, 8); sc.Size = UDim2.fromOffset(220, 46)
		local sub = text(row, "Sub", stateOf(m) .. "  ·  " .. namesOf(m), 26, T.MUTED, T.FONT_BOLD)
		sub.Position = UDim2.fromOffset(22, 58); sub.Size = UDim2.new(1, -44, 0, 34)
		sub.TextTruncate = Enum.TextTruncate.AtEnd
	end
end
local function addBoard(inst: Instance)
	if not inst:IsA("BasePart") or boards[inst] then return end
	local part = inst :: BasePart
	local gui = new("SurfaceGui", { Name = "JankSpectateBoard", Face = Enum.NormalId.Front, Adornee = part, ResetOnSpawn = false,
		SizingMode = Enum.SurfaceGuiSizingMode.PixelsPerStud, PixelsPerStud = 60, LightInfluence = 0, Brightness = 1.5,
		AlwaysOnTop = false, ZOffset = 1 }, pg)
	local bg = new("Frame", { Name = "Bg", BorderSizePixel = 0, BackgroundColor3 = T.BG, BackgroundTransparency = 0.05, Size = UDim2.fromScale(1, 1) }, gui)
	new("UIPadding", { PaddingLeft = UDim.new(0, 36), PaddingRight = UDim.new(0, 36), PaddingTop = UDim.new(0, 28), PaddingBottom = UDim.new(0, 28) }, bg)
	local head = text(bg, "Head", "LIVE MATCHES", 54, T.TEXT, T.FONT_TITLE)
	head.Size = UDim2.new(1, -300, 0, 64)
	local hint = text(bg, "Hint", "E  WATCH", 32, T.ACCENT, T.FONT_HEAVY, Enum.TextXAlignment.Right)
	hint.AnchorPoint = Vector2.new(1, 0); hint.Position = UDim2.new(1, 0, 0, 12); hint.Size = UDim2.fromOffset(280, 40)
	local list = new("Frame", { Name = "List", BackgroundTransparency = 1, Position = UDim2.fromOffset(0, 84), Size = UDim2.new(1, 0, 1, -84) }, bg)
	new("UIListLayout", { Padding = UDim.new(0, 12), SortOrder = Enum.SortOrder.LayoutOrder }, list)
	local b: Board = { part = part, gui = gui, list = list }
	boards[part] = b
	drawBoard(b)
	part.AncestryChanged:Connect(function()
		if not part:IsDescendantOf(workspace) then gui:Destroy(); boards[part] = nil end
	end)
end
for _, p in CollectionService:GetTagged("SpectateBoard") do addBoard(p) end
CollectionService:GetInstanceAddedSignal("SpectateBoard"):Connect(addBoard)

-- ------------------------------------------------------------------ the WATCH panel
local panelGui = new("ScreenGui", { Name = "JankSpectate", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 30, Enabled = false }, pg)
local panelS = T.scaled(panelGui)
local panel = new("Frame", { Name = "Panel", BorderSizePixel = 0, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A,
	AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.5), Size = UDim2.fromOffset(560, 420) }, panelS)
T.corner(panel, 8)
local pHead = text(panel, "Title", "WATCH", 22, T.TEXT, T.FONT_TITLE)
pHead.Position = UDim2.fromOffset(18, 14); pHead.Size = UDim2.fromOffset(300, 26)
local pSub = text(panel, "Sub", "matches on this server", 12, T.MUTED, T.FONT)
pSub.Position = UDim2.fromOffset(18, 40); pSub.Size = UDim2.fromOffset(300, 16)
local closeB = new("TextButton", { Name = "Close", AutoButtonColor = false, BorderSizePixel = 0, BackgroundColor3 = T.CARD, Text = "CLOSE",
	FontFace = T.FONT_HEAVY, TextSize = 12, TextColor3 = T.TEXT, AnchorPoint = Vector2.new(1, 0), Position = UDim2.new(1, -14, 0, 14), Size = UDim2.fromOffset(84, 30) }, panel)
T.corner(closeB, 5)
local rows = new("ScrollingFrame", { Name = "Rows", BackgroundTransparency = 1, BorderSizePixel = 0, ScrollBarThickness = 4, CanvasSize = UDim2.new(),
	AutomaticCanvasSize = Enum.AutomaticSize.Y, Position = UDim2.fromOffset(14, 66), Size = UDim2.new(1, -28, 1, -80) }, panel)
new("UIListLayout", { Padding = UDim.new(0, 8), SortOrder = Enum.SortOrder.LayoutOrder }, rows)
local panelOpen = false
local note: TextLabel? = nil
local function panelNote(s: string)
	if note then note:Destroy() end
	local n = text(panel, "Note", s, 12, T.DANGER, T.FONT_BOLD, Enum.TextXAlignment.Right)
	n.AnchorPoint = Vector2.new(1, 0); n.Position = UDim2.new(1, -108, 0, 20); n.Size = UDim2.fromOffset(330, 18)
	note = n
	task.delay(3, function() if note == n then n:Destroy(); note = nil end end)
end
local watchNow: (id: any) -> ()
local function drawPanel()
	for _, c in rows:GetChildren() do if c:IsA("Frame") then c:Destroy() end end
	if #matches == 0 then
		local f = new("Frame", { Name = "Empty", BackgroundTransparency = 1, Size = UDim2.new(1, 0, 0, 60) }, rows)
		local e = text(f, "Text", "no matches right now", 14, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
		e.Size = UDim2.fromScale(1, 1)
		return
	end
	for i, m in matches do
		local row = new("Frame", { Name = "Row" .. i, BorderSizePixel = 0, BackgroundColor3 = T.CARD, BackgroundTransparency = 0.1,
			Size = UDim2.new(1, -6, 0, 62), LayoutOrder = i }, rows)
		T.corner(row, 5)
		local top = text(row, "Mode", string.upper(tostring(m.mode)) .. "  ·  " .. string.upper(tostring(m.title or m.arena)) .. "   " .. scoreOf(m), 14, T.TEXT, T.FONT_HEAVY)
		top.Position = UDim2.fromOffset(12, 8); top.Size = UDim2.new(1, -130, 0, 18); top.TextTruncate = Enum.TextTruncate.AtEnd
		local sub = text(row, "Sub", stateOf(m) .. "  ·  " .. namesOf(m), 11, T.MUTED, T.FONT)
		sub.Position = UDim2.fromOffset(12, 32); sub.Size = UDim2.new(1, -130, 0, 16); sub.TextTruncate = Enum.TextTruncate.AtEnd
		if m.watch then
			local wb = new("TextButton", { Name = "Watch", AutoButtonColor = false, BorderSizePixel = 0, BackgroundColor3 = T.ACCENT, Text = "WATCH",
				FontFace = T.FONT_HEAVY, TextSize = 12, TextColor3 = T.INK, AnchorPoint = Vector2.new(1, 0.5), Position = UDim2.new(1, -10, 0.5, 0), Size = UDim2.fromOffset(100, 34) }, row)
			T.corner(wb, 5)
			wb.MouseButton1Click:Connect(function() watchNow(m.id) end)
		else
			local rk = text(row, "Ranked", if m.ranked then "RANKED" else "", 11, T.DIM, T.FONT_HEAVY, Enum.TextXAlignment.Right)
			rk.AnchorPoint = Vector2.new(1, 0.5); rk.Position = UDim2.new(1, -14, 0.5, 0); rk.Size = UDim2.fromOffset(100, 16)
		end
	end
end
local function closePanel()
	if not panelOpen then return end
	panelOpen = false
	panelGui.Enabled = false
	MenuCursor.set("spectatepanel", false)
end
local function openPanel()
	if me:GetAttribute("Watching") ~= nil then return end
	panelOpen = true
	panelGui.Enabled = true
	MenuCursor.set("spectatepanel", true, function() return panelOpen end)
	refreshList()
	drawPanel()
end
closeB.MouseButton1Click:Connect(closePanel)

-- ------------------------------------------------------------------ watching
local overlay = new("ScreenGui", { Name = "JankSpectateView", ResetOnSpawn = false, IgnoreGuiInset = true, DisplayOrder = 31, Enabled = false }, pg)
local ovS = T.scaled(overlay)
local bar = new("Frame", { Name = "Bar", BorderSizePixel = 0, BackgroundColor3 = T.BG, BackgroundTransparency = T.BG_A,
	AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.new(0.5, 0, 0, 14), Size = UDim2.fromOffset(460, 58) }, ovS)
T.corner(bar, 6)
local who = text(bar, "Who", "", 18, T.TEXT, T.FONT_HEAVY, Enum.TextXAlignment.Center)
who.Position = UDim2.fromOffset(0, 6); who.Size = UDim2.new(1, 0, 0, 24)
local what = text(bar, "What", "", 12, T.MUTED, T.FONT_BOLD, Enum.TextXAlignment.Center)
what.Position = UDim2.fromOffset(0, 32); what.Size = UDim2.new(1, 0, 0, 16)
local tag = text(bar, "Tag", "WATCHING", 10, T.ACCENT, T.FONT_HEAVY)
tag.Position = UDim2.fromOffset(12, 6); tag.Size = UDim2.fromOffset(90, 14)
local btnRow = new("Frame", { Name = "Buttons", BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 1), Position = UDim2.new(0.5, 0, 1, -18), Size = UDim2.fromOffset(470, 40) }, ovS)
local function btn(name: string, label: string, x: number, w: number, hi: boolean?): TextButton
	local b = new("TextButton", { Name = name, AutoButtonColor = false, BorderSizePixel = 0, BackgroundColor3 = if hi then T.ACCENT else T.BG,
		BackgroundTransparency = if hi then 0 else T.BG_A, Text = label, FontFace = T.FONT_HEAVY, TextSize = 13,
		TextColor3 = if hi then T.INK else T.TEXT, Position = UDim2.fromOffset(x, 0), Size = UDim2.fromOffset(w, 40) }, btnRow)
	T.corner(b, 5)
	return b
end
local prevB = btn("Prev", "<  PREV", 0, 104)
local nextB = btn("Next", "NEXT  >", 112, 104)
local freeB = btn("Free", "FREE CAM", 224, 116)
local leaveB = btn("Leave", "LEAVE", 348, 122, true)

type View = { id: any, users: { number }, arena: string, title: string, mode: string, centre: Vector3,
	idx: number, free: boolean, yaw: number, pitch: number, pos: Vector3, saved: { [string]: any }, hidden: { [ScreenGui]: boolean }, infoT: number }
local view: View? = nil

local function targets(v: View): { Player }
	local out = {}
	for _, uid in v.users do
		local p = Players:GetPlayerByUserId(uid)
		local ch = p and p.Character
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		if p and ch and hum and hum.Health > 0 and ch:FindFirstChild("HumanoidRootPart") then table.insert(out, p) end
	end
	return out
end
local function current(v: View): Player?
	local list = targets(v)
	if #list == 0 then return nil end
	v.idx = (v.idx - 1) % #list + 1
	return list[v.idx]
end
local function cycle(step: number)
	local v = view
	if not v then return end
	if v.free then v.free = false end
	v.idx += step
end
local function toggleFree()
	local v = view
	if not v then return end
	v.free = not v.free
	if v.free then
		local cf = camera.CFrame
		v.pos = cf.Position
		local lx, ly = cf:ToOrientation()
		v.pitch, v.yaw = lx, ly
	end
end
local function leave() task.spawn(ask, "leave") end
prevB.MouseButton1Click:Connect(function() cycle(-1) end)
nextB.MouseButton1Click:Connect(function() cycle(1) end)
freeB.MouseButton1Click:Connect(toggleFree)
leaveB.MouseButton1Click:Connect(leave)

local function enter(w: any)
	if view then return end
	closePanel()
	local saved = { Zone = me:GetAttribute("Zone"), Arena = me:GetAttribute("Arena"), LoadoutOpen = me:GetAttribute("LoadoutOpen") }
	local hidden: { [ScreenGui]: boolean } = {}
	for _, g in pg:GetChildren() do
		if g:IsA("ScreenGui") and g ~= overlay and g.Enabled then hidden[g] = true; g.Enabled = false end
	end
	view = { id = w.id, users = w.users or {}, arena = w.arena, title = w.title or w.arena, mode = w.mode or "", centre = w.centre or camera.CFrame.Position,
		idx = 1, free = false, yaw = 0, pitch = -0.3, pos = (w.centre or camera.CFrame.Position) + Vector3.new(0, 30, 40), saved = saved, hidden = hidden, infoT = os.clock() }
	-- (the arena's look, its life and the culling follow these two on this client: the server's are put back after)
	me:SetAttribute("Zone", "match")
	me:SetAttribute("Arena", w.arena)
	me:SetAttribute("LoadoutOpen", true) -- (hold still: hands, weapons, movement, the game's keys)
	MenuCursor.set("watch", true, function() return view ~= nil end)
	camera.CameraType = Enum.CameraType.Scriptable
	overlay.Enabled = true
end
local function exit()
	local v = view
	if not v then return end
	view = nil
	overlay.Enabled = false
	me:SetAttribute("Zone", v.saved.Zone)
	me:SetAttribute("Arena", v.saved.Arena)
	MenuCursor.set("watch", false)
	me:SetAttribute("LoadoutOpen", v.saved.LoadoutOpen)
	for g in v.hidden do if g.Parent then g.Enabled = true end end
	camera.CameraType = Enum.CameraType.Custom
	local hum = me.Character and me.Character:FindFirstChildOfClass("Humanoid")
	if hum then camera.CameraSubject = hum end
end

watchNow = function(id: any)
	local r = ask("watch", id)
	if not r.ok then panelNote(tostring(r.why or "can't watch that")); return end
	if r.watch then enter(r.watch) end
end

-- the server's word: Watching set = in (a watch started elsewhere: the PLAY tab), cleared = out (LEAVE, the match over)
me:GetAttributeChangedSignal("Watching"):Connect(function()
	if me:GetAttribute("Watching") == nil then
		exit()
	elseif not view then
		local r = ask("info")
		if r.ok and r.watch then enter(r.watch) end
	end
end)

-- the camera: behind the player being watched (smoothed), or the free camera
local mouseLook = false
local moveKeys: { [Enum.KeyCode]: Vector3 } = {
	[Enum.KeyCode.W] = Vector3.new(0, 0, -1), [Enum.KeyCode.S] = Vector3.new(0, 0, 1), [Enum.KeyCode.A] = Vector3.new(-1, 0, 0),
	[Enum.KeyCode.D] = Vector3.new(1, 0, 0), [Enum.KeyCode.Space] = Vector3.new(0, 1, 0), [Enum.KeyCode.LeftControl] = Vector3.new(0, -1, 0),
}
local padMove, padLook = Vector2.zero, Vector2.zero
RunService:BindToRenderStep("JankSpectateCam", Enum.RenderPriority.Camera.Value + 10, function(dt: number)
	local v = view
	if not v then return end
	if camera.CameraType ~= Enum.CameraType.Scriptable then camera.CameraType = Enum.CameraType.Scriptable end
	-- (the players now: someone left or came in. the server's list every 3 s)
	if os.clock() - v.infoT > 3 then
		v.infoT = os.clock()
		task.spawn(function()
			local r = ask("info")
			if r.ok and r.watch and view == v then v.users = r.watch.users or v.users end
		end)
	end
	if v.free then
		local dir = Vector3.zero
		for k, d in moveKeys do if UIS:IsKeyDown(k) then dir += d end end
		dir += Vector3.new(padMove.X, 0, -padMove.Y)
		v.yaw -= padLook.X * dt * 2.2
		v.pitch = math.clamp(v.pitch + padLook.Y * dt * 1.6, -1.4, 1.4)
		local rot = CFrame.fromOrientation(v.pitch, v.yaw, 0)
		local speed = if UIS:IsKeyDown(Enum.KeyCode.LeftShift) then 90 else 40
		if dir.Magnitude > 0 then v.pos += rot:VectorToWorldSpace(dir.Unit) * speed * dt end
		camera.CFrame = CFrame.new(v.pos) * rot
		who.Text = "FREE CAM"
	else
		local p = current(v)
		local root = p and p.Character and p.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
		if p and root then
			local look = root.CFrame.LookVector * Vector3.new(1, 0, 1)
			if look.Magnitude < 0.1 then look = Vector3.new(0, 0, -1) end
			local want = root.Position - look.Unit * 11 + Vector3.new(0, 4.5, 0)
			local k = 1 - math.exp(-dt * 8)
			local from = if (camera.CFrame.Position - want).Magnitude > 60 then want else camera.CFrame.Position:Lerp(want, k)
			camera.CFrame = CFrame.lookAt(from, root.Position + Vector3.new(0, 1.5, 0))
			local t = p:GetAttribute("Team")
			who.Text = string.upper(p.DisplayName)
			who.TextColor3 = if type(t) == "number" and TEAM_COLORS[t] then TEAM_COLORS[t] else T.TEXT
		else
			-- (nobody up right now: between rounds or everyone down. look at the arena from above)
			camera.CFrame = CFrame.lookAt(v.centre + Vector3.new(0, 60, 70), v.centre)
			who.Text = "-"
			who.TextColor3 = T.TEXT
		end
	end
	local m: any = nil
	for _, x in matches do if x.id == v.id then m = x end end
	what.Text = string.upper(v.mode) .. "  ·  " .. string.upper(v.title) .. (if m then "  ·  " .. scoreOf(m) .. "  ·  " .. stateOf(m) else "")
	freeB.BackgroundColor3 = if v.free then T.CARD_HI else T.BG
end)

UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if panelOpen and (io.KeyCode == Enum.KeyCode.ButtonB) then closePanel(); return end
	if not view then return end
	local k = io.KeyCode
	if k == Enum.KeyCode.Q or k == Enum.KeyCode.Left or k == Enum.KeyCode.DPadLeft then cycle(-1)
	elseif k == Enum.KeyCode.E or k == Enum.KeyCode.Right or k == Enum.KeyCode.DPadRight then cycle(1)
	elseif k == Enum.KeyCode.F or k == Enum.KeyCode.ButtonY then toggleFree()
	elseif k == Enum.KeyCode.Backspace or k == Enum.KeyCode.ButtonB then leave()
	elseif io.UserInputType == Enum.UserInputType.MouseButton2 then mouseLook = true
	end
end)
UIS.InputEnded:Connect(function(io: InputObject)
	if io.UserInputType == Enum.UserInputType.MouseButton2 then mouseLook = false end
	if io.KeyCode == Enum.KeyCode.Thumbstick1 then padMove = Vector2.zero end
	if io.KeyCode == Enum.KeyCode.Thumbstick2 then padLook = Vector2.zero end
end)
UIS.InputChanged:Connect(function(io: InputObject)
	local v = view
	if not v or not v.free then return end
	if io.UserInputType == Enum.UserInputType.MouseMovement and mouseLook then
		v.yaw -= io.Delta.X * 0.004
		v.pitch = math.clamp(v.pitch - io.Delta.Y * 0.004, -1.4, 1.4)
	elseif io.KeyCode == Enum.KeyCode.Thumbstick1 then
		local p = Vector2.new(io.Position.X, io.Position.Y)
		padMove = if p.Magnitude > 0.15 then p else Vector2.zero
	elseif io.KeyCode == Enum.KeyCode.Thumbstick2 then
		local p = Vector2.new(io.Position.X, io.Position.Y)
		padLook = if p.Magnitude > 0.15 then p else Vector2.zero
	end
end)

-- the board's prompt opens the panel
game:GetService("ProximityPromptService").PromptTriggered:Connect(function(prompt, by)
	if by ~= me or prompt:GetAttribute("SpectateOpen") ~= true then return end
	openPanel()
end)
-- the PLAY screen's WATCH tab
task.spawn(function()
	local m = script.Parent:WaitForChild("PlayUI", 10)
	if m and m:IsA("ModuleScript") then
		local ok, PlayUI = pcall(require, m)
		if ok and type(PlayUI) == "table" then
			(PlayUI :: any).openWatch = function()
				if (PlayUI :: any).close then (PlayUI :: any).close() end
				openPanel()
			end
		end
	end
end)

-- the list: every 2.5 s while the panel is open, you watch, or a board is near the camera
task.spawn(function()
	while true do
		task.wait(0.5)
		local near = false
		local cp = camera.CFrame.Position
		for part in boards do if (part.Position - cp).Magnitude < 140 then near = true; break end end
		if (panelOpen or view or near) and os.clock() - lastList > 2.5 then
			refreshList()
			if panelOpen then drawPanel() end
			for _, b in boards do if (b.part.Position - cp).Magnitude < 140 then drawBoard(b) end end
		end
	end
end)

-- (Studio tests) the player attribute SpectateTest: "open" opens the panel, a match id watches it, "leave" leaves
me:GetAttributeChangedSignal("SpectateTest"):Connect(function()
	local v = me:GetAttribute("SpectateTest")
	if v == nil or not RunService:IsStudio() then return end
	me:SetAttribute("SpectateTest", nil)
	if v == "open" then openPanel()
	elseif v == "leave" then leave()
	elseif v == "next" then cycle(1)
	elseif v == "free" then toggleFree()
	else watchNow(tonumber(v) or v) end
end)
