--!strict
-- your settings (the page on P: SettingsUI.luau; what each one does: SettingsApply.client.luau): one flat table of
-- key -> value, kept on the server per player (SettingsServer, its own session-locked save) and loaded when you join.
-- only what differs from DEFAULTS is stored. every change applies at once (no respawn):
--   Settings.get("look.sens")                  the value (the default until the save has loaded)
--   Settings.set("look.sens", 1.2)             change it (nil = back to the default); saved a moment later
--   Settings.watch("xh.color", fn)             fn(value) now and on every change; returns a connection
--   Settings.changed("xh.color", fn)           fn(value) on every change only
--   Settings.onAny(fn)                         fn(key, value) on every change of any key
--   Settings.row("touch", { kind = "slider", key = "touch.x", label = "...", sub = "...", min, max, step, default, fmt })
--                                              add a row to a tab from another script (kinds: slider, switch, choice)
-- other scripts' live state for the camera and the crosshair: Settings.live (aim 0..1, scoped, the weapon, its spread),
-- written each frame by FightHud.step.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Settings = {}

-- every key, with its default. ranges and words are the page's (SettingsUI); touch.* rows may also come from
-- the touch controls (Settings.row)
Settings.DEFAULTS = {
	-- controls (the web game's sens / adsSens: aiming turns 1/zoom as fast, times the multiplier)
	["look.sens"] = 1, ["look.ySpeed"] = 1, ["look.ads"] = 1, ["look.sniper"] = 1, ["look.dmr"] = 1, ["look.invert"] = false, ["look.pad"] = 1,
	["fov"] = 80, ["fov.kick"] = true, ["aim.toggle"] = false, ["crouch.toggle"] = false, ["sprint.toggle"] = false,
	-- crosshair (the defaults draw the crosshair the game always had: four white bars, 8 x 2, 5 px from the middle)
	["xh.style"] = "cross", ["xh.color"] = "ffffff", ["xh.size"] = 8, ["xh.thick"] = 2, ["xh.gap"] = 5, ["xh.outline"] = 1,
	["xh.dot"] = 0, ["xh.alpha"] = 1, ["xh.spread"] = false, ["xh.hideAim"] = true,
	-- audio (percent of each group's own level)
	["vol.master"] = 100, ["vol.weapons"] = 100, ["vol.effects"] = 100, ["vol.ui"] = 100, ["snd.hit"] = true, ["snd.kill"] = true,
	["vol.music"] = 100, ["snd.emoteMusic"] = true, -- (the dance emotes' music and others' on/off: the flair session's, 19 Nov)
	-- graphics
	["gfx.preset"] = "auto", ["gfx.shadows"] = true, ["gfx.particles"] = 1, ["gfx.bloom"] = true, ["gfx.colour"] = true,
	["gfx.speedLines"] = true, -- (fov.kick and gfx.speedLines: the VFX session's SpeedLines.client reads them, nil = on)
	["gfx.view"] = "normal", ["gfx.shake"] = true, ["gfx.recoil"] = 1, -- (recoil: visual only, Arsenal scales the gun tilt and view punch)
	["gfx.othersKill"] = true, ["gfx.othersSkin"] = true,
	["gfx.othersFinisher"] = true, -- (the finisher session's FinisherClient reads it: off skips finishers you only watch)
	["gfx.titles"] = true, -- (card titles over players' heads: the cosmetics session's OverheadTitles.client)
	["gfx.fps"] = false,
	-- hud and gameplay
	["hud.scale"] = 1, ["hud.dmg"] = true, ["hud.hits"] = true, ["hud.feed"] = true, ["hud.keys"] = false,
	["hud.cb"] = "off", ["hud.enemy"] = "green", ["hud.othersLoot"] = true, ["hud.quickJoin"] = true, -- (QuickJoinUI, play-party-ranked's)
	["hud.killcam"] = true, -- (ReplayClient: off = no killcam, DeathCam.client's orbit instead; play-party-ranked's)
	-- touch (the web game's touch settings and defaults)
	-- (TouchControls reads them: touch.size multiplies the size that suits the device, x1.2 on a tablet; touch.assist
	-- is the web game's aim help, 0 = off)
	["touch.sens"] = 1, ["touch.size"] = 1, ["touch.alpha"] = 0.75, ["touch.assist"] = 1, ["touch.autofire"] = true,
	["touch.lefty"] = false, ["touch.aimToggle"] = true,
	-- controller (the CONTROLLER tab; PadLook.client turns the view, Binds reads the hold / toggles; CONTROLLER.md):
	-- look speed and its aim and up-down parts, the right stick's inner deadzone and the outer one (from the edge), the
	-- response curve, the speed-up held all the way over, aim assist (a pad only) and its strength
	["pad.sens"] = 1, ["pad.ads"] = 1, ["pad.ySpeed"] = 1, ["pad.invert"] = false, ["pad.dead"] = 0.12, ["pad.outer"] = 0.05,
	["pad.curve"] = "standard", ["pad.accel"] = true, ["pad.assist"] = true, ["pad.assistK"] = 1,
	["pad.aimToggle"] = false, ["pad.crouchToggle"] = false, ["pad.sprintToggle"] = true,
} :: { [string]: any }

-- the page's tabs and their rows: SettingsUI fills its own; other scripts add with Settings.row
Settings.extra = {} :: { [string]: { any } }
Settings.rowAdded = Instance.new("BindableEvent")
function Settings.row(tab: string, def: any)
	if type(def) ~= "table" or type(def.key) ~= "string" then return end
	if def.default ~= nil and Settings.DEFAULTS[def.key] == nil then Settings.DEFAULTS[def.key] = def.default end
	local list = Settings.extra[tab]
	if not list then list = {}; Settings.extra[tab] = list end
	table.insert(list, def)
	Settings.rowAdded:Fire(tab, def)
end

Settings.live = { aim = 0, scoped = false, wid = "", spread = 0 }

-- the colour-blind palettes for the three team colours (PINK, CYAN, YELLOW: Matches' TEAM_HEX, Hud's TEAM). the red-green
-- ones are the Okabe-Ito colours nearest each team (made to stay apart for every kind of colour blindness), the
-- blue-yellow one moves yellow to white and pink to red, the pair that kind of eye mixes up
-- (20 Nov 2026: the teams' palette and its colour-blind sets are shared/TeamColors.luau's: the pads and the matches agree)
local TeamColorsMod = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("TeamColors")) :: any
Settings.TEAM = {} :: { string }
for i = 1, 4 do Settings.TEAM[i] = string.sub(TeamColorsMod.hex(i), 2) end
Settings.CB = TeamColorsMod.cb() :: { [string]: { string } }
-- the enemy outline colours (Settings > HUD; the goggles' outlines on everyone else)
Settings.ENEMY = { green = Color3.fromRGB(190, 255, 200), red = Color3.fromRGB(255, 75, 75), yellow = Color3.fromRGB(255, 225, 77),
	magenta = Color3.fromRGB(255, 106, 224), cyan = Color3.fromRGB(55, 214, 255), white = Color3.fromRGB(255, 255, 255) }
Settings.ENEMY_ORDER = { "green", "red", "yellow", "magenta", "cyan", "white" }
-- team i's colour as "#rrggbb" for rich text, after the colour-blind setting
function Settings.teamHex(i: number): string
	local set = Settings.CB[Settings.get("hud.cb")]
	return "#" .. ((set and set[i]) or Settings.TEAM[i] or "ffffff")
end
-- a rich-text line with the team colours swapped for the colour-blind ones (the match line from the server)
function Settings.cbText(s: string): string
	local set = Settings.CB[Settings.get("hud.cb")]
	if not set then return s end
	for i, hex in Settings.TEAM do s = string.gsub(s, "#" .. hex, "#" .. set[i]) end
	return s
end

-- ------------------------------------------------------------------ values
local values: { [string]: any } = {} -- (only what differs from the default)
local watchers: { [string]: { (any) -> () } } = {}
local anyWatchers: { (string, any) -> () } = {}

function Settings.get(k: string): any
	local v = values[k]
	if v == nil then v = Settings.DEFAULTS[k] end
	return v
end

local function fire(k: string, v: any)
	local list = watchers[k]
	if list then
		for _, fn in table.clone(list) do
			local ok, err = pcall(fn, v)
			if not ok then warn("[jankfire] settings " .. k .. ": " .. tostring(err)) end
		end
	end
	for _, fn in table.clone(anyWatchers) do
		local ok, err = pcall(fn, k, v)
		if not ok then warn("[jankfire] settings: " .. tostring(err)) end
	end
end

local saveSoon: () -> ()
function Settings.set(k: string, v: any)
	if v == Settings.DEFAULTS[k] then v = nil end
	local before = Settings.get(k)
	values[k] = v
	local now = Settings.get(k)
	if now ~= before then
		fire(k, now)
		saveSoon()
	end
end

function Settings.changed(k: string, fn: (any) -> ()): { Disconnect: () -> () }
	local list = watchers[k]
	if not list then list = {}; watchers[k] = list end
	table.insert(list, fn)
	return { Disconnect = function()
		local i = table.find(list, fn)
		if i then table.remove(list, i) end
	end }
end
function Settings.watch(k: string, fn: (any) -> ()): { Disconnect: () -> () }
	task.spawn(fn, Settings.get(k))
	return Settings.changed(k, fn)
end
function Settings.onAny(fn: (string, any) -> ()): { Disconnect: () -> () }
	table.insert(anyWatchers, fn)
	return { Disconnect = function()
		local i = table.find(anyWatchers, fn)
		if i then table.remove(anyWatchers, i) end
	end }
end
-- every key that starts with one of these back to its default (a tab's RESET)
function Settings.reset(prefixes: { string })
	local keys = {}
	for k in values do
		for _, p in prefixes do
			if string.sub(k, 1, #p) == p then table.insert(keys, k); break end
		end
	end
	for _, k in keys do Settings.set(k, nil) end
end

-- ------------------------------------------------------------------ the save (SettingsServer)
Settings.state = "loading" -- "loading" | "cloud" | "memory" (Studio without API access: kept for this session only)
Settings.loaded = Instance.new("BindableEvent")
local remote: RemoteFunction? = nil
local dirtyT: number? = nil
local saving = false

local function send()
	if not remote or saving then return end
	saving = true
	dirtyT = nil
	local snap = table.clone(values)
	local ok, res = pcall(function() return (remote :: RemoteFunction):InvokeServer("save", snap) end)
	saving = false
	if not ok or type(res) ~= "table" or res.ok ~= true then
		warn("[jankfire] settings weren't saved: " .. (if ok and type(res) == "table" then tostring(res.why) else tostring(res)))
	end
	if dirtyT then task.delay(1.5, send) end -- (changed again while that one was on its way)
end
function saveSoon()
	if Settings.state == "loading" then return end -- (the save hasn't come yet: nothing to write over it with)
	local first = dirtyT == nil
	dirtyT = os.clock()
	if first then
		task.delay(1.5, function()
			while dirtyT and os.clock() - dirtyT < 1.5 do task.wait(0.25) end
			if dirtyT then send() end
		end)
	end
end
-- write now (the page closing)
function Settings.flush()
	if dirtyT then task.spawn(send) end
end

task.spawn(function()
	local rs = ReplicatedStorage:WaitForChild("JankfireRemotes", 30)
	local r = rs and rs:WaitForChild("Settings", 30)
	if not (r and r:IsA("RemoteFunction")) then
		Settings.state = "memory"
		warn("[jankfire] settings: no Settings remote, kept for this session only")
		Settings.loaded:Fire()
		return
	end
	remote = r
	local got: any = nil
	for i = 1, 3 do
		local ok, res = pcall(function() return r:InvokeServer("load") end)
		if ok and type(res) == "table" and res.ok == true then got = res; break end
		task.wait(i * 2)
	end
	local local_ = values -- (anything changed while it loaded wins over the save)
	values = {}
	if got and type(got.data) == "table" then
		for k, v in got.data do
			if type(k) == "string" and (type(v) == "number" or type(v) == "boolean" or type(v) == "string") then values[k] = v end
		end
	end
	for k, v in local_ do values[k] = v end
	Settings.state = if got and got.state == "cloud" then "cloud" else "memory"
	-- (tell every watcher what it is now)
	local keys: { [string]: boolean } = {}
	for k in Settings.DEFAULTS do keys[k] = true end
	for k in values do keys[k] = true end
	for k in keys do
		local v = Settings.get(k)
		if v ~= Settings.DEFAULTS[k] then fire(k, v) end
	end
	Settings.loaded:Fire()
	if next(local_) then saveSoon() end
end)

-- Studio tests (never in a live server): the player attribute SettingsTest drives the page and the values, and
-- SettingsDump reads them back. "set:look.sens=0.5", "reset:xh.", "dump", "tab:audio", "open", "close" (a "#n"
-- on the end makes a repeat count as a change)
Settings.testHook = Instance.new("BindableEvent")
if game:GetService("RunService"):IsStudio() then
	local me = Players.LocalPlayer
	me:GetAttributeChangedSignal("SettingsTest"):Connect(function()
		local s = me:GetAttribute("SettingsTest")
		if type(s) ~= "string" then return end
		s = string.gsub(s, "#%d+$", "")
		local op, rest = string.match(s, "^(%a+):?(.*)$")
		if op == "set" then
			local k, v = string.match(rest, "^([^=]+)=(.*)$")
			if k then
				local val: any = v
				if v == "true" then val = true elseif v == "false" then val = false elseif v == "nil" then val = nil
				elseif tonumber(v) then val = tonumber(v) end
				Settings.set(k, val)
			end
		elseif op == "reset" then
			Settings.reset({ rest })
		elseif op == "dump" then
			local out = { state = Settings.state, values = values, live = Settings.live }
			me:SetAttribute("SettingsDump", game:GetService("HttpService"):JSONEncode(out))
		end
		Settings.testHook:Fire(op, rest)
	end)
end

return Settings
