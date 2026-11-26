"""Direction B: BROADCAST. Your match as a TV sports graphic: hard square black slabs, condensed
Oswald caps for headings and big numbers, Builder Sans in sentence case for everything small. The
JANKFIRE "channel bug" (a skewed Butter tab) sits on the hub ticker and the Tab board like a TV
station's mark. One cut corner marks what you can press (PLAY, DONE, prices). Black and white;
the team pastels are the only colour in a match, and Butter is the one thing to press."""
from common import *

NAME = "B  BROADCAST"
CSS = """
:root{--k:rgba(10,11,13,.92);--k2:#1c1e22;--w:#f4f3ef;--g:#a2a6ac;--g2:#4a4e54;--y:#f5dd8a;--rule:#2e3136}
body{font-family:'Oswald';font-weight:700;color:var(--w);text-transform:uppercase;font-variant-numeric:tabular-nums}
.slab{position:absolute;background:var(--k)}
.slab.w{background:var(--w);color:#0b0c0e}
.slab.y{background:var(--y);color:#0b0c0e}
.cut{clip-path:polygon(var(--c,16px) 0,100% 0,100% 100%,0 100%,0 var(--c,16px))}
.you{clip-path:polygon(0 0,calc(100% - 18px) 0,100% 18px,100% 100%,0 100%)}
.sk{transform:skewX(-12deg)}.sk>.un{transform:skewX(12deg)}
.k2{background:rgba(30,33,38,.94)}
.lbl{font-family:'Builder Sans';font-weight:800;letter-spacing:.02em}
.tab{position:absolute;height:30px;padding:0 12px;display:flex;align-items:center;background:var(--w);color:#0b0c0e;font-size:17px;letter-spacing:.06em}
.bug{display:inline-flex;align-items:center;height:100%;padding:0 26px 0 22px;background:var(--y);color:#0b0c0e;transform:skewX(-14deg);letter-spacing:.06em}
.bug>span{transform:skewX(14deg)}
.bs{font-family:'Builder Sans';font-weight:700;text-transform:none;letter-spacing:0}
.g{color:var(--g)}
.flexc{display:flex;align-items:center}
.hb{position:absolute;left:0;right:0;bottom:0;height:8px;background:var(--rule)}
.hb>b{display:block;height:100%;background:var(--w)}
.bar{height:8px;background:var(--rule)}.bar>b{display:block;height:100%;background:var(--w)}
.scrim{position:absolute;inset:0;background:rgba(8,9,11,.66)}
"""


def _wallet():
    return f"""<div class="slab flexc" style="right:64px;top:56px;height:64px;padding:0 24px 0 22px;gap:12px;font-size:34px">
 {cur('coin', 34)}{WALLET['coins']}<span style="width:2px;height:34px;background:var(--rule);margin:0 8px"></span>{cur('ticket', 42)}{WALLET['tickets']}</div>"""


def hub():
    info = {"quests": f"{QUESTS_DONE[0]}/{QUESTS_DONE[1]}", "party": PARTY_N}
    items = "".join(
        f'<div class="flexc lbl" style="height:72px;padding:0 28px;gap:10px;border-left:{"none" if i == 0 else "2px solid var(--rule)"}"><span style="font-size:24px">{"CHANGE HUB" if mid == "hubs" else label}</span>'
        f'<span class="bs g" style="font-size:21px">{info.get(mid, "")}</span></div>' for i, (mid, label, key) in enumerate([x for x in MENU[1:] if x[0] not in ("profile",)]))
    xp = PLAYER['xp'] / PLAYER['xp_next']
    tick = "".join(f'<span style="margin-right:34px">{m} <span class="bs g" style="font-size:20px">{q}</span></span>' for m, q in QUEUES)
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_spawn.jpg)"></div>
<div class="slab flexc" style="left:64px;top:56px;width:640px;height:64px;padding:0 10px 0 22px;gap:16px"><div style="flex:1"><div class="flexc" style="gap:14px"><span class="bs" style="font-size:28px">{PLAYER['name']}</span><span style="font-size:22px">LV {PLAYER['level']}</span><span class="bs g" style="font-size:16px;margin-left:auto">{PLAYER['xp']:,} / {PLAYER['xp_next']:,} XP</span></div></div>
 <div class="flexc lbl" style="gap:6px;font-size:16px;align-self:center"><div class="flexc" style="height:42px;padding:0 14px;background:var(--k2)">PROFILE</div><div class="flexc" style="height:42px;padding:0 14px;background:var(--k2)">SETTINGS</div></div>
 <div class="hb" style="height:5px"><b style="width:{xp*100:.0f}%"></b></div>
</div>
{_wallet()}
<div class="slab y sk" style="left:74px;bottom:76px;width:320px;height:168px">
 <div class="un" style="position:absolute;left:30px;top:-2px;font-size:104px;line-height:1.2;letter-spacing:.01em">PLAY</div>
 <div class="un" style="position:absolute;left:24px;bottom:14px;font-size:24px;font-weight:400;letter-spacing:.06em">{MODE_LABEL} <span class="bs" style="font-size:17px;margin-left:6px">rating {RATING}</span></div>
</div>
<div class="slab k2 flexc" style="left:394px;bottom:76px;height:72px;padding-left:34px;clip-path:polygon(15px 0,100% 0,100% 100%,0 100%)">{items}</div>
<div class="slab flexc" style="left:0;right:0;bottom:0;height:52px;font-size:22px;letter-spacing:.04em">
 <div class="flexc" style="height:52px;padding:0 22px 0 64px;margin-right:30px;background:var(--w);color:#0b0c0e">{HUB['name']}</div>
 {tick}
 <span style="margin-left:auto;margin-right:64px">{HUB['here']} <span class="lbl g" style="font-size:17px">PLAYERS</span></span>
</div>
</div>"""
    return page("B hub", CSS, body)


def match():
    m = MATCH
    def box(team, score):
        return f'<div style="width:128px;height:92px;background:{TEAM[team][0]};color:#0b0c0e;display:grid;place-items:center;font-size:80px;line-height:1">{score}</div>'
    def strip(team):
        return f'<div class="flexc" style="width:128px;height:28px;background:#0b0c0e;justify-content:center;font-size:16px;letter-spacing:.1em">{team.upper()}</div>'
    feed = "".join(f"""<div class="slab flexc bs {"you" if f[0] == PLAYER["name"] else ""}" style="right:64px;top:{56 + i*50}px;height:42px;padding:0 24px 0 18px;gap:12px;font-size:21px;{"background:rgba(60,64,71,.95)" if f[0] == PLAYER["name"] else ""}">{feed_line(*f)}</div>""" for i, f in enumerate(FEED))
    slots = ""
    hot = SLOTS + [("G", None, "")] + [("E", "hook", "")]
    for i, (k, g, n) in enumerate(hot):
        on = i == 0
        if g == "hook":
            inner = f'<span style="font-size:30px;line-height:0">{icon("hook")}</span><span style="font-size:22px;margin-left:6px">×{GRAPPLE["charges"]}</span>'
        elif g:
            inner = slot_icon(g, 62, 28)
        else:
            inner = f'<span style="font-size:28px;line-height:0">{icon("grenade")}</span><span style="font-size:22px;margin-left:6px">×{m["util_n"]}</span>'
        slots += f'<div class="slab flexc {"w sk" if on else ""}" style="right:{64 + (len(hot) - 1 - i)*112}px;bottom:176px;width:106px;height:58px;justify-content:center"><span class="{"un" if on else ""}" style="position:absolute;left:10px;top:2px;font-size:17px;opacity:.7">{k}</span><span class="{"un" if on else ""}">{inner}</span></div>'
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_crate.jpg)"></div>
<div class="abs flexc" style="left:50%;transform:translateX(-50%);top:24px;height:76px;background:var(--k)">
 <div class="flexc lbl" style="height:76px;padding:0 16px;background:var(--w);color:#0b0c0e;font-size:17px;line-height:1.05;text-align:center">ROUND<br>{m['round']}</div>
 <div class="flexc" style="height:76px;padding:0 14px 0 22px;gap:14px;background:{TEAM['blossom'][0]};color:#0b0c0e"><span style="font-size:64px;line-height:1">{m['us']}</span>{heads_col('blossom', 30, 4)}</div>
 <div class="flexc" style="height:76px;padding:0 22px 0 14px;gap:14px;background:{TEAM['sky'][0]};color:#0b0c0e">{heads_col('sky', 30, 4)}<span style="font-size:64px;line-height:1">{m['them']}</span></div>
 <div style="padding:0 22px;font-size:44px">{m['time']}</div>
</div>
{feed}
<div class="abs" style="left:64px;bottom:52px;text-shadow:0 2px 10px rgba(0,0,0,.45)">
 <div style="font-size:104px;line-height:1">{m['hp']}</div>
 <div style="width:220px;height:8px;margin-top:8px;background:rgba(244,243,239,.3)"><div style="width:{m['hp']}%;height:100%;background:var(--w)"></div></div>
</div>
<div class="abs" style="right:64px;bottom:52px;text-align:right;text-shadow:0 2px 10px rgba(0,0,0,.45)">
 <div style="font-size:104px;line-height:1">{m['ammo']}<span class="g" style="font-size:44px;font-weight:400;color:#d7d9dc"> /{m['mag']}</span></div>
 <div style="width:220px;height:8px;margin-top:8px;margin-left:auto;background:rgba(244,243,239,.3)"><div style="width:{m['ammo']/m['mag']*100:.0f}%;height:100%;background:var(--w);margin-left:auto"></div></div>
</div>
{slots}
<svg class="abs" style="left:942px;top:522px" width="36" height="36" viewBox="0 0 36 36"><g stroke="#0b0c0e" stroke-width="6" stroke-linecap="square"><path d="M18 4v8M18 24v8M4 18h8M24 18h8"/></g><g stroke="#f4f3ef" stroke-width="3" stroke-linecap="square"><path d="M18 4v8M18 24v8M4 18h8M24 18h8"/></g></svg>
</div>"""
    return page("B match", CSS, body)


def loadout():
    rows = ""
    pics = {"PRIMARY": gunpic("ar", "rimg"), "SECONDARY": slot_icon("revolver", 84, 44), "MELEE": gunpic("katana", "rimg"), "UTILITY": '<img class="rimg" src="../img/items/frag.png" style="max-height:74px">'}
    for i, (slot, g, name, note) in enumerate(LOADOUT):
        on = i == SEL
        k = ["1", "2", "3", "G"][i]
        sub = {"UTILITY": "×2"}.get(slot, "")
        rows += f"""<div class="slab {"w you" if on else ""}" style="left:64px;top:{218 + i*102}px;width:560px;height:94px">
 <div style="position:absolute;left:24px;top:24px;font-size:30px;font-weight:400;{"color:#8d9197" if on else "color:var(--g2)"}">{k}</div>
 <div style="position:absolute;left:66px;top:{10 if sub else 18}px;font-size:42px;line-height:1.25">{name}</div>
 {f'<div class="bs" style="position:absolute;left:68px;top:62px;font-size:19px;{"color:#55595f" if on else "color:var(--g)"}">{sub}</div>' if sub else ''}
 <div style="position:absolute;right:16px;top:10px;width:150px;height:74px;display:grid;place-items:center">{pics[slot]}</div></div>"""
    stats = "".join(f"""<div style="margin-top:22px"><div class="flexc" style="justify-content:space-between"><span class="bs g" style="font-size:21px">{k}</span><span style="font-size:40px;line-height:1.1;text-transform:none">{v}</span></div>
 <div class="bar" style="margin-top:6px;position:relative"><b style="width:{f*100:.0f}%"></b><i style="position:absolute;top:-4px;bottom:-4px;left:{avg*100:.0f}%;width:3px;background:var(--y)"></i></div></div>""" for (k, v, f), avg in zip(STATS, STAT_AVG))
    arm = ""
    x = 64
    for i, (g, n, st) in enumerate(ARMORY):
        on = st == "on"
        locked = isinstance(st, tuple)
        w = 440 if on else 326
        tag = ("" if not locked else (f'<span class="bs g flexc" style="font-size:19px;gap:6px">{icon("lock")}Level {st[1]}</span>' if st[0] == "level"
                                      else f'<span class="flexc g" style="font-size:21px;gap:6px;justify-content:flex-end">{cur("coin", 22)}{st[1]}</span><span class="bs" style="font-size:16px;color:#e0a070;display:block;text-align:right">need {int(st[1].replace(",", "")) - WALLET_N:,} more</span>'))
        pic = '<img class="aimg" src="../img/items/wish_duck_34.png">' if on else gunpic(g, "aimg")
        arm += f"""<div class="slab {"w you" if on else ""}" style="left:{x}px;bottom:44px;width:{w}px;height:150px">
 <div style="position:absolute;left:16px;top:14px;width:200px;height:84px;display:grid;place-items:center;{"filter:grayscale(1);opacity:.5" if locked else ""}">{pic}</div>
 <div style="position:absolute;left:18px;top:104px;font-size:26px">{n}</div>
 <div style="position:absolute;right:16px;top:20px">{tag}{'<span class="bs" style="font-size:17px;color:#55595f">Equipped</span>' if on else ''}</div></div>"""
        x += w + 12
    cos = f"""<div class="slab" style="left:64px;top:634px;width:560px;height:130px">
 <div class="flexc" style="height:64px;padding:0 20px;gap:16px;border-bottom:2px solid var(--rule)"><span class="bs g" style="width:44px;font-size:18px">Skin</span><span style="font-size:28px">WISH DUCK</span><span class="bs g" style="margin-left:auto;font-size:18px">4 owned</span></div>
 <div class="flexc" style="height:64px;padding:0 20px;gap:16px"><span class="bs g" style="width:44px;font-size:18px">Hat</span><img src="../img/items/royal-duck.png" style="max-height:48px;max-width:60px"><span style="font-size:28px">ROYAL DUCK</span></div></div>"""
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_rotunda_blur.jpg)"></div><div class="scrim"></div>
<style>.rimg{{max-width:150px;max-height:66px}} .aimg{{max-width:200px;max-height:80px}} .ic{{width:.9em;height:.9em}}</style>
<div class="abs" style="left:64px;top:44px;font-size:104px;line-height:1.1">{SEL_GUN['name'].upper()}</div>
<div class="abs bs g" style="left:70px;top:166px;font-size:23px">Secondary, Wish Duck skin</div>
<div class="slab y sk flexc" style="right:70px;top:56px;height:64px;padding:0 30px;font-size:30px"><span class="un">DONE</span></div>
{rows}
{cos}
{hatted(660, style="left:670px;top:236px")}
<div class="abs" style="left:1440px;top:196px;width:416px">
 <div class="flexc" style="justify-content:space-between"><span style="font-size:30px">MASTERY {MASTERY['level']}</span><span class="bs g" style="font-size:19px">{MASTERY['xp']} / {MASTERY['next']} XP</span></div>
 <div class="bar" style="margin-top:8px;height:10px"><b style="width:{MASTERY['frac']*100:.0f}%;background:var(--y)"></b></div>
 {stats}
 <div class="flexc bs g" style="font-size:17px;margin-top:14px;gap:8px"><i style="width:3px;height:16px;background:var(--y)"></i>Secondary average</div>
</div>
<div class="abs lbl" style="left:64px;bottom:206px;font-size:24px">SECONDARIES</div>
{arm}
</div>"""
    return page("B loadout", CSS, body)


def shop():
    tabs = "".join(f'<div class="flexc lbl {"sk" if i == 0 else ""}" style="height:56px;padding:0 22px;font-size:21px;{"background:var(--w);color:#0b0c0e" if i == 0 else ""}"><span class="{"un" if i == 0 else ""}">{t}</span></div>' for i, t in enumerate(SHOP_TABS))
    daily = "".join(f"""<div class="flexc" style="height:110px;border-top:{"none" if i == 0 else "2px solid var(--rule)"};gap:26px;padding:0 22px 0 8px">
 <div style="width:300px;height:96px;display:grid;place-items:center"><img src="../img/items/{img}.png" style="max-width:296px;max-height:94px;filter:drop-shadow(0 6px 8px rgba(0,0,0,.5))"></div>
 <div style="flex:1"><div style="font-size:34px;line-height:1.2">{name}</div><div class="bs" style="font-size:19px"><span style="color:{RARITY[rar]}">{rar.title()}</span> <span class="g">{kind.lower()}</span></div></div>
 <div style="text-align:right"><div class="flexc {"" if afford(price) else "g"}" style="gap:8px;font-size:34px;justify-content:flex-end">{rbx() if curr == "robux" else cur("coin", 30)}{price}</div>{"" if afford(price) else f'<div class="bs" style="font-size:15px;color:#e0a070">need {int(price.replace(",", "")) - WALLET_N:,} more</div>'}</div></div>""" for i, (img, name, kind, price, curr, rar) in enumerate(DAILY))
    crates = "".join(f"""<div class="flexc" style="height:68px;border-top:{"none" if i == 0 else "2px solid var(--rule)"};gap:18px;padding:0 20px 0 12px">
 <div style="width:110px;height:64px;display:grid;place-items:center"><img src="../img/items/{img}.png" style="max-width:100px;max-height:60px"></div>
 <div style="flex:1"><div style="font-size:30px;line-height:1.2">{name}</div><div class="bs g" style="font-size:18px">{holds}</div></div>
 <span class="flexc" style="gap:6px;font-size:26px">{cur('ticket', 34)}{tk}</span><span class="bs g" style="font-size:18px;margin:0 12px">or</span><span style="font-size:28px">{rbx()} {rp}</span></div>""" for i, (img, name, holds, tk, rp) in enumerate(CONTAINERS))
    packs = "".join(f"""<div class="flexc" style="height:42px;gap:12px;padding:0 20px 0 16px;border-top:{"none" if i == 0 else "2px solid var(--rule)"}"><span style="width:44px;display:flex;justify-content:center">{coin_stack(i + 1, 18)}</span>
 <span style="width:92px;font-size:24px">{c}</span><span class="bs g" style="flex:1;font-size:16px">{("+" + b) if b else ""}</span><span style="font-size:22px">{rbx()} {r}</span></div>""" for i, (c, r, b) in enumerate(COIN_PACKS))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_rotunda_blur.jpg)"></div><div class="scrim"></div>
<div class="abs" style="left:64px;top:28px;font-size:104px;line-height:1.2">SHOP</div>
<div class="slab flexc" style="left:330px;top:60px;height:56px">{tabs}</div>
{_wallet()}
<div class="slab" style="left:64px;top:170px;width:1792px;height:360px;overflow:hidden;background:#0b0c0e url(../img/bg/hub_rotunda_blur.jpg) center/cover">
 <div style="position:absolute;inset:0;background:linear-gradient(90deg,rgba(10,11,13,.35),rgba(10,11,13,.82) 62%)"></div>
 <div style="position:absolute;left:50px;top:6px">{set_shot(960, 350)}</div>
 <div style="position:absolute;left:1190px;top:44px;font-size:150px;line-height:1;white-space:nowrap">{HERO['name']}</div>
 <div class="bs" style="position:absolute;left:1196px;top:212px;font-size:22px;color:#c9b98f">{len(HERO['set'])} skins</div>
 <div class="slab y sk flexc" style="left:1200px;top:254px;height:80px;padding:0 36px;font-size:46px"><span class="un">{rbx()}&nbsp;{HERO['price']}</span></div>
</div>
<div class="abs flexc" style="left:64px;top:560px;gap:14px"><span class="lbl" style="font-size:24px">DAILY</span><span class="bs g" style="font-size:20px">New in {DAILY_RESET}</span></div>
<div class="slab" style="left:64px;top:606px;width:1050px;height:444px">{daily}</div>
<div class="abs lbl" style="left:1144px;top:560px;font-size:24px">CRATES</div>
<div class="slab" style="left:1144px;top:606px;width:712px;height:206px">{crates}</div>
<div class="abs lbl" style="left:1144px;top:836px;font-size:24px">COINS</div>
<div class="slab" style="left:1144px;top:882px;width:712px;height:168px">{packs}</div>
</div>"""
    return page("B shop", CSS, body)


def phone():
    m = MATCH
    import math
    order = ["jump", "aim", "hook", "reload", "grenade", "slide"]
    pts = [(k, 752 + 138 * math.cos(math.radians(98 + 26 * i)), 214 - 138 * math.sin(math.radians(98 + 26 * i)), 54 if k in ("jump", "aim") else 46) for i, k in enumerate(order)]
    keys = "".join(f'<div class="slab" style="left:{x - s/2:.0f}px;top:{y - s/2:.0f}px;width:{s}px;height:{s}px;display:grid;place-items:center">' + f'<span style="margin-top:{-6 if k in ("hook", "grenade") else 0}px">{act_icon(k, int(s*0.46))}</span>' + (f'<span style="position:absolute;left:0;right:0;bottom:4px;text-align:center;font-size:12px">×{GRAPPLE["charges"] if k == "hook" else m["util_n"]}</span>' if k in ("hook", "grenade") else "") + '</div>' for k, x, y, s in pts)
    slots = "".join(f'<div class="slab {"w" if i == 0 else ""}" style="position:relative;width:62px;height:34px;display:grid;place-items:center">{slot_icon(g, 42, 18)}</div>' for i, (k, g, n) in enumerate(SLOTS))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_crate.jpg)"></div>
<div class="abs" style="left:50%;transform:translateX(-50%);top:8px;display:flex;flex-direction:column;align-items:center">
 <div class="flexc" style="height:42px;background:var(--k)">
  <div class="flexc lbl" style="height:42px;padding:0 7px;background:var(--w);color:#0b0c0e;font-size:10px;line-height:1.05;text-align:center">ROUND<br>{m['round']}</div>
  <div class="flexc" style="height:42px;padding:0 6px 0 10px;gap:6px;background:{TEAM['blossom'][0]};color:#0b0c0e"><span style="font-size:34px;line-height:1">{m['us']}</span>{heads_col('blossom', 15, 2)}</div>
  <div class="flexc" style="height:42px;padding:0 10px 0 6px;gap:6px;background:{TEAM['sky'][0]};color:#0b0c0e">{heads_col('sky', 15, 2)}<span style="font-size:34px;line-height:1">{m['them']}</span></div>
  <div style="padding:0 10px;font-size:22px">{m['time']}</div>
 </div>
 {scores_tab('var(--w)', '#0b0c0e', 11, '0', "font-family:'Builder Sans';font-weight:800;text-transform:uppercase;letter-spacing:.04em")}
</div>
<div class="abs" style="left:58px;top:126px;width:120px;height:120px;background:rgba(10,11,13,.5);box-shadow:inset 0 0 0 3px rgba(244,243,239,.5)"></div>
<div class="abs" style="left:92px;top:160px;width:52px;height:52px;background:var(--w)"></div>
<div class="slab" style="left:232px;bottom:12px;width:96px;height:58px">
 <div style="position:absolute;left:12px;top:-6px;font-size:52px;line-height:1.2">{m['hp']}</div>
 <div class="hb" style="height:5px"><b style="width:{m['hp']}%"></b></div>
</div>
<div class="abs" style="left:340px;bottom:12px"><div class="flexc" style="gap:4px;margin-bottom:6px">{slots}</div>
 <div class="slab" style="position:relative;width:194px;height:52px"><div style="position:absolute;left:14px;top:-6px;font-size:48px;line-height:1.2">{m['ammo']}<span class="g" style="font-size:22px;font-weight:400"> /{m['mag']}</span></div></div></div>
{keys}
<div class="slab y sk" style="left:706px;top:162px;width:100px;height:104px;display:grid;place-items:center"><span class="un">{fire_icon(34)}</span></div>
<svg class="abs" style="left:412px;top:185px" width="20" height="20" viewBox="0 0 36 36"><g stroke="#0b0c0e" stroke-width="6"><path d="M18 4v8M18 24v8M4 18h8M24 18h8"/></g><g stroke="#f4f3ef" stroke-width="3"><path d="M18 4v8M18 24v8M4 18h8M24 18h8"/></g></svg>
</div>"""
    return page("B phone", CSS, body, 844, 390)


def scoreboard():
    bd = BOARD
    def table(team, players, n0):
        head_row = '<div class="flexc bs g" style="height:38px;font-size:19px;padding:0 18px 0 76px"><span style="flex:1">Player</span>' + "".join(
            f'<span style="width:{w}px;text-align:right">{h}</span>' for h, w in [("K", 46), ("D", 46), ("A", 46), ("Dmg", 90), ("Ping", 72)]) + "</div>"
        rows = ""
        for j, (nm, k, de, a, dmg, ping, alive, me) in enumerate(players):
            col = "#0b0c0e" if me else ("var(--w)" if alive else "var(--g2)")
            br = f'<span style="position:absolute;left:0;top:-56px">{party_mark2(84, "var(--y)", "PARTY", -26, 13)}</span>' if nm in PARTY and not me else ""
            rows += f"""<div class="flexc {"you" if me else ""}" style="position:relative;height:54px;padding:0 18px 0 14px;border-top:2px solid var(--rule);{"background:var(--w);" if me else ""}color:{col}">{br}
 <span style="position:relative;margin-right:18px;{"" if alive else "filter:grayscale(1);opacity:.55"}">{head(n0 + j, 40)}{"" if alive else dead_x(40)}</span>
 <span class="bs" style="flex:1;font-size:25px">{nm} <span style="font-size:15px;opacity:.6;margin-left:6px">LV {LEVELS[nm]}</span></span>
 {"".join(f'<span style="width:{w}px;text-align:right;font-size:30px">{v}</span>' for v, w in [(k, 46), (de, 46), (a, 46), (dmg, 90), (ping, 72)])}</div>"""
        return f"""<div style="width:980px;position:relative"><div class="flexc" style="height:48px;gap:14px"><span style="font-size:34px;color:{TEAM[team][0]}">{team}</span><span class="bs g" style="font-size:21px">{sum(p[1] for p in players)} kills</span></div>
 <div style="background:var(--k);padding-bottom:4px">{head_row}{rows}</div></div>"""
    t1, t2 = bd["teams"]
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_forest_blur.jpg)"></div><div class="scrim" style="background:rgba(8,9,11,.45)"></div>
<div class="abs" style="left:50%;transform:translateX(-50%);top:40px;display:flex;flex-direction:column;align-items:center">
 <div class="tab sk" style="position:relative"><span class="un">ROUND {bd['round']}</span></div>
 <div style="display:flex">
  <div style="width:150px;height:120px;background:{TEAM['blossom'][0]};color:#0b0c0e;display:grid;place-items:center;font-size:104px;line-height:1">{bd['us']}</div>
  <div style="width:180px;height:120px;background:var(--k);display:grid;place-items:center;font-size:56px">{bd['time']}</div>
  <div style="width:150px;height:120px;background:{TEAM['sky'][0]};color:#0b0c0e;display:grid;place-items:center;font-size:104px;line-height:1">{bd['them']}</div>
 </div>
 <div style="font-size:30px;margin-top:10px;text-shadow:0 2px 8px rgba(0,0,0,.6)">{bd['map']}</div>
</div>
<div class="abs" style="left:50%;transform:translateX(-50%);top:306px;display:flex;flex-direction:column;gap:14px">{table(*t1, 0)}{table(*t2, 4)}</div>
</div>"""
    return page("B scoreboard", CSS, body)


FRAMES = {"hub": hub, "match": match, "loadout": loadout, "shop": shop, "phone": phone, "scoreboard": scoreboard}
