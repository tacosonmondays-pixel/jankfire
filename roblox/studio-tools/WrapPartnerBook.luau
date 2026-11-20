-- WrapPartnerBook: run in Studio (Edit) through execute_luau, then save. Builds ReplicatedStorage.JankfireWrapPartner
-- and ReplicatedStorage.JankfireWrapFlow (below). JankfireWrapPartner holds
-- the SurfaceAppearances a wrap's PARTNER is made from (docs/WRAP-TEXTURES.md "Normal and reverse"; shared/WrapPartners
-- says which wraps take which). SurfaceAppearance maps are PluginSecurity, so this can't happen while playing.
--   metal: a satin anodised metal. White colour map (WeaponModels.wrap tints it with the wrap's partner colour through
--          Color), metalness 0.85, roughness 0.4. The maps are the wrap book's shared constant images
--          (tools/roblox/wrap_upload.py const_file: const_metal_100 doubles as a plain white picture).
local RS = game:GetService("ReplicatedStorage")
local f = RS:FindFirstChild("JankfireWrapPartner")
if not f then
	f = Instance.new("Folder")
	f.Name = "JankfireWrapPartner"
	f.Parent = RS
end
local old = f:FindFirstChild("metal")
if old then old:Destroy() end
local s = Instance.new("SurfaceAppearance")
s.Name = "metal"
s.ColorMap = "rbxassetid://95597645833170" -- const_metal_100.png: 8 x 8 white
s.MetalnessMap = "rbxassetid://117290716005650" -- const_metal_085.png
s.RoughnessMap = "rbxassetid://86227588438345" -- const_rough_040.png
s.Parent = f
-- the moving wraps' Textures (client/WrapAnim, WRAP FLOW): a game script can't set a Texture's pictures while playing
-- ("cannot write EmissiveMaskContent", 20 Nov), so they are made here and cloned there. Pictures from
-- tools/roblox/wrap_flow.py: a colour picture (white light, alpha) and its glow mask
local fl = RS:FindFirstChild("JankfireWrapFlow")
if not fl then
	fl = Instance.new("Folder")
	fl.Name = "JankfireWrapFlow"
	fl.Parent = RS
end
for name, ids in { stars = { 90506142503050, 138098836499581 }, glint = { 119853642092920, 119596018117654 } } do
	local o = fl:FindFirstChild(name)
	if o then o:Destroy() end
	local t = Instance.new("Texture")
	t.Name = name
	t.ColorMapContent = Content.fromUri("rbxassetid://" .. ids[1])
	t.EmissiveMaskContent = Content.fromUri("rbxassetid://" .. ids[2])
	t.EmissiveStrength = 2
	t.ZIndex = 2
	t.Parent = fl
end
return "JankfireWrapPartner.metal and JankfireWrapFlow.stars / .glint built"
