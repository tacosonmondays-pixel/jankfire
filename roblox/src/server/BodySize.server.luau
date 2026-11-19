--!strict
-- ONE BODY SIZE FOR EVERYONE (19 Nov 2026, the owner: "if theyre avatar is small turn them into r6? idk how to combat
-- pepole forcing sizes"). hits come from two fixed boxes per player (shared/Hitbox.luau), placed from the body's root:
-- the feet are taken as the root less 3 studs (Hitbox.ROOT_UP, a standard R15 body). a scaled body moves its root: a
-- tiny avatar's root sits about 1.5 studs lower, so its box sinks into the floor and a shot at its visible head goes over
-- it; a huge one's box floats over its legs. a tiny body is also hard to see. so on every spawn an R15 body is put back
-- to the standard size, keeping its look (clothes, accessories, face, colours, animations, body parts):
--   its HumanoidDescription gets HeightScale / WidthScale / DepthScale / HeadScale = 1, BodyTypeScale = 0 and
--   ProportionScale = 0 (Roblox's classic proportions), applied on the server (Humanoid:ApplyDescription) once the
--   appearance has loaded
--   a body still out of size after that (a package whose own parts are tiny or huge: its root not within ROOT_OK of
--   Hitbox.ROOT_UP over its feet) gets Roblox's standard torso, arms and legs too; the head and everything else stay
--   the resize moves the root, so the anti-cheat is told it's a server move (TeleportT) with a short ACGrace
-- accessories never change who gets hit: hits are the fixed boxes, never the parts
-- R6 is one size already and stays allowed (the owner's rule, 18 Nov): left alone
-- everywhere, the hub too: one body all the time, so nobody changes size between the hub and a match
-- Studio: ServerStorage.JankBodyTest: "fit" (a Model: the same fix on a stand-in; answers the measure after), "measure"
-- (a Model: its root over its feet, its scales), "make" (a scale table: a stand-in R15 body built with those scales)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local ROOT_UP = 3 -- studs: Hitbox.ROOT_UP, the root over the feet on a standard R15 body
local ROOT_OK = 0.45 -- studs either way still counts as the standard body
local STANDARD = { HeightScale = 1, WidthScale = 1, DepthScale = 1, HeadScale = 1, BodyTypeScale = 0, ProportionScale = 0 }
local PARTS = { "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg" }

-- the root's height over the feet, as the Humanoid stands it (HipHeight + half the root)
local function rootUp(ch: Model): number?
	local hum = ch:FindFirstChildOfClass("Humanoid")
	local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
	if not hum or not root then return nil end
	return hum.HipHeight + root.Size.Y / 2
end

local function scalesOf(d: HumanoidDescription): { [string]: number }
	local out = {}
	for k in STANDARD do out[k] = (d :: any)[k] end
	return out
end

local function standard(d: HumanoidDescription): boolean
	for k, v in STANDARD do
		if math.abs(((d :: any)[k] :: number) - v) > 1e-3 then return false end
	end
	return true
end

local busy: { [Model]: boolean } = {}
-- put one R15 body back to the standard size. answers what it did: "r6", "ok" (it was standard), "scaled", "parts"
-- (scaled, then the standard torso/arms/legs too), or nil + why
local function fit(ch: Model): (string?, string?)
	local hum = ch:FindFirstChildOfClass("Humanoid")
	if not hum then return nil, "no humanoid" end
	if hum.RigType ~= Enum.HumanoidRigType.R15 then return "r6", nil end
	if busy[ch] then return nil, "busy" end
	busy[ch] = true
	local ok, res, why = pcall(function(): (string?, string?)
		local d = hum:GetAppliedDescription()
		local did = "ok"
		if not standard(d) then
			for k, v in STANDARD do (d :: any)[k] = v end
			hum:ApplyDescription(d)
			did = "scaled"
		end
		local up = rootUp(ch)
		if up and math.abs(up - ROOT_UP) > ROOT_OK then
			local d2 = hum:GetAppliedDescription()
			for _, k in PARTS do (d2 :: any)[k] = 0 end
			hum:ApplyDescription(d2)
			did = "parts"
		end
		return did, nil
	end)
	busy[ch] = nil
	if not ok then return nil, tostring(res) end
	return res, why
end

local function spawned(p: Player, ch: Model)
	-- (the appearance loads after the body: wait for it, ten seconds at most)
	local t0 = os.clock()
	while p.Parent and p.Character == ch and not p:HasAppearanceLoaded() and os.clock() - t0 < 10 do task.wait(0.1) end
	if p.Character ~= ch or not ch.Parent then return end
	for try = 1, 3 do
		local before = rootUp(ch)
		local did, why = fit(ch)
		if did then
			if did == "scaled" or did == "parts" then
				p:SetAttribute("TeleportT", os.clock()) -- (a server move: the anti-cheat starts afresh from here)
				p:SetAttribute("ACGrace", os.clock() + 1.5)
				print(("[jankfire] body size: %s %s (root over feet %.2f -> %.2f)"):format(p.Name, did, before or -1, rootUp(ch) or -1))
			end
			return
		end
		if why == "busy" or p.Character ~= ch or not ch.Parent then return end
		warn(("[jankfire] body size: %s not fitted yet (%s), try %d"):format(p.Name, tostring(why), try))
		task.wait(1)
	end
end

local function added(p: Player)
	p.CharacterAdded:Connect(function(ch: Model) spawned(p, ch) end)
	if p.Character then task.spawn(spawned, p, p.Character) end
end
for _, p in Players:GetPlayers() do task.spawn(added, p) end
Players.PlayerAdded:Connect(added)

-- ------------------------------------------------------------------ Studio tests
if RunService:IsStudio() then
	local old = ServerStorage:FindFirstChild("JankBodyTest")
	if old then old:Destroy() end
	local fn = Instance.new("BindableFunction")
	fn.Name = "JankBodyTest"
	local function measure(ch: Model): any
		local hum = ch:FindFirstChildOfClass("Humanoid")
		local root = ch:FindFirstChild("HumanoidRootPart") :: BasePart?
		if not hum or not root then return nil end
		-- the feet as the parts have them (the lowest point of any limb) against the box's feet (root less ROOT_UP)
		local low = math.huge
		for _, d in ch:GetDescendants() do
			if d:IsA("BasePart") and d ~= root and d.Parent == ch then
				low = math.min(low, d.Position.Y - d.Size.Y / 2)
			end
		end
		local ok, d = pcall(function() return hum:GetAppliedDescription() end)
		return { rootUp = rootUp(ch), feetGap = (root.Position.Y - ROOT_UP) - low, rig = hum.RigType.Name,
			scales = if ok then scalesOf(d) else nil }
	end
	fn.OnInvoke = function(op: any, a: any): any
		if op == "fit" then
			local did, why = fit(a)
			return { did = did, why = why, after = measure(a) }
		elseif op == "measure" then
			return measure(a)
		elseif op == "make" then
			local d = Instance.new("HumanoidDescription")
			for k, v in (a or {}) :: any do (d :: any)[k] = v end
			local m = Players:CreateHumanoidModelFromDescription(d, Enum.HumanoidRigType.R15)
			m.Name = "JankBodyStandIn"
			return m
		end
		return nil
	end
	fn.Parent = ServerStorage
end
