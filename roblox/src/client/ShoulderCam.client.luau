--!strict
-- third person (V): the over-the-shoulder camera (16 Nov 2026, after the third-person weapon pose; doc:
-- docs/THIRD-PERSON.md). The camera sits behind your right shoulder, so the crosshair in the middle of the screen has
-- a clear view past you; the mouse is locked to the middle (moving it turns the camera, no button to hold, like
-- Roblox's Shift Lock); aiming a gun (RMB) brings the camera in close over the shoulder. Walls pull it in, never
-- through. First person is Roblox's own camera, untouched.
-- Move.client says when third person is on (the player's attribute ThirdPerson). How far you're aimed in comes from
-- ThirdPerson.luau (TP.aiming: Arsenal's ADS blend, the same speed as first person). Camera kicks and shakes (Arsenal,
-- items) are changes from last frame's look, so the look is read back from the camera every frame, as Roblox's own
-- camera does. Menus (LoadoutOpen: the loadout, shop, profile, loot) have the camera and the mouse while they're up;
-- under the settings panel (SettingsOpen) the mouse is free and the camera holds its look.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local HttpService = game:GetService("HttpService")

local me = Players.LocalPlayer

local TP: any = nil
task.spawn(function()
	local m = script.Parent:WaitForChild("ThirdPerson", 30)
	if not m then return end
	local ok, r = pcall(require, m)
	if ok then TP = r end
end)

-- distances in studs from the head (the camera's focus): right, up, back. Tune live in a Play test through this
-- script's "Tune" attribute (JSON merged in, e.g. '{"hip":{"back":9}}'), then write the numbers back here
local C = {
	hip = { right = 2.5, up = 0.6, back = 8 },
	ads = { right = 2.3, up = 0.55, back = 5.4 }, -- (wide enough that a big hat stays off the crosshair)
	-- (the guns, the HUD and the items tell first person from third by the camera being more than 4.5 studs from your
	-- root: every pose here stays well past that, unless a wall pulls the camera in)
	-- radians per pixel of mouse: Roblox's own camera's numbers, so turning feels the same as in first person (the P
	-- menu's sensitivity scales the mouse for both)
	turnX = math.rad(0.5),
	turnY = math.rad(0.5) * 0.77,
	pitchMax = math.rad(80),
	armUp = math.rad(25),
	radius = 0.4, -- the camera's own size against walls
	outRate = 6, -- how fast it slides back out once a wall is gone (per second)
	startBack = 0.6, -- coming out of first person: starts this far along the line and eases out
	inTime = 0.14, -- going back to first person: the glide in to your head (seconds)
	fadeNear = 1.0, fadeFar = 2.6, -- a wall right behind you pulls the camera this close to your head: your body fades
}
local function merge(dst: any, src: any)
	for k, v in src do
		if type(dst[k]) == "table" and type(v) == "table" then merge(dst[k], v)
		elseif type(v) == "number" then dst[k] = v end
	end
end
local function retune()
	local s = script:GetAttribute("Tune")
	if type(s) ~= "string" or s == "" then return end
	local ok, t = pcall(function() return HttpService:JSONDecode(s) end)
	if ok and type(t) == "table" then merge(C, t) end
end
script:GetAttributeChangedSignal("Tune"):Connect(retune)
retune()

local S = { on = false, frac = 1, leaving = nil :: number?, leaveFrac = 1 }

-- the point the camera turns about: Roblox's own camera's (1.5 above the root, more on a taller root), plus the
-- crouch / slide drop Move.client puts in CameraOffset. Dead: the head
local function focusOf(ch: Model): Vector3?
	local hum = ch:FindFirstChildOfClass("Humanoid")
	local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if root and hum and hum.Health > 0 then
		return root.Position + Vector3.new(0, 1.5 + root.Size.Y / 2 - 1 + hum.CameraOffset.Y, 0)
	end
	local head = ch:FindFirstChild("Head") :: BasePart?
	if head then return head.Position end
	return if root then root.Position else nil
end

-- walls: a ball the camera's size from the head out to where it wants to be. Bodies, see-through parts (glass,
-- invisible hit boxes), trusses and anything you can walk through don't stop it (Roblox's own camera's rules)
local params = RaycastParams.new()
params.FilterType = Enum.RaycastFilterType.Exclude
params.RespectCanCollide = true
params.IgnoreWater = true
local filterT = -1
local function refilter()
	local list: { Instance } = { workspace.CurrentCamera }
	for _, p in Players:GetPlayers() do
		if p.Character then table.insert(list, p.Character) end
	end
	local d = workspace:FindFirstChild("Dummies")
	if d then table.insert(list, d) end
	params.FilterDescendantsInstances = list
end
local function clear(from: Vector3, dir: Vector3, want: number): number
	if os.clock() - filterT > 0.5 then filterT = os.clock(); refilter() end -- (new bodies; forgets the see-through parts)
	for _ = 1, 8 do
		local hit = workspace:Spherecast(from, C.radius, dir * want, params)
		if not hit then return want end
		local p = hit.Instance
		local m = p:FindFirstAncestorOfClass("Model")
		local body = m ~= nil and m:FindFirstChildOfClass("Humanoid") ~= nil
		if p:IsA("BasePart") and (p.Transparency >= 0.25 or p:IsA("TrussPart") or body) then
			params:AddToFilter(p)
		else
			return math.max(0, hit.Distance)
		end
	end
	return want
end

local function lookOf(cf: CFrame): (number, number)
	local l = cf.LookVector
	return math.atan2(-l.X, -l.Z), math.asin(math.clamp(l.Y, -1, 1))
end

-- the camera pulled in close to your head (a wall right behind you): your body fades out of the way, as Roblox's own
-- camera does (the guns and items keep their own looks)
local fadeNow = 0
local function fade(ch: Model?, k: number)
	if not ch or math.abs(k - fadeNow) < 0.03 and not (k == 0 and fadeNow > 0) then return end
	fadeNow = k
	for _, d in ch:GetDescendants() do
		if d:IsA("BasePart") and not d:FindFirstAncestor("HeldWeapon") and not d:FindFirstAncestor("TPGun")
			and not d:FindFirstAncestor("TPItem") and not d:FindFirstAncestorOfClass("Tool") then
			d.LocalTransparencyModifier = k
		end
	end
end

local function release()
	if not S.on then return end
	S.on = false
	S.leaving = nil
	fade(me.Character, 0)
	local cam = workspace.CurrentCamera
	if cam.CameraType == Enum.CameraType.Scriptable and me:GetAttribute("LoadoutOpen") ~= true then
		cam.CameraType = Enum.CameraType.Custom
	end
	UIS.MouseBehavior = Enum.MouseBehavior.Default
end

RunService:BindToRenderStep("JankShoulderCam", Enum.RenderPriority.Camera.Value - 1, function(dt: number)
	local cam = workspace.CurrentCamera
	local ch = me.Character
	local focus = if ch then focusOf(ch) else nil
	if not UIS.MouseEnabled or not ch or not focus then
		release()
		return
	end
	if me:GetAttribute("LoadoutOpen") == true then -- (a menu has the camera and the mouse)
		if fadeNow > 0 then fade(ch, 0) end
		return
	end
	if me:GetAttribute("ThirdPerson") ~= true then
		-- back to first person: a quick glide in to your head, then Roblox's own camera
		if not S.on then return end
		if not S.leaving then S.leaving, S.leaveFrac = os.clock(), S.frac end
		if os.clock() - (S.leaving :: number) >= C.inTime then release(); return end
	elseif S.leaving then
		S.leaving = nil -- (V again mid-glide: back out)
	end
	if not S.on then
		S.on = true
		S.frac = C.startBack
		fadeNow = -1; fade(ch, 0) -- (your body shows from behind: first person's camera hid it)
	end
	if cam.CameraType ~= Enum.CameraType.Scriptable then cam.CameraType = Enum.CameraType.Scriptable end

	-- the look: last frame's (with any kick on it), then the mouse
	local yaw, pitch = lookOf(cam.CFrame)
	if me:GetAttribute("SettingsOpen") == true then
		if UIS.MouseBehavior ~= Enum.MouseBehavior.Default then UIS.MouseBehavior = Enum.MouseBehavior.Default end
	else
		if UIS.MouseBehavior ~= Enum.MouseBehavior.LockCenter then UIS.MouseBehavior = Enum.MouseBehavior.LockCenter end
		local d = UIS:GetMouseDelta()
		yaw -= d.X * C.turnX
		pitch -= d.Y * C.turnY
	end
	pitch = math.clamp(pitch, -C.pitchMax, C.pitchMax)
	local rot = CFrame.fromOrientation(pitch, yaw, 0)

	-- where it wants to be: over the right shoulder at the hip, closer in while aiming. Looking up, it stops going
	-- down behind you at armUp (it stays at the shoulder instead of swinging under you into the floor)
	local a = 0
	if TP and TP.aiming then a = math.clamp(TP.aiming(), 0, 1) end
	a = a * a * (3 - 2 * a)
	local h, s = C.hip, C.ads
	local arm = CFrame.fromOrientation(math.min(pitch, C.armUp), yaw, 0)
	local off = arm:VectorToWorldSpace(Vector3.new(
		h.right + (s.right - h.right) * a,
		h.up + (s.up - h.up) * a,
		h.back + (s.back - h.back) * a))
	local want = off.Magnitude
	local dir = off / want
	-- a wall in the way: straight in to it; gone: ease back out
	local free = clear(focus, dir, want) / want
	if free < S.frac then S.frac = free
	else S.frac += (free - S.frac) * (1 - math.exp(-dt * C.outRate)) end
	if S.leaving then
		local u = math.clamp((os.clock() - (S.leaving :: number)) / C.inTime, 0, 1)
		S.frac = math.min(S.frac, S.leaveFrac * (1 - u * u * (3 - 2 * u)))
	end
	cam.CFrame = CFrame.new(focus + dir * want * S.frac) * rot
	fade(ch, 1 - math.clamp((want * S.frac - C.fadeNear) / (C.fadeFar - C.fadeNear), 0, 1))
end)

-- a new body: back over the shoulder from the start (and shown)
me.CharacterAdded:Connect(function(ch)
	if S.on then
		S.frac = C.startBack
		task.defer(function() fadeNow = -1; fade(ch, 0) end)
	end
end)
