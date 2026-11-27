--!strict
-- The phone layout (the owner, 18 Nov: "a custom ui like remapping and a button resizer for mobile players, and they can
-- move buttons where they want"). Where every touch button, the move stick, the top row (EMOTE / AUTO / SETTINGS) and
-- the HUD's weapon and health boxes sit, how big and how see-through each one is, what each button does, which are
-- hidden, and the extra buttons a player added. TouchControls.client draws from it; TouchEdit.client is the editor.
--   * three layouts per player (LAYOUT 1-3), kept in the settings save (Settings.luau / SettingsServer) as one short
--     key per thing that differs from the default: "tl<n>.<id>" = "x,y,size,alpha,action,hidden" (x, y: the middle, in
--     thousandths of the safe area, empty = its default place; size and alpha in percent; the stick's action is
--     "float" or "fixed"). "tl.slot" = the layout in use. (the save takes plain values of at most 64 characters and
--     200 keys: three full layouts are about 60.) "tl" is not under "touch.", so the TOUCH tab's RESET leaves them
--   * an action is one of TL.ACTIONS: the key it presses through Keys (the action's default key, which Binds matches
--     for a touch press), its words, and how it behaves
--   * every place is worked out in the safe area's points (TouchControls' "Pad" frame) by TL.place, the same for the
--     game and the editor, so what you place is where it is
local GuiService = game:GetService("GuiService")
local Settings = require(script.Parent:WaitForChild("Settings"))

local TL = {}

local MB1, MB2 = Enum.UserInputType.MouseButton1, Enum.UserInputType.MouseButton2
local K = Enum.KeyCode

-- what a button can do. look: a thumb on it steers the view too; fight: only where weapons work; q: the katana's wave or
-- the Scythe's form (shown with one of them out); body: the grapple's yank (shown while your rope is on a person);
-- rope: shown while your rope is on anything; zm: in a ZOMBIES game only (the flashlight); lock: the AUTO GRAPPLE (shown in a match after GO; the id stays "reel":
-- it was the reel till 19 Nov 2026, so saved layouts keep their place); melee: shown with a swung melee weapon out.
-- act: the button presses that one action only (Keys.press's act; 26 Nov 2026: REEL and YANK both press F)
TL.ACTIONS = {
	fire = { key = MB1, label = "FIRE", look = true, fight = true },
	aim = { key = MB2, label = "AIM", look = true, fight = true },
	jump = { key = K.Space, label = "JUMP" },
	crouch = { key = K.C, label = "SLIDE" },
	sprint = { key = K.LeftShift, label = "RUN" },
	hook = { key = K.E, label = "GRAPPLE", look = true }, -- (27 Nov: the same word as the PC's)
	reload = { key = K.R, label = "RELOAD", fight = true },
	swap = { label = "SWAP", fight = true }, -- (your last weapon: TouchControls works out which)
	slot1 = { key = K.One, label = "SLOT 1", fight = true },
	slot2 = { key = K.Two, label = "SLOT 2", fight = true },
	melee = { key = K.Three, label = "STAB", fight = true },
	item = { key = K.G, label = "ITEM", fight = true }, -- (held for as long as you hold it: Utility)
	camera = { key = K.V, label = "CAMERA" }, -- (third person: Move.client)
	emote = { key = K.T, label = "EMOTE" },
	wave = { key = K.Q, label = "WAVE", fight = true, q = true },
	yank = { key = K.F, label = "YANK", fight = true, body = true, act = "yank" },
	reel = { key = K.X, label = "LOCK", lock = true },
	reelin = { key = K.F, label = "REEL", rope = true, act = "reelin" }, -- (26 Nov 2026: hold to be pulled along your rope, Move.client)
	lunge = { key = K.Z, label = "LUNGE", fight = true, melee = true, act = "lunge" }, -- (26 Nov 2026: the melee lunge, MeleeLunge)
	light = { key = K.F, label = "LIGHT", zm = true, act = "light" }, -- (27 Nov 2026: the flashlight, in a ZOMBIES game only: ZombieLight.client)
} :: { [string]: any }
-- the editor's ACTION list, in this order (only actions whose listeners hear Keys: the goggles' flash listens to the
-- keyboard alone, so it isn't here)
TL.PICK = { "fire", "aim", "jump", "crouch", "sprint", "hook", "reload", "swap", "slot1", "slot2", "melee", "item", "camera", "emote", "reelin", "lunge" }

-- the default layout: the web game's places (touch.css: points from the bottom corner on the fire side, x the button size)
-- keep: can't be hidden; fixed: its action can't be changed (it only shows when it can be used)
TL.ITEMS = {
	{ id = "fire", kind = "btn", act = "fire", x = 106, y = 98, d = 84 }, -- (27 Nov, ui-mocks round 6: the cluster spaced so no rim touches)
	{ id = "jump", kind = "btn", act = "jump", x = 36, y = 50, d = 58 },
	{ id = "crouch", kind = "btn", act = "crouch", x = 30, y = 128, d = 50 },
	{ id = "aim", kind = "btn", act = "aim", x = 44, y = 184, d = 50 },
	{ id = "hook", kind = "btn", act = "hook", x = 114, y = 184, d = 56 },
	{ id = "melee", kind = "btn", act = "melee", x = 176, y = 152, d = 44 },
	{ id = "swap", kind = "btn", act = "swap", x = 198, y = 98, d = 44 },
	{ id = "reload", kind = "btn", act = "reload", x = 176, y = 44, d = 46 },
	{ id = "wave", kind = "btn", act = "wave", x = 114, y = 248, d = 52, fixed = true },
	{ id = "yank", kind = "btn", act = "yank", x = 56, y = 244, d = 50, fixed = true },
	{ id = "reel", kind = "btn", act = "reel", x = 56, y = 304, d = 50, fixed = true },
	{ id = "reelin", kind = "btn", act = "reelin", x = 172, y = 214, d = 50, fixed = true }, -- (26 Nov 2026: by the HOOK, over STAB)
	{ id = "lunge", kind = "btn", act = "lunge", x = 238, y = 150, d = 50, fixed = true }, -- (26 Nov 2026: left of STAB, with a melee weapon out)
	{ id = "light", kind = "btn", act = "light", x = 236, y = 44, d = 46, fixed = true }, -- (27 Nov 2026: left of RELOAD, in ZOMBIES)
	{ id = "settings", kind = "pill", label = "SETTINGS", w = 34, keep = true }, -- (27 Nov, ui-mocks: a gear alone (TouchGlyphs), clear of the score)
	{ id = "auto", kind = "pill", label = "AUTO", w = 88 }, -- (27 Nov, ui-mocks: the fire glyph and AUTO ON / OFF)
	{ id = "emote", kind = "pill", label = "EMOTE", w = 76 },
	{ id = "board", kind = "pill", label = "SCORES", w = 84 }, -- (21 Nov 2026: the match scoreboard, in a match only: Scoreboard.client)
	{ id = "stick", kind = "stick", act = "float", keep = true },
	{ id = "weapon", kind = "box", label = "WEAPON", w = 236, h = 146, keep = true },
	{ id = "health", kind = "box", label = "HEALTH", w = 160, h = 134, keep = true },
} :: { any }
TL.MAX_EXTRA = 6 -- extra buttons a player can add ("x1".."x6")
TL.EXTRA_D = 50
TL.PILL_H = 28
TL.SIZE_MIN, TL.SIZE_MAX = 0.6, 1.6
TL.ALPHA_MIN = 0.2
local byId: { [string]: any } = {}
for _, b in TL.ITEMS do byId[b.id] = b end
TL.byId = byId
function TL.base(id: string): any
	return byId[id] or { id = id, kind = "btn", act = "jump", d = TL.EXTRA_D, extra = true }
end

-- ------------------------------------------------------------------ one layout: a list of records
-- record: { id, kind, act, fx: number?, fy: number?, s, a, hid }
local function fresh(b: any): any
	return { id = b.id, kind = b.kind, act = b.act, fx = nil, fy = nil, s = 1, a = 1, hid = false }
end
function TL.copy(r: any): any return table.clone(r) end
function TL.isDefault(r: any): boolean
	local b = TL.base(r.id)
	return not b.extra and r.fx == nil and r.fy == nil and math.abs(r.s - 1) < 0.005 and math.abs(r.a - 1) < 0.005
		and r.act == b.act and not r.hid
end
function TL.canAct(r: any): boolean -- (its action can be swapped)
	local b = TL.base(r.id)
	return r.kind == "btn" and not b.fixed
end
function TL.canHide(r: any): boolean return not TL.base(r.id).keep end
function TL.canSize(r: any): boolean return r.kind ~= "box" end

local function enc(r: any): string
	local x = if r.fx then tostring(math.floor(r.fx * 1000 + 0.5)) else ""
	local y = if r.fy then tostring(math.floor(r.fy * 1000 + 0.5)) else ""
	return ("%s,%s,%d,%d,%s,%d"):format(x, y, math.floor(r.s * 100 + 0.5), math.floor(r.a * 100 + 0.5), tostring(r.act or ""), if r.hid then 1 else 0)
end
local function dec(r: any, s: string)
	local p = string.split(s, ",")
	local x, y = tonumber(p[1]), tonumber(p[2])
	if x and y then r.fx, r.fy = math.clamp(x / 1000, 0, 1), math.clamp(y / 1000, 0, 1) end
	r.s = math.clamp((tonumber(p[3]) or 100) / 100, TL.SIZE_MIN, TL.SIZE_MAX)
	r.a = math.clamp((tonumber(p[4]) or 100) / 100, TL.ALPHA_MIN, 1)
	local act = p[5] or ""
	if r.kind == "stick" then r.act = if act == "fixed" then "fixed" else "float"
	elseif TL.canAct(r) and TL.ACTIONS[act] and table.find(TL.PICK, act) then r.act = act end
	r.hid = p[6] == "1" and TL.canHide(r)
end

function TL.slot(): number
	return math.clamp(math.floor(tonumber(Settings.get("tl.slot")) or 1), 1, 3)
end
-- a layout as saved (defaults where nothing is)
function TL.load(n: number): { any }
	local out = {}
	for _, b in TL.ITEMS do
		local r = fresh(b)
		local v = Settings.get(("tl%d.%s"):format(n, b.id))
		if type(v) == "string" then pcall(dec, r, v) end
		table.insert(out, r)
	end
	for i = 1, TL.MAX_EXTRA do
		local v = Settings.get(("tl%d.x%d"):format(n, i))
		if type(v) == "string" then
			local r = fresh(TL.base("x" .. i))
			pcall(dec, r, v)
			if r.fx == nil then r.fx, r.fy = 0.5, 0.5 end
			table.insert(out, r)
		end
	end
	return out
end
function TL.defaults(): { any }
	local out = {}
	for _, b in TL.ITEMS do table.insert(out, fresh(b)) end
	return out
end
-- write a layout: only what differs from the default, extras always; extras no longer there are cleared
function TL.save(n: number, items: { any })
	local seen: { [string]: boolean } = {}
	for _, r in items do
		local key = ("tl%d.%s"):format(n, r.id)
		seen[r.id] = true
		Settings.set(key, if TL.isDefault(r) then nil else enc(r))
	end
	for i = 1, TL.MAX_EXTRA do
		if not seen["x" .. i] then Settings.set(("tl%d.x%d"):format(n, i), nil) end
	end
end
-- a new extra button's id in this layout, or nil (all six taken)
function TL.freeExtra(items: { any }): string?
	local used: { [string]: boolean } = {}
	for _, r in items do used[r.id] = true end
	for i = 1, TL.MAX_EXTRA do if not used["x" .. i] then return "x" .. i end end
	return nil
end
function TL.newExtra(id: string, act: string): any
	local r = fresh(TL.base(id))
	r.act = act
	r.fx, r.fy = 0.5, 0.5
	return r
end

-- the layout in use, read once per change (Settings' "tl" keys)
local cache: { any }? = nil
TL.changed = Instance.new("BindableEvent") -- fires (deferred, once) after any layout key changes
local pending = false
Settings.onAny(function(k: string)
	if string.sub(k, 1, 2) ~= "tl" then return end
	cache = nil
	if pending then return end
	pending = true
	task.defer(function() pending = false; TL.changed:Fire() end)
end)
if Settings.loaded then Settings.loaded.Event:Connect(function() cache = nil; TL.changed:Fire() end) end
function TL.active(): { any }
	if not cache then cache = TL.load(TL.slot()) end
	return cache :: { any }
end

-- ------------------------------------------------------------------ places (safe-area points)
-- ts: the touch size (touch.size x the device's own); sd: the HUD's design pixels to points (its Scaled frame's scale)
function TL.size(r: any, ts: number, sd: number): (number, number)
	local b = TL.base(r.id)
	if r.kind == "btn" then local d = (b.d or TL.EXTRA_D) * ts * r.s; return d, d
	elseif r.kind == "pill" then return b.w * ts * r.s, TL.PILL_H * ts * r.s
	elseif r.kind == "stick" then local d = 104 * ts * r.s; return d, d end
	return b.w * sd, b.h * sd
end
-- its default middle (before the left-handed mirror). the top row runs right to left: SETTINGS, AUTO, EMOTE
local PILL_ORDER = { "settings", "auto", "emote", "board" }
function TL.home(r: any, W: number, H: number, ts: number, sd: number, pillTop: number?): (number, number)
	local b = TL.base(r.id)
	if r.kind == "btn" then return W - (b.x or 0) * ts, H - (b.y or 0) * ts end
	if r.kind == "pill" then
		local x = W - 10 * ts
		for _, id in PILL_ORDER do
			local w = byId[id].w * ts
			if id == r.id then return x - w / 2, (pillTop or 8 * ts) + TL.PILL_H * ts / 2 end
			x -= w + 6 * ts
		end
	end
	if r.kind == "stick" then return 100 * ts, H - 170 * ts end
	if r.id == "weapon" then return W / 2 - 72 * sd - b.w * sd / 2, H - 16 * sd - b.h * sd / 2 end
	return 16 * sd + b.w * sd / 2, H - 16 * sd - b.h * sd / 2 -- (health)
end
-- mirrored for a left-handed player: the buttons, the stick and the health box (the top row and the weapon box stay)
function TL.mirrors(r: any): boolean return r.kind == "btn" or r.kind == "stick" or r.id == "health" end
-- keep a w x h box with middle (cx, cy) inside the W x H area and out of `avoid` (Roblox's own buttons, top left: a Rect
-- in the same points)
function TL.clamp(cx: number, cy: number, w: number, h: number, W: number, H: number, avoid: Rect?): (number, number)
	local m = 2
	cx = math.clamp(cx, w / 2 + m, math.max(w / 2 + m, W - w / 2 - m))
	cy = math.clamp(cy, h / 2 + m, math.max(h / 2 + m, H - h / 2 - m))
	if avoid and cx - w / 2 < avoid.Max.X and cy - h / 2 < avoid.Max.Y and cx + w / 2 > avoid.Min.X then
		cy = math.max(cy, avoid.Max.Y + h / 2 + m)
	end
	return cx, cy
end
-- where it is: its middle and its size
function TL.place(r: any, W: number, H: number, ts: number, sd: number, lefty: boolean, avoid: Rect?, pillTop: number?): (Vector2, Vector2)
	local w, h = TL.size(r, ts, sd)
	local cx, cy
	if r.fx and r.fy then cx, cy = r.fx * W, r.fy * H else cx, cy = TL.home(r, W, H, ts, sd, pillTop) end
	if lefty and TL.mirrors(r) then cx = W - cx end
	cx, cy = TL.clamp(cx, cy, w, h, W, H, avoid)
	return Vector2.new(cx, cy), Vector2.new(w, h)
end
-- a middle the editor dropped it at, back to what's stored (un-mirrored, in thousandths)
function TL.store(r: any, c: Vector2, W: number, H: number, lefty: boolean)
	local x = c.X
	if lefty and TL.mirrors(r) then x = W - x end
	r.fx = math.clamp(x / W, 0, 1)
	r.fy = math.clamp(c.Y / H, 0, 1)
end
-- Roblox's own buttons (top left) as a Rect in an area's points. origin: the area's top left on the screen; fake: a
-- test's phone-sized box (they'd sit at its corner)
function TL.avoid(origin: Vector2, fake: boolean): Rect?
	local tb = GuiService.TopbarInset
	if tb.Max.Y <= 0 or tb.Min.X <= 0 then return nil end
	local o = if fake then Vector2.zero else origin
	return Rect.new(-1000, -1000, tb.Min.X - o.X, tb.Max.Y - o.Y)
end
-- the top row's top: under a match's scoreboard (FightHud's Score, ModeHud's line under it) when they'd touch the row
-- in its default place
local PILLS_W = 10 + 84 + 54 + 64 + 64 + 18
function TL.pillTop(pg: Instance, origin: Vector2, W: number, ts: number): number
	local top = 8 * ts
	local left = W - PILLS_W * ts
	for _ = 1, 2 do
		for _, path in { { "JankfireFight", "Score" }, { "JankfireModes", "ModeStrip" } } do
			local g = pg:FindFirstChild(path[1])
			local sc = g and g:FindFirstChild("Scaled")
			local f = sc and sc:FindFirstChild(path[2])
			if f and f:IsA("GuiObject") and f.Visible and g and g:IsA("ScreenGui") and g.Enabled then
				local x0, y0 = f.AbsolutePosition.X - origin.X, f.AbsolutePosition.Y - origin.Y
				local x1, y1 = x0 + f.AbsoluteSize.X, y0 + f.AbsoluteSize.Y
				if x1 + 6 > left and y0 < top + TL.PILL_H * ts + 4 and y1 + 6 > top then top = y1 + 6 end
			end
		end
	end
	return top
end
-- the words on it
function TL.label(r: any): string
	local b = TL.base(r.id)
	if r.kind == "pill" or r.kind == "box" then return b.label end
	if r.kind == "stick" then return "MOVE" end
	if r.act == "wave" then return "WAVE" end
	local a = TL.ACTIONS[r.act]
	return if a then a.label else string.upper(tostring(r.act))
end

return TL
