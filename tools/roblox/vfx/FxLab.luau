--!nonstrict
-- The VFX pipeline's Studio side (roblox/docs/VFX-PIPELINE.md, step 3). A ModuleScript for the CLIENT of a Play test,
-- required from execute_luau. It fires one effect from a fresh copy of an effects module (the new Fx, or FxOld: the
-- previous one made freezable) and stops the effect clock at a set time after it (the workspace attribute
-- FxTimeScale = 0), so screen_capture photographs exactly that moment. It also runs the cost guard.
--
--   local L = require(<this module's clone>)
--   L.load("new", <Fx ModuleScript>); L.load("old", <FxOld ModuleScript>)
--   L.cam(cf) / L.cam(nil)         hold the camera at cf (fov 70), or give it back to the game (first person)
--   L.look(dir)                     point the game's own first-person camera (eye shots: the viewmodel only draws
--                                   with the game's camera; a held Scriptable camera hides it)
--   L.frame("new", "shot", { w = "ar", from = .., to = .. }, 0.03, 0.1)   -> the effect time it froze at
--   L.cost("new", "smg", 5)       -> the cost guard's numbers
local L = {}
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local RS = game:GetService("ReplicatedStorage")
local me = Players.LocalPlayer
local S = 3
local W = require(RS:WaitForChild("Jankfire"):WaitForChild("Weapons")).list
local TRACER = Color3.fromRGB(255, 240, 160)

L.fx = {}
function L.load(name: string, module: ModuleScript)
	local J = me:WaitForChild("PlayerScripts"):WaitForChild("Jankfire")
	local old = J:FindFirstChild("FxLab_" .. name)
	if old then old:Destroy() end
	local m = module:Clone()
	m.Name = "FxLab_" .. name
	m.Parent = J
	L.fx[name] = require(m)
	return L.fx[name]
end

-- the camera: held at a CFrame (Scriptable, fov 70) or the game's own (nil)
local shotCF: CFrame? = nil
local camWas: Enum.CameraType? = nil
RunService:BindToRenderStep("FxLabCam", Enum.RenderPriority.Camera.Value + 2, function()
	local cam = workspace.CurrentCamera
	if shotCF then cam.CameraType = Enum.CameraType.Scriptable; cam.FieldOfView = 70; cam.CFrame = shotCF end
end)
function L.cam(cf: CFrame?)
	local cam = workspace.CurrentCamera
	if cf and not shotCF then camWas = cam.CameraType end
	shotCF = cf
	if not cf and camWas then cam.CameraType = camWas end
end
function L.look(dir: Vector3)
	L.cam(nil)
	local cam = workspace.CurrentCamera
	cam.CameraType = Enum.CameraType.Custom
	local p = cam.CFrame.Position
	cam.CFrame = CFrame.lookAt(p, p + dir)
end
function L.stop()
	RunService:UnbindFromRenderStep("FxLabCam")
	workspace:SetAttribute("FxTimeScale", nil)
	for _, f in L.fx do pcall(f.clear) end
end

-- where the viewmodel's muzzle is (first person) and the held gun's (third person: the lab looks for a Muzzle attachment
-- in the character's gun)
function L.vmMuzzle(): Vector3?
	for _, m in workspace.CurrentCamera:GetChildren() do
		if m:IsA("Model") and m.PrimaryPart then
			local a = m.PrimaryPart:FindFirstChild("Muzzle")
			if a and a:IsA("Attachment") then return a.WorldPosition end
		end
	end
	return nil
end
function L.tpMuzzle(): Vector3?
	local ch = me.Character
	if not ch then return nil end
	local best: Attachment? = nil
	for _, d in ch:GetDescendants() do
		if d:IsA("Attachment") and d.Name == "Muzzle" then
			local m = d:FindFirstAncestorOfClass("Model")
			local hid = m and m.Name == "HeldWeapon" and m:FindFirstChildWhichIsA("BasePart", true)
			if not (hid and (hid :: BasePart).LocalTransparencyModifier >= 1) then best = d end
		end
	end
	return best and best.WorldPosition
end

local mapRp = RaycastParams.new()
mapRp.FilterType = Enum.RaycastFilterType.Include
local function cast(o: Vector3, d: Vector3): RaycastResult?
	mapRp.FilterDescendantsInstances = { workspace:FindFirstChild("Map") }
	return workspace:Raycast(o, d, mapRp)
end
L.cast = cast

-- one effect. o: w (weapon id), from (muzzle), to (aim point), fpv, at (a point), n (a normal), r (radius)
local cloudN = 0
function L.fire(which: string, kind: string, o: any)
	local F = L.fx[which]
	if kind == "shot" then
		local w = W[o.w]
		local fx = w.fx or {}
		local from: Vector3 = o.from
		local dir = (o.to - from).Unit
		local ends, hits = {}, {}
		local n = if fx.spray then 1 else math.min(w.pellets or 1, 12)
		for i = 1, n do
			local d = if n > 1 then (dir + Vector3.new(math.random() - 0.5, math.random() - 0.5, math.random() - 0.5) * (w.spread or 0) * 1.6).Unit else dir
			local h = cast(from, d * 600)
			table.insert(ends, if h then h.Position else from + d * 600)
			if h and #hits < 6 then table.insert(hits, h) end
		end
		if which == "new" then
			F.gunShot(w, CFrame.lookAt(from, from + dir), if fx.spray then {} else ends, nil, o.fpv == true)
		else
			F.muzzle(CFrame.lookAt(from, from + dir), fx.big == true, o.fpv == true)
			if not fx.spray then for _, e in ends do F.tracer(from, e, w.tracer or TRACER, w.thick or 0.045 * S, 0.2) end end
		end
		if fx.spray then F.marbles(from, ends, 12) end
		if o.impact ~= false then
			for _, h in hits do
				F.impact(h.Position, h.Normal, h.Instance, h.Material, if fx.hole == false then { hole = false, scale = fx.scale or 1 } else nil)
			end
		end
	elseif kind == "impact" then
		local hit = cast(o.from, (o.to - o.from).Unit * 300)
		if hit then F.impact(hit.Position, hit.Normal, hit.Instance, hit.Material, o.opt) end
	elseif kind == "sparks" then
		F.sparks(o.at, o.dir or Vector3.new(0, 0, -1), o.n or 26, o.pop or 0.15)
	elseif kind == "explosion" then
		if which == "new" then F.explosion(o.at, o.r or 7.5 * S) else F.boom(o.at, o.r or 7.5 * S) end
	elseif kind == "smoke" then
		cloudN += 1
		if which == "new" then F.smokeCloud("lab" .. cloudN, o.at, o.r or 6.5 * S, o.left or 10) else F.cloud(o.at, o.r or 6.5 * S) end
	end
end

-- clear, fire, run the effect clock (slow = its speed: 0.1 = slow motion, for the short effects) until it has run t
-- seconds, then freeze. returns the effect time it stopped at
function L.frame(which: string, kind: string, o: any, t: number, slow: number?)
	local k = slow or 1
	workspace:SetAttribute("FxTimeScale", 1)
	for _, f in L.fx do pcall(f.clear) end
	RunService.RenderStepped:Wait()
	workspace:SetAttribute("FxTimeScale", k)
	L.fire(which, kind, o)
	local el = 0
	while el < t - 1e-4 do
		local dt = RunService.RenderStepped:Wait()
		el += dt * k
	end
	workspace:SetAttribute("FxTimeScale", 0)
	return el
end
function L.thaw()
	workspace:SetAttribute("FxTimeScale", 1)
	for _, f in L.fx do pcall(f.clear) end
end

-- the cost guard: secs of a gun firing at its rate (flash, tracer, impact on the wall it aims at, like a real shot),
-- against the same time doing nothing. reports frames and frame times, and what the effects asked for
local function pct(a: { number }, p: number): number
	if #a == 0 then return 0 end
	table.sort(a)
	return a[math.clamp(math.ceil(#a * p), 1, #a)]
end
local function window(secs: number, each: ((number) -> ())?)
	local dts, t = {}, 0
	local statsOk, Stats = pcall(function() return game:GetService("Stats") end)
	local cpu = {}
	while t < secs do
		local dt = RunService.RenderStepped:Wait()
		t += dt
		table.insert(dts, dt * 1000)
		if statsOk then
			local ok, v = pcall(function() return (Stats :: any).RenderCPUFrameTime end)
			if ok and type(v) == "number" then table.insert(cpu, v) end
		end
		if each then each(t) end
	end
	local sum = 0
	for _, d in dts do sum += d end
	return { frames = #dts, avgMs = math.floor(sum / #dts * 100) / 100, p95Ms = math.floor(pct(dts, 0.95) * 100) / 100,
		maxMs = math.floor(pct(dts, 1) * 100) / 100, cpuMs = if #cpu > 0 then math.floor(pct(cpu, 0.5) * 100) / 100 else nil }
end
function L.cost(which: string, wid: string, secs: number, from: Vector3, to: Vector3)
	local F = L.fx[which]
	local w = W[wid]
	local rate = (w.rate or 10)
	local base = window(secs)
	local st = F.stats
	local s0 = if st then table.clone(st) else nil
	local shots, nextT = 0, 0
	local load = window(secs, function(t)
		while t >= nextT do
			nextT += 1 / rate
			shots += 1
			local spread = Vector3.new(math.random() - 0.5, math.random() - 0.5, 0) * 2
			L.fire(which, "shot", { w = wid, from = from, to = to + spread, fpv = true })
		end
	end)
	local per = nil
	if st and s0 then
		per = { emits = (st.emits - s0.emits) / shots, particles = (st.particles - s0.particles) / shots,
			beams = (st.beams - s0.beams) / shots, lights = (st.lights - s0.lights) / shots, stepUs = math.floor(st.stepUs) }
	end
	local live = { emitters = 0, beams = 0, lights = 0 }
	for _, d in workspace:GetDescendants() do
		if d:IsA("ParticleEmitter") then live.emitters += 1 elseif d:IsA("Beam") then live.beams += 1
		elseif d:IsA("PointLight") then live.lights += 1 end
	end
	return { weapon = wid, rate = rate, shots = shots, idle = base, firing = load, perShot = per, inWorkspace = live }
end

return L
