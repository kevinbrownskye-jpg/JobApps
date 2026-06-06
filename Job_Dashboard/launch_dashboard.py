#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline Analytics Dashboard - Standalone Launcher
===================================================
Serves the project folder via a local HTTP server, then opens
dashboard.html in a native desktop window using pywebview.

Serving over HTTP (rather than file://) is required so that the
dashboard can load its JS modules from the js/ subfolder using
relative paths. The server runs in a background thread and shuts
down automatically when the window is closed.

The HTML file and js/ folder are never modified by this script.

Requirements (install once):
    pip install pywebview

Usage:
    python launch_dashboard.py
    python launch_dashboard.py --file /path/to/dashboard.html
    python launch_dashboard.py --width 1600 --height 900
    python launch_dashboard.py --debug
"""

import argparse
import os
import sys
import threading
import http.server
import socketserver


# ---------------------------------------------------------------------------
# Dependency check - print a friendly message before anything else fails
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

def exe_dir() -> str:
    """
    Return the directory that contains this script (or the compiled .exe).
    When frozen by PyInstaller, __file__ is unreliable, so we use sys.argv[0].
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.dirname(os.path.abspath(__file__))


def resolve_project_dir(cli_path: str | None) -> tuple[str, str]:
    """
    Return (project_dir, html_filename) for the dashboard.

    Search order:
        1. --file argument (if provided on the command line)
        2. PyInstaller bundle temp folder (sys._MEIPASS/assets/) - .exe builds only
        3. Same directory as this script / .exe
        4. Current working directory

    The HTTP server is rooted at project_dir, so the js/ subfolder
    is automatically reachable via relative paths in the HTML.
    """
    candidates = []

    # 1. Explicit --file flag - serve from that file's parent directory
    if cli_path:
        abs_path = os.path.abspath(cli_path)
        candidates.append((os.path.dirname(abs_path), os.path.basename(abs_path)))

    # 2. PyInstaller bundle: assets/ is extracted to sys._MEIPASS/assets/
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidates.append(
            (os.path.join(sys._MEIPASS, "assets"), "dashboard.html")
        )

    # 3 & 4. Script directory and current working directory
    candidates.append((exe_dir(), "dashboard.html"))
    candidates.append((os.getcwd(), "dashboard.html"))

    for project_dir, html_file in candidates:
        if os.path.isfile(os.path.join(project_dir, html_file)):
            return project_dir, html_file

    # Nothing found - show exactly where we looked
    searched = "\n  ".join(
        os.path.join(d, f) for d, f in dict.fromkeys(candidates)
    )
    print(
        # ANONYMIZED: Generalized template verification error messaging
        f"\n[ERROR] Could not find the dashboard template html file.\n"
        f"Expected path: {target_path}\n"
        f"Please verify this file is located next to the main launcher file or inside the build path layout."
    )
    sys.exit(1)


def start_server(project_dir: str, port: int) -> int:
    """
    Start a local HTTP server rooted at project_dir in a background thread.

    If the requested port is already in use, automatically tries the next
    port until a free one is found (up to 10 attempts).

    Returns the port the server successfully bound to.
    """
    # Silence the default per-request log lines in the console
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # suppress request logging

    for attempt in range(10):
        try_port = port + attempt
        try:
            httpd = socketserver.TCPServer(("", try_port), QuietHandler)
            httpd.allow_reuse_address = True

            # Change into the project directory so the server roots there;
            # the original cwd is restored after the server thread starts
            original_cwd = os.getcwd()

            def serve():
                os.chdir(project_dir)
                httpd.serve_forever()

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()

            # Give the thread a moment to chdir before the main thread proceeds
            import time; time.sleep(0.05)

            print(f"[INFO] Server    : http://localhost:{try_port} -> {project_dir}")
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
        description="Launch the Pipeline Analytics Dashboard as a desktop app."
    )
    parser.add_argument(
        "--file", "-f",
        metavar="PATH",
        help="Path to dashboard.html (default: same folder as this script)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Starting port for the local HTTP server (default: 8000)",
    )
    parser.add_argument(
        "--width", "-W",
        type=int,
        default=1280,
        help="Window width in pixels (default: 1280)",
    )
    parser.add_argument(
        "--height", "-H",
        type=int,
        default=800,
        help="Window height in pixels (default: 800)",
    )
    parser.add_argument(
        "--no-resizable",
        action="store_true",
        help="Disable window resizing",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Open the browser developer tools panel alongside the window",
    )
    args = parser.parse_args()

    project_dir, html_file = resolve_project_dir(args.file)

    print(f"[INFO] Project   : {project_dir}")
    print(f"[INFO] Window    : {args.width}x{args.height}")
    if args.debug:
        print("[INFO] DevTools  : ON")

    # Start HTTP server and get the port it bound to
    port = start_server(project_dir, args.port)
    url  = f"http://localhost:{port}/{html_file}"

    # Create the native desktop window pointed at the local server
    webview.create_window(
        # ANONYMIZED: Updated specialized branding string to a generic template framework label
        title="Application Tracking Metrics Dashboard",
        url=url,
        width=args.width,
        height=args.height,
        resizable=not args.no_resizable,
        min_size=(800, 600),
    )

    # Start the GUI event loop; server thread is daemon so it exits with the window
    webview.start(debug=args.debug)


if __name__ == "__main__":
    main()
