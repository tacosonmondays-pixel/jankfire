"""Direction D: SIGNAL. The hubs are stations, concourses and hotels, so the menus talk like their
signs: navy enamel with a cream keyline, sentence case in Titillium Web, platform badges for keys.
Nothing floats: every sign hangs from the top edge, stands on the bottom edge, or sticks out of a
side wall, and its keyline stops where it meets the edge. Two registers: menus are signs; in a
match only the score hangs as a sign and the rest is bare type with a shadow. Butter enamel
plates are the only buttons (Play, Buy, Done)."""
from common import *

NAME = "D  SIGNAL"
CSS = """
:root{--s:#173a33;--s2:#1f4a41;--s3:#2f6155;--c:#f1ead9;--m:#a9c2b8;--a:#f5dd8a}
body{font-family:'Titillium Web';font-weight:700;color:var(--c);font-variant-numeric:tabular-nums}
.sign{position:absolute;background:rgba(23,58,51,.93);border:none;border-radius:14px;box-shadow:0 12px 28px rgba(0,0,0,.3)}
.hang{top:0;border-top:none;border-radius:0 0 14px 14px}
.stand{bottom:0;border-bottom:none;border-radius:14px 14px 0 0}
.fromL{left:0;border-left:none;border-radius:0 14px 14px 0}
.fromR{right:0;border-right:none;border-radius:14px 0 0 14px}
.corner{top:0;right:0;border-top:none;border-right:none;border-radius:0 0 0 14px}
.sign.plain{border:none;background:rgba(23,58,51,.9);box-shadow:0 10px 24px rgba(0,0,0,.26)}
.arrow{clip-path:polygon(0 0,calc(100% - 46px) 0,100% 50%,calc(100% - 46px) 100%,0 100%)}
.arrow.s{clip-path:polygon(0 0,calc(100% - 26px) 0,100% 50%,calc(100% - 26px) 100%,0 100%)}
.notch{clip-path:polygon(0 0,100% 0,100% calc(100% - 9px),calc(50% + 10px) calc(100% - 9px),50% 100%,calc(50% - 10px) calc(100% - 9px),0 calc(100% - 9px))}
.way{display:inline-block;color:var(--a);line-height:0}
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
.scrim{position:absolute;inset:0;background:rgba(10,18,16,.58)}
.bare{color:#fff;text-shadow:0 2px 0 rgba(0,0,0,.45),0 0 16px rgba(0,0,0,.5)}
.shade{position:absolute;inset:0;background:radial-gradient(60% 55% at 0% 100%,rgba(10,14,20,.55),rgba(10,14,20,0) 70%),radial-gradient(60% 55% at 100% 100%,rgba(10,14,20,.5),rgba(10,14,20,0) 70%)}
"""


def way(size=26, color="var(--a)"):
    """The wayfinding arrow: 'you are here' / 'this one'."""
    return f'<span class="way" style="font-size:{size}px;color:{color}">{icon("way")}</span>'


def hub():
    caret = '<svg width="20" height="14" viewBox="0 0 20 14" style="flex:none"><path d="M2 2h16L10 12z" fill="currentColor"/></svg>'
    go = ""
    nq, nd, ng = NEXT_QUEST
    rows = (f"""<div class="row" style="height:84px;padding:0 34px;gap:10px">
 <div style="flex:1"><div class="flexc"><span style="font-size:31px">Quests</span><span class="m reg" style="font-size:20px;margin-left:auto">{QUESTS_DONE[0]} of {QUESTS_DONE[1]} done</span></div>
 <div class="flexc" style="gap:12px;margin-top:6px"><span class="reg" style="font-size:19px">{nq}</span><div class="hbar" style="flex:1;height:8px"><b style="width:{nd/ng*100:.0f}%"></b></div><span class="m reg" style="font-size:17px">{nd}/{ng}</span></div></div>{go}</div>"""
            f"""<div class="row" style="height:84px;padding:0 34px;gap:10px"><div><div style="font-size:31px;line-height:1.1">Party</div><div class="m reg" style="font-size:17px">{PLAYER['name']} and Dxnny4K</div></div><span class="flexc" style="margin-left:auto;gap:8px">{head(0, 40)}{head(1, 40)}</span>{go}</div>"""
            f"""<div class="row" style="height:84px;padding:0 34px;gap:10px"><div><div style="font-size:31px;line-height:1.1">Loadout</div><div class="m reg" style="font-size:17px">Assault Rifle, Revolver</div></div><span class="flexc" style="margin-left:auto;gap:12px">{slot_icon("ar", 62, 26)}<span style="opacity:.8">{slot_icon("revolver", 40, 24)}</span></span>{go}</div>"""
            f"""<div class="row" style="height:84px;padding:0 34px;gap:10px"><div><div style="font-size:31px;line-height:1.1">Shop</div><div class="m reg" style="font-size:17px">New daily in {DAILY_RESET}</div></div>
 <span class="flexc" style="margin-left:auto;gap:10px;font-size:22px">{cur('coin', 26)}{WALLET['coins']}<span style="width:6px"></span>{cur('ticket', 30)}{WALLET['tickets']}</span>{go}</div>""")
    xp = PLAYER['xp'] / PLAYER['xp_next']
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_spawn.jpg)"></div>
<div class="sign corner" style="width:500px">
 <div style="padding:44px 34px 14px">
  <div style="font-size:54px;line-height:1.05">The Rotunda</div>
  <div class="flexc" style="margin-top:6px;gap:12px"><span class="m reg" style="font-size:22px">{HUB['here']} players here</span>
   <span class="flexc" style="margin-left:auto;height:38px;padding:0 14px;border-radius:7px;background:var(--s2);font-size:19px">Change hub</span></div>
 </div>
 <div style="padding:18px 34px 24px;border-top:2px solid var(--s3);background:var(--s2)">
  <div class="btn arrow" style="width:100%;height:124px;border-radius:0;justify-content:flex-start;padding-left:34px;font-size:92px;letter-spacing:.01em;box-shadow:none">Play</div>
  <div class="flexc" style="margin-top:10px;height:52px;padding:0 18px;border-radius:8px;background:var(--s);gap:10px;font-size:24px"><span class="m reg" style="font-size:19px">Mode</span>Ranked 2v2<span class="m reg" style="font-size:18px;margin-left:10px">rating {RATING}</span><span style="margin-left:auto">{caret}</span></div>
 </div>
 {rows}
 <div class="flexc" style="padding:18px 34px 30px;gap:16px;border-top:2px solid var(--s3)">{head(0, 50)}
  <div style="flex:1"><div style="font-size:27px">{PLAYER['name']}</div>
  <div class="hbar" style="height:7px;margin-top:6px"><b style="width:{xp*100:.0f}%"></b></div>
  <div class="flexc m reg" style="font-size:16px;margin-top:4px;justify-content:space-between"><span>Level {PLAYER['level']}</span><span>{PLAYER['xp']:,} / {PLAYER['xp_next']:,} XP</span></div></div>
  <span class="flexc" style="height:40px;padding:0 14px;border-radius:7px;background:var(--s2);font-size:19px">Settings</span></div>
</div>
</div>"""
    return page("D hub", CSS, body)


def match():
    m = MATCH
    def sq(team, n):
        return f'<div class="tile" style="width:50px;height:46px;border-radius:6px;background:{TEAM[team][0]};font-size:38px;line-height:1">{n}</div>'
    feed = "".join(f'<div class="flexc" style="width:max-content;margin-left:auto;gap:12px;height:42px;margin-bottom:6px;padding:0 18px;border-radius:2px;background:{"#2a5c50" if f[0] == PLAYER["name"] else "rgba(23,58,51,.72)"};font-size:21px">{feed_line(*f)}</div>' for f in FEED)
    slots = ""
    for i, (k, g, n) in enumerate(SLOTS + [("G", None, "")]):
        on = i == 0
        inner = slot_icon(g, 62, 28) if g else f'<span style="font-size:28px;line-height:0">{icon("grenade")}</span><span style="font-size:20px;margin-left:4px">×{m["util_n"]}</span>'
        slots += f'<div class="flexc bare" style="gap:9px;opacity:{1 if on else .62}"><span class="badge" style="height:28px;font-size:17px;text-shadow:none;{"background:var(--a)" if on else ""}">{k}</span><span class="flexc" style="height:42px;padding:0 10px;border-radius:7px;background:rgba(23,58,51,.62);text-shadow:none">{inner}</span></div>'
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_crate.jpg)"></div><div class="shade"></div>
<div class="abs flexc" style="left:50%;transform:translateX(-50%);top:0;padding:12px 22px 14px 46px;gap:20px;background:rgba(23,58,51,.7);border-radius:0 0 4px 4px">
 <div style="display:flex;flex-direction:column;gap:6px">
  <div class="flexc" style="gap:12px;position:relative"><span style="position:absolute;left:-34px;top:9px">{way(24)}</span>{sq('blossom', m['us'])}{alive_heads('blossom', 30)}</div>
  <div class="flexc" style="gap:12px">{sq('sky', m['them'])}{alive_heads('sky', 30)}</div>
 </div>
 <div style="text-align:right"><div style="font-size:48px;line-height:1">{m['time']}</div><div class="m" style="font-size:19px;margin-top:4px">Round {m['round']}</div></div>
</div>
<div class="abs" style="right:56px;top:40px">{feed}</div>
<div class="abs bare" style="left:60px;bottom:48px"><div style="margin-bottom:14px;filter:drop-shadow(0 2px 0 rgba(0,0,0,.45))"><span class="flexc" style="gap:10px"><span class="badge" style="height:30px;font-size:18px;text-shadow:none">E</span>{grapple_readout('#fff', 36)}</span></div><div style="font-size:84px;line-height:1">{m['hp']}</div>
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
    pics = {"GRAPPLE": f'<span style="font-size:52px;line-height:0;color:var(--c)">{icon("hook")}</span>', "PRIMARY": gunpic("ar", "gimg"), "SECONDARY": '<img class="gimg" src="../img/items/wish_duck_34.png">', "MELEE": gunpic("katana", "gimg"), "UTILITY": '<img class="gimg" src="../img/items/frag.png" style="max-height:76px">'}
    for i, (slot, g, name, note) in enumerate(LOADOUT5):
        on = i == SEL
        sub = {"UTILITY": "×2", "GRAPPLE": "×2"}.get(slot, "")
        gates += f"""<div class="sign fromL {"arrow" if on else ""}" style="top:{140 + i*112}px;width:{640 if on else 580}px;height:100px;{"background:#2a5c50;border-radius:0" if on else ""}">
 <div class="badge" style="position:absolute;left:52px;top:23px;width:56px;height:56px;font-size:32px;{"background:var(--a)" if on else ""}">{KEYS5[i]}</div>
 <div style="position:absolute;left:130px;top:{16 if sub else 28}px;font-size:36px;line-height:1.2;{"color:var(--a)" if on else ""}">{name}</div>
 {f'<div class="m reg" style="position:absolute;left:131px;top:60px;font-size:20px">{sub}</div>' if sub else ''}
 <div style="position:absolute;right:{64 if on else 24}px;top:13px;width:150px;height:76px;display:grid;place-items:center">{pics[slot]}</div></div>"""
    stats = "".join(f'<div style="flex:1"><div class="m" style="font-size:19px">{k}</div><div style="font-size:38px;line-height:1.2">{v}</div><div class="hbar" style="height:9px;margin-top:6px"><b style="width:{f*100:.0f}%"></b><u style="left:{avg*100:.0f}%"></u></div></div>' for (k, v, f), avg in zip(STATS, STAT_AVG))
    board = ""
    for i, (g, n, st) in enumerate(ARMORY):
        locked = isinstance(st, tuple)
        if locked:
            s = (f'<span class="m reg flexc" style="gap:6px">{icon("lock")}Level {st[1]}</span>' if st[0] == "level"
                 else f'<span style="display:block;text-align:right;line-height:1.15"><span class="flexc m" style="gap:6px;justify-content:flex-end">{cur("coin", 22)}{st[1]}</span><span class="reg" style="font-size:16px;color:#e8b07a">need {int(st[1].replace(",", "")) - WALLET_N:,} more</span></span>')
        else:
            s = '<span style="color:var(--a)">Equipped</span>' if st == "on" else ""
        board += f"""<div class="row" style="height:72px;padding:0 30px;gap:18px;{"background:var(--s2)" if st == "on" else ""}">
 <div style="width:100px;display:grid;place-items:center;{"color:var(--m)" if locked else ""}">{sil_area(g, 2000, 40) if g != "akimbo" else silpic(g)}</div>
 <span style="font-size:27px;white-space:nowrap;{"color:var(--m)" if locked else ""}">{n}</span><span style="margin-left:auto;font-size:21px">{s}</span></div>"""
    cos = "".join(f'<div style="flex:1"><div class="tile d" style="height:110px;border-radius:6px"><img src="../img/items/{img}.png" style="max-width:150px;max-height:96px"></div><div class="flexc" style="gap:10px;margin-top:10px"><span class="m reg" style="font-size:18px">{k}</span><span style="font-size:24px">{v}</span></div></div>'
                  for k, v, img in [("Skin", "Wish Duck", "wish_duck_34"), ("Hat", "Royal Duck", "royal-duck")])
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_rotunda_blur.jpg)"></div><div class="scrim"></div>
<style>.gimg{{max-width:150px;max-height:72px}} .sil{{width:84px;height:30px}} .ic{{width:.9em;height:.9em}}</style>
<div class="abs" style="left:56px;top:40px;font-size:64px;line-height:1.2">Loadout</div>
{gates}
{hatted(560, style="left:720px;top:150px")}
<div class="sign stand flexc" style="left:0;right:0;height:240px;border-radius:0;align-items:stretch">
 <div style="width:1180px;padding:24px 40px 0 56px;border-right:2px solid var(--s3)">
  <div class="flexc" style="gap:14px"><span style="font-size:38px">{SEL_GUN['name']}</span><span class="m reg" style="font-size:20px">Wish Duck skin</span>
   <span class="m" style="margin-left:auto;font-size:20px">Mastery {MASTERY['level']}</span><div class="hbar" style="width:220px;height:8px"><b style="width:{MASTERY['frac']*100:.0f}%"></b></div><span class="m reg" style="font-size:17px">{MASTERY['xp']} / {MASTERY['next']} XP</span></div>
  <div style="display:flex;gap:34px;padding-top:18px">{stats}</div>
  <div class="flexc m reg" style="font-size:16px;gap:8px;padding-top:12px;padding-bottom:28px"><i style="width:3px;height:14px;background:var(--a)"></i>secondary average</div>
 </div>
 <div style="flex:1;padding:26px 56px 0 40px;display:flex;gap:24px">{cos}</div>
</div>
<div class="sign corner plain" style="width:500px">
 <div style="padding:46px 30px 16px;font-size:36px">Secondaries</div>
 {board}
 <div style="padding:20px 30px 26px;border-top:2px solid var(--s3)"><div class="btn arrow s" style="width:100%;height:68px;font-size:32px;border-radius:0;box-shadow:none;justify-content:flex-start;padding-left:30px">Done</div></div>
</div>
</div>"""
    return page("D loadout", CSS, body)


def shop():
    tabs = "".join(f'<div class="flexc" style="height:50px;padding:0 20px;border-radius:6px;font-size:25px;{"background:var(--a);color:var(--s);height:58px;padding-bottom:8px;border-radius:6px 6px 0 0" if i == 0 else ""}" class="{"notch" if i == 0 else ""}">{t.title()}</div>' for i, t in enumerate(SHOP_TABS))
    daily = "".join(f"""<div class="row" style="height:124px;gap:18px;padding:0 6px;{"border-top:none" if i == 0 else ""}">
 <div class="tile d" style="position:relative;width:190px;height:100px;border-radius:6px;overflow:hidden;box-shadow:inset 0 0 0 3px {RARITY[rar]}">{f'<img src="../img/items/{img}.png" style="max-width:176px;max-height:84px">' if kind != "Wrap" else f'<img src="../img/items/{img}.png" style="position:absolute;left:-150px;top:-46px;width:460px">'}</div>
 <div style="flex:1"><div style="font-size:28px;line-height:1.15">{name}</div><div class="reg" style="font-size:19px"><span style="color:{RARITY[rar]};font-weight:700">{rar.title()}</span> <span class="m">{kind.lower()}</span></div></div>
 <div style="text-align:right;margin-right:8px"><div class="flexc" style="gap:8px;font-size:27px;justify-content:flex-end;{"" if afford(price) else "color:var(--m)"}">{rbx() if curr == "robux" else cur("coin", 28)}{price}</div>{"" if afford(price) else f'<div class="reg" style="font-size:16px;color:#e8b07a">need {int(price.replace(",", "")) - WALLET_N:,} more</div>'}</div></div>""" for i, (img, name, kind, price, curr, rar) in enumerate(DAILY))
    cells = "".join(f"""<div class="row" style="height:76px;gap:16px;{"border-top:none" if i == 0 else ""}"><div class="tile d" style="width:100px;height:62px;border-radius:6px"><img src="../img/items/{img}.png" style="max-width:90px;max-height:54px"></div>
 <div style="flex:1"><div style="font-size:24px;line-height:1.1">{name}</div><div class="m reg" style="font-size:16px">{holds}</div></div>
 <span style="text-align:right"><span class="flexc" style="gap:6px;font-size:22px;justify-content:flex-end;{"" if int(tk) <= TICKETS_N else "color:var(--m);opacity:.8"}">{cur('ticket', 28)}{tk}</span>{"" if int(tk) <= TICKETS_N else f'<span class="reg" style="display:block;font-size:13px;color:#e8b07a">need {int(tk) - TICKETS_N} more</span>'}</span><span class="m reg" style="font-size:17px">or</span><span class="flexc" style="gap:4px;font-size:22px;width:70px;justify-content:flex-end">{rbx()} {rp}</span></div>""" for i, (img, name, holds, tk, rp) in enumerate(CONTAINERS))
    packs = "".join(f"""<div class="row" style="height:58px;gap:14px;{"border-top:none" if i == 0 else ""}"><span style="font-size:27px;width:290px">{(f"{int(c.replace(',', '')) - int(b.split()[0].replace(',', '')):,}" if b else c)}<span class="m reg" style="font-size:22px">{(" + " + b.split()[0]) if b else ""}</span> <span class="m reg" style="font-size:17px">coins</span></span><span style="flex:1"></span><span class="flexc" style="gap:4px;font-size:24px">{rbx()} {r}</span></div>""" for i, (c, r, b) in enumerate(COIN_PACKS))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_rotunda_blur.jpg)"></div><div class="scrim"></div>
<div class="abs" style="left:56px;top:26px;font-size:64px;line-height:1.2">Shop</div>
<div class="sign hang plain flexc" style="left:250px;height:84px;padding:12px 14px 0;gap:4px">{tabs}</div>
<div class="sign hang plain flexc" style="right:56px;height:84px;padding:10px 28px 0 22px;gap:10px;font-size:30px">
 {cur('coin', 36)}{WALLET['coins']}<span style="width:14px"></span>{cur('ticket', 40)}{WALLET['tickets']}</div>
<div class="sign fromL arrow" style="top:150px;width:1150px;height:580px;border-radius:0">
 <div class="flexc" style="position:absolute;left:56px;top:26px;gap:18px"><span style="font-size:72px;line-height:1.1">Seraph</span><span class="m reg" style="font-size:24px;margin-top:22px">set of {len(HERO['set'])}</span></div>
 <div class="btn arrow s" style="position:absolute;right:40px;top:40px;height:74px;padding:0 50px 0 30px;gap:12px;font-size:38px;border-radius:0;box-shadow:none">Buy {rbx()} {HERO['price']}</div>
 <div style="position:absolute;left:50px;top:160px">{set_shot(1020, 400)}</div>
</div>
<div class="sign fromR plain" style="top:150px;width:714px;height:580px;padding:22px 56px 14px 30px;background:rgba(14,36,31,.94)">
 <div class="flexc" style="height:44px;margin-bottom:8px"><span style="font-size:32px">Daily</span><span class="m reg" style="font-size:21px;margin-left:auto">New in {DAILY_RESET}</span></div>
 {daily}
</div>
<div class="sign stand plain flexc" style="left:0;right:0;height:330px;border-radius:0;align-items:stretch;padding-left:36px">
 <div style="width:930px;padding:20px 30px 18px 20px;border-right:2px solid var(--s3)"><div style="font-size:27px;margin-bottom:4px">Crates</div>{cells}</div>
 <div style="flex:1;padding:20px 56px 18px 30px"><div style="font-size:27px;margin-bottom:4px">Coins</div>{packs}</div>
</div>
</div>"""
    return page("D shop", CSS, body)


def phone():
    m = MATCH
    keys = "".join(f'<div class="abs" style="left:{x - s/2:.0f}px;top:{y - s/2:.0f}px;width:{s}px;height:{s}px;border-radius:50%;background:rgba(23,58,51,.86);display:grid;place-items:center;color:var(--c)">' + f'<span style="margin-top:{-7 if k in ("hook", "grenade") else 0}px">{act_icon(k, int(s*0.56))}</span>' + (f'<span style="position:absolute;left:0;right:0;bottom:4px;text-align:center;font-size:12px">×{GRAPPLE["charges"] if k == "hook" else m["util_n"]}</span>' if k in ("hook", "grenade") else "") + '</div>' for k, x, y, s in [(k, x, y, 56 if k in ("jump", "slide") else 44) for k, x, y, s in arc(752, 212, 134, 92, 260)])
    pfeed = "".join(f'<div class="flexc" style="width:max-content;margin-left:auto;gap:6px;height:20px;margin-bottom:3px;padding:0 8px;border-radius:4px;background:{"#2a5c50" if f[0] == PLAYER["name"] else "rgba(23,58,51,.78)"};font-size:11px">{feed_line(*f, size=11)}</div>' for f in FEED)
    slots = "".join(f'<div style="display:grid;place-items:center;width:56px;height:34px;border-radius:8px;background:{"rgba(245,221,138,.92)" if i == 0 else "rgba(23,58,51,.6)"};color:{"var(--s)" if i == 0 else "var(--c)"}">{slot_icon(g, 40, 18)}</div>' for i, (k, g, n) in enumerate(SLOTS))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_crate.jpg)"></div><div class="shade"></div>

<div class="abs" style="left:50%;transform:translateX(-50%);top:0;display:flex;flex-direction:column;align-items:center">
 <div class="flexc" style="padding:5px 10px 6px 26px;gap:10px;background:rgba(23,58,51,.78);border-radius:0 0 8px 8px">
  <div style="display:flex;flex-direction:column;gap:3px">
   <div class="flexc" style="gap:6px;position:relative"><span style="position:absolute;left:-20px;top:4px">{way(14)}</span><div class="tile" style="width:26px;height:22px;border-radius:4px;background:{TEAM['blossom'][0]};font-size:19px;line-height:1">{m['us']}</div>{alive_heads('blossom', 15, 3)}</div>
   <div class="flexc" style="gap:6px"><div class="tile" style="width:26px;height:22px;border-radius:4px;background:{TEAM['sky'][0]};font-size:19px;line-height:1">{m['them']}</div>{alive_heads('sky', 15, 3)}</div>
  </div>
  <div style="text-align:right"><div style="font-size:22px;line-height:1">{m['time']}</div><div class="m" style="font-size:10px;margin-top:2px">Round {m['round']}</div></div>
 </div>
 {scores_tab('rgba(23,58,51,.86)', 'var(--c)', 11, '0 0 4px 4px', 'margin-top:3px')}
</div>
<div class="abs" style="right:12px;top:8px">{pfeed}</div>
<div class="abs" style="left:76px;top:144px;width:88px;height:88px;border-radius:50%;background:rgba(23,58,51,.86)"></div>
<div class="tile" style="position:absolute;left:100px;top:168px;width:40px;height:40px;border-radius:50%"></div>
<div class="abs flexc" style="left:226px;bottom:12px;gap:26px;align-items:flex-end">
 <div class="bare"><div style="font-size:38px;line-height:1">{m['hp']}</div><div class="hbar" style="width:90px;height:7px;margin-top:6px;background:rgba(255,255,255,.25)"><b style="width:{m['hp']}%"></b></div></div>
 <div><div class="flexc" style="gap:8px;margin-bottom:6px">{slots}</div>
  <div class="bare"><span style="font-size:36px;line-height:1">{m['ammo']}</span><span class="reg" style="font-size:16px;opacity:.8"> / {m['mag']}</span></div></div>
</div>
{keys}
<div class="tile" style="position:absolute;left:706px;top:162px;width:104px;height:104px;border-radius:50%;background:var(--a);color:var(--s);box-shadow:inset 0 0 0 4px var(--a),inset 0 0 0 6px rgba(29,43,58,.35),0 6px 14px rgba(0,0,0,.3)">{fire_icon(34)}</div>
<svg class="abs" style="left:412px;top:185px" width="20" height="20" viewBox="0 0 36 36"><g stroke="#1d2b3a" stroke-width="7" stroke-linecap="round"><path d="M18 3v8M18 25v8M3 18h8M25 18h8"/></g><g stroke="#f1ead9" stroke-width="3.4" stroke-linecap="round"><path d="M18 3v8M18 25v8M3 18h8M25 18h8"/></g></svg>
</div>"""
    return page("D phone", CSS, body, 844, 390)


def scoreboard():
    bd = BOARD
    cols = [("Holding", 120), ("Kills", 76), ("Deaths", 92), ("Assists", 96), ("Damage", 116), ("Ping", 80)]
    head_row = '<div class="flexc m" style="height:40px;font-size:19px;padding:0 24px 0 86px"><span style="flex:1">Player</span>' + "".join(f'<span style="width:{w}px;text-align:center">{h}</span>' for h, w in cols) + "</div>"
    blocks, n = "", 0
    for team, players in bd["teams"]:
        c, d = TEAM[team]
        rows = ""
        for j, (nm, k, de, a, dmg, ping, alive, me) in enumerate(players):
            br = (party_mark2(112, "var(--m)", "Party", -28, 15) if nm in PARTY and me else "") + (f'<span style="position:absolute;left:-60px;top:17px">{way(26)}</span>' if me else "")
            rows += f"""<div class="row" style="position:relative;height:60px;padding:0 24px 0 20px;{"background:#2a5c50;border-radius:6px;border-top-color:transparent" if me else ""}">{br}
 <span style="position:relative;margin-right:22px"><span style="display:inline-block;{"" if alive else "filter:grayscale(1);opacity:.55"}">{head(n, 44)}</span>{"" if alive else dead_x(44)}</span>
 <span style="flex:1;font-size:25px;{"" if alive else "color:var(--m)"}">{nm} <span class="m reg" style="font-size:18px;margin-left:4px">Lv {LEVELS[nm]}</span></span>
 <span style="width:120px;display:flex;justify-content:center;{"" if alive else "opacity:.6"}">{sil_even(HOLDING[nm], 24, 96)}</span>{"".join(f'<span style="width:{w}px;text-align:center;font-size:25px">{v}</span>' for v, w in [(k, 76), (de, 92), (a, 96), (dmg, 116)])}<span class="m reg" style="width:80px;text-align:center;font-size:22px">{ping}</span></div>"""
            n += 1
        blocks += f"""<div style="margin-top:12px"><div class="flexc" style="height:44px;gap:14px;padding:0 24px"><span style="font-size:28px;color:{c}">{team.title()}</span><span class="m reg" style="font-size:20px">{sum(p[1] for p in players)} kills</span></div>{rows}</div>"""
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_forest_blur.jpg)"></div><div class="scrim" style="background:rgba(12,17,24,.35)"></div>
<div class="sign hang" style="left:50%;transform:translateX(-50%);width:1200px;padding:26px 30px 30px 96px">
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
