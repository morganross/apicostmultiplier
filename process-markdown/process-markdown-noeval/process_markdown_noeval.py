import os
import asyncio
import time
from pathlib import Path
import importlib.util
import uuid

# Simple no-eval runner that runs 3 MA runs sequentially per input file.
# It uses process-markdown-ma/ma_runner.py's run_ma_for_query function which
# delegates to the process-markdown/ma_runner_wrapper that atomically writes
# the repo multi_agents/task.json and invokes the MA subprocess.

def repo_root():
    # Return the gptr-eval-process directory as repo root
    return str(Path(__file__).resolve().parents[1])

def find_md_inputs(input_dir):
    return [str(p) for p in Path(input_dir).rglob("*.md")]

async def run_three_mas_for_file(md_path: str, instructions_path: str):
    # Load prompt pieces
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()
    with open(instructions_path, "r", encoding="utf-8") as f:
        instructions = f.read()

    # Build simple query prompt (instructions + markdown)
    query_prompt = f"{instructions}\n\n{md}"

    # Import ma_runner
    repo = repo_root()
    wrapper_spec = importlib.util.spec_from_file_location("ma_runner", os.path.join(repo, "process-markdown-ma", "ma_runner.py"))
    ma_runner = importlib.util.module_from_spec(wrapper_spec)
    wrapper_spec.loader.exec_module(ma_runner)

    produced = []
    for i in range(1, 4):
        try:
            print(f"Running MA {i} for file {os.path.basename(md_path)}...")
            # minimal overrides: small report, markdown only to avoid PDF conversion issues
            overrides = {"max_sections": 1, "publish_formats": {"markdown": True, "pdf": False, "docx": False}}
            result = await ma_runner.run_ma_for_query(query_prompt, overrides)
            produced.append(result)
            print(f"  MA {i} produced: {result}")
        except Exception as e:
            print(f"  MA {i} failed: {e}")
            # continue to next MA run (we want 3 attempts regardless)
    return produced

async def main():
    root = repo_root()
    # Use the repository test inputs folder (this contains the commerce example)
    input_dir = os.path.join(root, "test", "mdinputs")
    instructions_file = os.path.join(root, "test", "instructions.txt")

    if not os.path.isdir(input_dir):
        print("Input folder not found:", input_dir)
        return
    if not os.path.exists(instructions_file):
        print("Instructions file not found:", instructions_file)
        return

    md_files = find_md_inputs(input_dir)
    if not md_files:
        print("No markdown files found under", input_dir)
        return

    print(f"Found {len(md_files)} markdown files in {input_dir}. Running 3 MA runs per file (no evaluation).")

    for md_path in md_files:
        print("Processing:", md_path)
        produced = await run_three_mas_for_file(md_path, instructions_file)
        print(f"Produced {len(produced)} MA reports for {os.path.basename(md_path)}:")
        for p in produced:
            print("  -", p)

        # Build query prompt again for DR/DD runs
        with open(md_path, "r", encoding="utf-8") as f:
            md = f.read()
        with open(instructions_file, "r", encoding="utf-8") as f:
            instructions = f.read()
        query_prompt = f"{instructions}\n\n{md}"

        # Dynamically load the gpt_researcher client to run DR and DD
        repo = repo_root()
        gr_spec = importlib.util.spec_from_file_location("gpt_researcher_client", os.path.join(repo, "process-markdown", "gpt_researcher_client.py"))
        gr_client = importlib.util.module_from_spec(gr_spec)
        gr_spec.loader.exec_module(gr_client)

        # Run 3 Deep Research (DR) runs
        print("Running 3 Deep Research (DR) runs...")
        try:
            dr_results = await gr_client.run_concurrent_research(query_prompt, num_runs=3, report_type="deep")
            print(f"Produced {len(dr_results)} DR results:")
            # dr_results are expected to be tuples (path, model) from the client
            dr_renamed = []
            for path_model in dr_results:
                try:
                    path, model = path_model
                except Exception:
                    # Fallback if client returned just path
                    path = path_model
                    model = "unknown-model"
                print("  -", path, "(", model, ")")
                # Append model and report type to filename
                base, ext = os.path.splitext(path)
                safe_model = model.replace(":", "_").replace("/", "_")
                new_path = f"{base}__{safe_model}__DR{ext}"
                try:
                    os.replace(path, new_path)
                    dr_renamed.append(new_path)
                except Exception:
                    # fallback to copy
                    try:
                        import shutil
                        shutil.copy2(path, new_path)
                        dr_renamed.append(new_path)
                    except Exception:
                        dr_renamed.append(path)
            # replace dr_results with renamed paths for downstream reasoning if needed
            dr_results = dr_renamed
        except Exception as e:
            print("Deep Research runs failed:", e)
            dr_results = []

        # Run 3 Detailed Report (DD) runs
        print("Running 3 Detailed Report (DD) runs...")
        try:
            dd_results = await gr_client.run_concurrent_research(query_prompt, num_runs=3, report_type="detailed_report")
            print(f"Produced {len(dd_results)} DD results:")
            dd_renamed = []
            for path_model in dd_results:
                try:
                    path, model = path_model
                except Exception:
                    path = path_model
                    model = "unknown-model"
                print("  -", path, "(", model, ")")
                base, ext = os.path.splitext(path)
                safe_model = model.replace(":", "_").replace("/", "_")
                new_path = f"{base}__{safe_model}__DD{ext}"
                try:
                    os.replace(path, new_path)
                    dd_renamed.append(new_path)
                except Exception:
                    try:
                        import shutil
                        shutil.copy2(path, new_path)
                        dd_renamed.append(new_path)
                    except Exception:
                        dd_renamed.append(path)
            dd_results = dd_renamed
        except Exception as e:
            print("Detailed Report runs failed:", e)
            dd_results = []

    print("Done. Reports are in temp_gpt_researcher_reports/")

if __name__ == "__main__":
    asyncio.run(main())
