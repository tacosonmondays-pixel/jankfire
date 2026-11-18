--!strict
-- a weapon's picture in a ViewportFrame, the way the loadout screen shows it: the weapon's own model (or a utility
-- item's, or a grey crate for one that isn't on roblox yet) wearing YOUR skin, hat and wrap, scaled to the same size
-- every time (radius 3 studs) so one camera frames them all. (the builders are LoadoutUI's, its previewModel; the
-- match loadout screen, MatchLoadout.client, uses this module)
--   local vp, cam = GunPreview.viewport(parent, { Size = ..., Position = ... })
--   GunPreview.put(vp, cam, "redline")         -- builds it, poses it, frames it; again with the same looks does nothing
--   GunPreview.turn(vp, yaw)                   -- turns the shown model about its middle (a slow idle turn)
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local WeaponModels = require(Shared:WaitForChild("WeaponModels")) :: any
local Roster = require(Shared:WaitForChild("Roster")) :: any
local GunHats = require(Shared:WaitForChild("GunHats")) :: any
local GunSkins = require(Shared:WaitForChild("GunSkins")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any
local Tools = ReplicatedStorage:WaitForChild("JankfireTools")

local me = Players.LocalPlayer
local new = T.new
local GREY = T.MUTED

local P = {}

-- what you wear on a weapon
function P.looks(wid: string): (string, string, string, string)
	local w, md = WeaponModels.wrapFor(me, wid)
	return w or "default", md or "normal", GunHats.hatFor(me, wid) or "none", GunSkins.skinFor(me, wid) or "default"
end
function P.key(wid: string): string
	local w, md, hat, skin = P.looks(wid)
	return wid .. "|" .. w .. "|" .. md .. "|" .. hat .. "|" .. skin
end

-- ---------------------------------------------------------------- the models (LoadoutUI's)
local function shredderModel(skin: string?): Model?
	local src = (skin and Tools:FindFirstChild("Shredder@" .. skin)) or Tools:FindFirstChild("Shredder")
	if not src then return nil end
	local m = Instance.new("Model")
	local big: BasePart? = nil
	for _, d in src:GetDescendants() do
		if d:IsA("BasePart") and d.Transparency < 0.99 and d.Name ~= "SuckField" then
			local c = d:Clone()
			for _, x in c:GetChildren() do
				if not (x:IsA("SurfaceAppearance") or x:IsA("SpecialMesh") or x:IsA("Decal") or x:IsA("Texture")) then x:Destroy() end
			end
			c.Anchored = true
			c.Parent = m
			if not big or c.Size.Magnitude > big.Size.Magnitude then big = c end
		end
	end
	m.PrimaryPart = big
	return m
end
-- a weapon that isn't on roblox yet: a plain grey crate with one strap in its colour
local function crate(color: Color3): Model
	local m = Instance.new("Model")
	local function bx(size: Vector3, c: Color3, cf: CFrame): Part
		return new("Part", { Anchored = true, Size = size, Color = c, CFrame = cf, Material = Enum.Material.SmoothPlastic,
			TopSurface = Enum.SurfaceType.Smooth, BottomSurface = Enum.SurfaceType.Smooth }, m)
	end
	local box = bx(Vector3.new(3.6, 2.2, 2.2), Color3.fromRGB(84, 88, 98), CFrame.identity)
	for _, y in { -1.08, 1.08 } do for _, z in { -1.08, 1.08 } do bx(Vector3.new(3.7, 0.16, 0.16), Color3.fromRGB(46, 49, 58), CFrame.new(0, y, z)) end end
	bx(Vector3.new(0.5, 2.26, 2.26), color, CFrame.new(0.7, 0, 0))
	m.PrimaryPart = box
	return m
end
-- an item (the utility slot): its own model (ReplicatedStorage.JankfireItems), or a crate until that's there
local itemNames = { smoke = "x_smoke", frag = "x_frag", medkit = "x_medkit", bubble = "x_bubble" }
local function itemModel(id: string): Model?
	local lib = ReplicatedStorage:FindFirstChild("JankfireItems")
	local t = lib and lib:FindFirstChild(itemNames[id] or ("x_" .. id))
	if t and t:IsA("Model") then return t:Clone() end
	local e = Roster.byId[id]
	return crate(if e then e.color else GREY)
end

-- the model for weapon id with these looks, scaled to radius 3, and where its middle is (from its pivot)
function P.build(id: string, hat: string?, skin: string?, wrap: string?, mode: string?): (Model?, CFrame)
	local e = Roster.byId[id]
	local m: Model?
	if not e or not e.live then m = crate(if e then e.color else GREY)
	elseif e.slot == "utility" then m = itemModel(id)
	elseif id == "shredder" then m = shredderModel(if skin ~= "default" then skin else nil)
	else m = WeaponModels.build(id, 3, if skin ~= "default" then skin else nil) end
	if not m then return nil, CFrame.identity end
	for _, d in m:GetDescendants() do
		if d:IsA("BasePart") then d.Anchored = true; d.CastShadow = false end
	end
	local _, size = m:GetBoundingBox()
	local r = size.Magnitude / 2
	local want = if e and e.live then 3 else 2.3
	-- (its hat goes on after it is measured, so a hat never shrinks the weapon or moves it)
	local hm = nil
	if hat and hat ~= "none" and e and e.live then
		local ok, h = pcall(function()
			return if id == "shredder" then GunHats.attachToolCopy(m, Tools:FindFirstChild("Shredder") :: Instance, hat) else GunHats.attach(m, id, hat, 3, true)
		end)
		if ok then hm = h end
	end
	if r > 1e-3 then pcall(function() (m :: Model):ScaleTo((m :: Model):GetScale() * (want / r)) end) end
	if hm then hm.Parent = nil end
	local cf = m:GetBoundingBox()
	if hm then hm.Parent = m end
	if wrap and e and e.live then pcall(WeaponModels.wrap, m, wrap, mode) end
	return m, m:GetPivot():ToObjectSpace(cf)
end

-- ---------------------------------------------------------------- the frames
function P.viewport(parent: Instance, props: { [string]: any }): (ViewportFrame, Camera)
	local vp = new("ViewportFrame", {
		BackgroundTransparency = 1, Ambient = Color3.fromRGB(196, 199, 208), LightColor = Color3.fromRGB(255, 248, 240),
		LightDirection = Vector3.new(-0.5, -1, -0.7),
	}, parent)
	for k, v in props do (vp :: any)[k] = v end
	local cam = new("Camera", { FieldOfView = 40 }, vp)
	vp.CurrentCamera = cam
	return vp, cam
end

local shown: { [ViewportFrame]: { key: string, model: Model, rel: CFrame } } = setmetatable({}, { __mode = "k" }) :: any
local REST = CFrame.Angles(0.18, math.pi / 2, 0)
function P.put(vp: ViewportFrame, cam: Camera, wid: string): Model?
	local k = P.key(wid)
	local s = shown[vp]
	if s and s.key == k and s.model.Parent == vp then return s.model end
	if s then s.model:Destroy(); shown[vp] = nil end
	local w, md, hat, skin = P.looks(wid)
	local m, rel = P.build(wid, hat, skin, w, md)
	if not m then return nil end
	m:PivotTo(REST * rel:Inverse())
	m.Parent = vp
	shown[vp] = { key = k, model = m, rel = rel }
	-- (a narrower box steps the camera back so the long guns still fit across)
	local a = vp.AbsoluteSize
	local aspect = if a.Y > 0 then a.X / a.Y else 2
	cam.CFrame = CFrame.lookAt(Vector3.new(0, 0.6, 4.4 * math.max(1, 2.1 / math.max(aspect, 0.5))), Vector3.zero)
	return m
end
function P.turn(vp: ViewportFrame, yaw: number)
	local s = shown[vp]
	if not s or s.model.Parent ~= vp then return end
	s.model:PivotTo(CFrame.Angles(0, yaw, 0) * REST * s.rel:Inverse())
end
function P.clear(vp: ViewportFrame)
	local s = shown[vp]
	if s then s.model:Destroy(); shown[vp] = nil end
end

return P
