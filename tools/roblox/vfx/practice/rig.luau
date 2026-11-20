-- PRACTICE RIG (Client, in Play). Rows of copies of an effect, each fired so that at the freeze it is AGES[k] seconds old;
-- frozen together (TimeScale 0), so one photo shows the effect's life left to right. Row 1 = the pack, row 2 = ours.
-- GROUND = the effect lies on a floor (tilted 35 degrees toward the camera, as if seen from above at 35).
-- templates are looked up in ReplicatedStorage.JankfireVfx and ReplicatedStorage.VfxPracticeRT (the server's copy of
-- ServerStorage.VfxPractice)
return function(SPEC: any): string
	local AGES = SPEC.ages or { 0.05, 0.1, 0.2, 0.35, 0.6, 1.0 }
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
	local D = SPEC.D
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
	local function find(n: string): Instance?
		local a = game.ReplicatedStorage:FindFirstChild("JankfireVfx")
		local b = game.ReplicatedStorage:FindFirstChild("VfxPracticeRT")
		return (a and a:FindFirstChild(n)) or (b and b:FindFirstChild(n))
	end
	local W, H = 2.49 * D, 1.4 * D
	local nA = #AGES
	local T = 0
	for _, a in AGES do T = math.max(T, a) end
	T += 0.03
	local all, missing = {}, {}
	local frozen = false
	local t0 = os.clock()
	for r, row in SPEC.rows do
		local y = if #SPEC.rows == 1 then 0 else (if r == 1 then H * 0.22 else -H * 0.24)
		for k, age in AGES do
			local x = (k - (nA + 1) / 2) * (W / nA)
			local pos = (B * CFrame.new(x, y + (row.dy or 0), -D)).Position
			local cf = CFrame.lookAt(pos, B.Position)
			if SPEC.ground then cf = CFrame.new(pos) * CFrame.Angles(math.rad(35) + math.atan((y + (row.dy or 0)) / D), 0, 0) end -- (each row's floor seen from 35 degrees: a row above the camera's axis is seen from lower down, so it tilts more)
			if row.spin then cf = cf * CFrame.Angles(0, 0, math.rad(row.spin)) end
			for _, name in row.names do
				local t = find(name)
				if not t then missing[name] = true; continue end
				local c = t:Clone()
				c.Parent = stage
				if c:IsA("BasePart") then c.CFrame = cf; c.Transparency = 1; c.Anchored = true; c.CanCollide = false
				elseif c:IsA("Model") then c:PivotTo(cf) end
				local sc = row.scale or 1
				for _, d in c:GetDescendants() do
					if d:IsA("ParticleEmitter") then
						d.Enabled = false; d:Clear()
						if sc ~= 1 then
							local q = {}
							for _, kp in d.Size.Keypoints do table.insert(q, NumberSequenceKeypoint.new(kp.Time, kp.Value * sc, kp.Envelope * sc)) end
							d.Size = NumberSequence.new(q)
							d.Speed = NumberRange.new(d.Speed.Min * sc, d.Speed.Max * sc)
							d.Acceleration = d.Acceleration * sc
						end
						table.insert(all, d)
						local fireAt = T - age
						local delay = d:GetAttribute("EmitDelay") or 0
						local dur = d:GetAttribute("EmitDuration") or 0
						local cnt = d:GetAttribute("EmitCount") or 1
						if cnt == 0 then cnt = 12 end
						local ts0 = d:GetAttribute("TimeScale_Start")
						local tsd = d:GetAttribute("TimeScale_Duration") or 0
						task.delay(fireAt + delay, function()
							if frozen then return end
							if tsd > 0 and type(ts0) == "number" and ts0 ~= (d:GetAttribute("TimeScale_End") or 1) then
								d.TimeScale = ts0
								TS:Create(d, TweenInfo.new(tsd, Enum.EasingStyle.Sine, Enum.EasingDirection.Out), { TimeScale = d:GetAttribute("TimeScale_End") or 1 }):Play()
							end
							if dur > 0 then d.Enabled = true; task.delay(dur, function() d.Enabled = false end) else d:Emit(cnt) end
						end)
					elseif d:IsA("Beam") or d:IsA("Trail") then
						(d :: any).Enabled = false
						task.delay(T - age, function() (d :: any).Enabled = true end)
					end
				end
			end
		end
	end
	task.wait(T - (os.clock() - t0))
	frozen = true
	for _, d in all do d.TimeScale = 0; d.Enabled = false end
	task.wait()
	for _, d in all do d.TimeScale = 0 end
	local m = {}
	for n in missing do table.insert(m, n) end
	return ("%s: froze %d emitters at T=%.2f; missing: %s"):format(SPEC.cat, #all, T, table.concat(m, ","))
end
