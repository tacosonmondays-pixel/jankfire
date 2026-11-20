--!strict
-- GIFT FX: what a gift looks like to people, for anything on the server that gives someone something (19 Nov 2026).
-- the owner's GIFT tab (OwnerDev.server) uses it, and the shop's paid gifts can too: one present, one chat line, the
-- same names everywhere. it gives nothing itself: the giving stays with the module that owns the thing (Loot, Quests,
-- Vip, Purchases); call these after that answered yes
--   GiftFx.describe(kind, id, n) -> spec?, why?
--       kind "container" (id crate / bag / spray, n 1..999), "bundle" (a shop bundle or skin set id), "item" (id
--       "<type>:<id>", e.g. "wrap:ember"), "brass" or "coins" (the same: n 1..1,000,000), "tickets" (n 1..1,000,000),
--       "vip", "weapon" (a Robux weapon id). spec = { kind, id, qty, label = "5 CRATES", plain = "5 Crates",
--       items = the present's cards, what = "container:crate" (for logs) }. nil + why when it isn't a thing
--       the owner's XP and UNLOCKS (19 Nov): "xp" (n XP), "level" (n = the level), "mastery" (id a weapon, n its
--       mastery XP), "masterylevel" (id a weapon, n its mastery level): spec.kind "xp", spec.stats = what Stats.gift
--       takes. "unlock" (id any weapon with a lock: a Robux one or a level one) and "unlockall": spec.kind "unlock",
--       spec.ids = the weapons, for Purchases.unlockWeapons. the OWNER title is never a thing to give
--   GiftFx.present(to, fromName, spec)  the receiver's present box (GiftReveal.client: rise, spin, open, the loot
--       opening's cards). in a match it waits for a break between rounds and a toast says a gift came
--   GiftFx.say(byName, toName, what)    "<by> gifted <to> <what>" as a gold system line in this server's chat, for
--       everyone (OwnerDev.client posts it: the legacy chat's ChatMakeSystemMessage, or a TextChatService system
--       message if the place moves). build it from display names and spec.plain, never from anything a player typed
--   GiftFx.line(text)                   any gold system line in this server's chat (the owner's announcements use it;
--       typed text must have been through TextService's filter first)
--   GiftFx.remote                        the RemoteEvent all of this goes through (JankfireRemotes.DevFx, made here)
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Remotes = ReplicatedStorage:WaitForChild("JankfireRemotes")
local Shared = ReplicatedStorage:WaitForChild("Jankfire")

local GiftFx = {}

local fx = Remotes:FindFirstChild("DevFx")
if not fx or not fx:IsA("RemoteEvent") then
	local e = Instance.new("RemoteEvent")
	e.Name = "DevFx"
	e.Parent = Remotes
	fx = e
end
GiftFx.remote = fx :: RemoteEvent

GiftFx.CONTAINER_MAX = 999
GiftFx.CURRENCY_MAX = 1000000

local function count(v: unknown, hi: number): number?
	if type(v) ~= "number" or v ~= v then return nil end
	local n = math.floor(v)
	return if n >= 1 and n <= hi then n else nil
end
local function roster(): any return require(Shared:WaitForChild("Roster")) :: any end
local function commas(n: number): string
	local s = tostring(math.floor(n))
	local out = string.reverse((string.gsub(string.reverse(s), "(%d%d%d)", "%1,")))
	return (string.gsub(out, "^,", ""))
end

function GiftFx.describe(kind: unknown, id: unknown, n: unknown): (any, string?)
	local Shop = require(Shared:WaitForChild("Shop")) :: any
	local LootTable = require(Shared:WaitForChild("LootTable")) :: any
	if kind == "container" then
		local c = type(id) == "string" and LootTable.CONTAINERS[id]
		local qty = count(n, GiftFx.CONTAINER_MAX)
		if not c or not qty then return nil, "which container, and 1 to " .. GiftFx.CONTAINER_MAX end
		local so = Shop.byId[id]
		return {
			kind = "container", id = id, qty = qty,
			label = ("%d %s"):format(qty, string.upper(if qty == 1 then c.name else c.plural)),
			plain = ("%d %s"):format(qty, if qty == 1 then c.name else c.plural),
			items = { { type = "container", id = id, name = c.name, rarity = if so and so.rarity then so.rarity else "rare", n = qty } },
			what = "container:" .. (id :: string),
		}
	elseif kind == "bundle" then
		local o = type(id) == "string" and Shop.byId[id]
		if not o or o.type ~= "bundle" then return nil, "no such bundle" end
		local items = {}
		for _, it in (if type(Shop.contents) == "function" then Shop.contents(o) else {}) :: any do
			local inf = type(it) == "table" and LootTable.info(it.kind, it.id)
			if inf and #items < 12 then table.insert(items, { type = it.kind, id = it.id, name = inf.name, rarity = inf.rarity, weapon = it.weapon or inf.weapon }) end
		end
		return { kind = "bundle", id = id, qty = 1, label = string.upper(o.name), plain = tostring(o.name), items = items, what = "bundle:" .. (id :: string) }
	elseif kind == "item" then
		local t, iid = string.match(tostring(id), "^(%a+):([%w_]+)$")
		local info = t and iid and LootTable.info(t, iid)
		if not info then return nil, "no such item" end
		if info.rarity == "owner" then return nil, "the OWNER title stays yours alone" end
		return {
			kind = "item", id = tostring(id), qty = 1, label = string.upper(info.name), plain = tostring(info.name),
			items = { { type = t, id = iid, name = info.name, rarity = info.rarity, weapon = info.weapon } }, what = "item:" .. tostring(id),
		}
	elseif kind == "brass" or kind == "coins" or kind == "tickets" then
		local k = if kind == "tickets" then "tickets" else "brass" -- (coins are Brass: the shop's word, 18 Nov)
		local qty = count(n, GiftFx.CURRENCY_MAX)
		if not qty then return nil, "how many" end
		return {
			kind = k, qty = qty,
			label = ("%d %s"):format(qty, if k == "brass" then "COINS" elseif qty == 1 then "CRATE TICKET" else "CRATE TICKETS"),
			plain = ("%d %s"):format(qty, if k == "brass" then "Coins" elseif qty == 1 then "Crate Ticket" else "Crate Tickets"),
			items = { { type = if k == "brass" then "brass" else "tix", id = k, name = if k == "brass" then "Coins" else "Crate Tickets", rarity = "rare", n = qty } },
			what = k,
		}
	elseif kind == "vip" then
		return { kind = "vip", qty = 1, label = "VIP", plain = "VIP", items = { { type = "vip", id = "vip", name = "VIP", rarity = "vip" } }, what = "vip" }
	elseif kind == "weapon" then
		local Unlocks = require(Shared:WaitForChild("Unlocks")) :: any
		local Roster = require(Shared:WaitForChild("Roster")) :: any
		local e = type(id) == "string" and Roster.byId[id]
		if not e or not (type(Unlocks.robux) == "function" and Unlocks.robux(id)) then return nil, "not a Robux weapon" end
		return {
			kind = "weapon", id = id, qty = 1, label = string.upper(e.name), plain = tostring(e.name),
			items = { { type = "weapon", id = id, name = e.name, rarity = "legendary" } }, what = "weapon:" .. (id :: string),
		}
	elseif kind == "unlock" then
		local e = type(id) == "string" and GiftFx.lockable(id) and roster().byId[id]
		if not e then return nil, "not a weapon with a lock" end
		return {
			kind = "unlock", id = id, ids = { id }, qty = 1, label = string.upper(e.name), plain = tostring(e.name),
			items = { { type = "weapon", id = id, weapon = id, name = e.name, rarity = "legendary" } }, what = "unlock:" .. (id :: string),
		}
	elseif kind == "unlockall" then
		local ids = GiftFx.lockables()
		return {
			kind = "unlock", id = "all", ids = ids, qty = #ids, label = "EVERY WEAPON", plain = "every weapon",
			items = { { type = "weapon", id = "all", name = "Every weapon", rarity = "legendary", big = "ALL" } }, what = "unlock:all",
		}
	elseif kind == "xp" or kind == "level" then
		local Stats = GiftFx.statsLimits()
		if kind == "xp" then
			local qty = count(n, Stats.xp)
			if not qty then return nil, "how much XP: 1 to " .. commas(Stats.xp) end
			return {
				kind = "xp", qty = qty, stats = { xp = qty }, label = commas(qty) .. " XP", plain = commas(qty) .. " XP",
				items = { { type = "xp", id = "xp", name = commas(qty) .. " XP", rarity = "rare", big = "XP" } }, what = "xp",
			}
		end
		local lv = count(n, Stats.level)
		if not lv or lv < 2 then return nil, "which level: 2 to " .. Stats.level end
		return {
			kind = "xp", qty = lv, stats = { level = lv }, label = "LEVEL " .. lv, plain = "Level " .. lv,
			items = { { type = "xp", id = "level", name = "Level " .. lv, rarity = "epic", big = "LV " .. lv } }, what = "level",
		}
	elseif kind == "mastery" or kind == "masterylevel" then
		local M = require(Shared:WaitForChild("Mastery")) :: any
		local e = type(id) == "string" and M.levels(id) and roster().byId[id]
		if not e then return nil, "not a weapon with mastery" end
		local name = string.upper(e.name)
		if kind == "mastery" then
			local qty = count(n, GiftFx.statsLimits().xp)
			if not qty then return nil, "how much mastery XP" end
			return {
				kind = "xp", id = id, qty = qty, stats = { w = id, xp = qty }, label = ("%s %s MASTERY XP"):format(commas(qty), name),
				plain = ("%s %s Mastery XP"):format(commas(qty), tostring(e.name)),
				items = { { type = "mastery", id = id, weapon = id, name = commas(qty) .. " Mastery XP", rarity = "rare", big = "+" .. commas(qty) } },
				what = "mastery:" .. (id :: string),
			}
		end
		local lv = count(n, M.MAX)
		if not lv or lv < 2 then return nil, "which mastery level: 2 to " .. M.MAX end
		return {
			kind = "xp", id = id, qty = lv, stats = { w = id, level = lv }, label = ("%s MASTERY %d"):format(name, lv),
			plain = ("%s Mastery %d"):format(tostring(e.name), lv),
			items = { { type = "mastery", id = id, weapon = id, name = "Mastery " .. lv, rarity = "epic", big = "LV " .. lv } },
			what = "masterylevel:" .. (id :: string),
		}
	end
	return nil, "nope"
end

-- (the owner's XP and UNLOCKS, 19 Nov) a weapon with a lock: live, and a Robux one or one that opens past level 1
-- (Purchases.lockable says the same on the giving side), and every one of them in roster order
function GiftFx.lockable(wid: any): boolean
	local Unlocks = require(Shared:WaitForChild("Unlocks")) :: any
	local e = type(wid) == "string" and roster().byId[wid]
	return e ~= nil and e ~= false and e.live == true and (Unlocks.robux(wid) or Unlocks.level(wid) > 1)
end
function GiftFx.lockables(): { string }
	local out = {}
	for _, e in roster().list do if GiftFx.lockable(e.id) then table.insert(out, e.id) end end
	return out
end
-- the most XP in one gift and the highest level (Stats.GIFT_XP_MAX / GIFT_LEVEL_MAX; these if Stats isn't there)
function GiftFx.statsLimits(): { xp: number, level: number }
	local sc = script.Parent:FindFirstChild("Stats")
	local ok, S = false, nil
	if sc and sc:IsA("ModuleScript") then ok, S = pcall(require, sc) end
	local s = if ok and type(S) == "table" then S else {} :: any
	return { xp = tonumber(s.GIFT_XP_MAX) or 10000000, level = tonumber(s.GIFT_LEVEL_MAX) or 500 }
end

function GiftFx.present(to: Player, fromName: string, spec: any)
	if typeof(to) ~= "Instance" or not to:IsA("Player") or type(spec) ~= "table" then return end
	GiftFx.remote:FireClient(to, { k = "gift", text = "GIFT · " .. tostring(spec.label), from = string.sub(tostring(fromName), 1, 32), items = spec.items })
end

function GiftFx.line(text: string)
	GiftFx.remote:FireAllClients({ k = "giftchat", text = string.sub(tostring(text), 1, 200) })
end

function GiftFx.say(byName: string, toName: string, what: string)
	GiftFx.line(("%s gifted %s %s"):format(tostring(byName), tostring(toName), tostring(what)))
end

return GiftFx
