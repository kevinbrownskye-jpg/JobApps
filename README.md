# JobApps

🚀 Key Features
Live Web Scraping Engine: Leverages the Gemini API with active Google Search grounding tools to discover real-time, deep-linked position postings on the open web.

Automated Skill Alignment Audits: Evaluates candidate baseline CV text layers against discovered or pasted descriptions to isolate keyword tool gaps, calculate compatibility scores, and suggest preparation resources.

7-Day Visual Deduplication Gate: Built-in client-side tracking registry that automatically suppresses matching company-role positions exported within a rolling 7-day window.

Centralized Visual Analytics: Connects cleanly to external deployment endpoints (such as Google Apps Script macros) to stream tabular spreadsheets directly into Chart.js reporting modules, breaking down application pipelines by status, sourcing channel, and career discipline.

Native OS Desktop Container Integration: Uses cross-platform PyWebView wrappers to run modern HTML5 app frameworks as zero-dependency native desktop layout applications.

🔒 Security & Anonymization Guidelines
To distribute or modify this codebase within public version control environments securely, ensure personal runtime infrastructure configuration items are kept completely decoupled from the version history:

API Keys: Never hardcode your gemini_api_key directly in source blocks. The architecture relies on an external local config.json placed next to the launchers or runtime browser storage.

Webhook & Macro Routings: Ensure Job_Dashboard/js/config.js maintains the generic default fallback template pattern string (https://script.google.com/macros/s/YOUR_DEPLOYED_MACRO_ID_HERE/exec) instead of live production web application deployment sequences.

Local Files Verification: Always verify that config.json files and diagnostic trace outputs generated under /logs are properly captured and filtered by the root .gitignore parameters before pushing downstream tracking branches public.

💻 Technical Setup & Local Execution
1. Prerequisites
Ensure you have Python 3.10+ installed along with standard project dependencies:

Bash
pip install pywebview pyinstaller

2. Runtime Configuration
Create a config.json file in the root folder (and matching subsystem subdirectories if executing separately) to hold your local configuration parameters safely:

JSON
{
  "gemini_api_key": "YOUR_ACTUAL_GEMINI_API_KEY",
  "home_path": ""
}

3. Launching Applications Natively
To boot the full suite workspace through the main integrated standalone entry frame, run:

Bash
python launch_control_center.py
To run components as separate processes, you can launch their designated platform instances directly:

Bash
python AI_JobHunter/src/launch_dashboard.py
python Job_Dashboard/launch_dashboard.py

4. Compiling Zero-Dependency Executables (.exe)
To package any panel layout into a lightweight, standalone binary file that operates without requiring a local Python interpreter environment, invoke PyInstaller using the customized bundling scripts:

Bash
python build_exe.py
🗺️ Customizing Taxonomy & Role Mappings
To adapt the classification dashboard logic to fit alternative specialized industries or focus domains, simply modify the structural dictionary array map inside Job_Dashboard/js/roles-config.js:

JavaScript
const ROLE_MAPPING_DICTIONARY = {
    "Engineering & Dev": [
        "engineer", "developer", "programmer", "technical", "automation", "software"
    ],
    "Management & Operations": [
        "pm", "project manager", "coordinator", "lead", "scrum", "operations"
    ]
};
The data pipeline will automatically re-parse, aggregate, and display matched dashboard rows according to these explicit string evaluation guidelines at initialization runtime.
"""

├── AI_JobHunter/                # Sourcing & Evaluation Subsystem
│   ├── src/
│   │   ├── css/                 # UI Desktop Styling Layer
│   │   ├── js/                  # Application Logic Engines
│   │   │   ├── config.js        # Parameter State & Webhook Fallbacks
│   │   │   ├── exporter.js      # Pipeline Sync Data Dispatcher
│   │   │   ├── manualAnalyzer.js# Webpage Parsing & Raw Text Auditing
│   │   │   ├── scanner.js       # Live Web Scraping & Dedup Gates
│   │   │   └── uiManager.js     # Dom Renderers & System Toast Alerts
│   │   ├── index.html           # Sourcing Workspace GUI
│   │   ├── launch_dashboard.py  # Standalone PyWebView App Launcher
│   │   └── build_exe.py         # PyInstaller Packaging Script
│
├── Job_Dashboard/               # Metrics & Application Spreadsheet Tracker
│   ├── js/
│   │   ├── api.js               # External Macro Data Stream Gateway
│   │   ├── config.js            # Centralized API Connection Route
│   │   ├── metrics.js           # Chart.js Visual Configuration Engines
│   │   ├── roles-config.js      # Dynamic String Taxonomy Dictionary
│   │   └── viewer.js            # Spreadsheet Layout Grid Renderer
│   ├── dashboard.html           # Visual Analytics Shell Frame
│   ├── launch_dashboard.py      # Standalone Metrics Desktop Wrapper
│   └── build_exe.py             # Packaging Script for Dashboard Subsystem
│
├── index.html                   # Root Control Center Portal Entrance
├── launch_control_center.py     # Root Portal Desktop Standalone Launcher
├── build_exe.py                 # Master Executive Distribution Bundler
└── .gitignore                   # Active Version Control Exclusions (config.json, etc.)
