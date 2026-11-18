# The owner's dev menu and the OWNER title

Asked for on 18 Nov 2026: "can you give me a special title for being owner, I get a command menu where I can fly,
noclip, fling people like a troll thingy for being dev, essentially I can give myself weapons in hub like remote freeze
and rewind people XD".

Files:

- `src/server/OwnerDev.server.luau`: checks and runs every command.
- `src/client/OwnerDev.client.luau`: the menu, plus everyone's frozen-body hold.
- The OWNER title: `src/shared/CardStyles.luau` (`OWNER`, `styleTitle`) and `src/server/Stats.luau` (who may wear it).

## Who and where

- **Only the place's creator** (`game.CreatorId` of a user-owned place) can use it. No name is written in the code.
  - The client builds the menu only for the creator, and only after the server says yes.
  - The server checks the creator on every single command. Anyone else gets "owner only", logged once.
- **It works everywhere, matches included.** The owner overrode the first "never in a match" rule on 18 Nov: "I can use it in matches, I'm the owner".
- **The safeguard: a match a dev power touches counts for nothing.** That covers the owner using any command in a match, having a power on while in one, or doing something to someone who is in one.
  - That match gets `m.dev = true`. It plays on normally.
  - From then on nobody's stats, rank, quests or loot change from it:
    - `Stats.liveFor`, `finish` and `onRound` skip it.
    - `Quests.matchCounts` skips it.
    - `RankedData.rate` and `onEnd` skip it, so a leaver's loss is skipped too.
  - Its players carry `MatchDev` (the match id). FightHud's end card then shows a small grey "DEV" in its top-right corner.
  - `MatchDev` comes off 15 s after the match is over for them.
  - Damage dealt before the flag went up already counted, because Stats writes hits as they land. The match's record, win/loss, XP and rank at the end are skipped entirely.
- **Every command is printed to the server log** as `[dev] <owner> <what> <target>`.
  - Refusals ("refused (not the owner)") and match flags ("match N flagged dev (...)") are logged too.

## Opening it

- **Keyboard:** F8, or `/dev` in chat. In the legacy chat the server hears `/dev` and bumps the `DevPanel` attribute.
- **Touch:** the small DEV button in the top-right corner, under the currency box. Only the owner has it.
- **Controller:** VIEW reaches the DEV button (it's in PadNav's menu column). Once the menu is open, B backs out.
- **Hotkeys, menu open or not:**
  - **X** flings whoever you're looking at.
  - **Z** freezes or lets go of whoever you're looking at.
  - **Y** shows a red card to whoever you're looking at.
- The menu frees the mouse but doesn't hold you still (it's a cursor-only MenuCursor name). You can fly with it open.

## The powers

Each power is a server attribute on the owner. The owner's client acts on it.

| Power | Attribute | What it does |
|---|---|---|
| FLY | `DevFly` = speed (studs/s, 20 to 300, default 80) | Moves you where the camera looks (WASD or the stick). Space or pad A goes up; Ctrl, C or pad B goes down. With nothing pressed you hold still in the air. A LinearVelocity plus AlignOrientation and PlatformStand drive the body. `Move.client` stands down while `Body.flying` is set. |
| NOCLIP | `DevNoclip` | Your body's parts stop colliding every step. The Humanoid still stands on floors, so walls become air. |
| RUN SPEED | `DevSpeed` (1x to 4x, in 0.25 steps) | `Body.devSpeed` multiplies your run speed in `Move.client`. |
| WEAPONS IN HUB | `DevArms` | Weapons come out in the hub (see below). |
| INVISIBLE | `DevInvisible` | Everyone else stops seeing your body, gun, name, title and pet. The server makes every part and decal of your character fully see-through, switches off its lights, effects and labels, and hides the name (`DisplayDistanceType` None). Each value is kept so it can be put back, including anything added later, such as a new gun or a respawn. OverheadTitles, Pets and ThirdPerson skip an invisible player. Your own client draws a faint ghost of you from each part's `DevWas` attribute. Footsteps and shots can still be heard. |
| (all of the above) | `DevOn` | Set while any power is on, and for 3 s after the last one goes off. The anti-cheat's pass. |

**WEAPONS IN HUB:**

- Every hub weapon check lets `DevArms` through. That covers `Fight.holstered`, Combat, HubHolster, HoldWeapons, WeaponProj, WeaponTricks (the TV Remote), ScytheDash, Lasso, Cart, CardDeck and Utility on the server, and Arsenal, Katana, SaucePour, ScytheDash, Utility, TouchControls and PadLook on the client.
- `Zones.training` is true for the owner in the hub while `DevArms` is on. So any weapon picked goes into the loadout's try layer, the one training uses: never saved, and gone when the switch goes off.
- The menu's GIVE ME A WEAPON grid lists every live roster weapon. A click switches DEV weapons on if needed, then picks the weapon through the Loadout remote.
- The TV Remote works on anyone in the hub: left click pauses them, right click rewinds them 2 s.

**What it can do to others** (any player, in a match too; in Studio also a training dummy, the test stand-in):

| Command | What it does |
|---|---|
| FLING | 170 studs/s away from you and 130 up, through `Fight.knock`, so the anti-cheat sees the push. It also tags the victim, so a fall afterwards counts as yours. |
| FREEZE / LET GO | Holds them still where they are. Their own client anchors the body (`DevFrozen`) and `Rules.stun` stops their shots. They are let go if they die or leave, and everyone is let go when the owner leaves. |
| GO TO / BRING | Moves you 5 studs in front of them, or them in front of you. Anywhere: a map room or a match keeps its own list of who's in it, so a player brought out is still counted there. |
| JAIL / FREE | Sends them to the jail (below), or lets them out to the hub. |
| RED CARD | Football style. On every screen the owner's right arm goes up with a red card in the hand for 1.2 s, and a referee's whistle blows where they stand. The whistle is a recording: Pro Sound Effects "Referee Whistle, Exterior, Single Blast", asset 9118113825, from Roblox's licensed library. The target's screen flashes a red card shape, with no text. Then they're sent to the jail. |
| UNFREEZE EVERYONE, EMPTY THE JAIL, ALL MY POWERS OFF | Buttons under the player list. |

**The jail** (the owner's "small room for funsey"):

- **The room:** `Map.DevJail`, built by the server the first time someone is sent there. It sits 420 studs over the hub's `Origin`, because anything 60 studs under it is the void.
  - It's a `ZonePiece`, so ZoneCull draws it only for whoever is near it.
  - Inside it's 22 x 12 x 18 studs, in quiet greys: bars across the front with a dark sealed corridor behind them, a bench with a rounded edge, a white ceiling light panel, and a small bright window behind glass. There's no text.
  - Every piece is solid and anchored, so walking, jumping and a grapple's ray all stop at the walls. The bars' gaps are 1.15 studs, narrower than a body.
- **Going in:** being sent there is a server move (`TeleportT`). The first 2.5 s put them back in if their client still reports the old spot.
  - A player sent from a match is taken out of it first (`Matches.pull`, as if they'd left). The match is flagged dev, so it counts for nothing.
- **Getting out:** whichever comes first:
  - 60 s pass (`JAIL_TIME`; the `DevJailed` attribute is the end time);
  - the owner frees them;
  - they join a party or a lobby;
  - they die, or anything else moves them out;
  - they leave the game.
- **Where they go:** a timed or freed release goes to their hub spawn (`Fight.spawnAt`). After a match, that's the hub, or their lobby's plinth if they're in a party.

## Nothing counts

- **Saves:** no command writes anyone's saves, stats, rank, quests, currency or loot.
- **Damage:** the owner's dev weapons can hurt players outside a match (`Matches.devHit`). Stats and quests only count hits in live matches, so those hits are never counted.
- **Kills:** a kill outside a match by the owner (a dev weapon, or a fall after a fling) goes through `Fight.devKill`. It shows no kill feed, runs no kill hooks (stats, quests, kill effects, finishers), and the kill and death counts are taken back. The victim respawns in the hub 1 s later.
- **Victims and the anti-cheat:** victims of a fling, bring or freeze get the anti-cheat's usual pass for a server move (`ACGrace`, `TeleportT`), the same as a TV Remote rewind. They do not get the owner's dev exemption.

## The anti-cheat

- **The flag:** `AntiCheat.server`'s `devOn(p)` is true only while `DevOn` is set and the player is the place's creator.
- **While it's on:**
  - No movement checks run.
  - A verdict "dev powers on: movement not checked" shows as the owner's last line in the F7 panel.
  - The owner's aim flags are written with a `[dev]` prefix.
- **When it goes off:** the checks start afresh from wherever the body is, after a 1 s grace.

## The OWNER title

- **Data:** CardStyles title `owner`, words "OWNER", rarity `owner`.
- **Look:** a warm gold, with a slow white light running across the words. One pass takes 3.5 s, followed by 2 s still (`CardStyles.styleTitle`).
  - The same look appears over the head (`OverheadTitles`), on the player card and its list (`ProfileUI`), and in the picker's sample.
- **Only the creator can wear it.** `Stats.owns` asks for the creator id, whatever any save, grant or Studio unlock says.
  - It is put on for the creator once, on their first visit after it came (`ownerTitle` in their stats save). They can take it off like any other title.
- **It can never be sold, rolled, bundled or granted.**
  - `CardStyles.isSecret` covers it, which keeps it out of the shop's singles, bundles and rotation.
  - `forSale` leaves it out, and the loot tables never roll a rarity they don't know.
  - The card's picker hides it from everyone else.

## Studio tests

- **Server script attributes:** `TestNotOwner = true` on `ServerScriptService.Jankfire.OwnerDev` makes the owner a stranger, so every command is refused.
- **`ServerStorage.JankDev`** (Studio only) answers:
  - `"state"`: the owner's switches, who's frozen, and the log.
  - `"as"` (player, op, a, b): runs a command as that player.
  - `"log"`: the log.
- **Client:** the player attribute `DevMenuTest` = `"open"` or `"close"` opens or closes the menu.
- **Commands from the Client datamodel:**
  ```lua
  game.ReplicatedStorage.JankfireRemotes.OwnerDev:InvokeServer("set", "fly", true)
  ```
  Other ops: `"players"`, `"fling"` / `"freeze"` / `"goto"` / `"bring"` with a Player or a dummy Model, `"flingAim"` / `"freezeAim"` with a look vector, `"unfreezeAll"`.
- **A match:** `ServerStorage.JankMatchTest:Invoke("ghost", "<pad>", nil, 30, player)`.
- **The anti-cheat in Studio:** set `StudioOn = true` on `ServerScriptService.Jankfire.AntiCheat` to switch it on.

## Test results

**Round 1, place version 943** (solo Play, a training dummy as the stand-in):
- Fly holds its height exactly with nothing pressed. Noclip turns the body's parts non-colliding.
- With dev powers on, a 60-stud client jump scored 0 points; the panel's verdict was "dev powers on".
- The stand-in was brought to the hub, flung 30 studs up in 0.45 s, and frozen mid-air.
- WEAPONS in the hub: the TV Remote went into the try layer (`Trying`), and its pause froze the stand-in. The rewind fired, but the stand-in had stood still, so it didn't move.
- `TestNotOwner` made every command "owner only".
- A ghost match with the player: a power worked, and the match was flagged (`MatchDev` set).

**Round 2, place version 950:**
- A red card on the stand-in: the card was in the owner's hand with the arm at 172 degrees. The stand-in was in the jail 1.2 s later with its 60 s running.
- The jail is sealed: rays out of its middle hit the walls on all four sides and the ceiling.
- Invisible, as the server sees it (and so everyone else): 25 of 25 body parts fully hidden and the name off. The owner's own head showed at 0.72, a ghost. Switching it off brought everything back: 1 of 25 hidden (the root, as before) and the name back.
  - The first try at switching it off left the body hidden. The kept values sat in a weak-keyed table, and Roblox can drop Instance keys from one while the parts still exist. Fixed with a strong table, plus the `DevWas` fallback.

**Not tested yet:**
- On a second real player: fling, freeze, jail and the red card on a player rather than a stand-in, jailing someone out of a real match, and invisible as seen from another client.
- The jail's 60 s release (the Play test stopped before it ran out).
- The overhead OWNER title and the card's shimmer.

**Photos:** `docs/owner-dev/`:
- `menu_v950.jpg`
- `jail_v950.jpg`
- `red_card_flash_v950.jpg`
