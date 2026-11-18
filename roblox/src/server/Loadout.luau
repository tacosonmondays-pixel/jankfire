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
-- SKINS (GunSkins.luau): another body per weapon, from a crate. Only a skin you own (Inventory.owns, the loot
-- session's) and whose model is in the place (ReplicatedStorage.JankfireSkins); attribute "Skins" =
-- "ar=ar_toy;katana=katana_bokken", saved as `skins`; on right away, like a wrap. The Shredder's is a Tool of its own
-- TRY IN TRAINING (the owner, 17 Nov 2026: "when you're in the training hub you're free to use any weapon, and when you
-- leave it reloads your previous loadout"): in the training hall and its playground (the server's own zone,
-- Matches.zoneOf: the hall, the back lot, the basement, the playground) every pick goes into a layer of its own, d.try,
-- a copy of your loadout that is never saved and never owned: any live weapon, any skin, wrap or hat that exists (not
-- the guns session's concepts). the moment you're anywhere else (the hub, a match, a lobby; checked 5 times a second
-- and at every spawn) the layer goes, your saved loadout is back and, where re-arming is allowed, in your hands.
-- nothing tried reaches a match: f.nextLoadout always carries the saved picks (tried weapons are put in your hands on
-- the spot), and the looks a match, a replay or a finisher reads (Skins / Wraps / Hats) are the saved ones again
-- before any spawn outside training. the attribute "Trying" tells the loadout screen to mark what you're trying
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local DataStoreService = game:GetService("DataStoreService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Jankfire")
local Roster = require(Shared:WaitForChild("Roster"))
local WeaponModels = require(Shared:WaitForChild("WeaponModels"))
local GunHats = require(Shared:WaitForChild("GunHats"))
local GunSkins = require(Shared:WaitForChild("GunSkins"))
local LootTable = require(Shared:WaitForChild("LootTable")) :: any -- (REPLACED: a retired skin's successor, 18 Nov)
local Unlocks = require(Shared:WaitForChild("Unlocks")) :: any -- (weapons open by level, a few are Robux: docs/PROGRESSION.md)
local Rules = require(script.Parent:WaitForChild("Rules"))
local Utility = require(script.Parent:WaitForChild("Utility")) -- (the item on G: when a new pick goes in is its rule)
local Loot = require(script.Parent:WaitForChild("Loot")) -- (what you own: wraps and hats are won from Spray Cans and Duffel Bags, one gun at a time)
local Remote = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Loadout") :: RemoteFunction
local Tools = ReplicatedStorage:WaitForChild("JankfireTools")

local Loadout = {}
local STORE, VERSION = "JankfireLoadout_v1", 1
local DEFAULT = { primary = "ar", secondary = "pistol", melee = "katana", utility = "frag" } -- (all level 1: Unlocks. was the Redline and the Marble Shotgun until 18 Nov)
local SAVE_DELAY = 6 -- s after the last change (one write per burst of clicking)

type Data = {
	pick: { [string]: string }, wraps: { [string]: { id: string, mode: string } }, hats: { [string]: string },
	skins: { [string]: string }, try: any?,
	kept: { [string]: boolean }, u: number?, -- (weapons kept at any level, and whether that was worked out yet: Unlocks)
	loaded: boolean, canSave: boolean, dirty: boolean, saveAt: number, touched: boolean,
}
local data: { [Player]: Data } = {}
local Fight: any = nil

local function canHave(slot: string, wid: any): boolean
	local e = if type(wid) == "string" then Roster.byId[wid] else nil
	return e ~= nil and e.live and e.slot == slot
end
-- what you're wearing and carrying right now: the training try layer while it's on, else your saved loadout
local function layer(d: Data): any
	return d.try or d
end
-- the Shredder's wrap and hat, if you own them (Loot.owns; a saved pick you don't own stays saved but isn't worn).
-- trying in training: whatever you tried
local function ownedWrap(p: Player, d: Data?): { id: string, mode: string }?
	if d and d.try then return d.try.wraps.shredder end
	local w = d and d.wraps.shredder
	return if w and Loot.owns(p, "wrap", w.id, "shredder") then w else nil
end
local function ownedHat(p: Player, d: Data?): string?
	if d and d.try then return d.try.hats.shredder end
	local h = d and d.hats.shredder
	return if h and Loot.owns(p, "hat", h, "shredder") then h else nil
end
-- the SAVED weapons (what f.nextLoadout always carries, so nothing tried can reach a match)
local function list(d: Data): { string }
	return { d.pick.primary, d.pick.secondary, d.pick.melee }
end
-- every slot in Roster.SLOTS order (what the loadout screen reads): the three weapons, then the item (the ones you
-- have now: the try layer's while it's on)
local function slots(d: Data): { string }
	local L = layer(d)
	local out = {}
	for _, slot in Roster.SLOTS do table.insert(out, L.pick[slot] or DEFAULT[slot]) end
	return out
end

-- ------------------------------------------------------------------ what the clients see (player attributes)
local function publish(p: Player)
	local d = data[p]
	if not d then return end
	p:SetAttribute("LoadoutNext", table.concat(slots(d), ","))
	-- (trying in training: whatever you tried, owned or not; else only what you own is worn: a saved pick you don't
	-- own stays saved, and goes on the moment you win it)
	local L = layer(d)
	local free = d.try ~= nil
	local parts = {}
	for wid, w in L.wraps do if free or Loot.owns(p, "wrap", w.id, wid) then table.insert(parts, wid .. "=" .. w.id .. "/" .. w.mode) end end
	table.sort(parts)
	p:SetAttribute("Wraps", table.concat(parts, ";"))
	local hats = {}
	for wid, h in L.hats do if free or Loot.owns(p, "hat", h, wid) then table.insert(hats, wid .. "=" .. h) end end
	table.sort(hats)
	p:SetAttribute("Hats", table.concat(hats, ";"))
	p:SetAttribute("Trying", if free then true else nil)
	local skins = {}
	for wid, s in L.skins do table.insert(skins, wid .. "=" .. s) end
	table.sort(skins)
	p:SetAttribute("Skins", table.concat(skins, ";"))
	p:SetAttribute("LoadoutSave", if not d.loaded then "loading" elseif d.canSave then "cloud" else "off")
	local kept = {}
	for wid in d.kept do table.insert(kept, wid) end
	table.sort(kept)
	p:SetAttribute("WeaponsKept", if #kept > 0 then table.concat(kept, ",") else nil)
end

-- ------------------------------------------------------------------ where you are (the server's own zone)
-- one helper for every zone rule (Zones.luau, the utility-items session's: Matches.zoneOf, the Zone attribute until
-- Matches is up): the training hall, its back lot and basement, and the playground are where you try anything
local Zones = require(script.Parent:WaitForChild("Zones")) :: any
local function trying(p: Player): boolean return Zones.training(p) end
local tryArming: { [Player]: boolean } = {}
local tryArm: (Player) -> boolean = function() return false end -- (below)

-- ------------------------------------------------------------------ arming
local function syncTools(p: Player, f: any)
	local want = table.find(Rules.loadoutOf(f), "shredder") ~= nil
	local bag = p:FindFirstChildOfClass("Backpack")
	local ch = p.Character
	local d = data[p]
	-- its skin (a Tool of its own, "Shredder@<skin id>", handed over named "Shredder"): a Shredder in the wrong skin goes
	local sk = d and layer(d).skins.shredder
	local skinSrc = sk and Tools:FindFirstChild("Shredder@" .. sk)
	local wantSkin = if skinSrc then sk else nil
	local have: Tool? = nil
	for _, where in { bag, ch } :: { Instance? } do
		local t = where and where:FindFirstChild("Shredder")
		if t and t:IsA("Tool") then
			if want and not have and t:GetAttribute("Skin") == wantSkin then have = t else t:Destroy() end
		end
	end
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
	local d = data[p]
	if d and d.try and not tryArming[p] then
		if trying(p) then
			-- (a respawn in training: what you were trying comes back in your hands)
			task.defer(tryArm, p)
		else
			-- (a spawn anywhere else, a match: the try is over before anything reads your looks or weapons)
			d.try = nil
			publish(p)
		end
	end
	p:SetAttribute("Loadout", table.concat(Rules.loadoutOf(f), ","))
	syncTools(p, f)
	p:SetAttribute("ArmT", (tonumber(p:GetAttribute("ArmT")) or 0) + 1)
end

-- the hub (not in a match, alive): the new picks go in now. returns whether it did. a re-arm refills every magazine,
-- so it only happens where no fight counts: the hub, the training hall and its playground (an allow-list, so a new
-- arena or match zone can never refill mid-fight; anti-cheat audit, 17 Nov 2026)
local REARM_ZONES = { hub = true, training = true, playground = true }
-- (and a round-based match's loadout window, 17 Nov, the owner: "allow us to change weapons before first round and
-- between rounds": the countdown before a round and the break between rounds, when no damage counts. the server's
-- Matches sets LoadoutWindow on its players for it and clears it the moment the round goes live; a classic mode never
-- sets it. play-party-ranked's)
-- (18 Nov: READY locks your set for the round: LoadoutReady, Matches.ready)
local function inWindow(p: Player): boolean
	return p:GetAttribute("Zone") == "match" and p:GetAttribute("LoadoutWindow") ~= nil and p:GetAttribute("LoadoutReady") ~= true
end
local function rearmInHub(p: Player): boolean
	local f = Fight and Fight.byPlayer[p]
	if not f or not f.alive or not (REARM_ZONES[p:GetAttribute("Zone") :: any] or inWindow(p)) then return false end
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

-- ------------------------------------------------------------------ the training try layer
local function copyLayer(d: Data): any
	local wraps = {}
	for wid, w in d.wraps do wraps[wid] = { id = w.id, mode = w.mode } end
	return { pick = table.clone(d.pick), wraps = wraps, hats = table.clone(d.hats), skins = table.clone(d.skins) }
end
-- the tried weapons in your hands now (training re-arms on the spot), then f.nextLoadout back to the saved picks
tryArm = function(p: Player): boolean
	local d = data[p]
	local f = Fight and Fight.byPlayer[p]
	if not d or not d.try or not f or not f.alive or tryArming[p] or not trying(p) then return false end
	tryArming[p] = true
	local L = d.try
	f.nextLoadout = { L.pick.primary, L.pick.secondary, L.pick.melee }
	Rules.arm(f, os.clock())
	f.nextLoadout = list(d)
	Utility.pick(f, L.pick.utility, true)
	Fight.showWeapon(f)
	armed(f)
	tryArming[p] = nil
	return true
end
-- leaving training: the layer goes; your saved loadout is back, in your hands where re-arming is allowed (the hub)
local function endTry(p: Player)
	local d = data[p]
	if not d or not d.try then return end
	d.try = nil
	publish(p)
	pushNext(p)
	local f = Fight and Fight.byPlayer[p]
	if f and f.alive and not rearmInHub(p) then
		-- (where a re-arm isn't allowed, a match: its next spawn takes the saved picks; the looks are back now)
		Fight.showWeapon(f)
		syncTools(p, f)
	end
end
Loadout.endTry = endTry
-- the guns session's concepts (for the owner to choose from) aren't tried either
local function concept(id: string): boolean
	local m = Shared:FindFirstChild("SkinSets")
	if not (m and m:IsA("ModuleScript")) then return false end
	local ok, K = pcall(require, m)
	return ok and type(K) == "table" and type((K :: any).CONCEPTS) == "table" and table.find((K :: any).CONCEPTS, id) ~= nil
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
	if type(saved.kept) == "table" then
		for _, wid in saved.kept do if type(wid) == "string" and Roster.byId[wid] then d.kept[wid] = true end end
	end
	if type(saved.u) == "number" then d.u = saved.u end
	if type(saved.skins) == "table" then
		for wid, s0 in saved.skins do
			local e = if type(wid) == "string" then Roster.byId[wid] else nil
			-- (a skin retired for another, LootTable.REPLACED, 18 Nov: a worn old Seraph Rifle is the owner's Tripo one now)
			local s = if type(s0) == "string" and LootTable.REPLACED[s0] then LootTable.REPLACED[s0] else s0
			if e and e.live and GunSkins.valid(wid, s) then d.skins[wid] = s end
		end
	end
end

local function key(p: Player): string return "u" .. p.UserId end

-- (18 Nov: weapons open by level now. nobody loses anything: what a player already carried or used stays theirs at any
-- level, worked out once per player: their saved picks and every weapon their stats show they've used)
local function grandfatherWeapons(p: Player, d: Data)
	local okS, S = pcall(function() return require(script.Parent:WaitForChild("Stats", 10) :: ModuleScript) end)
	local used: { string }? = nil
	local t0 = os.clock()
	while p.Parent and data[p] == d and os.clock() - t0 < 30 do
		if okS and type(S) == "table" and type((S :: any).usedWeapons) == "function" then used = (S :: any).usedWeapons(p) end
		if used then break end
		task.wait(1)
	end
	if not used or not p.Parent or data[p] ~= d or d.u ~= nil then return end -- (stats unreadable: next join)
	for _, slot in Roster.SLOTS do
		local w = d.pick[slot]
		if w and Unlocks.level(w) > 1 then d.kept[w] = true end
	end
	for _, w in used do
		if Roster.byId[w] and Unlocks.level(w) > 1 then d.kept[w] = true end
	end
	d.u = 1
	d.dirty, d.saveAt = true, os.clock() + SAVE_DELAY
	publish(p)
end

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
		if d.u == nil then task.spawn(grandfatherWeapons, p, d) end
	end
	publish(p)
	pushNext(p)
	-- the first life started on the defaults while this loaded: in the hub, swap now
	if ok and not d.touched then rearmInHub(p) end
end

-- saves still writing: a server closing waits for them (18 Nov: the last player's leave-save was cut off when the
-- server shut down, since PlayerRemoving had already taken them out of data and BindToClose saw nobody)
local inflight = 0
local function save(p: Player)
	local d = data[p]
	if not d or not d.canSave or not d.dirty or not store then return end
	d.dirty = false
	inflight += 1
	local wraps = {}
	for wid, w in d.wraps do wraps[wid] = { w.id, w.mode } end
	local kept = {}
	for wid in d.kept do table.insert(kept, wid) end
	local payload = { v = VERSION, pick = table.clone(d.pick), wraps = wraps, hats = table.clone(d.hats), skins = table.clone(d.skins), kept = kept, u = d.u }
	local ok, err = retry(function() return (store :: DataStore):UpdateAsync(key(p), function() return payload end) end)
	inflight -= 1
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

-- ------------------------------------------------------------------ the remote: ("pick", slot, weapon) / ("wrap", weapon, wrap, mode) / ("hat", weapon, hat) / ("skin", weapon, skin) / ("arm")
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
	-- (in training every pick goes into the try layer: never saved, never owned; out of it, a leftover layer goes)
	local tr = trying(p)
	-- (the owner's dev weapons in the hub, DevArms (OwnerDev), borrow the try layer for WEAPONS only: a look picked there,
	-- a skin, a wrap or a hat, is the owner's own and saved like anywhere else, and shows in the layer too. 18 Nov, the
	-- owner: "it didn't save my skin options": every pick made with DevArms on went into the never-saved layer)
	local look = op == "wrap" or op == "hat" or op == "skin"
	local devHub = tr and Zones.TRAINING[Zones.of(p)] ~= true
	if d.try and not tr then endTry(p) end
	if tr and not d.try and (op == "pick" or (look and not devHub)) then d.try = copyLayer(d) end
	local L = if look and devHub then d else layer(d)
	local free = d.try ~= nil and not (look and devHub)
	local function done()
		if look and devHub and d.try and type(a) == "string" then
			local w = d.wraps[a]
			d.try.wraps[a] = if w then { id = w.id, mode = w.mode } else nil
			d.try.hats[a] = d.hats[a]
			d.try.skins[a] = d.skins[a]
		end
		if free then publish(p) else changed(p) end
	end
	if op == "pick" then
		if type(a) ~= "string" or not table.find(Roster.SLOTS, a) or type(b) ~= "string" then return false, "nope" end
		local e = Roster.byId[b]
		if not e or e.slot ~= a then return false, "wrong slot" end
		if not e.live then return false, "coming soon. it's not on roblox yet" end
		-- (in a match: only in the loadout window, never while a round is live)
		if not free and p:GetAttribute("Zone") == "match" and not inWindow(p) then
			return false, if p:GetAttribute("LoadoutReady") then "you're locked in for this round" else "the loadout opens before a round and between rounds"
		end
		-- (weapons open by level, a few are Robux: Unlocks. trying in training is still anything)
		if not free then
			local okU, whyU = Unlocks.forPlayer(p, b)
			if not okU then return false, if whyU == "ROBUX" then "a robux weapon" else string.lower(whyU or "locked") .. " unlocks it" end
		end
		if L.pick[a] == b then return true, nil end
		L.pick[a] = b
		done()
		if free then tryArm(p) else pushNext(p) end
		if not free and inWindow(p) then rearmInHub(p) end -- (the window: in your hands now; dead, at the next round's spawn)
		return true, nil
	elseif op == "wrap" then
		if type(a) ~= "string" or type(b) ~= "string" or type(c) ~= "string" then return false, "nope" end
		local e = Roster.byId[a]
		if not e or not e.live then return false, "that weapon isn't on roblox yet" end
		if not Roster.wrapById[b] or not table.find(Roster.MODES, c) then return false, "that wrap doesn't exist" end
		if not free and not Loot.owns(p, "wrap", b, a) then return false, "you don't own that one for this gun yet. it's in spray cans" end
		if b == "default" and c == "normal" then L.wraps[a] = nil else L.wraps[a] = { id = b, mode = c } end
		done()
		-- paint: right away (it's only a look), on what others see in your hand and on the Shredder
		local f = Fight and Fight.byPlayer[p]
		if f and f.alive and f.held == a then Fight.showWeapon(f) end
		if a == "shredder" and f then syncTools(p, f) end
		return true, nil
	elseif op == "hat" then
		if type(a) ~= "string" or type(b) ~= "string" then return false, "nope" end
		local e = Roster.byId[a]
		if not e or not e.live then return false, "that weapon isn't on roblox yet" end
		if e.slot == "utility" then return false, "items don't wear hats" end
		if not GunHats.valid(b) then return false, "that hat doesn't exist" end
		if b ~= "none" and not free and not Loot.owns(p, "hat", b, a) then return false, "you don't own that one for this gun yet. it's in duffel bags" end
		local was = L.hats[a]
		L.hats[a] = if b == "none" then nil else b
		if was == L.hats[a] then return true, nil end
		done()
		-- on right away (it's only a look): what others see in your hand, and the Shredder
		local f = Fight and Fight.byPlayer[p]
		if f and f.alive and f.held == a then Fight.showWeapon(f) end
		if a == "shredder" and f then syncTools(p, f) end
		return true, nil
	elseif op == "skin" then
		if type(a) ~= "string" or type(b) ~= "string" then return false, "nope" end
		local e = Roster.byId[a]
		if not e or not e.live then return false, "that weapon isn't on roblox yet" end
		-- (the gadgets take wraps and skins since 18 Nov; hats stay on guns)
		if b ~= "default" then
			if not GunSkins.valid(a, b) then return false, "that skin isn't here yet" end
			if free then
				if concept(b) then return false, "that one's still a concept" end
			elseif not ownsSkin(p, b) then
				return false, "you don't own that skin"
			end
		end
		local was = L.skins[a]
		L.skins[a] = if b == "default" then nil else b
		if was == L.skins[a] then return true, nil end
		done()
		-- on right away (it's only a look): what others see in your hand, and the Shredder
		local f = Fight and Fight.byPlayer[p]
		if f and f.alive and f.held == a then Fight.showWeapon(f) end
		if a == "shredder" and f then syncTools(p, f) end
		return true, nil
	elseif op == "unlockall" then
		-- (the owner and Studio: every weapon open, or back to your level to see the locks)
		if not (RunService:IsStudio() or p.UserId == game.CreatorId) then return false, "nope" end
		p:SetAttribute("UnlockAll", if a == true then true else nil)
		return true, nil
	elseif op == "arm" then
		local f = Fight and Fight.byPlayer[p]
		if not f then return false, "nope" end
		if free then return true, if tryArm(p) then "armed" else "same" end
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
	-- (a bad request must never break the handler: anything that throws is a plain "nope")
	local fine, ok, why = pcall(handle, p, op, a, b, c)
	if not fine then
		warn("[Loadout] request failed: " .. tostring(ok))
		return { ok = false, why = "nope" }
	end
	return { ok = ok, why = why }
end

local function added(p: Player)
	if data[p] then return end
	data[p] = { pick = table.clone(DEFAULT), wraps = {}, hats = {}, skins = {}, kept = {}, loaded = false, canSave = false, dirty = false, saveAt = 0, touched = false }
	-- (the owner, and every Studio test, start with every weapon open: Unlocks. "unlockall" false shows the locks)
	if RunService:IsStudio() or p.UserId == game.CreatorId then p:SetAttribute("UnlockAll", true) end
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
		tryArming[p] = nil
		save(p) -- (the saved loadout only: a try layer is never written)
		data[p] = nil
	end)
	-- a burst of clicks is one write, SAVE_DELAY s after the last one
	-- (a try ends within 0.2 s of leaving training, a teleport out included; a spawn outside it ends it at once: armed)
	local tryAcc = 0
	RunService.Heartbeat:Connect(function(dt)
		tryAcc += dt
		if tryAcc < 0.2 then return end
		tryAcc = 0
		for p, d in data do
			if d.try and not trying(p) then endTry(p) end
		end
	end)
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
		while (left > 0 or inflight > 0) and os.clock() - t0 < 25 do task.wait(0.1) end
		if inflight > 0 then warn("[jankfire] the server closed with " .. inflight .. " loadout save(s) still writing") end
	end)
end

return Loadout
