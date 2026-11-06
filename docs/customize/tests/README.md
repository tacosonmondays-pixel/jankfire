# customize screen tests

Env for all: `SP=<dir with pwlock.cjs>` `PORT=<server port>`; the account ones also need `TOKEN` (log in `cztest` via `/api/login`).

1. Make a test account: start a server with `JF_DATA_DIR=<dir>`, `POST /api/register {"name":"cztest","pass":"hunter22"}`,
   stop it, give `users.cztest.inv` = `{"finish":["camo","chrome","ice","neon","gold"],"hat":["cowboy","chef","crown"],"effect":["sparkles","hearts"],"kill":["grave","cash","chicken"],"model":["ar_toy","ar_bullpup","knife_bowie"]}` in `jankfire-db.json`, start it again.
2. `t_rand_srv.cjs`: ws only. Random slots reroll every life, favourites-only respected, only owned items, wrap mode kept.
3. `t_cz_func.cjs`: equip / favourites / random / finisher, reload + fresh device keep it, guest can try on but not equip locked, a second client sees the look and each life's roll.
4. `t_cz_bots.cjs` (any server, no account): WITH BOTS > CUSTOM, pause > COSMETICS > equip > LEAVE back to pause, melee on left click, 0 page errors.
5. `t_cz_shots.cjs` (`OUT=docs/customize`), `t_cz_clip.cjs`: the screenshots and the clip (also checks the idle 3D view stops drawing and the classic locker link).

Note: the old `t_cos.cjs` regression clicks the classic list (`#sk-finish`...). COSMETICS now opens this screen; the classic list
is behind its GRAPPLE + SPRAY button (`.cz-btn:has-text("GRAPPLE")`).
