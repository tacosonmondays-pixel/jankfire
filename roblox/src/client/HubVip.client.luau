--!strict
-- the hub's VIP door (HubRotundaRooms builds it, behind the lounge): its looks on your own screen. who may pass is the
-- server's decision (HubVip.server: Vip.isVip, a collision group that lets a VIP's character through the leaves, and a
-- check that puts anyone else back out of the room); the player attribute VIP it sets is only for looks:
--   a VIP: the door's leaves (Models tagged VipDoor, each with Slide = how far it moves to open) slide open as you come
--   near, and the "Get VIP" prompt is off
--   anyone else: the door stays shut, and its prompt (on the part tagged VipPrompt, ShopOpen = "vip") opens the shop on
--   the VIP tile (ShopClient acts on that)
local RunService = game:GetService("RunService")
local Players = game:GetService("Players")
local CollectionService = game:GetService("CollectionService")

local me = Players.LocalPlayer
local NEAR, SPEED = 10, 3.2 -- (studs from the door it opens at; opening a second)

type Leaf = { m: Model, parts: { { p: BasePart, home: CFrame } }, slide: Vector3, t: number }
local leaves: { [Model]: Leaf } = {}

local function addLeaf(m: Instance)
	if not m:IsA("Model") or leaves[m] then return end
	local slide = m:GetAttribute("Slide")
	if typeof(slide) ~= "Vector3" then return end
	local lf: Leaf = { m = m, parts = {}, slide = slide, t = 0 }
	for _, p in m:GetDescendants() do if p:IsA("BasePart") then table.insert(lf.parts, { p = p, home = p.CFrame }) end end
	leaves[m] = lf
end
CollectionService:GetInstanceAddedSignal("VipDoor"):Connect(addLeaf)
CollectionService:GetInstanceRemovedSignal("VipDoor"):Connect(function(m) leaves[m :: Model] = nil end)
for _, m in CollectionService:GetTagged("VipDoor") do addLeaf(m) end

local function isVip(): boolean return me:GetAttribute("VIP") == true end

local function prompts()
	local vip = isVip()
	for _, p in CollectionService:GetTagged("VipPrompt") do
		local pr = p:FindFirstChildWhichIsA("ProximityPrompt")
		if pr then pr.Enabled = not vip end
	end
end
me:GetAttributeChangedSignal("VIP"):Connect(prompts)
CollectionService:GetInstanceAddedSignal("VipPrompt"):Connect(prompts)
prompts()

RunService.RenderStepped:Connect(function(dt: number)
	if next(leaves) == nil then return end
	local vip = isVip()
	local ch = me.Character
	local root = ch and ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	for m, lf in leaves do
		if not m.Parent or #lf.parts == 0 then continue end
		local near = false
		if vip and root then near = (root.Position - lf.parts[1].home.Position).Magnitude < NEAR end
		local goal = if near then 1 else 0
		if lf.t ~= goal then
			lf.t = math.clamp(lf.t + (if goal > lf.t then dt else -dt) * SPEED, 0, 1)
			local e = lf.t * lf.t * (3 - 2 * lf.t)
			for _, q in lf.parts do q.p.CFrame = q.home + lf.slide * e end
		end
	end
end)
