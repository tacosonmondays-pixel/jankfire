-- (26 Nov 2026, the owner: projectiles "arent fun or fair when people fly around so much") a projectile or a cart that
-- hits you while you hang on your grapple rope cuts it: the server sends Grapple "cut", "shot" (WeaponProj, CartServer).
-- Move.client lets go of the rope as for any cut; this tells the grapple server the rope is gone (Main.server) and plays
-- the recorded rope snap with the HUD's ROPE SNAPPED, as the rubber duck's black hole does
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Sfx = require(script.Parent:WaitForChild("Sfx")) :: any
local Hud = require(script.Parent:WaitForChild("Hud")) :: any
local GrappleR = ReplicatedStorage:WaitForChild("JankfireRemotes"):WaitForChild("Grapple") :: RemoteEvent
GrappleR.OnClientEvent:Connect(function(what: any, why: any)
	if what ~= "cut" or why ~= "shot" then return end
	GrappleR:FireServer("release")
	pcall(Hud.callout, "ROPE SNAPPED", 0.7)
	pcall(Sfx.play, "ropesnap")
end)
