--!strict
-- Credits: the people whose work is in the game, shown to players on the Settings page's CREDITS section (20 Nov 2026;
-- main: "with attribution" means credited where players can see it). One shared list: every session that brings in
-- outside work appends its line here, in the form "<what>: <creator> (<pack or work>)". Plain names only: no links, no
-- handles with @, no logos. The licences behind each line are in the vault's Resources.md and the packs' vetting note.
local Credits = {}

-- { title, lines } in the order they show
Credits.SECTIONS = {
	{ title = "VFX", lines = {
		"VFX: coldd Development (Combat VFX Asset Pack)",
		"VFX: coldd Development (Crimson Slash Combat VFX)",
		"VFX: skaterstudios (100+ Combat VFX Asset Pack)",
		"VFX: artchive (Sword VFX: Heart & Butterfly)",
	} },
	{ title = "Animation", lines = {
		"Animation: robloxanimations (Katana Combat Pack)",
		"Animation: robloxanimations (Scythe Wielder)",
		"Animation: BZ1 Studios (Tactical Combat Animation Pack)",
	} },
	{ title = "Particles and textures", lines = {
		"Textures: Kenney (Particle Pack, Smoke Particles)",
		"Textures: binbun3d (Muzzle Flash VFX)",
		"Volumes: JangaFX (free VDB simulations)",
	} },
} :: { { title: string, lines: { string } } }

-- every line, flat, in order
function Credits.lines(): { string }
	local out = {}
	for _, s in Credits.SECTIONS do for _, l in s.lines do table.insert(out, l) end end
	return out
end

return Credits
