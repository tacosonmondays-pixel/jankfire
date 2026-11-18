--!strict
-- THE HUB'S MINI-GAMES (18 Nov 2026, the owner: "At the tables for the lobby hub can you add mini games that can actually
-- be played, like arm wrestling based on hitting skill checks, another table has chess/checkers, maybe the arcade
-- machine you can play like a mini version of the game against bots??"). three games, each a self-contained model the
-- server builds on a spot (server/MiniGames.server.luau), played through one remote (JankfireRemotes.MiniGame):
--   arm     ARM WRESTLING: two seats across a table, your own avatar's hands clasped (IKControls), timing checks (a
--           needle and a hit zone that shrinks as the bout goes on: Space / pad A / a tap); a hit pushes the arms your
--           way, a miss gives ground, first to slam the other's hand down wins. alone: a bot in three steps
--   board   CHESS or CHECKERS on one table, picked at the table: two players or one against a bot (shared/Chess,
--           shared/Checkers: a short minimax). the server checks every move; anyone can stand and watch
--   arcade  the cabinet: a small top-down JANKFIRE against waves of bots (Redline, Shotgun, Sniper and a dash) on a
--           screen that takes over while you play; a per-server high-score board on the cabinet
-- the rules for all three: hub only (and training, if a spot is ever put there; never in a match or a map room: the
-- server checks the Zone, the client MenuGate), leave any time (Backspace, pad B, a LEAVE button; Space when the game
-- has no use for it), nothing to farm (no loot, no currency, no quests: fun and the high scores only)
-- WHERE: the hub's builder drops spots: an invisible Part anywhere under workspace.Map.Hub tagged "MiniGameSpot" with
-- the attribute Game = "arm" | "board" | "arcade", its CFrame the footprint's centre on the floor. LookVector: the
-- arcade's screen faces it (you stand on that side); a table's two seats sit at +/- its look axis. with no spots in
-- the map the server uses SPOTS below (the lounge)
-- the furniture: tools/roblox/minigame_models.py (Blender) -> ReplicatedStorage.JankfireMiniGames.Kit
-- (studio-tools/MiniGameImport.luau). every number about where things are on a model is in L, in the model's own
-- frame: origin = the spot (floor centre), -Z = the spot's LookVector
local MG = {}

MG.ZONES = { hub = true, training = true } :: { [string]: boolean }
MG.TITLE = { arm = "ARM WRESTLING", board = "CHESS · CHECKERS", arcade = "ARCADE", box = "BOXING" } :: { [string]: string }
MG.LEVELS = { "easy", "medium", "hard" }
MG.LEVEL_NAME = { easy = "EASY", medium = "MEDIUM", hard = "HARD" } :: { [string]: string }

-- the place everything is built from. A sits on +Z facing -Z (its right hand is +X), B on -Z facing +Z (right = -X)
MG.SEAT_TOP = 2.0 -- a stool's and a chair's cushion top (the meshes)
MG.SEAT_SINK = 0.0 -- the invisible Seat's top under (+) or over (-) the cushion (measured in Play, then set here)
MG.L = {
	arm = {
		top = 3.25, -- the table's surface
		seat = { A = Vector3.new(-0.7, 0, 2.3), B = Vector3.new(0.7, 0, -2.3) },
		stand = { A = Vector3.new(-2.6, 0, 3.4), B = Vector3.new(2.6, 0, -3.4) }, -- where you're put when you get up
		lean = 16, -- degrees the sitter leans in over the table (the SeatWeld)
		-- the clasped hands swing round the table's long axis: through pivot, at reach from it; 0 = straight up,
		-- +1 = all the way to A's win (B's hand on the pin pad at -X)
		pivot = Vector3.new(0, 3.3, 0), reach = 1.12, swing = 72, -- (degrees at the meter's end; the slam goes to 88)
		elbow = { A = Vector3.new(0.2, 3.4, 0.75), B = Vector3.new(-0.2, 3.4, -0.75) },
		peg = { A = Vector3.new(-1.1, 3.89, 0.8), B = Vector3.new(1.1, 3.89, -0.8) },
		pin = { A = Vector3.new(1.0, 3.32, 0), B = Vector3.new(-1.0, 3.32, 0) }, -- the pad A's hand lands on when A loses
		-- the sitter's camera: side-on across the table (main, 19 Nov: "like a broadcast shot"), from the sitter's right,
		-- turned `angle` degrees toward their end, `dist` studs out from the hands and `up` above them
		cam = { dist = 6.6, angle = 10, up = 1.7 },
	},
	board = {
		top = 3.0, surface = 3.1, sq = 0.46, -- (the squares' tops; square size)
		seat = { A = Vector3.new(0, 0, 3.05), B = Vector3.new(0, 0, -3.05) },
		stand = { A = Vector3.new(-2.8, 0, 3.6), B = Vector3.new(2.8, 0, -3.6) },
		cam = { back = 3.0, up = 7.2, aim = 0.2, side = 1.4 }, -- high over the sitter's right shoulder, down on the board
	},
	arcade = {
		stand = Vector3.new(0, 0, -2.9), -- you stand here, facing the screen (+Z)
		leave = Vector3.new(0, 0, -4.2),
		-- the screen part (in the cabinet mesh's recess): its centre and its tilt back from upright
		screen = { at = Vector3.new(0, 5.03, -0.18), tilt = 14, size = Vector2.new(2.36, 2.06) },
		marquee = { at = Vector3.new(0, 7.05, -0.975), size = Vector2.new(2.65, 0.66) },
	},
	-- the gym's ring (19 Nov 2026, the owner: "when you step into the ring can it be a boxing mini game? perfect dodge,
	-- counter b low, upper cut jab, hook ... weave duck you know !"). the spot is the mat's middle on its top; the two
	-- boxers stand at +/- `gap` on the look's line, A on +Z facing -Z. each boxer's camera: a low side-on shot from
	-- their right, `dist` out from the middle, `up` over the mat, turned `angle` toward their end
	box = {
		gap = 2.3,
		mark = 4.6, -- the BOX prompts: at +/- this on the look's line (step onto your corner of the mat)
		cam = { dist = 9.5, angle = 14, up = 4.4, aim = 2.9 },
	},
}

-- fallback spots (world positions on the floor and the look's turn from -Z in degrees: { game, x, y, z, yaw }), used
-- only when the map has no MiniGameSpot markers. empty: since place v966 the hub's builder makes the markers (in
-- Rotunda.Scenery, remade on every rebuild: arm and board on the lobby's east and west rugs, the cabinet against the
-- east arcade's north wall), so nothing is kept here
MG.SPOTS = {} :: { { any } }

-- ------------------------------------------------------------------ arm wrestling
MG.ARM = {
	COUNT = 3, -- the countdown before a bout
	-- a check: the needle sweeps 0..1..0 (period T for one crossing); the zone is c +/- w. both shrink over SHRINK s
	W0 = 0.15, W1 = 0.06, T0 = 1.0, T1 = 0.6, SHRINK = 24,
	HIT = 0.11, PERFECT = 0.16, MISS = 0.07, -- how far the meter moves (it runs -1..1)
	PERFECT_K = 0.35, -- a hit within this share of the zone's half width is perfect
	GAP = 0.2, -- between your press and your next check
	TIMEOUT = 2.2, -- crossings with no press: counted as a miss
	SLAM_HOLD = 2.6, -- the slam's hold before the table is open again
	BOT = {
		easy = { hit = 0.55, fall = 0.15, perfect = 0.12, every = { 0.85, 1.25 } },
		medium = { hit = 0.72, fall = 0.14, perfect = 0.28, every = { 0.7, 1.0 } },
		hard = { hit = 0.86, fall = 0.1, perfect = 0.48, every = { 0.55, 0.8 } },
	},
}
-- where the needle is at time t (server time) for a check { t0, T }
function MG.needle(chk: { [string]: any }, t: number): number
	local u = ((t - chk.t0) / chk.T) % 2
	return if u <= 1 then u else 2 - u
end

-- ------------------------------------------------------------------ the board
MG.BOARD = {
	DEPTH = { chess = { easy = 1, medium = 3, hard = 4 }, checkers = { easy = 2, medium = 4, hard = 8 } },
	NOISE = { easy = 90, medium = 20, hard = 0 }, -- random centipawns added to the bot's scores (easy blunders)
	MOVE_LIMIT = 180, -- seconds on your move before you lose on time (the table can't be held forever)
	BOT_WAIT = { 0.6, 1.2 }, -- the bot's thinking pause, at least
}

-- ------------------------------------------------------------------ boxing (server/MiniBox, client/MiniBoxUI)
-- a punch: `wind` s of wind-up (the tell), it lands, then `rec` s before you can act again. dmg on a clean hit; a block
-- lets `chip` of it through (body blows go round a high block); `st` stamina it costs. `side`: a hook comes from the
-- puncher's hand, so it lands on the OTHER side of the one it hits (a right hook arrives at your left)
-- what dodges what: DUCK slips the jab and the hook (an uppercut catches a duck: x UPPER_DUCK); WEAVE slips the jab, the
-- uppercut and the body blow, and the hook coming from the side you weave to. PERFECT: a dodge that starts within
-- PERFECT s before the punch lands: the puncher is left open (OPEN s), you get a COUNTER window and the world slows
MG.BOX = {
	MOVES = {
		jab = { wind = 0.2, rec = 0.22, dmg = 5, chip = 0.15, st = 5, big = false },
		hook = { wind = 0.36, rec = 0.38, dmg = 11, chip = 0.2, st = 10, big = true },
		upper = { wind = 0.48, rec = 0.45, dmg = 16, chip = 0.25, st = 15, big = true },
		body = { wind = 0.3, rec = 0.34, dmg = 8, chip = 1, st = 8, big = false, drain = 10 },
	},
	DODGE = { duck = 0.42, weave = 0.38 }, -- how long a dodge keeps you clear
	DODGE_REST = 0.28, -- after a dodge, before the next one
	DODGE_ST = 4,
	PERFECT = 0.15,
	OPEN = 0.75, -- a perfectly dodged puncher can't act
	COUNTER = 0.9, -- the window for your counter
	COUNTER_X = 1.8, COUNTER_WIND = 0.6, -- a counter hits that much harder, and its wind-up is that much shorter
	UPPER_DUCK = 1.4,
	HIT_STUN = 0.32, BIG_STUN = 0.5, -- a landed punch stops the one hit (and cancels their wind-up)
	BLOCK_DRAIN = 6, BLOCK_HIT_ST = 7, -- stamina while holding the guard; per punch taken on it
	ST_MAX = 100, ST_REGEN = 15, ST_WAIT = 0.6, TIRED = 0.5, -- (a punch thrown with too little stamina hits at x TIRED)
	HP = 100,
	DOWN = 4, -- a knockdown lasts this long; then up with GETUP[n] health, n = knockdowns so far
	GETUP = { 55, 40, 25 },
	KOS = 3,
	ROUNDS = 3, ROUND = 45, REST = 5, REST_HP = 12,
	COUNT = 3, -- the countdown before round 1
	GRACE = 0.12, -- a punch is judged this long after it lands, so a dodge pressed just in time still counts over the net
	UP = 2.0, -- getting up after a knockdown
	-- the R15 clips: Mixamo mocap (the owner's account, 19 Nov; the .fbx stay in the vault, mixamo-18nov-boxing),
	-- retargeted by tools/blender/mixamo_r15.py and uploaded as animations. imp = when the punch lands in the clip
	-- (the client plays the wind-up to land there on time), len = the clip's length, hold = where a held pose stops.
	-- duck, weave and the off-balance "open" are posed by code (MiniBoxUI POSES), as is everything on an R6 body
	CLIPS = {
		idle = { id = "rbxassetid://76338948390073", len = 2.2, loop = true }, -- (15 bouncing boxing idle)
		jab = { id = "rbxassetid://117014901395569", imp = 0.4, len = 1.333 }, -- (02 short head jab)
		hookL = { id = "rbxassetid://110200541195544", imp = 0.6, len = 2.0 }, -- (05 lead hand hook)
		hookR = { id = "rbxassetid://140684068590744", imp = 0.73, len = 2.167 }, -- (06 back hand hook)
		upper = { id = "rbxassetid://99950974582380", imp = 0.7, len = 2.2 }, -- (09 back hand uppercut)
		body = { id = "rbxassetid://104499571706595", imp = 0.47, len = 1.8 }, -- (11 mid body jab)
		block = { id = "rbxassetid://113967255302565", hold = 0.45, len = 1.767 }, -- (18 high centre block, held up)
		hitHead = { id = "rbxassetid://133752383320930", len = 1.233 }, -- (25 medium hit to the head)
		hitBig = { id = "rbxassetid://129616818549252", len = 1.433 }, -- (24 big hit to the head)
		hitBody = { id = "rbxassetid://110057867863287", len = 1.2 }, -- (27 hit in the stomach)
		down = { id = "rbxassetid://77167239446919", hold = 2.1, len = 2.133 }, -- (30 knocked down by a punch)
		up = { id = "rbxassetid://137388307124591", len = 2.7 }, -- (31 getting up)
	},
	-- the bot: its wind-ups are this much longer (the tell), how often it reads your punch and answers it, how soon, how
	-- often it fakes, how long between its punches
	BOT = {
		easy = { wind = 1.7, read = 0.18, react = { 0.32, 0.5 }, feint = 0, every = { 1.4, 2.4 }, block = 0.25 },
		medium = { wind = 1.35, read = 0.38, react = { 0.2, 0.36 }, feint = 0.12, every = { 1.0, 1.9 }, block = 0.4 },
		hard = { wind = 1.12, read = 0.58, react = { 0.12, 0.24 }, feint = 0.25, every = { 0.7, 1.4 }, block = 0.5 },
	},
}

-- ------------------------------------------------------------------ the arcade
MG.ARCADE = {
	BOARD = 10, -- how many high scores the server keeps
	LIVE_EVERY = 1.5, -- how often a run reports its score to the cabinet's screen
	-- the server's sanity check on a finished run: what a human could have scored in that time
	MAX_KILLS_PER_S = 2.2, MAX_PER_KILL = 300 * 3, WAVE_BONUS = 250,
}

return MG
