--!strict
-- the gun shop at the back of the training range (16 Nov 2026, the owner: "behind the shooting range is still really
-- bland, maybe you can have a gun shop look behind it like this with an npc me?"):
--   * the shopkeeper is the owner's own avatar, the same for everyone (the owner: "I'll be the shop owner"): made on
--     the server from his user id when it starts (Players:CreateHumanoidModelFromUserId: his look of the day), or, if
--     Roblox won't give it, a copy saved in the place (ServerStorage.ShopKeeperCopy). he stands behind the glass
--     counter at Range.Shop.ShopKeeperSpot, anchored (nobody pushes him; his parts take no shots), his feet on the floor.
--     he is built as R15 from his avatar's description (like the hub's regulars), so his sway fits him. (17 Nov, the
--     owner: "I give players 3 special discounts on random skins if you talk to me! I want a cute sway waiting at the
--     cases"): he sways gently at the cases (SWAY), talking to him (DEALS, on E) opens your three deals of the day, and
--     the shop itself is on F. he waves when someone uses either. his name and DEALS over him, like the hub's regulars
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
-- his idle at the cases: a slow side-to-side sway, his weight going foot to foot, hands clasped, made with Studio's
-- prompt-to-animation tool on his avatar (17 Nov, its second take: the first barely moved). it loops as two copies
-- crossfading at each end (the hub's regulars' way); Roblox's own idle (IDLE) if it won't load
local SWAY = "rbxassetid://132873393676097"
-- the talk prompt: { what it says, the attribute it carries, its value } (ShopClient reads ShopOpen). the hub's
-- regulars' prompt style: on an attachment at chest height, E (gamepad X), no hold, 8 studs, no line of sight, clickable,
-- his name under it
local DEALS = { "Deals", "ShopOpen", "tab:deals" }
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

-- a loop with no pop where it ends: two tracks of the clip, the next fading in as the last one runs out (HubNPCs')
local function loop(animator: Animator, id: string): boolean
	local a = Instance.new("Animation"); a.AnimationId = id
	local ok1, t1 = pcall(function() return animator:LoadAnimation(a) end)
	local ok2, t2 = pcall(function() return animator:LoadAnimation(a) end)
	if not ok1 or not ok2 or not t1 or not t2 then return false end
	for _, t in { t1, t2 } do t.Looped = false; t.Priority = Enum.AnimationPriority.Idle end
	t1:Play(0.4)
	task.spawn(function()
		local cur = t1
		while animator.Parent do
			if cur.Length <= 0 then task.wait(0.2); continue end
			local left = cur.Length - cur.TimePosition
			if left > 0.8 then task.wait(left - 0.75); continue end
			local nxt = if cur == t1 then t2 else t1
			nxt:Play(0.7); cur:Stop(0.7)
			cur = nxt
			task.wait(0.9)
		end
	end)
	return true
end

-- his name over him, then what he does for you in a quieter grey (the hub's regulars' label)
local function label(head: BasePart, name: string)
	local bb = Instance.new("BillboardGui")
	bb.Name = "NameLabel"; bb.Size = UDim2.new(8.5, 0, 0.9, 0); bb.StudsOffsetWorldSpace = Vector3.new(0, 1.9, 0)
	bb.LightInfluence = 0; bb.MaxDistance = 45; bb.AlwaysOnTop = false; bb.Adornee = head
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(1, 1); t.TextScaled = true; t.RichText = true
	t.Text = ("%s  <font color=\"#98a2ac\">·  DEALS</font>"):format(string.upper(name))
	t.TextColor3 = Color3.fromRGB(236, 240, 242); t.TextStrokeTransparency = 0.6
	t.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Bold)
	t.Parent = bb
	bb.Parent = head
end

-- the shopkeeper: the owner's avatar as R15 (the saved copy if Roblox won't give it), anchored, swaying, deals and the
-- shop on his prompts
local function keeper(spot: BasePart, into: Instance)
	local m: Model? = nil
	local ok, res = pcall(function()
		local desc = Players:GetHumanoidDescriptionFromUserId(OWNER)
		return Players:CreateHumanoidModelFromDescription(desc, Enum.HumanoidRigType.R15)
	end)
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
	npc.PrimaryPart = root
	npc:PivotTo(spot.CFrame * CFrame.new(0, up, 0))
	npc.Parent = into
	-- (a scaled R15 avatar's legs can be longer than its HipHeight says: lift him till his lowest part is on the floor)
	local floorY = spot.Position.Y
	local low = math.huge
	for _, p in npc:GetDescendants() do if p:IsA("BasePart") and p.Transparency < 1 then low = math.min(low, p.Position.Y - p.Size.Y / 2) end end
	if low < floorY - 0.05 and low > floorY - 3 then npc:PivotTo(npc:GetPivot() + Vector3.new(0, floorY - low, 0)) end
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
	if r6 or SWAY == "" or not loop(an, SWAY) then
		local idle = track(IDLE[rig], true, Enum.AnimationPriority.Idle)
		if idle then idle:Play() end
	end
	local wave = track(WAVE[rig], false, Enum.AnimationPriority.Action)
	-- his prompts at his chest: Deals (E) over Shop (F)
	local at = Instance.new("Attachment")
	at.Name = "PromptAt"; at.Position = Vector3.new(0, floorY + 3.2 - root.Position.Y, 0); at.Parent = root
	local function prompt(name: string, action: string, key: Enum.KeyCode, pad: Enum.KeyCode, attr: string, value: any, below: number): ProximityPrompt
		local pr = Instance.new("ProximityPrompt")
		pr.Name = name; pr.ActionText = action; pr.ObjectText = ""
		pr.KeyboardKeyCode = key; pr.GamepadKeyCode = pad; pr.HoldDuration = 0
		pr.MaxActivationDistance = 8; pr.RequiresLineOfSight = false; pr.ClickablePrompt = true
		pr.UIOffset = Vector2.new(0, below)
		pr:SetAttribute(attr, value)
		pr.Parent = at
		return pr
	end
	local deals = prompt("DealsPrompt", DEALS[1], Enum.KeyCode.E, Enum.KeyCode.ButtonX, DEALS[2], DEALS[3], 0)
	local shopPr = prompt("ShopPrompt", "Shop", Enum.KeyCode.F, Enum.KeyCode.ButtonY, "ShopOpen", "tab:featured", 76)
	local waved = -math.huge
	for _, pr in { deals, shopPr } do
		pr.Triggered:Connect(function()
			if wave and os.clock() - waved > 4 then waved = os.clock(); wave:Play(0.15) end
		end)
	end
	task.spawn(function()
		local okN, name = pcall(function() return Players:GetNameFromUserIdAsync(OWNER) end)
		if not (okN and type(name) == "string") then name = "Shop" end
		deals.ObjectText = name; shopPr.ObjectText = name
		local head = npc:FindFirstChild("Head")
		if head and head:IsA("BasePart") then label(head, name) end
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
