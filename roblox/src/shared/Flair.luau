--!strict
-- FLAIR: kill effects, emotes and grapple skins. what exists, how rare, which are free, and a drawn tile for the shop, the loot reel and
-- the equip screen. (17 Nov 2026, the owner: "Can we also have basic kill effects? Reference the rivals ones!! As well
-- as other games and maybe some emotes??"; research in the vault, Research\Kill effects and emotes.md; doc FLAIR.md)
--   kill:  what plays on a body when YOU get the kill (client/KillFx.luau draws it, server/FlairServer picks the real
--          killer's). one per player, not per weapon: the web game's own rule (shared/cosmetics.js "kill").
--          "none" is the default: the body falls apart as it always has.
--   emote: a short animation on the wheel (hold T). made with Studio's prompt-to-animation tool (generate_animation).
--   grapple: your grappling hook's rope and head, everyone sees it (the web game's COSMETICS.grapple; the look is
--          shared/GrappleLook.luau, drawn by client/GrappleSkins.client.luau). one per player.
-- (17 Nov, the owner via the main session: "kill effects and grapples should be gacha too!!" and the kill effects use the
-- web game's own list, same ids, names and rarities, restyled to the serious look: no text, no gore)
-- the shape is CardStyles' (the loot and shop hooks read both): TYPES, info(t, id) -> { name, rarity }?, ORDER[t],
-- CONTAINER (the Duffel Bag), forSale(t), picture(t, id, frame). free ones everybody owns; the rest are kept by the
-- loot save as gun-less types (Loot.owns(p, "kill", id), key = the id, like a weapon skin).
local F = {}

F.TYPES = { "kill", "emote", "grapple" }
F.TYPE_NAMES = { kill = "Kill Effect", emote = "Emote", grapple = "Grapple" }
F.CONTAINER = "bag"
F.SLOTS = 8 -- the emote wheel (Fortnite's current wheel has 8; a slot may repeat an emote)
F.DEFAULT = { kill = "none", grapple = "rope", emotes = { "wave", "hello", "salute", "point", "shrug", "cheer", "laugh", "dance" } }
F.COOLDOWN = 2 -- s between emotes (Rivals has none; spam guard)

export type Item = { type: string, id: string, name: string, rarity: string, vip: boolean? }
export type Kill = Item & { dur: number, tint: Color3 }
export type Emote = Item & { anim: string, len: number, loop: boolean, catalog: number }

-- rarity tints (the same as LootTable.RARITY; copied so this module needs nothing else)
F.RARITY_COLOR = {
	free = Color3.fromRGB(150, 156, 166), common = Color3.fromRGB(122, 178, 104), rare = Color3.fromRGB(78, 150, 226),
	epic = Color3.fromRGB(162, 108, 226), legendary = Color3.fromRGB(240, 178, 52),
	vip = Color3.fromRGB(255, 208, 72),
}
F.VIP_ONLY = "vip"

-- kill effects: id, name, rarity, seconds, the one colour it carries (tiles and the equip screen's chip). the web game's
-- twelve (ids, names, rarities as cosmetics.js has them) and the five built from the Rivals research, by rarity
local KILLS = {
	{ "none", "Gibs", "free", 0, Color3.fromRGB(150, 156, 166) }, -- (the body falls apart, as it always has: no blood)
	{ "confetti", "Confetti", "free", 1.3, Color3.fromRGB(236, 196, 96) },
	{ "dissolve", "Dissolve", "free", 1.3, Color3.fromRGB(214, 224, 236) },
	{ "grave", "Tombstone", "common", 1.5, Color3.fromRGB(132, 136, 142) },
	{ "cash", "Make It Rain", "common", 1.4, Color3.fromRGB(122, 150, 108) },
	{ "pixel", "Missing Texture", "rare", 1.2, Color3.fromRGB(176, 64, 156) },
	{ "balloon", "Balloons", "rare", 1.5, Color3.fromRGB(232, 206, 150) },
	{ "shatter", "Shatter", "rare", 1.0, Color3.fromRGB(176, 214, 236) },
	{ "ember", "Ember", "rare", 1.4, Color3.fromRGB(236, 120, 52) },
	{ "chicken", "Chickens", "epic", 1.5, Color3.fromRGB(238, 230, 212) },
	{ "bsod", "Blue Screen", "epic", 1.2, Color3.fromRGB(44, 82, 168) },
	{ "yeet", "Yeet", "epic", 1.3, Color3.fromRGB(220, 228, 240) },
	{ "ink", "Ink", "epic", 1.2, Color3.fromRGB(58, 62, 96) },
	{ "static", "Static", "epic", 1.0, Color3.fromRGB(150, 226, 255) },
	{ "ascend", "Ascend", "legendary", 1.5, Color3.fromRGB(255, 232, 186) },
	{ "duck", "Big Duck", "legendary", 1.5, Color3.fromRGB(236, 196, 72) },
	{ "blastzone", "Blast Zone", "legendary", 1.0, Color3.fromRGB(255, 210, 150) },
}
-- grapple skins (the web game's eight): id, name, rarity, the colour it carries
local GRAPPLES = {
	{ "rope", "Rope", "free", Color3.fromRGB(150, 112, 74) },
	{ "chain", "Chain", "common", Color3.fromRGB(150, 156, 166) },
	{ "candy", "Candy Cane", "common", Color3.fromRGB(214, 96, 96) },
	{ "plunger", "Plunger", "rare", Color3.fromRGB(168, 64, 60) },
	{ "vine", "Jungle Vine", "rare", Color3.fromRGB(98, 142, 82) },
	{ "laser", "Laser", "epic", Color3.fromRGB(96, 214, 236) },
	{ "sticky", "Sticky Hand", "epic", Color3.fromRGB(112, 188, 124) },
	{ "rainbow", "Rainbow", "legendary", Color3.fromRGB(240, 178, 52) },
}
-- emotes: id, name, rarity, animation, seconds, loops (one-shots end on their own; a loop runs till you move), and the
-- Roblox catalog emote it comes from (0: one of Roblox's default emotes, every avatar's own wave/cheer/laugh/dance).
-- (17 Nov 2026: our own generate_animation clips "looked really really bad" to the owner, so the free set is Roblox's
-- own free emotes now, every one of them free for everybody: the body animation inside each catalog emote, read with
-- InsertService:LoadAsset + KeyframeSequenceProvider (owned by Roblox, so they play in any game). never sold in the
-- shop (forSale skips free). a player's OWN bought Roblox emotes are the wheel's second page: FlairServer reads their
-- avatar's (StarterPlayer.UserEmotesEnabled), ids "rbx:<name>", never stored in this table)
-- (19 Nov, the owner: "are there free emotes we can take based of current dances memes or trends?" so the catalog's FREE
-- emotes, Roblox's and creators', sorted by favourites: every one loads with InsertService, holds one full-body R15
-- animation and no sound. kept: dance, meme and trend moves; left out: named routines (a song's, a creator's or another
-- game's dance), brands and other games' promos, anything its maker says was generated. our names are plain move names,
-- never the item's, a song's or a creator's. NEW (the 8th column): listed first, a NEW dot till you've looked. all loop:
-- they run till you move, like Stadium and Dance. R15 only, as every catalog emote)
local EMOTES = {
	{ "worm", "Worm", "free", "rbxassetid://84498222331140", 0.57, true, 135289014127213, true },
	{ "fancyfeet", "Fancy Feet", "free", "rbxassetid://77495170519075", 1.07, true, 111231750028642, true },
	{ "dab", "Dab", "free", "rbxassetid://82652632188662", 0.93, true, 75495806621404, true },
	{ "slidestep", "Slide Step", "free", "rbxassetid://120958185092458", 4.50, true, 127134199058487, true },
	{ "vibe", "Vibe", "free", "rbxassetid://95586320418454", 4.80, true, 86842013063636, true },
	{ "flow", "Flow", "free", "rbxassetid://85705364159065", 4.73, true, 132588088326391, true },
	{ "sway", "Sway", "free", "rbxassetid://115205039111295", 4.93, true, 132074824206003, true },
	{ "twostep", "Two Step", "free", "rbxassetid://118849962129838", 8.97, true, 105998066457327, true },
	{ "flap", "Flap", "free", "rbxassetid://96674218109731", 1.17, true, 117234325189261, true },
	{ "hypeclap", "Hype Clap", "free", "rbxassetid://114657319753837", 4.70, true, 106023350138548, true },
	{ "float", "Float", "free", "rbxassetid://119959221864675", 2.03, true, 100611991648476, true },
	{ "flex", "Flex", "free", "rbxassetid://100545491329125", 3.43, true, 117784532603203, true },
	{ "kickfeet", "Kicking Feet", "free", "rbxassetid://89333774081397", 5.00, true, 128118777898011, true },
	{ "shywave", "Shy Wave", "free", "rbxassetid://85649907654049", 3.18, true, 80325859644495, true },
	{ "applaud", "Applaud", "free", "rbxassetid://10713966026", 3.00, true, 5915779043, true },
	{ "wave", "Wave", "free", "rbxassetid://507770239", 1.75, false, 0 },
	{ "hello", "Hello", "free", "rbxassetid://10714359093", 1.77, false, 3576686446 },
	{ "salute", "Salute", "free", "rbxassetid://10714389988", 3.70, false, 3360689775 },
	{ "point", "Point", "free", "rbxassetid://10714395441", 2.30, false, 3576823880 },
	{ "shrug", "Shrug", "free", "rbxassetid://10714374484", 2.03, false, 3576968026 },
	{ "cheer", "Cheer", "free", "rbxassetid://507770677", 2.50, false, 0 },
	{ "laugh", "Laugh", "free", "rbxassetid://507770818", 3.29, false, 0 },
	{ "stadium", "Stadium", "free", "rbxassetid://10714356920", 3.63, true, 3360686498 },
	{ "tilt", "Tilt", "free", "rbxassetid://10714338461", 4.80, true, 3360692915 },
	{ "dance", "Dance", "free", "rbxassetid://507771019", 1.08, true, 0 },
}

-- EMOTE MUSIC (19 Nov, the owner: "si there a copyright free instriumental to go with it?"): one track per dance emote
-- from Roblox's own licensed audio library (its music partners' production music, cleared for use in Roblox
-- experiences), instrumental only (the no-voice rule), no melody of any trend song; its stretch starts on a beat.
-- client/EmoteMusic.client.luau plays it from the dancer (within ~40 studs, the MUSIC slider; others' under the
-- OTHERS' EMOTE MUSIC switch), never in a live match round.
--   emote id = { sound, the track's title as the library lists it, from (s), to (s), volume }
local MUSIC: { [string]: { any } } = {
-- MUSIC BEGIN
	-- (APM Music: the library's creator APMOfficial. each starts just before its first strong beat, measured silently
	-- 19 Nov; a stretch of up to 60 s: an emote ends by 30, so its loop seam is never reached)
	worm = { "rbxassetid://1835617224", "Check It Out (Nicolas Baudino)", 0.21, 60.21, 0.35 },
	fancyfeet = { "rbxassetid://1836160504", "Playful Electro Funk (AXS)", 0.00, 60.00, 0.35 },
	dab = { "rbxassetid://9047105533", "No Smoking (Afro Dizzy)", 0.04, 60.04, 0.35 },
	slidestep = { "rbxassetid://1835566917", "Soul Dancefloor (Mr De La Main)", 0.24, 60.24, 0.35 },
	vibe = { "rbxassetid://9043887091", "Lo-fi Chill A (Hip Hop Shop)", 0.28, 60.28, 0.45 },
	flow = { "rbxassetid://9047105108", "Moving Round The Block (Afro Dizzy)", 0.04, 60.04, 0.35 },
	sway = { "rbxassetid://9047104411", "Beach Cushions (Afro Dizzy)", 0.13, 60.13, 0.35 },
	twostep = { "rbxassetid://1841352457", "Discoball (a) (KPM Main Series)", 0.04, 60.04, 0.35 },
	flap = { "rbxassetid://1836665607", "Hot Potato 60 (John Stuart)", 0.45, 60.45, 0.35 },
	kickfeet = { "rbxassetid://1838941661", "Jolly Pranks (Yannick Kalfayan)", 0.34, 49.50, 0.35 },
	float = { "rbxassetid://9046622104", "Chill Groove to Gamma (a) (Lee Briskett)", 0.04, 59.50, 0.35 },
	hypeclap = { "rbxassetid://9046354385", "Wake Up Beat (Bastien Thomas Deshayes)", 0.45, 60.45, 0.35 },
	dance = { "rbxassetid://1839705126", "Hype (Samson Robin Penot)", 0.34, 60.34, 0.38 },
-- MUSIC END
}
F.MUSIC = {} :: { [string]: { sound: string, title: string, from: number?, to: number?, volume: number } }
for id, r in MUSIC do F.MUSIC[id] = { sound = r[1], title = r[2], from = r[3], to = r[4], volume = r[5] } end
function F.music(id: any): { sound: string, title: string, from: number?, to: number?, volume: number }?
	return if type(id) == "string" then F.MUSIC[id] else nil
end

F.ORDER = { kill = {}, emote = {}, grapple = {} } :: { [string]: { string } }
F.ITEMS = { kill = {}, emote = {}, grapple = {} } :: { [string]: { [string]: any } }
for _, r in KILLS do
	table.insert(F.ORDER.kill, r[1])
	F.ITEMS.kill[r[1]] = { type = "kill", id = r[1], name = r[2], rarity = r[3], dur = r[4], tint = r[5] }
end
for _, r in EMOTES do
	table.insert(F.ORDER.emote, r[1])
	F.ITEMS.emote[r[1]] = { type = "emote", id = r[1], name = r[2], rarity = r[3], anim = r[4], len = r[5], loop = r[6], catalog = r[7],
		new = r[8] == true }
end
for _, r in GRAPPLES do
	table.insert(F.ORDER.grapple, r[1])
	F.ITEMS.grapple[r[1]] = { type = "grapple", id = r[1], name = r[2], rarity = r[3], tint = r[4] }
end
-- PETS (18 Nov 2026, the owner: "Secret pets: when you find jank npc you'll have a mini scaled down version that follows
-- you. Another one could be the train, a slug made of hardware with his mask, it crawls using his hands from in game.
-- Those like fleshy meat dogs?"). one worn at a time; it follows you everywhere (client/Pets.client.luau draws every
-- player's, client-side). found only, never sold or rolled: NOT one of F.TYPES (the loot and shop hooks read those), and
-- owned in FlairServer's own save, not the loot save. how each is found is server/PetSecrets.server.luau's (no hint of
-- it anywhere on screen: the picker shows a pet you haven't found as a black silhouette, no name)
--   id, name, the gait the follower plays (client/PetRig.luau), how far behind you it keeps, ON: the pet's switch
-- (18 Nov, the owner: "Maybe just jank player pet for now". a pet that's off is parked: not in the PETS tab, its secret
-- doesn't run (PetSecrets), nothing can grant or wear it, nobody draws it; F.pet() doesn't know it. its model and code
-- stay: true here brings it back)
local PETS = {
	{ "mannequin", "Mini Mannequin", "waddle", 3.2, true }, -- (the hub egg's mannequin, knee high)
	{ "slug", "Train Slug", "crawl", 3.8, false },          -- (the Gut train's mask on a slug of steel plates; parked)
	{ "dog", "Meat Dog", "trot", 3.4, false },              -- (a pink sausage-link dog; parked)
}
F.PET_ORDER = {} :: { string }
F.PETS = {} :: { [string]: { id: string, name: string, gait: string, keep: number } }
F.PARKED = {} :: { [string]: boolean }
for _, r in PETS do
	if r[5] then
		table.insert(F.PET_ORDER, r[1])
		F.PETS[r[1]] = { id = r[1], name = r[2], gait = r[3], keep = r[4] }
	else
		F.PARKED[r[1]] = true
	end
end
function F.pet(id: any): { id: string, name: string, gait: string, keep: number }?
	return if type(id) == "string" then F.PETS[id] else nil
end

-- a grapple's look is in the place once its head model is (ReplicatedStorage.JankfireGrapples.<id>): until then it
-- neither rolls nor sells (the plain rope is always there)
function F.grappleReady(id: string): boolean
	if id == "rope" then return true end
	local f = game:GetService("ReplicatedStorage"):FindFirstChild("JankfireGrapples")
	return f ~= nil and f:FindFirstChild(id) ~= nil
end

function F.isType(t: any): boolean
	return t == "kill" or t == "emote" or t == "grapple"
end
function F.info(t: any, id: any): any
	if not F.isType(t) or type(id) ~= "string" then return nil end
	return F.ITEMS[t][id]
end
function F.isFree(t: string, id: string): boolean
	local i = F.info(t, id)
	return i ~= nil and i.rarity == "free"
end
function F.isVip(t: string, id: string): boolean
	local i = F.info(t, id)
	return i ~= nil and i.rarity == F.VIP_ONLY
end
-- what the shop may sell and a bag may roll: not free, not VIP-only, an emote's clip uploaded, a grapple's look in place
function F.forSale(t: string): { any }
	local out = {}
	for _, id in (F.ORDER[t] or {}) do
		local i = F.ITEMS[t][id]
		if i and i.rarity ~= "free" and i.rarity ~= F.VIP_ONLY and (t ~= "emote" or i.anim ~= "rbxassetid://0")
			and (t ~= "grapple" or F.grappleReady(id)) then
			table.insert(out, i)
		end
	end
	return out
end
-- the wheel's slots from the player attribute "Emotes" ("wave,salute,,,,,,")
function F.slotsOf(s: any): { string }
	local out = {}
	local parts = if type(s) == "string" then string.split(s, ",") else {}
	for i = 1, F.SLOTS do
		local id = parts[i] or ""
		out[i] = if F.info("emote", id) then id else ""
	end
	return out
end

-- ------------------------------------------------------------------ the tile (drawn from frames: no uploads)
-- a figure on a dark card, the effect's one colour on it; for an emote, the figure's arms show the move. the shop,
-- the loot reel and the equip screen call it on an empty frame of any size (it redraws when the size changes)
local function new(class: string, props: { [string]: any }, parent: Instance?): any
	local o = Instance.new(class)
	for k, v in props do (o :: any)[k] = v end
	if parent then o.Parent = parent end
	return o
end
local function round(o: Instance, r: number?) new("UICorner", { CornerRadius = if r then UDim.new(0, r) else UDim.new(0.5, 0) }, o) end
local PALE = Color3.fromRGB(196, 202, 212)

-- one limb: a rounded bar from (x0, y0) to (x1, y1) in the figure's 0..1 box
local BS = Vector2.new(64, 80) -- the figure box's pixel size while drawing (set by F.picture)
local function limb(p: Frame, x0: number, y0: number, x1: number, y1: number, w: number, c: Color3, z: number)
	local dx, dy = x1 - x0, y1 - y0
	local s = BS
	local len = math.sqrt((dx * s.X) ^ 2 + (dy * s.Y) ^ 2)
	local f = new("Frame", {
		BackgroundColor3 = c, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale((x0 + x1) / 2, (y0 + y1) / 2), Size = UDim2.fromOffset(len + w, w),
		Rotation = math.deg(math.atan2(dy * s.Y, dx * s.X)), ZIndex = z,
	}, p)
	round(f)
end

-- arm poses per emote: (shoulder -> elbow -> hand) for the left and right arm, in the figure box
local ARMS = {
	wave = { { 0.36, 0.34, 0.26, 0.5, 0.3, 0.64 }, { 0.64, 0.34, 0.8, 0.22, 0.78, 0.06 } },
	salute = { { 0.36, 0.34, 0.3, 0.5, 0.32, 0.64 }, { 0.64, 0.34, 0.78, 0.3, 0.6, 0.16 } },
	hello = { { 0.36, 0.34, 0.26, 0.5, 0.3, 0.64 }, { 0.64, 0.34, 0.8, 0.22, 0.78, 0.06 } },
	point = { { 0.36, 0.34, 0.3, 0.5, 0.32, 0.64 }, { 0.64, 0.34, 0.8, 0.36, 0.96, 0.36 } },
	shrug = { { 0.36, 0.34, 0.28, 0.5, 0.14, 0.42 }, { 0.64, 0.34, 0.72, 0.5, 0.86, 0.42 } },
	cheer = { { 0.36, 0.34, 0.28, 0.2, 0.26, 0.04 }, { 0.64, 0.34, 0.72, 0.2, 0.74, 0.04 } },
	laugh = { { 0.36, 0.34, 0.3, 0.5, 0.46, 0.56 }, { 0.64, 0.34, 0.7, 0.5, 0.54, 0.56 } },
	stadium = { { 0.36, 0.34, 0.24, 0.22, 0.16, 0.08 }, { 0.64, 0.34, 0.76, 0.22, 0.84, 0.08 } },
	tilt = { { 0.36, 0.34, 0.3, 0.5, 0.28, 0.66 }, { 0.64, 0.34, 0.7, 0.5, 0.72, 0.66 } },
	dance = { { 0.36, 0.34, 0.24, 0.42, 0.22, 0.26 }, { 0.64, 0.34, 0.74, 0.46, 0.8, 0.6 } },
	worm = { { 0.36, 0.34, 0.24, 0.46, 0.12, 0.5 }, { 0.64, 0.34, 0.76, 0.46, 0.88, 0.5 } },
	fancyfeet = { { 0.36, 0.34, 0.26, 0.44, 0.2, 0.58 }, { 0.64, 0.34, 0.74, 0.44, 0.8, 0.58 } },
	dab = { { 0.36, 0.34, 0.5, 0.24, 0.6, 0.16 }, { 0.64, 0.34, 0.82, 0.22, 0.98, 0.1 } },
	slidestep = { { 0.36, 0.34, 0.26, 0.48, 0.22, 0.62 }, { 0.64, 0.34, 0.76, 0.4, 0.86, 0.3 } },
	vibe = { { 0.36, 0.34, 0.24, 0.4, 0.3, 0.26 }, { 0.64, 0.34, 0.74, 0.46, 0.7, 0.6 } },
	flow = { { 0.36, 0.34, 0.3, 0.22, 0.4, 0.08 }, { 0.64, 0.34, 0.72, 0.5, 0.64, 0.62 } },
	sway = { { 0.36, 0.34, 0.3, 0.5, 0.36, 0.64 }, { 0.64, 0.34, 0.74, 0.2, 0.7, 0.04 } },
	twostep = { { 0.36, 0.34, 0.24, 0.44, 0.3, 0.56 }, { 0.64, 0.34, 0.76, 0.44, 0.7, 0.56 } },
	flap = { { 0.36, 0.34, 0.2, 0.3, 0.06, 0.24 }, { 0.64, 0.34, 0.8, 0.3, 0.94, 0.24 } },
	hypeclap = { { 0.36, 0.34, 0.3, 0.46, 0.48, 0.42 }, { 0.64, 0.34, 0.7, 0.46, 0.52, 0.42 } },
	float = { { 0.36, 0.34, 0.22, 0.42, 0.12, 0.5 }, { 0.64, 0.34, 0.78, 0.42, 0.88, 0.5 } },
	flex = { { 0.36, 0.34, 0.2, 0.34, 0.2, 0.18 }, { 0.64, 0.34, 0.8, 0.34, 0.8, 0.18 } },
	kickfeet = { { 0.36, 0.34, 0.3, 0.5, 0.4, 0.6 }, { 0.64, 0.34, 0.7, 0.5, 0.6, 0.6 } },
	shywave = { { 0.36, 0.34, 0.3, 0.5, 0.42, 0.56 }, { 0.64, 0.34, 0.7, 0.28, 0.66, 0.12 } },
	applaud = { { 0.36, 0.34, 0.3, 0.46, 0.48, 0.38 }, { 0.64, 0.34, 0.7, 0.46, 0.52, 0.38 } },
}

local function figure(box: Frame, body: Color3, arms: any, lean: number)
	local z = box.ZIndex + 1
	local head = new("Frame", { BackgroundColor3 = body, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(0.5 + lean * 0.5, 0.17 + math.abs(lean) * 0.3), Size = UDim2.fromScale(0.2, 0.2), ZIndex = z }, box)
	new("UIAspectRatioConstraint", {}, head)
	round(head)
	local w = math.max(3, BS.X * 0.11)
	limb(box, 0.5 + lean * 0.4, 0.33, 0.5, 0.62, w * 1.6, body, z) -- the body
	limb(box, 0.45, 0.62, 0.4, 0.95, w, body, z) -- legs
	limb(box, 0.55, 0.62, 0.6, 0.95, w, body, z)
	for _, a in arms do
		limb(box, a[1] + lean * 0.3, a[2], a[3], a[4], w * 0.85, body, z)
		limb(box, a[3], a[4], a[5], a[6], w * 0.85, body, z)
	end
end

local DOWN = { { 0.36, 0.34, 0.3, 0.5, 0.32, 0.64 }, { 0.64, 0.34, 0.7, 0.5, 0.68, 0.64 } }

local function drawKill(box: Frame, id: string, tint: Color3)
	local z = box.ZIndex + 1
	if id == "dissolve" then
		figure(box, PALE, DOWN, 0)
		-- the lower half gone to motes
		local cut = new("Frame", { BackgroundColor3 = Color3.fromRGB(22, 24, 30), BorderSizePixel = 0, Position = UDim2.fromScale(0, 0.62),
			Size = UDim2.fromScale(1, 0.4), ZIndex = z + 2 }, box)
		new("UIGradient", { Transparency = NumberSequence.new(1, 0), Rotation = 90 }, cut)
		for i = 1, 14 do
			local d = new("Frame", { BackgroundColor3 = tint, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.fromScale(0.3 + ((i * 37) % 41) / 100, 0.48 + ((i * 23) % 50) / 100 * 0.9),
				Size = UDim2.fromScale(0.035, 0.035), BackgroundTransparency = (i % 4) * 0.2, ZIndex = z + 3 }, box)
			new("UIAspectRatioConstraint", {}, d)
			round(d)
		end
	elseif id == "shatter" then
		figure(box, tint, DOWN, 0)
		for i = 1, 9 do
			local a = i * 40
			local r = 0.3 + (i % 3) * 0.08
			local sh = new("Frame", { BackgroundColor3 = tint, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
				Position = UDim2.fromScale(0.5 + math.cos(math.rad(a)) * r, 0.5 + math.sin(math.rad(a)) * r * 0.9),
				Size = UDim2.fromScale(0.07, 0.035), Rotation = a + 30, BackgroundTransparency = 0.15, ZIndex = z + 3 }, box)
			sh.Name = "Shard"
		end
		for _, l in { { 0.42, 0.2, 0.56, 0.5 }, { 0.56, 0.5, 0.46, 0.8 }, { 0.5, 0.36, 0.62, 0.42 } } do
			limb(box, l[1], l[2], l[3], l[4], 2, Color3.fromRGB(30, 34, 42), z + 3)
		end
	elseif id == "ember" then
		figure(box, Color3.fromRGB(40, 34, 32), DOWN, 0)
		local g = new("Frame", { BackgroundColor3 = tint, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = z, BackgroundTransparency = 0 }, box)
		new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.6, 0.75), NumberSequenceKeypoint.new(1, 0.35) }) }, g)
		for i = 1, 10 do
			local d = new("Frame", { BackgroundColor3 = if i % 3 == 0 then Color3.fromRGB(255, 196, 120) else tint, BorderSizePixel = 0,
				AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.25 + ((i * 31) % 50) / 100, 0.08 + ((i * 17) % 40) / 100),
				Size = UDim2.fromScale(0.03, 0.03), ZIndex = z + 3 }, box)
			new("UIAspectRatioConstraint", {}, d)
			round(d)
		end
	elseif id == "ink" then
		figure(box, Color3.fromRGB(14, 14, 20), DOWN, 0)
		for i = 1, 8 do
			local a = i * 45 + 10
			local r = 0.32 + (i % 2) * 0.1
			local b = new("Frame", { BackgroundColor3 = if i % 4 == 0 then tint else Color3.fromRGB(14, 14, 20), BorderSizePixel = 0,
				AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5 + math.cos(math.rad(a)) * r, 0.52 + math.sin(math.rad(a)) * r),
				Size = UDim2.fromScale(0.06 + (i % 3) * 0.025, 0.06 + (i % 3) * 0.025), ZIndex = z + 3 }, box)
			new("UIAspectRatioConstraint", {}, b)
			round(b)
		end
	elseif id == "ascend" then
		local col = new("Frame", { BackgroundColor3 = tint, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0), Position = UDim2.fromScale(0.5, 0),
			Size = UDim2.fromScale(0.5, 1), ZIndex = z }, box)
		new("UIGradient", { Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.55), NumberSequenceKeypoint.new(1, 1) }) }, col)
		local inner = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromScale(0, -0.08), Size = UDim2.fromScale(1, 1), ZIndex = z }, box)
		figure(inner, Color3.fromRGB(255, 246, 228), DOWN, 0)
	elseif id == "static" then
		local back = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromScale(0.06, 0), Size = UDim2.fromScale(1, 1), ZIndex = z }, box)
		figure(back, Color3.fromRGB(70, 120, 150), DOWN, 0)
		local front = new("Frame", { BackgroundTransparency = 1, Size = UDim2.fromScale(1, 1), ZIndex = z + 2 }, box)
		figure(front, tint, DOWN, 0)
		for _, y in { 0.24, 0.46, 0.7 } do
			new("Frame", { BackgroundColor3 = Color3.fromRGB(220, 244, 255), BorderSizePixel = 0, Position = UDim2.fromScale(0.16, y),
				Size = UDim2.fromScale(0.68, 0.025), ZIndex = z + 5 }, box)
			new("Frame", { BackgroundColor3 = Color3.fromRGB(22, 24, 30), BorderSizePixel = 0, Position = UDim2.fromScale(0.2, y + 0.03),
				Size = UDim2.fromScale(0.6, 0.045), ZIndex = z + 5 }, box)
		end
	else -- the default: a plain figure, slumped
		figure(box, PALE, DOWN, 0.06)
	end
end

-- a filled block at (x, y) (centre, 0..1), size (w, h) (0..1 of the box), turned r degrees, optionally rounded
local function block(p: Frame, x: number, y: number, w: number, h: number, c: Color3, z: number, r: number?, round_: number?): Frame
	local f = new("Frame", { BackgroundColor3 = c, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale(x, y), Size = UDim2.fromScale(w, h), Rotation = r or 0, ZIndex = z }, p)
	if round_ then new("UICorner", { CornerRadius = UDim.new(round_, 0) }, f) end
	return f
end
-- a round dot d wide (of the box's width)
local function dot(p: Frame, x: number, y: number, d: number, c: Color3, z: number): Frame
	return block(p, x, y, d, d * BS.X / BS.Y, c, z, 0, 0.5)
end
local function ring(p: Frame, x: number, y: number, d: number, c: Color3, thick: number, z: number): Frame
	local f = dot(p, x, y, d, c, z)
	f.BackgroundTransparency = 1
	new("UIStroke", { Color = c, Thickness = thick }, f)
	return f
end

-- the web game's kill effects, drawn (false: not one of these)
local function drawKillWeb(box: Frame, id: string, tint: Color3): boolean
	local z = box.ZIndex + 1
	local DARK = Color3.fromRGB(22, 24, 30)
	if id == "confetti" then
		figure(box, PALE, DOWN, 0)
		local cols = { Color3.fromRGB(240, 236, 226), tint, Color3.fromRGB(150, 160, 176), Color3.fromRGB(196, 150, 120) }
		for i = 1, 14 do
			block(box, 0.12 + ((i * 37) % 76) / 100, 0.05 + ((i * 29) % 40) / 100, 0.07, 0.035, cols[i % 4 + 1], z + 3, (i * 47) % 180)
		end
	elseif id == "grave" then
		local STONE = Color3.fromRGB(122, 126, 132)
		block(box, 0.5, 0.6, 0.56, 0.58, STONE, z, 0, 0.1)
		block(box, 0.5, 0.36, 0.56, 0.3, STONE, z, 0, 0.5)
		block(box, 0.5, 0.52, 0.3, 0.035, Color3.fromRGB(96, 100, 106), z + 1)
		block(box, 0.5, 0.6, 0.22, 0.035, Color3.fromRGB(96, 100, 106), z + 1)
		block(box, 0.5, 0.91, 0.84, 0.06, Color3.fromRGB(70, 74, 80), z + 1, 0, 0.5)
	elseif id == "cash" then
		figure(box, Color3.fromRGB(90, 96, 106), DOWN, 0)
		for i = 1, 8 do
			local f = block(box, 0.18 + ((i * 41) % 66) / 100, 0.1 + ((i * 23) % 70) / 100, 0.2, 0.09, tint, z + 3, (i * 53) % 90 - 45, 0.15)
			new("UIStroke", { Color = Color3.fromRGB(196, 214, 184), Thickness = 1 }, f)
		end
	elseif id == "pixel" then
		for i = 0, 5 do
			for j = 0, 7 do
				if (i + j) % 3 ~= 0 or (i * j) % 4 == 1 then
					block(box, 0.3 + i * 0.08, 0.18 + j * 0.09, 0.075, 0.085, if (i + j) % 2 == 0 then tint else DARK, z)
				end
			end
		end
		for i = 1, 6 do block(box, 0.12 + i * 0.13, 0.08 + (i % 3) * 0.05, 0.05, 0.055, if i % 2 == 0 then tint else DARK, z + 1) end
	elseif id == "balloon" then
		local inner = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromScale(0, 0.28), Size = UDim2.fromScale(1, 0.72), ZIndex = z }, box)
		local was = BS
		BS = Vector2.new(BS.X, BS.Y * 0.72)
		figure(inner, PALE, DOWN, 0)
		BS = was
		local cols = { Color3.fromRGB(240, 236, 226), tint, Color3.fromRGB(150, 160, 176) }
		for i, x in { 0.3, 0.5, 0.7 } do
			limb(box, x, 0.2, 0.5, 0.42, 1, Color3.fromRGB(200, 204, 212), z)
			dot(box, x, 0.14 + (i % 2) * 0.04, 0.26, cols[i], z + 2)
		end
	elseif id == "chicken" then
		for i, c in { { 0.3, 0.64, 1 }, { 0.68, 0.46, 0.8 } } do
			local x, y, k = c[1], c[2], c[3]
			dot(box, x, y, 0.3 * k, tint, z + i)
			dot(box, x + 0.13 * k, y - 0.12 * k, 0.16 * k, tint, z + i)
			block(box, x + 0.22 * k, y - 0.11 * k, 0.06 * k, 0.04 * k, Color3.fromRGB(214, 150, 70), z + i, 45)
			dot(box, x + 0.13 * k, y - 0.21 * k, 0.05 * k, Color3.fromRGB(176, 72, 66), z + i)
		end
	elseif id == "bsod" then
		local pnl = block(box, 0.5, 0.48, 0.86, 0.6, tint, z, 0, 0.04)
		new("UIStroke", { Color = Color3.fromRGB(16, 18, 22), Thickness = 2 }, pnl)
		block(box, 0.3, 0.32, 0.18, 0.08, Color3.fromRGB(226, 232, 244), z + 1)
		for i, w in { 0.6, 0.48, 0.54 } do
			block(box, 0.16 + w / 2, 0.46 + i * 0.07, w, 0.035, Color3.fromRGB(200, 210, 232), z + 1)
		end
		block(box, 0.5, 0.86, 0.3, 0.05, Color3.fromRGB(60, 64, 72), z, 0, 0.5)
	elseif id == "yeet" then
		local streak = block(box, 0.5, 0.58, 0.12, 0.76, tint, z)
		new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 0.2), NumberSequenceKeypoint.new(1, 1) }) }, streak)
		local inner = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromScale(0.3, -0.02), Size = UDim2.fromScale(0.4, 0.34), ZIndex = z + 2 }, box)
		local was = BS
		BS = Vector2.new(BS.X * 0.4, BS.Y * 0.34)
		figure(inner, PALE, DOWN, 0)
		BS = was
		for i = 1, 4 do block(box, 0.5 + (i - 2.5) * 0.12, 0.05, 0.03, 0.03, Color3.fromRGB(255, 244, 214), z + 3, 45) end
	elseif id == "duck" then
		dot(box, 0.44, 0.64, 0.7, tint, z)
		dot(box, 0.64, 0.3, 0.38, tint, z + 1)
		block(box, 0.86, 0.33, 0.16, 0.07, Color3.fromRGB(214, 128, 52), z + 2, 0, 0.5)
		dot(box, 0.69, 0.26, 0.06, DARK, z + 3)
		block(box, 0.24, 0.54, 0.18, 0.1, tint:Lerp(Color3.new(1, 1, 1), 0.2), z + 1, -30, 0.5)
	elseif id == "blastzone" then
		for i = 0, 7 do block(box, 0.5, 0.5, 0.05, 0.86, tint, z, i * 22.5, 0.5).BackgroundTransparency = 0.35 end
		dot(box, 0.5, 0.5, 0.42, Color3.fromRGB(255, 240, 220), z + 1)
		local inner = new("Frame", { BackgroundTransparency = 1, Position = UDim2.fromScale(0.62, 0.02), Size = UDim2.fromScale(0.34, 0.3), ZIndex = z + 2 }, box)
		local was = BS
		BS = Vector2.new(BS.X * 0.34, BS.Y * 0.3)
		figure(inner, Color3.fromRGB(90, 96, 106), DOWN, 0.2)
		BS = was
	else
		return false
	end
	return true
end

-- a grapple: its rope across the tile and its head at the top end
local function drawGrapple(box: Frame, id: string, tint: Color3)
	local z = box.ZIndex + 1
	local ROPE = { rope = Color3.fromRGB(150, 112, 74), chain = Color3.fromRGB(150, 156, 166), candy = Color3.fromRGB(236, 232, 226),
		plunger = Color3.fromRGB(150, 112, 74), vine = Color3.fromRGB(86, 126, 70), laser = Color3.fromRGB(160, 236, 248),
		sticky = Color3.fromRGB(112, 188, 124), rainbow = Color3.fromRGB(255, 255, 255) }
	local x0, y0, x1, y1 = 0.12, 0.92, 0.62, 0.38
	local len = math.sqrt(((x1 - x0) * BS.X) ^ 2 + ((y1 - y0) * BS.Y) ^ 2)
	local rope = new("Frame", { BackgroundColor3 = ROPE[id] or tint, BorderSizePixel = 0, AnchorPoint = Vector2.new(0.5, 0.5),
		Position = UDim2.fromScale((x0 + x1) / 2, (y0 + y1) / 2), Size = UDim2.fromOffset(len, if id == "laser" then 3 else 5),
		Rotation = math.deg(math.atan2((y1 - y0) * BS.Y, (x1 - x0) * BS.X)), ZIndex = z }, box)
	if id == "candy" or id == "rainbow" or id == "chain" then
		local cols = if id == "rainbow" then { Color3.fromRGB(226, 104, 104), Color3.fromRGB(236, 196, 96), Color3.fromRGB(110, 190, 120), Color3.fromRGB(96, 160, 226), Color3.fromRGB(164, 120, 226) }
			elseif id == "candy" then { Color3.fromRGB(236, 232, 226), Color3.fromRGB(206, 84, 84) }
			else { Color3.fromRGB(170, 176, 186), Color3.fromRGB(96, 100, 110) }
		local kp = {}
		local n = 8 -- (two keys a stripe plus the end: a ColorSequence holds at most 20)
		for i = 0, n - 1 do
			local c = cols[i % #cols + 1]
			table.insert(kp, ColorSequenceKeypoint.new(i / n, c))
			table.insert(kp, ColorSequenceKeypoint.new((i + 1) / n - 0.002, c))
		end
		table.insert(kp, ColorSequenceKeypoint.new(1, cols[(n - 1) % #cols + 1]))
		new("UIGradient", { Color = ColorSequence.new(kp) }, rope)
	end
	if id == "vine" then
		for i = 1, 4 do
			local t = i / 5
			block(box, x0 + (x1 - x0) * t + 0.04, y0 + (y1 - y0) * t, 0.1, 0.05, Color3.fromRGB(110, 160, 92), z + 1, -40, 0.5)
		end
	end
	local hx, hy = x1 + 0.1, y1 - 0.12
	if id == "rope" or id == "vine" then
		ring(box, hx, hy, 0.3, if id == "vine" then Color3.fromRGB(150, 112, 74) else Color3.fromRGB(116, 120, 128), 4, z + 2)
		block(box, hx - 0.12, hy + 0.06, 0.14, 0.14, Color3.fromRGB(22, 24, 30), z + 3)
	elseif id == "chain" then
		for i = -1, 1 do limb(box, x1, y1, hx + i * 0.12, hy - 0.16, 4, Color3.fromRGB(150, 156, 166), z + 2) end
	elseif id == "candy" then
		ring(box, hx, hy, 0.26, Color3.fromRGB(206, 84, 84), 5, z + 2)
		block(box, hx - 0.1, hy + 0.07, 0.16, 0.14, Color3.fromRGB(22, 24, 30), z + 3)
	elseif id == "plunger" then
		block(box, hx - 0.02, hy + 0.02, 0.32, 0.16, tint, z + 2, -45, 0.5)
	elseif id == "laser" then
		local g = dot(box, hx - 0.06, hy + 0.05, 0.26, tint, z + 2)
		g.BackgroundTransparency = 0.4
		dot(box, hx - 0.06, hy + 0.05, 0.1, Color3.fromRGB(230, 250, 255), z + 3)
	elseif id == "sticky" then
		dot(box, hx - 0.04, hy + 0.04, 0.22, tint, z + 2)
		for i = 0, 3 do
			local a = math.rad(-150 + i * 40)
			limb(box, hx - 0.04, hy + 0.04, hx - 0.04 + math.cos(a) * 0.2, hy + 0.04 + math.sin(a) * 0.16, 5, tint, z + 2)
		end
	elseif id == "rainbow" then
		for i = 0, 1 do block(box, hx - 0.04, hy + 0.03, 0.2, 0.2 * BS.X / BS.Y, tint, z + 2, i * 45) end
		dot(box, hx - 0.04, hy + 0.03, 0.08, Color3.fromRGB(255, 248, 226), z + 3)
	end
end

-- draw the tile into `frame` (cleared first). the frame keeps its own size, corner and background
function F.picture(t: string, id: string, frame: GuiObject)
	local i = F.info(t, id)
	local function draw()
		for _, c in frame:GetChildren() do if c.Name == "FlairPic" then c:Destroy() end end
		if not i then return end
		local s = frame.AbsoluteSize
		if s.X < 2 or s.Y < 2 then return end
		local holder = new("Frame", { Name = "FlairPic", BackgroundColor3 = Color3.fromRGB(22, 24, 30), BorderSizePixel = 0,
			Size = UDim2.fromScale(1, 1), ZIndex = frame.ZIndex, ClipsDescendants = true }, frame)
		round(holder, 6)
		-- the rarity's colour, a soft glow from below
		local glow = new("Frame", { BackgroundColor3 = F.RARITY_COLOR[i.rarity] or PALE, BorderSizePixel = 0, Size = UDim2.fromScale(1, 1), ZIndex = frame.ZIndex }, holder)
		new("UIGradient", { Rotation = 90, Transparency = NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.7, 0.92), NumberSequenceKeypoint.new(1, 0.7) }) }, glow)
		-- the figure in a square in the middle
		local side = math.min(s.X, s.Y) * 0.84
		BS = Vector2.new(side * 0.8, side)
		local box = new("Frame", { BackgroundTransparency = 1, AnchorPoint = Vector2.new(0.5, 0.5), Position = UDim2.fromScale(0.5, 0.52),
			Size = UDim2.fromOffset(side * 0.8, side), ZIndex = frame.ZIndex + 1 }, holder)
		if t == "kill" then
			if not drawKillWeb(box, id, i.tint) then drawKill(box, id, i.tint) end
		elseif t == "grapple" then drawGrapple(box, id, i.tint)
		else
			figure(box, PALE, ARMS[id] or DOWN, 0)
		end
	end
	draw()
	local con: RBXScriptConnection? = nil
	con = frame:GetPropertyChangedSignal("AbsoluteSize"):Connect(function()
		if not frame.Parent then if con then con:Disconnect() end return end
		draw()
	end)
end
F.preview = F.picture

return F
