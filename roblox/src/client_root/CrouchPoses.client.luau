-- crouch and slide poses on R15 bodies, for everyone: bent knees, hips down and back, a forward lean for a crouch (C);
-- leaning back with one leg out and an arm out for balance for a slide. layered on top of whatever animation is
-- playing (crouch-walking bends the run), eased in and out. standing still in a crouch the legs and hips take the
-- crouch pose outright (not on top of the idle) so both feet stay planted. your own pose comes from your keys and
-- Move's slide; everyone else's from the "Pose" the server puts on their character.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local remote = game:GetService("ReplicatedStorage"):WaitForChild("PoseRemote")

local lp = Players.LocalPlayer
local rad = math.rad
local A = CFrame.Angles
local ID = CFrame.identity

local function len(part, a, b)
	local x, y = part and part:FindFirstChild(a), part and part:FindFirstChild(b)
	return if x and y then (x.Position - y.Position).Magnitude else 1
end

-- the joints that carry you: held exactly in the crouch pose when you crouch standing still
local LEGS = { Root = true, LeftHip = true, RightHip = true, LeftKnee = true, RightKnee = true, LeftAnkle = true, RightAnkle = true }

-- the joint bends for one body (leg lengths decide how far the hips drop so the feet stay on the floor)
local function posesFor(ch)
	local l1 = len(ch:FindFirstChild("RightUpperLeg"), "RightHipRigAttachment", "RightKneeRigAttachment")
	local l2 = len(ch:FindFirstChild("RightLowerLeg"), "RightKneeRigAttachment", "RightAnkleRigAttachment")
	local t, k = rad(80), rad(-115)
	local drop = (l1 + l2) - (l1 * math.cos(t) + l2 * math.cos(t + k))
	local fwd = l1 * math.sin(t) + l2 * math.sin(t + k) -- how far in front of the hips the feet would end up
	return {
		crouch = {
			Root = CFrame.new(0, -drop, fwd * 0.8),
			Waist = A(rad(-22), 0, 0),
			Neck = A(rad(18), 0, 0),
			LeftHip = A(t, 0, rad(-6)), RightHip = A(t, 0, rad(6)),
			LeftKnee = A(k, 0, 0), RightKnee = A(k, 0, 0),
			LeftAnkle = A(-(t + k), 0, 0), RightAnkle = A(-(t + k), 0, 0),
		},
		slide = {
			Root = CFrame.new(0, -0.6, 0) * A(rad(28), 0, 0),
			Waist = A(rad(8), 0, 0),
			Neck = A(rad(-30), 0, 0),
			RightHip = A(rad(50), 0, 0), RightKnee = A(rad(-8), 0, 0), RightAnkle = A(rad(-20), 0, 0),
			LeftHip = A(rad(20), 0, rad(-10)), LeftKnee = A(rad(-100), 0, 0), LeftAnkle = A(rad(40), 0, 0),
			LeftShoulder = A(0, 0, rad(-70)),
		},
	}
end

-- every body's joints (old Motor6Ds or the new avatar AnimationConstraints). the avatar's joints get rebuilt a moment
-- after a spawn (scaling, the new joints), so the list is collected again whenever joints come or go
local bodies = {} -- [character] = { poses, motors = {name = joint}, w = {crouch, slide}, written = {}, dirty }
local function isJoint(d) return d:IsA("Motor6D") or d:IsA("AnimationConstraint") end
local function collect(ch, b)
	b.motors = {}
	for _, m in ipairs(ch:GetDescendants()) do
		-- (not a held weapon's or a tool's own joints)
		if isJoint(m) and not m:FindFirstAncestorOfClass("Tool") and not m:FindFirstAncestor("HeldWeapon") then b.motors[m.Name] = m end
	end
	b.poses = posesFor(ch)
	b.written = {}
	b.dirty = false
end
local function bodyOf(ch)
	local b = bodies[ch]
	if not b then
		if not ch:FindFirstChild("RightUpperLeg") then return nil end -- R15 only
		b = { w = { crouch = 0, slide = 0 }, dirty = true }
		bodies[ch] = b
		local function mark(d) if isJoint(d) then b.dirty = true end end
		ch.DescendantAdded:Connect(mark)
		ch.DescendantRemoving:Connect(mark)
		task.delay(1.5, function() b.dirty = true end) -- the scaled leg lengths, once the avatar has settled
		ch.AncestryChanged:Connect(function() if not ch.Parent then bodies[ch] = nil end end)
	end
	if b.dirty then collect(ch, b) end
	return b
end

-- our own pose: Move lowers HipHeight while sliding; C / left ctrl is a crouch
local hipBase, sent = nil, "stand"
local function myPose(ch, hum)
	if hum.PlatformStand or hum.Health <= 0 then return "stand" end
	hipBase = math.max(hipBase or hum.HipHeight, hum.HipHeight)
	if hum.HipHeight < hipBase - 0.5 then return "slide" end
	if not UIS:GetFocusedTextBox() and (UIS:IsKeyDown(Enum.KeyCode.C) or UIS:IsKeyDown(Enum.KeyCode.LeftControl)) then return "crouch" end
	return "stand"
end
lp.CharacterAdded:Connect(function() hipBase = nil; sent = "stand" end)

-- bend a joint on top of what the animation put there this frame (and never on top of our own last bend)
local function bend(b, m, delta)
	local rec = b.written[m]
	local cur = m.Transform
	local base = cur
	if rec and (cur.Position - rec.out.Position).Magnitude < 1e-4 and cur.LookVector:Dot(rec.out.LookVector) > 0.99999 and cur.UpVector:Dot(rec.out.UpVector) > 0.99999 then
		base = rec.base
	end
	local out = base * delta
	m.Transform = out
	b.written[m] = { base = base, out = out }
	return out
end

RunService.Stepped:Connect(function(_, dt)
	for _, p in ipairs(Players:GetPlayers()) do
		local ch = p.Character
		local hum = ch and ch:FindFirstChildOfClass("Humanoid")
		local b = hum and bodyOf(ch)
		if b then
			local pose
			if p == lp then
				pose = myPose(ch, hum)
				if pose ~= sent then sent = pose; remote:FireServer(pose) end
			else
				pose = ch:GetAttribute("Pose") or "stand"
				if hum.PlatformStand or hum.Health <= 0 then pose = "stand" end
			end
			local a = math.min(1, dt * 12)
			b.w.crouch += ((if pose == "crouch" then 1 else 0) - b.w.crouch) * a
			b.w.slide += ((if pose == "slide" then 1 else 0) - b.w.slide) * a
			if b.w.crouch > 0.005 or b.w.slide > 0.005 then
				-- standing still: the legs take the crouch outright; moving: the crouch bends the run
				local root = ch:FindFirstChild("HumanoidRootPart")
				local v = root and root.AssemblyLinearVelocity or Vector3.zero
				local still = 1 - math.clamp((Vector3.new(v.X, 0, v.Z).Magnitude - 2) / 8, 0, 1)
				for name, m in pairs(b.motors) do
					local c, s = b.poses.crouch[name], b.poses.slide[name]
					if c or s then
						local legs = LEGS[name] == true
						local delta = ID
						if c then delta = delta * ID:Lerp(c, b.w.crouch * (if legs then 1 - still else 1)) end
						if s then delta = delta * ID:Lerp(s, b.w.slide) end
						local out = bend(b, m, delta)
						if c and legs and still > 0 then
							out = out:Lerp(c, b.w.crouch * still)
							m.Transform = out
							b.written[m].out = out
						end
					end
				end
			else
				b.written = {}
			end
		end
	end
end)
