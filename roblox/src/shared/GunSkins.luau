--!strict
-- WEAPON SKINS (the web game's COSMETICS.model + SKINS_2, rebuilt as Roblox kit models, 16 Nov 2026): a skin is a
-- whole other body for one weapon, from a crate. Its model is ReplicatedStorage.JankfireSkins.<skin id> (attribute
-- Weapon = the weapon it dresses, FileLo / FileHi = its file bounds), built by tools/roblox/gun_set.py SKINS and put
-- there by PolishBackup.WeaponImport W.skins(). Every skin keeps its weapon's spots, grip and moving pieces, so the
-- hold, the reloads, the wraps and the hats work on it unchanged (tools/roblox/gunskin_kit.py, the contract).
-- The names and rarities are LootTable.SKINS (the loot session's); this module only finds and reads them.
-- What a player wears: the "Skins" attribute the server keeps ("ar=ar_toy;katana=katana_bokken"), like "Wraps".
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GunSkins = {}

-- the skin's model, if it is in the place and dresses this weapon
function GunSkins.template(wid: string, id: string?): Model?
	if type(id) ~= "string" or id == "" or id == "default" then return nil end
	local lib = ReplicatedStorage:FindFirstChild("JankfireSkins")
	local m = lib and lib:FindFirstChild(id)
	if m and m:IsA("Model") and m:GetAttribute("Weapon") == wid then return m end
	return nil
end

-- a skin with no model that only changes its weapon's effects (18 Nov, shop-gui: the Shadow Cross, the Blood Cross in
-- purple; the Blood Cross is your own hand, nothing to dress): its LootTable.SKINS row has effectOnly = true. it's worn
-- like any skin (the "Skins" attribute), the gun drawn is the plain one (skinFor: no template), and the weapon's own
-- effects read the attribute (client/BloodCrossFx). the list is here, plain data: no require of another module and no
-- loop over the catalogue (18 Nov: a lazy require of LootTable from here was the suspect in a menu report). LootTable's row
-- carries effectOnly = true for the pools and the shop; keep the two in step
GunSkins.EFFECT_ONLY = { bloodcross_shadow = "bloodcross" } :: { [string]: string }
function GunSkins.effectOnly(wid: string, id: any): boolean
	return type(id) == "string" and GunSkins.EFFECT_ONLY[id] == wid
end

-- every skin in the place for one weapon (ids, sorted): its models, and its effect-only skins
function GunSkins.forWeapon(wid: string): { string }
	local out = {}
	local lib = ReplicatedStorage:FindFirstChild("JankfireSkins")
	if lib then
		for _, m in lib:GetChildren() do
			if m:IsA("Model") and m:GetAttribute("Weapon") == wid then table.insert(out, m.Name) end
		end
	end
	for id, w in GunSkins.EFFECT_ONLY do
		if w == wid and not table.find(out, id) then table.insert(out, id) end
	end
	table.sort(out)
	return out
end

-- a skin id that exists in the place for that weapon (a model, or effect-only)
function GunSkins.valid(wid: string, id: any): boolean
	return type(id) == "string" and (GunSkins.template(wid, id) ~= nil or GunSkins.effectOnly(wid, id))
end

-- a player's skin on one weapon (nil = the plain gun), from the "Skins" attribute the server keeps
function GunSkins.skinFor(p: Player?, wid: string): string?
	-- (a classic mode's look, Modes.luau: gun game's last rung and spoons & grapples put every knife in the spoon look,
	-- WeaponModels' "spoon": JankfireWeapons.w_spoon, never a skin of the catalog)
	if wid == "knife" and p and p:GetAttribute("SpoonLook") then return "spoon" end
	local s = p and p:GetAttribute("Skins")
	if type(s) ~= "string" then return nil end
	for w, id in string.gmatch(s, "([%w_]+)=([%w_]+)") do
		if w == wid then return if GunSkins.template(wid, id) then id else nil end
	end
	return nil
end

return GunSkins
