#!/usr/bin/env python3
"""Render an architecture-diagram HTML file to a PNG.

The diagrams are self-contained HTML/CSS. This drives a headless browser to
render one and screenshot it, cropped tight to the diagram at 2x for crisp
output. Three backends, auto-selected in this order (override with --backend):

  1. playwright        Playwright Python package + Chromium (element crop, DSF).
                         pip install playwright && playwright install chromium
  2. playwright-cli    The Homebrew `playwright-cli` tool (element crop; served
                         over a short-lived local HTTP server because it blocks
                         file:// URLs, with CSS zoom for the 2x scale).
                         brew install playwright-cli && playwright-cli install-browser
  3. browser           An installed Chrome / Chromium / Edge / Brave binary.
                         Over-renders, then trims whitespace with Pillow.

Accepts:
  - a full .html file (your rendered diagram, or gallery.html with --full-page)
  - a style .md file from styles/ (the "## Template" block is extracted)
  - a bare HTML fragment (just the <div> ...); it gets wrapped automatically

Usage:
  python3 scripts/html_to_png.py diagram.html
  python3 scripts/html_to_png.py styles/steel-blue.md -o steel-blue.png
  python3 scripts/html_to_png.py gallery.html --full-page --max-height 12000
  python3 scripts/html_to_png.py diagram.html --scale 3 --backend playwright-cli

Fonts: rendering uses the OS font stack, so run on macOS/Windows to get the
serif / monospace / Helvetica voices. Headless Linux lacks those fonts and
substitutes — install matching fonts or render on a desktop OS.
"""
import argparse
import functools
import http.server
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import threading

FRAGMENT_WRAPPER = (
    "<!doctype html><html><head><meta charset='utf-8'>"
    "<style>*{box-sizing:border-box}"
    "body{margin:0;padding:__PAD__px;background:#ffffff;display:inline-block}"
    "</style></head><body>__BODY__</body></html>"
)

# Chrome/Chromium-family binaries for the `browser` backend.
BROWSER_CANDIDATES = [
    os.environ.get("CHROME") or "",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "chromium", "chromium-browser", "google-chrome", "google-chrome-stable",
    "microsoft-edge", "brave-browser",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


# --------------------------------------------------------------------------- #
# HTML preparation
# --------------------------------------------------------------------------- #
def load_html(path: pathlib.Path, padding: int) -> str:
    """Read the file and normalise it into a renderable HTML page."""
    raw = path.read_text()
    # Style files keep the diagram after a "## Template" heading.
    if "## Template" in raw and (path.suffix.lower() == ".md" or "<html" not in raw.lower()):
        raw = raw.split("## Template", 1)[1].strip()
    # Wrap a bare fragment so it renders as a standalone page.
    low = raw.lower()
    if "<html" not in low and "<body" not in low:
        raw = FRAGMENT_WRAPPER.replace("__PAD__", str(padding)).replace("__BODY__", raw)
    return raw


def inject_zoom(html: str, scale: float) -> str:
    """Inflate the layout with CSS zoom so a DSF-1 backend still captures at scale."""
    if scale == 1:
        return html
    tag = f"<style>:root{{zoom:{scale}}}</style>"
    low = html.lower()
    i = low.find("</head>")
    if i != -1:
        return html[:i] + tag + html[i:]
    i = low.find("<body")
    if i != -1:
        j = html.find(">", i)
        if j != -1:
            return html[:j + 1] + tag + html[j + 1:]
    return tag + html


# --------------------------------------------------------------------------- #
# Backend: Playwright Python package
# --------------------------------------------------------------------------- #
def render_playwright(html, out, width, scale, selector, full_page) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context(
            device_scale_factor=scale,
            viewport={"width": width, "height": 900},
        ).new_page()
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(150)  # let gradients / fonts settle
        target = None if full_page else page.query_selector(selector)
        if target is not None:
            target.screenshot(path=str(out))
        else:
            page.screenshot(path=str(out), full_page=True)
        browser.close()


# --------------------------------------------------------------------------- #
# Backend: playwright-cli (Homebrew) — serve over HTTP, element-crop, CSS zoom
# --------------------------------------------------------------------------- #
class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # silence request logging
        pass


def _serve(directory: str):
    handler = functools.partial(_QuietHandler, directory=directory)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def _pw_cli(binary, session, args, timeout=90) -> str:
    proc = subprocess.run([binary, f"-s={session}", *args],
                          capture_output=True, text=True, timeout=timeout)
    combined = proc.stdout + proc.stderr
    if "### Error" in combined:
        raise RuntimeError(combined.strip())
    return combined


def render_playwright_cli(binary, html, out, width, scale, selector,
                          full_page, max_height) -> None:
    html = inject_zoom(html, scale)
    session = f"arch2png-{os.getpid()}"
    tmpdir = tempfile.mkdtemp(prefix="arch2png-")
    (pathlib.Path(tmpdir) / "index.html").write_text(html)
    httpd, port = _serve(tmpdir)
    win_w = int(width * scale) + 40
    win_h = max_height if full_page else 2200
    try:
        _pw_cli(binary, session, ["open", f"http://127.0.0.1:{port}/index.html"])
        _pw_cli(binary, session, ["resize", str(win_w), str(win_h)])
        shot = ["screenshot", f"--filename={out}"]
        if full_page:
            _pw_cli(binary, session, shot + ["--full-page"])
        else:
            try:
                _pw_cli(binary, session, [shot[0], selector, shot[1]])
            except RuntimeError as e:
                if "does not match" not in str(e):
                    raise
                print(f"warning: selector '{selector}' not found; capturing full page",
                      file=sys.stderr)
                _pw_cli(binary, session, shot + ["--full-page"])
        if not pathlib.Path(out).exists():
            raise RuntimeError("playwright-cli did not produce a screenshot")
    finally:
        try:
            _pw_cli(binary, session, ["close"], timeout=30)
        except Exception:
            pass
        httpd.shutdown()
        httpd.server_close()
        shutil.rmtree(tmpdir, ignore_errors=True)


# --------------------------------------------------------------------------- #
# Backend: direct Chrome/Chromium binary
# --------------------------------------------------------------------------- #
def find_browser() -> "str | None":
    for cand in BROWSER_CANDIDATES:
        if not cand:
            continue
        if os.path.isabs(cand) and os.access(cand, os.X_OK):
            return cand
        found = shutil.which(cand)
        if found:
            return found
    return None


def _trim_whitespace(out: pathlib.Path) -> None:
    """Crop uniform white margins so the PNG hugs the diagram."""
    try:
        from PIL import Image, ImageChops
    except ImportError:
        print("note: Pillow not installed; PNG not trimmed "
              "(pip install pillow for a tight crop)", file=sys.stderr)
        return
    im = Image.open(out).convert("RGB")
    bg = Image.new("RGB", im.size, (255, 255, 255))
    bbox = ImageChops.difference(im, bg).getbbox()
    if bbox:
        im.crop(bbox).save(out)


def render_browser(binary, html, out, width, scale, max_height, full_page) -> None:
    height = max_height if full_page else min(max_height, 4000)
    fd, tmp = tempfile.mkstemp(suffix=".html")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(html)
        cmd = [
            binary, "--headless=new", "--disable-gpu", "--no-sandbox",
            "--hide-scrollbars", "--default-background-color=FFFFFFFF",
            f"--force-device-scale-factor={scale}",
            f"--window-size={width},{height}",
            "--virtual-time-budget=1500",
            f"--screenshot={out}", pathlib.Path(tmp).as_uri(),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if not out.exists():
            sys.stderr.write(proc.stderr)
            raise RuntimeError("browser did not produce a screenshot")
    finally:
        os.unlink(tmp)
    _trim_whitespace(out)


# --------------------------------------------------------------------------- #
# Backend selection
# --------------------------------------------------------------------------- #
def have_playwright() -> bool:
    try:
        import playwright.sync_api  # noqa: F401
        return True
    except ImportError:
        return False


def find_playwright_cli() -> "str | None":
    return shutil.which(os.environ.get("PLAYWRIGHT_CLI") or "playwright-cli")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Render an HTML diagram to PNG via a headless browser.")
    ap.add_argument("input", help="HTML file, styles/*.md, or an HTML fragment")
    ap.add_argument("-o", "--output", help="Output PNG path (default: <input>.png)")
    ap.add_argument("--backend", default="auto",
                    choices=["auto", "playwright", "playwright-cli", "browser"],
                    help="Rendering backend (default: auto)")
    ap.add_argument("--width", type=int, default=1280,
                    help="Viewport width in px (default 1280)")
    ap.add_argument("--scale", type=float, default=2.0,
                    help="Pixel scale — 2 = retina (default 2)")
    ap.add_argument("--padding", type=int, default=16,
                    help="Padding around a wrapped fragment (default 16)")
    ap.add_argument("--max-height", type=int, default=6000,
                    help="Render height for full-page / browser backends (raise for gallery.html)")
    ap.add_argument("--selector", default="body > div",
                    help="Element to crop to (default: first body div); ignored with --full-page")
    ap.add_argument("--full-page", action="store_true",
                    help="Capture the whole page instead of cropping to the diagram")
    args = ap.parse_args()

    src = pathlib.Path(args.input)
    if not src.exists():
        print(f"error: no such file: {src}", file=sys.stderr)
        return 1
    out = pathlib.Path(args.output) if args.output else src.with_suffix(".png")

    html = load_html(src, args.padding)

    use = args.backend
    if use == "auto":
        if have_playwright():
            use = "playwright"
        elif find_playwright_cli():
            use = "playwright-cli"
        else:
            use = "browser"

    if use == "playwright":
        if not have_playwright():
            print("error: --backend playwright but the Playwright package is not installed.\n"
                  "  pip install playwright && playwright install chromium", file=sys.stderr)
            return 2
        render_playwright(html, out, args.width, args.scale, args.selector, args.full_page)
    elif use == "playwright-cli":
        binary = find_playwright_cli()
        if not binary:
            print("error: playwright-cli not found on PATH.\n"
                  "  brew install playwright-cli && playwright-cli install-browser", file=sys.stderr)
            return 2
        render_playwright_cli(binary, html, out, args.width, args.scale,
                              args.selector, args.full_page, args.max_height)
    else:
        binary = find_browser()
        if not binary:
            print("error: no headless browser found.\n"
                  "  Install Chrome/Chromium/Edge, or `brew install playwright-cli`, or\n"
                  "  pip install playwright && playwright install chromium", file=sys.stderr)
            return 2
        render_browser(binary, html, out, args.width, args.scale, args.max_height, args.full_page)

    print(f"wrote {out} (backend: {use})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
