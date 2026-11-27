--!strict
-- THE VFX LAB (the VFX session, 26 Nov 2026): the owner's panel for seeing and testing every anime weapon effect.
-- Studio, or the place's creator only (it draws on this client alone, so no server check is needed). F6 or "/vfx" (F10 is Roblox's graphics quality).
--   every effect: PLAY once, or LOOP (again as soon as it ends)
--   speed: 1x, 0.5x, 0.25x, 0.1x, FREEZE (the effects' own clock: AnimeFx.setTimeScale)
--   tint: the melee weapons' colours
--   DUMMY: a still copy of you, 10 studs ahead, to hit; effects play on it when it's out
--   SWING: L>R and R>L, the slash as your own first-person swing draws it
-- plain on purpose: no flavour text (the owner's rule)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local TextChatService = game:GetService("TextChatService")

local me = Players.LocalPlayer
local creator = game.CreatorType == Enum.CreatorType.User and me.UserId > 0 and me.UserId == game.CreatorId
if not (RunService:IsStudio() or creator) then return end

local AnimeFx = require(script.Parent:WaitForChild("AnimeFx")) :: any
local Fx = require(script.Parent:WaitForChild("Fx")) :: any -- (the gun's flash and puff)

local TINTS = {
	{ "KATANA", Color3.fromRGB(70, 160, 255) },
	{ "SCYTHE", Color3.fromRGB(62, 230, 200) },
	{ "KNIFE", Color3.fromRGB(200, 208, 220) },
	{ "RED", Color3.fromRGB(235, 60, 50) },
	{ "GOLD", Color3.fromRGB(255, 196, 70) },
	{ "VIOLET", Color3.fromRGB(170, 110, 255) },
}
local tint = TINTS[1][2]
local loops: { [string]: boolean } = {}
local dummy: Model? = nil

local gui = Instance.new("ScreenGui")
gui.Name = "VfxLab"
gui.ResetOnSpawn = false
gui.DisplayOrder = 60
gui.Enabled = false
gui.Parent = me:WaitForChild("PlayerGui")

local frame = Instance.new("ScrollingFrame") -- (the list outgrew a short screen: it scrolls)
frame.Size = UDim2.new(0, 310, 0.86, 0)
frame.Position = UDim2.new(0, 16, 0.07, 0)
frame.CanvasSize = UDim2.new()
frame.AutomaticCanvasSize = Enum.AutomaticSize.Y
frame.ScrollBarThickness = 5
frame.ScrollingDirection = Enum.ScrollingDirection.Y
frame.BackgroundColor3 = Color3.fromRGB(22, 23, 27)
frame.BackgroundTransparency = 0.08
frame.BorderSizePixel = 0
frame.Parent = gui
local pad = Instance.new("UIPadding")
pad.PaddingLeft = UDim.new(0, 10); pad.PaddingRight = UDim.new(0, 10); pad.PaddingTop = UDim.new(0, 10); pad.PaddingBottom = UDim.new(0, 10)
pad.Parent = frame
local list = Instance.new("UIListLayout")
list.Padding = UDim.new(0, 6)
list.SortOrder = Enum.SortOrder.LayoutOrder
list.Parent = frame

local order = 0
local function label(text: string, size: number?): TextLabel
	order += 1
	local t = Instance.new("TextLabel")
	t.Size = UDim2.new(1, 0, 0, size or 18)
	t.BackgroundTransparency = 1
	t.Font = Enum.Font.GothamBold
	t.TextSize = 13
	t.TextColor3 = Color3.fromRGB(150, 154, 165)
	t.TextXAlignment = Enum.TextXAlignment.Left
	t.Text = text
	t.LayoutOrder = order
	t.Parent = frame
	return t
end
local function row(): Frame
	order += 1
	local r = Instance.new("Frame")
	r.Size = UDim2.new(1, 0, 0, 26)
	r.BackgroundTransparency = 1
	r.LayoutOrder = order
	r.Parent = frame
	local l = Instance.new("UIListLayout")
	l.FillDirection = Enum.FillDirection.Horizontal
	l.Padding = UDim.new(0, 4)
	l.Parent = r
	return r
end
local function button(parent: Instance, text: string, w: number, fn: (TextButton) -> ()): TextButton
	local b = Instance.new("TextButton")
	b.Size = UDim2.new(0, w, 1, 0)
	b.BackgroundColor3 = Color3.fromRGB(44, 46, 54)
	b.BorderSizePixel = 0
	b.AutoButtonColor = true
	b.Font = Enum.Font.GothamBold
	b.TextSize = 12
	b.TextColor3 = Color3.fromRGB(230, 232, 238)
	b.Text = text
	b.Parent = parent
	b.MouseButton1Click:Connect(function() fn(b) end)
	return b
end

-- where an effect plays: on the dummy if it's out, else 10 studs ahead at chest height
local function target(): (Vector3, Vector3)
	local cam = workspace.CurrentCamera
	local root = me.Character and me.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
	local from = if cam then cam.CFrame.Position else Vector3.zero
	if dummy and dummy.Parent then
		local r = dummy:FindFirstChild("HumanoidRootPart") :: BasePart?
		if r then return r.Position + Vector3.new(0, 0.6, 0), from end
	end
	if root and cam then
		local f = Vector3.new(cam.CFrame.LookVector.X, 0, cam.CFrame.LookVector.Z)
		f = if f.Magnitude > 1e-3 then f.Unit else Vector3.new(0, 0, -1)
		return root.Position + f * 10 + Vector3.new(0, 0.6, 0), from
	end
	return from + Vector3.new(0, 0, -10), from
end

-- a first-person swing's tip path, left to right (or back), in camera space: a shallow arc in front
local function fpPath(rtl: boolean): { Vector3 }
	local pts = {}
	for i = 0, 8 do
		local k = i / 8
		local x = -1.6 + 3.2 * k
		if rtl then x = -x end
		local y = 0.35 - 0.9 * (x / 1.6) ^ 2 * 0.5 - 0.25 * k
		table.insert(pts, Vector3.new(x, y, -2.6))
	end
	return pts
end

local alt = false
local function play(kind: string, id: string): number
	local at, from = target()
	if kind == "slash" then
		local root = me.Character and me.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
		if dummy and dummy.Parent then
			-- seen from outside: the dummy swings at you
			local r = dummy:FindFirstChild("HumanoidRootPart") :: BasePart?
			if r then AnimeFx.bodySlash(r, (from - r.Position).Unit, alt, 9, tint) end
		elseif root then
			local d2 = Vector2.new(if alt then -1 else 1, -0.15)
			AnimeFx.slash(CFrame.new(at), d2.Unit, alt, 3.2, tint, { take = id })
		end
		alt = not alt
	elseif kind == "burst" then AnimeFx.burst(at, 2.4, tint, nil, id)
	elseif kind == "sparks" then AnimeFx.sparks(at, (at - from).Unit * 0.7 + Vector3.new(0, 0.7, 0), 6, tint) -- (away from you, as a hit's)
	elseif kind == "twinkle" then AnimeFx.twinkle(at, 1.6, tint)
	elseif kind == "hit" then AnimeFx.hit(at, from, tint, true, false)
	elseif kind == "impact" then AnimeFx.impactFrame()
	elseif kind == "muzzle" then
		-- side-on: the barrel points across the screen (the jet); facing you: at the camera (the front drawing)
		local cam = workspace.CurrentCamera
		local dir = if id == "muzzle_front" then (from - at).Unit elseif cam then cam.CFrame.RightVector else Vector3.xAxis
		Fx.muzzle(CFrame.lookAt(at, at + dir), false, false, nil)
		return 0.9
	elseif kind == "bullet" then
		-- Fx.impact as a gun calls it, on concrete: the anime pop, the chips and the dust (no hole: nothing is hit)
		local cam = workspace.CurrentCamera
		local n = if id == "pop_wall" and cam then -cam.CFrame.RightVector else Vector3.yAxis
		Fx.impact(at - Vector3.new(0, 1.2, 0), n, nil, Enum.Material.Concrete, { hole = false })
		return 0.6
	elseif kind == "lib" then
		AnimeFx.lib(id, at, 3)
		local l = AnimeFx.LIB[id]
		return if l then l.life else 1
	end
	return 0.6
end

label("VFX LAB", 20).TextColor3 = Color3.fromRGB(235, 236, 240)
for _, e in AnimeFx.LIST do
	local r = row()
	local name = Instance.new("TextLabel")
	name.Size = UDim2.new(0, 150, 1, 0)
	name.BackgroundTransparency = 1
	name.Font = Enum.Font.Gotham
	name.TextSize = 12
	name.TextColor3 = Color3.fromRGB(210, 212, 220)
	name.TextXAlignment = Enum.TextXAlignment.Left
	name.Text = e.label
	name.TextTruncate = Enum.TextTruncate.AtEnd
	name.Parent = r
	button(r, "PLAY", 54, function() play(e.kind, e.id) end)
	button(r, "LOOP", 54, function(b)
		loops[e.id] = not loops[e.id]
		b.BackgroundColor3 = if loops[e.id] then Color3.fromRGB(70, 110, 170) else Color3.fromRGB(44, 46, 54)
		if loops[e.id] then
			task.spawn(function()
				while loops[e.id] and gui.Parent do
					local w = play(e.kind, e.id)
					local t = 0
					while t < w + 0.25 and loops[e.id] do t += task.wait() * math.max(AnimeFx.timeScale(), 0.02) end
				end
			end)
		end
	end)
end

label("FIRST-PERSON SWING")
do
	local r = row()
	button(r, "L > R", 80, function() AnimeFx.ownSlash(fpPath(false), tint) end)
	button(r, "R > L", 80, function() AnimeFx.ownSlash(fpPath(true), tint) end)
end

label("SPEED")
do
	local r = row()
	local speedBtns: { TextButton } = {}
	for _, s in { { "1x", 1 }, { "0.5x", 0.5 }, { "0.25x", 0.25 }, { "0.1x", 0.1 }, { "FREEZE", 0 } } do
		local b = button(r, s[1] :: string, if s[2] == 0 then 62 else 48, function(b)
			AnimeFx.setTimeScale(s[2] :: number)
			Fx.setTimeScale(s[2] :: number)
			for _, o in speedBtns do o.BackgroundColor3 = Color3.fromRGB(44, 46, 54) end
			b.BackgroundColor3 = Color3.fromRGB(70, 110, 170)
		end)
		table.insert(speedBtns, b)
	end
end

label("TINT")
do
	local r = row()
	for _, t in TINTS do
		local b = button(r, "", 40, function() tint = t[2] :: Color3 end)
		b.BackgroundColor3 = t[2] :: Color3
	end
end

label("DUMMY")
do
	local r = row()
	button(r, "PLACE", 80, function()
		if dummy then dummy:Destroy(); dummy = nil end
		local ch = me.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		local cam = workspace.CurrentCamera
		if not (ch and root and cam) then return end
		ch.Archivable = true
		local m = ch:Clone()
		ch.Archivable = false
		for _, d in m:GetDescendants() do
			if d:IsA("Script") or d:IsA("LocalScript") or d:IsA("Sound") then d:Destroy()
			elseif d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false end
		end
		local hum = m:FindFirstChildOfClass("Humanoid")
		if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
		local f = Vector3.new(cam.CFrame.LookVector.X, 0, cam.CFrame.LookVector.Z)
		f = if f.Magnitude > 1e-3 then f.Unit else Vector3.new(0, 0, -1)
		local at = root.Position + f * 10
		m:PivotTo(CFrame.lookAt(at, at - f))
		m.Name = "VfxLabDummy"
		m.Parent = workspace
		dummy = m
	end)
	button(r, "REMOVE", 80, function() if dummy then dummy:Destroy(); dummy = nil end end)
	button(r, "CLEAR FX", 90, function() AnimeFx.clear() end)
end

local function toggle()
	gui.Enabled = not gui.Enabled
	AnimeFx.LAB = gui.Enabled
	if not gui.Enabled then
		for k in loops do loops[k] = false end
		AnimeFx.setTimeScale(1)
		Fx.setTimeScale(1)
	end
end
UIS.InputBegan:Connect(function(io: InputObject, gp: boolean)
	if gp then return end
	if io.KeyCode == Enum.KeyCode.F6 then toggle() end
end)
if TextChatService.ChatVersion == Enum.ChatVersion.TextChatService then
	local cmd = Instance.new("TextChatCommand")
	cmd.Name = "JankVfxLab"
	cmd.PrimaryAlias = "/vfx"
	cmd.Parent = TextChatService
	cmd.Triggered:Connect(function() toggle() end)
end
-- (Studio tests: player attribute VfxLab = "open" / "close")
me:GetAttributeChangedSignal("VfxLab"):Connect(function()
	local v = me:GetAttribute("VfxLab")
	if v == "open" and not gui.Enabled then toggle() elseif v == "close" and gui.Enabled then toggle() end
end)
