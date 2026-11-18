--!strict
-- THE HIDDEN NPCS' BOOK (18 Nov 2026). The owner: "Perhaps the hidden NPCs including guy from hr can be rehidden around
-- hub areas? As well as the cast from [the JANKFIRE] story?" The web game hid five ☺ CORP employees in its maps
-- (shared/secrets.js: Gary, Dale, the Janitor, Mr. Smiles, Todd), each with an outfit, props, an idle and a chat that
-- tells one chapter of the lore; some hand you something the first time. Here they are hidden round the hub's areas
-- (workspace.Map.Lore, placed by ServerStorage.PolishBackup.LoreSpots), built by the web's own code (LoreRigs).
-- Finding one (walking up to them) is saved per player (LoreNPCs.server); the count shows on your profile card only.
-- Their lines are the web's, trimmed: short, lowercase, nothing Roblox wouldn't show. They are said in a speech bubble
-- over their head (in the world, not on the HUD): the opening beat when you come near, the next beat each time you
-- press TALK, the gift line the first time you find them.
-- entry: name, title, kind ("lore" | "story"), voice (unused for now: the web's talk-blip pitch), gift, beats (each a
-- list of lines said one after another), got (the first find), again (later visits)
-- gift: { kind = "grapple" | "kill" | ..., id = "plunger", orElse = "bag" } (a cosmetic; a container instead if you
-- own it already), or { container = "crate" | "bag" | "spray" }, or nil (they only talk)
local L = {}

export type Gift = { kind: string?, id: string?, orElse: string?, container: string? }
export type Entry = {
	id: string, name: string, title: string, kind: string, gift: Gift?,
	beats: { { string } }, got: { string }, again: { string },
	idle: string?, clips: { string }?, greet: string?,
}

-- reach (the web's SECRET.reach / up / down, metres, x 3 studs): finding one needs your body this close to them
L.REACH, L.UP, L.DOWN = 8.4, 7.2, 7.8

L.ORDER = { "gary", "dale", "janitor", "smiles", "todd", "hr",
	"auntie", "lumps", "gordo", "mina", "sharon", "dumpling", "pallet_jack", "eotm", "overtime" } :: { string }
-- the board of directors (the five cats): finding all five gives the secret title BOARD MEMBER (LoreNPCs)
L.CATS = { "cat_biscuit", "cat_beans", "cat_gravy", "cat_meatloaf", "cat_gremlin" } :: { string }
-- PARKED (owner, 18 Nov 2026: "No cats please"). false: they aren't built (LoreSpots), don't count, can't be found and
-- BOARD MEMBER is never granted (its CardStyles row stays, so anyone who has it keeps it; ProfileUI hides an unowned
-- secret). Their models, rigs, spots and lines stay in the repo: true + LoreSpots.build(L.CATS) brings them back
L.CATS_ON = false
if L.CATS_ON then for _, id in L.CATS do table.insert(L.ORDER, id) end end
-- does a find of this one count? (only what's in ORDER: a parked one doesn't)
function L.counts(id: any): boolean
	return type(id) == "string" and table.find(L.ORDER, id) ~= nil
end

L.NPCS = {
	gary = {
		id = "gary", name = "GARY", title = "regional manager (the region is this room)", kind = "lore", gift = nil,
		beats = {
			{ "oh. a visitor. nobody comes to the site office. that is why i picked it.", "i'm gary. regional manager. the region is this room." },
			{ "the merger. ☺ CORP bought the government at an auction. it was the only bidder.", "then it merged with everyone else. you didn't sign anything? you breathed near a form. that counts now.", "so we're all employees. me, you, the bots. the bots got better benefits." },
			{ "it's fine. i've been fine for nineteen years.", "i get one day off a year. it's always during a match." },
			{ "productivity. we tried spreadsheets. people lied in the spreadsheets.", "you can't lie about a headshot. so the job is matches now.", "you respawn in a body from the stockroom. returned mannequins. that's why your knee bends wrong." },
			{ "close the door on your way out.", "there's no door. close it anyway." },
		},
		got = { "i'd love to give you something. the gift budget got restructured into a firm handshake.", "*he shakes your hand. it's limp.*" },
		again = { "still no gift budget. it's in a meeting. so am i." },
	},
	dale = {
		id = "dale", name = "DALE", title = "vending machine guy", kind = "lore", gift = { container = "spray" },
		beats = {
			{ "careful. she bites.", "that's a Jank Cola machine. i fix them. been fixing this one since tuesday. not sure which tuesday." },
			{ "☺ CORP started as one of these. one vending machine, in a mall. it never gave change.", "it kept the change for forty years. it bought the mall. then the town. then the idea of money.", "now it's everywhere and i fix it. it doesn't thank me. i don't thank it either." },
			{ "the machine stopped taking money. money was too predictable.", "so wages are containers now. crates, duffel bags, spray cans.", "that's the whole economy. the surprise. you're welcome." },
			{ "the cola's 0% water now. i don't know what it is. i don't ask.", "*he hits the machine with the wrench. something falls out.*" },
		},
		got = { "here. it fell out while i was hitting her. don't tell anyone." },
		again = { "one per customer. she counts. she always counts." },
	},
	janitor = {
		id = "janitor", name = "THE JANITOR", title = "has seen things", kind = "lore", gift = { kind = "grapple", id = "plunger", orElse = "bag" },
		beats = {
			{ "*squeak. squeak.*", "careful. floor's wet. i mop it anyway. job's a job." },
			{ "the edge of the map? ☺ CORP sold it. \"premium negative space\". investors love it.", "every bad quarter they repossess a bit more ground. every night it's a little closer.", "i had a house out there. now it's a premium feature." },
			{ "you fall in, you're still employed. you just lose the dental.", "some of them wave. don't wave back. it gets them excited." },
			{ "i've seen the board of directors. little furry executives. they sleep on everything.", "don't tell them i said furry." },
			{ "since the carpet had a colour. you could pick it, back then.", "i picked beige. look how that turned out." },
		},
		got = { "take this. my plunger. it sticks to anything.", "don't ask where it's been." },
		again = { "*squeak. squeak.* the floor's still wet." },
	},
	smiles = {
		id = "smiles", name = "MR. SMILES", title = "mascot (retired)", kind = "lore", gift = { kind = "kill", id = "balloon", orElse = "bag" },
		beats = {
			{ "oh! a fan! nobody climbs up here. that's the point of up here.", "i used to be the mascot. the big happy face of ☺ CORP. now i'm a guy in a hot suit on a hook." },
			{ "they made fun mandatory. if fun is mandatory it's a job.", "i did the maths. the maths broke me." },
			{ "take the head off? no.", "there's nothing under there anymore. it's smiles all the way down." },
			{ "nobody's seen the founder. the plaque just says OUR FOUNDER.", "i was in the room for the merger vote. the founder walked across the keyboard.", "it typed yyyyyyyyyyyy. legally that's a yes.", "the founder is a cat." },
			{ "the whole board of directors is cats. they hide all over the place. shelves. awnings. boxes, mostly.", "find them and pet them. that's how you get promoted." },
		},
		got = { "here. my balloons. anyone you get floats away.", "last fun thing i own. take care of it." },
		again = { "go pet the board. they're waiting. they're always waiting." },
	},
	todd = {
		id = "todd", name = "TODD", title = "intern (year 40)", kind = "lore", gift = { container = "crate" },
		beats = {
			{ "oh hey! sorry, i'm on a deadline. the deadline was in 1986.", "i'm todd. i'm the intern. i'm also the whole physics department. they downsized it to me." },
			{ "i wrote gravity on my first day. from memory. i was nervous.", "the bananas? i copied the floor code onto the banana. that's why you slip.", "this purple and black square is where i ran out of textures. i'm patching it. with hope." },
			{ "stopping things was a paid add-on. we never bought it. so things just keep going.", "if you grapple fast enough you can leave the quarter. please don't. accounting gets weird." },
			{ "unpaid! well. paid in exposure. it's very exposed up here.", "my lanyard says INTERN. the lanyard is also an intern." },
		},
		got = { "oh! take this crate. it's from my onboarding kit. i never opened it. i was scared." },
		again = { "back to work. the floor isn't going to code itself. it is, actually. badly." },
	},
	-- (not found by walking up: he finds you. HrGuy.server: rare, on the back lot, only when you're alone. "found" =
	-- he had you once. his lines are the story's; he says one over his head as he gets you)
	hr = {
		id = "hr", name = "TALL GUY FROM HR", title = "human resources (on loan)", kind = "hr", gift = nil,
		beats = { { "he just wants a quick word." } },
		got = { "if you could just sign here, i could go." },
		again = { "this is a safe space. it's very large. it's mostly negative." },
	},
	-- THE STORY CAST (OVERDUE, shared/story/content/cast_main.js and cast_districts.js): their own Blender models on
	-- their code skeletons. no gift: finding them counts. lines: the cast bible's samples, trimmed. idle: the web's
	-- actors.js idle style; clips: gestures now and then (the web's CLIPS); greet: the gesture when you first come near
	auntie = {
		id = "auntie", name = "AUNTIE SPREADSHEET", title = "keeps the Bottom's books, in crayon", kind = "story",
		idle = "write", clips = { "nod", "think" }, greet = "wave",
		beats = { { "you hungry? sit down. you're a debit until you've eaten." }, { "write it down. if it isn't written down, they'll say it didn't happen." },
			{ "that doesn't reconcile. nothing they send us reconciles." }, { "i've audited worse. i can't think of when." }, { "stairs. why is it always stairs." } },
		got = { "two hundred and forty-four quarters of back pay. for a job none of us had." },
		again = { "every debt they collect is a lie with a signature on it. i want the signatures." },
	},
	lumps = {
		id = "lumps", name = "LUMPS", title = "the Bottom's muscle, cries at sunsets", kind = "story",
		idle = "sway", clips = { "cry", "shrug" }, greet = "wave",
		beats = { { "sorry. *thud*. sorry." }, { "i'm not crying. it's the sunset. it does this." },
			{ "nine hundred and ninety-eight. nine hundred and ninety-nine. that's the stairs." },
			{ "you came out of a machine. so what. i came out of a woman who sells soup." }, { "i'll carry it. i'll carry you if you want. i carry nan sometimes." } },
		got = { "that's a lot of stairs. good for the legs." },
		again = { "sorry. *thud*. sorry." },
	},
	gordo = {
		id = "gordo", name = "WEE GORDO", title = "the Bottom's planner, born late", kind = "story",
		idle = "fidget", clips = { "point", "think" }, greet = "nod",
		beats = { { "right. listen. three ways in, two ways out, one of them's on fire." }, { "plan b is plan a but faster." },
			{ "a deal is a leash you sign yourself." }, { "every company in this city killed the world and then opened a gift shop." },
			{ "you came out of their machine with their barcode. so forgive me if i check your pockets." } },
		got = { "he means steal a car. and watch out for interns." },
		again = { "ok. now the hard part." },
	},
	mina = {
		id = "mina", name = "MINA", title = "waited at the school gate", kind = "story",
		idle = nil, clips = { "late", "nod" }, greet = "late",
		beats = { { "you're late." }, { "i waited at the gate till the teacher made me go. then i waited in the vents. then i waited here." },
			{ "i'm seventy. you're twenty-two and made of plastic. we'll call it even." }, { "don't you dare apologise. you were coming. i know you were coming." } },
		got = { "you're late." },
		again = { "you don't remember me. that's all right. i remember enough for both of us." },
	},
	sharon = {
		id = "sharon", name = "BIG SAUCE SHARON", title = "runs the soup kitchen", kind = "story",
		idle = "hold", clips = { "stomp", "nod" }, greet = "nod",
		beats = { { "eat. you're plastic. eat anyway." }, { "you'll take the red pot and you'll not spill it." },
			{ "soup for medicine. it's a fair trade. it's the only fair trade on this hill." } },
		got = { "if you spill that i'll ladle you." },
		again = { "eat. you're plastic. eat anyway." },
	},
	dumpling = {
		id = "dumpling", name = "DUMPLING", title = "a kid who follows you about", kind = "story",
		idle = "fidget", clips = { "wave", "shock" }, greet = "shock",
		beats = { { "ghost! ghost! you came out the machine! do it again!" }, { "auntie says don't touch your knee. i'm not touching it. i'm looking at it." },
			{ "what's a wednesday?" }, { "i'm doing sinner-gee. it's when you do stuff together." } },
		got = { "ghost! do it again!" },
		again = { "ghost! do it again!" },
	},
	pallet_jack = {
		id = "pallet_jack", name = "PALLET JACK", title = "the Bottom's delivery man", kind = "story",
		idle = "hold", clips = { "flex", "nod" }, greet = "wave",
		beats = { { "go on. it's not heavy." }, { "you're about forty kilos, light one. lightest friend i've got." },
			{ "it's not heavy. it's just all at once." }, { "hold that for me. it's about three hundred grams. i'll want it back." } },
		got = { "that pot's ninety. the soup's another sixty. the worry's free." },
		again = { "bev says i've got ten years left in the knees. she said that ten years ago." },
	},
	eotm = {
		id = "eotm", name = "EMPLOYEE OF THE MONTH", title = "warlord of the Unpaid", kind = "story",
		idle = nil, clips = { "flex", "point" }, greet = "flex",
		beats = { { "every month. since the end of the world." }, { "we're not raiders. we're a startup." },
			{ "you're robbed. also, would you like an internship? it's unpaid." }, { "who gave me this award? i did. who deserved it? also me." } },
		got = { "the grind never stops. i've tried to stop it. it won't." },
		again = { "every month. since the end of the world." },
	},
	overtime = {
		id = "overtime", name = "MR. OVERTIME", title = "Head of Timekeeping Enforcement. Employee #1", kind = "story",
		idle = nil, clips = { "stomp", "point" }, greet = "point",
		beats = { { "this will only take a minute. it will take exactly a minute." }, { "you're running. that's against policy." },
			{ "please hold still. you're being processed." }, { "i was going home at 17:30. why didn't i go home?" } },
		got = { "the bottom. two hundred and forty-four quarters of back pay. i'm here to collect." },
		again = { "you're absent. everyone's absent. i don't know where everyone goes." },
	},
	-- THE BOARD OF DIRECTORS (shared/secrets.js, public/js/lorecats.js): five cats, the web's own, each ONE cohesive
	-- body (lore_cat_meshes.py). they don't talk: TALK is "Pet" (LoreLife: a purr, a slow blink, a headbutt, a stretch,
	-- a roll, the odd swat), and the lines are what they do
	cat_biscuit = { id = "cat_biscuit", name = "BISCUIT", title = "chief financial officer", kind = "cat",
		beats = {}, got = { "*purrs*" }, again = { "*slow blink*" } },
	cat_beans = { id = "cat_beans", name = "BEANS", title = "vp of sitting", kind = "cat",
		beats = {}, got = { "*purrs*" }, again = { "*slow blink*" } },
	cat_gravy = { id = "cat_gravy", name = "PRINCESS GRAVY", title = "chair of the board", kind = "cat",
		beats = {}, got = { "*purrs*" }, again = { "*slow blink*" } },
	cat_meatloaf = { id = "cat_meatloaf", name = "MEATLOAF", title = "head of synergy", kind = "cat",
		beats = {}, got = { "*purrs*" }, again = { "*slow blink*" } },
	cat_gremlin = { id = "cat_gremlin", name = "GREMLIN", title = "head of legal", kind = "cat",
		beats = {}, got = { "*mrrp*" }, again = { "*slow blink*" } },
} :: { [string]: Entry }

-- how many there are to find (the profile card's "n / N")
function L.total(): number
	return #L.ORDER
end
function L.get(id: any): Entry?
	return if type(id) == "string" then L.NPCS[id] else nil
end

return L
