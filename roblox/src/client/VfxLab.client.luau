--!strict
-- THE VFX LAB (the VFX session, 26 Nov 2026): the owner's panel for seeing and testing every anime weapon effect.
-- Studio, or the place's creator only (it draws on this client alone, so no server check is needed). F6 or "/vfx" (F10 is Roblox's graphics quality).
--   every effect: PLAY once, or LOOP (again as soon as it ends)
--   speed: 1x, 0.5x, 0.25x, 0.1x, FREEZE (the effects' own clock: AnimeFx.setTimeScale)
--   tint: the melee weapons' colours
--   DUMMY: a still copy of you, 10 studs ahead, to hit; effects play on it when it's out
--   SWING: L>R and R>L, the slash as your own first-person swing draws it
--   WEAPON SWING (27 Nov): a body that swings each melee weapon as everyone sees a player swing it, the blade's sweep
--   on it; BLADE / CARD switches the sweep and the old camera-facing crescent. Walk round it, or FREEZE and look
-- plain on purpose: no flavour text (the owner's rule)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local TextChatService = game:GetService("TextChatService")

local me = Players.LocalPlayer
local creator = game.CreatorType == Enum.CreatorType.User and me.UserId > 0 and me.UserId == game.CreatorId
if not (RunService:IsStudio() or creator) then return end

local AnimeFx = require(script.Parent:WaitForChild("AnimeFx")) :: any
local Anims = require(game:GetService("ReplicatedStorage"):WaitForChild("Jankfire"):WaitForChild("Anims")) :: any
local CollectionService = game:GetService("CollectionService")
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

-- the weapon swing: a copy of you posed by ThirdPerson as a test rig (tagged TPRig, TPWeapon = the weapon; a new
-- TPSwing number swings it), side-on 8 studs ahead, the sweep on the blade it holds
label("WEAPON SWING (walk round it)")
do
	local MELEE = { "katana", "scythe", "knife", "claw", "bread", "slapper", "slipper", "scales" }
	local swingW = "katana"
	local swinger: Model? = nil
	local swingN = 0
	local looping = false
	local function makeSwinger()
		if swinger then swinger:Destroy(); swinger = nil end
		local ch = me.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		local cam = workspace.CurrentCamera
		if not (ch and root and cam) then return end
		ch.Archivable = true
		local m = ch:Clone()
		ch.Archivable = false
		for _, d in m:GetDescendants() do
			if d:IsA("Script") or d:IsA("LocalScript") or d:IsA("Sound") then d:Destroy()
			elseif d:IsA("BasePart") then d.Anchored = d.Name == "HumanoidRootPart"; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
		end
		for _, n in { "TPGun", "TPGun2" } do local g = m:FindFirstChild(n); if g then g:Destroy() end end
		local hum = m:FindFirstChildOfClass("Humanoid")
		if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
		local f = Vector3.new(cam.CFrame.LookVector.X, 0, cam.CFrame.LookVector.Z)
		f = if f.Magnitude > 1e-3 then f.Unit else Vector3.new(0, 0, -1)
		local at = root.Position + f * 8
		m:PivotTo(CFrame.lookAt(at, at + f:Cross(Vector3.yAxis))) -- (side-on: you see the swing's plane at once)
		m.Name = "VfxLabSwinger"
		m:SetAttribute("TPWeapon", swingW)
		CollectionService:AddTag(m, "TPRig")
		m.Parent = workspace
		swinger = m
	end
	local function swing(): number
		if not swinger or not swinger.Parent then makeSwinger(); task.wait(0.4) end
		local m = swinger
		if not m then return 1 end
		if m:GetAttribute("TPWeapon") ~= swingW then m:SetAttribute("TPWeapon", swingW); task.wait(0.4) end
		swingN += 1
		m:SetAttribute("TPSwing", swingN)
		local an = Anims["swing_" .. swingW]
		local t1 = if an and an.trail then an.trail[1] else 0.08
		local dur = if an and an.trail then math.max(0.12, (an.trail[2] - an.trail[1]) * 1.3) else 0.18
		local wid, n = swingW, swingN
		task.delay(t1, function()
			if not m.Parent then return end
			if AnimeFx.STYLE == "blade" and AnimeFx.bodySweep(m, AnimeFx.tintFor(wid), dur) then return end
			local r = m:FindFirstChild("HumanoidRootPart") :: BasePart?
			if r then AnimeFx.bodySlash(r, r.CFrame.LookVector, n % 2 == 0, AnimeFx.reach(wid), AnimeFx.tintFor(wid)) end
		end)
		return 1.1
	end
	local wBtns: { [string]: TextButton } = {}
	for i = 1, #MELEE, 4 do
		local r = row()
		for j = i, math.min(i + 3, #MELEE) do
			local w = MELEE[j]
			wBtns[w] = button(r, string.upper(w), 66, function(b)
				swingW = w
				for _, o in wBtns do o.BackgroundColor3 = Color3.fromRGB(44, 46, 54) end
				b.BackgroundColor3 = Color3.fromRGB(70, 110, 170)
				if swinger then swinger:SetAttribute("TPWeapon", w) end
			end)
		end
	end
	wBtns.katana.BackgroundColor3 = Color3.fromRGB(70, 110, 170)
	local r = row()
	button(r, "SWING", 70, function() task.spawn(swing) end)
	button(r, "LOOP", 60, function(b)
		looping = not looping
		b.BackgroundColor3 = if looping then Color3.fromRGB(70, 110, 170) else Color3.fromRGB(44, 46, 54)
		if looping then
			task.spawn(function()
				while looping and gui.Parent do
					local w = swing()
					local t = 0
					while t < w and looping do t += task.wait() * math.max(AnimeFx.timeScale(), 0.02) end
				end
			end)
		end
	end)
	button(r, "REMOVE", 76, function() looping = false; if swinger then swinger:Destroy(); swinger = nil end end)
	local r2 = row()
	local styleB: TextButton
	styleB = button(r2, "STYLE: BLADE", 130, function()
		AnimeFx.STYLE = if AnimeFx.STYLE == "blade" then "card" else "blade"
		styleB.Text = "STYLE: " .. string.upper(AnimeFx.STYLE)
	end)
end

-- VFX.LAB TRIAL (27 Nov 2026, main's trial of VFX.LAB, a browser effect editor kept in the vault): two bodies side by
-- side swing the same weapon at once. The LEFT one plays our live effects (the blade sweep and the hit), the RIGHT one
-- plays flipbooks baked in VFX.LAB (uploaded images). Lab only: no live effect changes.
-- The right body's flipbook lies in the blade's plane: each swing samples the blade tip, fits its plane and circle (in
-- the body's own space) and the next swing places the sheet's arc on it (the first swing of a weapon only measures)
label("VFX.LAB TRIAL: OURS left, VFX.LAB right")
do
	local SHEETS: { [string]: { tex: string, h: number, life: number } } = {
		-- (the baked cell: a top view of an arc of mean radius 2 around the pivot, which sits 0.6 below the cell's centre;
		-- the cell is 2 h wide, h = the bake camera's distance * tan 19 degrees)
		katana = { tex = "rbxassetid://75647748106209", h = 8.4 * math.tan(math.rad(19)), life = 0.26 },
		scythe = { tex = "rbxassetid://102968309029301", h = 8.8 * math.tan(math.rad(19)), life = 0.26 },
	}
	local HIT_TEX, HIT_LIFE = "rbxassetid://103114439178777", 0.3
	local BAKE_R, BAKE_OFF = 2, 0.6
	local trialW = "katana"
	local pair: { Model } = {}
	local swingN = 0
	local looping = false
	local cal: { [string]: { c: Vector3, nrm: Vector3, mid: Vector3, r: number } } = {}
	local function fxFolder(): Instance return workspace:FindFirstChild("JankAnimeFx") or workspace end
	local function body(at: Vector3, f: Vector3, name: string): Model?
		local ch = me.Character
		if not ch then return nil end
		ch.Archivable = true
		local m = ch:Clone()
		ch.Archivable = false
		for _, d in m:GetDescendants() do
			if d:IsA("Script") or d:IsA("LocalScript") or d:IsA("Sound") then d:Destroy()
			elseif d:IsA("BasePart") then d.Anchored = d.Name == "HumanoidRootPart"; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
		end
		for _, n in { "TPGun", "TPGun2" } do local g = m:FindFirstChild(n); if g then g:Destroy() end end
		local hum = m:FindFirstChildOfClass("Humanoid")
		if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None end
		m:PivotTo(CFrame.lookAt(at, at + f))
		m.Name = name
		m:SetAttribute("TPWeapon", trialW)
		CollectionService:AddTag(m, "TPRig")
		m.Parent = workspace
		return m
	end
	local function removePair()
		looping = false
		for _, m in pair do m:Destroy() end
		table.clear(pair)
	end
	local function makePair()
		removePair()
		local ch = me.Character
		local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		local cam = workspace.CurrentCamera
		if not (root and cam) then return end
		local f = Vector3.new(cam.CFrame.LookVector.X, 0, cam.CFrame.LookVector.Z)
		f = if f.Magnitude > 1e-3 then f.Unit else Vector3.new(0, 0, -1)
		local right = f:Cross(Vector3.yAxis)
		local c0 = root.Position + f * 12
		-- (side-on, both facing the camera's right: you see each swing's plane; workspace TrialFace = "front" turns them
		-- to face you)
		local face = if workspace:GetAttribute("TrialFace") == "front" then -f else right
		local a = body(c0 - right * 5, face, "VfxLabOurs")
		local b = body(c0 + right * 5, face, "VfxLabTrial")
		if a and b then pair[1] = a; pair[2] = b end
	end
	-- one flat or camera-facing flipbook particle, painted (LightEmission 0, unlit), on the effect clock
	local function emit(cf: CFrame, tex: string, size: number, life: number, flat: boolean, rot: number)
		local p = Instance.new("Part")
		p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false; p.CastShadow = false
		p.Transparency = 1
		p.Size = Vector3.new(0.2, 0.2, 0.2)
		p.CFrame = cf
		p.Name = "VfxLabTrialFx"
		local at = Instance.new("Attachment")
		at.Parent = p
		local e = Instance.new("ParticleEmitter")
		e.Texture = tex
		e.Enabled = false
		pcall(function() (e :: any).FlipbookBlendFrames = false end)
		e.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
		e.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
		e.FlipbookFramerate = NumberRange.new(16 / life)
		e.FlipbookStartRandom = false
		e.Lifetime = NumberRange.new(life)
		e.Rotation = NumberRange.new(rot)
		e.RotSpeed = NumberRange.new(0)
		e.Size = NumberSequence.new(size)
		e.LightEmission = 0
		e.LightInfluence = 0
		e.Brightness = 1
		e.LockedToPart = true
		e.TimeScale = AnimeFx.timeScale()
		if flat then
			-- (a flat sheet: perpendicular to its velocity, a crawl along the attachment's look)
			e.Orientation = Enum.ParticleOrientation.VelocityPerpendicular
			e.EmissionDirection = Enum.NormalId.Front
			e.Speed = NumberRange.new(0.01)
			e.SpreadAngle = Vector2.zero
		else
			e.Orientation = Enum.ParticleOrientation.FacingCamera
			e.Speed = NumberRange.new(0)
			e.ZOffset = AnimeFx.nearZ(cf.Position)
		end
		e.Parent = at
		p.Parent = fxFolder()
		e:Emit(1)
		task.delay(life / math.max(AnimeFx.timeScale(), 0.01) + 0.3, function()
			while p.Parent and AnimeFx.timeScale() < 0.01 do task.wait(0.2) end
			p:Destroy()
		end)
	end
	-- the blade's plane and circle from tip samples, in the body's root space. The normal follows the right-hand rule
	-- of the swing (it turns anticlockwise seen from +nrm); the circle is a least-squares (Kasa) fit in that plane
	local function fit(pts: { Vector3 }): { c: Vector3, nrm: Vector3, mid: Vector3, r: number }?
		local n = #pts
		if n < 4 then return nil end
		local area = Vector3.zero
		for i = 2, n - 1 do area += (pts[i] - pts[1]):Cross(pts[i + 1] - pts[1]) end
		if area.Magnitude < 1e-4 then return nil end
		local nrm = area.Unit
		local mean = Vector3.zero
		for _, q in pts do mean += q end
		mean /= n
		local e1 = (pts[n] - pts[1]) - nrm * (pts[n] - pts[1]):Dot(nrm)
		e1 = if e1.Magnitude > 1e-4 then e1.Unit else nrm:Cross(Vector3.yAxis).Unit
		local e2 = nrm:Cross(e1)
		-- x^2 + y^2 + D x + E y + F = 0, least squares: the 3x3 normal equations by Cramer's rule
		local sxx, sxy, sx, syy, sy, sxz, syz, sz = 0, 0, 0, 0, 0, 0, 0, 0
		for _, q in pts do
			local x, y = (q - mean):Dot(e1), (q - mean):Dot(e2)
			local z = -(x * x + y * y)
			sxx += x * x; sxy += x * y; sx += x; syy += y * y; sy += y; sxz += x * z; syz += y * z; sz += z
		end
		local function det(a: number, b: number, c: number, d: number, e: number, f: number, g: number, h: number, i: number): number
			return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
		end
		local D0 = det(sxx, sxy, sx, sxy, syy, sy, sx, sy, n)
		if math.abs(D0) < 1e-6 then return nil end
		local D = det(sxz, sxy, sx, syz, syy, sy, sz, sy, n) / D0
		local E = det(sxx, sxz, sx, sxy, syz, sy, sx, sz, n) / D0
		local F = det(sxx, sxy, sxz, sxy, syy, syz, sx, sy, sz) / D0
		local cx, cy = -D / 2, -E / 2
		local r2 = cx * cx + cy * cy - F
		if r2 <= 0 then return nil end
		local c = mean + e1 * cx + e2 * cy
		local midP = pts[math.ceil(n / 2)]
		local mid = (midP - c) - nrm * (midP - c):Dot(nrm)
		if mid.Magnitude < 1e-4 then return nil end
		return { c = c, nrm = nrm, mid = mid.Unit, r = math.sqrt(r2) }
	end
	-- the blade tip of a body's held weapon, world space
	local function tipOf(m: Model): Vector3?
		local g = m:FindFirstChild("TPGun")
		local mz = g and g:FindFirstChild("Muzzle", true)
		return if mz and mz:IsA("Attachment") then mz.WorldPosition else nil
	end
	-- the sheet's arc on the measured circle. The bake looks down on an arc that runs clockwise on screen, so it is
	-- seen from -nrm; the particle crawls along the attachment's look (VelocityPerpendicular) and its texture's up is
	-- set by the attachment's up (workspace TrialVel = +-1 and TrialRot (deg) correct either if the probe says so)
	local function trialSweep(m: Model, wid: string)
		local k = cal[wid]
		local s = SHEETS[wid] or SHEETS.katana
		local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not (k and root) then return end
		local rc = root.CFrame
		local c, nrm, mid = rc:PointToWorldSpace(k.c), rc:VectorToWorldSpace(k.nrm), rc:VectorToWorldSpace(k.mid)
		local sc = k.r / BAKE_R
		local vel = (tonumber(workspace:GetAttribute("TrialVel")) or 1) * -nrm
		local centre = c + mid * (BAKE_OFF * sc)
		local cf = CFrame.lookAt(centre, centre + vel, mid)
		emit(cf, s.tex, s.h * sc, s.life, true, tonumber(workspace:GetAttribute("TrialRot")) or 0)
	end
	local function swingPair()
		if #pair < 2 or not pair[1].Parent or not pair[2].Parent then makePair(); task.wait(0.5) end
		if #pair < 2 then return end
		local A, B = pair[1], pair[2]
		for _, m in pair do
			if m:GetAttribute("TPWeapon") ~= trialW then m:SetAttribute("TPWeapon", trialW); task.wait(0.4) end
		end
		swingN += 1
		A:SetAttribute("TPSwing", swingN)
		B:SetAttribute("TPSwing", swingN)
		local wid = trialW
		local an = Anims["swing_" .. wid]
		local t1 = if an and an.trail then an.trail[1] else 0.08
		local dur = if an and an.trail then math.max(0.12, (an.trail[2] - an.trail[1]) * 1.3) else 0.18
		local tint = AnimeFx.tintFor(wid)
		task.delay(t1, function()
			if A.Parent then AnimeFx.bodySweep(A, tint, dur) end
			if B.Parent and cal[wid] then trialSweep(B, wid) end
			-- B's tip, sampled over the cut, measures the plane for the next swing (on the effect clock)
			local pts: { Vector3 } = {}
			local rb = B:FindFirstChild("HumanoidRootPart") :: BasePart?
			local t = 0
			while t < dur and B.Parent do
				local p = tipOf(B)
				if p and rb then table.insert(pts, rb.CFrame:PointToObjectSpace(p)) end
				t += task.wait() * math.max(AnimeFx.timeScale(), 0.02)
			end
			local k = fit(pts)
			if k then
				cal[wid] = k
				-- (tests: the fitted circle and how far the tip swept round it, degrees)
				local u0, u1 = pts[1] - k.c, pts[#pts] - k.c
				u0 -= k.nrm * u0:Dot(k.nrm); u1 -= k.nrm * u1:Dot(k.nrm)
				local sw = if u0.Magnitude > 1e-4 and u1.Magnitude > 1e-4 then math.deg(math.acos(math.clamp(u0.Unit:Dot(u1.Unit), -1, 1))) else 0
				workspace:SetAttribute("TrialCal_" .. wid, string.format("r=%.2f sweep=%.0f n=%d", k.r, sw, #pts))
			end
		end)
		-- the hit, halfway through the cut, at each body's blade tip
		task.delay(t1 + dur * 0.5, function()
			local pa = if A.Parent then tipOf(A) else nil
			local pb = if B.Parent then tipOf(B) else nil
			local ra, rb = A:FindFirstChild("HumanoidRootPart") :: BasePart?, B:FindFirstChild("HumanoidRootPart") :: BasePart?
			if pa and ra then AnimeFx.hit(pa, ra.Position, tint, false, false, false) end
			if pb and rb then
				local cam = workspace.CurrentCamera
				local at = pb
				if cam then
					local toCam = cam.CFrame.Position - at
					if toCam.Magnitude > 2.5 then at += toCam.Unit * 1.4 end -- (as ours: drawn on the side facing you)
				end
				emit(CFrame.new(at), HIT_TEX, 2.4, HIT_LIFE, false, math.random(0, 359))
			end
		end)
	end
	local r = row()
	local wb: { [string]: TextButton } = {}
	for _, w in { "katana", "scythe" } do
		wb[w] = button(r, string.upper(w), 70, function(b)
			trialW = w
			for _, o in wb do o.BackgroundColor3 = Color3.fromRGB(44, 46, 54) end
			b.BackgroundColor3 = Color3.fromRGB(70, 110, 170)
			for _, m in pair do m:SetAttribute("TPWeapon", w) end
		end)
	end
	wb.katana.BackgroundColor3 = Color3.fromRGB(70, 110, 170)
	button(r, "PAIR", 54, function() makePair() end)
	local r2 = row()
	button(r2, "SWING", 70, function() task.spawn(swingPair) end)
	button(r2, "LOOP", 60, function(b)
		looping = not looping
		b.BackgroundColor3 = if looping then Color3.fromRGB(70, 110, 170) else Color3.fromRGB(44, 46, 54)
		if looping then
			task.spawn(function()
				while looping and gui.Parent do
					swingPair()
					local t = 0
					while t < 1.6 and looping do t += task.wait() * math.max(AnimeFx.timeScale(), 0.02) end -- (1.6 s apart: always the first cut, never the backhand)
				end
			end)
		end
	end)
	button(r2, "REMOVE", 76, removePair)
	-- (tests: workspace TrialMake = n makes the pair (TrialWeapon picks katana / scythe); TrialSwing = n swings it once)
	workspace:GetAttributeChangedSignal("TrialSwing"):Connect(function() task.spawn(swingPair) end)
	workspace:GetAttributeChangedSignal("TrialMake"):Connect(function()
		local w = workspace:GetAttribute("TrialWeapon")
		if type(w) == "string" and SHEETS[w] then trialW = w end
		makePair()
	end)
	-- the probe (tests): one flat trial sheet 10 studs ahead, look = TrialProbeLook, up = TrialProbeUp, held for 8 s
	workspace:GetAttributeChangedSignal("TrialProbe"):Connect(function()
		local cam = workspace.CurrentCamera
		if not cam then return end
		local look = workspace:GetAttribute("TrialProbeLook")
		local up = workspace:GetAttribute("TrialProbeUp")
		local at = cam.CFrame.Position + cam.CFrame.LookVector * 10
		local lv = if typeof(look) == "Vector3" then look else -cam.CFrame.LookVector
		local uv = if typeof(up) == "Vector3" then up else Vector3.yAxis
		emit(CFrame.lookAt(at, at + lv, uv), SHEETS.katana.tex, 3, 8, true, tonumber(workspace:GetAttribute("TrialRot")) or 0)
	end)
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
