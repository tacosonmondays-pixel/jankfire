# JANKFIRE: read this first

JANKFIRE is a deliberately janky, chaotic, funny multiplayer FPS made with its owner. Current status, open branches and
queued requests live in `HANDOFF.md` on the `claude/handoff` branch (`git show origin/claude/handoff:HANDOFF.md`).

## The game's style (keep it)
- **Jank is the point.** Physics comedy is a feature: flinging, slipping on marbles and bananas, huge sniper knockback,
  wrecking-ball slams, ragdoll-ish deaths, people exploding into gibs or kill effects. Make things feel absurd but readable.
- **Juice everything.** Big satisfying feedback: hit-stop, sparks, screen flashes, anime-style red impact frames, kill-feed
  icons, loud HUD callouts in the game's voice ("YOU TOUCHED GRASS", "BLOOD CROSSED", "HUNG JURY", "MARBLES!", MLG no-scope
  overlays, fireworks). Sounds are synthesized in `public/js/audio.js`.
- **Look:** chunky low-poly Three.js models, bright saturated colours, a pink/magenta + yellow comic-style UI, and render
  presets from "Potato" (pixelated, vertex-snapped) to "Too HD". Weapons and props are modelled from real references
  (real proportions, real parts), then made fun.
- **Quality bar from the owner: "Models and animation max!! We need quality."** Model and animation work gets max effort,
  pose and model sheets, screenshots, and iteration until it looks good.
- **Inspired by, never copied:** systems may nod to CS, CoD, Rivals, Roblox physics games, anime, etc., but every name, logo,
  character, map layout and asset is original. Homages are fine; replicas are not.
- **Every weapon has a gimmick** (the Redline fires faster at low HP, the marble shotgun leaves slippery marbles, the katana
  grows and parries, the Scales of Justice deal verdict damage...). Killstreaks and items are spectacles, not stat bumps.
- Bots must actually know how to play every mode (routes, objectives, buying, grappling).

### Style details (match these exactly)
- **UI look:** a comic/zine style. Font: Comic Neue (bundled in `public/fonts`, `var(--font)`). Panels are dark purple-black
  (`rgba(18,8,24,0.92)`) with a thick 4 px pink border and a hard, offset **cyan drop shadow** (`8px 8px 0`, no blur). The
  main button is yellow (`#ffe14d`) with a black border and a pink offset shadow, tilted a degree or two. Other buttons are
  white with black borders; destructive ones are red. Everything uses hard offset shadows: no soft blurs, no gradients on
  buttons, no rounded "app" look.
- **Palette:** hot pink/magenta (`#ff4fd8`, `#ff00dc`), yellow (`#ffe14d`), cyan (`#4fd8ff`), toxic green (`#39ff14`,
  `#7dff4f`), red (`#ff3030`) on near-black. Each weapon has its own colour in `shared/weapons.js`, used for its icon, kill-feed
  tag and tracer.
- **3D look:** chunky low-poly built from boxes, lathes and simple shapes. Blender-made weapons and props (`tools/blender/`,
  `.glb` in `public/models/`, visual only: collisions stay boxes) use the glossy bevelled look: real-reference proportions,
  candy/clear-coat paint, chrome and brass, small crusty textures (the owner's pick, 2026-11-05). Each one keeps the code
  model's muzzle/grip/sight spots, tags its wrap zones in its part names (`_wzA` / `_wzB` / `_wzN`) and falls back to the
  code model if the file is missing. Characters are mannequins with
  built-in jank (random tilt, a wrong knee); other players get outlines. Maps are big readable blocks with scenery around them
  (never floating in a void), and sky, fog and lighting are tuned per map.
- **Writing voice:** short, lowercase-ish, deadpan and cheeky. Item descriptions are one or two plain sentences with a joke
  ("Hard bananas that bonk and make them slip. Misses stay on the floor as peels."). Kill-feed and death lines are silly
  ("t-bagged too hard and exploded", "smoked too much", "into the void"). Big HUD callouts are ALL CAPS and punchy.
- **Names:** silly-literal, not edgy-generic. For example: Peel Shooter, Hand Slapper, Bread, Spoon, Jank Cola, Dead Mall,
  Scales of Justice ("HUNG JURY"), Wrecking Ball, Golden Sniper.
- **Sound:** synthesized in code (`public/js/audio.js`, Web Audio), punchy and cartoonish. Every action gets a sound, and
  headshots and kills get special ones (DINK / TONK).
- **Feel:** fast movement (grapple, slides, rocket jumps), generous fun over balance-spreadsheet fairness, but the server
  still keeps it honest (no cheating).

## How we work
- **The owner** types fast, with typos and slang ("XD", "cuh"). Read requests generously and build the fun version. If
  something is truly ambiguous, build the likely meaning and say what you assumed. They send lots of ideas: queue them
  rather than dropping any.
- **Shipping:** small PRs to `main`, often. Open them as drafts. The owner lets the coordinating Claude session merge a PR once
  its session reports it done and tested and it re-checks it on the latest main; look choices, `supabase.sql` re-runs and the
  exe still wait for the owner. Render
  auto-deploys `main` to https://jankfire.onrender.com; PLAY ONLINE in the exe loads the game from there. Rebuild the Windows
  exe with `npm run dist:win:zip` (output in `dist/`) when asked. The owner creates GitHub releases themselves.
- **Patch notes:** every update players notice gets a line in `public/js/patchnotes.js` (PATCH NOTES in the menu, newest first, in the game's voice). Feature sessions describe their change in the PR; the coordinating session adds the patch-notes line when it ships, so parallel PRs don't fight over that file.
- **Show the work:** send screenshots and short clips (Playwright `recordVideo` + ffmpeg, graphics setting `jank: 3` = Too HD)
  of new features.
- **Usage is limited:** use effort levels (max for models and animation, high for gameplay and fixes, medium for reviews),
  avoid needless parallel agents, and keep branches pushed so nothing is lost when a session ends.

## Code conventions
- Node `ws` server (`server.js`, `server/`), Three.js client (`public/js/`), shared rules and data (`shared/`), Electron
  wrapper (`desktop/`). Movement is client-authoritative; the server validates hits and owns HP, kills, items, streaks,
  rounds and bots.
- **Every server message handler validates input:** types, `Number.isFinite`, `Object.hasOwn`/`has()`, ranges, alive/mode
  checks, rate limits. A per-connection message budget applies, `tooDeep` guards nesting, and `_` keys are stripped at join.
- Compact JS, short lowercase comments that explain *why*. Keep changes additive and local (new files and functions); don't
  reformat or reorder existing code.
- Test knobs are `JF_*` env vars at the top of `server.js`. The regression scripts are on the `claude/handoff` branch in
  `handoff/tests/` (`regress2.sh <checkout> <port>`). Cap headless browsers with `pwlock.cjs`.
- **Secrets:** the Supabase secret key (`sb_secret_...`, service_role) lives only in `.env` / Render env vars. It never goes
  in the exe, `desktop/config.json`, the repo or chat; never ask for it or the DB password. Account schema: `supabase.sql`
  (the owner re-runs it in the Supabase SQL editor when columns are added).
- **Commits:** author `Claude <noreply@anthropic.com>`; end messages with the session's Co-Authored-By / Claude-Session
  trailers.

## Working style (how the earlier sessions ran, keep doing it)
- **One branch + git worktree per feature** (`claude/f-<name>`, worktree in the scratchpad, `node_modules` symlinked), so
  features build in parallel without touching each other. Push branches often; a session can end at any time.
- **Build, then verify, then fix.** A builder (max effort for models/animation, high for gameplay), then a reviewer that
  plays it and attacks it (exploits, edge cases, visuals) and returns must-fix / nice-to-have lists, then a fixer. Reviewers
  have caught real bugs every time, so skip them only to save usage.
- **Integration branch:** finished features are merged one at a time into an integration branch (`claude/int-features`), each
  merge resolved so both sides keep working (never just take one side), smoke-tested, then a full regression against the
  `main` baseline before the PR. Merge commit messages record the cross-feature decisions.
- **Hotfixes for the live game:** small PRs from a branch based on `main`; after a PR merges, keep committing on top (no
  force-push) and open a new PR.
- **Testing:** prefer plain `ws` scripts for server logic; Playwright for anything visual (screenshots, frame contact sheets
  made with ffmpeg, actually looked at). Use `JF_*` knobs to skip grinding (short rounds, instant streaks; Training always has
  your 3 picked killstreaks). Never claim something works without a test or a screenshot.
- **Talking to the owner:** short, plain updates with no jargon. Say what changed in player terms, give exact click steps
  for anything they must do (merge a PR, run SQL in Supabase), link PRs, send screenshots/clips, and be honest when
  something failed or wasn't tested. Track every request in the task list; queue ideas instead of dropping them.
- **Commit messages** describe what players see ("Sniper knockback is back: a body shot sends them flying...").

## Tools and environment
- Start sessions on the **jankfire** cloud environment: its setup script installs Blender 4.0 (`blender`), Blender 5.2
  (`blender52`, for the vendored `blender-*` skills), software GL for EEVEE renders, and the npm packages; it can reach
  jankfire.onrender.com to check the live site. Which skill fits which job: the `jankfire-toolbox` skill (`.claude/skills`).
- Claude Code cloud session. Preinstalled: Node 22, Playwright + Chromium (`require('playwright')`; launch with
  `--use-gl=swiftshader --enable-unsafe-swiftshader --mute-audio`), ffmpeg, `gh` (use `gh api` REST; GraphQL is blocked).
  Exe builds use electron-builder from the repo's devDependencies (`npm run dist:win:zip`).
- Multi-agent work used the Agent tool and the Workflow tool. Caveat: Workflow sub-agents only see the owner's latest message
  as "the request" and may refuse work asked for earlier; for that, use plain agents with the request quoted in the prompt.
- Limits seen in the sandbox: on other environments onrender.com isn't reachable, GitHub release
  creation and force-push are blocked, and killing processes you didn't start is refused. Headless browsers are slow (cap
  them at 2 with `pwlock.cjs`).
- Helper scripts live on the `claude/handoff` branch in `handoff/tests/`: `regress2.sh` (full regression), `t_*.cjs`
  (feature tests), `rec*.cjs` (record HD gameplay clips). Fix the absolute scratchpad paths in them first.
