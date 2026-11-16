--!nonstrict
-- the hub's regulars: the owner's friends, standing or sitting about the hub in their own avatars (owner, 16 Nov: "Can you
-- put these two as NPCs somewhere?" and "This one too"). every part tagged "HubNPC" is a regular's place (HubRotunda's
-- B.npc leaves them; any builder may): attributes Who (the name to show), User (their Roblox username), UserId (optional,
-- else looked up), Pose ("sit" on the Seat that is the place, or "stand" on its spot). at server start their avatar is
-- built from their user id; if that fails, the saved copy ServerStorage.JankfireNPCs.<Who> is used. they can't be pushed
-- (seated on an anchored seat, or anchored), shot (no queries, no touches) or killed, and play a calm idle or sit
-- animation. one label over them, their name; no other text
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")
local ServerStorage = game:GetService("ServerStorage")

local TAG = "HubNPC"
local ANIM = { -- Roblox's own default animations
	[Enum.HumanoidRigType.R15] = { stand = "rbxassetid://507766388", sit = "rbxassetid://2506281703" },
	[Enum.HumanoidRigType.R6] = { stand = "rbxassetid://180435571", sit = "rbxassetid://178130996" },
}

local function userIdOf(spot: BasePart): number?
	local id = spot:GetAttribute("UserId")
	if type(id) == "number" and id > 0 then return id end
	local name = spot:GetAttribute("User")
	if type(name) ~= "string" then return nil end
	for _ = 1, 3 do
		local ok, res = pcall(function() return Players:GetUserIdFromNameAsync(name) end)
		if ok and res then spot:SetAttribute("UserId", res); return res end
		task.wait(2)
	end
	return nil
end

local function avatar(spot: BasePart, who: string): Model?
	local id = userIdOf(spot)
	if id then
		for _ = 1, 2 do
			local ok, m = pcall(function() return Players:CreateHumanoidModelFromUserId(id) end)
			if ok and m then return m end
			task.wait(2)
		end
	end
	local lib = ServerStorage:FindFirstChild("JankfireNPCs")
	local saved = lib and lib:FindFirstChild(who)
	if saved and saved:IsA("Model") then return saved:Clone() end
	warn("[jankfire] no avatar for the hub's " .. who)
	return nil
end

local function label(m: Model, text: string, head: BasePart?)
	local bb = Instance.new("BillboardGui")
	bb.Name = "NameLabel"; bb.Size = UDim2.new(5, 0, 0.9, 0); bb.StudsOffsetWorldSpace = Vector3.new(0, 1.9, 0)
	bb.LightInfluence = 0; bb.MaxDistance = 45; bb.AlwaysOnTop = false; bb.Adornee = head
	local t = Instance.new("TextLabel")
	t.BackgroundTransparency = 1; t.Size = UDim2.fromScale(1, 1); t.TextScaled = true; t.Text = text
	t.TextColor3 = Color3.fromRGB(236, 240, 242); t.TextStrokeTransparency = 0.6
	t.FontFace = Font.new("rbxasset://fonts/families/Montserrat.json", Enum.FontWeight.Bold)
	t.Parent = bb
	bb.Parent = head or m
end

local function place(spot: BasePart)
	if spot:GetAttribute("Built") then return end
	spot:SetAttribute("Built", true)
	local who = spot:GetAttribute("Who") or spot.Name
	local m = avatar(spot, who)
	if not m then return end
	m.Name = "Regular_" .. who
	local hum = m:FindFirstChildOfClass("Humanoid")
	local root = m:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root then m:Destroy(); return end
	for _, d in m:GetDescendants() do
		if d:IsA("LuaSourceContainer") or d:IsA("Sound") then d:Destroy()
		elseif d:IsA("BasePart") then d.CanQuery = false; d.CanTouch = false; d.CastShadow = true end
	end
	hum.DisplayDistanceType = Enum.HumanoidDisplayDistanceType.None
	hum.BreakJointsOnDeath = false
	hum.MaxHealth = math.huge; hum.Health = math.huge
	hum:SetStateEnabled(Enum.HumanoidStateType.Dead, false)
	hum:SetStateEnabled(Enum.HumanoidStateType.Ragdoll, false)
	hum:SetStateEnabled(Enum.HumanoidStateType.FallingDown, false)
	local pose = if spot:GetAttribute("Pose") == "sit" and spot:IsA("Seat") then "sit" else "stand"
	-- the floor (or the seat's cushion) under the place: a ray down, the place itself and every regular left out
	local skip = { spot, m }
	for _, r in CollectionService:GetTagged(TAG) do table.insert(skip, r) end
	local rp = RaycastParams.new(); rp.FilterType = Enum.RaycastFilterType.Exclude; rp.FilterDescendantsInstances = skip; rp.RespectCanCollide = false
	local hit = workspace:Raycast(spot.Position + Vector3.new(0, 4, 0), Vector3.new(0, -9, 0), rp)
	local floorY = if hit then hit.Position.Y else spot.Position.Y
	local turn = spot.CFrame.Rotation
	m.Parent = spot.Parent
	if pose == "sit" then
		-- (the seat stays where its builder put it, on the cushion: the hub's kit pieces don't take rays)
		local seat = spot :: Seat
		root.Anchored = false
		m:PivotTo(seat.CFrame * CFrame.new(0, 3, 0))
		seat.Disabled = false
		seat:Sit(hum)
	else
		local h = if hum.RigType == Enum.HumanoidRigType.R6 then 3 else hum.HipHeight + root.Size.Y / 2
		root.Anchored = true
		m.PrimaryPart = root
		m:PivotTo(CFrame.new(spot.Position.X, floorY + h, spot.Position.Z) * turn)
		-- (a scaled R15 avatar's legs can be longer than its HipHeight says: lift it till its lowest part is on the floor)
		local low = math.huge
		for _, p in m:GetDescendants() do if p:IsA("BasePart") and p.Transparency < 1 then low = math.min(low, p.Position.Y - p.Size.Y / 2) end end
		if low < floorY - 0.05 and low > floorY - 3 then m:PivotTo(m:GetPivot() + Vector3.new(0, floorY - low, 0)) end
	end
	local animator = hum:FindFirstChildOfClass("Animator") or Instance.new("Animator")
	animator.Parent = hum
	local a = Instance.new("Animation")
	a.AnimationId = (ANIM[hum.RigType] or ANIM[Enum.HumanoidRigType.R15])[pose]
	local ok, track = pcall(function() return animator:LoadAnimation(a) end)
	if ok and track then track.Looped = true; track.Priority = Enum.AnimationPriority.Idle; track:Play(0.3, 1, if pose == "stand" then 0.8 else 1) end
	label(m, tostring(who), m:FindFirstChild("Head") :: BasePart?)
end

CollectionService:GetInstanceAddedSignal(TAG):Connect(function(s) if s:IsA("BasePart") then task.spawn(place, s) end end)
for _, s in CollectionService:GetTagged(TAG) do if s:IsA("BasePart") then task.spawn(place, s) end end
