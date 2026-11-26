"""Direction A: PLATE. Made of the hub's own parts. One rule: only things you can press are plates
(bone, with the queue pads' thick lip); everything you only read is type straight on the world
over a soft shade. PLAY is the one big pad: ink with the pads' cream rim. Ink is the action
colour; the team pastels show only inside the score pads. Two registers of type: Builder Sans
ExtraBold caps for names and numbers, Builder Sans Medium in sentence case for everything said."""
from common import *

NAME = "A  PLATE"
CSS = """
:root{--bone:#efe9de;--bone2:#e2d9c9;--lip:#c3b8a5;--ink:#1d1f23;--ink2:#5d584f}
body{font-family:'Builder Sans';font-weight:800;color:var(--ink);font-variant-numeric:tabular-nums}
.plate{position:absolute;background:var(--bone);border-radius:16px;box-shadow:0 5px 0 var(--lip),0 14px 26px rgba(0,0,0,.28)}
.plate.ink{background:var(--ink);color:var(--bone);box-shadow:0 5px 0 #000,0 14px 26px rgba(0,0,0,.34)}
.pad{position:absolute;background:var(--ink);color:var(--bone);border-radius:26px;box-shadow:inset 0 0 0 7px var(--bone),inset 0 0 0 9px var(--lip),0 7px 0 var(--lip),0 18px 32px rgba(0,0,0,.35)}
.flat{position:absolute;background:var(--bone);border-radius:10px;box-shadow:0 10px 26px rgba(0,0,0,.22)}
.sp{border-radius:11px;box-shadow:inset 0 3px 0 rgba(0,0,0,.16);display:grid;place-items:center;color:var(--ink)}
.bm{font-weight:500;text-transform:none}
.dim{color:var(--ink2)}
.flexc{display:flex;align-items:center}
.bar{height:14px;border-radius:7px;overflow:hidden;background:var(--bone2);position:relative}
.bar>b{display:block;height:100%;border-radius:7px;background:var(--ink)}
.bar>u{position:absolute;top:0;bottom:0;width:3px;background:#b0632f}
.wash{position:absolute;inset:0;background:rgba(28,26,23,.55)}
.lab{font-size:17px;color:var(--ink2)}
.price{display:inline-flex;align-items:center;gap:8px;padding:0 16px;height:46px;border-radius:12px;background:var(--ink);color:var(--bone);font-size:22px;box-shadow:0 4px 0 #000}
.w{color:#fff;text-shadow:0 2px 0 rgba(0,0,0,.4),0 0 18px rgba(0,0,0,.5)}
.wd{color:rgba(255,255,255,.8)}
.shade{position:absolute;inset:0;background:radial-gradient(60% 60% at 0% 100%,rgba(10,10,12,.62),rgba(10,10,12,0) 72%),radial-gradient(60% 55% at 100% 100%,rgba(10,10,12,.5),rgba(10,10,12,0) 70%),radial-gradient(45% 40% at 100% 0%,rgba(10,10,12,.42),rgba(10,10,12,0) 70%),radial-gradient(40% 35% at 0% 0%,rgba(10,10,12,.4),rgba(10,10,12,0) 70%)}
.tk{filter:drop-shadow(0 0 1px #5d584f) drop-shadow(0 0 1px #5d584f)}
.key{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:9px;font-size:19px;background:var(--bone2);color:var(--ink);box-shadow:inset 0 2px 0 rgba(0,0,0,.12)}
"""


def wallet(top=56, right=64):
    return f"""<div class="abs flexc w" style="right:{right}px;top:{top}px;gap:12px;font-size:30px">{cur('coin', 36)}{WALLET['coins']}<span style="width:18px"></span>{cur('ticket', 44)}{WALLET['tickets']}</div>"""


def hub():
    xp = PLAYER['xp'] / PLAYER['xp_next']
    links = [("QUESTS", f"{QUESTS_DONE[0]}/{QUESTS_DONE[1]}"), ("PARTY", "1/4"), ("LOADOUT", ""), ("SHOP", ""), ("HUBS", ""), ("PROFILE", ""), ("SETTINGS", "")]
    menu = "".join(f'<div class="flexc w" style="height:{56 if i < 2 else 46}px;font-size:{32 if i < 2 else 24}px;gap:14px;{"" if i < 2 else "opacity:.92"}">{t}<span class="wd" style="font-size:24px">{c}</span></div>' for i, (t, c) in enumerate(links))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_spawn.jpg)"></div><div class="shade"></div>
<div class="abs flexc w" style="left:60px;top:52px;gap:18px">{head(0, 60)}<div><div style="font-size:30px">{PLAYER['name']}</div>
 <div class="flexc" style="gap:12px;margin-top:6px"><span style="font-size:20px">LV {PLAYER['level']}</span><div style="width:200px;height:8px;border-radius:4px;background:rgba(255,255,255,.3)"><div style="width:{xp*100:.0f}%;height:100%;border-radius:4px;background:#fff"></div></div><span class="wd bm" style="font-size:18px">{PLAYER['xp']:,} / {PLAYER['xp_next']:,} xp</span></div></div></div>
{wallet()}
<div class="pad" style="left:56px;top:316px;width:420px;height:172px">
 <div style="position:absolute;left:38px;top:26px;font-size:96px;line-height:1">PLAY</div>
 <div style="position:absolute;left:41px;bottom:30px;font-size:22px;color:#b9b2a5">1V1 RANKED</div>
</div>
<div class="abs" style="left:62px;top:516px">{menu}</div>
<div class="abs w" style="left:62px;bottom:46px;font-size:22px">{HUB['name']} <span class="wd bm" style="margin-left:10px">{HUB['here']} here</span></div>
</div>"""
    return page("A hub", CSS, body)


def match():
    m = MATCH
    feed = "".join(f'<div class="flexc" style="justify-content:flex-end;gap:12px;height:40px;margin-bottom:6px;padding:0 16px;border-radius:8px;background:rgba(20,20,24,.62);color:#fff;font-size:21px">{feed_line(*f)}</div>' for f in FEED)
    slots = ""
    for i, (k, g, n) in enumerate(SLOTS + [("G", None, "")]):
        on = i == 0
        inner = slot_icon(g, 66, 30) if g else f'<span style="font-size:30px;line-height:0">{icon("grenade")}</span><span style="font-size:20px;margin-left:4px">×{m["util_n"]}</span>'
        slots += f'<div class="w" style="text-align:center;width:98px;opacity:{1 if on else .66}"><div class="flexc" style="height:36px;justify-content:center;filter:drop-shadow(0 2px 0 rgba(0,0,0,.4))">{inner}</div><div style="font-size:16px;margin-top:4px">{k}</div><div style="height:6px;margin-top:4px;border-radius:3px;background:{"var(--bone)" if on else "transparent"}"></div></div>'
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_crate.jpg)"></div><div class="shade"></div>
<div class="flat flexc" style="left:50%;transform:translateX(-50%);top:24px;height:92px;padding:0 12px;gap:16px;background:var(--ink);color:var(--bone);box-shadow:inset 0 0 0 3px var(--bone),0 10px 24px rgba(0,0,0,.3);border-radius:16px">
 <div class="sp" style="width:112px;height:68px;background:{TEAM['blossom'][0]};font-size:54px">{m['us']}</div>
 <div style="width:128px;text-align:center"><div style="font-size:17px;color:#b9b2a5">ROUND {m['round']}</div><div style="font-size:38px;line-height:1.05">{m['time']}</div></div>
 <div class="sp" style="width:112px;height:68px;background:{TEAM['sky'][0]};font-size:54px">{m['them']}</div>
</div>
<div class="abs" style="right:60px;top:40px">{feed}</div>
<div class="abs w" style="left:62px;bottom:50px">
 <div style="font-size:88px;line-height:1">{m['hp']}</div>
 <div style="width:300px;height:16px;margin-top:10px;border-radius:8px;background:rgba(255,255,255,.28)"><div style="width:{m['hp']}%;height:100%;border-radius:8px;background:var(--bone)"></div></div>
</div>
<div class="abs" style="right:60px;bottom:50px;text-align:right">
 <div class="flexc" style="gap:6px;justify-content:flex-end;margin-bottom:20px">{slots}</div>
 <div class="w" style="font-size:88px;line-height:1">{m['ammo']}<span style="font-size:38px;opacity:.72"> /{m['mag']}</span></div>
</div>
<svg class="abs" style="left:942px;top:522px" width="36" height="36" viewBox="0 0 36 36"><g stroke="#1d1f23" stroke-width="7" stroke-linecap="round"><path d="M18 3v8M18 25v8M3 18h8M25 18h8"/></g><g stroke="#efe9de" stroke-width="3.4" stroke-linecap="round"><path d="M18 3v8M18 25v8M3 18h8M25 18h8"/></g></svg>
</div>"""
    return page("A match", CSS, body)


def loadout():
    slots = ""
    pics = {"PRIMARY": gunpic("ar", "gp"), "SECONDARY": '<img class="gp" src="../img/items/wish_duck_34.png">', "MELEE": gunpic("katana", "gp"), "UTILITY": '<img class="gp" src="../img/items/frag.png" style="max-height:84px">'}
    for i, (slot, g, name, note) in enumerate(LOADOUT):
        on = i == SEL
        sub = {"SECONDARY": "Wish Duck skin", "UTILITY": "2 charges"}.get(slot, "")
        slots += f"""<div class="plate {"ink" if on else ""}" style="left:64px;top:{176 + i*124}px;width:480px;height:108px">
 <span class="key" style="position:absolute;left:22px;top:37px;{"background:#3a3d44;color:var(--bone);box-shadow:none" if on else ""}">{["1","2","3","G"][i]}</span>
 <div style="position:absolute;left:76px;top:{24 if sub else 36}px;font-size:30px">{name.upper()}</div>
 {f'<div class="bm" style="position:absolute;left:76px;top:62px;font-size:19px;color:{"#b9b2a5" if on else "var(--ink2)"}">{sub}</div>' if sub else ''}
 <div style="position:absolute;right:18px;top:12px;width:170px;height:84px;display:grid;place-items:center">{pics[slot]}</div></div>"""
    stats = "".join(f"""<div style="margin-top:20px"><div class="flexc" style="justify-content:space-between"><span class="lab">{k.upper()}</span><span style="font-size:26px">{v}</span></div>
 <div class="bar" style="margin-top:8px"><b style="width:{f*100:.0f}%"></b><u style="left:{avg*100:.0f}%"></u></div></div>""" for (k, v, f), avg in zip(STATS, STAT_AVG))
    frac = MASTERY['frac']
    medal = f"""<svg width="92" height="92" viewBox="0 0 92 92" style="flex:none"><circle cx="46" cy="46" r="38" fill="none" stroke="#e2d9c9" stroke-width="10"/>
 <circle cx="46" cy="46" r="38" fill="none" stroke="#1d1f23" stroke-width="10" stroke-dasharray="{238.8*frac:.1f} 300" transform="rotate(-90 46 46)" stroke-linecap="round"/>
 <text x="46" y="58" text-anchor="middle" font-family="Builder Sans" font-weight="800" font-size="34" fill="#1d1f23">{MASTERY['level']}</text></svg>"""
    arm = ""
    for i, (g, n, st) in enumerate(ARMORY):
        on = st == "on"
        locked = isinstance(st, tuple)
        tag = ""
        if locked:
            tag = (f'<span class="price" style="height:34px;font-size:17px;padding:0 12px;border-radius:9px;box-shadow:0 3px 0 #000">{cur("coin", 22)}{st[1]}</span>' if st[0] == "coins"
                   else f'<span class="bm flexc" style="font-size:18px;color:var(--ink2);line-height:34px;gap:6px">{icon("lock")} Level {st[1]}</span>')
        arm += f"""<div class="plate {"ink" if on else ""}" style="left:{64 + i*362}px;bottom:44px;width:346px;height:142px;{"opacity:.86" if locked else ""}">
 <div style="position:absolute;left:18px;top:14px;width:190px;height:80px;display:grid;place-items:center;{"filter:grayscale(1) brightness(.85)" if locked else ""}">{gunpic(g, "ap")}</div>
 <div style="position:absolute;left:22px;top:100px;font-size:20px">{n.upper()}</div>
 <div style="position:absolute;right:16px;top:24px">{tag}</div></div>"""
    cos = "".join(f"""<div class="flexc" style="gap:14px;margin-top:{18 if i == 0 else 10}px"><span class="lab" style="width:48px">{k}</span>
 <div class="plate" style="position:relative;width:130px;height:74px;box-shadow:0 4px 0 var(--lip)"><img src="../img/items/{img}.png" style="position:absolute;left:12px;top:6px;max-width:106px;max-height:62px"></div>
 <div><div style="font-size:20px">{v}</div><div class="bm dim" style="font-size:16px">Equipped</div></div></div>""" for i, (k, v, img) in enumerate([("SKIN", "WISH DUCK", "wish_duck_34"), ("HAT", "ROYAL DUCK", "royal-duck")]))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_rotunda_blur.jpg)"></div><div class="wash"></div>
<style>.gp{{max-width:170px;max-height:80px}} .ap{{max-width:186px;max-height:76px}} .ic{{width:1em;height:1em}}</style>
<div class="abs w" style="left:64px;top:62px;font-size:52px">LOADOUT</div>
<div class="plate ink flexc" style="right:64px;top:62px;height:62px;padding:0 28px;font-size:24px">DONE</div>
{slots}
<img class="abs" src="../img/{SEL_GUN['img']}" style="left:610px;top:190px;width:690px;filter:drop-shadow(0 28px 30px rgba(0,0,0,.45))">
<div class="flat" style="left:1360px;top:176px;width:496px;height:676px;padding:28px">
 <div class="flexc" style="gap:20px">{medal}<div><div style="font-size:38px;line-height:1">{SEL_GUN['name'].upper()}</div><div class="bm dim" style="font-size:18px;margin-top:8px">Mastery {MASTERY['level']}, {MASTERY['xp']} of {MASTERY['next']} xp</div></div></div>
 {stats}
 <div class="flexc bm dim" style="font-size:16px;margin-top:10px;gap:8px"><i style="width:3px;height:14px;background:#b0632f"></i>secondary average</div>
 <div style="height:2px;background:var(--bone2);margin-top:16px"></div>
 {cos}
</div>
<div class="abs w" style="left:64px;bottom:204px;font-size:24px">SECONDARIES</div>
{arm}
</div>"""
    return page("A loadout", CSS, body)


def shop():
    tabs = "".join(f'<div class="{"plate ink" if i == 0 else "w"} flexc" style="position:relative;height:52px;padding:0 22px;font-size:22px">{t}</div>' for i, t in enumerate(SHOP_TABS))
    setrow = "".join(f'<div style="width:124px"><div style="height:70px;display:flex;align-items:flex-end"><img src="../img/items/{img}.png" style="max-width:118px;max-height:70px"></div>'
                     f'<div style="font-size:18px;margin-top:8px">{s.upper()}</div><div class="bm dim" style="font-size:16px">{g}</div></div>' for s, g, img in HERO['set'] + [("Royal Duck", "Hat", "royal-duck")])
    daily = ""
    for i, (img, name, kind, price, curr, rar) in enumerate(DAILY):
        tag = f'<span class="price">{rbx() if curr == "robux" else cur("coin", 24)}{price}</span>'
        daily += f"""<div class="plate" style="left:{64 + i*282}px;top:812px;width:268px;height:216px;background:linear-gradient(180deg,{RARITY[rar]}33,var(--bone) 55%)">
 <img src="../img/items/{img}.png" style="position:absolute;left:14px;top:-26px;max-width:238px;max-height:114px;filter:drop-shadow(0 8px 8px rgba(0,0,0,.25))">
 <div style="position:absolute;left:18px;top:100px;font-size:21px">{name.upper()}</div>
 <div class="bm" style="position:absolute;left:18px;top:128px;font-size:17px"><span style="color:{RARITY[rar]};font-weight:800;filter:brightness(.75)">{rar.title()}</span> <span class="dim">{kind.lower()}</span></div>
 <div style="position:absolute;left:16px;bottom:14px">{tag}</div></div>"""
    crates = "".join(f"""<div class="plate" style="left:1210px;top:{176 + i*120}px;width:646px;height:106px">
 <img src="../img/items/{img}.png" style="position:absolute;left:18px;top:10px;max-width:130px;max-height:86px">
 <div style="position:absolute;left:170px;top:22px;font-size:25px">{name.upper()}</div>
 <div class="bm dim" style="position:absolute;left:170px;top:56px;font-size:18px">{holds}</div>
 <div class="flexc" style="position:absolute;right:16px;top:30px;gap:10px"><span class="flexc tk" style="gap:6px;font-size:20px">{cur('ticket', 34)}{tk}</span><span class="bm dim" style="font-size:17px">or</span><span class="price">{rbx()}{rp}</span></div></div>""" for i, (img, name, holds, tk, rp) in enumerate(CONTAINERS))
    packs = "".join(f"""<div class="flexc" style="height:110px;padding:0 22px;border-top:{"none" if i == 0 else "2px solid var(--bone2)"};gap:16px">
 {cur('coin', 30 + i*8)}<div style="flex:1"><div style="font-size:30px">{c}</div><div class="bm dim" style="font-size:17px">{b or "coins"}</div></div>
 <span class="price">{rbx()}{r}</span></div>""" for i, (c, r, b) in enumerate(COIN_PACKS))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_rotunda_blur.jpg)"></div><div class="wash"></div>
<div class="plate flexc" style="left:64px;top:58px;height:60px;padding:0 22px;font-size:22px">BACK</div>
<div class="abs w" style="left:206px;top:60px;font-size:50px">SHOP</div>
<div class="abs flexc" style="left:380px;top:62px;gap:8px">{tabs}</div>
{wallet(70, 64)}
<div class="flat" style="left:64px;top:176px;width:1118px;height:580px">
 <img src="../img/items/wish_duck_34.png" style="position:absolute;left:-10px;top:-26px;width:560px;filter:drop-shadow(0 18px 18px rgba(0,0,0,.3))">
 <div style="position:absolute;left:580px;top:40px;font-size:104px;line-height:1">{HERO['name']}</div>
 <div class="bm dim" style="position:absolute;left:584px;top:156px;width:470px;font-size:22px;line-height:1.4">The VIP pass. Three skins, the Royal Duck hat and the VIP title.</div>
 <div class="flexc" style="position:absolute;left:584px;top:262px;gap:6px;align-items:flex-start;width:520px">{setrow}</div>
 <div style="position:absolute;left:584px;bottom:34px"><span class="price" style="height:70px;font-size:32px;padding:0 30px;border-radius:16px;box-shadow:0 5px 0 #000">{rbx()}{HERO['price']}</span></div>
</div>
{daily}
{crates}
<div class="flat" style="left:1210px;top:576px;width:646px;height:452px;padding-top:4px">{packs}</div>
</div>"""
    return page("A shop", CSS, body)


def phone():
    m = MATCH
    keys = ""
    for k, x, y, s in arc(752, 222, 122, 84, 266):
        keys += f'<div class="plate" style="left:{x - s/2:.0f}px;top:{y - s/2:.0f}px;width:{s}px;height:{s}px;border-radius:50%;box-shadow:0 3px 0 var(--lip),0 6px 12px rgba(0,0,0,.28);display:grid;place-items:center;color:var(--ink)">{act_icon(k, int(s*0.52))}</div>'
    slots = "".join(f'<div class="plate {"ink" if i == 0 else ""}" style="position:relative;width:64px;height:34px;border-radius:10px;display:grid;place-items:center;box-shadow:0 3px 0 {"#000" if i == 0 else "var(--lip)"}">{slot_icon(g, 44, 20)}</div>' for i, (k, g, n) in enumerate(SLOTS))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_crate.jpg)"></div><div class="shade"></div>
<div class="flat flexc" style="left:50%;transform:translateX(-50%);top:10px;height:48px;padding:0 6px;gap:8px;background:var(--ink);color:var(--bone);box-shadow:inset 0 0 0 2px var(--bone),0 6px 14px rgba(0,0,0,.3);border-radius:12px">
 <div class="sp" style="width:56px;height:36px;border-radius:8px;background:{TEAM['blossom'][0]};font-size:26px">{m['us']}</div>
 <div style="width:66px;text-align:center"><div style="font-size:9px;color:#b9b2a5">ROUND {m['round']}</div><div style="font-size:19px;line-height:1.05">{m['time']}</div></div>
 <div class="sp" style="width:56px;height:36px;border-radius:8px;background:{TEAM['sky'][0]};font-size:26px">{m['them']}</div>
</div>
<div class="abs" style="left:58px;top:124px;width:124px;height:124px;border-radius:50%;background:rgba(29,31,35,.32);box-shadow:inset 0 0 0 4px rgba(239,233,222,.8)"></div>
<div class="plate" style="left:92px;top:158px;width:56px;height:56px;border-radius:50%"></div>
<div class="abs flexc" style="left:232px;bottom:14px;gap:22px;align-items:flex-end">
 <div class="w"><div style="font-size:40px;line-height:1">{m['hp']}</div><div style="width:110px;height:8px;margin-top:6px;border-radius:4px;background:rgba(255,255,255,.3)"><div style="width:{m['hp']}%;height:100%;border-radius:4px;background:var(--bone)"></div></div></div>
 <div class="w" style="font-size:40px;line-height:1;padding-bottom:14px">{m['ammo']}<span style="font-size:19px;opacity:.8"> /{m['mag']}</span></div>
 <div class="flexc" style="gap:6px;padding-bottom:14px">{slots}</div>
</div>
{keys}
<div class="pad" style="left:700px;top:170px;width:104px;height:104px;border-radius:50%;display:grid;place-items:center;box-shadow:inset 0 0 0 4px var(--bone),0 4px 0 var(--lip),0 8px 16px rgba(0,0,0,.35)">{fire_icon(34)}</div>
<svg class="abs" style="left:412px;top:185px" width="20" height="20" viewBox="0 0 36 36"><g stroke="#1d1f23" stroke-width="7" stroke-linecap="round"><path d="M18 3v8M18 25v8M3 18h8M25 18h8"/></g><g stroke="#efe9de" stroke-width="3.4" stroke-linecap="round"><path d="M18 3v8M18 25v8M3 18h8M25 18h8"/></g></svg>
</div>"""
    return page("A phone", CSS, body, 844, 390)


def scoreboard():
    bd = BOARD
    cols = [("K", 56), ("D", 56), ("A", 56), ("DMG", 96), ("PING", 80)]
    head_row = '<div class="flexc lab" style="height:34px;padding:0 20px 0 82px"><span style="flex:1">PLAYER</span>' + "".join(f'<span style="width:{w}px;text-align:right">{h}</span>' for h, w in cols) + "</div>"
    blocks, n = "", 0
    for team, players in bd["teams"]:
        c, d = TEAM[team]
        rows = ""
        for j, (nm, k, de, a, dmg, ping, alive, me) in enumerate(players):
            style = "background:var(--ink);color:var(--bone);border-radius:12px" if me else ""
            br = party_bracket(124, "#b9b2a5") if nm in PARTY and j == 0 else ""
            rows += f"""<div class="flexc" style="position:relative;height:58px;margin:4px 0;padding:0 20px 0 14px;{style};{"" if alive else "color:#a49d90"}">{br}
 <span style="position:relative;margin-right:22px;{"" if alive else "filter:grayscale(1);opacity:.6"}">{head(n, 44)}{"" if alive else dead_x(44)}</span>
 <span style="flex:1;font-size:23px">{nm} <span class="bm" style="font-size:16px;opacity:.7;margin-left:6px">lv {LEVELS[nm]}</span></span>
 {"".join(f'<span style="width:{w}px;text-align:right;font-size:23px">{v}</span>' for v, w in [(k, 56), (de, 56), (a, 56), (dmg, 96), (ping, 80)])}</div>"""
            n += 1
        blocks += f"""<div style="margin-top:14px"><div class="flexc" style="gap:14px;height:38px;padding-left:16px"><span style="font-size:22px;color:{d}">{team.upper()}</span><span class="lab">{sum(p[1] for p in players)} KILLS</span></div>{rows}</div>"""
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_forest_blur.jpg)"></div><div class="wash" style="background:rgba(20,19,17,.4)"></div>
<div class="flat" style="left:470px;top:96px;width:980px;padding:24px 26px 22px 34px">
 <div class="flexc" style="height:96px;gap:22px">
  <div class="sp" style="width:112px;height:84px;background:{TEAM['blossom'][0]};font-size:60px">{bd['us']}</div>
  <div style="flex:1;text-align:center"><div style="font-size:34px">{bd['map'].upper()}</div><div class="bm dim" style="margin-top:4px;font-size:19px">Round {bd['round']}, <b style="color:var(--ink)">{bd['time']}</b> left</div></div>
  <div class="sp" style="width:112px;height:84px;background:{TEAM['sky'][0]};font-size:60px">{bd['them']}</div>
 </div>
 <div style="height:3px;background:var(--bone2);margin:14px 0 4px;border-radius:2px"></div>
 {head_row}{blocks}
</div>
</div>"""
    return page("A scoreboard", CSS, body)


FRAMES = {"hub": hub, "match": match, "loadout": loadout, "shop": shop, "phone": phone, "scoreboard": scoreboard}
