"""Direction D: SIGNAL. The hubs are stations, concourses and hotels, so the menus talk like their
signs: navy enamel with a cream keyline, sentence case in Titillium Web, platform badges for keys.
Nothing floats: every sign hangs from the top edge, stands on the bottom edge, or sticks out of a
side wall, and its keyline stops where it meets the edge. Two registers: menus are signs; in a
match only the score hangs as a sign and the rest is bare type with a shadow. Butter enamel
plates are the only buttons (Play, Buy, Done)."""
from common import *

NAME = "D  SIGNAL"
CSS = """
:root{--s:#1d2b3a;--s2:#24364a;--s3:#36495e;--c:#f1ead9;--m:#9fb0c2;--a:#f5dd8a}
body{font-family:'Titillium Web';font-weight:700;color:var(--c);font-variant-numeric:tabular-nums}
.sign{position:absolute;background:var(--s);border-radius:10px;box-shadow:0 12px 28px rgba(0,0,0,.32)}
.sign::before{content:"";position:absolute;inset:7px;border:2px solid rgba(241,234,217,.34);border-radius:6px;pointer-events:none}
.hang{top:0;border-radius:0 0 10px 10px}.hang::before{top:-12px;border-radius:0 0 6px 6px}
.stand{bottom:0;border-radius:10px 10px 0 0}.stand::before{bottom:-12px;border-radius:6px 6px 0 0}
.fromL{left:0;border-radius:0 10px 10px 0}.fromL::before{left:-12px;border-radius:0 6px 6px 0}
.fromR{right:0;border-radius:10px 0 0 10px}.fromR::before{right:-12px;border-radius:6px 0 0 6px}
.corner{top:0;right:0;border-radius:0 0 0 10px}.corner::before{top:-12px;right:-12px;border-radius:0 0 0 6px}
.btn{display:inline-flex;align-items:center;justify-content:center;background:var(--a);color:var(--s);border-radius:8px;box-shadow:inset 0 0 0 3px var(--a),inset 0 0 0 5px rgba(29,43,58,.35)}
.badge{display:inline-grid;place-items:center;border-radius:6px;background:var(--c);color:var(--s);line-height:1;flex:none;padding:0 8px}
.tile{display:grid;place-items:center;background:var(--c);color:var(--s);border-radius:8px;flex:none}
.tile.d{background:var(--s3);color:var(--c)}
.m{color:var(--m)}
.reg{font-weight:400}
.flexc{display:flex;align-items:center}
.row{display:flex;align-items:center;border-top:2px solid var(--s3)}
.hbar{height:12px;border-radius:3px;background:var(--s3);overflow:hidden;position:relative}.hbar>b{display:block;height:100%;background:var(--c)}
.hbar>u{position:absolute;top:0;bottom:0;width:3px;background:var(--a)}
.scrim{position:absolute;inset:0;background:rgba(12,17,24,.6)}
.bare{color:#fff;text-shadow:0 2px 0 rgba(0,0,0,.45),0 0 16px rgba(0,0,0,.5)}
.shade{position:absolute;inset:0;background:radial-gradient(60% 55% at 0% 100%,rgba(10,14,20,.55),rgba(10,14,20,0) 70%),radial-gradient(60% 55% at 100% 100%,rgba(10,14,20,.5),rgba(10,14,20,0) 70%)}
"""


def hub():
    info = {"quests": f"{QUESTS_DONE[0]} of {QUESTS_DONE[1]} done", "party": "1 of 4"}
    rows = "".join(f"""<div class="row" style="height:60px;padding:0 34px">
 <span style="font-size:31px">{label.title()}</span><span class="m reg" style="font-size:22px;margin-left:auto">{info.get(mid, "")}</span></div>""" for mid, label, key in MENU[1:] + [("settings", "SETTINGS", "")])
    xp = PLAYER['xp'] / PLAYER['xp_next']
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_spawn.jpg)"></div>
<div class="sign hang flexc" style="right:536px;height:80px;padding:12px 26px 0 22px;gap:12px;font-size:28px">{cur('coin', 32)}{WALLET['coins']}<span style="width:12px"></span>{cur('ticket', 38)}{WALLET['tickets']}</div>
<div class="sign corner" style="width:500px">
 <div style="padding:44px 34px 14px">
  <div style="font-size:54px;line-height:1.05">The Rotunda</div>
  <div class="m reg" style="font-size:22px;margin-top:4px">{HUB['here']} players here</div>
 </div>
 <div style="padding:18px 34px 24px;border-top:2px solid var(--s3);background:var(--s2)">
  <div class="m" style="font-size:22px;margin-bottom:10px">Ranked 1v1</div>
  <div class="btn" style="width:100%;height:110px;font-size:80px">Play</div>
 </div>
 {rows}
 <div class="flexc" style="padding:16px 34px 30px;gap:16px;border-top:2px solid var(--s3)">{head(0, 50)}
  <div style="flex:1"><div class="flexc" style="justify-content:space-between"><span style="font-size:27px">{PLAYER['name']}</span><span class="m" style="font-size:21px">Level {PLAYER['level']}</span></div>
  <div class="hbar" style="height:7px;margin-top:8px"><b style="width:{xp*100:.0f}%"></b></div></div></div>
</div>
</div>"""
    return page("D hub", CSS, body)


def match():
    m = MATCH
    def sq(team, n):
        return f'<div class="tile" style="width:76px;height:76px;background:{TEAM[team][0]};font-size:58px;line-height:1">{n}</div>'
    feed = "".join(f'<div class="flexc" style="justify-content:flex-end;gap:12px;height:42px;margin-bottom:6px;padding:0 18px;border-radius:6px;background:rgba(29,43,58,.66);font-size:21px">{feed_line(*f)}</div>' for f in FEED)
    slots = ""
    for i, (k, g, n) in enumerate(SLOTS + [("G", None, "")]):
        on = i == 0
        inner = slot_icon(g, 62, 28) if g else f'<span style="font-size:28px;line-height:0">{icon("grenade")}</span><span style="font-size:20px;margin-left:4px">×{m["util_n"]}</span>'
        slots += f'<div class="flexc bare" style="gap:9px;opacity:{1 if on else .62}"><span class="badge" style="height:28px;font-size:17px;text-shadow:none;{"background:var(--a)" if on else ""}">{k}</span><span style="filter:drop-shadow(0 2px 0 rgba(0,0,0,.45))">{inner}</span></div>'
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_crate.jpg)"></div><div class="shade"></div>
<div class="sign hang flexc" style="left:50%;transform:translateX(-50%);padding:16px 22px 18px;gap:18px">
 {sq('blossom', m['us'])}
 <div style="text-align:center;width:118px"><div style="font-size:44px;line-height:1.05">{m['time']}</div><div class="m" style="font-size:19px">Round {m['round']}</div></div>
 {sq('sky', m['them'])}
</div>
<div class="abs" style="right:56px;top:40px">{feed}</div>
<div class="abs bare" style="left:60px;bottom:48px"><div style="font-size:84px;line-height:1">{m['hp']}</div>
 <div class="hbar" style="width:290px;height:14px;margin-top:10px;background:rgba(255,255,255,.25)"><b style="width:{m['hp']}%"></b></div></div>
<div class="abs" style="right:60px;bottom:48px;text-align:right">
 <div class="flexc" style="gap:28px;justify-content:flex-end;margin-bottom:18px">{slots}</div>
 <div class="bare"><span style="font-size:84px;line-height:1">{m['ammo']}</span><span class="reg" style="font-size:34px;opacity:.75"> / {m['mag']}</span></div>
</div>
<svg class="abs" style="left:942px;top:522px" width="36" height="36" viewBox="0 0 36 36"><g stroke="#1d2b3a" stroke-width="7" stroke-linecap="round"><path d="M18 3v8M18 25v8M3 18h8M25 18h8"/></g><g stroke="#f1ead9" stroke-width="3.4" stroke-linecap="round"><path d="M18 3v8M18 25v8M3 18h8M25 18h8"/></g></svg>
</div>"""
    return page("D match", CSS, body)


def loadout():
    gates = ""
    pics = {"PRIMARY": gunpic("ar", "gimg"), "SECONDARY": '<img class="gimg" src="../img/items/wish_duck_34.png">', "MELEE": gunpic("katana", "gimg"), "UTILITY": '<img class="gimg" src="../img/items/frag.png" style="max-height:76px">'}
    for i, (slot, g, name, note) in enumerate(LOADOUT):
        on = i == SEL
        sub = {"SECONDARY": "Wish Duck skin", "UTILITY": "2 charges"}.get(slot, "")
        gates += f"""<div class="sign fromL" style="top:{168 + i*122}px;width:600px;height:108px;{"background:var(--s2)" if on else ""}">
 <div class="badge" style="position:absolute;left:52px;top:26px;width:56px;height:56px;font-size:32px;{"background:var(--a)" if on else ""}">{["1","2","3","G"][i]}</div>
 <div style="position:absolute;left:130px;top:{16 if sub else 28}px;font-size:36px;line-height:1.2;{"color:var(--a)" if on else ""}">{name}</div>
 {f'<div class="m reg" style="position:absolute;left:131px;top:60px;font-size:20px">{sub}</div>' if sub else ''}
 <div style="position:absolute;right:24px;top:16px;width:150px;height:76px;display:grid;place-items:center">{pics[slot]}</div></div>"""
    stats = "".join(f'<div style="flex:1"><div class="m" style="font-size:19px">{k}</div><div style="font-size:38px;line-height:1.2">{v}</div><div class="hbar" style="height:9px;margin-top:6px"><b style="width:{f*100:.0f}%"></b><u style="left:{avg*100:.0f}%"></u></div></div>' for (k, v, f), avg in zip(STATS, STAT_AVG))
    board = ""
    for i, (g, n, st) in enumerate(ARMORY):
        locked = isinstance(st, tuple)
        if locked:
            s = (f'<span class="m reg flexc" style="gap:6px">{icon("lock")}Level {st[1]}</span>' if st[0] == "level"
                 else f'<span class="flexc" style="gap:6px">{cur("coin", 22)}{st[1]}</span>')
        else:
            s = '<span style="color:var(--a)">Equipped</span>' if st == "on" else ""
        board += f"""<div class="row" style="height:72px;padding:0 30px;gap:18px;{"background:var(--s2)" if st == "on" else ""}">
 <div style="width:100px;display:grid;place-items:center;{"color:var(--m)" if locked else ""}">{slot_icon(g, 84, 30) if g != "akimbo" else silpic(g)}</div>
 <span style="font-size:27px;{"color:var(--m)" if locked else ""}">{n}</span><span style="margin-left:auto;font-size:21px">{s}</span></div>"""
    cos = "".join(f'<div class="flexc" style="flex:1;gap:16px"><div class="tile d" style="width:132px;height:88px;border-radius:8px"><img src="../img/items/{img}.png" style="max-width:118px;max-height:74px"></div><div><div class="m" style="font-size:19px">{k}</div><div style="font-size:26px;line-height:1.15">{v}</div></div></div>'
                  for k, v, img in [("Skin", "Wish Duck", "wish_duck_34"), ("Hat", "Royal Duck", "royal-duck")])
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_rotunda_blur.jpg)"></div><div class="scrim"></div>
<style>.gimg{{max-width:150px;max-height:72px}} .sil{{width:84px;height:30px}} .ic{{width:.9em;height:.9em}}</style>
<div class="abs" style="left:56px;top:40px;font-size:64px;line-height:1.2">Loadout</div>
{gates}
<img class="abs" src="../img/{SEL_GUN['img']}" style="left:660px;top:130px;width:640px;filter:drop-shadow(0 24px 26px rgba(0,0,0,.5))">
<div class="sign stand" style="left:636px;width:720px">
 <div class="flexc" style="padding:26px 34px 6px;gap:14px"><span style="font-size:38px">{SEL_GUN['name']}</span>
  <span class="m" style="margin-left:auto;font-size:20px">Mastery {MASTERY['level']}</span></div>
 <div style="padding:0 34px"><div class="flexc" style="gap:12px"><div class="hbar" style="flex:1;height:8px"><b style="width:{MASTERY['frac']*100:.0f}%"></b></div><span class="m reg" style="font-size:17px">{MASTERY['xp']} / {MASTERY['next']} xp</span></div></div>
 <div style="display:flex;gap:24px;padding:20px 34px 6px">{stats}</div>
 <div class="flexc m reg" style="font-size:16px;gap:8px;padding:4px 34px 14px"><i style="width:3px;height:14px;background:var(--a)"></i>secondary average</div>
 <div style="height:2px;background:var(--s3);margin:0 20px"></div>
 <div style="display:flex;gap:24px;padding:18px 34px 30px">{cos}</div>
</div>
<div class="sign corner" style="width:500px">
 <div style="padding:46px 30px 16px;font-size:36px">Secondaries</div>
 {board}
 <div style="padding:20px 30px 26px;border-top:2px solid var(--s3)"><div class="btn" style="width:100%;height:68px;font-size:32px">Done</div></div>
</div>
</div>"""
    return page("D loadout", CSS, body)


def shop():
    tabs = "".join(f'<div class="flexc" style="height:50px;padding:0 20px;border-radius:6px;font-size:25px;{"background:var(--c);color:var(--s)" if i == 0 else ""}">{t.title()}</div>' for i, t in enumerate(SHOP_TABS))
    setrow = "".join(f"""<div style="width:120px"><div class="tile d" style="height:96px;border-radius:8px"><img src="../img/items/{img}.png" style="max-width:108px;max-height:80px"></div>
 <div style="font-size:21px;margin-top:8px;line-height:1.15">{s}</div><div class="m reg" style="font-size:18px">{g}</div></div>""" for s, g, img in HERO['set'] + [("Royal Duck", "Hat", "royal-duck")])
    daily = "".join(f"""<div class="row" style="height:124px;gap:18px;padding:0 6px;{"border-top:none" if i == 0 else ""}">
 <div class="tile" style="width:190px;height:100px;border-radius:8px;background:{RARITY[rar]}40"><img src="../img/items/{img}.png" style="max-width:176px;max-height:84px"></div>
 <div style="flex:1"><div style="font-size:28px;line-height:1.15">{name}</div><div class="reg" style="font-size:19px"><span style="color:{RARITY[rar]};font-weight:700">{rar.title()}</span> <span class="m">{kind.lower()}</span></div></div>
 <div class="flexc" style="gap:8px;font-size:27px;margin-right:8px">{rbx() if curr == "robux" else cur("coin", 28)}{price}</div></div>""" for i, (img, name, kind, price, curr, rar) in enumerate(DAILY))
    cells = "".join(f"""<div style="width:300px;padding:22px 22px 18px;border-right:2px solid var(--s3)">
 <div class="tile d" style="height:100px;border-radius:8px"><img src="../img/items/{img}.png" style="max-width:200px;max-height:86px"></div>
 <div style="font-size:27px;margin-top:8px">{name}</div><div class="m reg" style="font-size:18px">{holds}</div>
 <div class="flexc" style="gap:12px;font-size:22px;margin-top:2px"><span class="flexc" style="gap:6px">{cur('ticket', 30)}{tk}</span><span class="m reg" style="font-size:18px">or</span><span class="flexc" style="gap:4px">{rbx()} {rp}</span></div></div>""" for img, name, holds, tk, rp in CONTAINERS)
    packs = "".join(f"""<div class="row" style="height:46px;gap:14px;{"border-top:none" if i == 0 else ""}"><span style="font-size:27px;width:120px">{c}</span><span class="m reg" style="font-size:18px;flex:1">{b or "coins"}</span><span class="flexc" style="gap:4px;font-size:24px">{rbx()} {r}</span></div>""" for i, (c, r, b) in enumerate(COIN_PACKS))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_rotunda_blur.jpg)"></div><div class="scrim"></div>
<div class="abs" style="left:56px;top:26px;font-size:64px;line-height:1.2">Shop</div>
<div class="sign hang flexc" style="left:250px;height:84px;padding:12px 14px 0;gap:4px">{tabs}</div>
<div class="sign hang flexc" style="right:56px;height:84px;padding:10px 28px 0 22px;gap:10px;font-size:30px">
 {cur('coin', 36)}{WALLET['coins']}<span style="width:14px"></span>{cur('ticket', 40)}{WALLET['tickets']}</div>
<div class="sign fromL" style="top:150px;width:1130px;height:590px">
 <div class="flexc" style="position:absolute;left:56px;top:26px;gap:18px"><span style="font-size:72px;line-height:1.1">Ducky</span><span class="m reg" style="font-size:24px;margin-top:22px">VIP pass</span></div>
 <img src="../img/items/wish_duck_34.png" style="position:absolute;left:44px;top:130px;width:460px;filter:drop-shadow(0 16px 16px rgba(0,0,0,.35))">
 <div class="reg" style="position:absolute;left:560px;top:56px;width:520px;font-size:22px;line-height:1.4">Three skins, the Royal Duck hat and the VIP title.</div>
 <div class="flexc" style="position:absolute;left:560px;top:150px;gap:14px;align-items:flex-start">{setrow}</div>
 <div class="btn" style="position:absolute;left:560px;bottom:40px;height:74px;padding:0 34px;gap:12px;font-size:38px">Buy {rbx()} {HERO['price']}</div>
</div>
<div class="sign fromR" style="top:150px;width:734px;height:590px;padding:22px 56px 14px 30px">
 <div class="flexc" style="height:44px;margin-bottom:8px"><span style="font-size:32px">Daily</span><span class="m reg" style="font-size:21px;margin-left:auto">New in {DAILY_RESET}</span></div>
 {daily}
</div>
<div class="sign stand flexc" style="left:0;right:0;height:270px;border-radius:0;align-items:stretch;padding-left:36px">
 {cells}
 <div style="flex:1;padding:20px 56px 18px 30px"><div style="font-size:27px;margin-bottom:4px">Coins</div>{packs}</div>
</div>
</div>"""
    return page("D shop", CSS, body)


def phone():
    m = MATCH
    keys = "".join(f'<div class="sign" style="left:{x - s/2:.0f}px;top:{y - s/2:.0f}px;width:{s}px;height:{s}px;border-radius:12px;display:grid;place-items:center;box-shadow:0 4px 10px rgba(0,0,0,.25)">{act_icon(k, int(s*0.52))}</div>' for k, x, y, s in arc(752, 222, 124, 84, 266))
    slots = "".join(f'<div class="flexc bare" style="gap:5px;opacity:{1 if i == 0 else .62}"><span class="badge" style="height:16px;font-size:10px;padding:0 4px;text-shadow:none;{"background:var(--a)" if i == 0 else ""}">{k}</span><span style="filter:drop-shadow(0 1px 0 rgba(0,0,0,.5))">{slot_icon(g, 36, 16)}</span></div>' for i, (k, g, n) in enumerate(SLOTS))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_crate.jpg)"></div><div class="shade"></div>
<style>.sign::before{{inset:4px;border-width:1px}} .hang::before{{top:-8px}}</style>
<div class="sign hang flexc" style="left:50%;transform:translateX(-50%);padding:6px 10px 8px 10px;gap:8px;border-radius:0 0 8px 8px">
 <div class="tile" style="width:40px;height:40px;background:{TEAM['blossom'][0]};font-size:30px;border-radius:7px">{m['us']}</div>
 <div style="text-align:center;width:58px"><div style="font-size:21px;line-height:1">{m['time']}</div><div class="m" style="font-size:10px">Round {m['round']}</div></div>
 <div class="tile" style="width:40px;height:40px;background:{TEAM['sky'][0]};font-size:30px;border-radius:7px">{m['them']}</div>
</div>
<div class="abs" style="left:58px;top:124px;width:124px;height:124px;border-radius:50%;background:rgba(29,43,58,.55);box-shadow:inset 0 0 0 3px rgba(241,234,217,.7)"></div>
<div class="tile" style="position:absolute;left:94px;top:160px;width:52px;height:52px;border-radius:50%"></div>
<div class="abs flexc" style="left:226px;bottom:12px;gap:22px;align-items:flex-end">
 <div class="bare"><div style="font-size:38px;line-height:1">{m['hp']}</div><div class="hbar" style="width:90px;height:7px;margin-top:6px;background:rgba(255,255,255,.25)"><b style="width:{m['hp']}%"></b></div></div>
 <div class="flexc" style="gap:10px;padding-bottom:12px">{slots}</div>
 <div class="bare" style="padding-bottom:6px"><span style="font-size:38px;line-height:1">{m['ammo']}</span><span class="reg" style="font-size:16px;opacity:.8"> / {m['mag']}</span></div>
</div>
{keys}
<div class="tile" style="position:absolute;left:700px;top:170px;width:104px;height:104px;border-radius:50%;background:var(--a);color:var(--s);box-shadow:inset 0 0 0 4px var(--a),inset 0 0 0 6px rgba(29,43,58,.35),0 6px 14px rgba(0,0,0,.3)">{fire_icon(34)}</div>
<svg class="abs" style="left:412px;top:185px" width="20" height="20" viewBox="0 0 36 36"><g stroke="#1d2b3a" stroke-width="7" stroke-linecap="round"><path d="M18 3v8M18 25v8M3 18h8M25 18h8"/></g><g stroke="#f1ead9" stroke-width="3.4" stroke-linecap="round"><path d="M18 3v8M18 25v8M3 18h8M25 18h8"/></g></svg>
</div>"""
    return page("D phone", CSS, body, 844, 390)


def scoreboard():
    bd = BOARD
    cols = [("Kills", 76), ("Deaths", 92), ("Assists", 96), ("Damage", 116), ("Ping", 90)]
    head_row = '<div class="flexc m" style="height:40px;font-size:19px;padding:0 24px 0 86px"><span style="flex:1">Player</span>' + "".join(f'<span style="width:{w}px;text-align:right">{h}</span>' for h, w in cols) + "</div>"
    blocks, n = "", 0
    for team, players in bd["teams"]:
        c, d = TEAM[team]
        rows = ""
        for j, (nm, k, de, a, dmg, ping, alive, me) in enumerate(players):
            br = party_bracket(130, "var(--a)") if nm in PARTY and j == 0 else ""
            rows += f"""<div class="row" style="position:relative;height:60px;padding:0 24px 0 20px;{"background:var(--s2);box-shadow:inset 0 0 0 3px var(--c);border-radius:6px;border-top-color:transparent" if me else ""};{"" if alive else "color:var(--m)"}">{br}
 <span style="margin-right:22px;{"" if alive else "filter:grayscale(1);opacity:.5"}">{head(n, 44)}</span>
 <span style="flex:1;font-size:25px">{nm} <span class="m reg" style="font-size:18px;margin-left:4px">level {LEVELS[nm]}</span>{" <span class=reg style=font-size:18px>(dead)</span>" if not alive else ""}</span>
 {"".join(f'<span style="width:{w}px;text-align:right;font-size:25px">{v}</span>' for v, w in [(k, 76), (de, 92), (a, 96), (dmg, 116), (f"{ping} ms", 90)])}</div>"""
            n += 1
        blocks += f"""<div style="margin-top:12px"><div class="flexc" style="height:44px;gap:14px;padding:0 24px"><span style="font-size:28px;color:{c}">{team.title()}</span><span class="m reg" style="font-size:20px">{sum(p[1] for p in players)} kills</span></div>{rows}</div>"""
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_forest_blur.jpg)"></div><div class="scrim" style="background:rgba(12,17,24,.35)"></div>
<div class="sign hang" style="left:50%;transform:translateX(-50%);width:1100px;padding:26px 30px 30px">
 <div class="flexc" style="gap:18px;height:96px">
  <div><div style="font-size:42px;line-height:1.1">{bd['map']}</div><div class="m reg" style="font-size:21px">{bd['mode'].lower()}, round {bd['round']}, <span style="color:var(--c);font-weight:700">{bd['time']}</span> left</div></div>
  <div class="tile" style="margin-left:auto;width:88px;height:88px;background:{TEAM['blossom'][0]};font-size:64px">{bd['us']}</div>
  <div class="tile" style="width:88px;height:88px;background:{TEAM['sky'][0]};font-size:64px">{bd['them']}</div>
 </div>
 <div style="height:2px;background:var(--s3);margin:18px 0 6px"></div>
 {head_row}{blocks}
</div>
</div>"""
    return page("D scoreboard", CSS, body)


FRAMES = {"hub": hub, "match": match, "loadout": loadout, "shop": shop, "phone": phone, "scoreboard": scoreboard}
