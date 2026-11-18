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
MG.TITLE = { arm = "ARM WRESTLING", board = "CHESS · CHECKERS", arcade = "ARCADE" } :: { [string]: string }
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
		cam = { back = 4.4, up = 4.95, side = -2.8 }, -- the sitter's camera: high behind their left shoulder, down on the clasp
	},
	board = {
		top = 3.0, surface = 3.1, sq = 0.46, -- (the squares' tops; square size)
		seat = { A = Vector3.new(0, 0, 3.05), B = Vector3.new(0, 0, -3.05) },
		stand = { A = Vector3.new(-2.8, 0, 3.6), B = Vector3.new(2.8, 0, -3.6) },
		cam = { back = 3.4, up = 6.6, aim = 0.35 }, -- over the sitter's side, looking down on the board (60 degrees)
	},
	arcade = {
		stand = Vector3.new(0, 0, -2.9), -- you stand here, facing the screen (+Z)
		leave = Vector3.new(0, 0, -4.2),
		-- the screen part (in the cabinet mesh's recess): its centre and its tilt back from upright
		screen = { at = Vector3.new(0, 5.03, -0.18), tilt = 14, size = Vector2.new(2.36, 2.06) },
		marquee = { at = Vector3.new(0, 7.05, -0.975), size = Vector2.new(2.65, 0.66) },
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

-- ------------------------------------------------------------------ the arcade
MG.ARCADE = {
	BOARD = 10, -- how many high scores the server keeps
	LIVE_EVERY = 1.5, -- how often a run reports its score to the cabinet's screen
	-- the server's sanity check on a finished run: what a human could have scored in that time
	MAX_KILLS_PER_S = 2.2, MAX_PER_KILL = 300 * 3, WAVE_BONUS = 250,
}

return MG
