--!strict
-- what the settings DO (the values: Settings.luau; the page: SettingsUI.luau). everything here is this client's own:
-- the look speed and the scope speeds, the field of view, the sound groups, the graphics switches, the HUD's size, the
-- FPS readout, the colour-blind palettes and the enemy outline colour. every one applies the moment it changes.
-- (the crosshair is drawn by Crosshair.luau from FightHud; damage numbers, hit markers and the kill feed are checked
-- in FightHud; the keys in Binds.luau)
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UIS = game:GetService("UserInputService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")
local Lighting = game:GetService("Lighting")

local me = Players.LocalPlayer
local Settings = require(script.Parent:WaitForChild("Settings")) :: any
local T = require(script.Parent:WaitForChild("Theme")) :: any
local Weapons = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("Weapons")) :: any
local S = Settings.get

-- ================================================================== looking
-- the web game: aiming turns sens * adsSens / zoom (main.js). here the zoom part follows the sights coming up (the
-- view narrows by 1 + (zoom - 1) * aim) and the multiplier blends in with them: the Sniper's and the Second
-- Opinion's scopes have their own. the mouse goes through MouseDeltaSensitivity (Roblox's camera and the shoulder
-- camera both read it); a controller and a touch screen through Roblox's camera input, below
local function aimK(): number
	local L = Settings.live
	local a = math.clamp(L.aim or 0, 0, 1)
	if a <= 0 then return 1 end
	local w = Weapons.list[L.wid or ""]
	local zoom = if w and w.ads and type(w.ads.zoom) == "number" then w.ads.zoom else 1
	local m = if L.wid == "sniper" then S("look.sniper") elseif L.wid == "dmr" then S("look.dmr") else S("look.ads")
	m = if type(m) == "number" then m else 1
	return (1 + (m - 1) * a) / (1 + (zoom - 1) * a)
end
Settings.aimK = aimK -- (the measuring test reads it)
RunService:BindToRenderStep("JankLookSpeed", Enum.RenderPriority.Camera.Value - 2, function()
	local want = math.clamp((S("look.sens") :: number) * aimK(), 0.001, 20)
	if math.abs(UIS.MouseDeltaSensitivity - want) > 1e-4 then UIS.MouseDeltaSensitivity = want end
end)
-- up/down: the shoulder camera multiplies its up-down turn by the player attribute LookY (-1 = inverted)
local function lookY()
	local y = ((S("look.ySpeed") :: any) or 1) * (if S("look.invert") == true then -1 else 1)
	me:SetAttribute("LookY", if y == 1 then nil else y)
end
Settings.watch("look.invert", lookY)
Settings.watch("look.ySpeed", lookY)
-- Roblox's own camera (first person): its turn this frame, scaled for a controller or a touch screen and the aim, and
-- the up-down part inverted / scaled. (the mouse's speed is already in its delta, above)
task.spawn(function()
	local pm = me:WaitForChild("PlayerScripts"):WaitForChild("PlayerModule", 60)
	local cm = pm and pm:WaitForChild("CameraModule", 20)
	local ci = cm and cm:WaitForChild("CameraInput", 20)
	if not ci then warn("[jankfire] settings: no CameraInput, controller speed and invert are off"); return end
	local ok, CI = pcall(require, ci)
	if not ok or type(CI) ~= "table" or type((CI :: any).getRotation) ~= "function" then return end
	local orig = (CI :: any).getRotation
	-- (a controller in your hands: its stick turns the view itself, with its own curve, deadzones and aim assist,
	-- PadLook.client. Pad.on is false the moment the mouse moves, so a pad lying on the desk never takes the mouse's turn)
	local okP, Pad = pcall(require, script.Parent:WaitForChild("Pad"))
	;(CI :: any).getRotation = function(dt: number, ...)
		local r: Vector2 = orig(dt, ...)
		if r.X == 0 and r.Y == 0 then return r end
		if okP and (Pad :: any).on() then return Vector2.zero end
		local last = UIS:GetLastInputType()
		local k = 1
		if string.sub(last.Name, 1, 7) == "Gamepad" then k = (S("look.pad") :: number) * aimK()
		elseif last == Enum.UserInputType.Touch then k = (S("touch.sens") :: number) * aimK() end
		local y = ((S("look.ySpeed") :: any) or 1) * (if S("look.invert") == true then -1 else 1)
		return Vector2.new(r.X * k, r.Y * k * y)
	end
end)
-- the field of view (Arsenal reads BaseFov and zooms from it)
Settings.watch("fov", function(v: any) me:SetAttribute("BaseFov", if type(v) == "number" then v else 80) end)

-- ================================================================== sound
-- three groups under one master: WEAPONS (guns, handling, blades, hits and kills), EFFECTS (everything else out in the
-- world: steps, jumps, impacts, explosions, kill effects), INTERFACE (menus, loot, round banners). the library's
-- Sounds get their group here (a copy keeps it); any other Sound that turns up without one goes to EFFECTS, or to
-- INTERFACE when it's in your screen gui
local function group(name: string, parent: Instance): SoundGroup
	local g = parent:FindFirstChild(name)
	if not (g and g:IsA("SoundGroup")) then
		local ng = Instance.new("SoundGroup")
		ng.Name = name
		ng.Parent = parent
		g = ng
	end
	return g :: SoundGroup
end
local master = group("JankMaster", SoundService)
local G = { weapons = group("Weapons", master), effects = group("Effects", master), ui = group("Interface", master) }
local WEAPON_NAMES = { click = true, empty = true, reload = true, thwack = true, glug = true, rev_up = true, marble = true,
	boing = true, swing = true, bonk = true, tink = true, ting = true, parry = true, parry_perfect = true, ricochet = true,
	hit = true, headshot = true, headshot_ko = true, kill = true,
	crit_return = true, wave_cast = true, wave_fly = true, wave_hit = true, wave_wall = true, edge_full = true, -- (the katana's moves sit with its parry: 18 Nov)
	minigun_spinup = true, minigun_spin = true, minigun_spindown = true, reload_minigun = true, water_soak = true,
	nail_wall = true, nail_pinned = true, bread_bonk = true, slap_hit = true, slap_whoosh = true, -- (weapons batch A, d8fb3a1)
	scythe_swing = true, scythe_hit = true, scythe_dash = true, scythe_shot = true, scythe_form = true, -- (the Scythe and its rifle form)
	bowl_roll = true, bowl_hit = true, bowl_strike = true, slipper_throw = true, slipper_hit = true, slipper_catch = true,
	scales_swing = true, scales_hit = true, gavel_strike = true, gavel_charge = true, remote_click = true, remote_pause = true,
	remote_rewind = true, bow_draw = true, arrow_hit = true, arrow_wall = true, flame_burn = true, gas_hiss = true, sleep_hit = true, -- (weapons batch D)
	card_throw = true, card_deal = true, card_heal = true, card_blast = true, card_dash = true, card_tp = true } -- (weapons batch E: the Card Deck)
local function kind(name: string): string
	local base = string.match(name, "^(.-)#%d+$") or name
	-- (skin_<skin>_<kind>: a special skin's shot and reload layers, the sound session's: they go with the guns)
	if string.sub(base, 1, 4) == "gun_" or string.sub(base, 1, 5) == "draw_" or string.sub(base, 1, 5) == "skin_" or WEAPON_NAMES[base] then return "weapons" end
	if string.sub(base, 1, 5) == "loot_" or string.sub(base, 1, 6) == "round_" or string.sub(base, 1, 3) == "ui_" then return "ui" end
	return "effects"
end
local lib = ReplicatedStorage:WaitForChild("JankfireSounds", 10)
if lib then
	local function tag(s: Instance) if s:IsA("Sound") then s.SoundGroup = G[kind(s.Name)] end end
	for _, s in lib:GetChildren() do tag(s) end
	lib.ChildAdded:Connect(tag)
end
local function stray(d: Instance, ui: boolean)
	if d:IsA("Sound") and d.SoundGroup == nil then d.SoundGroup = if ui then G.ui else G.effects end
end
for _, d in workspace:GetDescendants() do stray(d, false) end
workspace.DescendantAdded:Connect(function(d) stray(d, false) end)
SoundService.DescendantAdded:Connect(function(d) task.defer(stray, d, false) end) -- (deferred: Sfx sets nothing, but a script may set its own group)
local pg = me:WaitForChild("PlayerGui")
pg.DescendantAdded:Connect(function(d) stray(d, true) end)
local function vol(key: string, g: SoundGroup)
	Settings.watch(key, function(v: any) g.Volume = math.clamp((if type(v) == "number" then v else 100) / 100, 0, 2) end)
end
vol("vol.master", master); vol("vol.weapons", G.weapons); vol("vol.effects", G.effects); vol("vol.ui", G.ui)
-- the hit and kill sounds on / off (Sfx.mute: names Sfx.play skips)
do
	local ok, Sfx = pcall(require, script.Parent:WaitForChild("Sfx"))
	if ok and type(Sfx) == "table" then
		local sfx = Sfx :: any
		sfx.mute = sfx.mute or {}
		Settings.watch("snd.hit", function(v: any)
			local off = v == false
			sfx.mute.hit = off; sfx.mute.headshot = off; sfx.mute.headshot_ko = off
		end)
		Settings.watch("snd.kill", function(v: any) sfx.mute.kill = v == false end)
	end
end

-- ================================================================== graphics
-- a preset sets the switches under it; touching one of those makes it CUSTOM (the page does that). AUTO follows
-- Roblox's own graphics level (the Esc menu): 1-3 low, 4-6 medium, 7-10 or automatic high. HIGH is the game as it was
local PRESETS = {
	low = { ["gfx.shadows"] = false, ["gfx.particles"] = 0.35, ["gfx.bloom"] = false, ["gfx.view"] = "near" },
	med = { ["gfx.shadows"] = true, ["gfx.particles"] = 0.7, ["gfx.bloom"] = true, ["gfx.view"] = "normal" },
	high = { ["gfx.shadows"] = true, ["gfx.particles"] = 1, ["gfx.bloom"] = true, ["gfx.view"] = "normal" }, -- (FAR is a choice of its own: ZoneCull's near-only drawing is what keeps the frame rate up)
}
Settings.PRESETS = PRESETS
local function autoLevel(): string
	local ok, lvl = pcall(function() return UserSettings():GetService("UserGameSettings").SavedQualityLevel end)
	if not ok or lvl == nil or lvl == Enum.SavedQualitySetting.Automatic then return "high" end
	local n = tonumber(string.match(lvl.Name, "%d+")) or 10
	return if n <= 3 then "low" elseif n <= 6 then "med" else "high"
end
Settings.autoLevel = autoLevel
local function applyPreset()
	if Settings.state == "loading" then return end -- (the save decides first; Settings.loaded runs this again)
	local p = S("gfx.preset")
	local level = if p == "auto" then autoLevel() else p
	local set = PRESETS[level]
	if not set then return end -- (custom: the switches stay as they are)
	for k, v in set do
		if Settings.get(k) ~= v then Settings.set(k, v) end
	end
end
Settings.watch("gfx.preset", function() task.defer(applyPreset) end)
pcall(function()
	UserSettings():GetService("UserGameSettings"):GetPropertyChangedSignal("SavedQualityLevel"):Connect(function()
		if S("gfx.preset") == "auto" then applyPreset() end
	end)
end)
Settings.loaded.Event:Connect(function() task.defer(applyPreset) end)

-- an "off" switch holds a property at its off value even when a zone's look changes it, and gives back what the look
-- last wanted when it is turned on again
local function holdOff(inst: Instance, prop: string, offValue: any, isOff: () -> boolean)
	local wanted = (inst :: any)[prop]
	local writing = false
	local function put()
		local want = if isOff() then offValue else wanted
		if (inst :: any)[prop] ~= want then writing = true; (inst :: any)[prop] = want; writing = false end
	end
	inst:GetPropertyChangedSignal(prop):Connect(function()
		if writing then return end
		wanted = (inst :: any)[prop]
		if isOff() then put() end
	end)
	return put
end
-- shadows
local shadowPut = holdOff(Lighting, "GlobalShadows", false, function() return S("gfx.shadows") == false end)
Settings.watch("gfx.shadows", function() shadowPut() end)
-- bloom (Bloom + SunRays) and colour (ColorCorrection): the zone looks' own effects under Lighting (HubLook names them
-- so). effects other scripts make (the goggles' JankNightVision, flashes) are left alone
local postPuts: { [string]: { () -> () } } = { bloom = {}, colour = {} }
local seen: { [Instance]: boolean } = {}
local function post(e: Instance)
	if seen[e] or string.sub(e.Name, 1, 4) == "Jank" then return end
	local which = if e:IsA("BloomEffect") or e:IsA("SunRaysEffect") then "bloom" elseif e:IsA("ColorCorrectionEffect") then "colour" else nil
	if not which then return end
	seen[e] = true
	local key = "gfx." .. which
	local put = holdOff(e, "Enabled", false, function() return S(key) == false end)
	table.insert(postPuts[which], put)
	put()
end
for _, e in Lighting:GetChildren() do post(e) end
Lighting.ChildAdded:Connect(post)
Settings.watch("gfx.bloom", function() for _, f in postPuts.bloom do f() end end)
Settings.watch("gfx.colour", function() for _, f in postPuts.colour do f() end end)
-- particles: Fx's bursts are scaled by Fx.density; emitters that run on their own have their Rate scaled (only
-- while below 100%: at full nothing is touched). KillFx reads Settings "gfx.particles" itself
local baseRate: { [ParticleEmitter]: number } = setmetatable({}, { __mode = "k" }) :: any
local density = 1
local function rate(pe: ParticleEmitter)
	local b = baseRate[pe]
	if b == nil then b = pe.Rate; baseRate[pe] = b end
	local want = (b :: number) * density
	if pe.Rate ~= want then pe.Rate = want end
end
workspace.DescendantAdded:Connect(function(d)
	if density < 1 and d:IsA("ParticleEmitter") then task.defer(rate, d) end
end)
Settings.watch("gfx.particles", function(v: any)
	local was = density
	density = math.clamp(if type(v) == "number" then v else 1, 0.1, 1)
	local okFx, Fx = pcall(require, script.Parent:WaitForChild("Fx"))
	if okFx and type(Fx) == "table" then (Fx :: any).density = density end
	if was == density then return end
	task.spawn(function()
		for i, d in workspace:GetDescendants() do
			if d:IsA("ParticleEmitter") and (density < 1 or baseRate[d] ~= nil) then rate(d) end
			if i % 4000 == 0 then task.wait() end
		end
	end)
end)
-- view distance: how near you must be before ZoneCull draws a map (its attribute Margin, studs)
local VIEW = { near = 140, normal = 250, far = 600 }
Settings.watch("gfx.view", function(v: any)
	local zc = script.Parent:FindFirstChild("ZoneCull")
	if zc then zc:SetAttribute("Margin", VIEW[v] or 250) end
end)
-- the FPS readout: top left, under Roblox's buttons, frames a second and the round trip to the server
do
	local gui = Instance.new("ScreenGui")
	gui.Name = "JankFps"; gui.ResetOnSpawn = false; gui.IgnoreGuiInset = true; gui.DisplayOrder = 30; gui.Enabled = false
	gui.Parent = pg
	local lbl = T.text(gui, "Fps", "", 13, T.SOFT, T.FONT_BOLD)
	lbl.Position = UDim2.fromOffset(16, 62); lbl.Size = UDim2.fromOffset(200, 18); lbl.TextStrokeTransparency = 0.6
	local frames, acc = 0, 0
	local conn: RBXScriptConnection? = nil
	Settings.watch("gfx.fps", function(v: any)
		gui.Enabled = v == true
		if v == true and not conn then
			conn = RunService.RenderStepped:Connect(function(dt: number)
				frames += 1; acc += dt
				if acc >= 0.5 then
					local ping = 0
					pcall(function() ping = me:GetNetworkPing() * 2000 end)
					lbl.Text = ("%d FPS   %d MS"):format(math.floor(frames / acc + 0.5), math.floor(ping + 0.5))
					frames, acc = 0, 0
				end
			end)
		elseif v ~= true and conn then
			conn:Disconnect(); conn = nil
		end
	end)
end

-- ================================================================== HUD
Settings.watch("hud.scale", function(v: any)
	T.hudScale = math.clamp(if type(v) == "number" then v else 1, 0.6, 1.4)
	if T.rescaled then T.rescaled:Fire() end
end)
Settings.watch("hud.keys", function(v: any) me:SetAttribute("ShowKeys", v == true) end)
-- the enemy outline (the night-vision goggles' outlines on everyone else): its colour
local ENEMY = Settings.ENEMY
local GOGGLE = ENEMY.green
task.spawn(function()
	local fx = workspace:WaitForChild("JankfireItemFx", 60)
	if not fx then return end
	local function paint(h: Instance)
		if not h:IsA("Highlight") then return end
		local want = ENEMY[S("hud.enemy")] or GOGGLE
		if h:GetAttribute("EnemyGlow") or (h.OutlineColor :: Color3):ToHex() == GOGGLE:ToHex() then
			h:SetAttribute("EnemyGlow", true)
			h.OutlineColor = want
		end
	end
	fx.ChildAdded:Connect(paint)
	Settings.watch("hud.enemy", function() for _, h in fx:GetChildren() do paint(h) end end)
end)
