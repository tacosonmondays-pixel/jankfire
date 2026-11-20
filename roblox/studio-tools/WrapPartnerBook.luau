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
local FLOW_IDS = { -- (colour picture, glow mask): tools/roblox/wrap_flow.py, ids also in roblox/assets/wraps/assets.json
	stars = { 90506142503050, 138098836499581 }, glint = { 119853642092920, 119596018117654 },
	-- round 2 (20 Nov 2026)
	embers = { 89475906567636, 134982456858827 }, caustics = { 124130068259573, 134456976506565 },
	curtain = { 90098317954130, 99349511317536 }, pulses = { 128359552723712, 139339901162334 },
	scan = { 115697585005812, 136963496615589 }, rain = { 117697635998277, 75627737056988 },
	petals = { 72032965443587, 123477821102584 }, grid = { 85331936546926, 89070126560295 },
	blobs = { 137154093505268, 74046826322449 },
}
for name, ids in FLOW_IDS do
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
return "JankfireWrapPartner.metal and " .. #fl:GetChildren() .. " JankfireWrapFlow textures built"
