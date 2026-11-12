# THE HUB: mode lobbies, parties, friends (design)

The owner: *"Can you add lobbies like cod to the different modes the main menu will be like a center hub. You choose
the mode and it brings you into a lobby. You can add friends into a party and queue a match with your desired traits
enable disable bots pick your map for quick play zombies s and d and battle royale and new mech"*

Mockups (in the real game page: its fonts, mode art, map thumbs and 3D characters; the yellow sticky notes are
explanations, not UI): `hub.jpg`, `lobby_public.jpg`, `lobby_private.jpg`, `friends.jpg` (today's menu: `before_home.jpg`; the mockup code: `mockup.js`) next to this file.

## 1. The hub (the main menu, rebuilt)
- **Middle: your party, standing.** You (yellow plinth, crown when you lead) and up to 5 party members, each in their
  own outfit, names and level over their heads (the existing character renderer, one small scene). An empty dashed
  slot says **+ INVITE**. Click yourself to open CHARACTER, as the hero does now.
- **Right: the mode cards** (the 3D mode art we already render, the live "N playing" from `/lobbies`):
  QUICK PLAY, PLANT & DEFUSE, JANK ROYALE, ZOMBIES, BATTLE ISLAND (with a MECHS sticker), TRAINING, and a greyed
  STORY: OVERDUE strip ("coming to the hub. you still owe us."). The ONLINE / WITH BOTS / COOP buttons go away: those
  become PUBLIC / PRIVATE inside each mode's lobby (COOP = ZOMBIES or a private Quick Play with bots, see 6).
- **Left: STAFF ENTRANCE stays** as it is (customize, containers, leaderboard, settings, guide, lore, patch notes).
- **Bottom: the party bar.** PARTY n/6 · the party code (JNK4Q) · INVITE · JOIN CODE · FRIENDS (n online) · LEAVE.
- TODAY'S EVENT becomes a banner on the card whose mode it is (Quick Play's, mostly) plus a line in the strip.
- Desktop (the exe): HOST / JOIN, FULLSCREEN and QUIT move into SETTINGS' top row.

## 2. A mode lobby (click a card)
One screen per mode, same layout (mockups: `lobby_public.jpg`, `lobby_private.jpg`):
- **Top:** < HUB, the mode name big, its one-line description.
- **Middle:** the party on plinths with READY / not ready under each name. Members press READY (or R); the leader's
  button is the big one.
- **Left panel: MATCH.** PUBLIC | PRIVATE (leader only; members see it greyed with "only the leader (name) can change
  these").
  - PUBLIC: your party plays as one team (S&D: one side; Royale / Battle Island: one squad; Zombies: one squad),
    map VOTED, fill with bots after 30 s (on / off, 15-60 s), warm up while we look (on: the current warm-up
    deathmatch arena, see 4).
  - PRIVATE: bots on / off, bot count (0-12; royale 0-31), difficulty (easy, normal, hard, jank), the mode's own
    options (S&D: rounds to win, buy time; Royale: zone speed, loot; Zombies: starting round; Battle Island: squad
    size), teams (party vs bots / split the party / free for all), friends can join (off = code only).
- **Right panel:** PUBLIC: FINDING A MATCH, a clock, players found x / y, bots fill in 0:18. PRIVATE: the MAP, big
  thumbnail, < > through the mode's maps, a strip of the others, random map toggle.
- **Bottom:** INVITE · the big yellow button: **FIND MATCH** (public) / **START MATCH** (private) for the leader,
  CANCEL SEARCH while searching; members get READY and "waiting for taco". The party code sits beside it.
- **Battle Island:** each member picks their mech hero here (a hero card under their plinth) instead of on the blimp.
  The Gameplay session owns BATTLE ISLAND: the pick is their `{ t: 'isle', k: 'hero', h }` message (server/islemeter.js,
  validated with `isHero`, no double picks in a squad, only before the jump; PR #342). The lobby sends the same message
  once the match room is joined; the server rule stays theirs. Squads are assigned in server/island.js (`isleFreeSquad`,
  the pre-assign in `brRound` / `brJoin`) from a join-order list: a party goes in as one block of that list.
- **Training:** no public / private: START puts the party on the range together (or you alone).

## 3. Parties
- Up to **6**. Everyone is in a party of one when they open the game, so the hub always looks the same.
- **Codes:** 5 characters from `ABCDEFGHJKMNPQRSTUVWXYZ23456789` (no 0/O, 1/I/L), shown big, COPY button. Works for
  guests: no account needed to make, join or lead a party.
- **Invites:** from the friends list, or from the + INVITE slot (shows the code and your friends). An invite is a toast
  "noodle_arms wants you in their party (ZOMBIES) · JOIN / NAH", 30 s.
- **Leader:** whoever made it; passes to the next member if they leave. The leader can kick (a member's name > KICK)
  and promote. Only the leader changes settings, starts, cancels.
- **Follow the leader:** when the leader starts, every member goes into the same room together; when a match ends the
  party stays in that room for the next one (as now). If the leader goes back to the hub, members get "taco went back
  to the lobby · FOLLOW (5)" and follow when it counts down.
- A member already in a match when the leader starts gets "your party is starting PLANT & DEFUSE · GO / STAY".

## 4. Matchmaking (public)
- FIND MATCH = the whole party asks the server for a seat. The server looks for an open lobby of that mode with room for
  **all of you** (cap - humans >= party size) and puts you all in it; otherwise it opens a new one. Today's lobbies
  already do the rest: the warm-up deathmatch on the match's map, the countdown, READY, the map vote after a match.
- **Same team:** the room remembers each player's party; `joinTeam` puts a party on the same side (S&D) when it fits,
  Battle Island / Royale squads are built from parties first, then filled.
- **Fill with bots after N s:** the online lobbies wait for `min` humans now; with this on, when the countdown ends
  short of players, bots take the empty seats instead of waiting again.
- **Warm up while we look** on: you're in the warm-up arena with the party (what happens today). Off: you stay on the
  lobby screen with the clock, and drop in when the match starts (the room still runs; you're held as watchers).

## 5. Friends (accounts only)
- FRIENDS panel (mockup `friends.jpg`): FRIENDS n / REQUESTS n tabs, "add by username" + ADD, then each friend with a
  status dot and a line: in your party / in lobby: ZOMBIES (2/4) / in match: JANK ROYALE · 14 left / in the menu /
  offline · 3 days ago. Buttons: INVITE (to your party), JOIN (their party, if it's open to friends and not full).
- Requests: ACCEPT / NAH. Remove friend / block from a friend's row menu.
- Guests see "friends need an account. guests can still join a party with its code."
- Limits: 100 friends, 20 requests a day, 1 request per person per day after a NAH.

**The SQL** (the owner runs this once in the Supabase SQL editor; nothing else changes in `jf_users`):
```sql
-- friends: one row per pair (a < b by name_lower), who asked, and whether it's accepted yet
create table if not exists jf_friends (
  a text not null references jf_users(name_lower) on delete cascade,
  b text not null references jf_users(name_lower) on delete cascade,
  asked_by text not null,
  status text not null default 'pending' check (status in ('pending', 'friends', 'blocked')),
  created_at timestamptz not null default now(),
  primary key (a, b),
  check (a < b)
);
create index if not exists jf_friends_b on jf_friends (b);
alter table jf_friends enable row level security; -- (no policies: only the server's service key reads and writes it)
```
The file store (`data/jankfire-db.json`, the exe and LAN hosting) gets the same rows in a `friends` list.

## 6. What happens to today's buttons
| today | in the hub |
|---|---|
| ONLINE > Quick Play / P&D / Royale / Zombies | the mode card > PUBLIC |
| WITH BOTS > a mode | the mode card > PUBLIC with fill-with-bots on, or PRIVATE with bots |
| WITH BOTS > CUSTOM (any mode, any map, Battle Island) | PRIVATE in that mode's lobby; the odd modes (Gun Game, Duck Rain...) stay reachable from QUICK PLAY > PRIVATE > mode |
| COOP (friends vs waves of bots) | ZOMBIES, or QUICK PLAY > PRIVATE > Coop |
| TRAINING | the TRAINING card |
| PLAY IT WITH BOTS (event card) | the event banner on its mode card |

## 7. How it's built (the server stays honest)
- A **menu socket** (`/ws/hub`) opens with the game and stays open during matches: presence, the party, invites,
  friends' status. The game socket is unchanged; a party start just tells each member's client which room to join
  (`{ t: 'pgo', room, ticket }`); the room only lets in a private room's members with a one-use ticket.
- `server/party.js` (new): parties in memory (`code -> { leader, members, mode, pub, settings, state }`), presence
  (`name_lower -> where`). Messages: `pmake`, `pjoin {code}`, `pleave`, `pkick {id}`, `plead {id}`, `pset {...}`,
  `pready {on}`, `pgo`, `pcancel`, `pinvite {name}`, `fadd`, `faccept`, `fdecline`, `fremove`.
- **Validation** (CLAUDE.md): every field type-checked and range-clamped (`Number.isFinite`, `Object.hasOwn` on the mode,
  map and option tables, the map must suit the mode via `mapsFor`); only the leader may `pset`, `pgo`, `pcancel`,
  `pkick`, `plead`; joining needs the code (5 chars from the alphabet) or a pending invite; full parties refuse; rate
  limits: 1 code try per second and 10 wrong codes a minute per socket (a code has 28 million values), 6 invites a
  minute, settings changes 5 a second; parties and presence die with their sockets (a 30 s grace for reconnects).
- Friends over HTTP (`/api/friends`, `/api/friends/add`, ...) with the account token like `/api/me`.
- Client: `public/js/hubmenu.js` (hub + lobby screens), `public/js/party.js` (the socket, party state, toasts),
  `public/js/friends.js`; the lineup renders with `buildCharacter` in its own small scene (like `preview.js`).

## 8. Build order (small PRs, each tested, reviewer pass on the server ones)
1. **Hub + mode lobby screens + private match settings.** Solo party only, no new server state except the private
   room settings (they ride on today's `cfg`). The old ONLINE / WITH BOTS screens stay one click away until 2 lands.
2. **Parties with codes:** the menu socket, `server/party.js`, the lineup with real members, follow-the-leader, same team.
3. **Friends:** `jf_friends` (the SQL above), the panel, presence, invites from the list.
4. **Matchmaking polish:** fill with bots after N, warm-up off, whole-party seats, follow / GO prompts, reconnect grace.
