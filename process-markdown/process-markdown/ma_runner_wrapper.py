"""
ma_runner_wrapper.py

Replaces the previous copy-then-write temp-copy logic by writing a runtime task.json
directly into the repository multi_agents directory (atomically), invoking the multi_agents
runner as a subprocess with PYTHONPATH pointed at the gpt-researcher package, then
collecting outputs into the provided run_out_dir.

This implementation intentionally does NOT use global locking so concurrent runs are
possible in the future; it uses atomic os.replace on task.json and per-run output
directories to avoid partial-read races.
"""
import os
import sys
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GPT_RESEARCHER_DIR = os.path.join(REPO_ROOT, "gpt-researcher-3.2.9")
MULTI_AGENTS_DIR = os.path.join(GPT_RESEARCHER_DIR, "multi_agents")
TASK_JSON_PATH = os.path.join(MULTI_AGENTS_DIR, "task.json")

def _atomic_write_task_json(task_dict: Dict) -> Optional[str]:
    """
    Atomically write task_dict to MULTI_AGENTS_DIR/task.json.
    Returns path to backup file if an original was backed up, else None.
    """
    backup_path = None
    try:
        # Backup existing task.json if present
        if os.path.exists(TASK_JSON_PATH):
            backup_path = TASK_JSON_PATH + ".bak"
            os.replace(TASK_JSON_PATH, backup_path)

        # Write to a tmp file in the same directory then replace atomically
        tmp_path = TASK_JSON_PATH + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(task_dict, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, TASK_JSON_PATH)
        return backup_path
    except Exception:
        # If atomic write failed, try to restore backup immediately
        if backup_path and os.path.exists(backup_path):
            try:
                os.replace(backup_path, TASK_JSON_PATH)
            except Exception:
                pass
        raise

def _restore_backup(backup_path: Optional[str]):
    """
    Restore the backup task.json if provided, else remove the runtime task.json.
    """
    try:
        if backup_path and os.path.exists(backup_path):
            os.replace(backup_path, TASK_JSON_PATH)
        else:
            # Remove runtime task if exists
            if os.path.exists(TASK_JSON_PATH):
                os.remove(TASK_JSON_PATH)
    except Exception:
        # Ignore restore errors; caller may inspect preserved files
        pass

def _run_multi_agents_subprocess(run_stdout_path: str) -> subprocess.CompletedProcess:
    """
    Run the multi_agents runner as a subprocess using the gpt-researcher package.
    Returns CompletedProcess object.
    """
    env = os.environ.copy()
    # Ensure the gpt-researcher package dir is on PYTHONPATH so '-m multi_agents.main' resolves
    # Use absolute GPT_RESEARCHER_DIR as module root
    env["PYTHONPATH"] = GPT_RESEARCHER_DIR + (os.pathsep + env.get("PYTHONPATH", "")) if env.get("PYTHONPATH") else GPT_RESEARCHER_DIR

    # Force UTF-8 in child Python processes to avoid Windows chmap encoding issues
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    # Use -m multi_agents.main to run the example entrypoint
    cmd = [sys.executable, "-m", "multi_agents.main"]

    # Run in the multi_agents dir so the script's relative open_task() reads task.json from that folder
    # Capture output as UTF-8 and replace undecodable bytes to avoid UnicodeDecodeError on Windows
    proc = subprocess.run(cmd, cwd=MULTI_AGENTS_DIR, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    # Save stdout/stderr for auditing
    try:
        with open(run_stdout_path, "w", encoding="utf-8") as f:
            f.write("=== STDOUT ===\n")
            f.write(proc.stdout or "")
            f.write("\n=== STDERR ===\n")
            f.write(proc.stderr or "")
    except Exception:
        pass
    return proc

def _collect_outputs(run_tmp_dir: str, run_out_dir: str) -> List[str]:
    """
    Collect outputs from MULTI_AGENTS_DIR/outputs (or similar) into run_out_dir.
    Returns list of moved output paths.
    """
    collected = []
    # Common outputs locations used by the MA example
    candidate_dirs = [
        os.path.join(MULTI_AGENTS_DIR, "outputs"),
        os.path.join(MULTI_AGENTS_DIR, "output"),
        os.path.join(MULTI_AGENTS_DIR, "runs"),
    ]
    for cand in candidate_dirs:
        if os.path.exists(cand):
            for root, _, files in os.walk(cand):
                for file in files:
                    src = os.path.join(root, file)
                    # create mirrored structure under run_out_dir
                    rel = os.path.relpath(src, cand)
                    dest = os.path.join(run_out_dir, rel)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    try:
                        shutil.copy2(src, dest)
                        collected.append(dest)
                    except Exception:
                        # best-effort copy
                        try:
                            shutil.copy(src, dest)
                            collected.append(dest)
                        except Exception:
                            pass
    return collected

def run_ma_with_runtime_task(task_dict: Dict, run_out_dir: str) -> List[str]:
    """
    Core entrypoint used by the process runner:
      - Atomically write task.json to repo multi_agents folder
      - Run multi_agents.main as a subprocess (cwd=multi_agents dir) with PYTHONPATH set
      - Collect outputs into run_out_dir
      - Restore backup task.json (if any) or remove runtime task.json
    Returns list of produced output file paths.
    """
    os.makedirs(run_out_dir, exist_ok=True)
    run_stdout_path = os.path.join(run_out_dir, "ma_run_stdout.log")
    backup_path = None
    produced = []
    try:
        backup_path = _atomic_write_task_json(task_dict)
        proc = _run_multi_agents_subprocess(run_stdout_path)
        if proc.returncode != 0:
            # preserve logs and return whatever artifacts exist
            produced = _collect_outputs(MULTI_AGENTS_DIR, run_out_dir)
            return produced
        # On success, collect outputs
        produced = _collect_outputs(MULTI_AGENTS_DIR, run_out_dir)
        return produced
    finally:
        # restore or remove runtime task.json; preserve run_out_dir/logs for debugging
        _restore_backup(backup_path)
