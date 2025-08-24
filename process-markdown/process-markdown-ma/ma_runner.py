import os
import sys
import json
import uuid
import tempfile
import asyncio
import importlib.util
from pathlib import Path

def _repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

async def run_ma_for_query(query: str, task_overrides: dict | None = None):
    """
    New implementation: do NOT copy the multi_agents code tree.
    Instead, build the runtime task dict (merged), then call the process-markdown
    wrapper that atomically writes task.json into the repo multi_agents folder
    and invokes the multi_agents runner as a subprocess.

    Returns: path(s) to produced report files (list) — for compatibility, returns
    the first produced path if any, else raises on failure.
    """
    repo = _repo_root()
    from dotenv import load_dotenv

    # Load root .env and gpt-researcher .env if present so API keys are available to the run
    root_env = os.path.join(repo, '.env')
    gr_env = os.path.join(repo, 'gpt-researcher-3.2.9', '.env')
    if os.path.exists(root_env):
        load_dotenv(root_env)
    if os.path.exists(gr_env):
        load_dotenv(gr_env)

    # Locate template task.json (either custom template in repo/ma_task_templates or default in multi_agents)
    src_multi_agents = os.path.join(repo, "gpt-researcher-3.2.9", "multi_agents")
    template_dir = os.path.join(repo, "ma_task_templates")
    template_path = os.path.join(template_dir, "default_task.json")
    if not os.path.exists(template_path):
        template_path = os.path.join(src_multi_agents, "task.json")

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Task template not found at {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        task = json.load(f)

    # Merge overrides, set query explicitly
    merged = {**task, **(task_overrides or {})}
    merged["query"] = query

    # Prepare run output folder for this run
    out_dir = os.path.abspath(os.path.join(repo, "..", "temp_gpt_researcher_reports", f"run_{uuid.uuid4().hex}"))
    os.makedirs(out_dir, exist_ok=True)

    # Import the process-markdown wrapper (without modifying gpt-researcher source)
    wrapper_path = os.path.join(repo, "process-markdown", "ma_runner_wrapper.py")
    if not os.path.exists(wrapper_path):
        raise FileNotFoundError(f"ma_runner_wrapper not found at expected path: {wrapper_path}")

    spec = importlib.util.spec_from_file_location("ma_runner_wrapper", wrapper_path)
    ma_wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ma_wrapper)

    # run_ma_with_runtime_task is synchronous (it writes atomically and invokes a subprocess).
    loop = asyncio.get_running_loop()
    produced = await loop.run_in_executor(None, ma_wrapper.run_ma_with_runtime_task, merged, out_dir)

    # produced is a list of file paths copied into the run out dir
    if produced:
        # Return first produced report path for compatibility with prior behavior
        return os.path.abspath(produced[0])
    else:
        # No produced artifacts; raise with diagnostic note
        raise RuntimeError(f"MA run completed but produced no outputs. See {out_dir} for logs.")
