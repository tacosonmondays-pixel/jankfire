-- PACK CATALOGUE RIG (Client, in Play; the VFX session, 20 Nov 2026). Photographs a pack's effects as a grid (4 x 3 by
-- default), every effect frozen at the same age, each scaled to fit its cell, so a pack of ~100 numbered "VFXTemplate"s
-- can be browsed and picked from. Templates are read from ReplicatedStorage.<folder> (built client-side by
-- pack_templates.py --root=ReplicatedStorage.<folder>, so nothing is added to the place).
--   require(rig)({ cat, D, folder, names = {...}, cols = 4, rows = 3, age = 0.3, bg = "grey", live = false }) -> report
-- live = true for auras and trails (emitters that run instead of bursting): they run for `age` seconds, then freeze.
-- The report gives each effect's fit scale (1 / scale ~ how big it is as the pack made it: a scale of 0.5 means about
-- twice the cell, i.e. about 0.4 D across).
return function(SPEC: any): string
	local me = game.Players.LocalPlayer
	local RS = game:GetService("RunService")
	local TS = game:GetService("TweenService")
	local cam = workspace.CurrentCamera
	local base = me:GetAttribute("PracBase")
	if typeof(base) ~= "CFrame" then
		local hrp = me.Character and me.Character:FindFirstChild("HumanoidRootPart") :: BasePart?
		base = CFrame.new((if hrp then hrp.Position else Vector3.zero) + Vector3.new(0, 900, 0))
		me:SetAttribute("PracBase", base)
	end
	local B = base :: CFrame
	local D = SPEC.D or 40
	local COLS, ROWS = SPEC.cols or 4, SPEC.rows or 3
	local AGE = SPEC.age or 0.3
	local stage = workspace:FindFirstChild("PracStage") or Instance.new("Folder")
	stage.Name = "PracStage"; stage.Parent = workspace
	stage:ClearAllChildren()
	local wall = Instance.new("Part"); wall.Name = "Wall"; wall.Anchored = true; wall.CanCollide = false
	wall.Size = Vector3.new(D * 6, D * 4, 1)
	if (SPEC.bg or "grey") == "grey" then wall.Color = Color3.fromRGB(92, 92, 92); wall.Material = Enum.Material.Neon
	else wall.Color = Color3.fromRGB(18, 19, 23); wall.Material = Enum.Material.SmoothPlastic end
	wall.CFrame = B * CFrame.new(0, 0, -D * 1.9); wall.Parent = stage
	pcall(function() RS:UnbindFromRenderStep("PracCam") end)
	RS:BindToRenderStep("PracCam", Enum.RenderPriority.Last.Value + 90, function() cam.CFrame = B; cam.FieldOfView = 70 end)
	for _, g in me.PlayerGui:GetChildren() do if g:IsA("ScreenGui") then g.Enabled = false end end
	local folder = game.ReplicatedStorage:FindFirstChild(SPEC.folder or "Pack100RT")
	-- the grid: W = 2.7 D wide (the photo shows 2.88 D), rows 0.44 D apart (the photo shows 1.4 D)
	local W, RY = 2.7 * D, 0.44 * D
	local cellR = math.min(W / COLS, RY) * 0.5 * 0.92
	-- how far an emitter's particles reach (studs): travel (with drag) + gravity + half the biggest size + the part's reach
	local function reach(d: ParticleEmitter, partR: number): number
		local mx = 0
		for _, kp in d.Size.Keypoints do mx = math.max(mx, kp.Value + kp.Envelope) end
		local life = d.Lifetime.Max
		local spd = d.Speed.Max
		local tr = if d.Drag > 0.05 then spd / d.Drag * (1 - math.exp(-d.Drag * life)) else spd * life
		local g = math.min(0.5 * d.Acceleration.Magnitude * life * life, 40)
		return math.min(tr + g, 120) + mx * 0.5 + partR
	end
	local all, report, missing = {}, {}, {}
	local frozen = false
	local T = AGE + 0.03
	local t0 = os.clock()
	for i, name in SPEC.names do
		local t = folder and folder:FindFirstChild(name)
		if not t then table.insert(missing, name); continue end
		local c = (t :: Instance):Clone()
		local col, row = (i - 1) % COLS, (i - 1) // COLS
		local x = (col - (COLS - 1) / 2) * (W / COLS)
		local y = ((ROWS - 1) / 2 - row) * RY
		local pos = (B * CFrame.new(x, y, -D)).Position
		local cf = CFrame.lookAt(pos, B.Position)
		local partR = if c:IsA("BasePart") then c.Size.Magnitude * 0.5 else 0
		local ext = 0.5
		for _, d in c:GetDescendants() do
			if d:IsA("ParticleEmitter") then
				local pr = if d.Parent and d.Parent:IsA("BasePart") then partR else 0
				ext = math.max(ext, reach(d, pr))
			end
		end
		local sc = math.clamp(cellR / ext, 0.03, 4)
		table.insert(report, ("%s=%.2f"):format(name, sc))
		c.Parent = stage
		if c:IsA("BasePart") then
			c.Size = c.Size * sc
			c.CFrame = cf; c.Transparency = 1; c.Anchored = true; c.CanCollide = false
		elseif c:IsA("Model") then c:PivotTo(cf) end
		for _, d in c:GetDescendants() do
			if d:IsA("Attachment") then
				d.Position = d.Position * sc
			elseif d:IsA("BasePart") then
				d.Size = d.Size * sc; d.Transparency = 1; d.Anchored = true; d.CanCollide = false
			end
		end
		for _, d in c:GetDescendants() do
			if d:IsA("ParticleEmitter") then
				d.Enabled = false; d:Clear()
				local q = {}
				for _, kp in d.Size.Keypoints do table.insert(q, NumberSequenceKeypoint.new(kp.Time, kp.Value * sc, kp.Envelope * sc)) end
				d.Size = NumberSequence.new(q)
				d.Speed = NumberRange.new(d.Speed.Min * sc, d.Speed.Max * sc)
				d.Acceleration = d.Acceleration * sc
				table.insert(all, d)
				local delay = d:GetAttribute("EmitDelay") or 0
				local dur = d:GetAttribute("EmitDuration") or 0
				local cnt = d:GetAttribute("EmitCount") or 1
				if cnt == 0 then cnt = 12 end
				local ts0 = d:GetAttribute("TimeScale_Start")
				local tsd = d:GetAttribute("TimeScale_Duration") or 0
				task.delay(T - AGE + delay, function()
					if frozen then return end
					if SPEC.live then d.Enabled = true; return end -- (an aura or trail: it runs until the freeze)
					if tsd > 0 and type(ts0) == "number" and ts0 ~= (d:GetAttribute("TimeScale_End") or 1) then
						d.TimeScale = ts0
						TS:Create(d, TweenInfo.new(tsd, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), { TimeScale = d:GetAttribute("TimeScale_End") or 1 }):Play()
					end
					if dur > 0 then d.Enabled = true; task.delay(dur, function() d.Enabled = false end) else d:Emit(cnt) end
				end)
			elseif d:IsA("Beam") or d:IsA("Trail") then
				(d :: any).Enabled = false
				task.delay(T - AGE, function() (d :: any).Enabled = true end)
			end
		end
	end
	task.wait(T - (os.clock() - t0))
	frozen = true
	for _, d in all do d.TimeScale = 0; d.Enabled = false end
	task.wait()
	for _, d in all do d.TimeScale = 0 end
	return ("%s age %.2f: froze %d emitters; scales %s; missing %s"):format(SPEC.cat or "?", AGE, #all, table.concat(report, " "), table.concat(missing, ","))
end
