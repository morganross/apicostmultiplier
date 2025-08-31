import sys
import os
import re
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml  # PyYAML
except Exception:  # pragma: no cover
    yaml = None  # we will guard uses and show message box if missing

from PyQt5 import QtWidgets, QtCore, uic


def clamp_int(value: int, min_v: int, max_v: int) -> int:
    return max(min_v, min(max_v, int(value)))


def temp_from_slider(v: int) -> float:
    # Scale 0-100 slider to [0.0, 1.0] with two decimals
    f = round((float(v) / 100.0), 2)
    if f < 0.0:
        f = 0.0
    if f > 1.0:
        f = 1.0
    return f


def backup_once(path: Path) -> None:
    bak = path.with_suffix(path.suffix + ".bak")
    try:
        if path.exists() and not bak.exists():
            shutil.copy2(str(path), str(bak))
    except Exception as e:
        # Non-fatal: allow continuing; user will be notified on write if it fails
        print(f"[WARN] Failed to create backup for {path}: {e}", flush=True)


def read_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is not installed. Please install PyYAML.")
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        data = {}
    return data


def write_yaml(path: Path, data: Dict[str, Any]) -> None:
    if yaml is None:
        raise RuntimeError("PyYAML is not installed. Please install PyYAML.")
    backup_once(path)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, indent=2, sort_keys=False, allow_unicode=True)


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    backup_once(path)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    with path.open("r", encoding="utf-8") as fh:
        return fh.read()


def write_text(path: Path, content: str) -> None:
    backup_once(path)
    with path.open("w", encoding="utf-8") as fh:
        fh.write(content)


def extract_number_from_default_py(text: str, key: str) -> Optional[float]:
    """
    Extract numeric (int/float) value for a given key inside DEFAULT_CONFIG.
    Matches patterns like: "KEY": 123 or "KEY": 0.45
    """
    # Restrict to DEFAULT_CONFIG block to reduce false positives
    # but keep robust if formatting changes.
    # First, try to find within DEFAULT_CONFIG {...}
    m_cfg = re.search(r"DEFAULT_CONFIG\s*:\s*BaseConfig\s*=\s*\{(.*?)\}\s*$", text, re.DOTALL | re.MULTILINE)
    scope = m_cfg.group(1) if m_cfg else text
    pattern = rf'("{re.escape(key)}"\s*:\s*)(-?\d+(?:\.\d+)?)'
    m = re.search(pattern, scope)
    if not m:
        # Try a more permissive search on whole text
        m = re.search(pattern, text)
    if m:
        try:
            return float(m.group(2))
        except Exception:
            return None
    return None


def replace_number_in_default_py(text: str, key: str, new_value: float) -> (str, bool):
    """
    Replace numeric (int/float) for a given key inside DEFAULT_CONFIG.
    Keeps trailing commas / comments intact by replacing only the numeric literal.
    Returns (new_text, replaced_flag).
    """
    def _fmt(v: float) -> str:
        # Keep ints as ints, floats with up to two decimals
        if abs(v - int(v)) < 1e-9:
            return str(int(v))
        return f"{v:.2f}"

    pattern = rf'("{re.escape(key)}"\s*:\s*)(-?\d+(?:\.\d+)?)'
    def _repl(m):
        return m.group(1) + _fmt(new_value)
    new_text, n = re.subn(pattern, _repl, text, count=1)
    return new_text, n > 0


class RunnerThread(QtCore.QThread):
    finished_ok = QtCore.pyqtSignal(bool, int, str)  # (success, returncode, message)

    def __init__(self, pm_dir: Path, generate_py: Path, parent=None):
        super().__init__(parent)
        self.pm_dir = pm_dir
        self.generate_py = generate_py

    def run(self) -> None:  # type: ignore[override]
        try:
            cmd = [sys.executable, "-u", str(self.generate_py)]
            env = os.environ.copy()
            env.setdefault("PYTHONIOENCODING", "utf-8")
            print(f"[INFO] Starting generate.py with: {cmd}", flush=True)
            proc = subprocess.Popen(
                cmd,
                cwd=str(self.pm_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            # Stream output
            assert proc.stdout is not None
            assert proc.stderr is not None
            for line in proc.stdout:
                print(line, end="", flush=True)
            for line in proc.stderr:
                print(line, end="", flush=True)

            proc.wait()
            ok = proc.returncode == 0
            msg = "generate.py finished successfully" if ok else f"generate.py exited with code {proc.returncode}"
            self.finished_ok.emit(ok, proc.returncode, msg)
        except Exception as e:
            self.finished_ok.emit(False, -1, f"Failed to run generate.py: {e}")


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Paths
        self.this_file = Path(__file__).resolve()
        self.pm_dir = self.this_file.parents[1]  # process_markdown/
        self.repo_root = self.pm_dir.parent

        self.ui_path = self.pm_dir / "apicostmultiplier" / "config_sliders.ui"

        self.pm_config_yaml = self.pm_dir / "config.yaml"
        self.fpf_yaml = self.pm_dir / "FilePromptForge" / "default_config.yaml"
        self.gptr_default_py = self.pm_dir / "gpt-researcher" / "gpt_researcher" / "config" / "variables" / "default.py"
        self.ma_task_json = self.pm_dir / "gpt-researcher" / "multi_agents" / "task.json"
        self.generate_py = self.pm_dir / "generate.py"

        # Load UI
        self.ui = uic.loadUi(str(self.ui_path), self)

        # Cache widgets (sliders)
        self.sliderIterations_2: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderIterations_2")

        self.sliderGroundingMaxResults: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderGroundingMaxResults")
        self.sliderGoogleMaxTokens: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderGoogleMaxTokens")

        self.sliderFastTokenLimit: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderFastTokenLimit")
        self.sliderSmartTokenLimit: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderSmartTokenLimit")
        self.sliderStrategicTokenLimit: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderStrategicTokenLimit")
        self.sliderBrowseChunkMaxLength: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderBrowseChunkMaxLength")
        self.sliderSummaryTokenLimit: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderSummaryTokenLimit")
        self.sliderTemperature: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderTemperature")
        self.sliderMaxSearchResultsPerQuery: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderMaxSearchResultsPerQuery")
        self.sliderTotalWords: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderTotalWords")
        self.sliderMaxIterations: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderMaxIterations")
        self.sliderMaxSubtopics: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderMaxSubtopics")

        self.sliderDeepResearchBreadth: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderDeepResearchBreadth")
        self.sliderDeepResearchDepth: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderDeepResearchDepth")

        self.sliderMaxSections: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderMaxSections")

        # Master quality slider (Presets)
        self.sliderMasterQuality: QtWidgets.QSlider = self.findChild(QtWidgets.QSlider, "sliderIterations")

        # Buttons
        self.btn_write_configs: QtWidgets.QPushButton = self.findChild(QtWidgets.QPushButton, "pushButton_3")  # "Write to Configs"
        self.btn_run: QtWidgets.QPushButton = self.findChild(QtWidgets.QPushButton, "btnAction7")  # "Run"

        # Path widgets (line edits + browse/open buttons)
        self.lineInputFolder: QtWidgets.QLineEdit = self.findChild(QtWidgets.QLineEdit, "lineInputFolder")
        self.btnBrowseInputFolder: QtWidgets.QPushButton = self.findChild(QtWidgets.QPushButton, "btnBrowseInputFolder")
        self.btnOpenInputFolder: QtWidgets.QPushButton = self.findChild(QtWidgets.QPushButton, "btnOpenInputFolder")

        self.lineOutputFolder: QtWidgets.QLineEdit = self.findChild(QtWidgets.QLineEdit, "lineOutputFolder")
        self.btnBrowseOutputFolder: QtWidgets.QPushButton = self.findChild(QtWidgets.QPushButton, "btnBrowseOutputFolder")
        self.btnOpenOutputFolder: QtWidgets.QPushButton = self.findChild(QtWidgets.QPushButton, "btnOpenOutputFolder")

        self.lineInstructionsFile: QtWidgets.QLineEdit = self.findChild(QtWidgets.QLineEdit, "lineInstructionsFile")
        self.btnBrowseInstructionsFile: QtWidgets.QPushButton = self.findChild(QtWidgets.QPushButton, "btnBrowseInstructionsFile")
        self.btnOpenInstructionsFolder: QtWidgets.QPushButton = self.findChild(QtWidgets.QPushButton, "btnOpenInstructionsFolder")

        # Provider / Model combos (initial subset)
        self.comboFPFProvider: QtWidgets.QComboBox = self.findChild(QtWidgets.QComboBox, "comboFPFProvider")
        self.comboFPFModel: QtWidgets.QComboBox = self.findChild(QtWidgets.QComboBox, "comboFPFModel")
        self.comboGPTRProvider: QtWidgets.QComboBox = self.findChild(QtWidgets.QComboBox, "comboGPTRProvider")
        self.comboGPTRModel: QtWidgets.QComboBox = self.findChild(QtWidgets.QComboBox, "comboGPTRModel")
        self.comboDRProvider: QtWidgets.QComboBox = self.findChild(QtWidgets.QComboBox, "comboDRProvider")
        self.comboDRModel: QtWidgets.QComboBox = self.findChild(QtWidgets.QComboBox, "comboDRModel")
        self.comboMAProvider: QtWidgets.QComboBox = self.findChild(QtWidgets.QComboBox, "comboMAProvider")
        self.comboMAModel: QtWidgets.QComboBox = self.findChild(QtWidgets.QComboBox, "comboMAModel")

        # Checkable groupboxes (enable/disable report types)
        self.groupProvidersFPF: Optional[QtWidgets.QGroupBox] = self.findChild(QtWidgets.QGroupBox, "groupProvidersFPF")
        self.groupProvidersGPTR: Optional[QtWidgets.QGroupBox] = self.findChild(QtWidgets.QGroupBox, "groupProvidersGPTR")
        self.groupProvidersDR: Optional[QtWidgets.QGroupBox] = self.findChild(QtWidgets.QGroupBox, "groupProvidersDR")
        self.groupProvidersMA: Optional[QtWidgets.QGroupBox] = self.findChild(QtWidgets.QGroupBox, "groupProvidersMA")
        self.groupEvaluation: Optional[QtWidgets.QGroupBox] = self.findChild(QtWidgets.QGroupBox, "groupEvaluation")
        self.groupEvaluation2: Optional[QtWidgets.QGroupBox] = self.findChild(QtWidgets.QGroupBox, "groupEvaluation2")

        if self.btn_write_configs:
            self.btn_write_configs.clicked.connect(self.on_write_clicked)
        if self.btn_run:
            self.btn_run.clicked.connect(self.on_run_clicked)
        if self.sliderMasterQuality:
            self.sliderMasterQuality.valueChanged.connect(self.on_master_quality_changed)

        # Bottom toolbar button connections (wire UI buttons to handlers)
        # Note: objectNames are taken from config_sliders.ui
        try:
            btn = self.findChild(QtWidgets.QPushButton, "pushButton_2")  # Download and Install
            if btn:
                btn.clicked.connect(self.on_download_and_install)
        except Exception:
            pass
        try:
            btn = self.findChild(QtWidgets.QPushButton, "btnOpenPMConfig")  # Open PM Config (file)
            if btn:
                btn.clicked.connect(self.on_open_pm_config)
        except Exception:
            pass
        try:
            btn = self.findChild(QtWidgets.QPushButton, "btnAction8")  # Open .env
            if btn:
                btn.clicked.connect(self.on_open_env)
        except Exception:
            pass
        try:
            btn = self.findChild(QtWidgets.QPushButton, "pushButton")  # Install .env
            if btn:
                btn.clicked.connect(self.on_install_env)
        except Exception:
            pass
        try:
            btn = self.findChild(QtWidgets.QPushButton, "btnAction1")  # Open GPT-R Config (file)
            if btn:
                btn.clicked.connect(self.on_open_gptr_config)
        except Exception:
            pass
        try:
            btn = self.findChild(QtWidgets.QPushButton, "btnAction2")  # Open FPF Config (file)
            if btn:
                btn.clicked.connect(self.on_open_fpf_config)
        except Exception:
            pass
        try:
            btn = self.findChild(QtWidgets.QPushButton, "btnAction3")  # Open MA Config (file)
            if btn:
                btn.clicked.connect(self.on_open_ma_config)
        except Exception:
            pass
        try:
            btn = self.findChild(QtWidgets.QPushButton, "btnAction4")  # Load Preset
            if btn:
                btn.clicked.connect(self.on_load_preset)
        except Exception:
            pass
        try:
            btn = self.findChild(QtWidgets.QPushButton, "btnAction5")  # Save Preset
            if btn:
                btn.clicked.connect(self.on_save_preset)
        except Exception:
            pass
        try:
            btn = self.findChild(QtWidgets.QPushButton, "btnAction6")  # Run One File
            if btn:
                btn.clicked.connect(self.on_run_one_file)
        except Exception:
            pass

        # Connect path browse/open buttons
        if self.btnBrowseInputFolder:
            self.btnBrowseInputFolder.clicked.connect(self.on_browse_input_folder)
        if self.btnOpenInputFolder:
            self.btnOpenInputFolder.clicked.connect(self.on_open_input_folder)
        if self.btnBrowseOutputFolder:
            self.btnBrowseOutputFolder.clicked.connect(self.on_browse_output_folder)
        if self.btnOpenOutputFolder:
            self.btnOpenOutputFolder.clicked.connect(self.on_open_output_folder)
        if self.btnBrowseInstructionsFile:
            self.btnBrowseInstructionsFile.clicked.connect(self.on_browse_instructions_file)
        if self.btnOpenInstructionsFolder:
            self.btnOpenInstructionsFolder.clicked.connect(self.on_open_instructions_folder)

        # Connect groupbox toggles
        if self.groupProvidersFPF:
            self.groupProvidersFPF.toggled.connect(lambda v, k="fpf": self.on_groupbox_toggled(k, v))
        if self.groupProvidersGPTR:
            self.groupProvidersGPTR.toggled.connect(lambda v, k="gptr": self.on_groupbox_toggled(k, v))
        if self.groupProvidersDR:
            self.groupProvidersDR.toggled.connect(lambda v, k="dr": self.on_groupbox_toggled(k, v))
        if self.groupProvidersMA:
            self.groupProvidersMA.toggled.connect(lambda v, k="ma": self.on_groupbox_toggled(k, v))
        if self.groupEvaluation:
            self.groupEvaluation.toggled.connect(lambda v, k="evaluation": self.on_groupbox_toggled(k, v))
        if self.groupEvaluation2:
            self.groupEvaluation2.toggled.connect(lambda v, k="pairwise": self.on_groupbox_toggled(k, v))

        # Set up dynamic readouts that show current slider value next to max label
        self._setup_slider_readouts()

        # Initial load (configs -> UI)
        self.load_current_values()
        # Refresh readouts to reflect initial values
        self._refresh_all_readouts()

    def show_error(self, text: str) -> None:
        QtWidgets.QMessageBox.critical(self, "Error", text)

    def show_info(self, text: str) -> None:
        QtWidgets.QMessageBox.information(self, "Info", text)

    def load_current_values(self) -> None:
        """
        Read config files and set slider values accordingly.
        """
        try:
            # process_markdown/config.yaml
            try:
                y = read_yaml(self.pm_config_yaml)
                iterations_default = int(y.get("iterations_default", 1) or 1)
                if self.sliderIterations_2:
                    self.sliderIterations_2.setValue(clamp_int(iterations_default, self.sliderIterations_2.minimum(), self.sliderIterations_2.maximum()))
            except Exception as e:
                print(f"[WARN] Could not load {self.pm_config_yaml}: {e}", flush=True)

            # FilePromptForge/default_config.yaml
            try:
                fy = read_yaml(self.fpf_yaml)
                if self.sliderGroundingMaxResults:
                    gmr = int((((fy.get("grounding") or {}).get("max_results")) or 5))
                    self.sliderGroundingMaxResults.setValue(clamp_int(gmr, self.sliderGroundingMaxResults.minimum(), self.sliderGroundingMaxResults.maximum()))
                if self.sliderGoogleMaxTokens:
                    gmt = int((((fy.get("google") or {}).get("max_tokens")) or 1500))
                    self.sliderGoogleMaxTokens.setValue(clamp_int(gmt, self.sliderGoogleMaxTokens.minimum(), self.sliderGoogleMaxTokens.maximum()))
            except Exception as e:
                print(f"[WARN] Could not load {self.fpf_yaml}: {e}", flush=True)

            # gpt-researcher/gpt_researcher/config/variables/default.py
            try:
                t = read_text(self.gptr_default_py)
                def set_from_py(slider: Optional[QtWidgets.QSlider], key: str, scale_temp: bool = False, default_val: int = 0):
                    if not slider:
                        return
                    val = extract_number_from_default_py(t, key)
                    if val is None:
                        # keep default slider value
                        return
                    if scale_temp:
                        v100 = int(round(float(val) * 100.0))
                        slider.setValue(clamp_int(v100, slider.minimum(), slider.maximum()))
                    else:
                        slider.setValue(clamp_int(int(round(val)), slider.minimum(), slider.maximum()))

                set_from_py(self.sliderFastTokenLimit, "FAST_TOKEN_LIMIT")
                set_from_py(self.sliderSmartTokenLimit, "SMART_TOKEN_LIMIT")
                set_from_py(self.sliderStrategicTokenLimit, "STRATEGIC_TOKEN_LIMIT")
                set_from_py(self.sliderBrowseChunkMaxLength, "BROWSE_CHUNK_MAX_LENGTH")
                set_from_py(self.sliderSummaryTokenLimit, "SUMMARY_TOKEN_LIMIT")
                set_from_py(self.sliderTemperature, "TEMPERATURE", scale_temp=True)
                set_from_py(self.sliderMaxSearchResultsPerQuery, "MAX_SEARCH_RESULTS_PER_QUERY")
                set_from_py(self.sliderTotalWords, "TOTAL_WORDS")
                set_from_py(self.sliderMaxIterations, "MAX_ITERATIONS")
                set_from_py(self.sliderMaxSubtopics, "MAX_SUBTOPICS")
                set_from_py(self.sliderDeepResearchBreadth, "DEEP_RESEARCH_BREADTH")
                set_from_py(self.sliderDeepResearchDepth, "DEEP_RESEARCH_DEPTH")
            except Exception as e:
                print(f"[WARN] Could not load {self.gptr_default_py}: {e}", flush=True)

            # gpt-researcher/multi_agents/task.json
            try:
                j = read_json(self.ma_task_json)
                ms = int(j.get("max_sections", 1))
                if self.sliderMaxSections:
                    self.sliderMaxSections.setValue(clamp_int(ms, self.sliderMaxSections.minimum(), self.sliderMaxSections.maximum()))
            except Exception as e:
                print(f"[WARN] Could not load {self.ma_task_json}: {e}", flush=True)

        except Exception as e:
            self.show_error(f"Failed to initialize UI from configs: {e}")

    def gather_values(self) -> Dict[str, Any]:
        """
        Collect slider values and other UI selections from UI.
        Returns a nested dict with keys for config, providers and enable flags.
        """
        vals: Dict[str, Any] = {}

        # General (config.yaml)
        if self.sliderIterations_2:
            vals["iterations_default"] = int(self.sliderIterations_2.value())

        # Paths (config.yaml)
        if self.lineInputFolder:
            vals["input_folder"] = str(self.lineInputFolder.text())
        if self.lineOutputFolder:
            vals["output_folder"] = str(self.lineOutputFolder.text())
        if self.lineInstructionsFile:
            vals["instructions_file"] = str(self.lineInstructionsFile.text())

        # FPF (default_config.yaml)
        if self.sliderGroundingMaxResults:
            vals.setdefault("fpf", {})["grounding.max_results"] = int(self.sliderGroundingMaxResults.value())
        if self.sliderGoogleMaxTokens:
            vals.setdefault("fpf", {})["google.max_tokens"] = int(self.sliderGoogleMaxTokens.value())

        # GPTR (default.py)
        if self.sliderFastTokenLimit:
            vals["FAST_TOKEN_LIMIT"] = int(self.sliderFastTokenLimit.value())
        if self.sliderSmartTokenLimit:
            vals["SMART_TOKEN_LIMIT"] = int(self.sliderSmartTokenLimit.value())
        if self.sliderStrategicTokenLimit:
            vals["STRATEGIC_TOKEN_LIMIT"] = int(self.sliderStrategicTokenLimit.value())
        if self.sliderBrowseChunkMaxLength:
            vals["BROWSE_CHUNK_MAX_LENGTH"] = int(self.sliderBrowseChunkMaxLength.value())
        if self.sliderSummaryTokenLimit:
            vals["SUMMARY_TOKEN_LIMIT"] = int(self.sliderSummaryTokenLimit.value())
        if self.sliderTemperature:
            vals["TEMPERATURE"] = float(temp_from_slider(int(self.sliderTemperature.value())))
        if self.sliderMaxSearchResultsPerQuery:
            vals["MAX_SEARCH_RESULTS_PER_QUERY"] = int(self.sliderMaxSearchResultsPerQuery.value())
        if self.sliderTotalWords:
            vals["TOTAL_WORDS"] = int(self.sliderTotalWords.value())
        if self.sliderMaxIterations:
            vals["MAX_ITERATIONS"] = int(self.sliderMaxIterations.value())
        if self.sliderMaxSubtopics:
            vals["MAX_SUBTOPICS"] = int(self.sliderMaxSubtopics.value())

        # DR (default.py)
        if self.sliderDeepResearchBreadth:
            vals["DEEP_RESEARCH_BREADTH"] = int(self.sliderDeepResearchBreadth.value())
        if self.sliderDeepResearchDepth:
            vals["DEEP_RESEARCH_DEPTH"] = int(self.sliderDeepResearchDepth.value())

        # MA (task.json)
        if self.sliderMaxSections:
            vals.setdefault("ma", {})["max_sections"] = int(self.sliderMaxSections.value())

        # Provider/model selections are UI-only and are NOT persisted to process_markdown/config.yaml.
        # We intentionally do not collect or write providers/models into vals for config.yaml.
        # If we want to remember providers/models, use presets.yaml (separate persistence).

        # Enable flags from checkable groupboxes (if unchecked, intent is to disable)
        enables: Dict[str, bool] = {}
        if self.groupProvidersFPF is not None:
            enables["fpf"] = bool(self.groupProvidersFPF.isChecked())
        if self.groupProvidersGPTR is not None:
            enables["gptr"] = bool(self.groupProvidersGPTR.isChecked())
        if self.groupProvidersDR is not None:
            enables["dr"] = bool(self.groupProvidersDR.isChecked())
        if self.groupProvidersMA is not None:
            enables["ma"] = bool(self.groupProvidersMA.isChecked())
        if self.groupEvaluation is not None:
            enables["evaluation"] = bool(self.groupEvaluation.isChecked())
        if self.groupEvaluation2 is not None:
            enables["pairwise"] = bool(self.groupEvaluation2.isChecked())
        if enables:
            vals["enable"] = enables

        return vals

    def write_configs(self, vals: Dict[str, Any]) -> None:
        """
        Persist collected slider values into the underlying config files.
        """
        # process_markdown/config.yaml
        try:
            y = read_yaml(self.pm_config_yaml)

            # Paths
            if "input_folder" in vals:
                y["input_folder"] = vals["input_folder"]
            if "output_folder" in vals:
                y["output_folder"] = vals["output_folder"]
            if "instructions_file" in vals:
                y["instructions_file"] = vals["instructions_file"]

            # iterations_default
            y["iterations_default"] = int(vals.get("iterations_default", y.get("iterations_default", 1) or 1))

            # Enable/disable iteration flags and set explicit per-report-type iteration counts.
            # For each report type: if disabled -> 0, if enabled -> set to iterations_default.
            it = y.get("iterations", {})
            if not isinstance(it, dict):
                it = {}
            en = vals.get("enable", {})
            if not isinstance(en, dict):
                en = {}
            for rpt in ("fpf", "gptr", "dr", "ma"):
                if en.get(rpt) is False:
                    it[rpt] = 0
                else:
                    # Use iterations_default when enabled (or preserve existing non-zero)
                    it[rpt] = int(vals.get("iterations_default", it.get(rpt) or 1))
            y["iterations"] = it

            # providers section
            provs = y.get("providers", {})
            if not isinstance(provs, dict):
                provs = {}
            for key, pdata in vals.get("providers", {}).items():
                if not isinstance(pdata, dict):
                    continue
                sub = provs.get(key, {})
                if not isinstance(sub, dict):
                    sub = {}
                if "provider" in pdata:
                    sub["provider"] = pdata["provider"]
                if "model" in pdata:
                    sub["model"] = pdata["model"]
                provs[key] = sub
            if provs:
                y["providers"] = provs

            write_yaml(self.pm_config_yaml, y)

            # Detailed console output: list each written variable and destination file
            try:
                log_lines = []
                # Paths
                for k in ("input_folder", "output_folder", "instructions_file"):
                    if k in vals:
                        log_lines.append(f"Wrote {k} = {vals[k]!r} -> {self.pm_config_yaml}")
                # iterations_default
                if "iterations_default" in vals:
                    log_lines.append(f"Wrote iterations_default = {vals['iterations_default']} -> {self.pm_config_yaml}")
                # enable flags
                for k, v in vals.get("enable", {}).items():
                    log_lines.append(f"Wrote enable.{k} = {bool(v)} -> {self.pm_config_yaml}")
                # (provider/model keys intentionally not persisted to config.yaml)
                if log_lines:
                    print("[OK] Wrote to", self.pm_config_yaml)
                    for ln in log_lines:
                        print("  -", ln)
                else:
                    print(f"[OK] Wrote {self.pm_config_yaml} (no detailed keys found in vals)", flush=True)
            except Exception:
                # Fallback simple message
                print(f"[OK] Wrote {self.pm_config_yaml}", flush=True)
        except Exception as e:
            raise RuntimeError(f"Failed to write {self.pm_config_yaml}: {e}")

        # FilePromptForge/default_config.yaml
        try:
            fy = read_yaml(self.fpf_yaml)
            grounding = fy.get("grounding")
            if not isinstance(grounding, dict):
                grounding = {}
                fy["grounding"] = grounding
            # support both top-level keys and nested 'fpf' keys
            gmr = None
            if "grounding.max_results" in vals:
                gmr = int(vals["grounding.max_results"])
            else:
                gmr = int((vals.get("fpf", {}) or {}).get("grounding.max_results") or 0)
            if gmr is not None and gmr != 0:
                grounding["max_results"] = int(gmr)

            google = fy.get("google")
            if not isinstance(google, dict):
                google = {}
                fy["google"] = google
            gmt = None
            if "google.max_tokens" in vals:
                gmt = int(vals["google.max_tokens"])
            else:
                gmt = int((vals.get("fpf", {}) or {}).get("google.max_tokens") or 0)
            if gmt is not None and gmt != 0:
                google["max_tokens"] = int(gmt)

            write_yaml(self.fpf_yaml, fy)

            # Detailed console output
            try:
                log_lines = []
                if gmr:
                    log_lines.append(f"Wrote grounding.max_results = {gmr} -> {self.fpf_yaml}")
                if gmt:
                    log_lines.append(f"Wrote google.max_tokens = {gmt} -> {self.fpf_yaml}")
                if log_lines:
                    print("[OK] Wrote to", self.fpf_yaml)
                    for ln in log_lines:
                        print("  -", ln)
                else:
                    print(f"[OK] Wrote {self.fpf_yaml} (no relevant keys found in vals)", flush=True)
            except Exception:
                print(f"[OK] Wrote {self.fpf_yaml}", flush=True)
        except Exception as e:
            raise RuntimeError(f"Failed to write {self.fpf_yaml}: {e}")

        # gpt-researcher/gpt_researcher/config/variables/default.py
        try:
            t = read_text(self.gptr_default_py)
            if not t:
                raise RuntimeError("default.py not found or empty")
            keys_to_update = [
                "FAST_TOKEN_LIMIT",
                "SMART_TOKEN_LIMIT",
                "STRATEGIC_TOKEN_LIMIT",
                "BROWSE_CHUNK_MAX_LENGTH",
                "SUMMARY_TOKEN_LIMIT",
                "TEMPERATURE",
                "MAX_SEARCH_RESULTS_PER_QUERY",
                "TOTAL_WORDS",
                "MAX_ITERATIONS",
                "MAX_SUBTOPICS",
                "DEEP_RESEARCH_BREADTH",
                "DEEP_RESEARCH_DEPTH",
            ]
            replaced_any = False
            missing: list[str] = []
            updated_keys: list[str] = []
            for k in keys_to_update:
                if k == "TEMPERATURE":
                    if "TEMPERATURE" in vals:
                        t2, ok = replace_number_in_default_py(t, "TEMPERATURE", float(vals["TEMPERATURE"]))
                        if ok:
                            t = t2
                            replaced_any = True
                            updated_keys.append("TEMPERATURE")
                        else:
                            missing.append(k)
                else:
                    if k in vals:
                        try:
                            newv = float(vals[k])
                        except Exception:
                            newv = float(vals[k])
                        t2, ok = replace_number_in_default_py(t, k, float(newv))
                        if ok:
                            t = t2
                            replaced_any = True
                            updated_keys.append(k)
                        else:
                            missing.append(k)
            if replaced_any:
                write_text(self.gptr_default_py, t)
                # Detailed console output for default.py updates
                try:
                    print("[OK] Wrote to", self.gptr_default_py)
                    for k in updated_keys:
                        val_display = vals.get(k) if k != "TEMPERATURE" else vals.get("TEMPERATURE")
                        print(f"  - Wrote {k} = {val_display!r} -> {self.gptr_default_py}")
                except Exception:
                    print(f"[OK] Wrote {self.gptr_default_py}", flush=True)
            if missing:
                print(f"[WARN] Some keys were not found for update in default.py: {', '.join(missing)}", flush=True)
        except Exception as e:
            raise RuntimeError(f"Failed to write {self.gptr_default_py}: {e}")

        # gpt-researcher/multi_agents/task.json
        try:
            j = read_json(self.ma_task_json)
            if "ma.max_sections" in vals:
                j["max_sections"] = int(vals["ma.max_sections"])
            write_json(self.ma_task_json, j)
            # Detailed output for task.json
            try:
                if "ma.max_sections" in vals:
                    print("[OK] Wrote to", self.ma_task_json)
                    print(f"  - Wrote ma.max_sections = {int(vals['ma.max_sections'])} -> {self.ma_task_json}")
                else:
                    print(f"[OK] Wrote {self.ma_task_json} (no ma.max_sections in vals)", flush=True)
            except Exception:
                print(f"[OK] Wrote {self.ma_task_json}", flush=True)
        except Exception as e:
            raise RuntimeError(f"Failed to write {self.ma_task_json}: {e}")

    def on_write_clicked(self) -> None:
        try:
            vals = self.gather_values()
            self.write_configs(vals)
            self.show_info("Configurations have been written successfully.")
        except Exception as e:
            self.show_error(str(e))

    def on_run_clicked(self) -> None:
        if self.btn_run:
            self.btn_run.setEnabled(False)
        try:
            vals = self.gather_values()
            self.write_configs(vals)
        except Exception as e:
            if self.btn_run:
                self.btn_run.setEnabled(True)
            self.show_error(str(e))
            return

        # Launch generate.py in a thread so GUI stays responsive
        self.runner_thread = RunnerThread(self.pm_dir, self.generate_py, self)
        self.runner_thread.finished_ok.connect(self._on_generate_finished)
        self.runner_thread.start()

    def _on_generate_finished(self, ok: bool, code: int, message: str) -> None:
        if self.btn_run:
            self.btn_run.setEnabled(True)
        if ok:
            self.show_info(message)
        else:
            self.show_error(message)


    def on_master_quality_changed(self, value: int) -> None:
        """
        When the 'Master Quality' slider changes, proportionally adjust all other sliders
        based on their own min/max ranges. This only affects in-UI values; config files
        are still written only on 'Write to Configs' or 'Run'.
        """
        try:
            s = getattr(self, "sliderMasterQuality", None)
            if not s:
                return
            smin, smax = s.minimum(), s.maximum()
            if smax <= smin:
                percent = 0.0
            else:
                percent = (float(value) - float(smin)) / float(smax - smin)
                if percent < 0.0:
                    percent = 0.0
                if percent > 1.0:
                    percent = 1.0
            self._apply_master_quality(percent)
        except Exception as e:
            print(f"[WARN] Master quality change failed: {e}", flush=True)

    def _apply_master_quality(self, percent: float) -> None:
        """
        Apply proportional scaling to all controlled sliders using the given percent in [0,1].
        """
        sliders = [
            self.sliderIterations_2,
            self.sliderGroundingMaxResults,
            self.sliderGoogleMaxTokens,
            self.sliderFastTokenLimit,
            self.sliderSmartTokenLimit,
            self.sliderStrategicTokenLimit,
            self.sliderBrowseChunkMaxLength,
            self.sliderSummaryTokenLimit,
            self.sliderTemperature,
            self.sliderMaxSearchResultsPerQuery,
            self.sliderTotalWords,
            self.sliderMaxIterations,
            self.sliderMaxSubtopics,
            self.sliderDeepResearchBreadth,
            self.sliderDeepResearchDepth,
            self.sliderMaxSections,
        ]
        for sl in sliders:
            self._scale_slider(sl, percent)
        # After programmatic changes, refresh value readouts since signals are blocked
        self._refresh_all_readouts()

    def _scale_slider(self, slider: Optional[QtWidgets.QSlider], percent: float) -> None:
        """
        Set a slider to min + percent*(max-min), blocking signals to avoid feedback loops.
        """
        if not slider:
            return
        try:
            smin = slider.minimum()
            smax = slider.maximum()
            if smax <= smin:
                return
            target = smin + round(percent * (smax - smin))
            prev = slider.blockSignals(True)
            slider.setValue(int(target))
            slider.blockSignals(prev)
        except Exception as e:
            print(f"[WARN] Scaling slider failed: {e}", flush=True)

    def _display_value_for(self, slider_name: str, value: int) -> str:
        """
        Convert a slider integer value to display text.
        Temperature uses mapped float 0.00-1.00; others show integer.
        """
        if slider_name == "sliderTemperature":
            return f"{temp_from_slider(value):.2f}"
        return str(int(value))

    def _setup_slider_readouts(self) -> None:
        """
        Bind valueChanged handlers for each slider to update the 'max' label to show
        'current / max' while the min label remains as-is. This provides live feedback.
        """
        # (slider_objectName, min_label_objectName, max_label_objectName)
        self._readout_map = [
            ("sliderIterations", "labelIterationsMin", "labelIterationsMax"),
            ("sliderIterations_2", "labelIterationsMin_2", "labelIterationsMax_2"),
            ("sliderGroundingMaxResults", "labelGroundingMaxResultsMin", "labelGroundingMaxResultsMax"),
            ("sliderGoogleMaxTokens", "labelGoogleMaxTokensMin", "labelGoogleMaxTokensMax"),
            ("sliderFastTokenLimit", "labelFastTokenLimitMin", "labelFastTokenLimitMax"),
            ("sliderSmartTokenLimit", "labelSmartTokenLimitMin", "labelSmartTokenLimitMax"),
            ("sliderStrategicTokenLimit", "labelStrategicTokenLimitMin", "labelStrategicTokenLimitMax"),
            ("sliderBrowseChunkMaxLength", "labelBrowseChunkMaxLengthMin", "labelBrowseChunkMaxLengthMax"),
            ("sliderSummaryTokenLimit", "labelSummaryTokenLimitMin", "labelSummaryTokenLimitMax"),
            ("sliderTemperature", "labelTemperatureMin", "labelTemperatureMax"),
            ("sliderMaxSearchResultsPerQuery", "labelMaxSearchResultsPerQueryMin", "labelMaxSearchResultsPerQueryMax"),
            ("sliderTotalWords", "labelTotalWordsMin", "labelTotalWordsMax"),
            ("sliderMaxIterations", "labelMaxIterationsMin", "labelMaxIterationsMax"),
            ("sliderMaxSubtopics", "labelMaxSubtopicsMin", "labelMaxSubtopicsMax"),
            ("sliderDeepResearchBreadth", "labelDeepResearchBreadthMin", "labelDeepResearchBreadthMax"),
            ("sliderDeepResearchDepth", "labelDeepResearchDepthMin", "labelDeepResearchDepthMax"),
            ("sliderMaxSections", "labelMaxSectionsMin", "labelMaxSectionsMax"),
        ]
        for s_name, min_name, max_name in self._readout_map:
            slider = self.findChild(QtWidgets.QSlider, s_name)
            # Connect handler if slider exists
            if slider is not None:
                slider.valueChanged.connect(lambda v, sn=s_name: self._update_slider_readout(sn))

    def _update_slider_readout(self, slider_name: str) -> None:
        """
        Update the 'max' label to show 'current / max'. For temperature, current shows 0.00-1.00,
        and max shows 1.0.
        """
        slider = self.findChild(QtWidgets.QSlider, slider_name)
        if slider is None:
            return
        # Find associated max label by name from mapping
        max_label_name = None
        for s_name, _min_name, max_name in getattr(self, "_readout_map", []):
            if s_name == slider_name:
                max_label_name = max_name
                break
        if not max_label_name:
            return
        max_label = self.findChild(QtWidgets.QLabel, max_label_name)
        if max_label is None:
            return

        current_disp = self._display_value_for(slider_name, int(slider.value()))
        if slider_name == "sliderTemperature":
            max_disp = "1.0"
        else:
            max_disp = str(int(slider.maximum()))
        max_label.setText(f"{current_disp} / {max_disp}")

    def _refresh_all_readouts(self) -> None:
        """
        Call _update_slider_readout for all mapped sliders to sync labels with current values.
        """
        for s_name, _min_name, _max_name in getattr(self, "_readout_map", []):
            self._update_slider_readout(s_name)

    # ---- Additional handlers wired for paths/providers/groupboxes ----
    def on_browse_input_folder(self) -> None:
        """Open a folder dialog and set input folder line edit."""
        try:
            dlg = QtWidgets.QFileDialog(self, "Select Input Folder")
            dlg.setFileMode(QtWidgets.QFileDialog.Directory)
            dlg.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
            if dlg.exec_():
                sel = dlg.selectedFiles()
                if sel:
                    path = sel[0]
                    if self.lineInputFolder:
                        self.lineInputFolder.setText(path)
        except Exception as e:
            print(f"[WARN] on_browse_input_folder failed: {e}", flush=True)

    def on_open_input_folder(self) -> None:
        """Open OS explorer at input folder path."""
        try:
            path = None
            if self.lineInputFolder:
                path = self.lineInputFolder.text()
            if not path:
                return
            self._open_in_file_explorer(path)
        except Exception as e:
            print(f"[WARN] on_open_input_folder failed: {e}", flush=True)

    def on_browse_output_folder(self) -> None:
        """Open a folder dialog and set output folder line edit."""
        try:
            dlg = QtWidgets.QFileDialog(self, "Select Output Folder")
            dlg.setFileMode(QtWidgets.QFileDialog.Directory)
            dlg.setOption(QtWidgets.QFileDialog.ShowDirsOnly, True)
            if dlg.exec_():
                sel = dlg.selectedFiles()
                if sel:
                    path = sel[0]
                    if self.lineOutputFolder:
                        self.lineOutputFolder.setText(path)
        except Exception as e:
            print(f"[WARN] on_browse_output_folder failed: {e}", flush=True)

    def on_open_output_folder(self) -> None:
        """Open OS explorer at output folder path."""
        try:
            path = None
            if self.lineOutputFolder:
                path = self.lineOutputFolder.text()
            if not path:
                return
            self._open_in_file_explorer(path)
        except Exception as e:
            print(f"[WARN] on_open_output_folder failed: {e}", flush=True)

    def on_browse_instructions_file(self) -> None:
        """Open file dialog to pick instructions file."""
        try:
            fname, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Instructions File", "", "Text Files (*.txt);;All Files (*)")
            if fname:
                if self.lineInstructionsFile:
                    self.lineInstructionsFile.setText(fname)
        except Exception as e:
            print(f"[WARN] on_browse_instructions_file failed: {e}", flush=True)

    def on_open_instructions_folder(self) -> None:
        """Open OS explorer at the folder containing the instructions file."""
        try:
            path = None
            if self.lineInstructionsFile:
                path = self.lineInstructionsFile.text()
            if not path:
                return
            p = Path(path)
            if p.exists():
                self._open_in_file_explorer(str(p.parent))
        except Exception as e:
            print(f"[WARN] on_open_instructions_folder failed: {e}", flush=True)

    def on_groupbox_toggled(self, key: str, checked: bool) -> None:
        """
        Handler when a checkable groupbox is toggled.
        key is one of 'fpf','gptr','dr','ma','evaluation','pairwise'
        """
        # No immediate side-effect is required here; states are gathered and written by on_write_clicked/on_run_clicked.
        try:
            # Provide lightweight feedback by updating statusbar or printing
            status = f"{key} enabled" if checked else f"{key} disabled"
            try:
                self.statusBar().showMessage(status, 3000)
            except Exception:
                print(f"[INFO] {status}", flush=True)
        except Exception as e:
            print(f"[WARN] on_groupbox_toggled failed: {e}", flush=True)

    def _open_in_file_explorer(self, path: str) -> None:
        """Open path in OS file explorer (cross-platform)."""
        try:
            p = Path(path)
            if not p.exists():
                return
            if sys.platform.startswith("win"):
                os.startfile(str(p))
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", str(p)])
            else:
                subprocess.Popen(["xdg-open", str(p)])
        except Exception as e:
            print(f"[WARN] _open_in_file_explorer failed: {e}", flush=True)

    # ---- Bottom toolbar handlers ----
    def on_download_and_install(self) -> None:
        """Run download_and_extract.py in background (non-blocking)."""
        try:
            script = self.pm_dir / "download_and_extract.py"
            if not script.exists():
                self.show_error(f"download_and_extract.py not found at {script}")
                return
            cmd = [sys.executable, str(script)]
            try:
                proc = subprocess.Popen(cmd, cwd=str(self.pm_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                self.show_info("Download started in background. Check console for output.")
            except Exception as e:
                self.show_error(f"Failed to start download: {e}")
        except Exception as e:
            print(f"[WARN] on_download_and_install failed: {e}", flush=True)

    def on_open_env(self) -> None:
        """Open the .env file (or .env.example) with the system default application, if present."""
        try:
            candidate = self.pm_dir / "gpt-researcher" / ".env"
            if not candidate.exists():
                candidate = self.pm_dir / "gpt-researcher" / ".env.example"
            if candidate.exists():
                # On Windows, os.startfile opens associated app; on other platforms use system command
                if sys.platform.startswith("win"):
                    os.startfile(str(candidate))
                elif sys.platform.startswith("darwin"):
                    subprocess.Popen(["open", str(candidate)])
                else:
                    subprocess.Popen(["xdg-open", str(candidate)])
            else:
                self.show_info("No .env or .env.example found in gpt-researcher.")
        except Exception as e:
            print(f"[WARN] on_open_env failed: {e}", flush=True)

    def on_install_env(self) -> None:
        """Create .env from .env.example if possible (ask for confirmation)."""
        try:
            example = self.pm_dir / "gpt-researcher" / ".env.example"
            target = self.pm_dir / "gpt-researcher" / ".env"
            if not example.exists():
                self.show_info("No .env.example found to install from.")
                return
            if target.exists():
                res = QtWidgets.QMessageBox.question(self, "Overwrite .env?", f".env already exists at {target}. Overwrite?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
                if res != QtWidgets.QMessageBox.Yes:
                    return
            shutil.copy2(str(example), str(target))
            self.show_info(f"Installed .env from .env.example to {target}")
        except Exception as e:
            self.show_error(f"Failed to install .env: {e}")

    def on_open_gptr_config(self) -> None:
        """Open the GPT Researcher default.py file in the system editor (if present)."""
        try:
            if self.gptr_default_py.exists():
                if sys.platform.startswith("win"):
                    os.startfile(str(self.gptr_default_py))
                elif sys.platform.startswith("darwin"):
                    subprocess.Popen(["open", str(self.gptr_default_py)])
                else:
                    subprocess.Popen(["xdg-open", str(self.gptr_default_py)])
            else:
                self.show_info(f"GPT-R default.py not found at {self.gptr_default_py}")
        except Exception as e:
            print(f"[WARN] on_open_gptr_config failed: {e}", flush=True)

    def on_open_fpf_config(self) -> None:
        """Open the FilePromptForge default_config.yaml file in the system editor (if present)."""
        try:
            if self.fpf_yaml.exists():
                if sys.platform.startswith("win"):
                    os.startfile(str(self.fpf_yaml))
                elif sys.platform.startswith("darwin"):
                    subprocess.Popen(["open", str(self.fpf_yaml)])
                else:
                    subprocess.Popen(["xdg-open", str(self.fpf_yaml)])
            else:
                self.show_info(f"FilePromptForge default_config.yaml not found at {self.fpf_yaml}")
        except Exception as e:
            print(f"[WARN] on_open_fpf_config failed: {e}", flush=True)

    def on_open_ma_config(self) -> None:
        """Open the multi-agent task.json file in the system editor (if present)."""
        try:
            if self.ma_task_json.exists():
                if sys.platform.startswith("win"):
                    os.startfile(str(self.ma_task_json))
                elif sys.platform.startswith("darwin"):
                    subprocess.Popen(["open", str(self.ma_task_json)])
                else:
                    subprocess.Popen(["xdg-open", str(self.ma_task_json)])
            else:
                self.show_info(f"MA task.json not found at {self.ma_task_json}")
        except Exception as e:
            print(f"[WARN] on_open_ma_config failed: {e}", flush=True)

    def on_open_pm_config(self) -> None:
        """Open process_markdown/config.yaml in default editor (if present)."""
        try:
            if self.pm_config_yaml.exists():
                if sys.platform.startswith("win"):
                    os.startfile(str(self.pm_config_yaml))
                elif sys.platform.startswith("darwin"):
                    subprocess.Popen(["open", str(self.pm_config_yaml)])
                else:
                    subprocess.Popen(["xdg-open", str(self.pm_config_yaml)])
            else:
                self.show_info(f"PM config.yaml not found at {self.pm_config_yaml}")
        except Exception as e:
            print(f"[WARN] on_open_pm_config failed: {e}", flush=True)

    def on_save_preset(self) -> None:
        """Ask for a preset name and save current UI state to presets.yaml."""
        try:
            name, ok = QtWidgets.QInputDialog.getText(self, "Save Preset", "Preset name:")
            if not ok or not name:
                return
            presets_path = self.pm_dir / "presets.yaml"
            presets = {}
            try:
                presets = read_yaml(presets_path)
            except Exception:
                presets = {}
            vals = self.gather_values()
            presets[name] = vals
            write_yaml(presets_path, presets)
            self.show_info(f"Saved preset '{name}' to {presets_path}")
        except Exception as e:
            self.show_error(f"Failed to save preset: {e}")

    def on_load_preset(self) -> None:
        """Load a preset from presets.yaml and apply to UI."""
        try:
            presets_path = self.pm_dir / "presets.yaml"
            if not presets_path.exists():
                self.show_info("No presets found.")
                return
            presets = read_yaml(presets_path)
            if not isinstance(presets, dict) or not presets:
                self.show_info("No presets available.")
                return
            names = list(presets.keys())
            item, ok = QtWidgets.QInputDialog.getItem(self, "Load Preset", "Select preset:", names, 0, False)
            if not ok or not item:
                return
            data = presets.get(item, {})
            self._apply_preset(data)
            self.show_info(f"Applied preset '{item}'")
        except Exception as e:
            self.show_error(f"Failed to load preset: {e}")

    def _apply_preset(self, data: Dict[str, Any]) -> None:
        """Apply preset dict to UI widgets (partial, best-effort)."""
        try:
            # Paths
            if "input_folder" in data and self.lineInputFolder:
                self.lineInputFolder.setText(str(data["input_folder"]))
            if "output_folder" in data and self.lineOutputFolder:
                self.lineOutputFolder.setText(str(data["output_folder"]))
            if "instructions_file" in data and self.lineInstructionsFile:
                self.lineInstructionsFile.setText(str(data["instructions_file"]))

            # Providers
            provs = data.get("providers", {})
            if isinstance(provs, dict):
                fpf = provs.get("fpf", {})
                if isinstance(fpf, dict):
                    if "provider" in fpf and self.comboFPFProvider:
                        self._set_combobox_text(self.comboFPFProvider, str(fpf["provider"]))
                    if "model" in fpf and self.comboFPFModel:
                        self._set_combobox_text(self.comboFPFModel, str(fpf["model"]))
                gptr = provs.get("gptr", {})
                if isinstance(gptr, dict):
                    if "provider" in gptr and self.comboGPTRProvider:
                        self._set_combobox_text(self.comboGPTRProvider, str(gptr["provider"]))
                    if "model" in gptr and self.comboGPTRModel:
                        self._set_combobox_text(self.comboGPTRModel, str(gptr["model"]))
                dr = provs.get("dr", {})
                if isinstance(dr, dict):
                    if "provider" in dr and self.comboDRProvider:
                        self._set_combobox_text(self.comboDRProvider, str(dr["provider"]))
                    if "model" in dr and self.comboDRModel:
                        self._set_combobox_text(self.comboDRModel, str(dr["model"]))
                ma = provs.get("ma", {})
                if isinstance(ma, dict):
                    if "provider" in ma and self.comboMAProvider:
                        self._set_combobox_text(self.comboMAProvider, str(ma["provider"]))
                    if "model" in ma and self.comboMAModel:
                        self._set_combobox_text(self.comboMAModel, str(ma["model"]))

            # Enables
            en = data.get("enable", {})
            if isinstance(en, dict):
                if "fpf" in en and self.groupProvidersFPF:
                    self.groupProvidersFPF.setChecked(bool(en["fpf"]))
                if "gptr" in en and self.groupProvidersGPTR:
                    self.groupProvidersGPTR.setChecked(bool(en["gptr"]))
                if "dr" in en and self.groupProvidersDR:
                    self.groupProvidersDR.setChecked(bool(en["dr"]))
                if "ma" in en and self.groupProvidersMA:
                    self.groupProvidersMA.setChecked(bool(en["ma"]))

            # Sliders (limited set)
            if "iterations_default" in data and self.sliderIterations_2:
                self.sliderIterations_2.setValue(int(data["iterations_default"]))
            # More keys can be applied similarly as needed.
        except Exception as e:
            print(f"[WARN] _apply_preset failed: {e}", flush=True)

    def _set_combobox_text(self, combo: QtWidgets.QComboBox, text: str) -> None:
        """Set combobox current text if exists; otherwise add and select."""
        try:
            idx = combo.findText(text)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            else:
                combo.addItem(text)
                combo.setCurrentIndex(combo.count() - 1)
        except Exception as e:
            print(f"[WARN] _set_combobox_text failed: {e}", flush=True)

    def on_run_one_file(self) -> None:
        """Prompt for a single input file and start generate.py with SINGLE_INPUT_FILE env var."""
        try:
            start_dir = str(self.pm_dir / "test" / "mdinputs")
            fname, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select input file to run", start_dir, "Markdown Files (*.md);;Text Files (*.txt);;All Files (*)")
            if not fname:
                return
            cmd = [sys.executable, "-u", str(self.generate_py)]
            env = os.environ.copy()
            env["SINGLE_INPUT_FILE"] = fname
            try:
                proc = subprocess.Popen(cmd, cwd=str(self.pm_dir), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                self.show_info("Started generate.py for single file in background. Check console for output.")
            except Exception as e:
                self.show_error(f"Failed to start generate for single file: {e}")
        except Exception as e:
            print(f"[WARN] on_run_one_file failed: {e}", flush=True)

def launch_gui() -> int:
    """
    Launcher entrypoint for the GUI (separate from module import).
    """
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec_()
