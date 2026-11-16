--!strict
-- a way for a Studio play test to reach the running server. the Studio MCP's own Luau runs beside the game with its
-- own copies of the modules, so it can't see the fighters; this gives it a BindableFunction, ServerStorage.JankTest,
-- that ONLY exists in Studio (nothing here runs in a live server, and a client can never call a BindableFunction).
-- a test can arm itself with any weapons WITHOUT touching the saved loadout, and read the server's own numbers (HP,
-- ammo, the Yeehaw's chain) to check them against the spec.
--   local T = game.ServerStorage.JankTest
--   T:Invoke("arm", player, { "smg", "revolver", "katana" })   -> true (this life only, not saved)
--   T:Invoke("me", player)    -> { hp, alive, held, ammo = { smg = 45 }, chain, aiming, kills }
--   T:Invoke("all")           -> { { name, kind, hp, alive, pos } ... }
--   T:Invoke("hp", "Dummy", 100)  -> sets a fighter's HP by name (a dummy that must survive a volley)
--   T:Invoke("item", player, "frag") -> gives this life that item with full charges (nil: just read) and returns the
--     server's numbers: { item, n, next, heal, hp, projs, bubbles, clouds }
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")

local TestHook = {}

function TestHook.init(Fight: any, Rules: any, Weapons: any)
	if not RunService:IsStudio() then return end
	local old = ServerStorage:FindFirstChild("JankTest")
	if old then old:Destroy() end
	local fn = Instance.new("BindableFunction")
	fn.Name = "JankTest"
	fn.OnInvoke = function(op: any, a: any, b: any, c: any): any
		if op == "arm" then
			local f = Fight.byPlayer[a]
			if not f or type(b) ~= "table" or #b ~= 3 then return false end
			for _, id in b do if not Weapons.list[id] then return false end end
			f.nextLoadout = table.clone(b)
			Rules.arm(f, os.clock())
			Fight.showWeapon(f)
			a:SetAttribute("Loadout", table.concat(b, ","))
			a:SetAttribute("ArmT", (tonumber(a:GetAttribute("ArmT")) or 0) + 1)
			return true
		elseif op == "me" then
			local f = Fight.byPlayer[a]
			if not f then return nil end
			local ammo = {}
			for id, am in f.ammo do ammo[id] = am.mag end
			return { hp = f.hp, alive = f.alive, held = f.held, ammo = ammo, chain = if f.lev then f.lev.k else 0, aiming = f.aimT ~= nil, kills = f.kills }
		elseif op == "all" then
			local out = {}
			for _, f in Fight.all do
				local r = Fight.root(f)
				table.insert(out, { name = f.name, kind = f.kind, hp = f.hp, alive = f.alive, pos = if r then r.Position else nil })
			end
			return out
		elseif op == "item" then
			local f = Fight.byPlayer[a]
			if not f then return nil end
			return require(script.Parent:WaitForChild("Utility")).test(f, if type(b) == "string" then b else nil)
		elseif op == "smoke" then -- (a, b: two points) does a smoke cloud stand between them
			return Fight.smokeBlocks(a, b)
		elseif op == "rev" then -- (a fighter's name or model, secs) a reverse card on them: Utility.testReverse
			for _, f in Fight.all do
				if (f.name == a or Fight.model(f) == a) and f.alive then require(script.Parent:WaitForChild("Utility")).testReverse(f, if type(b) == "number" then b else 3); return true end
			end
			return false
		elseif op == "hurt" then -- (a fighter's name or model, amount, by: a player) one hit through Fight.hurt; their HP after
			for _, f in Fight.all do
				if (f.name == a or Fight.model(f) == a) and f.alive and type(b) == "number" then
					Fight.hurt(f, b, if typeof(c) == "Instance" then Fight.byPlayer[c] else nil, "test", false)
					return f.hp
				end
			end
			return nil
		elseif op == "hp" then
			for _, f in Fight.all do
				if f.name == a and f.alive and type(b) == "number" then f.hp = b; Fight.syncHp(f); return true end
			end
			return false
		end
		return nil
	end
	fn.Parent = ServerStorage
end

return TestHook
