# ACM Implementation Plan (Phase 1: Sliders + Run)

Objective
- Connect the existing Qt UI (config_sliders.ui) to process_markdown by:
  - Reading current config values on launch and reflecting them in sliders.
  - Writing updated values from sliders into the appropriate config files.
  - Executing process_markdown/generate.py when the Run button is clicked.
- Scope is limited to the sliders and the Run button. Provider/model combos, additional model groups, evaluation panels, and other buttons are out of scope for this phase.

Key Paths
- UI file:
  - process_markdown/apicostmultiplier/config_sliders.ui
- Config files to read/write:
  - process_markdown/config.yaml
  - process_markdown/FilePromptForge/default_config.yaml
  - process_markdown/gpt-researcher/gpt_researcher/config/variables/default.py
  - process_markdown/gpt-researcher/multi_agents/task.json
- Orchestrator to run:
  - process_markdown/generate.py
- Application entry for this phase:
  - process_markdown/apicostmultiplier/main.py (to be implemented)

UI → Config Mappings (sliders only)
- General (process_markdown/config.yaml)
  - sliderIterations_2 → iterations_default (int)
- FPF (process_markdown/FilePromptForge/default_config.yaml)
  - sliderGroundingMaxResults → grounding.max_results (int)
  - sliderGoogleMaxTokens → google.max_tokens (int)
- GPTR (process_markdown/gpt-researcher/gpt_researcher/config/variables/default.py, DEFAULT_CONFIG)
  - sliderFastTokenLimit → FAST_TOKEN_LIMIT (int)
  - sliderSmartTokenLimit → SMART_TOKEN_LIMIT (int)
  - sliderStrategicTokenLimit → STRATEGIC_TOKEN_LIMIT (int)
  - sliderBrowseChunkMaxLength → BROWSE_CHUNK_MAX_LENGTH (int)
  - sliderSummaryTokenLimit → SUMMARY_TOKEN_LIMIT (int)
  - sliderTemperature → TEMPERATURE (float: UI 0–100 → 0.00–1.00)
  - sliderMaxSearchResultsPerQuery → MAX_SEARCH_RESULTS_PER_QUERY (int)
  - sliderTotalWords → TOTAL_WORDS (int)
  - sliderMaxIterations → MAX_ITERATIONS (int)
  - sliderMaxSubtopics → MAX_SUBTOPICS (int)
- DR (same default.py)
  - sliderDeepResearchBreadth → DEEP_RESEARCH_BREADTH (int)
  - sliderDeepResearchDepth → DEEP_RESEARCH_DEPTH (int)
- MA (process_markdown/gpt-researcher/multi_agents/task.json)
  - sliderMaxSections → max_sections (int)

Initialization (Config → UI)
- On application start:
  1) Read process_markdown/config.yaml and set sliderIterations_2 from iterations_default (default 1 if missing).
  2) Read process_markdown/FilePromptForge/default_config.yaml and set:
     - sliderGroundingMaxResults from grounding.max_results (default 5)
     - sliderGoogleMaxTokens from google.max_tokens (default 1500)
  3) Read process_markdown/gpt-researcher/gpt_researcher/config/variables/default.py:
     - Parse DEFAULT_CONFIG using targeted regex for each key listed above.
     - Set corresponding sliders. For TEMPERATURE, multiply by 100 and clamp to UI range.
  4) Read process_markdown/gpt-researcher/multi_agents/task.json and set sliderMaxSections from max_sections (default 1).
- If a file/key is missing, retain UI defaults and proceed.

Write-Back Strategy (UI → Config)
- Timing:
  - Phase 1 writes occur when the user clicks Run. (Live-write on slider change can be added in a later phase.)
- Backups:
  - Before the first write in a session, create a single .bak alongside each target:
    - config.yaml.bak
    - default_config.yaml.bak
    - default.py.bak
    - task.json.bak
- YAML/JSON:
  - Use PyYAML safe_load/safe_dump with indent=2, default_flow_style=False, sort_keys=False.
  - For JSON, load/dump with indent=2, ensure_ascii=False.
- Python default.py:
  - Load as text. For each DEFAULT_CONFIG key, perform a targeted regex substitution that updates the value literal while preserving formatting, commas, and comments around it.
  - Examples:
    - Integers: ("FAST_TOKEN_LIMIT"\s*:\s*)(\d+)
    - Float (TEMPERATURE): ("TEMPERATURE"\s*:\s*)([0-9]*\.?[0-9]+)
    - Deep research ints: ("DEEP_RESEARCH_BREADTH"\s*:\s*)(\d+), ("DEEP_RESEARCH_DEPTH"\s*:\s*)(\d+)
  - Validate each intended key was found; log a warning for any misses and continue.

Value Handling and Validation
- Clamp all integer sliders to non-negative ints within their UI min/max bounds.
- Temperature:
  - Convert UI value v (0–100) to float f = round(v / 100.0, 2).
  - Clamp to [0.0, 1.0].
- Missing nested dicts (YAML/JSON):
  - If sections like grounding are absent, create them before writing the leaf values.

Run Button Behavior
- Button: btnAction7 (“Run”).
- On click:
  1) Disable the button to prevent concurrent launches.
  2) Collect slider values and write to the four targets in this order:
     - process_markdown/config.yaml
     - process_markdown/FilePromptForge/default_config.yaml
     - process_markdown/gpt-researcher/gpt_researcher/config/variables/default.py
     - process_markdown/gpt-researcher/multi_agents/task.json
  3) Launch the generator:
     - Executable: sys.executable
     - Args: ["-u", str(generate_py)]
     - cwd: process_markdown/
     - env: inherit with PYTHONIOENCODING="utf-8"
     - Use subprocess.Popen with stdout/stderr pipes; stream lines to console or a log widget later.
     - Do NOT use shell or ampersand chaining; invoke directly via argument list.
  4) On process exit, re-enable the Run button and surface success/failure to the user.

main.py Structure
- Imports:
  - Qt binding (PyQt5 recommended): from PyQt5 import QtWidgets, uic
  - pathlib, os, sys, json, re, shutil, subprocess
  - yaml (PyYAML)
- Paths:
  - repo_root = Path(__file__).resolve().parents[1]
  - pm_dir = repo_root / "process_markdown"
  - pm_config_yaml = pm_dir / "config.yaml"
  - fpf_yaml = pm_dir / "FilePromptForge" / "default_config.yaml"
  - gptr_default_py = pm_dir / "gpt-researcher" / "gpt_researcher" / "config" / "variables" / "default.py"
  - ma_task_json = pm_dir / "gpt-researcher" / "multi_agents" / "task.json"
  - generate_py = pm_dir / "generate.py"
- Startup:
  - app = QApplication()
  - window = uic.loadUi(config_sliders.ui)
  - Wire widget references by objectName for each slider and btnAction7.
  - Call load_current_values() to set sliders from disk.
- Event wiring:
  - btnAction7.clicked.connect(self.on_run_clicked)
- Helpers:
  - backup_once(path: Path) -> None
  - load_* (for YAML/JSON/Python)
  - write_pm_config_yaml(iterations_default: int)
  - write_fpf_yaml(grounding_max_results: int, google_max_tokens: int)
  - write_ma_task(max_sections: int)
  - write_gptr_default_py(updates: dict[str, int|float])
  - temp_from_slider(v: int) -> float
  - show_error(text: str), show_info(text: str)
- Run handler:
  - try: write all; except: show_error + re-enable.
  - spawn subprocess; stream output; finalize with message.

Edge Cases and Fallbacks
- Missing files:
  - Show a clear dialog stating which file is missing; suggest using “Download and Install” (present in UI) before running.
- Permission errors:
  - Catch exceptions on write and present actionable messages (e.g., “close the file in another program and retry”).
- Regex misses in default.py:
  - Log which key failed to update. Consider adding optional JSON/YAML overlay strategy later to avoid editing Python source.

Testing Checklist
- Launch main.py; verify sliders reflect current config values from disk.
- Change sliders and press Run:
  - Confirm process_markdown/config.yaml iterations_default updated.
  - Confirm FilePromptForge/default_config.yaml updated for grounding.max_results and google.max_tokens.
  - Confirm gpt-researcher/gpt_researcher/config/variables/default.py updated for all target fields (including TEMPERATURE scaling).
  - Confirm gpt-researcher/multi_agents/task.json max_sections updated.
  - Confirm generate.py runs to completion and logs progress. Run button re-enables afterwards.
- Verify .bak files were created only once and not overwritten.

Future Phases (out of scope here)
- Provider/model combos and “Additional Model” groups.
- Enabling/disabling report types by setting iterations.{ma,gptr,dr,fpf} based on group checkboxes.
- Evaluation panels (graded, pairwise) and additional evaluation groups.
- Path browser/open buttons and metrics updates.
- .env helpers and API key validation.
- React frontend + API backend refactor.

Notes
- Stick to direct subprocess invocation with a list of args (no shell), and ensure UTF-8 I/O to avoid Windows encoding issues.
- The UI contains minor typos (e.g., “Maser Quality”, “Load Prest”, “Multipler”); do not change UI strings in this phase.
