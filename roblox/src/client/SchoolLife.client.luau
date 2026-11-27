--!strict
-- SchoolLife (20 Nov 2026): Jankfield High v2's ceiling lights flicker. The owner: "make it a little darker, maybe the
-- ceiling lights flicker you know more ambiance". The kit (tools/roblox/school_models.py --variant=v2A|v2B) puts each
-- flickering group's fittings (frosted shade + small neon core) in its own model, Shell.sc_flk<group>x, and the layout
-- tags those fittings' lights (Lights.Light, attribute FlickGroup = group; WebArena reads the layout's lightGroups).
-- Each group dies on its own timer. Writes happen only on a change, a handful of parts and lights at a time, never per
-- frame (roblox/docs/PERFORMANCE.md). Nothing runs unless the player's Arena is a v2 school; the nearest copy flickers:
-- the source (workspace.Map.<name>), a match copy (Map.ArenaCopies, CopyOf = name) or a zombies game's copy (a child of
-- workspace with the map's name, at (0, 600, 24000)).
-- (26 Nov 2026, the owner on zombies: "the ambiance isnt there yet, it should be darker, with fog, not all ceiling likes
-- should work so the ones that do give a better vibe") a flickering tube buzzes now (zm_flicker, a recording, from the
-- fitting), a few groups stay dead for good, and a thin mist hangs over the floor round you: one emitter box that
-- follows you at your feet (moved twice a second, not per frame), its puffs lit by the lamps they drift under
local Players = game:GetService("Players")
local okSfx, Sfx = pcall(require, script.Parent:WaitForChild("Sfx"))
local me = Players.LocalPlayer
local OFF_MAT = Enum.Material.SmoothPlastic
local NAMES = { JankfieldHighV2A = true, JankfieldHighV2B = true }
local NGROUPS = 24
local DEAD_GROUPS = { [3] = true, [9] = true, [15] = true, [20] = true } -- (gone for good: a dark fitting among the lit)

type Group = { parts: { BasePart }, cols: { Color3 }, mats: { Enum.Material }, lights: { Light }, at: Vector3?, held: boolean?,
	ats: { Vector3 }, fills: { Light }, fillBr: { number }, on: boolean?, lit: boolean?, lastL: number?, pend: boolean? }
local current: Model? = nil
local groups: { [number]: Group } = {}

local function arenaModel(): Model?
	local name = me:GetAttribute("Arena")
	if type(name) ~= "string" or not NAMES[name] then return nil end
	local cam = workspace.CurrentCamera
	local at = if cam then cam.CFrame.Position else Vector3.zero
	local best: Model?, bestD = nil, math.huge
	local function consider(m: Instance?)
		if not m or not m:IsA("Model") then return end
		local d = (m:GetPivot().Position - at).Magnitude
		if d < bestD then best, bestD = m, d end
	end
	local map = workspace:FindFirstChild("Map")
	if map then
		consider(map:FindFirstChild(name))
		local copies = map:FindFirstChild("ArenaCopies")
		if copies then
			for _, c in copies:GetChildren() do
				if c:GetAttribute("CopyOf") == name then consider(c) end
			end
		end
	end
	consider(workspace:FindFirstChild(name))
	return if best and bestD < 1500 then best else nil
end

local function collect(m: Model)
	local out: { [number]: Group } = {}
	local function g(n: number): Group
		local x = out[n]
		if not x then x = { parts = {}, cols = {}, mats = {}, lights = {}, ats = {}, fills = {}, fillBr = {} }; out[n] = x end
		return x
	end
	local shell = m:FindFirstChild("Shell")
	if shell then
		for _, c in shell:GetChildren() do
			local n = tonumber(string.match(c.Name, "^sc_flk(%d+)x$"))
			if n then
				for _, p in c:GetDescendants() do
					if p:IsA("BasePart") then
						local x = g(n)
						table.insert(x.parts, p); table.insert(x.cols, p.Color); table.insert(x.mats, p.Material)
					end
				end
			end
		end
	end
	local lights = m:FindFirstChild("Lights")
	if lights then
		for _, a in lights:GetChildren() do
			local n = a:GetAttribute("FlickGroup")
			if type(n) == "number" then
				for _, l in a:GetChildren() do
					if l:IsA("Light") then table.insert(g(n).lights, l) end
				end
				if a:IsA("BasePart") and not g(n).at then g(n).at = a.Position end
				if a:IsA("BasePart") then table.insert(g(n).ats, a.Position) end
			end
		end
		-- (27 Nov 2026) the fill light the layout puts beside a fitting (an untagged light within 6 studs of a group's
		-- light) dims with that tube, or the room stays lit while its tube is out
		for _, a in lights:GetChildren() do
			if a:GetAttribute("FlickGroup") ~= nil or not a:IsA("BasePart") then continue end
			local best: Group?, bd = nil, 6
			for _, x in out do
				for _, at in x.ats do
					local d = (at - a.Position).Magnitude
					if d < bd then best, bd = x, d end
				end
			end
			if best then
				for _, l in a:GetChildren() do
					if l:IsA("Light") then table.insert(best.fills, l); table.insert(best.fillBr, l.Brightness) end
				end
			end
		end
	end
	return out
end

-- where a group's sounds and sparks come from: its fitting nearest your camera (a group spans floors)
local function pos(x: Group): Vector3?
	local cam = workspace.CurrentCamera
	if not cam or #x.ats == 0 then return x.at end
	local e = cam.CFrame.Position
	local best, bd = x.at, math.huge
	for _, a in x.ats do
		local d = (a - e).Magnitude
		if d < bd then best, bd = a, d end
	end
	return best
end

local function buzz(x: Group)
	local at = pos(x)
	local cam = workspace.CurrentCamera
	if not at or not cam or not okSfx or (cam.CFrame.Position - at).Magnitude > 70 then return end
	pcall((Sfx :: any).play, "zm_flicker", at)
end
-- (27 Nov 2026, the owner: "Can lights flicker too? Some electrical certain sounds etc?") the sounds a tube makes,
-- all recorded (store.json): the ballast's tick as it catches (zm_ballast), a spark's crackle (zm_spark); positional,
-- only when you're near, a tick at most every 0.08 s a tube
local lastTick: { [Group]: number } = {}
local function near(x: Group, r: number): boolean
	local cam = workspace.CurrentCamera
	local at = pos(x)
	return at ~= nil and cam ~= nil and (cam.CFrame.Position - at).Magnitude < r
end
local function tick(x: Group)
	if not okSfx or not near(x, 45) then return end
	local t = os.clock()
	if t - (lastTick[x] or 0) < 0.08 then return end
	lastTick[x] = t
	pcall((Sfx :: any).play, "zm_ballast", pos(x))
end
-- a dying tube sparks: a burst of long hot streaks falling from the fitting (the VFX library's vfx_spark, no upload),
-- one flash, the crackle, then a few more spat a beat later (no second flash: seizure safety)
local SPARK = "rbxassetid://73042129135061"
local function spark(x: Group)
	local at = pos(x)
	if not at or not near(x, 70) then return end
	local p = Instance.new("Part")
	p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
	p.Transparency = 1; p.Size = Vector3.new(0.4, 0.4, 0.4)
	p.CFrame = CFrame.new(at - Vector3.new(0, 0.5, 0))
	local e = Instance.new("ParticleEmitter")
	e.Texture = SPARK
	e.Color = ColorSequence.new({ ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 250, 232)),
		ColorSequenceKeypoint.new(0.35, Color3.fromRGB(255, 208, 120)), ColorSequenceKeypoint.new(1, Color3.fromRGB(255, 128, 48)) })
	e.LightEmission = 1
	e.LightInfluence = 0
	e.Brightness = 6
	e.Orientation = Enum.ParticleOrientation.VelocityParallel
	e.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.34), NumberSequenceKeypoint.new(0.6, 0.2), NumberSequenceKeypoint.new(1, 0.06) })
	e.Squash = NumberSequence.new(1.6) -- (long thin streaks along the fall)
	e.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0), NumberSequenceKeypoint.new(0.75, 0.15), NumberSequenceKeypoint.new(1, 1) })
	e.Lifetime = NumberRange.new(0.35, 0.8)
	e.Speed = NumberRange.new(9, 18)
	e.SpreadAngle = Vector2.new(65, 65)
	e.EmissionDirection = Enum.NormalId.Bottom
	e.Acceleration = Vector3.new(0, -55, 0)
	e.Drag = 1.2
	e.Rate = 0
	e.Parent = p
	local l = Instance.new("PointLight")
	l.Color = Color3.fromRGB(255, 214, 160); l.Range = 16; l.Brightness = 5; l.Shadows = false
	l.Parent = p
	p.Parent = workspace
	e:Emit(math.random(24, 34))
	task.delay(0.06, function() l.Enabled = false end)
	task.delay(0.14 + math.random() * 0.16, function() if p.Parent then e:Emit(math.random(6, 12)) end end)
	task.delay(1.5, function() p:Destroy() end)
	if okSfx then pcall((Sfx :: any).play, "zm_spark", at) end
end

-- (27 Nov 2026, ZOMBIES: a dark area's tubes stay off till the power is on, like its lamps: a zombies game's copy has
-- Power = false till then; ZM.DARK names the areas)
local okZM, ZM = pcall(function() return require(game:GetService("ReplicatedStorage"):WaitForChild("Jankfire"):WaitForChild("ZM")) :: any end)
local darkFor: Model?, darkMap: any = nil, nil
local function unpowered(x: Group): boolean
	local m = current
	if not m or m:GetAttribute("Power") ~= false or not x.at or not okZM or type(ZM.DARK) ~= "table" then return false end
	if darkFor ~= m then
		darkFor = m
		local ok, r = pcall(ZM.read, m)
		darkMap = if ok then r else nil
	end
	if not darkMap then return false end
	local id = ZM.areaAt(darkMap, x.at :: Vector3)
	return id ~= nil and ZM.DARK[id] == true
end
-- the room's light (the group's lights and their fills) changes at most 3 times a second, whatever the tube does: only
-- the small fitting stutters fast; a room-wide flash never repeats faster than that (seizure safety, 27 Nov 2026)
local ROOM_GAP = 0.34
local function roomLight(x: Group)
	local on = x.on ~= false
	if x.lit == on then return end
	x.lit = on; x.lastL = os.clock()
	for _, l in x.lights do l.Enabled = on end
	for i, l in x.fills do l.Brightness = if on then x.fillBr[i] else x.fillBr[i] * 0.12 end
end
local function setOn(x: Group, on: boolean)
	x.on = on
	for i, p in x.parts do
		local mat = x.mats[i]
		if mat == Enum.Material.Neon then
			p.Material = if on then mat else OFF_MAT
			p.Color = if on then x.cols[i] else x.cols[i]:Lerp(Color3.new(0, 0, 0), 0.55)
		end
	end
	local due = (x.lastL or 0) + ROOM_GAP - os.clock()
	if due <= 0 then roomLight(x)
	elseif not x.pend then
		x.pend = true
		task.delay(due, function() x.pend = false; roomLight(x) end)
	end
end

-- one watcher: which school (if any) is ours, and its groups (read once per model, while everything's lit)
task.spawn(function()
	while true do
		local m = arenaModel()
		if m ~= current then
			for _, x in groups do setOn(x, true) end
			current = m
			groups = if m then collect(m) else {}
			for n, x in groups do if DEAD_GROUPS[n] then setOn(x, false) end end
		end
		for n, x in groups do -- (a dark area's tubes off at once when its game starts; with the power they stutter to life)
			if DEAD_GROUPS[n] then continue end
			if not x.held and unpowered(x) then x.held = true; setOn(x, false)
			elseif x.held and not unpowered(x) then
				x.held = false
				;(x :: any).wake = os.clock() + math.random() * 1.5 -- (the restart below picks it up)
			end
		end
		task.wait(2)
	end
end)

-- the mist: faint puffs low over the floor in a box round you (lit by whatever lamp they're under: LightInfluence 1)
do
	local box = Instance.new("Part")
	box.Name = "SchoolMist"
	box.Anchored, box.CanCollide, box.CanQuery, box.CanTouch, box.CastShadow = true, false, false, false, false
	box.Transparency = 1
	box.Size = Vector3.new(76, 1.6, 76)
	local pe = Instance.new("ParticleEmitter")
	pe.Shape = Enum.ParticleEmitterShape.Box
	pe.ShapeInOut = Enum.ParticleEmitterShapeInOut.Outward
	pe.ShapeStyle = Enum.ParticleEmitterShapeStyle.Volume
	pe.Texture = "rbxasset://textures/particles/smoke_main.dds"
	pe.Color = ColorSequence.new(Color3.fromRGB(150, 160, 178))
	pe.LightEmission = 0
	pe.LightInfluence = 1
	pe.Size = NumberSequence.new({ NumberSequenceKeypoint.new(0, 7), NumberSequenceKeypoint.new(1, 13) })
	pe.Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.3, 0.86),
		NumberSequenceKeypoint.new(0.7, 0.88), NumberSequenceKeypoint.new(1, 1) })
	pe.Lifetime = NumberRange.new(7, 11)
	pe.Rate = 9
	pe.Speed = NumberRange.new(0.2, 0.7)
	pe.SpreadAngle = Vector2.new(180, 8)
	pe.Rotation = NumberRange.new(0, 360)
	pe.RotSpeed = NumberRange.new(-6, 6)
	pe.Acceleration = Vector3.new(0, 0.05, 0)
	pe.LockedToPart = false
	pe.Enabled = false
	pe.Parent = box
	task.spawn(function()
		while true do
			local ch = me.Character
			local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
			local on = current ~= nil and root ~= nil and current:IsDescendantOf(workspace)
			if on and root then
				if box.Parent ~= workspace then box.Parent = workspace end
				box.CFrame = CFrame.new(root.Position - Vector3.new(0, 2.3, 0)) -- (the puffs start a knee deep: their middles over the floor)
			end
			if pe.Enabled ~= on then pe.Enabled = on; if not on then pe:Clear() end end
			task.wait(0.5)
		end
	end)
end

-- (27 Nov 2026, the owner: "Can lights flicker too?") a tube's ways of failing, as fluorescents do: a few blinks; a
-- struggling restart (dark, then tries that catch and drop, then it holds); a dying stutter into a dark spell, now
-- and then with a spark; a long dropout then a pop back. Each tube on its own clock, never in step; every change is
-- irregular and short (no steady fast strobe: no stutter longer than about a second), the light and the fitting's
-- glow together. A tick from the ballast each time it catches
local function blinks(x: Group)
	for _ = 1, math.random(1, 3) do
		setOn(x, false); task.wait(0.05 + math.random() * 0.16)
		setOn(x, true); tick(x); task.wait(0.06 + math.random() * 0.14)
	end
end
local function restart(x: Group)
	setOn(x, false); task.wait(0.3 + math.random() * 0.5)
	for _ = 1, math.random(2, 4) do
		setOn(x, true); tick(x); task.wait(0.05 + math.random() * 0.12)
		setOn(x, false); task.wait(0.15 + math.random() * 0.35)
	end
	setOn(x, true); tick(x)
end
local function dying(x: Group)
	local t0 = os.clock()
	while os.clock() - t0 < 0.9 do
		setOn(x, false); task.wait(0.05 + math.random() * 0.12)
		setOn(x, true); tick(x); task.wait(0.05 + math.random() * 0.15)
	end
	if math.random() < 0.35 then spark(x) end
	setOn(x, false); task.wait(0.8 + math.random() * 1.8)
	restart(x)
end
local function dropout(x: Group)
	setOn(x, false); task.wait(1.4 + math.random() * 2.6)
	setOn(x, true); tick(x)
end
for n = 1, NGROUPS do
	task.spawn(function()
		task.wait(math.random() * 6)
		while true do
			task.wait(3 + math.random() * 9)
			local x = groups[n]
			if not x or current == nil or DEAD_GROUPS[n] or x.held then continue end
			if unpowered(x) then continue end
			buzz(x)
			local r = math.random()
			if r < 0.45 then blinks(x)
			elseif r < 0.65 then restart(x)
			elseif r < 0.85 then dying(x)
			else dropout(x) end
		end
	end)
end

-- the hum: the two nearest lit tubes buzz, quietly (a looped recording, zm_tubehum, moved to them once a second; silent
-- while that tube is out)
do
	local hums: { { p: BasePart, s: Sound?, x: Group? } } = {}
	local lib = game:GetService("ReplicatedStorage"):FindFirstChild("JankfireSounds")
	for i = 1, 2 do
		local p = Instance.new("Part")
		p.Name = "TubeHum" .. i
		p.Anchored, p.CanCollide, p.CanQuery, p.CanTouch, p.CastShadow = true, false, false, false, false
		p.Transparency = 1; p.Size = Vector3.new(0.2, 0.2, 0.2)
		local src = lib and lib:FindFirstChild("zm_tubehum")
		local s = if src and src:IsA("Sound") then src:Clone() else nil
		if s then
			s.Looped = true
			s.RollOffMode = Enum.RollOffMode.InverseTapered
			s.RollOffMinDistance = tonumber(s:GetAttribute("RollMin")) or 4
			s.RollOffMaxDistance = tonumber(s:GetAttribute("RollMax")) or 24
			s:SetAttribute("Full", s.Volume)
			s.Parent = p
		end
		table.insert(hums, { p = p, s = s, x = nil })
	end
	task.spawn(function()
		while true do
			task.wait(1)
			local cam = workspace.CurrentCamera
			if not current or not cam then
				for _, h in hums do if h.s and h.s.Playing then h.s:Stop() end; h.p.Parent = nil end
				continue
			end
			local eye = cam.CFrame.Position
			local list = {}
			for n, x in groups do
				local at = pos(x)
				if not DEAD_GROUPS[n] and not x.held and at and (at - eye).Magnitude < 30 then table.insert(list, x) end
			end
			table.sort(list, function(a, b) return ((pos(a) :: Vector3) - eye).Magnitude < ((pos(b) :: Vector3) - eye).Magnitude end)
			for i, h in hums do
				local x = list[i]
				h.x = x
				if x and h.s then
					h.p.CFrame = CFrame.new(pos(x) :: Vector3)
					if h.p.Parent ~= workspace then h.p.Parent = workspace end
					local lit = x.on ~= false
					h.s.Volume = if lit then (tonumber(h.s:GetAttribute("Full")) or 0.1) else 0
					if not h.s.Playing then h.s:Play() end
				elseif h.s and h.s.Playing then
					h.s:Stop()
				end
			end
		end
	end)
end

-- the power's back: each dark tube stutters to life on its own beat (the watcher above sets wake)
task.spawn(function()
	while true do
		task.wait(0.2)
		for _, x in groups do
			local w = (x :: any).wake
			if w and os.clock() >= w then
				(x :: any).wake = nil
				task.spawn(function() buzz(x); restart(x) end)
			end
		end
	end
end)

-- far off in the building, now and then: an arc or a relay's clunk (positional, from a tube 30-90 studs away)
task.spawn(function()
	while true do
		task.wait(18 + math.random() * 24)
		local cam = workspace.CurrentCamera
		if not current or not cam or not okSfx then continue end
		local far = {}
		for _, x in groups do
			local at = pos(x)
			local d = if at then (at - cam.CFrame.Position).Magnitude else 0
			if d > 30 and d < 90 then table.insert(far, x) end
		end
		local x = far[math.random(1, math.max(1, #far))]
		local at = if x then pos(x) else nil
		if at then pcall((Sfx :: any).play, if math.random() < 0.5 then "zm_arc" else "zm_relay", at) end
	end
end)

-- (Studio test: the player attribute ZmFlickTest = "spark" | "restart" | "dying": the nearest lit tube does it now)
me:GetAttributeChangedSignal("ZmFlickTest"):Connect(function()
	local k = me:GetAttribute("ZmFlickTest")
	if type(k) ~= "string" then return end
	me:SetAttribute("ZmFlickTest", nil)
	local cam = workspace.CurrentCamera
	if not cam then return end
	local best: Group?, bd = nil, math.huge
	for n, x in groups do
		local at = pos(x)
		if not DEAD_GROUPS[n] and not x.held and at then
			local d = (at - cam.CFrame.Position).Magnitude
			if d < bd then best, bd = x, d end
		end
	end
	local x = best
	if not x then return end
	task.spawn(function()
		if k == "spark" then
			buzz(x); spark(x); setOn(x, false); task.wait(1.2); restart(x)
		elseif k == "restart" then
			restart(x)
		else
			dying(x)
		end
	end)
end)
