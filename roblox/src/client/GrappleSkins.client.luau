--!strict
-- GRAPPLE SKINS: every grappling rope this client sees wears its owner's grapple skin (17 Nov 2026; the look of each
-- skin is shared/GrappleLook.luau). Look only: the swing is Move.client's and the server's, untouched.
-- Ropes are Beams in workspace.Terrain:
--   - with attribute Owner (a UserId): the server's rope for that player (server/Main.server.luau), everyone else's
--     view of it. The skin is that player's Grapple attribute (FlairServer publishes the one they wear). Our OWN
--     player's server copy is hidden by HideOwnRope (Move.client already drew ours), so it is skipped here.
--   - without Owner: our own rope, drawn by Move.client the moment we hook. The skin is our own Grapple attribute.
--   - attribute Skin (a grapple id) overrides both (a test hook: Beam:SetAttribute("Skin", "laser")).
-- Unknown or missing ids wear the plain "rope". A Beam already marked GrappleLook (the equip screen's preview) is
-- left alone. The head and the rope's tie come off when the Beam goes.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local GrappleLook = require(ReplicatedStorage:WaitForChild("Jankfire"):WaitForChild("GrappleLook")) :: any
local me = Players.LocalPlayer

local function valid(id: any): string
	return if type(id) == "string" and GrappleLook.LOOKS[id] then id else "rope"
end

-- the skin this rope wears, or nil for a rope we leave alone
local function skinFor(b: Beam): string?
	local owner = b:GetAttribute("Owner")
	if owner ~= nil and owner == me.UserId then return nil end -- (our own server copy: hidden, ours is drawn by Move)
	local forced = b:GetAttribute("Skin")
	if forced ~= nil then return valid(forced) end
	if owner ~= nil then
		local p = if type(owner) == "number" then Players:GetPlayerByUserId(owner) else nil
		return valid(p and p:GetAttribute("Grapple"))
	end
	return valid(me:GetAttribute("Grapple"))
end

local function watch(c: Instance)
	if not c:IsA("Beam") then return end
	local b = c :: Beam
	if b:GetAttribute("GrappleLook") ~= nil then return end
	task.spawn(function()
		-- (a replicated rope's ends can land a moment after the Beam)
		local t0 = os.clock()
		while b.Attachment1 == nil and b.Parent ~= nil and os.clock() - t0 < 3 do task.wait() end
		if b.Parent == nil or b.Attachment1 == nil then return end
		local stop: (() -> ())? = nil
		local function wear()
			if stop then stop(); stop = nil end
			local id = skinFor(b)
			if not id or b.Parent == nil then return end
			GrappleLook.dress(b, id)
			stop = GrappleLook.attach(b, id)
		end
		wear()
		local skinCon = b:GetAttributeChangedSignal("Skin"):Connect(wear)
		local goneCon: RBXScriptConnection? = nil
		goneCon = b.AncestryChanged:Connect(function(_, parent: Instance?)
			if parent ~= nil then return end
			skinCon:Disconnect()
			if goneCon then goneCon:Disconnect() end
			if stop then stop(); stop = nil end
		end)
	end)
end

for _, c in workspace.Terrain:GetChildren() do watch(c) end
workspace.Terrain.ChildAdded:Connect(watch)
