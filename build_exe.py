#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_exe.py — One-click builder for Workspace Control Center .exe
===================================================================
Packages launch_control_center.py + the entire project tree into a
standalone Windows executable using PyInstaller.

The full folder structure is preserved inside the bundle under app/,
so relative navigation between the Control Center and child apps
(AI_JobHunter/, Job_Dashboard/) works identically to development.

Requirements (install once):
    pip install pyinstaller pywebview

Usage:
    python build_exe.py              # folder output (fast startup, default)
    python build_exe.py --onefile    # single .exe (easier to share)
    python build_exe.py --debug      # keep console window for troubleshooting
    python build_exe.py --debug-app  # bake DevTools (F12) into the .exe
    python build_exe.py --no-clean   # skip removing previous build/dist

Output:
    dist/ControlCenter/ControlCenter.exe   (--onedir, default)
    dist/ControlCenter.exe                 (--onefile)

IMPORTANT — what to bundle:
    The entire project root (index.html, AI_JobHunter/, Job_Dashboard/) is
    bundled under app/ in the package. Make sure both child app folders are
    present next to index.html before building.

    config.json files inside child apps are intentionally NOT bundled —
    they stay next to the .exe so credentials can be updated without rebuilding.
    After building, config.json is automatically copied from AI_JobHunter/src/
    into the dist output folder next to ControlCenter.exe.
"""

import argparse
import os
import shutil
import subprocess
import sys
import stat
import time

# ---------------------------------------------------------------------------
# Config — update if your files or folders have different names
# ---------------------------------------------------------------------------
APP_NAME     = "ControlCenter"
SCRIPT_FILE  = "launch_control_center.py"
# config.json is copied from here into the dist output after building,
# so the JobHunter launcher finds it next to ControlCenter.exe.
CONFIG_SRC   = os.path.join("AI_JobHunter", "src", "config.json")
# Subfolders to bundle (relative to this script's directory).
# The entire project root is mapped to app/ inside the bundle.
BUNDLE_DIR   = "."   # bundle from the project root downward
# ---------------------------------------------------------------------------


def check_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print(
            "\n[ERROR] PyInstaller is not installed.\n"
            "Install it with:\n\n"
            "    pip install pyinstaller\n"
        )
        sys.exit(1)


def find_file(filename: str, base_dir: str) -> str:
    """Locate a required file; abort with a clear message if missing."""
    path = os.path.join(base_dir, filename)
    if not os.path.isfile(path):
        print(f"\n[ERROR] Required file not found: {path}")
        print(f"  Make sure '{filename}' is in the same folder as this build script.\n")
        sys.exit(1)
    return path


def _force_remove(path: str) -> None:
    """
    Robustly delete a file or folder on Windows.
    Handles read-only files (chmod first) and locked files (retry with delay).
    """
    def _on_error(func, failing_path, exc_info):
        try:
            os.chmod(failing_path, stat.S_IWRITE)
            func(failing_path)
        except Exception:
            pass

    for attempt in range(3):
        try:
            if os.path.isfile(path):
                os.chmod(path, stat.S_IWRITE)
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path, onexc=_on_error)
            return
        except PermissionError as exc:
            if attempt < 2:
                print(f"[CLEAN] Locked — retrying in 2s ({exc.filename})")
                time.sleep(2)
            else:
                print(f"[CLEAN] WARNING: Could not delete {path}")
                print(f"         Reason : {exc}")
                print(f"         Fix    : close the app / pause OneDrive, then rebuild.")


def clean_build_artifacts(base_dir: str) -> None:
    """Remove all artifacts from a previous build for a clean start."""
    removed = []
    skipped = []

    for folder in ("build", "dist"):
        target = os.path.join(base_dir, folder)
        if os.path.isdir(target):
            _force_remove(target)
            removed.append(folder + "/")
        else:
            skipped.append(folder + "/")

    spec = os.path.join(base_dir, f"{APP_NAME}.spec")
    if os.path.isfile(spec):
        _force_remove(spec)
        removed.append(f"{APP_NAME}.spec")
    else:
        skipped.append(f"{APP_NAME}.spec")

    pycache = os.path.join(base_dir, "__pycache__")
    if os.path.isdir(pycache):
        _force_remove(pycache)
        removed.append("__pycache__/")
    else:
        skipped.append("__pycache__/")

    hook = os.path.join(base_dir, "_debug_hook.py")
    if os.path.isfile(hook):
        _force_remove(hook)
        removed.append("_debug_hook.py")

    if removed:
        print(f"[CLEAN] Deleted      : {', '.join(removed)}")
    if skipped:
        print(f"[CLEAN] Not found    : {', '.join(skipped)}")


def copy_config_next_to_exe(base_dir: str, onefile: bool) -> None:
    """
    Copy AI_JobHunter/src/config.json into the dist output folder after building,
    so the JobHunter launcher can find it next to ControlCenter.exe via exe_dir().

    Skipped with a clear message if config.json doesn't exist at the source path.
    Creates the destination directory if it doesn't exist yet.
    """
    src = os.path.join(base_dir, CONFIG_SRC)
    if not os.path.isfile(src):
        print(f"[INFO] No config.json found at {CONFIG_SRC} — skipping copy.")
        print(f"       (Add it at {CONFIG_SRC} and rebuild, or place it manually next to the .exe.)")
        return

    dest_dir = os.path.join(base_dir, "dist") if onefile else os.path.join(base_dir, "dist", APP_NAME)
    dest     = os.path.join(dest_dir, "config.json")

    try:
        os.makedirs(dest_dir, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"[INFO] config.json copied to: {dest}")
    except Exception as exc:
        print(f"[WARN] config.json copy failed: {exc}")
        print(f"       Copy it manually: {src}  ->  {dest}")


def build(onefile: bool, debug: bool, base_dir: str, debug_app: bool = False) -> None:
    """
    Construct and run the PyInstaller command.

    The project root (index.html + child app folders) is bundled under app/
    inside the package. resolve_project_dir() in the launcher looks for
    sys._MEIPASS/app/index.html, which is exactly where it will land.

    Excluded from the bundle:
      - config.json files (stay external so credentials don't need a rebuild)
      - build/, dist/, __pycache__/ (build artifacts, not app content)
      - .git/, .gitignore (source control metadata)
    """
    script_path = find_file(SCRIPT_FILE, base_dir)

    # Bundle the entire project root into app/ inside the package.
    # This preserves the folder structure: app/index.html,
    # app/AI_JobHunter/src/index.html, app/Job_Dashboard/dashboard.html, etc.
    add_data = f"{base_dir}{os.pathsep}app"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name",     APP_NAME,
        "--add-data", add_data,
        "--noconfirm",
        "--clean",
        # Exclude Python config module to avoid accidentally bundling config files
        "--exclude-module", "config",
    ]

    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    if not debug:
        cmd.append("--noconsole")

    # Bake PYWEBVIEW_DEBUG=1 into the .exe if --debug-app was requested
    if debug_app:
        hook_path = os.path.join(base_dir, "_debug_hook.py")
        with open(hook_path, "w") as hf:
            hf.write("import os\nos.environ['PYWEBVIEW_DEBUG'] = '1'\n")
        cmd += ["--runtime-hook", hook_path]
        print("[INFO] DevTools (F12) will be enabled in the compiled .exe")

    icon_path = os.path.join(base_dir, "icon.ico")
    if os.path.isfile(icon_path):
        print(f"[INFO] Using icon: {icon_path}")
        cmd += ["--icon", icon_path]
    else:
        print("[INFO] No icon.ico found — using default PyInstaller icon.")
        print("       (Place icon.ico next to this script to use a custom icon.)")

    cmd.append(script_path)

    print("\n[INFO] Running PyInstaller...")
    print("  " + " ".join(cmd) + "\n")

    result = subprocess.run(cmd, cwd=base_dir)

    if result.returncode != 0:
        print("\n[ERROR] PyInstaller failed. See output above for details.\n")
        sys.exit(result.returncode)

    # Copy config.json next to the .exe so the JobHunter launcher finds it
    copy_config_next_to_exe(base_dir, onefile)

    # -----------------------------------------------------------------------
    # Final summary
    # -----------------------------------------------------------------------
    if onefile:
        exe = os.path.join(base_dir, "dist", f"{APP_NAME}.exe")
        print(f"\n{'='*60}")
        print(f"  Build complete!")
        print(f"  Executable : {exe}")
        print(f"{'='*60}")
        print("\n  Single-file build — share just the .exe.")
        print("  Any config.json files must sit in the SAME folder as the .exe.")
        print("  Set \'home_path\' in config.json to point to your source index.html")
        print("  so edits are picked up on next launch without rebuilding.\n")
    else:
        out_dir = os.path.join(base_dir, "dist", APP_NAME)
        exe     = os.path.join(out_dir, f"{APP_NAME}.exe")
        print(f"\n{'='*60}")
        print(f"  Build complete!")
        print(f"  Folder     : {out_dir}")
        print(f"  Executable : {exe}")
        print(f"{'='*60}")
        print("\n  Share the entire dist/ControlCenter/ folder.")
        print("  Place config.json next to the .exe before sharing.")
        print("  Set \'home_path\' in config.json to point to your source index.html")
        print("  so edits are picked up on next launch without rebuilding.\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the Workspace Control Center into a Windows .exe"
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--onefile",
        action="store_true",
        help="Pack everything into a single .exe (slower startup, easier to share)",
    )
    mode.add_argument(
        "--onedir",
        action="store_true",
        help="Output a folder with the .exe (faster startup, default)",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Keep the console window open (useful for troubleshooting crashes)",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip removing previous build/dist folders",
    )
    parser.add_argument(
        "--debug-app",
        action="store_true",
        help="Bake DevTools (F12) into the .exe — useful for testing a built version",
    )

    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"\n{'='*60}")
    print(f"  Workspace Control Center — EXE Builder")
    print(f"{'='*60}")
    print(f"  Mode    : {'single .exe' if args.onefile else 'folder (onedir)'}")
    print(f"  Debug   : {'yes (console visible)' if args.debug else 'no'}")
    print(f"  DevTools: {'yes (F12 enabled in .exe)' if args.debug_app else 'no'}")
    print(f"  Base dir: {base_dir}\n")

    check_pyinstaller()

    if not args.no_clean:
        clean_build_artifacts(base_dir)

    build(
        onefile=args.onefile,
        debug=args.debug,
        base_dir=base_dir,
        debug_app=args.debug_app,
    )


if __name__ == "__main__":
    main()