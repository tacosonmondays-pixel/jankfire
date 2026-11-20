-- the black-backed texture rule (20 Nov 2026; kill-effects found it on Static, v1133; main for the Combat templates):
-- a texture with a black (or dark, low-alpha) background shows that square whenever its emitter's LightEmission is under
-- 1, so such an emitter gets LightEmission 1 (black adds nothing) and is kept quiet with Brightness (at most CAP) and FADE
-- more transparency instead. The pack's own dark layers (negative LightEmission) are left alone unless their texture is
-- in DARK_TOO. DIM: textures already at LightEmission 1 whose faint background shows as a pale quad under a big
-- Brightness: Brightness at most CAP. Idempotent: an emitter done once carries BlackFix = what it had.
local BLACK = { %BLACK% }
local DARK_TOO = { %DARK% }
local DIM = { %DIM% }
local CAP, FADE = 2, 0.3
local set, dark, dim = {}, {}, {}
for _, id in BLACK do set[id] = true end
for _, id in DARK_TOO do dark[id] = true end
for _, id in DIM do dim[id] = true end
local function fixOne(d: ParticleEmitter): boolean
	local id = d.Texture:match("%d+$")
	if not id or d:GetAttribute("BlackFix") then return false end
	local le = d.LightEmission
	local conv = (set[id] and le >= 0 and le < 1) or (dark[id] and le < 0)
	local damp = dim[id] and le >= 1 and d.Brightness > CAP
	if not conv and not damp then return false end
	d:SetAttribute("BlackFix", string.format("LE %.2f B %.1f", le, d.Brightness))
	d.Brightness = math.min(d.Brightness, CAP)
	if conv then
		d.LightEmission = 1
		local tk = {}
		for _, kp in d.Transparency.Keypoints do
			table.insert(tk, NumberSequenceKeypoint.new(kp.Time, 1 - (1 - kp.Value) * (1 - FADE), kp.Envelope))
		end
		d.Transparency = NumberSequence.new(tk)
	end
	return true
end
local function fixTree(root: Instance): number
	local n = 0
	for _, d in root:GetDescendants() do
		if d:IsA("ParticleEmitter") and fixOne(d) then n += 1 end
	end
	return n
end
