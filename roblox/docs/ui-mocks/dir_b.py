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
    return f"""<div class="slab flexc" style="right:56px;top:56px;height:64px;padding:0 24px 0 22px;gap:12px;font-size:34px">
 {cur('coin', 34)}{WALLET['coins']}<span style="width:2px;height:34px;background:var(--rule);margin:0 8px"></span>{cur('ticket', 42)}{WALLET['tickets']}</div>"""


def hub():
    info = {"quests": f"{QUESTS_DONE[0]}/{QUESTS_DONE[1]}", "party": "1/4"}
    items = "".join(
        f'<div class="flexc" style="flex:1;justify-content:center;height:72px;gap:12px;border-left:2px solid var(--rule)"><span style="font-size:30px;letter-spacing:.03em">{label}</span>'
        f'<span class="bs g" style="font-size:21px">{info.get(mid, "")}</span></div>' for mid, label, key in MENU[1:] + [("settings", "SETTINGS", "")])
    xp = PLAYER['xp'] / PLAYER['xp_next']
    tick = "".join(f'<span style="margin-right:34px">{m} <span class="bs g" style="font-size:20px">{q}</span></span>' for m, q in QUEUES)
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_spawn.jpg)"></div>
<div class="slab flexc" style="left:56px;top:56px;width:470px;height:84px;padding:0 22px;gap:16px">
 {head(0, 56)}<div style="flex:1"><div class="flexc" style="justify-content:space-between"><span class="bs" style="font-size:30px">{PLAYER['name']}</span><span style="font-size:24px">LV {PLAYER['level']}</span></div>
 <div class="bs g" style="font-size:17px">{PLAYER['xp']:,} / {PLAYER['xp_next']:,} xp</div></div>
 <div class="hb" style="height:6px"><b style="width:{xp*100:.0f}%"></b></div>
</div>
{_wallet()}
<div class="slab y cut" style="left:56px;bottom:76px;width:330px;height:168px;--c:26px">
 <div style="position:absolute;left:28px;top:-2px;font-size:104px;line-height:1.2;letter-spacing:.01em">PLAY</div>
 <div style="position:absolute;left:31px;bottom:16px;font-size:24px;font-weight:400;letter-spacing:.06em">1V1 RANKED</div>
</div>
<div class="slab flexc" style="left:386px;right:56px;bottom:76px;height:72px">{items}</div>
<div class="slab flexc" style="left:0;right:0;bottom:0;height:52px;font-size:22px;letter-spacing:.04em">
 <div style="height:52px;margin-left:40px"><div class="bug" style="font-size:24px"><span>JANKFIRE</span></div></div>
 <div class="flexc" style="height:52px;padding:0 22px;margin:0 26px 0 10px;background:var(--w);color:#0b0c0e">{HUB['name']}</div>
 <span class="bs g" style="margin-right:26px;font-size:20px">In queue</span>{tick}
 <span style="margin-left:auto;margin-right:56px">{HUB['here']} <span class="bs g" style="font-size:20px">players</span></span>
</div>
</div>"""
    return page("B hub", CSS, body)


def match():
    m = MATCH
    def box(team, score):
        return f'<div style="width:128px;height:92px;background:{TEAM[team][0]};color:#0b0c0e;display:grid;place-items:center;font-size:80px;line-height:1">{score}</div>'
    def strip(team):
        return f'<div class="flexc" style="width:128px;height:28px;background:#0b0c0e;justify-content:center;font-size:16px;letter-spacing:.1em">{team.upper()}</div>'
    feed = "".join(f"""<div class="slab flexc bs" style="right:56px;top:{56 + i*50}px;height:42px;padding:0 18px;gap:12px;font-size:21px">{feed_line(*f)}</div>""" for i, f in enumerate(FEED))
    slots = ""
    for i, (k, g, n) in enumerate(SLOTS + [("G", None, "")]):
        on = i == 0
        inner = slot_icon(g, 62, 28) if g else f'<span style="font-size:28px;line-height:0">{icon("grenade")}</span><span style="font-size:22px;margin-left:6px">×{m["util_n"]}</span>'
        slots += f'<div class="slab flexc {"w" if on else ""}" style="right:{56 + (3-i)*112}px;bottom:180px;width:106px;height:58px;justify-content:center"><span style="position:absolute;left:8px;top:2px;font-size:17px;opacity:.7">{k}</span>{inner}</div>'
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_crate.jpg)"></div>
<div class="abs" style="left:50%;transform:translateX(-50%);top:24px;display:flex;flex-direction:column;align-items:center">
 <div class="tab" style="position:relative">ROUND {m['round']}</div>
 <div style="display:flex">
  <div>{box('blossom', m['us'])}{strip('blossom')}</div>
  <div style="width:150px;height:92px;background:var(--k);display:grid;place-items:center;font-size:48px">{m['time']}</div>
  <div>{box('sky', m['them'])}{strip('sky')}</div>
 </div>
</div>
{feed}
<div class="slab" style="left:56px;bottom:56px;width:196px;height:112px">
 <div style="position:absolute;left:24px;top:-8px;font-size:96px;line-height:1.2">{m['hp']}</div>
 <div class="hb" style="height:10px"><b style="width:{m['hp']}%"></b></div>
</div>
<div class="slab" style="right:56px;bottom:56px;width:300px;height:112px">
 <div style="position:absolute;left:26px;top:-8px;font-size:96px;line-height:1.2">{m['ammo']}<span class="g" style="font-size:40px;font-weight:400"> /{m['mag']}</span></div>
</div>
{slots}
<svg class="abs" style="left:942px;top:522px" width="36" height="36" viewBox="0 0 36 36"><g stroke="#0b0c0e" stroke-width="6" stroke-linecap="square"><path d="M18 4v8M18 24v8M4 18h8M24 18h8"/></g><g stroke="#f4f3ef" stroke-width="3" stroke-linecap="square"><path d="M18 4v8M18 24v8M4 18h8M24 18h8"/></g></svg>
</div>"""
    return page("B match", CSS, body)


def loadout():
    rows = ""
    pics = {"PRIMARY": gunpic("ar", "rimg"), "SECONDARY": '<img class="rimg" src="../img/items/wish_duck_34.png">', "MELEE": gunpic("katana", "rimg"), "UTILITY": '<img class="rimg" src="../img/items/frag.png" style="max-height:74px">'}
    for i, (slot, g, name, note) in enumerate(LOADOUT):
        on = i == SEL
        k = ["1", "2", "3", "G"][i]
        sub = {"SECONDARY": "Wish Duck", "UTILITY": "2 charges"}.get(slot, "")
        rows += f"""<div class="slab {"w" if on else ""}" style="left:64px;top:{212 + i*102}px;width:560px;height:94px">
 <div style="position:absolute;left:24px;top:24px;font-size:30px;font-weight:400;{"color:#8d9197" if on else "color:var(--g2)"}">{k}</div>
 <div style="position:absolute;left:66px;top:{10 if sub else 18}px;font-size:42px;line-height:1.25">{name}</div>
 {f'<div class="bs" style="position:absolute;left:68px;top:62px;font-size:19px;{"color:#55595f" if on else "color:var(--g)"}">{sub}</div>' if sub else ''}
 <div style="position:absolute;right:16px;top:10px;width:150px;height:74px;display:grid;place-items:center">{pics[slot]}</div></div>"""
    stats = "".join(f"""<div style="margin-top:22px"><div class="flexc" style="justify-content:space-between"><span class="bs g" style="font-size:21px">{k}</span><span style="font-size:40px;line-height:1.1;text-transform:none">{v}</span></div>
 <div class="bar" style="margin-top:6px;position:relative"><b style="width:{f*100:.0f}%"></b><i style="position:absolute;top:-4px;bottom:-4px;left:{avg*100:.0f}%;width:3px;background:var(--y)"></i></div></div>""" for (k, v, f), avg in zip(STATS, STAT_AVG))
    arm = ""
    for i, (g, n, st) in enumerate(ARMORY):
        on = st == "on"
        locked = isinstance(st, tuple)
        tag = ("" if not locked else (f'<span class="bs g flexc" style="font-size:19px;gap:6px">{icon("lock")}Level {st[1]}</span>' if st[0] == "level"
                                      else f'<span class="flexc" style="font-size:21px;gap:6px">{cur("coin", 22)}{st[1]}</span>'))
        arm += f"""<div class="slab {"w" if on else ""}" style="left:{64 + i*362}px;bottom:44px;width:350px;height:150px">
 <div style="position:absolute;left:16px;top:14px;width:200px;height:84px;display:grid;place-items:center;{"filter:grayscale(1);opacity:.5" if locked else ""}">{gunpic(g, "aimg")}</div>
 <div style="position:absolute;left:18px;top:104px;font-size:26px">{n}</div>
 <div style="position:absolute;right:16px;top:20px">{tag}</div></div>"""
    cos = "".join(f"""<div class="slab" style="left:{64 + i*284}px;top:634px;width:276px;height:130px">
 <img src="../img/items/{img}.png" style="position:absolute;left:18px;top:10px;max-width:150px;max-height:78px">
 <div style="position:absolute;left:18px;bottom:10px;font-size:26px">{name}</div><div class="bs g" style="position:absolute;right:16px;top:14px;font-size:18px">{what}</div></div>"""
                  for i, (img, name, what) in enumerate([("wish_duck_34", "WISH DUCK", "Skin"), ("royal-duck", "ROYAL DUCK", "Hat")]))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_rotunda_blur.jpg)"></div><div class="scrim"></div>
<style>.rimg{{max-width:150px;max-height:66px}} .aimg{{max-width:200px;max-height:80px}} .ic{{width:.9em;height:.9em}}</style>
<div class="abs" style="left:64px;top:44px;font-size:104px;line-height:1.1">{SEL_GUN['name']}</div>
<div class="slab y cut flexc" style="right:64px;top:56px;height:64px;padding:0 30px;font-size:30px;--c:12px">DONE</div>
{rows}
{cos}
<img class="abs" src="../img/{SEL_GUN['img']}" style="left:660px;top:190px;width:680px;filter:drop-shadow(0 24px 26px rgba(0,0,0,.5))">
<div class="abs" style="left:1440px;top:196px;width:416px">
 <div class="flexc" style="justify-content:space-between"><span style="font-size:30px">MASTERY {MASTERY['level']}</span><span class="bs g" style="font-size:19px">{MASTERY['xp']} / {MASTERY['next']} xp</span></div>
 <div class="bar" style="margin-top:8px;height:10px"><b style="width:{MASTERY['frac']*100:.0f}%;background:var(--y)"></b></div>
 {stats}
 <div class="flexc bs g" style="font-size:17px;margin-top:14px;gap:8px"><i style="width:3px;height:16px;background:var(--y)"></i>Secondary average</div>
</div>
<div class="abs" style="left:64px;bottom:206px;font-size:30px">SECONDARIES</div>
{arm}
</div>"""
    return page("B loadout", CSS, body)


def shop():
    tabs = "".join(f'<div class="flexc" style="height:56px;padding:0 22px;font-size:26px;letter-spacing:.04em;{"background:var(--w);color:#0b0c0e" if i == 0 else ""}">{t}</div>' for i, t in enumerate(SHOP_TABS))
    others = "".join(f"""<div style="width:220px"><div style="height:92px;display:flex;align-items:flex-end"><img src="../img/items/{img}.png" style="max-width:210px;max-height:92px"></div>
 <div style="font-size:26px;margin-top:8px">{s}</div><div class="bs g" style="font-size:19px">{g}</div></div>""" for s, g, img in HERO['set'][1:] + [("Royal Duck", "Hat", "royal-duck")])
    daily = "".join(f"""<div class="flexc" style="height:100px;border-top:{"none" if i == 0 else "2px solid var(--rule)"};gap:22px;padding:0 22px 0 12px">
 <div style="width:200px;height:86px;background:{RARITY[rar]}38;display:grid;place-items:center"><img src="../img/items/{img}.png" style="max-width:184px;max-height:78px"></div>
 <div style="flex:1"><div style="font-size:34px;line-height:1.2">{name}</div><div class="bs" style="font-size:19px"><span style="color:{RARITY[rar]}">{rar.title()}</span> <span class="g">{kind.lower()}</span></div></div>
 <div class="flexc" style="gap:8px;font-size:34px">{rbx() if curr == "robux" else cur("coin", 30)}{price}</div></div>""" for i, (img, name, kind, price, curr, rar) in enumerate(DAILY))
    crates = "".join(f"""<div class="flexc" style="height:84px;border-top:{"none" if i == 0 else "2px solid var(--rule)"};gap:18px;padding:0 20px 0 12px">
 <div style="width:110px;height:72px;display:grid;place-items:center"><img src="../img/items/{img}.png" style="max-width:106px;max-height:68px"></div>
 <div style="flex:1"><div style="font-size:30px;line-height:1.2">{name}</div><div class="bs g" style="font-size:18px">{holds}</div></div>
 <span class="flexc" style="gap:6px;font-size:26px">{cur('ticket', 34)}{tk}</span><span class="bs g" style="font-size:18px;margin:0 12px">or</span><span style="font-size:28px">{rbx()} {rp}</span></div>""" for i, (img, name, holds, tk, rp) in enumerate(CONTAINERS))
    packs = "".join(f"""<div style="flex:1;padding:12px 14px 10px;border-left:{"none" if i == 0 else "2px solid var(--rule)"}">
 <div style="font-size:32px;line-height:1.1">{c}</div><div class="bs g" style="font-size:17px;height:22px">{b or "coins"}</div>
 <div style="font-size:24px;margin-top:6px">{rbx()} {r}</div></div>""" for i, (c, r, b) in enumerate(COIN_PACKS))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/hub_rotunda_blur.jpg)"></div><div class="scrim"></div>
<div class="abs" style="left:64px;top:28px;font-size:104px;line-height:1.2">SHOP</div>
<div class="slab flexc" style="left:330px;top:60px;height:56px">{tabs}</div>
{_wallet()}
<div class="slab" style="left:64px;top:170px;width:1792px;height:400px;overflow:hidden">
 <img src="../img/items/wish_duck_34.png" style="position:absolute;left:-40px;top:-30px;width:640px;filter:drop-shadow(0 20px 22px rgba(0,0,0,.6))">
 <div style="position:absolute;left:610px;top:30px;font-size:120px;line-height:1">{HERO['name']}</div>
 <div class="bs g" style="position:absolute;left:614px;top:164px;width:430px;font-size:23px;line-height:1.4">The VIP pass. Wish Duck and two more skins, the Royal Duck hat and the VIP title.</div>
 <div class="slab y cut flexc" style="left:614px;top:286px;height:76px;padding:0 32px;font-size:44px;--c:14px">{rbx()}&nbsp;{HERO['price']}</div>
 <div class="flexc" style="position:absolute;left:1090px;top:110px;gap:18px;align-items:flex-start">{others}</div>
</div>
<div class="abs flexc" style="left:64px;top:598px;gap:14px"><span style="font-size:30px">DAILY</span><span class="bs g" style="font-size:20px">New in {DAILY_RESET}</span></div>
<div class="slab" style="left:64px;top:646px;width:1050px;height:404px">{daily}</div>
<div class="abs" style="left:1144px;top:598px;font-size:30px">CRATES</div>
<div class="slab" style="left:1144px;top:646px;width:712px;height:256px">{crates}</div>
<div class="slab flexc" style="left:1144px;top:916px;width:712px;height:134px;align-items:stretch">{packs}</div>
</div>"""
    return page("B shop", CSS, body)


def phone():
    m = MATCH
    keys = "".join(f'<div class="slab" style="left:{x - s/2:.0f}px;top:{y - s/2:.0f}px;width:{s}px;height:{s}px;display:grid;place-items:center">{act_icon(k, int(s*0.52))}</div>' for k, x, y, s in arc(752, 222, 124, 84, 266))
    slots = "".join(f'<div class="slab {"w" if i == 0 else ""}" style="position:relative;width:62px;height:34px;display:grid;place-items:center">{slot_icon(g, 42, 18)}</div>' for i, (k, g, n) in enumerate(SLOTS))
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_crate.jpg)"></div>
<div class="abs" style="left:50%;transform:translateX(-50%);top:8px;display:flex">
 <div style="width:58px;height:44px;background:{TEAM['blossom'][0]};color:#0b0c0e;display:grid;place-items:center;font-size:36px;line-height:1">{m['us']}</div>
 <div style="width:76px;height:44px;background:var(--k);display:grid;place-items:center;font-size:24px">{m['time']}</div>
 <div style="width:58px;height:44px;background:{TEAM['sky'][0]};color:#0b0c0e;display:grid;place-items:center;font-size:36px;line-height:1">{m['them']}</div>
</div>
<div class="abs" style="left:58px;top:126px;width:120px;height:120px;border-radius:50%;background:var(--k)"></div>
<div class="abs" style="left:92px;top:160px;width:52px;height:52px;border-radius:50%;background:var(--w)"></div>
<div class="slab" style="left:232px;bottom:12px;width:96px;height:58px">
 <div style="position:absolute;left:12px;top:-6px;font-size:52px;line-height:1.2">{m['hp']}</div>
 <div class="hb" style="height:5px"><b style="width:{m['hp']}%"></b></div>
</div>
<div class="abs" style="left:340px;bottom:12px"><div class="flexc" style="gap:4px;margin-bottom:6px">{slots}</div>
 <div class="slab" style="position:relative;width:194px;height:52px"><div style="position:absolute;left:14px;top:-6px;font-size:48px;line-height:1.2">{m['ammo']}<span class="g" style="font-size:22px;font-weight:400"> /{m['mag']}</span></div></div></div>
{keys}
<div class="slab y cut" style="left:700px;top:170px;width:104px;height:104px;display:grid;place-items:center;--c:18px">{fire_icon(34)}</div>
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
            br = party_bracket(138, "var(--y)") if nm in PARTY and j == 0 else ""
            rows += f"""<div class="flexc" style="position:relative;height:70px;padding:0 18px 0 14px;border-top:2px solid var(--rule);{"background:var(--w);" if me else ""}color:{col}">{br}
 <span style="position:relative;margin-right:18px;{"" if alive else "filter:grayscale(1);opacity:.55"}">{head(n0 + j, 46)}{"" if alive else dead_x(46)}</span>
 <span class="bs" style="flex:1;font-size:26px">{nm} <span style="font-size:17px;opacity:.65;margin-left:4px">lv {LEVELS[nm]}</span></span>
 {"".join(f'<span style="width:{w}px;text-align:right;font-size:30px">{v}</span>' for v, w in [(k, 46), (de, 46), (a, 46), (dmg, 90), (ping, 72)])}</div>"""
        return f"""<div style="width:680px;position:relative"><div class="flexc" style="height:48px;gap:14px"><span style="font-size:34px;color:{TEAM[team][0]}">{team}</span><span class="bs g" style="font-size:21px">{sum(p[1] for p in players)} kills</span></div>
 <div style="background:var(--k);padding-bottom:4px">{head_row}{rows}</div></div>"""
    t1, t2 = bd["teams"]
    body = f"""<div class="stage"><div class="bg" style="background-image:url(../img/bg/match_forest_blur.jpg)"></div><div class="scrim" style="background:rgba(8,9,11,.45)"></div>
<div class="abs" style="left:50%;transform:translateX(-50%);top:64px;display:flex;flex-direction:column;align-items:center">
 <div class="flexc" style="height:32px"><div class="bug" style="font-size:18px"><span>JANKFIRE</span></div><div class="tab" style="position:relative;margin-left:8px">ROUND {bd['round']}</div></div>
 <div style="display:flex">
  <div style="width:150px;height:120px;background:{TEAM['blossom'][0]};color:#0b0c0e;display:grid;place-items:center;font-size:104px;line-height:1">{bd['us']}</div>
  <div style="width:180px;height:120px;background:var(--k);display:grid;place-items:center;font-size:56px">{bd['time']}</div>
  <div style="width:150px;height:120px;background:{TEAM['sky'][0]};color:#0b0c0e;display:grid;place-items:center;font-size:104px;line-height:1">{bd['them']}</div>
 </div>
 <div style="font-size:30px;margin-top:10px;text-shadow:0 2px 8px rgba(0,0,0,.6)">{bd['map']}</div>
</div>
<div class="abs flexc" style="left:260px;top:356px;gap:40px;align-items:flex-start">{table(*t1, 0)}{table(*t2, 4)}</div>
</div>"""
    return page("B scoreboard", CSS, body)


FRAMES = {"hub": hub, "match": match, "loadout": loadout, "shop": shop, "phone": phone, "scoreboard": scoreboard}
