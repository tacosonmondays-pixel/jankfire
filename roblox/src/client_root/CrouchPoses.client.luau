-- crouch and slide poses on R15 bodies, for everyone. A crouch (C): bent knees, hips down and back, a forward lean,
-- layered on top of whatever animation is playing (crouch-walking bends the run); standing still in a crouch the legs
-- and hips take the crouch pose outright (not on top of the idle) so both feet stay planted. A slide takes the whole
-- body outright (16 Nov 2026: "your feet still move like they kick like they're trying to run"): the run cycle
-- underneath doesn't show at all. Leaning back, the right leg out in front nearly straight, the left folded under,
-- hips low (worked out from the body's own leg lengths so the folded shin lies on the floor), the left arm out for
-- balance; eased in and out in about 0.1 s. Your own pose comes from your keys and Move's slide; everyone else's from
-- the "Pose" the server puts on their character. The third-person weapon pose (ThirdPerson.luau) has the last word on
-- the upper body, so a held gun stays held through a slide. Footsteps (Steps.client) are silent while sliding.
-- Tune live in a Play test through this script's "Tune" attribute (JSON merged into T, angles in degrees), then write
-- the numbers back. Test bodies tagged TPRig are posed too (attribute "Pose"; "PoseW" = a number freezes the weight)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local HttpService = game:GetService("HttpService")
local CollectionService = game:GetService("CollectionService")
local remote = game:GetService("ReplicatedStorage"):WaitForChild("PoseRemote")

local lp = Players.LocalPlayer
local Binds = require(script.Parent:WaitForChild("Jankfire"):WaitForChild("Binds")) :: any -- (the crouch, held or toggled: Settings)
local Keys = require(script.Parent:WaitForChild("Jankfire"):WaitForChild("Keys")) -- (C held: a keyboard, or the phone's SLIDE)
-- the third-person weapon pose (Jankfire.ThirdPerson) has the last word on the upper body: it runs right after these
-- bends every frame, so the gun, the chest and the hands are placed on top of the crouch and the slide
local TPose: any = nil
task.spawn(function()
	local f = script.Parent:WaitForChild("Jankfire", 30)
	local m = f and f:WaitForChild("ThirdPerson", 30)
	if m then
		local ok, t = pcall(require, m)
		if ok then TPose = t end
	end
end)
local rad = math.rad
local A = CFrame.Angles
local ID = CFrame.identity

-- the slide (degrees; sink = how far Move.client lowers HipHeight in a slide; lift = the hips up from the worked-out
-- height, measured in Play: without it the folded shin sat 0.35 into the floor; rate = the ease, per second)
local T = {
	lean = 28, waist = 4, neck = -30,
	frontHip = 32, frontKnee = -6, frontAnkle = -18,
	backHip = 14, backKnee = -108, backAnkle = 30, backOut = -8,
	leftArm = -65, leftArmBack = 20, rightArm = 18, rightArmOut = 12,
	sink = 0.9, lift = 0.3, rate = 18,
}
local bodies = {} -- [character] = { poses, motors = {name = joint}, w = {crouch, slide}, written = {}, dirty }
local function retune()
	local s = script:GetAttribute("Tune")
	if type(s) ~= "string" or s == "" then return end
	local ok, t = pcall(function() return HttpService:JSONDecode(s) end)
	if ok and type(t) == "table" then
		for k, v in t do if type(v) == "number" and T[k] ~= nil then T[k] = v end end
		for _, b in bodies do b.dirty = true end
	end
end
script:GetAttributeChangedSignal("Tune"):Connect(retune)
retune()

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
	-- the slide: how high the hips have to be for each leg's lowest point to reach the floor (the folded shin lies on
	-- it, the front heel touches it), against a standing hip height of the whole leg; Move.client already lowers the
	-- body by T.sink, the Root joint takes the rest (up or down)
	local foot = ch:FindFirstChild("RightFoot")
	local fa = foot and foot:FindFirstChild("RightAnkleRigAttachment")
	local f = if foot and fa then math.max(0.1, foot.Size.Y / 2 + fa.Position.Y) else 0.3
	local L = rad(T.lean)
	local fa1, ba1 = L + rad(T.frontHip), L + rad(T.backHip)
	local front = l1 * math.cos(fa1) + l2 * math.cos(fa1 + rad(T.frontKnee)) + f * 0.6
	local back = l1 * math.cos(ba1) + l2 * math.cos(ba1 + rad(T.backKnee)) + f * 0.4
	local sdrop = (l1 + l2 + f) - math.max(front, back) - T.sink - T.lift
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
			Root = CFrame.new(0, -sdrop, 0) * A(L, 0, 0),
			Waist = A(rad(T.waist), 0, 0),
			Neck = A(rad(T.neck), 0, 0),
			RightHip = A(rad(T.frontHip), 0, 0), RightKnee = A(rad(T.frontKnee), 0, 0), RightAnkle = A(rad(T.frontAnkle), 0, 0),
			LeftHip = A(rad(T.backHip), 0, rad(T.backOut)), LeftKnee = A(rad(T.backKnee), 0, 0), LeftAnkle = A(rad(T.backAnkle), 0, 0),
			LeftShoulder = A(rad(T.leftArmBack), 0, rad(T.leftArm)), LeftElbow = ID, LeftWrist = ID,
			RightShoulder = A(rad(T.rightArm), 0, rad(T.rightArmOut)), RightElbow = ID, RightWrist = ID,
		},
	}
end

-- every body's joints (old Motor6Ds or the new avatar AnimationConstraints). the avatar's joints get rebuilt a moment
-- after a spawn (scaling, the new joints), so the list is collected again whenever joints come or go
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
	if not UIS:GetFocusedTextBox() and Binds.on("crouch") then return "crouch" end -- (held or toggled, any key bound to it: Jankfire.Binds)
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

-- one body, one frame. w: a fixed weight for the pose (test bodies), else eased toward the pose
local function poseBody(ch, b, pose, dt, w)
	if type(w) == "number" then
		b.w.crouch = if pose == "crouch" then math.clamp(w, 0, 1) else 0
		b.w.slide = if pose == "slide" then math.clamp(w, 0, 1) else 0
	else
		b.w.crouch += ((if pose == "crouch" then 1 else 0) - b.w.crouch) * math.min(1, dt * 12)
		b.w.slide += ((if pose == "slide" then 1 else 0) - b.w.slide) * math.min(1, dt * T.rate)
	end
	if b.w.crouch <= 0.005 and b.w.slide <= 0.005 then
		b.written = {}
		return
	end
	-- crouching standing still: the legs take the crouch outright; moving: the crouch bends the run
	local root = ch:FindFirstChild("HumanoidRootPart")
	local v = root and root.AssemblyLinearVelocity or Vector3.zero
	local still = 1 - math.clamp((Vector3.new(v.X, 0, v.Z).Magnitude - 2) / 8, 0, 1)
	for name, m in pairs(b.motors) do
		local c, s = b.poses.crouch[name], b.poses.slide[name]
		if c or s then
			local legs = LEGS[name] == true
			local out = bend(b, m, if c then ID:Lerp(c, b.w.crouch * (if legs then 1 - still else 1)) else ID)
			if c and legs and still > 0 then out = out:Lerp(c, b.w.crouch * still) end
			if s then out = out:Lerp(s, b.w.slide) end -- (the slide: outright, whatever the run is doing)
			m.Transform = out
			b.written[m].out = out
		end
	end
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
			poseBody(ch, b, pose, dt, nil)
		end
	end
	-- test bodies (ThirdPerson's TPRig): posed like other players, from their own "Pose" (and "PoseW")
	for _, ch in CollectionService:GetTagged("TPRig") do
		if ch:IsA("Model") and ch.Parent and ch:FindFirstChildOfClass("Humanoid") then
			local b = bodyOf(ch)
			if b then poseBody(ch, b, ch:GetAttribute("Pose") or "stand", dt, ch:GetAttribute("PoseW")) end
		end
	end
	if TPose then TPose.step(dt) end
end)
