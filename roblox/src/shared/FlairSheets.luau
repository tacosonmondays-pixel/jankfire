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

return S
