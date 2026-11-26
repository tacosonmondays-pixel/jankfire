"""Direction A: PLATE. Made of the hub's own parts. One rule: only things you can press are plates
(bone, with the queue pads' thick lip); everything you only read is flat or straight on the world.
PLAY is the one big pad: ink with the pads' cream rim. The set's own mark is a stencil slit through
the big numbers and PLAY (in Roblox a UIGradient transparency band). Ink is the action colour; the
team pastels show only inside the score pads. Two registers of type: Builder Sans ExtraBold caps
for names and numbers, Builder Sans Medium in sentence case for everything said."""
from common import *

NAME = "A  PLATE"
CSS = """
:root{--bone:#e5e2db;--bone2:#d4d0c7;--lip:#aaa498;--ink:#1d1f23;--ink2:#56534d}
body{font-family:'Builder Sans';font-weight:800;color:var(--ink);font-variant-numeric:tabular-nums}
.plate{position:absolute;background:var(--bone);border-radius:16px;box-shadow:0 5px 0 var(--lip),0 14px 26px rgba(0,0,0,.28)}
.plate.ink{background:var(--ink);color:var(--bone);box-shadow:0 5px 0 #000,0 14px 26px rgba(0,0,0,.34)}
.pad{position:absolute;background:var(--ink);color:var(--bone);border-radius:26px;box-shadow:inset 0 0 0 7px var(--bone),inset 0 0 0 9px var(--lip),0 7px 0 var(--lip),0 18px 32px rgba(0,0,0,.35)}
.flat{position:absolute;background:var(--bone);border-radius:3px;box-shadow:0 10px 26px rgba(0,0,0,.22)}
.flat.ink{background:#22252a;color:var(--bone)}
.sp{border-radius:4px;display:grid;place-items:center;color:var(--ink)}
.bm{font-weight:500;text-transform:none}
.dim{color:var(--ink2)}
.flexc{display:flex;align-items:center}
.bar{height:14px;border-radius:7px;overflow:hidden;background:var(--bone2);position:relative}
.bar>b{display:block;height:100%;border-radius:7px;background:var(--ink)}
.bar>u{position:absolute;top:0;bottom:0;width:3px;background:#b0632f}
.wash{position:absolute;inset:0;background:rgba(28,26,23,.55)}
.lab{font-size:17px;color:var(--ink2)}
.price{display:inline-flex;align-items:center;gap:8px;padding:0 16px;height:46px;border-radius:12px;background:var(--ink);color:var(--bone);font-size:22px;box-shadow:0 4px 0 #000}
.price.no{background:var(--bone2);color:#8f897e;box-shadow:0 4px 0 var(--lip)}
.w{color:#fff;text-shadow:0 2px 0 rgba(0,0,0,.4),0 0 18px rgba(0,0,0,.5)}
.wd{color:rgba(255,255,255,.8)}
.shade{position:absolute;inset:0;background:radial-gradient(60% 60% at 0% 100%,rgba(10,10,12,.62),rgba(10,10,12,0) 72%),radial-gradient(60% 55% at 100% 100%,rgba(10,10,12,.5),rgba(10,10,12,0) 70%),radial-gradient(45% 40% at 100% 0%,rgba(10,10,12,.42),rgba(10,10,12,0) 70%),radial-gradient(40% 35% at 0% 0%,rgba(10,10,12,.4),rgba(10,10,12,0) 70%)}
.tk{filter:drop-shadow(0 0 1px #5d584f) drop-shadow(0 0 1px #5d584f)}
.slit{-webkit-mask-image:linear-gradient(180deg,#000 0,#000 53%,transparent 53%,transparent 59%,#000 59%)}
.key{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:9px;font-size:19px;background:var(--bone2);color:var(--ink);box-shadow:inset 0 2px 0 rgba(0,0,0,.12)}
"""


def wallet(top=56, right=64):
    return f"""<div class="abs flexc w" style="right:{right}px;top:{top}px;gap:12px;font-size:30px">{cur('coin', 36)}{WALLET['coins']}<span style="width:18px"></span>{cur('ticket', 44)}{WALLET['tickets']}</div>"""


def price(p, curr="coin", size=24):
    ok = afford(p) if curr == "coin" else True
    return f'<span class="price {"" if ok else "no"}">{rbx() if curr == "robux" else cur("coin", size)}{p}</span>'


def esc(label):
    """Leave a screen: plain words with the key that does it."""
    return f'<div class="abs flexc w" style="right:64px;top:70px;gap:12px;font-size:24px">{label}<span class="key" style="width:auto;padding:0 8px;font-size:15px">ESC</span></div>'


def set_column(w=360):
    """The five Seraph skins stacked down a tall card at their true relative sizes."""
    parts = [("seraph_sniper", 360, 0), ("seraph_rifle", 320, 100), ("seraph_burst", 290, 240), ("seraph_katana", 360, 360), ("seraph_pistol", 120, 470)]
    return "".join(f'<img src="../img/items/{i}.png" style="position:absolute;left:{(w - wd) // 2}px;top:{t}px;width:{wd}px;filter:drop-shadow(0 10px 10px rgba(0,0,0,.45))">' for i, wd, t in parts)


def hub():
    xp = PLAYER['xp'] / PLAYER['xp_next']
    links = [("QUESTS", f"{QUESTS_DONE[0]}/{QUESTS_DONE[1]}"), ("PARTY", PARTY_N), ("LOADOUT", ""), ("SHOP", ""), ("CHANGE HUB", ""), ("PROFILE", ""), ("SETTINGS", "")]
    menu = "".join(f'<div class="flexc w" style="height:{54 if i < 4 else 42}px;font-size:{30 if i < 4 else 21}px;gap:14px;{"margin-top:14px" if i == 4 else ""}">{t}<span class="wd" style="font-size:22px">{c}</span></div>' for i, (t, c) in enumerate(links))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_spawn.jpg)"></div><div class="shade"></div>
<div class="abs flexc w" style="left:60px;top:52px;gap:18px">{head(0, 60)}<div><div style="font-size:30px">{PLAYER['name']}</div>
 <div class="flexc" style="gap:12px;margin-top:6px"><span style="font-size:20px">LV {PLAYER['level']}</span><div style="width:200px;height:8px;border-radius:4px;background:rgba(255,255,255,.3)"><div style="width:{xp*100:.0f}%;height:100%;border-radius:4px;background:#fff"></div></div><span class="wd" style="font-size:16px">{PLAYER['xp']:,} / {PLAYER['xp_next']:,} XP</span></div></div></div>
{wallet()}
<div class="pad" style="left:56px;top:316px;width:500px;height:172px">
 <div class="slit" style="position:absolute;left:38px;top:26px;font-size:96px;line-height:1">PLAY</div>
 <div style="position:absolute;left:41px;bottom:30px;font-size:22px;color:#b9b2a5">{MODE_LABEL} <span class="bm" style="margin-left:10px;font-size:18px">rating {RATING}</span></div>
 <div class="plate" style="right:24px;top:54px;height:60px;padding:0 20px;display:flex;align-items:center;font-size:18px;border-radius:12px;color:var(--ink)">CHANGE MODE</div>
</div>
<div class="abs" style="left:62px;top:516px">{menu}</div>
<div class="abs w" style="left:62px;bottom:46px;font-size:22px">{HUB['name']} <span class="wd bm" style="margin-left:10px">{HUB['here']} here</span></div>
</div>"""
    return page("A hub", CSS, body)


def match():
    m = MATCH
    feed = "".join(f'<div class="flexc" style="width:max-content;margin-left:auto;gap:12px;height:40px;margin-bottom:6px;padding:0 16px;border-radius:3px;background:rgba(20,20,24,.62);color:#fff;font-size:21px;{"box-shadow:inset 0 0 0 2px var(--bone)" if f[0] == PLAYER["name"] else ""}">{feed_line(*f)}</div>' for f in FEED)
    slots = ""
    for i, (k, g, n) in enumerate(SLOTS + [("G", None, "")]):
        on = i == 0
        inner = slot_icon(g, 66, 30) if g else f'<span style="font-size:30px;line-height:0">{icon("grenade")}</span><span style="font-size:20px;margin-left:4px">×{m["util_n"]}</span>'
        slots += f'<div class="w" style="text-align:center;width:98px;opacity:{1 if on else .66}"><div class="flexc" style="height:36px;justify-content:center;filter:drop-shadow(0 2px 0 rgba(0,0,0,.4))">{inner}</div><div style="font-size:16px;margin-top:4px">{k}</div><div style="height:6px;margin-top:4px;border-radius:3px;background:{"var(--bone)" if on else "transparent"}"></div></div>'
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_crate.jpg)"></div><div class="shade"></div>
<div class="abs" style="left:50%;transform:translateX(-50%);top:24px;display:flex;flex-direction:column;align-items:center">
 <div class="flexc" style="gap:10px">
  <div class="flexc" style="height:88px;padding:0 20px 0 26px;gap:16px;border-radius:20px;background:{TEAM['blossom'][0]};box-shadow:inset 0 0 0 6px var(--bone),0 5px 0 var(--lip),0 12px 24px rgba(0,0,0,.3)"><span class="slit" style="font-size:58px;line-height:1">{m['us']}</span>{heads_col('blossom', 28, 4)}</div>
  <div class="flexc" style="height:88px;padding:0 26px 0 20px;gap:16px;border-radius:20px;background:{TEAM['sky'][0]};box-shadow:inset 0 0 0 6px var(--bone),0 5px 0 var(--lip),0 12px 24px rgba(0,0,0,.3)">{heads_col('sky', 28, 4)}<span class="slit" style="font-size:58px;line-height:1">{m['them']}</span></div>
 </div>
 <div class="flexc" style="margin-top:10px;height:36px;padding:0 16px;gap:12px;background:rgba(29,31,35,.82);color:var(--bone);border-radius:3px;font-size:24px"><span style="font-size:15px;color:#b9b2a5">ROUND {m['round']}</span>{m['time']}</div>
</div>
<div class="abs" style="right:60px;top:40px">{feed}</div>
<div class="abs w" style="left:62px;bottom:50px">
 <div class="flexc" style="gap:10px;margin-bottom:16px"><span class="key" style="text-shadow:none">E</span><span style="filter:drop-shadow(0 2px 0 rgba(0,0,0,.4))">{grapple_readout('#fff', 36)}</span></div>
 <div class="slit" style="font-size:88px;line-height:1">{m['hp']}</div>
 <div style="width:300px;height:16px;margin-top:10px;border-radius:8px;background:rgba(255,255,255,.28)"><div style="width:{m['hp']}%;height:100%;border-radius:8px;background:var(--bone)"></div></div>
</div>
<div class="abs" style="right:60px;bottom:50px;text-align:right">
 <div class="flexc" style="gap:6px;justify-content:flex-end;margin-bottom:20px">{slots}</div>
 <div class="w" style="font-size:88px;line-height:1"><span class="slit">{m['ammo']}</span><span style="font-size:38px;opacity:.72"> /{m['mag']}</span></div>
</div>
<svg class="abs" style="left:942px;top:522px" width="36" height="36" viewBox="0 0 36 36"><g stroke="#1d1f23" stroke-width="7" stroke-linecap="round"><path d="M18 3v8M18 25v8M3 18h8M25 18h8"/></g><g stroke="#efe9de" stroke-width="3.4" stroke-linecap="round"><path d="M18 3v8M18 25v8M3 18h8M25 18h8"/></g></svg>
</div>"""
    return page("A match", CSS, body)


def loadout():
    slots = ""
    pics = {"PRIMARY": slot_icon("ar", 120, 44), "SECONDARY": slot_icon("revolver", 90, 46), "MELEE": slot_icon("katana", 120, 40), "UTILITY": f'<span style="font-size:48px;line-height:0">{icon("grenade")}</span>'}
    y = 176
    for i, (slot, g, name, note) in enumerate(LOADOUT):
        on = i == SEL
        h = 132 if on else 92
        sub = {"SECONDARY": "Wish Duck skin", "UTILITY": "×2"}.get(slot, "")
        slots += f"""<div class="flat" style="left:64px;top:{y}px;width:480px;height:{h}px;{"background:var(--ink);color:var(--bone)" if on else ""}">
 <span class="key" style="position:absolute;left:22px;top:{h/2-17:.0f}px;{"background:#3a3d44;color:var(--bone);box-shadow:none" if on else ""}">{["1","2","3","G"][i]}</span>
 <div style="position:absolute;left:76px;top:{h/2-(26 if sub else 17):.0f}px;font-size:{32 if on else 28}px">{name.upper()}</div>
 {f'<div class="bm" style="position:absolute;left:76px;top:{h/2+12:.0f}px;font-size:18px;color:{"#b9b2a5" if on else "var(--ink2)"}">{sub}</div>' if sub else ''}
 <div style="position:absolute;right:18px;top:{(h-74)/2:.0f}px;width:150px;height:74px;display:grid;place-items:center">{pics[slot]}</div></div>"""
        y += h + 14
    stats = "".join(f"""<div style="margin-top:20px"><div class="flexc" style="justify-content:space-between"><span class="lab">{k.upper()}</span><span style="font-size:26px">{v}</span></div>
 <div class="bar" style="margin-top:8px"><b style="width:{f*100:.0f}%"></b><u style="left:{avg*100:.0f}%"></u></div></div>""" for (k, v, f), avg in zip(STATS, STAT_AVG))
    rail = ""
    x = 64
    for g, n, st in ARMORY:
        on = st == "on"
        locked = isinstance(st, tuple)
        w = 432 if on else 328
        if locked and st[0] == "coins":
            tag = f'<span class="bm flexc" style="font-size:16px;color:var(--ink2);gap:5px">{cur("coin", 17)}{st[1]}</span><span class="bm" style="font-size:15px;color:#a35a2a">need {int(st[1].replace(",", "")) - WALLET_N:,} more</span>'
        elif locked:
            tag = f'<span class="bm flexc" style="font-size:16px;color:var(--ink2);gap:5px">{icon("lock")} Level {st[1]}</span>'
        else:
            tag = '<span class="bm" style="font-size:17px;color:#b9b2a5">Equipped</span>' if on else ""
        pic = '<img class="ap" src="../img/items/wish_duck_34.png">' if on else gunpic(g, "ap")
        rail += f"""<div class="flat" style="left:{x}px;bottom:44px;width:{w}px;height:136px;{"background:var(--ink);color:var(--bone);" if on else ""}">
 <div style="position:absolute;left:16px;top:14px;width:{180 if on else 150}px;height:{90 if on else 70}px;display:grid;place-items:center;{"filter:grayscale(1) brightness(.85);opacity:.8" if locked else ""}">{pic}</div>
 <div style="position:absolute;left:{216 if on else 172}px;top:{34 if on else 22}px;font-size:{22 if on else 18}px;width:{w-(230 if on else 184)}px;line-height:1.15">{n.upper()}<div style="margin-top:6px">{tag}</div></div></div>"""
        x += w + 12
        if x > 1800:
            break
    cos = (f"""<div class="flexc" style="gap:14px;margin-top:18px;height:40px"><span class="lab" style="width:48px">SKIN</span><div style="font-size:20px">WISH DUCK</div><span class="bm dim" style="margin-left:auto;font-size:17px">4 owned</span></div>"""
           f"""<div class="flexc" style="gap:14px;margin-top:8px"><span class="lab" style="width:48px">HAT</span>
 <div style="position:relative;width:90px;height:56px;border-radius:3px;background:var(--bone2)"><img src="../img/items/royal-duck.png" style="position:absolute;left:18px;top:4px;max-width:56px;max-height:48px"></div>
 <div style="font-size:20px">ROYAL DUCK</div></div>""")
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_rotunda_blur.jpg)"></div><div class="wash"></div>
<style>.gp{{max-width:150px;max-height:72px}} .ap{{max-width:100%;max-height:100%}} .ic{{width:1em;height:1em}}</style>
<div class="abs w" style="left:64px;top:62px;font-size:52px">LOADOUT</div>
{esc("DONE")}
{slots}
{hatted(660, style="left:620px;top:214px")}
<div class="flat" style="left:1360px;top:176px;width:496px;padding:28px 28px 24px">
 <div class="flexc" style="justify-content:space-between"><span style="font-size:30px">MASTERY {MASTERY['level']}</span><span class="bm dim" style="font-size:17px">{MASTERY['xp']} / {MASTERY['next']} XP</span></div>
 <div class="bar" style="margin-top:8px;height:10px"><b style="width:{MASTERY['frac']*100:.0f}%"></b></div>
 {stats}
 <div class="flexc bm dim" style="font-size:16px;margin-top:10px;gap:8px"><i style="width:3px;height:14px;background:#b0632f"></i>Secondary average</div>
 <div style="height:2px;background:var(--bone2);margin-top:16px"></div>
 {cos}
</div>
<div class="abs w" style="left:64px;bottom:196px;font-size:24px">SECONDARIES</div>
{rail}
</div>"""
    return page("A loadout", CSS, body)


def shop():
    tabs = "".join(f'<div class="w flexc" style="position:relative;height:52px;padding:0 16px;font-size:22px;{"" if i == 0 else "opacity:.62"}">{t}{"<i style=&quot;position:absolute;left:16px;right:16px;bottom:2px;height:5px;border-radius:3px;background:var(--bone)&quot;></i>" if i == 0 else ""}</div>' for i, t in enumerate(SHOP_TABS))
    first = DAILY[0]
    daily = f"""<div class="flat" style="left:500px;top:178px;width:640px;height:330px">
 <img src="../img/items/{first[0]}.png" style="position:absolute;left:270px;top:-30px;max-width:340px;max-height:250px;filter:drop-shadow(0 10px 10px rgba(0,0,0,.25))">
 <div style="position:absolute;left:28px;top:236px;font-size:30px">{first[1].upper()}</div>
 <div class="bm dim" style="position:absolute;left:28px;top:274px;font-size:18px">{first[5].title()} {first[2].lower()}</div>
 <div style="position:absolute;right:24px;bottom:24px;text-align:right">{price(first[3], first[4])}<div class="bm" style="font-size:15px;color:#a35a2a;margin-top:10px">need {int(first[3].replace(",", "")) - WALLET_N:,} more</div></div></div>
<div class="flat" style="left:500px;top:524px;width:640px;height:504px">"""
    for i, (img, name, kind, p, curr, rar) in enumerate(DAILY[1:]):
        daily += f"""<div class="flexc" style="height:168px;padding:0 24px;gap:22px;border-top:{"none" if i == 0 else "2px solid var(--bone2)"}">
 <div style="width:230px;display:grid;place-items:center"><img src="../img/items/{img}.png" style="max-width:230px;max-height:120px;filter:drop-shadow(0 6px 6px rgba(0,0,0,.22))"></div>
 <div style="flex:1"><div style="font-size:23px">{name.upper()}</div><div class="bm dim" style="font-size:17px">{rar.title()} {kind.lower()}</div></div>
 <div style="text-align:right">{price(p, curr, 22)}{"" if afford(p) else f'<div class="bm" style="font-size:14px;color:#a35a2a;margin-top:8px">need {int(p.replace(",", "")) - WALLET_N:,} more</div>'}</div></div>"""
    daily += "</div>"
    crates = "".join(f"""<div class="flexc" style="height:112px;padding:0 16px;border-top:{"none" if i == 0 else "2px solid var(--bone2)"};gap:16px">
 <div style="width:110px;display:grid;place-items:center"><img src="../img/items/{img}.png" style="max-width:104px;max-height:76px"></div>
 <div style="flex:1"><div style="font-size:23px">{name.upper()}</div><div class="bm dim" style="font-size:17px">{holds}</div></div>
 <span class="price" style="width:92px;justify-content:center">{cur('ticket', 28)}{tk}</span><span class="bm dim" style="font-size:16px">or</span><span class="price" style="width:104px;justify-content:center">{rbx()}{rp}</span></div>""" for i, (img, name, holds, tk, rp) in enumerate(CONTAINERS))
    packs = "".join(f"""<div class="flexc" style="height:112px;padding:0 16px;border-top:{"none" if i == 0 else "2px solid var(--bone2)"};gap:18px">
 <span style="width:64px;display:flex;justify-content:center">{coin_stack(i + 1, 34)}</span><div style="flex:1"><div style="font-size:28px">{c}</div><div class="bm dim" style="font-size:17px">{("+" + b) if b else ""}</div></div>
 <span class="price" style="width:132px;justify-content:center">{rbx()}{r}</span></div>""" for i, (c, r, b) in enumerate(COIN_PACKS))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_rotunda_blur.jpg)"></div><div class="wash"></div>
<div class="abs w" style="left:64px;top:60px;font-size:50px">SHOP</div>
<div class="abs flexc" style="left:236px;top:62px;gap:8px">{tabs}</div>
<div class="abs flexc w" style="left:500px;top:150px;gap:14px;font-size:20px">DAILY<span class="wd bm" style="font-size:17px">New in {DAILY_RESET}</span></div>
{wallet(70, 250)}
{esc("CLOSE")}
<div class="flat ink" style="left:64px;top:178px;width:420px;height:850px">
 <div class="slit" style="position:absolute;left:30px;top:28px;font-size:84px;line-height:1">{HERO['name']}</div>
 <div class="bm" style="position:absolute;left:32px;top:118px;font-size:20px;color:#b9b2a5">{len(HERO['set'])} skins</div>
 <div style="position:absolute;left:30px;top:170px;width:360px;height:560px">{set_column(360)}</div>
 <div style="position:absolute;left:30px;bottom:30px"><span class="price" style="height:70px;font-size:32px;padding:0 30px;border-radius:16px;background:var(--bone);color:var(--ink);box-shadow:0 5px 0 var(--lip)">{rbx()}{HERO['price']}</span></div>
</div>
{daily}
<div class="abs w" style="left:1170px;top:150px;font-size:20px">CRATES</div>
<div class="flat" style="left:1170px;top:178px;width:686px;height:336px">{crates}</div>
<div class="abs w" style="left:1170px;top:540px;font-size:20px">COINS</div>
<div class="flat" style="left:1170px;top:568px;width:686px;height:460px;padding-top:6px">{packs}</div>
</div>"""
    return page("A shop", CSS, body)


def phone():
    m = MATCH
    keys = ""
    for k, x, y, s in arc(752, 212, 134, 92, 260):
        extra = f'<span style="position:absolute;left:0;right:0;bottom:3px;text-align:center;font-size:11px">×{GRAPPLE["charges"]}</span>' if k == "hook" else ""
        extra = f'<span style="position:absolute;left:0;right:0;bottom:3px;text-align:center;font-size:11px">×{m["util_n"]}</span>' if k == "grenade" else extra
        lip = "0 3px 0 var(--lip),0 6px 12px rgba(0,0,0,.28)" if k == "jump" else "0 6px 12px rgba(0,0,0,.22)"
        keys += f'<div class="plate" style="left:{x - s/2:.0f}px;top:{y - s/2:.0f}px;width:{s}px;height:{s}px;border-radius:50%;box-shadow:{lip};{"" if k == "jump" else "background:rgba(239,233,222,.9);"}display:grid;place-items:center;color:var(--ink)"><span style="margin-top:{-6 if extra else 0}px">{act_icon(k, int(s*0.46))}</span>{extra}</div>'
    slots = "".join(f'<div class="plate {"ink" if i == 0 else ""}" style="position:relative;width:60px;height:34px;border-radius:10px;display:grid;place-items:center;box-shadow:0 3px 0 {"#000" if i == 0 else "var(--lip)"}">{slot_icon(g, 42, 19)}</div>' for i, (k, g, n) in enumerate(SLOTS))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_crate.jpg)"></div><div class="shade"></div>
<div class="abs" style="left:50%;transform:translateX(-50%);top:8px;display:flex;flex-direction:column;align-items:center">
 <div class="flexc" style="border-radius:3px;overflow:hidden;box-shadow:0 6px 14px rgba(0,0,0,.3)">
  <div class="flexc" style="height:40px;padding:0 8px 0 12px;gap:7px;background:{TEAM['blossom'][0]}"><span style="font-size:28px;line-height:1">{m['us']}</span>{heads_col('blossom', 14, 2)}</div>
  <div class="flexc" style="height:40px;padding:0 12px 0 8px;gap:7px;background:{TEAM['sky'][0]}">{heads_col('sky', 14, 2)}<span style="font-size:28px;line-height:1">{m['them']}</span></div>
 </div>
 <div class="flexc" style="height:20px;padding:0 8px;gap:6px;background:var(--ink);color:var(--bone);font-size:13px"><span style="font-size:9px;color:#b9b2a5">ROUND {m['round']}</span>{m['time']}</div>
 {scores_tab('rgba(229,226,219,.94)', 'var(--ink)', 10, '0 0 5px 5px', 'text-transform:uppercase;letter-spacing:.05em')}
</div>
<div class="abs" style="left:58px;top:124px;width:124px;height:124px;border-radius:50%;background:rgba(29,31,35,.32);box-shadow:inset 0 0 0 4px rgba(239,233,222,.8)"></div>
<div class="plate" style="left:92px;top:158px;width:56px;height:56px;border-radius:50%"></div>
<div class="abs flexc" style="left:200px;bottom:14px;gap:16px;align-items:flex-end">
 <div class="w"><div style="font-size:40px;line-height:1">{m['hp']}</div><div style="width:100px;height:8px;margin-top:6px;border-radius:4px;background:rgba(255,255,255,.3)"><div style="width:{m['hp']}%;height:100%;border-radius:4px;background:var(--bone)"></div></div></div>
 <div class="w" style="font-size:40px;line-height:1;padding-bottom:14px">{m['ammo']}<span style="font-size:19px;opacity:.8"> /{m['mag']}</span></div>
 <div class="flexc" style="gap:6px;padding-bottom:14px">{slots}</div>
</div>
{keys}
<div class="pad" style="left:704px;top:160px;width:104px;height:104px;border-radius:50%;display:grid;place-items:center;box-shadow:inset 0 0 0 4px var(--bone),0 4px 0 var(--lip),0 8px 16px rgba(0,0,0,.35)">{fire_icon(34)}</div>
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
            style = "background:var(--ink);color:var(--bone);border-radius:10px" if me else ""
            party = ""
            br = party_mark(108, "var(--ink2)", "var(--ink2)", -30) if nm in PARTY and me else ""
            rows += f"""<div class="flexc" style="position:relative;height:58px;margin:4px 0;padding:0 20px 0 14px;{style};{"" if alive else "color:#a49d90"}">{br}
 <span style="position:relative;margin-right:22px;{"" if alive else "filter:grayscale(1);opacity:.6"}">{head(n, 44)}{"" if alive else dead_x(44)}</span>
 <span style="flex:1;font-size:23px">{nm}<span style="font-size:15px;opacity:.6;margin-left:8px">LV {LEVELS[nm]}</span>{party}</span>
 {"".join(f'<span style="width:{w}px;text-align:right;font-size:23px">{v}</span>' for v, w in [(k, 56), (de, 56), (a, 56), (dmg, 96), (ping, 80)])}</div>"""
            n += 1
        blocks += f"""<div style="margin-top:14px"><div class="flexc" style="gap:14px;height:38px;padding-left:16px"><span style="font-size:22px;color:{d}">{team.upper()}</span><span class="lab">{sum(p[1] for p in players)} KILLS</span></div>{rows}</div>"""
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_forest_blur.jpg)"></div><div class="wash" style="background:rgba(20,19,17,.4)"></div>
<div class="flat" style="left:500px;top:96px;width:920px;padding:24px 26px 22px 64px">
 <div class="flexc" style="height:96px;gap:22px">
  <div class="sp" style="width:112px;height:84px;background:{TEAM['blossom'][0]};font-size:60px"><span class="slit">{bd['us']}</span></div>
  <div style="flex:1;text-align:center"><div style="font-size:34px">{bd['map'].upper()}</div><div class="bm dim" style="margin-top:4px;font-size:19px">Round {bd['round']}, <b style="color:var(--ink)">{bd['time']}</b> left</div></div>
  <div class="sp" style="width:112px;height:84px;background:{TEAM['sky'][0]};font-size:60px"><span class="slit">{bd['them']}</span></div>
 </div>
 <div style="height:3px;background:var(--bone2);margin:14px 0 4px;border-radius:2px"></div>
 {head_row}{blocks}
</div>
</div>"""
    return page("A scoreboard", CSS, body)


FRAMES = {"hub": hub, "match": match, "loadout": loadout, "shop": shop, "phone": phone, "scoreboard": scoreboard}
