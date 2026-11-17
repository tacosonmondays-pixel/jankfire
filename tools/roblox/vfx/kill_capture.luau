-- (copy of the VFX session's capture script, 17 Nov 2026: run in the Client datamodel of a Play test with execute_luau)
-- (Client, in a Play test) the kill effects' preview capture, v2: a dark box far from the maps, its own camera (a game
-- script forces the main camera's FieldOfView to 80), two soft lights; C.stage(ids) puts a row of training-dummy
-- stand-ins (12 studs apart, cropped 8: no effect spills into a neighbour's square) playing each effect from this
-- context's KillFx copy on the frozen FlairTimeScale clock; C.runTo(t) advances them (Gibs by hand: flung, falling,
-- stopping where they land). returns the crop squares
local Players = game:GetService("Players")
local RS = game:GetService("RunService")
local me = Players.LocalPlayer
local t00 = os.clock()
while not me.Character and os.clock() - t00 < 10 do task.wait(0.2) end
task.wait(1)
local J = me.PlayerScripts:WaitForChild("Jankfire")
_G.kc = _G.kc or {}
local C = _G.kc
if C.fold then C.fold:Destroy() end
workspace:SetAttribute("FlairTimeScale", 0)
local K = C.K or require(J:WaitForChild("KillFx"))
C.K = K
C.hidden = C.hidden or {}
for _, g in me.PlayerGui:GetChildren() do
	if g:IsA("ScreenGui") and g.Enabled then g.Enabled = false; table.insert(C.hidden, g) end
end
local fold = Instance.new("Folder"); fold.Name = "JankKillCap"; fold.Parent = workspace
C.fold = fold
local O = Vector3.new(0, 900, 4000)
local BG = Color3.fromRGB(22, 24, 30)
C.slabs = {}
local function slab(size: Vector3, cf: CFrame)
	local p = Instance.new("Part"); p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
	p.Material = Enum.Material.Neon; p.Color = BG; p.Size = size; p.CFrame = cf; p.CastShadow = false; p.Parent = fold
	table.insert(C.slabs, p)
end
-- (Ink: black ink vanishes on the box's black; a lighter wall, mapped back to the card's dark by kill_sheets.py remap)
function C.backdrop(c: Color3, mat: Enum.Material?)
	for _, p in C.slabs do p.Color = c; p.Material = mat or Enum.Material.Neon end
	RS.RenderStepped:Wait(); RS.RenderStepped:Wait()
	return "backdrop " .. tostring(c) .. " " .. os.date("!%H:%M:%S")
end
slab(Vector3.new(500, 1, 400), CFrame.new(O + Vector3.new(0, -0.5, 0)))
slab(Vector3.new(500, 300, 1), CFrame.new(O + Vector3.new(0, 100, -60)))
local src: Model? = nil
for _, m in workspace:GetDescendants() do
	if m:IsA("Model") and (m.Name == "Stand" or m.Name == "Dummy") and m:FindFirstChildOfClass("Humanoid") and not m:IsDescendantOf(fold) then src = m; break end
end
if not src then return "no dummy to copy" end
local SP, N, CROP, D, FOV = 12, 6, 8, 178, 10
local face = Vector3.new(math.sin(math.rad(28)), 0, math.cos(math.rad(28)))
C.ms, C.runs, C.gib = {}, {}, {}
local function px(i: number): Vector3 return O + Vector3.new((i - (N + 1) / 2) * SP, 0, 0) end
function C.stage(ids: { string }): string
	for _, m in C.ms do pcall(function() K.reset(m) end); m:Destroy() end
	C.ms, C.runs, C.gib = {}, {}, {}
	workspace:SetAttribute("FlairTimeScale", 0)
	local g = workspace.Gravity
	for i, id in ids do
		local s = src :: Model
		local was = s.Archivable; s.Archivable = true
		local c = s:Clone(); s.Archivable = was
		for _, d in c:GetDescendants() do
			if d:IsA("LuaSourceContainer") or d:IsA("Sound") or d:IsA("BillboardGui") then d:Destroy()
			elseif d:IsA("BasePart") then d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false end
		end
		local hum = c:FindFirstChildOfClass("Humanoid")
		if hum then hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None; hum.EvaluateStateMachine = false; hum.BreakJointsOnDeath = false end
		local bcf, bsz = c:GetBoundingBox()
		local up = c:GetPivot().Position.Y - (bcf.Position.Y - bsz.Y / 2)
		local at = px(i)
		c:PivotTo(CFrame.lookAt(at + Vector3.new(0, up, 0), at + Vector3.new(0, up, 0) + face))
		c.Name = "KillCapStandIn"; c.Parent = fold
		C.ms[i] = c
		if id == "none" then
			for _, d in c:GetDescendants() do
				if d:IsA("BasePart") and d.Name ~= "HumanoidRootPart" then
					local v = Vector3.new(math.random() * 6 - 3, math.random() * 5, math.random() * 6 - 3)
					local floor = O.Y + math.min(d.Size.X, d.Size.Y, d.Size.Z) / 2
					local y0 = d.CFrame.Position.Y
					local tl = (v.Y + math.sqrt(v.Y * v.Y + 2 * g * math.max(0, y0 - floor))) / g -- (when it lands)
					table.insert(C.gib, { p = d, cf = d.CFrame, v = v, tl = tl, floor = floor,
						w = Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * 7 })
				end
			end
		else
			C.runs[i] = K.play(c, id, { preview = true })
		end
	end
	C.ref = nil
	for _, r in C.runs do if r and (not C.ref or r.dur > C.ref.dur) then C.ref = r end end
	C.t = 0
	RS.RenderStepped:Wait(); RS.RenderStepped:Wait()
	C.words()
	return "staged " .. table.concat(ids, ",") .. " ref " .. (C.ref and C.ref.id or "-") .. " " .. os.date("!%H:%M:%S")
end
function C.gibs(t: number)
	local g = workspace.Gravity
	for _, gb in C.gib do
		local tt = math.min(t, gb.tl)
		local p = gb.cf.Position + gb.v * tt + Vector3.new(0, -0.5 * g * tt * tt, 0)
		if t > gb.tl then -- (landed: a short skid, then still)
			local skid = 1 - math.exp(-(t - gb.tl) * 8)
			p = Vector3.new(p.X + gb.v.X * 0.12 * skid, gb.floor, p.Z + gb.v.Z * 0.12 * skid)
		end
		local a = gb.w * tt
		gb.p.CFrame = CFrame.new(p) * (gb.cf - gb.cf.Position) * CFrame.Angles(a.X, a.Y, a.Z)
	end
end
function C.words()
	for _, r in C.runs do
		if r and r.id == "bsod" and r.s and r.s.gui then
			for _, l in (r.s.gui :: Instance):GetDescendants() do if l:IsA("TextLabel") then l.TextTransparency = 1 end end
		end
	end
end
function C.runTo(t: number): string
	local ref = C.ref
	if ref then
		if ref.t < t - 0.05 then
			workspace:SetAttribute("FlairTimeScale", 1)
			while ref.t < t - 0.05 and not ref.done do RS.RenderStepped:Wait() end
		end
		workspace:SetAttribute("FlairTimeScale", 0.04)
		while ref.t < t and not ref.done do RS.RenderStepped:Wait() end
		workspace:SetAttribute("FlairTimeScale", 0)
	end
	C.words()
	C.gibs(t)
	RS.RenderStepped:Wait()
	return string.format("t=%.3f %s", if ref then ref.t else t, os.date("!%H:%M:%S"))
end
local cam = Instance.new("Camera")
cam.Name = "KillCapCamera"; cam.CameraType = Enum.CameraType.Scriptable; cam.FieldOfView = FOV
cam.CFrame = CFrame.lookAt(O + Vector3.new(0, 3.6, D), O + Vector3.new(0, 3.5, 0))
cam.Parent = fold
workspace.CurrentCamera = cam
C.cam = cam.CFrame
pcall(function() RS:UnbindFromRenderStep("KillCapCam") end)
RS:BindToRenderStep("KillCapCam", Enum.RenderPriority.Last.Value, function()
	if workspace.CurrentCamera ~= cam then workspace.CurrentCamera = cam end
	cam.FieldOfView = FOV; cam.CFrame = C.cam
end)
local function lamp(cf: CFrame, faceN: Enum.NormalId, bright: number, range: number)
	local p = Instance.new("Part"); p.Anchored = true; p.CanCollide = false; p.CanQuery = false; p.CanTouch = false
	p.Transparency = 1; p.Size = Vector3.new(90, 1, 1); p.CFrame = cf; p.Parent = fold
	local l = Instance.new("SurfaceLight"); l.Face = faceN; l.Brightness = bright; l.Range = range; l.Angle = 120; l.Shadows = false; l.Parent = p
end
lamp(CFrame.new(O + Vector3.new(0, 5, 14)), Enum.NormalId.Front, 2.2, 40)
lamp(CFrame.new(O + Vector3.new(0, 16, 3)), Enum.NormalId.Bottom, 1.2, 30)
RS.RenderStepped:Wait(); RS.RenderStepped:Wait()
local out = {}
local vp = cam.ViewportSize
for i = 1, N do
	local at = px(i) + Vector3.new(0, 3.5, 0)
	local p = cam:WorldToViewportPoint(at)
	local q = cam:WorldToViewportPoint(at + Vector3.new(0, CROP / 2, 0))
	table.insert(out, string.format("[%.1f,%.1f,%.1f]", p.X, p.Y, math.abs(p.Y - q.Y) * 2))
end
return string.format("vp %dx%d | rects [%s] | %s", vp.X, vp.Y, table.concat(out, ","), os.date("!%H:%M:%S"))
