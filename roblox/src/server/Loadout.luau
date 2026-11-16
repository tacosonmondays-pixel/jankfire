--!strict
-- the loadout (the screen on L / the hub button): which weapon sits on keys 1 2 3, the item on G (the utility slot,
-- Utility.luau) and each weapon's wrap. the server
-- owns it. it takes only weapons that are on roblox today (Roster live), each in its own slot, and wraps from the list;
-- it keeps them in a DataStore (pcall + retries; nothing is written for a player whose load failed, so a hiccup can't
-- wipe a save); new picks wait for your next spawn (Rules.arm takes nextLoadout) and never land mid-round. in the hub
-- the screen closing re-arms you on the spot. Combat refuses any weapon outside your loadout (Rules.inLoadout).
-- the Shredder is a Tool (ShredderServer): you only get one when it's your primary.
-- HATS (GunHats.luau): one per weapon, from the hat list (GunHatData), kept and saved beside the wraps (attribute
-- "Hats" = "ar=crown;katana=duck", saved as `hats`); a hat goes on right away, like a wrap
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local DataStoreService = game:GetService("DataStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Roster = require(Shared:WaitForChild("Roster"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local GunHats = require(Shared:WaitForChild("GunHats"))
local GunSkins = require(Shared:WaitForChild("GunSkins"))
local Rules = require(script.Parent:WaitForChild("Rules"))
local Utility = require(script.Parent:WaitForChild("Utility")) -- (the item on G: when a new pick goes in is its rule)
local Loot = require(script.Parent:WaitForChild("Loot")) -- (what you own: wraps and hats are won from Spray Cans and Duffel Bags, one gun at a time)
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Loadout") :: RemoteFunction
local Tools = ReplicatedStorage:WaitForChild("JankfireTools")

local Loadout = {}
local STORE, VERSION = "JankfireLoadout_v1", 1
local DEFAULT = { primary = "redline", secondary = "marbles", melee = "katana", utility = "frag" }
local SAVE_DELAY = 6 -- s after the last change (one write per burst of clicking)

type Data = {
	pick: { [string]: string }, wraps: { [string]: { id: string, mode: string } }, hats: { [string]: string },
	skins: { [string]: string },
	loaded: boolean, canSave: boolean, dirty: boolean, saveAt: number, touched: boolean,
}
local data: { [Player]: Data } = {}
local Fight: any = nil

local function canHave(slot: string, wid: any): boolean
	local e = if type(wid) == "string" then Roster.byId[wid] else nil
	return e ~= nil and e.live and e.slot == slot
end
-- the Shredder's wrap and hat, if you own them (Loot.owns; a saved pick you don't own stays saved but isn't worn)
local function ownedWrap(p: Player, d: Data?): { id: string, mode: string }?
	local w = d and d.wraps.shredder
	return if w and Loot.owns(p, "wrap", w.id, "shredder") then w else nil
end
local function ownedHat(p: Player, d: Data?): string?
	local h = d and d.hats.shredder
	return if h and Loot.owns(p, "hat", h, "shredder") then h else nil
end
local function list(d: Data): { string }
	return { d.pick.primary, d.pick.secondary, d.pick.melee }
end
-- every slot in Roster.SLOTS order (what the loadout screen reads): the three weapons, then the item
local function slots(d: Data): { string }
	local out = {}
	for _, slot in Roster.SLOTS do table.insert(out, d.pick[slot] or DEFAULT[slot]) end
	return out
end

-- ------------------------------------------------------------------ what the clients see (player attributes)
local function publish(p: Player)
	local d = data[p]
	if not d then return end
	p:SetAttribute("LoadoutNext", table.concat(slots(d), ","))
	local parts = {}
	-- (only what you own is worn: a saved pick you don't own stays saved, and goes on the moment you win it)
	for wid, w in d.wraps do if Loot.owns(p, "wrap", w.id, wid) then table.insert(parts, wid .. "=" .. w.id .. "/" .. w.mode) end end
	table.sort(parts)
	p:SetAttribute("Wraps", table.concat(parts, ";"))
	local hats = {}
	for wid, h in d.hats do if Loot.owns(p, "hat", h, wid) then table.insert(hats, wid .. "=" .. h) end end
	table.sort(hats)
	p:SetAttribute("Hats", table.concat(hats, ";"))
	local skins = {}
	for wid, s in d.skins do table.insert(skins, wid .. "=" .. s) end
	table.sort(skins)
	p:SetAttribute("Skins", table.concat(skins, ";"))
	p:SetAttribute("LoadoutSave", if not d.loaded then "loading" elseif d.canSave then "cloud" else "off")
end

-- ------------------------------------------------------------------ arming
local function syncTools(p: Player, f: any)
	local want = table.find(Rules.loadoutOf(f), "shredder") ~= nil
	local bag = p:FindFirstChildOfClass("Backpack")
	local ch = p.Character
	-- its skin (a Tool of its own, "Shredder@<skin id>", handed over named "Shredder"): a Shredder in the wrong skin goes
	local sk = data[p] and data[p].skins.shredder
	local skinSrc = sk and Tools:FindFirstChild("Shredder@" .. sk)
	local wantSkin = if skinSrc then sk else nil
	local have: Tool? = nil
	for _, where in { bag, ch } :: { Instance? } do
		local t = where and where:FindFirstChild("Shredder")
		if t and t:IsA("Tool") then
			if want and not have and t:GetAttribute("Skin") == wantSkin then have = t else t:Destroy() end
		end
	end
	local d = data[p]
	local wr = ownedWrap(p, d)
	if want and not have and bag then
		local src = skinSrc or Tools:FindFirstChild("Shredder")
		if src then
			local t = src:Clone()
			t.Name = "Shredder"
			t:SetAttribute("Skin", wantSkin)
			if wr then WeaponModels.wrap(t, wr.id, wr.mode) end
			GunHats.attachTool(t, ownedHat(p, d))
			t.Parent = bag
		end
	elseif have then
		WeaponModels.wrap(have, wr and wr.id, wr and wr.mode)
		GunHats.attachTool(have, ownedHat(p, d))
	end
end

-- after every (re)arm: tell the client which weapons are on its keys, give / take the Shredder
local function armed(f: any)
	if f.kind ~= "player" then return end
	local p = f.ref :: Player
	if not p.Parent then return end
	p:SetAttribute("Loadout", table.concat(Rules.loadoutOf(f), ","))
	syncTools(p, f)
	p:SetAttribute("ArmT", (tonumber(p:GetAttribute("ArmT")) or 0) + 1)
end

-- the hub (not in a match, alive): the new picks go in now. returns whether it did
local function rearmInHub(p: Player): boolean
	local f = Fight and Fight.byPlayer[p]
	if not f or not f.alive or p:GetAttribute("Zone") == "match" then return false end
	Rules.arm(f, os.clock())
	local d = data[p]
	if d then Utility.pick(f, d.pick.utility, true) end -- (the item too, charges used this life stay used)
	Fight.showWeapon(f)
	armed(f)
	return true
end

-- the picks Rules.arm takes at the next spawn
local function pushNext(p: Player)
	local d = data[p]
	local f = Fight and Fight.byPlayer[p]
	if d and f then
		f.nextLoadout = list(d)
		Utility.pick(f, d.pick.utility) -- (in at once while you're dead or in the first 5 s of a life, like the web game)
	end
end

-- ------------------------------------------------------------------ the DataStore
local store: DataStore? = nil
do
	local ok, s = pcall(function() return DataStoreService:GetDataStore(STORE) end)
	if ok then store = s end
end
local function retry(fn: () -> any): (boolean, any)
	local err: any = nil
	for i = 1, 3 do
		local ok, res = pcall(fn)
		if ok then return true, res end
		err = res
		if i < 3 then task.wait(i) end
	end
	return false, err
end
local warned = false
local function noStore(err: any)
	if warned then return end
	warned = true
	warn("[jankfire] loadouts won't save this session (" .. tostring(err) .. "). in Studio: Game Settings > Security > Enable Studio Access to API Services")
end

-- a saved loadout, checked like anything a client sends (a bad save just falls back to the defaults)
local function adopt(d: Data, saved: any)
	if type(saved) ~= "table" then return end
	if type(saved.pick) == "table" then
		for _, slot in Roster.SLOTS do
			if canHave(slot, saved.pick[slot]) then d.pick[slot] = saved.pick[slot] end
		end
	end
	if type(saved.wraps) == "table" then
		for wid, w in saved.wraps do
			local e = if type(wid) == "string" then Roster.byId[wid] else nil
			if e and e.live and type(w) == "table" and type(w[1]) == "string" and Roster.wrapById[w[1]]
				and type(w[2]) == "string" and table.find(Roster.MODES, w[2]) then
				d.wraps[wid] = { id = w[1], mode = w[2] }
			end
		end
	end
	if type(saved.hats) == "table" then
		for wid, h in saved.hats do
			local e = if type(wid) == "string" then Roster.byId[wid] else nil
			if e and e.live and GunHats.valid(h) and h ~= "none" then d.hats[wid] = h end
		end
	end
	if type(saved.skins) == "table" then
		for wid, s in saved.skins do
			local e = if type(wid) == "string" then Roster.byId[wid] else nil
			if e and e.live and GunSkins.valid(wid, s) then d.skins[wid] = s end
		end
	end
end

local function key(p: Player): string return "u" .. p.UserId end

local function load(p: Player)
	local d = data[p]
	if not store then noStore("no DataStoreService"); d.loaded = true; publish(p); return end
	local ok, res = retry(function() return (store :: DataStore):GetAsync(key(p)) end)
	if not p.Parent or data[p] ~= d then return end
	d.loaded, d.canSave = true, ok
	if not ok then noStore(res)
	elseif not d.touched then adopt(d, res) end -- (picks made while it loaded win)
	if ok then
		-- (what you wore before wraps and hats had to be won stays yours: Loot.grandfather, once per player)
		local old = {}
		for wid, w in d.wraps do table.insert(old, { type = "wrap", id = w.id, weapon = wid }) end
		for wid, h in d.hats do table.insert(old, { type = "hat", id = h, weapon = wid }) end
		Loot.grandfather(p, old)
	end
	publish(p)
	pushNext(p)
	-- the first life started on the defaults while this loaded: in the hub, swap now
	if ok and not d.touched then rearmInHub(p) end
end

local function save(p: Player)
	local d = data[p]
	if not d or not d.canSave or not d.dirty or not store then return end
	d.dirty = false
	local wraps = {}
	for wid, w in d.wraps do wraps[wid] = { w.id, w.mode } end
	local payload = { v = VERSION, pick = table.clone(d.pick), wraps = wraps, hats = table.clone(d.hats), skins = table.clone(d.skins) }
	local ok, err = retry(function() return (store :: DataStore):UpdateAsync(key(p), function() return payload end) end)
	if not ok then
		d.dirty = true; d.saveAt = os.clock() + 20
		warn("[jankfire] couldn't save " .. p.Name .. "'s loadout: " .. tostring(err))
	end
end

local function changed(p: Player)
	local d = data[p]
	d.dirty, d.touched, d.saveAt = true, true, os.clock() + SAVE_DELAY
	publish(p)
end

-- ------------------------------------------------------------------ the remote: ("pick", slot, weapon) / ("wrap", weapon, wrap, mode) / ("hat", weapon, hat) / ("arm")
local budget: { [Player]: { n: number, t: number } } = {}
local function spend(p: Player): boolean
	local b, t = budget[p], os.clock()
	if not b then b = { n = 30, t = t }; budget[p] = b end
	b.n = math.min(30, b.n + (t - b.t) * 6); b.t = t
	if b.n < 1 then return false end
	b.n -= 1
	return true
end

-- does the player own this skin? the loot session's Loot decides (won from Crates; in Studio its owner-only
-- "unlock all", the Loot remote op ("dev", "unlock"), opens them up to try)
local function ownsSkin(p: Player, id: string): boolean
	local mod = script.Parent:FindFirstChild("Loot")
	local ok, L = false, nil
	if mod and mod:IsA("ModuleScript") then ok, L = pcall(require, mod) end
	if not ok or type(L) ~= "table" then return false end
	local ok2, yes = pcall((L :: any).owns, p, "skin", id)
	return ok2 and yes == true
end

local function handle(p: Player, op: unknown, a: unknown, b: unknown, c: unknown): (boolean, string?)
	local d = data[p]
	if not d then return false, "still loading" end
	if op == "pick" then
		if type(a) ~= "string" or not table.find(Roster.SLOTS, a) or type(b) ~= "string" then return false, "nope" end
		local e = Roster.byId[b]
		if not e or e.slot ~= a then return false, "wrong slot" end
		if not e.live then return false, "coming soon. it's not on roblox yet" end
		if d.pick[a] == b then return true, nil end
		d.pick[a] = b
		changed(p); pushNext(p)
		return true, nil
	elseif op == "wrap" then
		if type(a) ~= "string" or type(b) ~= "string" or type(c) ~= "string" then return false, "nope" end
		local e = Roster.byId[a]
		if not e or not e.live then return false, "no paint on vapourware" end
		if e.slot == "utility" then return false, "items don't take paint" end
		if not Roster.wrapById[b] or not table.find(Roster.MODES, c) then return false, "that wrap doesn't exist" end
		if not Loot.owns(p, "wrap", b, a) then return false, "you don't own that one for this gun yet. it's in spray cans" end
		if b == "default" and c == "normal" then d.wraps[a] = nil else d.wraps[a] = { id = b, mode = c } end
		changed(p)
		-- paint: right away (it's only a look), on what others see in your hand and on the Shredder
		local f = Fight and Fight.byPlayer[p]
		if f and f.alive and f.held == a then Fight.showWeapon(f) end
		if a == "shredder" and f then syncTools(p, f) end
		return true, nil
	elseif op == "hat" then
		if type(a) ~= "string" or type(b) ~= "string" then return false, "nope" end
		local e = Roster.byId[a]
		if not e or not e.live then return false, "no hats on vapourware" end
		if e.slot == "utility" then return false, "items don't wear hats" end
		if not GunHats.valid(b) then return false, "that hat doesn't exist" end
		if b ~= "none" and not Loot.owns(p, "hat", b, a) then return false, "you don't own that one for this gun yet. it's in duffel bags" end
		local was = d.hats[a]
		d.hats[a] = if b == "none" then nil else b
		if was == d.hats[a] then return true, nil end
		changed(p)
		-- on right away (it's only a look): what others see in your hand, and the Shredder
		local f = Fight and Fight.byPlayer[p]
		if f and f.alive and f.held == a then Fight.showWeapon(f) end
		if a == "shredder" and f then syncTools(p, f) end
		return true, nil
	elseif op == "skin" then
		if type(a) ~= "string" or type(b) ~= "string" then return false, "nope" end
		local e = Roster.byId[a]
		if not e or not e.live then return false, "no skins on vapourware" end
		if e.slot == "utility" then return false, "items don't take skins" end
		if b ~= "default" then
			if not GunSkins.valid(a, b) then return false, "that skin isn't here yet" end
			if not ownsSkin(p, b) then return false, "you don't own that skin" end
		end
		local was = d.skins[a]
		d.skins[a] = if b == "default" then nil else b
		if was == d.skins[a] then return true, nil end
		changed(p)
		-- on right away (it's only a look): what others see in your hand, and the Shredder
		local f = Fight and Fight.byPlayer[p]
		if f and f.alive and f.held == a then Fight.showWeapon(f) end
		if a == "shredder" and f then syncTools(p, f) end
		return true, nil
	elseif op == "arm" then
		local f = Fight and Fight.byPlayer[p]
		if not f then return false, "nope" end
		local nxt = list(d)
		local cur = Rules.loadoutOf(f)
		if cur[1] == nxt[1] and cur[2] == nxt[2] and cur[3] == nxt[3] and Utility.itemOf(f) == d.pick.utility then return true, "same" end
		if rearmInHub(p) then return true, "armed" end
		return true, "next spawn"
	end
	return false, "nope"
end

Remote.OnServerInvoke = function(p: Player, op: unknown, a: unknown, b: unknown, c: unknown)
	if not spend(p) then return { ok = false, why = "slow down" } end
	local ok, why = handle(p, op, a, b, c)
	return { ok = ok, why = why }
end

local function added(p: Player)
	if data[p] then return end
	data[p] = { pick = table.clone(DEFAULT), wraps = {}, hats = {}, skins = {}, loaded = false, canSave = false, dirty = false, saveAt = 0, touched = false }
	publish(p)
	task.spawn(load, p)
end

function Loadout.init(fight: any)
	Fight = fight
	-- every spawn arms you (Rules.spawn -> Rules.arm); then the client hears what's on its keys and gets its tools
	fight.onSpawn(armed)
	-- what you own changed (a container opened, your things loaded): what everyone sees follows at once
	Loot.changed:Connect(function(p: Player)
		if not data[p] then return end
		publish(p)
		local f = Fight and Fight.byPlayer[p]
		if f and f.alive then
			Fight.showWeapon(f)
			syncTools(p, f)
		end
	end)
	for _, p in Players:GetPlayers() do added(p) end
	Players.PlayerAdded:Connect(added)
	Players.PlayerRemoving:Connect(function(p)
		budget[p] = nil
		save(p)
		data[p] = nil
	end)
	-- a burst of clicks is one write, SAVE_DELAY s after the last one
	local acc = 0
	RunService.Heartbeat:Connect(function(dt)
		acc += dt
		if acc < 1 then return end
		acc = 0
		local t = os.clock()
		for p, d in data do
			if d.dirty and d.canSave and t >= d.saveAt then
				d.saveAt = t + 30 -- (one write in flight at a time; save() clears dirty)
				task.spawn(save, p)
			end
		end
	end)
	game:BindToClose(function()
		local left = 0
		for p in data do
			left += 1
			task.spawn(function() save(p); left -= 1 end)
		end
		local t0 = os.clock()
		while left > 0 and os.clock() - t0 < 20 do task.wait(0.1) end
	end)
end

return Loadout
