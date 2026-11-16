--!strict
-- the gun shop at the back of the training range (16 Nov 2026, the owner: "behind the shooting range is still really
-- bland, maybe you can have a gun shop look behind it like this with an npc me?"):
--   * the shopkeeper is the owner's own avatar, the same for everyone (the owner: "I'll be the shop owner"): made on
--     the server from his user id when it starts (Players:CreateHumanoidModelFromUserId: his look of the day), or, if
--     Roblox won't give it, a copy saved in the place (ServerStorage.ShopKeeperCopy). he stands behind the glass
--     counter at Range.Shop.ShopKeeperSpot, idling, anchored (nobody pushes him; his parts take no shots), with the shop
--     on his prompt: ShopOpen = "tab:featured" (ShopClient opens it). he waves when someone opens it
--   * the guns on the slatwall, under the counter's glass and in the tall case are made here when the server starts,
--     from WeaponModels at the size they are in your hands (so they are always today's models), at the Pegs TrainingV2
--     leaves in Range.Shop: Gun = a weapon id or "item:<id>", Len = the longest it may be, High = the tallest, Out =
--     which way is out of the surface it hangs or rests on, Hook = two hooks under it
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))

local OWNER = 2833796200
local K = 4.5 -- studs per metre: a gun's size in your hands (Fight's HAND_K)
local IDLE = { R15 = "rbxassetid://507766388", R6 = "rbxassetid://180435571" } -- (Roblox's own idle and wave)
local WAVE = { R15 = "rbxassetid://507770239", R6 = "rbxassetid://128777973" }
local QUIET = { "Sound", "ParticleEmitter", "Light", "Beam", "Trail", "LuaSourceContainer", "ProximityPrompt", "BillboardGui",
	"ClickDetector", "Smoke", "Fire", "Sparkles" }
local HOOK = Color3.fromHex("62666f")

local function settle(m: Instance)
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then
			d.Anchored = true; d.CanCollide = false; d.CanQuery = false; d.CanTouch = false; d.Massless = true
		else
			for _, c in QUIET do if d:IsA(c) then d:Destroy(); break end end
		end
	end
end

-- a weapon (WeaponModels) or an item (the items' own models, as the hub's holograms use them)
local function make(gun: string): Model?
	local item = string.match(gun, "^item:(.+)$")
	if item then
		local lib = ReplicatedStorage:FindFirstChild("JankfireItems")
		local t = lib and lib:FindFirstChild(if item == "quiz" then "x_calc" else "x_" .. item)
		return if t and t:IsA("Model") then t:Clone() else nil
	end
	local ok, m = pcall(WeaponModels.build, gun, K)
	if ok and m and m:FindFirstChildWhichIsA("BasePart") then return m end
	local lib = ReplicatedStorage:FindFirstChild("JankfireWeapons") -- (the racks' template, as a last resort)
	local t = lib and lib:FindFirstChild("w_" .. gun)
	return if t and t:IsA("Model") then t:Clone() else nil
end

-- half the box's reach along a direction
local function reach(cf: CFrame, size: Vector3, d: Vector3): number
	return math.abs(d:Dot(cf.RightVector)) * size.X / 2 + math.abs(d:Dot(cf.UpVector)) * size.Y / 2 + math.abs(d:Dot(cf.LookVector)) * size.Z / 2
end

local function hang(peg: BasePart, into: Instance)
	local gun = peg:GetAttribute("Gun")
	if type(gun) ~= "string" then return end
	local m = make(gun)
	if not m then warn("[jankfire] shop: no model for " .. gun); return end
	m.Name = gun
	settle(m)
	m.Parent = into -- (ScaleTo wants it in the place)
	local rot = peg.CFrame.Rotation
	m:PivotTo(rot)
	local cf, size = m:GetBoundingBox()
	local len, high = peg:GetAttribute("Len"), peg:GetAttribute("High")
	local f = 1
	local long = math.max(size.X, size.Y, size.Z)
	if type(len) == "number" and long > len then f = math.min(f, len / long) end
	local tall = 2 * reach(cf, size, Vector3.yAxis)
	if type(high) == "number" and tall > high then f = math.min(f, high / tall) end
	if f < 0.999 then
		pcall(function() m:ScaleTo(m:GetScale() * f) end)
		cf, size = m:GetBoundingBox()
	end
	-- the box's middle on the peg, then out from the surface by half the box that way and a little more
	local out = peg:GetAttribute("Out")
	local o = if typeof(out) == "Vector3" and out.Magnitude > 0 then out.Unit else Vector3.yAxis
	local lying = o.Y > 0.5
	local half = reach(cf, size, o)
	local gap = if lying then 0.02 else 0.12
	m:PivotTo(m:GetPivot() + (peg.Position + o * (half + gap) - cf.Position))
	if peg:GetAttribute("Hook") == true and not lying then
		-- two hooks out of the wall under it, a third of its length either side of its middle
		cf, size = m:GetBoundingBox()
		local side = Vector3.yAxis:Cross(o).Unit
		local along = reach(cf, size, side)
		local below = cf.Position.Y - reach(cf, size, Vector3.yAxis)
		local long2 = 2 * half + gap + 0.25
		for _, s in { -0.55, 0.55 } do
			local at = Vector3.new(cf.Position.X, below - 0.11, cf.Position.Z) + side * (s * along)
			at = at - o * o:Dot(at - peg.Position) -- (back onto the wall's plane)
			local h = Instance.new("Part")
			h.Name = "ShopHook"; h.Anchored = true; h.CanCollide = false; h.CanQuery = false; h.CanTouch = false
			h.Material = Enum.Material.SmoothPlastic; h.Color = HOOK; h.Size = Vector3.new(0.2, 0.2, long2)
			h.CFrame = CFrame.lookAt(at + o * (long2 / 2 - 0.08), at + o * long2)
			h.Parent = m
		end
	end
end

-- the shopkeeper: the owner's avatar (the saved copy if Roblox won't give it), anchored, idling, the shop on his prompt
local function keeper(spot: BasePart, into: Instance)
	local m: Model? = nil
	local ok, res = pcall(function() return Players:CreateHumanoidModelFromUserId(OWNER) end)
	if ok and res then
		m = res
	else
		local saved = ServerStorage:FindFirstChild("ShopKeeperCopy")
		warn("[jankfire] shopkeeper: no avatar from Roblox (" .. tostring(res) .. "), " .. (if saved then "the saved copy" else "a plain one") .. " stands in")
		if saved and saved:IsA("Model") then
			m = saved:Clone()
		else
			local ok2, res2 = pcall(function()
				return Players:CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R15)
			end)
			if ok2 then m = res2 end
		end
	end
	if not m then return end
	local npc = m :: Model
	npc.Name = "ShopKeeper"
	local hum = npc:FindFirstChildOfClass("Humanoid")
	local root = npc:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root then npc:Destroy(); return end
	hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	hum.HealthDisplayType = Enum.HumanoidHealthDisplayType.AlwaysOff
	hum.BreakJointsOnDeath = false; hum.RequiresNeck = false
	hum:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
	for _, d in npc:GetDescendants() do
		if d:IsA("BasePart") then d.CanQuery = false; d.CanTouch = false; d.CanCollide = false
		elseif d:IsA("LuaSourceContainer") then d:Destroy() end
	end
	root.Anchored = true
	local r6 = hum.RigType == Enum.HumanoidRigType.R6
	local up = if r6 then 3 else hum.HipHeight + root.Size.Y / 2
	npc:PivotTo(spot.CFrame * CFrame.new(0, up, 0))
	npc.Parent = into
	local an = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator")
	an.Parent = hum
	local rig = if r6 then "R6" else "R15"
	local function track(id: string, looped: boolean, pri: Enum.AnimationPriority): AnimationTrack?
		local a = Instance.new("Animation")
		a.AnimationId = id
		local ok3, t = pcall(function() return an:LoadAnimation(a) end)
		if not ok3 or not t then return nil end
		t.Looped = looped; t.Priority = pri
		return t
	end
	local idle = track(IDLE[rig], true, Enum.AnimationPriority.Idle)
	if idle then idle:Play() end
	local wave = track(WAVE[rig], false, Enum.AnimationPriority.Action)
	local pr = Instance.new("ProximityPrompt")
	pr.Name = "ShopPrompt"; pr.ActionText = "Shop"; pr.ObjectText = ""
	pr.HoldDuration = 0; pr.MaxActivationDistance = 11; pr.RequiresLineOfSight = false
	pr.KeyboardKeyCode = Enum.KeyCode.E
	pr:SetAttribute("ShopOpen", "tab:featured")
	pr.Parent = root
	local waved = -math.huge
	pr.Triggered:Connect(function()
		if wave and os.clock() - waved > 4 then waved = os.clock(); wave:Play(0.15) end
	end)
	task.spawn(function()
		local okN, name = pcall(function() return Players:GetNameFromUserIdAsync(OWNER) end)
		if okN and type(name) == "string" then pr.ObjectText = name end
	end)
end

local hub = workspace:WaitForChild("Map"):WaitForChild("Hub")
local tg = hub:WaitForChild("TrainingGround", 30)
local range = tg and tg:WaitForChild("Range", 30)
local shop = range and range:WaitForChild("Shop", 30)
if shop then
	local old = shop:FindFirstChild("Stock")
	if old then old:Destroy() end
	local stock = Instance.new("Folder")
	stock.Name = "Stock"
	stock.Parent = shop
	for _, p in shop:GetChildren() do
		if p:IsA("BasePart") and p.Name == "Peg" then
			local ok, err = pcall(hang, p, stock)
			if not ok then warn("[jankfire] shop peg " .. tostring(p:GetAttribute("Gun")) .. ": " .. tostring(err)) end
		end
	end
	local spot = shop:FindFirstChild("ShopKeeperSpot")
	if spot and spot:IsA("BasePart") then keeper(spot, stock) end
end
