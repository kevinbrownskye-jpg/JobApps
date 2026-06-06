#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_exe.py - One-click builder for Pipeline Analytics Dashboard .exe
=======================================================================
Packages launch_dashboard.py + dashboard.html + js/ folder into a
standalone Windows executable using PyInstaller.

Requirements (install once):
    pip install pyinstaller pywebview

Usage:
    python build_exe.py              # folder-based build (faster startup, default)
    python build_exe.py --onefile    # single .exe (easier to share, slower to start)
    python build_exe.py --onedir     # same as default - explicit folder-based build
    python build_exe.py --debug      # keep console window open for troubleshooting

Output:
    dist/PipelineAnalytics/PipelineAnalytics.exe   (--onedir, default)
    dist/PipelineAnalytics.exe                     (--onefile)
"""

import argparse
import os
import shutil
import subprocess
import sys

# ---------------------------------------------------------------------------
# Config - update these if your files or folders have different names
# ---------------------------------------------------------------------------
APP_NAME    = "PipelineAnalytics"
SCRIPT_FILE = "launch_dashboard.py"
HTML_FILE   = "dashboard.html"
JS_FOLDER   = "js"
ICON_FILE   = "dashboard_icon_182989.ico"
# ---------------------------------------------------------------------------


def find_file(filename: str, base_dir: str) -> str:
    """
    Locate a required file in base_dir.
    Exits with a clear error message if the file is not found,
    rather than letting PyInstaller fail with a cryptic traceback.
    """
    path = os.path.join(base_dir, filename)
    if not os.path.isfile(path):
        print(f"\n[ERROR] Required file not found: {path}")
        print(f"  Make sure '{filename}' is in the same folder as this build script.\n")
        sys.exit(1)
    return path


def find_folder(foldername: str, base_dir: str) -> str:
    """
    Locate a required subfolder in base_dir.
    Exits with a clear error message if the folder is not found,
    rather than letting PyInstaller silently omit it from the bundle.
    """
    path = os.path.join(base_dir, foldername)
    if not os.path.isdir(path):
        print(f"\n[ERROR] Required folder not found: {path}")
        print(f"  Make sure the '{foldername}/' folder is in the same folder as this build script.\n")
        sys.exit(1)
    return path


def check_pyinstaller() -> None:
    """Verify PyInstaller is installed before attempting a build."""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print(
            "\n[ERROR] PyInstaller is not installed.\n"
            "Install it with:\n\n"
            "    pip install pyinstaller\n"
        )
        sys.exit(1)


def clean_build_artifacts(base_dir: str) -> None:
    """
    Remove previous build/ and dist/ folders and any leftover .spec file.
    This ensures a clean rebuild and avoids stale cached files causing issues.
    """
    for folder in ("build", "dist"):
        target = os.path.join(base_dir, folder)
        if os.path.isdir(target):
            print(f"[INFO] Removing old {folder}/")
            shutil.rmtree(target)

    spec = os.path.join(base_dir, f"{APP_NAME}.spec")
    if os.path.isfile(spec):
        os.remove(spec)


def build(onefile: bool, debug: bool, base_dir: str) -> None:
    """
    Construct and run the PyInstaller command.

    Parameters
    ----------
    onefile  : True  -> single self-contained .exe
               False -> folder containing .exe + support files (faster startup)
    debug    : True  -> keep the console window visible (useful for troubleshooting)
               False -> hide the console (clean production build)
    base_dir : the directory containing the source files and this script

    Both dashboard.html and the js/ folder are bundled into assets/ inside
    the package, mirroring the original folder structure so relative paths
    in the HTML continue to work at runtime via the local HTTP server.
    """
    script_path = find_file(SCRIPT_FILE, base_dir)
    html_path   = find_file(HTML_FILE,   base_dir)
    js_path     = find_folder(JS_FOLDER, base_dir)

    # --add-data bundles each item into the assets/ subfolder inside the package.
    # At runtime they are unpacked to sys._MEIPASS/assets/, which is where
    # launch_dashboard.py roots the HTTP server.
    # Windows --add-data separator is a semicolon; destination is the target folder.
    add_data_html = f"{html_path};assets"
    add_data_js   = f"{js_path};assets/js"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name",     APP_NAME,
        "--add-data", add_data_html,
        "--add-data", add_data_js,
        "--noconfirm",   # overwrite dist/ without asking
        "--clean",       # wipe PyInstaller's internal cache before building
    ]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    if not debug:
        cmd.append("--noconsole")  # suppress the console window in production

    # Optional: use a custom icon if ICON_FILE exists next to this script
    icon_path = os.path.join(base_dir, ICON_FILE)
    if os.path.isfile(icon_path):
        print(f"[INFO] Using icon : {icon_path}")
        cmd += ["--icon", icon_path]
    else:
        print(f"[INFO] No {ICON_FILE} found - using the default PyInstaller icon.")
        print(f"       (Place {ICON_FILE} next to this script to set a custom icon.)")

    cmd.append(script_path)

    print("\n[INFO] Running PyInstaller...")
    print("  " + " ".join(cmd) + "\n")

    result = subprocess.run(cmd, cwd=base_dir)

    if result.returncode != 0:
        print("\n[ERROR] PyInstaller failed. See output above for details.\n")
        sys.exit(result.returncode)

    # -----------------------------------------------------------------------
    # Report the output location clearly
    # -----------------------------------------------------------------------
    if onefile:
        exe = os.path.join(base_dir, "dist", f"{APP_NAME}.exe")
        print(f"\n{'='*60}")
        print(f"  Build complete!")
        print(f"  Executable : {exe}")
        print(f"{'='*60}")
        print("  Single-file build - share just this .exe.\n")
    else:
        out_dir = os.path.join(base_dir, "dist", APP_NAME)
        exe     = os.path.join(out_dir, f"{APP_NAME}.exe")
        print(f"\n{'='*60}")
        print(f"  Build complete!")
        print(f"  Folder     : {out_dir}")
        print(f"  Executable : {exe}")
        print(f"{'='*60}")
        print("  Folder build - share the entire dist/PipelineAnalytics/ folder.\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the Pipeline Analytics Dashboard into a Windows .exe"
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--onefile",
        action="store_true",
        help="Package everything into a single .exe (slower to start, easier to share)",
    )
    mode.add_argument(
        "--onedir",
        action="store_true",
        help="Package into a folder with .exe (faster to start, default)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Keep the console window visible - useful for troubleshooting",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip removing previous build/ and dist/ folders before building",
    )

    args = parser.parse_args()

    check_pyinstaller()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    if not args.no_clean:
        clean_build_artifacts(base_dir)

    # --onefile takes priority; anything else defaults to --onedir
    onefile = args.onefile

    build(onefile=onefile, debug=args.debug, base_dir=base_dir)


if __name__ == "__main__":
    main()