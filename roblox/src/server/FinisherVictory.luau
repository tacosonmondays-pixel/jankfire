--!strict
-- FINISHER VICTORY (27 Nov 2026): the cinematic finisher as the match's victory scene. The owner: "if you win with a
-- team and multipple people have different finishers, the person who did the best has theirs play against the enemy
-- best because weapon finishers are usualy duels". The victory scene (its own session's code) ranks the players and
-- asks here; FinisherServer (the owner of the cutscenes) fills these in at its start. Until then they answer "not ready".
--   FV.finisherOf(player, m) -> { fid, skin, w, scene, len }?
--       the cutscene this player would bring: a finisher with an in-game scene that one of their equipped skins owns
--       (several: the weapon with the most kills this match). Only scenes qualify - the other finishers are replays
--       of a recorded kill, and between the two best there is none.
--   FV.play(m, killer, victim) -> (ok, why, len?)
--       sends that scene to everyone in the match, `killer` (the best winner) against `victim` (the enemy best), and
--       holds the end screen on m.finisherUntil as the old match-winning cut did. false: play the default scene.
--   FV.ON: FinisherServer's own match-winning-kill cut stays on while this is false (the default, until the victory
--       scene calls FV.play live) - so no match ends with neither.
local FV = {}

FV.ON = false

function FV.finisherOf(_p: Player, _m: any): any?
	return nil
end

function FV.play(_m: any, _k: Player, _v: Player): (boolean, string, number?)
	return false, "not ready", nil
end

return FV
