--!strict
-- KILL EFFECT FLIPBOOKS: small looping previews of the kill effects for cards (the owner, 17 Nov 2026: "for kill effects
-- in shop can they be small previews? same with in inv?"). a ViewportFrame can't draw particles, so each effect is a
-- sprite sheet captured in Studio on a stand-in (the VFX session's), stepped frame by frame in an ImageLabel by the
-- client's FlairAnim (the shop's cards and inventory; anyone may use it). an effect with no sheet here keeps its still
-- tile (Flair.picture).
--   kill[id] = {
--     image = "rbxassetid://<n>", -- one upload, no text in it (the upload rules)
--     cols = 4, rows = 4, px = 256, -- the grid and one frame's size in the image's pixels
--     n = 16, fps = 10, hold = 0, -- frames used, frames a second, extra frames the last one stays before the loop
--     words = { text = "...", x = 0.2, y = 0.3, w = 0.6, h = 0.2, from = 4, to = 12, color = Color3? }?, -- live text
--       over the frames from..to (1-based) in the frame's 0..1 box (Blue Screen's words: images can't carry text)
--   }
-- the backdrop: the flair tile's dark (22, 24, 30), so a sheet sits on a card with no edge. data only: no requires
local S = {}

S.kill = {} :: { [string]: any }

-- the sheets (17 Nov 2026, the VFX session: tools/roblox/vfx/kill_sheets.py from Studio captures of a stand-in, 0.1 s a
-- frame; roblox/assets/kill-previews/). n stops a loop before its empty tail frames (the body gone, nothing left on
-- screen) so each one comes round again after a short beat. Ink has no sheet yet (its black ink was lost against the
-- capture's black: a retake on a lighter backdrop)
local function sheet(id: number, n: number): { [string]: any }
	return { image = "rbxassetid://" .. id, cols = 4, rows = 4, px = 256, n = n, fps = 10, hold = 0 }
end
S.kill.none = sheet(92097830523226, 10) -- (Gibs: the pieces land and lie still from frame 6)
S.kill.confetti = sheet(78711723291776, 14)
S.kill.dissolve = sheet(85070467429892, 15)
S.kill.grave = sheet(100876377252714, 16)
S.kill.cash = sheet(129154762764065, 15)
S.kill.pixel = sheet(90481731860274, 13)
S.kill.balloon = sheet(87486225947491, 15)
S.kill.shatter = sheet(99080843960243, 9)
S.kill.ember = sheet(131676615523232, 16)
S.kill.chicken = sheet(134327025965380, 14)
S.kill.bsod = sheet(98981813962072, 13)
-- (the words where the effect writes them: the panel's top line; the panel itself is x 0.246, y 0.312, w 0.68, h 0.562
-- on frames 2-9, a little smaller on 2 as it switches on)
S.kill.bsod.words = { text = "FATAL ERROR", x = 0.314, y = 0.368, w = 0.544, h = 0.084, from = 2, to = 9, color = Color3.fromRGB(214, 224, 244) }
S.kill.yeet = sheet(138930126356222, 8) -- (the body is out of sight above from frame 4)
S.kill.static = sheet(70597060116498, 10)
S.kill.ascend = sheet(74885896822851, 16)
S.kill.duck = sheet(121664077077152, 16)
S.kill.blastzone = sheet(127042928731850, 6) -- (knocked out of sight by frame 4)

return S
