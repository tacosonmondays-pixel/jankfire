"""Build the UI mock frames: writes html/<dir>_<frame>.html and renders png/<dir>_<frame>.png with
headless Chrome. Usage: python mocks.py [a b c d] [--frames hub,match,...] [--no-render]

Needs: Chrome (or Edge), Python with Pillow, Roblox Studio installed (fonts are copied from it)."""
import importlib
import os
import subprocess
import sys

import common

HERE = common.HERE
HTML = os.path.join(HERE, "html")
PNG = os.path.join(HERE, "png")
BROWSERS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
ALL = ["a", "b", "d"]  # C OPEN dropped after critic round 2


def browser():
    for b in BROWSERS:
        if os.path.exists(b):
            return b
    raise SystemExit("no Chrome or Edge found")


def render(html_path, png_path, w, h, scale):
    url = "file:///" + html_path.replace("\\", "/")
    cmd = [browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
           f"--force-device-scale-factor={scale}", f"--window-size={w},{h}", "--virtual-time-budget=6000",
           "--default-background-color=00000000", "--run-all-compositor-stages-before-draw", f"--screenshot={png_path}", url]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dirs = args or ALL
    frames = None
    for a in sys.argv[1:]:
        if a.startswith("--frames="):
            frames = a.split("=", 1)[1].split(",")
    common.setup_fonts()
    os.makedirs(HTML, exist_ok=True)
    os.makedirs(PNG, exist_ok=True)
    for d in dirs:
        mod = importlib.import_module(f"dir_{d}")
        for fname, fn in mod.FRAMES.items():
            if frames and fname not in frames:
                continue
            html = fn()
            hp = os.path.join(HTML, f"{d}_{fname}.html")
            with open(hp, "w", encoding="utf-8") as f:
                f.write(html)
            if "--no-render" in sys.argv:
                continue
            phone = fname == "phone"
            render(hp, os.path.join(PNG, f"{d}_{fname}.png"), 844 if phone else 1920, 390 if phone else 1080, 2 if phone else 1)
            print("rendered", d, fname)


if __name__ == "__main__":
    main()
