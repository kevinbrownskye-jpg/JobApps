# Pipeline Analytics Dashboard - Desktop Launcher

Runs `dashboard.html` as a native Windows desktop app, with no browser required.
The HTML file and `js/` folder are **never modified** by any of these scripts.

---

## Files

| File | Purpose |
|---|---|
| `dashboard.html` | The dashboard itself - your original file, untouched |
| `js/` | Modular JS files loaded by the dashboard (`config.js`, `api.js`, `metrics.js`, `viewer.js`) |
| `launch_dashboard.py` | Launches the dashboard in a native desktop window |
| `build_exe.py` | Packages everything into a standalone `.exe` using PyInstaller |

Place all files in the same folder, with `js/` as a subfolder:

```
your_folder/
├── dashboard.html
├── launch_dashboard.py
├── build_exe.py
├── dashboard_icon_182989.ico     <- optional, for custom taskbar/window icon
└── js/
    ├── config.js
    ├── api.js
    ├── metrics.js
    └── viewer.js
```

---

## Requirements

Python 3.10+ is required. Install dependencies once:

```bash
pip install pywebview pyinstaller
```

- **pywebview** - wraps the OS's built-in web renderer in a native window
- **pyinstaller** - only needed if building a `.exe`; not required to run the launcher directly

---

## Running the launcher (no build needed)

The quickest way to use the dashboard as a desktop app - no build step required.

```bash
python launch_dashboard.py
```

The launcher starts a local HTTP server rooted at the project folder, then opens
a native window pointed at `http://localhost:8000/dashboard.html`. This allows
the dashboard to load its `js/` modules via relative paths, which the `file://`
protocol does not support.

The window opens at **1280 x 800** by default, suitable for a laptop screen.
It is resizable with a minimum size of 800 x 600. The server shuts down
automatically when the window is closed.

### Launcher options

| Flag | Description |
|---|---|
| `--file PATH` / `-f PATH` | Use a dashboard.html in a different location |
| `--port N` / `-p N` | Starting port for the HTTP server (default: 8000; auto-increments if in use) |
| `--width N` / `-W N` | Set window width in pixels (default: 1280) |
| `--height N` / `-H N` | Set window height in pixels (default: 800) |
| `--no-resizable` | Lock the window to its starting size |
| `--debug` | Open the browser DevTools panel - useful for diagnosing data or layout issues |

**Examples:**

```bash
# Custom window size
python launch_dashboard.py --width 1600 --height 900

# HTML file in a different folder
python launch_dashboard.py --file C:\Users\you\Documents\dashboard.html

# Open with DevTools visible
python launch_dashboard.py --debug

# Use a specific port
python launch_dashboard.py --port 9000
```

---

## Building a standalone .exe

Creates a self-contained executable that can be run without Python installed.

```bash
python build_exe.py
```

### Build options

| Command | Result |
|---|---|
| `python build_exe.py` | Folder-based build - faster startup, default |
| `python build_exe.py --onedir` | Same as above, explicit |
| `python build_exe.py --onefile` | Single `.exe` - easier to share, slower to start |
| `python build_exe.py --debug` | Keeps the console window visible for troubleshooting |
| `python build_exe.py --no-clean` | Skips removing previous `build/` and `dist/` folders |

### Output locations

| Build type | Output |
|---|---|
| `--onedir` (default) | `dist/PipelineAnalytics/PipelineAnalytics.exe` |
| `--onefile` | `dist/PipelineAnalytics.exe` |

**Folder build** (`--onedir`): share the entire `dist/PipelineAnalytics/` folder.
**Single-file build** (`--onefile`): share just the `.exe`. Slightly slower to open
because it unpacks itself to a temp folder on each launch.

### Custom icon

Place the `.ico` file next to `build_exe.py` before running the build. The filename
is set by the `ICON_FILE` variable at the top of `build_exe.py`. If no icon is found,
the default PyInstaller icon is used and the build still succeeds. A new icon requires
a rebuild - the icon is baked in at build time.

### Config block

The top of `build_exe.py` contains a config block for names that may need updating:

```python
APP_NAME    = "PipelineAnalytics"
SCRIPT_FILE = "launch_dashboard.py"
HTML_FILE   = "dashboard.html"
JS_FOLDER   = "js"
ICON_FILE   = "dashboard_icon_182989.ico"
```

---

## How it works

`launch_dashboard.py` starts Python's built-in `http.server` in a background thread,
rooted at the project folder. This means `dashboard.html` and its `js/` subfolder are
both reachable via standard relative paths, exactly as they would be on a web server.
pywebview then opens a native OS window (backed by Edge WebView2 on Windows) pointed
at `http://localhost:<port>/dashboard.html`. No browser is launched; the window behaves
like any other desktop application. The server shuts down when the window closes.

The dashboard fetches live data from a Google Apps Script endpoint hardcoded in
`dashboard.html`. If that URL ever changes, update the one line in the HTML file -
no changes to the launcher or build script are needed.

When compiled with PyInstaller, `dashboard.html` and the entire `js/` folder are
bundled inside the package under `assets/`, mirroring the original structure so
relative paths continue to work at runtime.

---

## Troubleshooting

**"Could not find dashboard.html"**
The launcher searches for `dashboard.html` in the same folder as the script, then
the current working directory. Either move the HTML file next to the script, or
pass `--file <path>` to point to it directly.

**"pywebview is not installed"**
Run `pip install pywebview` and try again.

**"PyInstaller is not installed"**
Run `pip install pyinstaller` and try again. Only needed for `.exe` builds.

**"Could not find a free port after 10 attempts"**
10 consecutive ports starting from 8000 are all in use. Pass `--port 9000` (or
any other free range) to start from a different base port.

**Dashboard shows "Failed to connect to data stream"**
This is a network error from the dashboard itself, not the launcher. Check that
the Google Apps Script URL in `dashboard.html` is correct and that the deployment
is set to allow access.

**Build succeeds but the .exe shows a blank window or missing charts**
Run the build with `--debug` to keep the console open and see any JS errors.
You can also run `launch_dashboard.py --debug` directly to open DevTools without
needing to rebuild. Check that the `js/` folder was present when the build ran -
`build_exe.py` will exit with an error if it is missing.