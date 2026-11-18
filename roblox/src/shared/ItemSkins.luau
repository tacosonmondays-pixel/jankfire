--!strict
-- GADGET SKINS (owner, 18 Nov 2026: "Gadgets should have skins and be wrappable"): a skin is a whole other object that
-- does a gadget's job (the utility slot's item on G). Built by tools/roblox/item_skins.py on the gadgets' own contract
-- (the same grip, pivot and the nodes the game reads: lamp, pin, ring, lid*), put in the place by
-- tools/roblox/item_skin_import.luau as ReplicatedStorage.JankfireSkins.<id> with attributes Weapon = the gadget id and
-- Item = true. LootTable merges these rows into LootTable.SKINS, so a gadget skin is owned, rolled, sold and picked like
-- a weapon skin (GunSkins.template finds its model; the "Skins" attribute picks it: "frag=frag_keg").
-- id = { name, rarity, gadget id }
local ItemSkins = {}

ItemSkins.SKINS = {
	frag_keg = { "Powder Keg", "rare", "frag" },
	frag_lantern = { "Paper Lantern", "legendary", "frag" },
	medkit_doctorbag = { "Doctor's Bag", "rare", "medkit" },
	medkit_bento = { "Bento Box", "legendary", "medkit" },
	smoke_coffeepot = { "Camp Coffee Pot", "rare", "smoke" },
	smoke_censer = { "Incense Burner", "legendary", "smoke" },
	duck_decoy = { "Decoy Duck", "rare", "duck" },
	duck_origami = { "Origami Duck", "legendary", "duck" },
} :: { [string]: { string } }

-- the skins of one gadget (ids, sorted)
function ItemSkins.forGadget(gid: string): { string }
	local out = {}
	for id, row in ItemSkins.SKINS do if row[3] == gid then table.insert(out, id) end end
	table.sort(out)
	return out
end

return ItemSkins
