#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control Center — Standalone Launcher
=====================================
Serves index.html and all subdirectories (AI_JobHunter/, Job_Dashboard/)
via a local HTTP server, then opens the Control Center in a native desktop
window using pywebview.

Serving over HTTP (rather than file://) is required so that relative links
to subdirectory HTML files resolve correctly. The server is rooted at the
project folder, so all child apps are reachable via their relative paths,
and each app's "Back to Main" link (../index.html, ../../index.html) also
resolves correctly without any special handling.

Config injection:
    config.json is read from next to the .exe at startup. If found, the
    config values are served as a standalone JS file at /__cc_config.js,
    and a <script src="/__cc_config.js"> tag is injected into every HTML
    response. Serving config as a separate file (rather than inlining it)
    avoids regex and special-character parse interference with the page's
    own scripts.

    The Dashboard app has inbuilt config and does not use config.json.

The server runs in a background thread and shuts down automatically when
the window is closed.

Requirements (install once):
    pip install pywebview

Usage:
    python launch_control_center.py
    python launch_control_center.py --width 1280 --height 800
    python launch_control_center.py --debug
"""

import argparse
import http.server
import json
import os
import socketserver
import sys
import threading


# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------
try:
    import webview  # pywebview
except ImportError:
    print(
        "\n[ERROR] pywebview is not installed.\n"
        "Install it with:\n\n"
        "    pip install pywebview\n"
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Keys read from config.json — mirrors the JobHunter launcher
# home_path: full path to the project root index.html on disk, allowing source
# edits to be picked up on next launch without a rebuild (same pattern as
# html_path in the JobHunter config)
CONFIG_KEYS = ("gemini_api_key", "gdrive_webhook", "export_webhook", "home_path")

# Virtual path the config script is served at — unlikely to clash with any
# real file in the project tree
CONFIG_SCRIPT_PATH = "/__cc_config.js"


def exe_dir() -> str:
    """
    Return the directory containing this script (or the compiled .exe).
    sys.argv[0] is used when frozen because __file__ points into the
    PyInstaller temp folder rather than the .exe's actual location.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.dirname(os.path.abspath(__file__))


def load_config() -> dict:
    """
    Read config.json from next to the .exe.
    Returns a dict of whichever CONFIG_KEYS are present and non-empty.
    Returns an empty dict silently if the file is absent (Dashboard-only
    use is perfectly valid without a config).
    """
    config_path = os.path.join(exe_dir(), "config.json")
    if not os.path.isfile(config_path):
        print("[INFO] No config.json found — JobHunter API keys will use page defaults.")
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"[WARN] config.json is not valid JSON ({exc}) — using page defaults.")
        return {}
    config = {k: raw[k] for k in CONFIG_KEYS if k in raw and str(raw[k]).strip()}
    print(f"[INFO] Config loaded. Keys found: {', '.join(config.keys()) or '(none)'}")
    return config


def build_config_script(config: dict) -> str:
    """
    Build a self-contained JS file content string that:
      - Writes webhook values into localStorage before window.onload reads them
      - Wraps window.fetch to substitute the Gemini API key on outgoing requests

    This is served as /__cc_config.js and referenced via <script src> rather
    than inlined into the HTML, so its content is never parsed as part of the
    HTML document. This prevents regex literals and special characters in the
    script from interfering with the page's own script parsing.

    Returns an empty string if config is empty (script file won't be served).
    """
    if not config:
        return ""

    lines = ["(function () {"]

    for cfg_key, ls_key in [("gdrive_webhook", "gdrive_webhook"),
                             ("export_webhook",  "export_webhook")]:
        if cfg_key in config:
            lines.append(
                f"  localStorage.setItem({json.dumps(ls_key)}, {json.dumps(config[cfg_key])});"
            )

    if "gemini_api_key" in config:
        key  = json.dumps(config["gemini_api_key"])
        base = json.dumps("https://generativelanguage.googleapis.com")
        lines += [
            f"  var _k = {key}, _b = {base}, _f = window.fetch.bind(window);",
            "  window.fetch = function (url, opts) {",
            "    if (typeof url === 'string' && url.indexOf(_b) === 0) {",
            "      url = url.indexOf('key=') !== -1",
            "        ? url.replace(/([?&]key=)[^&]*/, '$1' + _k)",
            "        : url + (url.indexOf('?') === -1 ? '?' : '&') + 'key=' + _k;",
            "    }",
            "    return _f(url, opts);",
            "  };",
        ]

    lines += [
        "  console.log('[config] Script executed.');",
        "  console.log('[config] gdrive_webhook =', localStorage.getItem('gdrive_webhook'));",
        "  console.log('[config] export_webhook =', localStorage.getItem('export_webhook'));",
        "  console.log('[config] fetch wrapper active:', window.fetch.toString().indexOf('_k') !== -1);",
    ]
    lines.append("}());")
    return "\n".join(lines)


def resolve_project_dir(config: dict) -> str:
    """
    Locate the folder that contains index.html.

    Search order:
        1. home_path from config.json (full path to index.html on disk) —
           allows source edits to be picked up on next launch without a rebuild
        2. PyInstaller bundle temp folder (sys._MEIPASS/app/) — .exe builds only
        3. Same directory as this script / .exe
        4. Current working directory

    Returns the absolute path to the project root.
    """
    # 1. home_path from config.json — highest priority so live source edits
    #    are always picked up over the bundled copy
    if config.get("home_path"):
        home = os.path.abspath(config["home_path"])
        # home_path may point to index.html itself or its parent folder
        if os.path.isfile(home):
            folder = os.path.dirname(home)
            print(f"[INFO] home_path : {home} (from config.json)")
            return folder
        elif os.path.isfile(os.path.join(home, "index.html")):
            print(f"[INFO] home_path : {home} (from config.json)")
            return home
        else:
            print(f"[WARN] home_path in config.json not found: {home} — falling back.")

    candidates = []

    # 2. PyInstaller bundle: entire project tree extracted to sys._MEIPASS/app/
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(os.path.join(sys._MEIPASS, "app"))

    # 3 & 4. Script directory and cwd
    candidates.append(exe_dir())
    candidates.append(os.getcwd())

    for folder in candidates:
        if os.path.isfile(os.path.join(folder, "index.html")):
            return folder

    searched = "\n  ".join(dict.fromkeys(candidates))
    print(
        f"\n[ERROR] Could not find index.html.\n"
        f"Searched:\n  {searched}\n\n"
        "Place index.html next to this script, or set \'home_path\' in config.json.\n"
    )
    sys.exit(1)


def start_server(project_dir: str, port: int, config_js: str) -> int:
    """
    Start a local HTTP server rooted at project_dir in a background thread.

    Two responsibilities beyond normal static file serving:
      1. Serve config_js at CONFIG_SCRIPT_PATH (/__cc_config.js) — an in-memory
         virtual file that never touches disk.
      2. Inject a <script src="/__cc_config.js"> tag into every HTML response,
         placed immediately before </head> so it loads before any page scripts.
         Only active when config_js is non-empty.

    If the requested port is already in use, tries the next port up to 10
    times before giving up.

    Returns the port the server successfully bound to.
    """
    config_js_bytes = config_js.encode("utf-8") if config_js else b""
    script_tag      = f'<script src="{CONFIG_SCRIPT_PATH}"></script>\n'

    class ControlCenterHandler(http.server.SimpleHTTPRequestHandler):

        def log_message(self, format, *args):
            pass  # suppress per-request console noise

        def do_GET(self):
            path = self.path.split("?")[0]

            # --- Virtual file: serve the config script from memory ---
            # No disk read needed; content was built once at startup.
            if path == CONFIG_SCRIPT_PATH:
                self.send_response(200)
                self.send_header("Content-Type",   "application/javascript; charset=utf-8")
                self.send_header("Content-Length", str(len(config_js_bytes)))
                self.send_header("Cache-Control",  "no-store")
                self.end_headers()
                self.wfile.write(config_js_bytes)
                return

            # --- HTML files: inject <script src> tag before </head> ---
            # All other file types (JS, CSS, images) pass through unchanged,
            # so scanner.js and other app scripts are never touched.
            if config_js and (path.endswith(".html") or path == "/"):
                rel  = path.lstrip("/") or "index.html"
                full = os.path.join(project_dir, rel)
                if os.path.isfile(full):
                    try:
                        with open(full, "r", encoding="utf-8") as fh:
                            html = fh.read()

                        # Inject before </head> so the config is available
                        # to all scripts in <body> when they execute
                        insert_at = html.lower().find("</head>")
                        if insert_at != -1:
                            html = html[:insert_at] + script_tag + html[insert_at:]

                        body = html.encode("utf-8")
                        self.send_response(200)
                        self.send_header("Content-Type",   "text/html; charset=utf-8")
                        self.send_header("Content-Length", str(len(body)))
                        self.send_header("Cache-Control",  "no-store")
                        self.end_headers()
                        self.wfile.write(body)
                        return
                    except Exception as exc:
                        self.send_error(500, str(exc))
                        return

            # --- Everything else: default static file serving ---
            super().do_GET()

    for attempt in range(10):
        try_port = port + attempt
        try:
            httpd = socketserver.TCPServer(("127.0.0.1", try_port), ControlCenterHandler)
            httpd.allow_reuse_address = True

            def serve():
                os.chdir(project_dir)
                httpd.serve_forever()

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()

            # Brief pause so the chdir completes before the window tries to load
            import time; time.sleep(0.05)

            print(f"[INFO] Server    : http://127.0.0.1:{try_port}  ->  {project_dir}")
            return try_port

        except OSError:
            print(f"[INFO] Port {try_port} in use, trying {try_port + 1}...")

    print("\n[ERROR] Could not find a free port after 10 attempts.\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Launch the Workspace Control Center as a desktop app."
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8100,
        help="Starting port for the local HTTP server (default: 8100)",
    )
    parser.add_argument(
        "--width", "-W",
        type=int,
        default=900,
        help="Window width in pixels (default: 900)",
    )
    parser.add_argument(
        "--height", "-H",
        type=int,
        default=600,
        help="Window height in pixels (default: 600)",
    )
    parser.add_argument(
        "--no-resizable",
        action="store_true",
        help="Disable window resizing",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Open browser DevTools alongside the window",
    )
    args = parser.parse_args()

    config    = load_config()
    config_js = build_config_script(config)

    project_dir = resolve_project_dir(config)

    print(f"[INFO] Project   : {project_dir}")
    print(f"[INFO] Window    : {args.width}x{args.height}")
    if config_js:
        print(f"[INFO] Config    : injection active ({len(config_js)} chars) via {CONFIG_SCRIPT_PATH}")
    if args.debug:
        print("[INFO] DevTools  : ON")

    port = start_server(project_dir, args.port, config_js)
    url  = f"http://127.0.0.1:{port}/index.html"

    webview.create_window(
        title="Workspace Control Center",
        url=url,
        width=args.width,
        height=args.height,
        resizable=not args.no_resizable,
        min_size=(700, 500),
    )

    # PYWEBVIEW_DEBUG env var lets build_exe.py bake in debug mode
    # without needing CLI args at runtime (mirrors AIJobHunter pattern)
    force_debug = os.environ.get("PYWEBVIEW_DEBUG", "").lower() in ("1", "true")
    webview.start(debug=args.debug or force_debug)


if __name__ == "__main__":
    main()