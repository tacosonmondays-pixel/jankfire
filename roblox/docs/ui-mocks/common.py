"""Shared parts for the UI mocks: fonts, icons, the real game data shown on screen, page shell."""
import glob
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")  # copied from the local Roblox install, not in git

# Only fonts that ship with Roblox (rbxasset://fonts/families/*.json).
FONT_FILES = {
    ("Builder Sans", 400): "BuilderSans-Regular.otf",
    ("Builder Sans", 500): "BuilderSans-Medium.otf",
    ("Builder Sans", 700): "BuilderSans-Bold.otf",
    ("Builder Sans", 800): "BuilderSans-ExtraBold.otf",
    ("Builder Extended", 400): "BuilderExtended-Regular.otf",
    ("Builder Extended", 600): "BuilderExtended-SemiBold.otf",
    ("Builder Extended", 700): "BuilderExtended-Bold.otf",
    ("Builder Mono", 400): "BuilderMono-Regular.otf",
    ("Builder Mono", 700): "BuilderMono-Bold.otf",
    ("Oswald", 400): "Oswald-Regular.ttf",
    ("Oswald", 700): "Oswald-Bold.ttf",
    ("Titillium Web", 400): "TitilliumWeb-Regular.ttf",
    ("Titillium Web", 700): "TitilliumWeb-Bold.ttf",
}


def setup_fonts():
    os.makedirs(FONTS, exist_ok=True)
    roots = sorted(glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Roblox\Versions\*\content\fonts")),
                   key=os.path.getmtime, reverse=True)
    for f in FONT_FILES.values():
        dst = os.path.join(FONTS, f)
        if os.path.exists(dst):
            continue
        for r in roots:
            src = os.path.join(r, f)
            if os.path.exists(src):
                shutil.copy(src, dst)
                break
        else:
            raise SystemExit(f"font {f} not found in a Roblox install")


def font_css():
    out = []
    for (fam, w), f in FONT_FILES.items():
        out.append(f"@font-face{{font-family:'{fam}';src:url('../fonts/{f}');font-weight:{w};font-style:normal}}")
    return "\n".join(out)


# ---------------------------------------------------------------- icons (our own, 24x24, filled)
ICONS = {
    "play": '<path d="M7 4.6c0-1.1 1.2-1.8 2.2-1.2l11 6.9c.9.6.9 1.9 0 2.5l-11 6.9C8.2 20.3 7 19.6 7 18.5z"/>',
    "quests": '<path fill-rule="evenodd" d="M6 2h12a3 3 0 0 1 3 3v14a3 3 0 0 1-3 3H6a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3zm10.7 6.3a1.3 1.3 0 0 0-1.9-1.8l-4.3 4.6-1.6-1.6a1.3 1.3 0 1 0-1.8 1.8l2.5 2.5a1.3 1.3 0 0 0 1.9 0zM7 16.2h10v2.3H7z"/>',
    "party": '<circle cx="8.5" cy="7.5" r="3.6"/><circle cx="16.8" cy="8.6" r="3"/><path d="M1.8 19.6c0-3.6 3-6.2 6.7-6.2s6.7 2.6 6.7 6.2v.9H1.8z"/><path d="M16.4 13.4c3.3 0 5.8 2.3 5.8 5.5v1.6h-5.3v-1c0-2.4-.9-4.4-2.4-5.8.6-.2 1.2-.3 1.9-.3z"/>',
    "hubs": '<path fill-rule="evenodd" d="M2 21V9.5L12 3l10 6.5V21h-6.5v-5.5a3.5 3.5 0 0 0-7 0V21z"/>',
    "profile": '<path fill-rule="evenodd" d="M5 2h14a3 3 0 0 1 3 3v14a3 3 0 0 1-3 3H5a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3zm7 3.6a3.6 3.6 0 1 0 0 7.2 3.6 3.6 0 0 0 0-7.2zM5.8 18.8h12.4c-.4-2.9-3-4.8-6.2-4.8s-5.8 1.9-6.2 4.8z"/>',
    "shop": '<path fill-rule="evenodd" d="M8 7V6a4 4 0 0 1 8 0v1h2.6c.8 0 1.4.6 1.5 1.4l1 11.5A2 2 0 0 1 19.1 22H4.9a2 2 0 0 1-2-2.1l1-11.5C4 7.6 4.6 7 5.4 7zm2.3 0h3.4V6a1.7 1.7 0 0 0-3.4 0z"/>',
    "loadout": '<path d="M2 7.5h17.5l2.5 2v3H15l-1.6 2.3h-2.6l-.9 5.2H6.2l1-6.3L2 12.5z"/>',
    "settings": '<path fill-rule="evenodd" d="M10.3 2h3.4l.6 2.7 1.8.8 2.4-1.5 2.4 2.4-1.5 2.4.8 1.8 2.8.7v3.4l-2.8.6-.8 1.8 1.5 2.4-2.4 2.4-2.4-1.5-1.8.8-.6 2.8h-3.4l-.6-2.8-1.8-.8-2.4 1.5-2.4-2.4 1.5-2.4-.8-1.8L2 13.7v-3.4l2.7-.7.8-1.8L4 5.4 6.4 3l2.4 1.5 1.8-.8zM12 8.4a3.6 3.6 0 1 0 0 7.2 3.6 3.6 0 0 0 0-7.2z"/>',
    "coin": '<path fill-rule="evenodd" d="M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20zm0 3.2a6.8 6.8 0 1 0 0 13.6 6.8 6.8 0 0 0 0-13.6z"/><circle cx="12" cy="12" r="3.4"/>',
    "ticket": '<path d="M2 6.5C2 5.7 2.7 5 3.5 5h17c.8 0 1.5.7 1.5 1.5v3a2.5 2.5 0 0 0 0 5v3c0 .8-.7 1.5-1.5 1.5h-17C2.7 19 2 18.3 2 17.5v-3a2.5 2.5 0 0 0 0-5z"/>',
    "robux": '<path fill-rule="evenodd" d="M12 1.8l8.9 5.1v10.2L12 22.2l-8.9-5.1V6.9zm0 3.4L6 8.7v6.6l6 3.5 6-3.5V8.7zM9.6 9.6h4.8v4.8H9.6z"/>',
    "lock": '<path fill-rule="evenodd" d="M7 10V7.5a5 5 0 0 1 10 0V10h.5a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-11a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2zm2.6 0h4.8V7.5a2.4 2.4 0 0 0-4.8 0z"/>',
    "plus": '<path d="M10.4 3h3.2v7.4H21v3.2h-7.4V21h-3.2v-7.4H3v-3.2h7.4z"/>',
    "arrow": '<path d="M3 10.4h12.3l-4.6-4.6L13 3.5l8.5 8.5-8.5 8.5-2.3-2.3 4.6-4.6H3z"/>',
    "health": '<path d="M9 2.5h6v6.5h6.5v6H15v6.5H9V15H2.5V9H9z"/>',
    "speed": '<path d="M13.5 1.5L4 13.5h6.5L9 22.5l10-12.5h-6.6z"/>',
    "grenade": '<path fill-rule="evenodd" d="M10 2h5v2.2h1.5a1 1 0 0 1 1 1v1.6A8 8 0 1 1 6.5 7.5V5.2a1 1 0 0 1 1-1H10zm2 7.5a5 5 0 0 0-5 5h2.6a2.4 2.4 0 0 1 2.4-2.4z"/>',
    "check": '<path d="M9.2 15.6l10-10.3 2.3 2.3L9.2 20.2 2.5 13.4l2.3-2.3z"/>',
    "people": '<circle cx="12" cy="7" r="4"/><path d="M4 21c0-4.4 3.6-7.4 8-7.4s8 3 8 7.4z"/>',
    "aim": '<path fill-rule="evenodd" d="M10.8 1.5h2.4v2.7a8 8 0 0 1 6.6 6.6h2.7v2.4h-2.7a8 8 0 0 1-6.6 6.6v2.7h-2.4v-2.7a8 8 0 0 1-6.6-6.6H1.5v-2.4h2.7a8 8 0 0 1 6.6-6.6zm1.2 5a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11zm0 3.5a2 2 0 1 1 0 4 2 2 0 0 1 0-4z"/>',
    "jump": '<path d="M12 3.5l8.5 8.5-2.3 2.3-4.6-4.6V21h-3.2V9.7l-4.6 4.6L3.5 12z"/>',
    "slide": '<path d="M5 4h3.2v10.3l11.3-0.1V17.5H5z"/><path d="M14.5 8.5l5.5 5.5-5.5 5.5-2.2-2.2 3.3-3.3-3.3-3.3z"/>',
    "hook": '<circle cx="12" cy="3.6" r="2.2"/><path d="M10.6 5.5h2.8v10.9c2.2-.5 3.8-2 4.4-4l-1.9.4 2.9-4.2 2 4.7-1.7-.3c-.9 3.6-4.4 6.4-9.1 6.4S3.8 16.6 2.9 13l-1.7.3 2-4.7 2.9 4.2-1.9-.4c.6 2 2.2 3.5 4.4 4z"/>',
    "reload": '<path d="M12 3.5a8.5 8.5 0 0 1 8 5.6l1.6-1v6.2l-5.6-2.8 1.7-1A5.6 5.6 0 1 0 17 16.6l2.3 1.9A8.5 8.5 0 1 1 12 3.5z"/>',
    "swap": '<path d="M7 3l4.5 4.5L7 12V9H2V6h5z"/><path d="M17 12l-4.5 4.5L17 21v-3h5v-3h-5z"/>',
    "stab": '<path d="M20.5 2.5l-1.4 6.3-8.6 8.6-3-3 8.6-8.6z"/><path d="M5.2 13.3l5.5 5.5-1.8 1.8-1.6-1.6-3.2 3.2-2.3-2.3 3.2-3.2-1.6-1.6z"/>',
    "emote": '<path fill-rule="evenodd" d="M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20zM8.6 8a1.6 1.6 0 1 0 0 3.2 1.6 1.6 0 0 0 0-3.2zm6.8 0a1.6 1.6 0 1 0 0 3.2 1.6 1.6 0 0 0 0-3.2zM7.2 13.6a5 5 0 0 0 9.6 0z"/>',
    "star": '<path d="M12 2.5l2.7 6.3 6.8.6-5.2 4.5 1.6 6.7L12 17l-5.9 3.6 1.6-6.7-5.2-4.5 6.8-.6z"/>',
    "close": '<path d="M5.6 3.4L12 9.8l6.4-6.4 2.2 2.2-6.4 6.4 6.4 6.4-2.2 2.2-6.4-6.4-6.4 6.4-2.2-2.2 6.4-6.4-6.4-6.4z"/>',
    "clock": '<path fill-rule="evenodd" d="M12 2a10 10 0 1 1 0 20 10 10 0 0 1 0-20zm-1.3 4.5v6.6l5 3 1.3-2.1-3.7-2.2V6.5z"/>',
    "crown": '<path d="M3 7l4.5 4L12 4l4.5 7L21 7l-2 12H5z"/>',
    "auto": '<path d="M9.2 3h5.6L21 21h-3.6l-1.5-4.5H8.1L6.6 21H3zm-.1 10.4h5.8L12 5.6z"/>',
}


def icon(name, cls="ic"):
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">{ICONS[name]}</svg>'


def rbx(cls="rbx"):
    """Stand-in for Roblox's own Robux glyph (utf8.char(0xE002) in game)."""
    return f'<b class="{cls}">R$</b>'


def sil(gid, cls="sil", kind="side"):
    """A gun's own outline (from the keyed render's alpha) filled with currentColor."""
    return f'<i class="{cls}" style="-webkit-mask-image:url(../img/guns/{gid}_{kind}.png)"></i>'


def gun(gid, cls="gunimg", kind="side"):
    return f'<img class="{cls}" src="../img/guns/{gid}_{kind}.png" alt="">'


def item(name, cls="itemimg"):
    return f'<img class="{cls}" src="../img/items/{name}.png" alt="">'


# ---------------------------------------------------------------- what the screens show (real game labels)
TEAM = {
    "blossom": ("#f4a7c8", "#e87fb0"),
    "sky": ("#a3cbf2", "#5b88e0"),
    "butter": ("#f5dd8a", "#e8c45a"),
    "mint": ("#a6e3c4", "#5fbf8f"),
}

PLAYER = {"name": "Rook", "level": 24, "xp": 1240, "xp_next": 2000}
WALLET = {"coins": "2,450", "tickets": 3}
HUB = {"name": "THE ROTUNDA", "here": 31}
MENU = [  # (id, label, key)
    ("play", "PLAY", "M"), ("quests", "QUESTS", "U"), ("party", "PARTY", "J"), ("hubs", "HUBS", "H"),
    ("profile", "PROFILE", "K"), ("shop", "SHOP", "B"), ("loadout", "LOADOUT", "L"),
]
PLAY_PICK = "1V1 · RANKED"
QUESTS_DONE = (2, 3)

MATCH = {"mode": "2V2", "round": 4, "time": "1:12", "us": 2, "them": 1, "hp": 86, "speed": 21,
         "weapon": "Assault Rifle", "ammo": 24, "mag": 30, "util": "Frag Grenade", "util_n": 2}
SLOTS = [("1", "ar", "Assault Rifle"), ("2", "revolver", "Revolver"), ("3", "katana", "Katana")]
FEED = [("Rook", "blossom", "ar", "moth_09", "sky"), ("Kestrel", "sky", "revolver", "lumen", "blossom")]

LOADOUT = [  # (slot, gun id or None, name, note)
    ("PRIMARY", "ar", "Assault Rifle", "Seigaiha wrap"),
    ("SECONDARY", "revolver", "Revolver", "Default"),
    ("MELEE", "katana", "Katana", "Default"),
    ("UTILITY", None, "Frag Grenade", "2 charges"),
]
STATS = [("DAMAGE", "11", 0.22), ("FIRE RATE", "10/s", 0.55), ("RANGE", "300 m", 0.75), ("MAG", "30", 0.5)]
MASTERY = 7
ARMORY = [  # (gun id, name, state) state: "on" / "owned" / ("coins", price) / ("level", n)
    ("redline", "Redline", "owned"), ("shredder", "Shredder", "owned"), ("ar", "Assault Rifle", "on"),
    ("smg", "SMG", "owned"), ("shotgun", "Shotgun", "owned"), ("sniper", "Sniper", "owned"),
    ("burst", "Burst Rifle", "owned"), ("lmg", "LMG", ("level", 26)),
    ("dmr", "Marksman Rifle", ("level", 30)), ("lever", "Lever Rifle", ("level", 34)),
    ("autoshot", "Auto Shotgun", ("coins", "2,500")),
]

SHOP_TABS = ["FEATURED", "SETS", "DAILY", "CONTAINERS", "COINS", "INVENTORY"]
HERO = {"name": "DUCKY", "tag": "VIP SET", "skins": "Wish Duck · Bubble Bath · Ribbon Duck",
        "guns": "Revolver · LMG · Katana", "price": "399"}
DAILY = [  # (img, name, kind, coins, rarity)
    ("wrap_seigaiha", "Seigaiha", "Wrap", "1,800", "RARE"),
    ("star-tricorne", "Star Tricorne", "Hat", "9,000", "LEGENDARY"),
    ("wrap_sakura_storm", "Sakura Storm", "Wrap", "3,600", "EPIC"),
    ("wrap_kintsugi", "Kintsugi", "Wrap", "3,600", "EPIC"),
]
DAILY_RESET = "07:12:40"
CONTAINERS = [  # (img, name, holds, coins, robux)  real prices: roblox/docs/MONEY.md
    ("crate", "Crate", "Skins", "900", "120"), ("duffel", "Duffel Bag", "Hats", "2,500", "90"), ("spray", "Spray Can", "Wraps", "1,000", "60")]
COIN_PACKS = [("1,200", "99"), ("6,500", "499"), ("28,000", "1,999"), ("70,000", "4,500")]

TOUCH = ["aim", "jump", "slide", "hook", "reload", "swap", "stab"]


def page(title, css, body, w=1920, h=1080, extra_head=""):
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<style>
{font_css()}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{w}px;height:{h}px;overflow:hidden;background:#111;-webkit-font-smoothing:antialiased}}
.stage{{position:relative;width:{w}px;height:{h}px;overflow:hidden}}
.bg{{position:absolute;inset:0;background-size:cover;background-position:center}}
.ic{{display:inline-block;width:1em;height:1em;flex:none}}
.sil{{display:inline-block;-webkit-mask-size:contain;-webkit-mask-repeat:no-repeat;-webkit-mask-position:center;background:currentColor}}
.abs{{position:absolute}}
.rbx{{font-family:'Builder Sans';font-weight:800;font-size:.8em;letter-spacing:-.02em;opacity:.85}}
{css}
</style>{extra_head}</head><body>{body}</body></html>"""


# held-Tab scoreboard (a 4v4 on Spooky Forest; the local player is Rook)
BOARD = {
    "mode": "4V4", "round": 6, "map": "Spooky Forest", "time": "0:48", "us": 3, "them": 2,
    "teams": [
        ("blossom", [  # (name, kills, deaths, assists, damage, ping, alive, local)
            ("Rook", 9, 4, 3, "1,840", 38, True, True),
            ("Kestrel", 7, 5, 6, "1,610", 52, True, False),
            ("Pebble", 5, 6, 4, "1,120", 71, False, False),
            ("Juno", 3, 7, 8, "940", 44, True, False),
        ]),
        ("sky", [
            ("moth_09", 8, 5, 2, "1,720", 61, True, False),
            ("lumen", 6, 6, 5, "1,390", 35, False, False),
            ("Vesper", 6, 7, 3, "1,250", 88, True, False),
            ("tidepool", 2, 8, 6, "760", 47, False, False),
        ]),
    ],
}


def cur(kind="coin", size=24, cls="cur"):
    """The game's own coin / crate-ticket art (roblox/docs/money/icons)."""
    return f'<img class="{cls}" src="../img/icons/{kind}.png" style="width:{size}px;height:{size}px;flex:none;object-fit:contain;filter:drop-shadow(0 1px 1.5px rgba(0,0,0,.45))" alt="">'


# ---------------------------------------------------------------- round 2 (26 Nov): critic fixes shared by every direction
# Names that look like a real Roblox lobby (the critics read Kestrel/Vesper/Juno as LLM placeholders).
PLAYER = {"name": "rookshots", "level": 24, "xp": 1240, "xp_next": 2000}
FEED = [("rookshots", "blossom", "ar", "moth_09", "sky"), ("ItzFrostyy", "sky", "revolver", "Kaito_kun7", "blossom")]
BOARD["teams"] = [
    ("blossom", [("rookshots", 9, 4, 3, "1,840", 38, True, True), ("Dxnny4K", 7, 5, 6, "1,610", 52, True, False),
                 ("lilnoob2013", 5, 6, 4, "1,120", 71, False, False), ("Kaito_kun7", 3, 7, 8, "940", 44, True, False)]),
    ("sky", [("moth_09", 8, 5, 2, "1,720", 61, True, False), ("xX_Vortex_Xx", 6, 6, 5, "1,390", 35, False, False),
             ("ItzFrostyy", 6, 7, 3, "1,250", 88, True, False), ("bacon2011", 2, 8, 6, "760", 47, False, False)]),
]
QUEUES = [("1V1", "1/2"), ("1V1V1", "0/3"), ("2V2", "2/4"), ("3V3", "0/6"), ("4V4", "3/8")]

# Loadout: the Secondary slot is open, with the VIP Ducky skin and hat actually equipped (we have renders of both).
LOADOUT = [  # (slot, gun id or None, name, skin/charges)
    ("PRIMARY", "ar", "Assault Rifle", "Default"),
    ("SECONDARY", "revolver", "Revolver", "Wish Duck"),
    ("MELEE", "katana", "Katana", "Default"),
    ("UTILITY", None, "Frag Grenade", "2 charges"),
]
SEL = 1
SEL_GUN = {"name": "Revolver", "skin": "Wish Duck", "hat": "Royal Duck", "img": "items/wish_duck_34.png"}
STATS = [("Damage", "33", 0.62), ("Fire rate", "2.5/s", 0.25), ("Range", "250 m", 0.70), ("Magazine", "6", 0.20)]
MASTERY = {"level": 7, "xp": "1,850", "next": "3,000", "frac": 0.62}
ARMORY = [  # Secondaries
    ("revolver", "Revolver", "on"), ("pistol", "Pistol", "owned"), ("sawnoff", "Sawed-Off", "owned"),
    ("marbles", "Marble Shotgun", ("level", 14)), ("akimbo", "Lefty & Righty", ("coins", "5,000")),
]

SHOP_TABS = ["FEATURED", "DAILY", "SETS", "CRATES", "COINS"]
HERO = {"name": "DUCKY", "price": "399", "set": [("Wish Duck", "Revolver", "wish_duck_34"), ("Bubble Bath", "LMG", "bubble_bath_side"),
                                                   ("Ribbon Duck", "Katana", "ribbon_duck_side")], "extra": "Royal Duck hat and the VIP title"}
RARITY = {"RARE": "#79aee6", "EPIC": "#b994ea", "LEGENDARY": "#e7c35a"}
DAILY = [  # (img, name, kind, price, currency, rarity)
    ("triangulum_side", "Triangulum", "Sniper skin", "600", "robux", "EPIC"),
    ("star-tricorne", "Star Tricorne", "Hat", "9,000", "coin", "LEGENDARY"),
    ("wrap_seigaiha", "Seigaiha", "Wrap", "1,800", "coin", "RARE"),
    ("wrap_sakura_storm", "Sakura Storm", "Wrap", "3,600", "coin", "EPIC"),
]
CONTAINERS = [  # (img, name, holds, tickets, robux): prices from roblox/docs/MONEY.md
    ("crate", "Crate", "A skin", "12", "120"), ("duffel", "Duffel Bag", "A hat", "6", "90"), ("spray", "Spray Can", "A wrap", "3", "60")]


# Our own icon family, drawn as solid shapes in the same weight as the gun silhouettes (no web icon sets).
ICONS2 = {  # name: (viewBox, svg)
    "gear": ("0 0 32 32", '<g>' + "".join(f'<rect x="13" y="1" width="6" height="7" rx="1" transform="rotate({a} 16 16)"/>' for a in range(0, 360, 45)) +
             '</g><path fill-rule="evenodd" d="M16 5.5a10.5 10.5 0 1 1 0 21a10.5 10.5 0 1 1 0-21zM16 11.2l4.2 2.4v4.8L16 20.8l-4.2-2.4v-4.8z"/>'),
    "hook": ("0 0 32 32", '<path fill-rule="evenodd" d="M16 0.5a4 4 0 1 1 0 8a4 4 0 1 1 0-8zm0 2.4a1.6 1.6 0 1 0 0 3.2a1.6 1.6 0 1 0 0-3.2z"/>'
             '<rect x="14" y="7" width="4" height="17" rx="1"/>'
             '<path d="M16 22 Q7 25 5 14" stroke="currentColor" stroke-width="4" fill="none" stroke-linecap="round"/>'
             '<path d="M16 22 Q25 25 27 14" stroke="currentColor" stroke-width="4" fill="none" stroke-linecap="round"/>'
             '<path d="M2 15.5L5 9l3.6 5.6z"/><path d="M30 15.5L27 9l-3.6 5.6z"/><path d="M13.6 23h4.8L16 31z"/>'),
    "reload": ("0 0 32 32", '<path d="M10.5 6.5H21C21 14 22.5 20 26 26.5L17.5 30.5C13.5 23 11 15 10.5 6.5Z"/><path d="M12.5 5.5V3.2Q15.8 0.4 19 3.2V5.5Z"/>'
               '<rect x="13" y="12" width="6.5" height="2.2" rx="1" fill="rgba(0,0,0,.35)"/>'),
    "aim": ("0 0 32 32", '<rect x="7" y="13" width="19" height="6.5" rx="2"/><path d="M24.5 10.5L31 9.5V23L24.5 22Z"/><path d="M1 12L7.5 13V19.5L1 20.5Z"/>'
            '<rect x="14" y="8" width="5" height="6" rx="1"/><rect x="10" y="19" width="3.5" height="5" rx="1"/><rect x="19.5" y="19" width="3.5" height="5" rx="1"/>'),
    "fire": ("0 0 32 32", '<path d="M16 1C20 5 21.6 9 21.6 12.5H10.4C10.4 9 12 5 16 1Z"/><rect x="10" y="14" width="12" height="13" rx="1"/><rect x="8.5" y="27.5" width="15" height="3.5" rx="1"/>'),
    "grenade": ("0 0 32 32", '<path fill-rule="evenodd" d="M15 9.5c5.2 0 9 4.6 9 10.2S20.2 30 15 30S6 25.3 6 19.7S9.8 9.5 15 9.5zM7.5 16.6h15v2H7.5zM7 21.8h16v2H7zM14 10v19.5h2V10z"/>'
                '<rect x="11.5" y="5" width="7" height="5.5" rx="1"/><path d="M18.5 6L25.5 8.5L23.5 17" stroke="currentColor" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                '<circle cx="9" cy="5.5" r="3" stroke="currentColor" stroke-width="2.2" fill="none"/>'),
    "jump": ("0 0 32 32", '<rect x="12.5" y="1" width="7.5" height="7" rx="1.6"/><rect x="11.5" y="9" width="9.5" height="10" rx="1"/>'
             '<rect x="6.5" y="2.5" width="4" height="10" rx="1" transform="rotate(-18 8.5 7.5)"/><rect x="22" y="2.5" width="4" height="10" rx="1" transform="rotate(18 24 7.5)"/>'
             '<rect x="11.5" y="19.5" width="4.4" height="9" rx="1" transform="rotate(28 13.7 20)"/><rect x="16.8" y="19.5" width="4.4" height="9" rx="1" transform="rotate(-28 19 20)"/>'),
    "slide": ("0 0 32 32", '<rect x="12" y="21" width="19" height="5" rx="1"/><g transform="rotate(-38 11 24)"><rect x="7" y="12" width="8.5" height="12" rx="1"/>'
              '<rect x="7.5" y="3.8" width="7.5" height="7" rx="1.6"/><rect x="2.5" y="14" width="3.8" height="10" rx="1"/></g>'
              '<rect x="1" y="28" width="30" height="2.4" rx="1.2"/>'),
}


def icon(name, cls="ic"):
    if name in ICONS2:
        vb, body = ICONS2[name]
        return f'<svg class="{cls}" viewBox="{vb}" fill="currentColor" aria-hidden="true">{body}</svg>'
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">{ICONS[name]}</svg>'


def stab_icon(h=24):
    """Stab = the game's own knife, tilted."""
    return f'<i class="sil" style="width:{h*1.6:.0f}px;height:{h*0.5:.0f}px;transform:rotate(-38deg);-webkit-mask-image:url(../img/guns/knife_side.png)"></i>'


def swap_icon(h=24):
    """Swap = the rifle behind the revolver, both from the game's own renders."""
    return (f'<span style="position:relative;display:inline-block;width:{h*1.7:.0f}px;height:{h}px">'
            f'<i class="sil" style="position:absolute;left:0;top:0;width:{h*1.3:.0f}px;height:{h*0.55:.0f}px;opacity:.55;-webkit-mask-image:url(../img/guns/ar_side.png)"></i>'
            f'<i class="sil" style="position:absolute;right:0;bottom:0;width:{h*0.95:.0f}px;height:{h*0.7:.0f}px;-webkit-mask-image:url(../img/guns/revolver_side.png)"></i></span>')


def act_icon(k, h=24):
    if k == "stab":
        return stab_icon(h)
    if k == "swap":
        return swap_icon(h)
    return f'<span style="font-size:{h}px;line-height:0">{icon(k)}</span>'


def gunpic(gid, cls="gunimg"):
    """A gun picture; Lefty & Righty is two pistols."""
    if gid == "akimbo":
        return (f'<span style="position:relative;display:inline-block;width:140px;height:64px">'
                f'<img class="{cls}" src="../img/guns/pistol_side.png" style="position:absolute;left:0;top:0;width:84px">'
                f'<img class="{cls}" src="../img/guns/pistol_side.png" style="position:absolute;right:0;bottom:0;width:84px;transform:scaleX(-1)"></span>')
    return f'<img class="{cls}" src="../img/guns/{gid}_side.png" alt="">'


def silpic(gid, cls="sil"):
    if gid == "akimbo":
        return (f'<span style="position:relative;display:inline-block;width:76px;height:30px">'
                f'<i class="{cls}" style="position:absolute;left:0;top:0;width:44px;height:22px;-webkit-mask-image:url(../img/guns/pistol_side.png)"></i>'
                f'<i class="{cls}" style="position:absolute;right:0;bottom:0;width:44px;height:22px;transform:scaleX(-1);-webkit-mask-image:url(../img/guns/pistol_side.png)"></i></span>')
    return sil(gid, cls)


# Blocky Roblox-style headshots (placeholders for the players' real avatar thumbnails).
_HEADS = [  # (skin, hair/hat colour, style)
    ("#f2c84b", "#2b2b30", "cap"), ("#e9b48a", "#5a3a22", "hair"), ("#c98d62", "#e74c3c", "beanie"), ("#f2c84b", "#3d6fb0", "hood"),
    ("#8a5a3c", "#1f1f22", "hair"), ("#f1d1b5", "#d9a13a", "hair"), ("#f2c84b", "#5bbf7a", "cap"), ("#e9b48a", "#7a4fc9", "beanie"),
]


def head(i, size=40):
    sk, hc, st = _HEADS[i % len(_HEADS)]
    hat = {
        "cap": f'<rect x="7" y="5" width="26" height="9" rx="4" fill="{hc}"/><rect x="22" y="11" width="14" height="4" rx="2" fill="{hc}"/>',
        "hair": f'<path d="M8 15 Q8 5 20 5 Q32 5 32 15 L32 12 Q26 10 20 12 Q13 9 8 15Z" fill="{hc}"/>',
        "beanie": f'<path d="M8 15 Q8 3 20 3 Q32 3 32 15Z" fill="{hc}"/><rect x="7" y="12" width="26" height="4" rx="2" fill="{hc}" opacity=".85"/>',
        "hood": f'<path d="M4 40 L4 16 Q4 2 20 2 Q36 2 36 16 L36 40 L31 40 L31 18 Q31 9 20 9 Q9 9 9 18 L9 40Z" fill="{hc}"/>',
    }[st]
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 40 40" style="flex:none;display:block">'
            f'<rect width="40" height="40" rx="7" fill="rgba(255,255,255,.10)"/>'
            f'<rect x="9" y="8" width="22" height="22" rx="5" fill="{sk}"/>'
            f'<rect x="15" y="16" width="2.6" height="4" rx="1.3" fill="#1b1b1b"/><rect x="22.4" y="16" width="2.6" height="4" rx="1.3" fill="#1b1b1b"/>'
            f'<path d="M15 23 Q20 27 25 23" stroke="#1b1b1b" stroke-width="1.8" fill="none" stroke-linecap="round"/>'
            f'<rect x="12" y="31" width="16" height="9" fill="{hc}" opacity=".9"/>{hat}</svg>')


ARC_KEYS = ["aim", "hook", "stab", "swap", "reload", "grenade", "slide", "jump"]


def arc(cx=752, cy=232, R=120, a0=80, a1=276):
    """Phone action keys on an asymmetric arc round FIRE's left side (thumb sweep), top to bottom."""
    import math
    n = len(ARC_KEYS)
    out = []
    for i, k in enumerate(ARC_KEYS):
        a = math.radians(a0 + (a1 - a0) * i / (n - 1))
        out.append((k, cx + R * math.cos(a), cy - R * math.sin(a)))
    return out


def speed(color="#fff", font="'Builder Sans'", weight=800, size=22, shadow="0 2px 0 rgba(0,0,0,.35),0 0 14px rgba(0,0,0,.4)"):
    """The speedometer's home: just under the crosshair."""
    return (f'<div class="abs" style="left:0;right:0;top:588px;text-align:center;font-family:{font};font-weight:{weight};font-size:{size}px;'
            f'color:{color};text-shadow:{shadow};font-variant-numeric:tabular-nums;text-transform:none">{MATCH["speed"]} m/s</div>')


# ---------------------------------------------------------------- round 3 (26 Nov): numbers that add up, new icons
# 4v4 elimination, round 6, Blossom leads 3-2. Kills on one side = deaths on the other (no self-kills).
# Blossom: 3 wins x 4 + 2 losses (2 + 1) + 2 now = 17 kills. Sky: 2 wins x 4 + 3 losses (2 + 1 + 3) + 1 now = 15.
BOARD["teams"] = [
    ("blossom", [("rookshots", 6, 3, 3, "1,290", 38, True, True), ("Dxnny4K", 5, 4, 4, "1,060", 52, True, False),
                 ("milo_pr", 4, 4, 2, "880", 71, False, False), ("Kaito_kun7", 2, 4, 5, "610", 44, True, False)]),
    ("sky", [("moth_09", 6, 4, 2, "1,180", 61, True, False), ("vortexx2", 4, 4, 3, "870", 35, False, False),
             ("frostbyte_r", 4, 4, 4, "820", 88, True, False), ("beanzz", 1, 5, 5, "430", 47, False, False)]),
]
FEED = [("rookshots", "blossom", "ar", "vortexx2", "sky"), ("frostbyte_r", "sky", "revolver", "milo_pr", "blossom")]
SLOTS = [("1", "ar", "Assault Rifle"), ("2", "duck", "Revolver"), ("3", "katana", "Katana")]
ARMORY = [("revolver", "Revolver", "on"), ("pistol", "Pistol", "owned"), ("sawnoff", "Sawed-Off", "owned"),
          ("marbles", "Marble Shotgun", ("level", 30)), ("akimbo", "Lefty & Righty", ("coins", "5,000"))]
QUEST_LIST = [("Win a match", 1, 1, "30"), ("Get 3 kills in a row", 3, 3, "50"), ("Win without losing a round", 0, 1, "80")]
DAILY = [  # (img, name, kind, price, currency, rarity)
    ("triangulum_side", "Triangulum", "Sniper skin", "300", "robux", "rare"),
    ("star-tricorne", "Star Tricorne", "Hat", "9,000", "coin", "legendary"),
    ("wrap_seigaiha", "Seigaiha", "Wrap", "1,800", "coin", "rare"),
    ("wrap_sakura_storm", "Sakura Storm", "Wrap", "3,600", "coin", "epic"),
]
# The game's own rarity colours (shared/LootTable.luau)
RARITY = {"rare": "#4aa3e0", "epic": "#a76ae0", "legendary": "#f0b234"}
CONTAINERS = [("crate", "Crate", "One random skin", "12", "120"), ("duffel", "Duffel Bag", "One random hat", "6", "90"),
              ("spray", "Spray Can", "One random wrap", "3", "60")]
COIN_PACKS = [("1,200", "99", "packsq_99"), ("6,500", "499", "packsq_499"), ("28,000", "1,999", "packsq_1999"), ("70,000", "4,500", "packsq_4500")]
ARC_KEYS = ["aim", "hook", "stab", "reload", "grenade", "slide", "jump"]

ICONS2["hook"] = ("0 0 32 32",
    '<path d="M27 2.5C24 6 21 7.5 17.5 8" stroke="currentColor" stroke-width="2.6" fill="none" stroke-linecap="round" stroke-dasharray="3 2.4"/>'
    '<rect x="13" y="6" width="6" height="5" rx="1.2"/>'
    '<path d="M16 10.5V21Q16 27 10.5 27Q6 27 5 22" stroke="currentColor" stroke-width="4.4" fill="none" stroke-linecap="round"/>'
    '<path d="M1.8 23.8L5.6 16.8L9.4 23.2Z"/>')
ICONS2["reload"] = ("0 0 32 32",
    '<path d="M9.5 5.5H20.5V9C20.5 15 22.5 20.5 27 25.5L18.5 30.5C13 24.5 10 17 9.5 9Z"/>'
    '<path d="M11.5 5.6Q15 0.5 18.5 5.6Z"/>'
    '<g fill="rgba(0,0,0,.38)"><rect x="12" y="12" width="6.5" height="2" rx="1" transform="rotate(-14 15 13)"/><rect x="13.4" y="17" width="6.5" height="2" rx="1" transform="rotate(-22 16.5 18)"/></g>')
ICONS2["grenade"] = ("0 0 32 32",
    '<path fill-rule="evenodd" d="M14.5 9.5c5.4 0 9.2 4.7 9.2 10.3S19.9 30.5 14.5 30.5S5.3 25.4 5.3 19.8S9.1 9.5 14.5 9.5zM6.6 16.5h15.8v2.2H6.6zM6.2 22h16.6v2.2H6.2z"/>'
    '<rect x="11" y="5" width="7" height="5.5" rx="1"/><path d="M18 6L25.5 8.8L23.8 17.5" stroke="currentColor" stroke-width="2.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="8.6" cy="5.4" r="3.1" stroke="currentColor" stroke-width="2.3" fill="none"/>')
# Roblox-style blocky figure: square head, torso, four limbs
ICONS2["jump"] = ("0 0 32 32",
    '<rect x="12.5" y="0.5" width="7" height="6.6" rx="1.4"/><rect x="11.5" y="7.8" width="9" height="10" rx="0.8"/>'
    '<rect x="6.4" y="1.4" width="4" height="10" rx="0.8" transform="rotate(-14 8.4 6.4)"/><rect x="21.6" y="1.4" width="4" height="10" rx="0.8" transform="rotate(14 23.6 6.4)"/>'
    '<rect x="11.5" y="18.4" width="4.2" height="8" rx="0.8"/><rect x="16.3" y="18.4" width="4.2" height="8" rx="0.8"/>'
    '<path d="M8 30.5h16" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" opacity=".55"/>')
ICONS2["slide"] = ("0 0 32 32",
    '<g transform="rotate(-62 14 20)"><rect x="10.5" y="9" width="8.5" height="10" rx="0.8"/><rect x="11.2" y="1.5" width="7" height="6.6" rx="1.4"/>'
    '<rect x="10.5" y="19.6" width="4" height="8.5" rx="0.8"/><rect x="15" y="19.6" width="4" height="8.5" rx="0.8"/><rect x="19.6" y="9.4" width="3.6" height="8.5" rx="0.8"/></g>'
    '<path d="M1 29.5h30" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/>'
    '<path d="M3 21h4M2 25h6" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity=".6"/>')
ICONS2["robux"] = ("0 0 24 24", '<path fill-rule="evenodd" d="M12 1.6l9 5.2v10.4l-9 5.2-9-5.2V6.8zm0 3.4L6 8.5v7L12 19l6-3.5v-7zM9.6 9.6h4.8v4.8H9.6z"/>')
# a chunky wayfinding arrow (D)
ICONS2["way"] = ("0 0 32 32", '<path d="M2 12.5h15.5V4L30 16 17.5 28v-8.5H2z"/>')


def rbx(cls="rbx"):
    """The Robux mark (in game: utf8.char(0xE002) in a Roblox font)."""
    return f'<svg class="{cls}" viewBox="0 0 24 24" fill="currentColor" style="width:.92em;height:.92em;vertical-align:-.1em;flex:none" aria-hidden="true">{ICONS2["robux"][1]}</svg>'


def stab_icon(h=24):
    """Stab = the game's own katana, tilted."""
    return f'<i class="sil" style="width:{h*1.9:.0f}px;height:{h*0.34:.0f}px;transform:rotate(-40deg);-webkit-mask-image:url(../img/guns/katana_side.png)"></i>'


def sil(gid, cls="sil", kind="side"):
    """A gun's own outline (keyed render's alpha) in currentColor. 'duck' = the equipped Wish Duck revolver."""
    src = "../img/items/wish_duck_34.png" if gid == "duck" else f"../img/guns/{gid}_{kind}.png"
    return f'<i class="{cls}" style="-webkit-mask-image:url({src})"></i>'


def fire_icon(h=40, gid="ar"):
    """FIRE shows the gun you hold."""
    return f'<i class="sil" style="display:inline-block;width:{h*1.7:.0f}px;height:{h*0.75:.0f}px;-webkit-mask-image:url(../img/guns/{gid}_side.png);-webkit-mask-size:contain;-webkit-mask-repeat:no-repeat;-webkit-mask-position:center;background:currentColor"></i>'


def act_icon(k, h=24):
    if k == "stab":
        return stab_icon(h)
    return f'<span style="font-size:{h}px;line-height:0">{icon(k)}</span>'


def arc(cx=752, cy=222, R=122, a0=86, a1=268):
    """Phone action keys on an arc round FIRE (top to bottom on the thumb's side). Returns (key, x, y, size)."""
    import math
    size = {"jump": 58, "slide": 50, "aim": 48}
    n = len(ARC_KEYS)
    out = []
    for i, k in enumerate(ARC_KEYS):
        a = math.radians(a0 + (a1 - a0) * i / (n - 1))
        out.append((k, cx + R * math.cos(a), cy - R * math.sin(a), size.get(k, 44)))
    return out


def dead_x(size=44):
    """A cross over a dead player's headshot."""
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 40 40" style="position:absolute;left:0;top:0">'
            f'<path d="M9 9L31 31M31 9L9 31" stroke="#e0473f" stroke-width="5" stroke-linecap="round"/></svg>')


# ---------------------------------------------------------------- round 4 (26 Nov)
STATS = [("Damage", "33", 0.55), ("Headshot", "79", 0.70), ("Fire rate", "2.5/s", 0.25), ("Magazine", "6", 0.20)]
STAT_AVG = [0.45, 0.50, 0.42, 0.50]   # secondary averages, for the comparison mark
# coin packs: base rate 12 coins a Robux, bonuses from docs/MONEY.md
COIN_PACKS = [("1,200", "99", ""), ("6,500", "499", "500 bonus"), ("28,000", "1,999", "4,000 bonus"), ("70,000", "4,500", "16,000 bonus")]
ARC_KEYS = ["aim", "hook", "reload", "grenade", "slide", "jump"]
LEVELS = {"rookshots": 24, "Dxnny4K": 31, "milo_pr": 12, "Kaito_kun7": 40, "moth_09": 27, "vortexx2": 18, "frostbyte_r": 35, "beanzz": 9}
PARTY = {"rookshots", "Dxnny4K"}
FEED = [("rookshots", "blossom", "ar", "vortexx2", "sky", True), ("frostbyte_r", "sky", "revolver", "milo_pr", "blossom", False)]

ICONS2["headshot"] = ("0 0 32 32", '<rect x="8" y="6" width="16" height="15" rx="3"/><rect x="11" y="22" width="10" height="5" rx="1"/>'
                      '<path d="M16 1v6M16 25v6M1 13.5h6M25 13.5h6" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>')
ICONS2["hook"] = ("0 0 32 32",
    '<path d="M30 1.5L19 9" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-dasharray="3.2 2.6"/>'
    '<rect x="13" y="8" width="7" height="5.5" rx="1"/><rect x="14.5" y="13" width="4" height="9" rx="1"/>'
    '<path d="M16.5 21.5L5 17.5L7.5 26Z"/><path d="M16.5 21.5L28 17.5L25.5 26Z"/><path d="M14 21h5l-2.5 9.5Z"/>')
ICONS2["aim"] = ("0 0 32 32",
    '<rect x="7" y="12" width="18" height="8" rx="1"/><rect x="25" y="9.5" width="6" height="13" rx="1"/><rect x="1" y="11" width="6" height="10" rx="1"/>'
    '<rect x="13" y="6" width="6" height="6" rx="1"/><rect x="10.5" y="20" width="4" height="5" rx="1"/><rect x="18" y="20" width="4" height="5" rx="1"/>')


def katana_sil(w=92, h=26):
    """The katana silhouette, stretched thicker so it holds up at small sizes."""
    return f'<i style="display:inline-block;width:{w}px;height:{h}px;background:currentColor;-webkit-mask-image:url(../img/guns/katana_side.png);-webkit-mask-size:100% 100%;-webkit-mask-repeat:no-repeat"></i>'


def slot_icon(g, w=64, h=30):
    if g == "katana":
        return katana_sil(int(w * 1.3), int(h * 0.62))
    if g == "duck":
        g = "revolver"
    return f'<i style="display:inline-block;width:{w}px;height:{h}px;background:currentColor;-webkit-mask-image:url(../img/guns/{g}_side.png);-webkit-mask-size:contain;-webkit-mask-repeat:no-repeat;-webkit-mask-position:center"></i>'


SLOTS = [("1", "ar", "Assault Rifle"), ("2", "revolver", "Revolver"), ("3", "katana", "Katana")]


def feed_line(a, ta, g, b, tb, hs, size=21, cls=""):
    return (f'<span style="color:{TEAM[ta][0]}">{a}</span>{slot_icon(g, int(size*2.9), int(size*1.3))}'
            + (f'<span style="font-size:{size+3}px;line-height:0;opacity:.9">{icon("headshot")}</span>' if hs else "")
            + f'<span style="color:{TEAM[tb][0]}">{b}</span>')


def party_bracket(h=128, color="rgba(255,255,255,.45)"):
    return f'<i style="position:absolute;left:-14px;top:14px;width:8px;height:{h}px;border:3px solid {color};border-right:none;border-radius:4px 0 0 4px"></i>'


# ---------------------------------------------------------------- round 5 (26 Nov): identity pass helpers
# 2v2, round 4: Blossom = rookshots + milo_pr, Sky = vortexx2 + frostbyte_r. The feed shows rookshots
# killed vortexx2 and frostbyte_r killed milo_pr, so one player is down on each side.
ALIVE = {"blossom": [(0, True), (2, False)], "sky": [(5, False), (6, True)]}
GRAPPLE = {"charges": 2, "max": 3}

ICONS2["katana"] = ("0 0 64 16",
    '<path d="M2 8.6C14 7.4 28 6.2 40.5 5.4L43 9.6C30 10 15 10.6 2.4 11Z"/>'
    '<rect x="41.5" y="2" width="3.4" height="12" rx="1.2"/><rect x="45" y="5.6" width="17" height="5" rx="2"/>')
ICONS2["aim"] = ("0 0 32 32",
    '<path fill-rule="evenodd" d="M16 2a14 14 0 1 1 0 28a14 14 0 1 1 0-28zm0 5.2a8.8 8.8 0 1 0 0 17.6a8.8 8.8 0 1 0 0-17.6z"/>'
    '<rect x="14.8" y="7" width="2.4" height="6.5" rx="1"/><rect x="14.8" y="18.5" width="2.4" height="6.5" rx="1"/>'
    '<rect x="7" y="14.8" width="6.5" height="2.4" rx="1"/><rect x="18.5" y="14.8" width="6.5" height="2.4" rx="1"/>')
ICONS2["menu"] = ("0 0 32 32", '<rect x="5" y="7" width="22" height="4.4" rx="1.6"/><rect x="5" y="14" width="22" height="4.4" rx="1.6"/><rect x="5" y="21" width="22" height="4.4" rx="1.6"/>')


def katana_icon(w=64, h=16):
    return f'<svg width="{w}" height="{h}" viewBox="0 0 64 16" fill="currentColor" style="display:inline-block;flex:none">{ICONS2["katana"][1]}</svg>'


def slot_icon(g, w=64, h=30):
    if g == "katana":
        return katana_icon(int(w * 1.15), int(h * 0.62))
    if g == "duck":
        g = "revolver"
    return f'<i style="display:inline-block;width:{w}px;height:{h}px;background:currentColor;-webkit-mask-image:url(../img/guns/{g}_side.png);-webkit-mask-size:contain;-webkit-mask-repeat:no-repeat;-webkit-mask-position:center"></i>'


def alive_heads(team, size=30, gap=6):
    out = []
    for idx, alive in ALIVE[team]:
        x = "" if alive else (f'<svg width="{size}" height="{size}" viewBox="0 0 40 40" style="position:absolute;left:0;top:0">'
                              f'<path d="M10 10L30 30M30 10L10 30" stroke="#e0473f" stroke-width="5" stroke-linecap="round"/></svg>')
        out.append(f'<span style="position:relative;display:inline-block;{"" if alive else "filter:grayscale(1);opacity:.65"}">{head(idx, size)}{x}</span>')
    return f'<span style="display:inline-flex;gap:{gap}px">{"".join(out)}</span>'


def grapple_readout(color="#fff", size=30, dim="rgba(255,255,255,.35)"):
    """Grapple charges: the hook plus one bar per charge (the game's HookChargesUI)."""
    bars = "".join(f'<i style="width:{size*0.42:.0f}px;height:{size*0.3:.0f}px;border-radius:2px;background:{color if k < GRAPPLE["charges"] else dim}"></i>' for k in range(GRAPPLE["max"]))
    return f'<span style="display:inline-flex;align-items:center;gap:{size*0.18:.0f}px;color:{color}"><span style="font-size:{size}px;line-height:0">{icon("hook")}</span>{bars}</span>'


# ---------------------------------------------------------------- round 6 (26 Nov)
# Damage that fits six rounds of 4v4 at 100 HP (a team can deal at most ~2,400): about 100 per kill plus chip.
BOARD["teams"] = [
    ("blossom", [("rookshots", 6, 3, 3, "720", 38, True, True), ("Dxnny4K", 5, 4, 4, "610", 52, True, False),
                 ("milo_pr", 4, 4, 2, "470", 71, False, False), ("Kaito_kun7", 2, 4, 5, "290", 44, True, False)]),
    ("sky", [("moth_09", 6, 4, 2, "680", 61, True, False), ("vortexx2", 4, 4, 3, "450", 35, False, False),
             ("frostbyte_r", 4, 4, 4, "430", 88, True, False), ("beanzz", 1, 5, 5, "180", 47, False, False)]),
]
# The player owns VIP (the Wish Duck is equipped), so the shop features a set they don't own: Seraph.
# Price = its skins' whole worth (MONEY.md): Rifle legendary 1,200 + Sniper, Burst, Katana epic 600 each + Pistol rare 300.
HERO = {"name": "SERAPH", "price": "3,300", "img": "seraph_rifle",
        "set": [("Seraph Rifle", "Assault Rifle", "seraph_rifle"), ("Seraph Sniper", "Sniper", "seraph_sniper"),
                ("Seraph Burst", "Burst Rifle", "seraph_burst"), ("Seraph Pistol", "Pistol", "seraph_pistol"),
                ("Seraph Katana", "Katana", "seraph_katana")],
        "copy": "Five skins: the Rifle, Sniper, Burst Rifle, Pistol and Katana."}
DAILY = [  # all coin items; the wallet holds 2,450
    ("star-tricorne", "Star Tricorne", "Hat", "9,000", "coin", "legendary"),
    ("wrap_seigaiha", "Seigaiha", "Wrap", "1,800", "coin", "rare"),
    ("wrap_sakura_storm", "Sakura Storm", "Wrap", "3,600", "coin", "epic"),
    ("wrap_kintsugi", "Kintsugi", "Wrap", "3,600", "coin", "epic"),
]
WALLET_N = 2450


def afford(price):
    return int(price.replace(",", "")) <= WALLET_N


ICONS2["aim"] = ("0 0 32 32", '<rect x="14" y="2" width="4" height="10" rx="1.4"/><rect x="14" y="20" width="4" height="10" rx="1.4"/>'
                 '<rect x="2" y="14" width="10" height="4" rx="1.4"/><rect x="20" y="14" width="10" height="4" rx="1.4"/>')
ICONS2["menu"] = ("0 0 32 32", ''.join(f'<rect x="4" y="{y}" width="6" height="6" rx="1.4"/><rect x="12.5" y="{y+1}" width="15.5" height="4" rx="1.4"/>' for y in (5, 13, 21)))
ICONS2["headshot"] = ("0 0 32 32", '<path fill-rule="evenodd" d="M9 4h14a3 3 0 0 1 3 3v13a3 3 0 0 1-3 3H9a3 3 0 0 1-3-3V7a3 3 0 0 1 3-3zm7 4.5a5.5 5.5 0 1 0 0 11a5.5 5.5 0 1 0 0-11zm0 3a2.5 2.5 0 1 1 0 5a2.5 2.5 0 1 1 0-5z"/><rect x="11" y="24" width="10" height="5" rx="1"/>')
ICONS2["reload"] = ("0 0 32 32", '<path d="M10 4H21L21.5 9.5C22 15 23.5 20 26.5 25L18.5 29C15.5 23.5 13 17 11.5 9.5Z"/><rect x="12" y="1.5" width="8" height="3.5" rx="1.2"/>'
                    '<g fill="rgba(0,0,0,.38)"><rect x="13.4" y="11" width="7" height="2" rx="1" transform="rotate(-12 17 12)"/><rect x="15" y="16.5" width="7" height="2" rx="1" transform="rotate(-20 18.5 17.5)"/></g>')
ICONS2["slide"] = ("0 0 32 32",
    '<rect x="2" y="9" width="7" height="6.6" rx="1.4"/>'
    '<path d="M5.5 15.5L14.5 23.5L11.5 27L2.5 19Z"/>'
    '<rect x="12" y="21" width="16" height="4" rx="1"/><rect x="12" y="25.8" width="16" height="3.6" rx="1"/>'
    '<path d="M8 15.5L4 9" stroke="currentColor" stroke-width="3.6" stroke-linecap="round"/>'
    '<path d="M18 9h8M20 14h8" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" opacity=".6"/>'
    '<path d="M1 31h30" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity=".55"/>')


def grapple_readout(color="#fff", size=30, dim=None):
    """Grapple charges as one number beside the hook (the same on PC and phone)."""
    return f'<span style="display:inline-flex;align-items:center;gap:{size*0.22:.0f}px;color:{color}"><span style="font-size:{size}px;line-height:0">{icon("hook")}</span><span style="font-size:{size*0.85:.0f}px;line-height:1">×{GRAPPLE["charges"]}</span></span>'


def hatted(w=680, cls="", style=""):
    """The previewed Wish Duck wearing the Royal Duck hat it has equipped."""
    return (f'<div class="abs {cls}" style="{style};width:{w}px">'
            f'<img src="../img/items/wish_duck_34.png" style="width:{w}px;display:block;filter:drop-shadow(0 26px 28px rgba(0,0,0,.45))">'
            f'<img src="../img/items/royal-duck.png" style="position:absolute;left:{w*0.30:.0f}px;top:{-w*0.13:.0f}px;width:{w*0.17:.0f}px;transform:rotate(-8deg)"></div>')


def feed_line(a, ta, g, b, tb, hs, size=21, cls=""):
    return (f'<span style="color:{TEAM[ta][0]}">{a}</span>{slot_icon(g, int(size*2.9), int(size*1.3))}'
            + (f'<span style="font-size:{size+3}px;line-height:0;opacity:.92">{icon("headshot")}</span>' if hs else "")
            + f'<span style="color:{TEAM[tb][0]}">{b}</span>')


# ---------------------------------------------------------------- round 7 (26 Nov)
# Rarity reads as a word in the line's own colour: the blue/purple/gold ladder read as Fortnite's
# to every critic. The loot opening keeps the game's rarity colours.
RARITY = {k: "inherit" for k in ("rare", "epic", "legendary", "RARE", "EPIC", "LEGENDARY")}
DAILY_RESET = "7 h 12 m"

# Sliding feet first: a blocky body leaning back on one hand, legs out along the ground.
ICONS2["slide"] = ("0 0 32 32",
    '<g transform="rotate(-42 15 24)"><rect x="11" y="12.5" width="8.5" height="11" rx="0.8"/><rect x="11.7" y="4.2" width="7" height="6.8" rx="1.4"/></g>'
    '<rect x="14.5" y="19.4" width="16.5" height="4.2" rx="0.8"/><rect x="14.5" y="24.2" width="14.5" height="4.2" rx="0.8"/>'
    '<rect x="5.2" y="18.5" width="3.6" height="10.5" rx="0.8" transform="rotate(16 7 24)"/>'
    '<path d="M1 31h30" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity=".55"/>')


def coin_row(c, r, b, h=56, price_cls="", sub_cls="", coin=28):
    """A coin pack as a plain row: the game's coin, the amount, its bonus, the Robux price."""
    return (f'<div class="flexc" style="height:{h}px;gap:14px">{cur("coin", coin)}'
            f'<span style="min-width:120px">{c}</span>'
            f'<span class="{sub_cls}" style="flex:1;font-size:.72em">{("+" + b) if b else ""}</span>'
            f'<span class="flexc {price_cls}" style="gap:6px">{rbx()}{r}</span></div>')


def scores_tab(bg, fg, size=13, radius="0 0 6px 6px", extra=""):
    """Phone: the score plate is the scoreboard button; a pull tab under it says so."""
    return (f'<div style="margin:0 auto;width:max-content;padding:1px 10px 3px;background:{bg};color:{fg};'
            f'font-size:{size}px;line-height:1.3;border-radius:{radius};{extra}">Scores</div>')


def party_mark(h=100, color="var(--a)", label_color=None, left=-30):
    """The party bracket, labelled: one line joining the rows of players in your party."""
    lc = label_color or color
    return (f'<i style="position:absolute;left:{left}px;top:12px;width:9px;height:{h}px;border:3px solid {color};border-right:none;border-radius:4px 0 0 4px"></i>'
            f'<span style="position:absolute;left:{left - 22}px;top:{12 + h/2:.0f}px;transform:translate(-50%,-50%) rotate(-90deg);'
            f'font-size:13px;letter-spacing:.06em;color:{lc};white-space:nowrap">PARTY</span>')


def set_shot(w=1000, h=380):
    """The five Seraph skins laid out flat together at their true relative sizes (knolled), not a thumbnail strip."""
    s = w / 1000
    parts = [  # (img, left, top, width)
        ("seraph_sniper", 0, 6, 590), ("seraph_katana", 610, 30, 390),
        ("seraph_rifle", 20, 150, 450), ("seraph_burst", 480, 176, 350), ("seraph_pistol", 870, 196, 122),
    ]
    imgs = "".join(f'<img src="../img/items/{i}.png" style="position:absolute;left:{l*s:.0f}px;top:{t*s:.0f}px;width:{wd*s:.0f}px;'
                   f'filter:drop-shadow(0 {10*s:.0f}px {10*s:.0f}px rgba(0,0,0,.42))">' for i, l, t, wd in parts)
    return f'<div style="position:relative;width:{w}px;height:{h}px">{imgs}</div>'


def heads_col(team, size=26, gap=4):
    """The alive heads stacked, to sit inside a team's score tile."""
    return alive_heads(team, size, gap).replace("display:inline-flex;", "display:inline-flex;flex-direction:column;", 1)


SHOP_TABS = ["FEATURED", "SKINS", "WRAPS", "HATS", "SETS"]


def sil_even(g, h=28, maxw=110):
    """A gun silhouette at one height for every gun (narrower only if it would pass maxw), on one baseline."""
    from PIL import Image
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "guns", f"{g}_side.png")
    try:
        im = Image.open(p)
        bb = im.getchannel("A").getbbox() or (0, 0, im.width, im.height)
        asp = (bb[2] - bb[0]) / max(1, bb[3] - bb[1])
    except Exception:
        asp = 2.5
    w = h * asp
    hh = h
    if w > maxw:
        w, hh = maxw, maxw / asp
    return (f'<i style="display:inline-block;width:{w:.0f}px;height:{hh:.0f}px;margin-top:{h - hh:.0f}px;background:currentColor;'
            f'-webkit-mask-image:url(../img/guns/{g}_side.png);-webkit-mask-size:100% 100%;-webkit-mask-repeat:no-repeat"></i>')



# ---------------------------------------------------------------- round 8 (26 Nov)
# Our own coin and ticket marks (the star coin read as simulator clipart, and both blurred to dots
# at HUD sizes): a blocky square-holed coin and a notched crate ticket, drawn as flat shapes.
COIN_SVG = ('<svg viewBox="0 0 24 24" width="{s}" height="{s}" style="flex:none;display:inline-block;filter:drop-shadow(0 1px 1.5px rgba(0,0,0,.4))">'
            '<circle cx="12" cy="12" r="11" fill="#e2ad2f"/><circle cx="12" cy="12" r="10" fill="none" stroke="#9c6b16" stroke-width="2"/>'
            '<circle cx="12" cy="12" r="6.6" fill="none" stroke="#b9851f" stroke-width="1.4"/><rect x="9.2" y="9.2" width="5.6" height="5.6" rx=".6" fill="#6e4a10"/></svg>')
TICKET_SVG = ('<svg viewBox="0 0 32 22" width="{w}" height="{h}" style="flex:none;display:inline-block;filter:drop-shadow(0 1px 1.5px rgba(0,0,0,.4))">'
              '<path d="M3 2h26a1 1 0 0 1 1 1v5.2a2.9 2.9 0 0 0 0 5.6V19a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1v-5.2a2.9 2.9 0 0 0 0-5.6V3a1 1 0 0 1 1-1z" fill="#efdcaa" stroke="#6d5a2c" stroke-width="1.6"/>'
              '<path d="M11 4.5v13" stroke="#6d5a2c" stroke-width="1.4" stroke-dasharray="2 1.8"/><rect x="15" y="7.5" width="10" height="2.4" rx="1" fill="#6d5a2c"/><rect x="15" y="12" width="7" height="2.4" rx="1" fill="#6d5a2c"/></svg>')


def cur(kind="coin", size=24, cls="cur"):
    if kind == "coin":
        return COIN_SVG.format(s=size)
    return TICKET_SVG.format(w=round(size * 1.05), h=round(size * 0.72))


# A grappling hook you can read at 20 px: ring, shaft, two barbed tines and a point.
ICONS2["hook"] = ("0 0 32 32",
    '<circle cx="16" cy="4.6" r="3" fill="none" stroke="currentColor" stroke-width="2.6"/>'
    '<rect x="14.3" y="7.2" width="3.4" height="16" rx="1"/>'
    '<path d="M16 22.5C12 27.5 5.5 25.5 5 17.5M16 22.5C20 27.5 26.5 25.5 27 17.5" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"/>'
    '<path d="M2.4 18.6L5 12.2L8.6 17.4Z"/><path d="M29.6 18.6L27 12.2L23.4 17.4Z"/><path d="M14.2 23L16 29.5L17.8 23Z"/>')
# Jumping: the blocky figure in the air, knees up, lifted off its ground line.
ICONS2["jump"] = ("0 0 32 32",
    '<rect x="12.5" y="0.6" width="7" height="6.4" rx="1.4"/><rect x="11.5" y="7.6" width="9" height="9.2" rx="0.8"/>'
    '<rect x="6.4" y="1.6" width="4" height="9.5" rx="0.8" transform="rotate(-24 8.4 6.4)"/><rect x="21.6" y="1.6" width="4" height="9.5" rx="0.8" transform="rotate(24 23.6 6.4)"/>'
    '<rect x="10.4" y="17" width="4.4" height="6.4" rx="0.8" transform="rotate(14 12.6 17)"/><rect x="17.2" y="17" width="4.4" height="6.4" rx="0.8" transform="rotate(-14 19.4 17)"/>'
    '<path d="M7 31h18" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" opacity=".6"/>'
    '<path d="M12 26.5v1.8M20 26.5v1.8" stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity=".6"/>')

# Stats say what they measure; mastery isn't at the same fill as the XP bar.
STATS = [("Damage", "33", 0.55), ("Headshot dmg", "79", 0.70), ("Fire rate", "2.5/s", 0.25), ("Magazine", "6", 0.20)]
MASTERY = {"level": 7, "xp": "2,250", "next": "3,000", "frac": 0.75}
# The scoreboard is another match (4v4 Spooky Forest): its dead players are not the match HUD's.
BOARD["teams"] = [
    ("blossom", [("rookshots", 6, 3, 3, "720", 38, True, True), ("Dxnny4K", 5, 4, 4, "610", 52, True, False),
                 ("milo_pr", 4, 4, 2, "470", 71, True, False), ("Kaito_kun7", 2, 4, 5, "290", 44, False, False)]),
    ("sky", [("moth_09", 6, 4, 2, "680", 61, False, False), ("vortexx2", 4, 4, 3, "450", 35, True, False),
             ("frostbyte_r", 4, 4, 4, "430", 88, True, False), ("beanzz", 1, 5, 5, "180", 47, False, False)]),
]
# You are in a party of two (Dxnny4K), queued for 2v2 ranked, which is the match on the HUD.
PARTY_N = "2/4"
MODE_LABEL = "2V2 RANKED"
RATING = "1,482"


def party_mark2(h=100, color="var(--a)", label="Party", left=-30, size=14):
    """The party bracket with its label in the direction's own case."""
    return (f'<i style="position:absolute;left:{left}px;top:12px;width:9px;height:{h}px;border:3px solid {color};border-right:none;border-radius:4px 0 0 4px"></i>'
            f'<span style="position:absolute;left:{left - 20}px;top:{12 + h/2:.0f}px;transform:translate(-50%,-50%) rotate(-90deg);'
            f'font-size:{size}px;color:{color};white-space:nowrap">{label}</span>')


# what each player on the Tab board is holding right now
HOLDING = {"rookshots": "ar", "Dxnny4K": "sniper", "milo_pr": "smg", "Kaito_kun7": "shotgun",
           "moth_09": "dmr", "vortexx2": "burst", "frostbyte_r": "ar", "beanzz": "lmg"}
NEXT_QUEST = ("Land 6 headshots", 4, 6)


def coin_stack(n, size=26):
    """1 to 4 of our coins, overlapped: a bigger pack is a taller stack."""
    return (f'<span style="position:relative;display:inline-block;width:{size + 6 * (n - 1)}px;height:{size + 5 * (n - 1)}px;flex:none">'
            + "".join(f'<span style="position:absolute;left:{6 * k}px;top:{5 * (n - 1 - k)}px">{cur("coin", size)}</span>' for k in range(n)) + '</span>')
