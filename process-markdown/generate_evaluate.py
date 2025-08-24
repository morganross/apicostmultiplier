import os
import asyncio
import shutil
import uuid
import sys # Import sys
from typing import Optional

# Add the parent directory of llm_doc_eval to sys.path
# This assumes test_eval_script.py is in the root (c:/dev/flagday)
# and llm_doc_eval is at gptr-eval-process/llm_doc_eval
script_dir = os.path.dirname(os.path.abspath(__file__))
gptr_eval_process_path = os.path.join(script_dir, 'gptr-eval-process')
if gptr_eval_process_path not in sys.path:
    sys.path.insert(0, gptr_eval_process_path)

try:
    from llm_doc_eval.api import run_pairwise_evaluation, get_best_report_by_elo, DOC_PATHS, DB_PATH
except ImportError as e:
    print(f"Error importing llm_doc_eval: {e}")
    print("Please ensure 'llm_doc_eval' is correctly installed or its path is in PYTHONPATH.")
    sys.exit(1) # Exit if import fails, as the script cannot proceed without it.


async def evaluate_reports_for_test(report_paths, output_dir: Optional[str] = None):
    """
    Adapted evaluation logic for the test script.
    """
    temp_eval_dir = os.path.join("temp_llm_eval_reports", str(uuid.uuid4()))
    os.makedirs(temp_eval_dir, exist_ok=True)
    
    DOC_PATHS.clear() # Clear global DOC_PATHS before each run

    try:
        documents_for_evaluator = []
        for report_path in report_paths:
            dest_path = os.path.join(temp_eval_dir, os.path.basename(report_path))
            shutil.copy(report_path, dest_path)
            
            with open(dest_path, 'r', encoding='utf-8') as f:
                content = f.read()
            doc_id = os.path.basename(dest_path)
            documents_for_evaluator.append((doc_id, content, dest_path))

        await run_pairwise_evaluation(folder_path=temp_eval_dir, db_path=DB_PATH)
        best_report_path = get_best_report_by_elo(db_path=DB_PATH, doc_paths=DOC_PATHS)
        
        if best_report_path:
            print(f"Identified best report: {best_report_path}")
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                final_report_path = os.path.join(output_dir, os.path.basename(best_report_path))
                shutil.copy(best_report_path, final_report_path)
                print(f"Copied best report to final location: {final_report_path}")
            return best_report_path
        else:
            raise Exception("Could not identify best report from evaluation results.")

    except Exception as e:
        print(f"An error occurred during evaluation: {e}")
        raise
    finally:
        if os.path.exists(temp_eval_dir):
            shutil.rmtree(temp_eval_dir)
            print(f"Cleaned up temporary evaluation directory: {temp_eval_dir}")


async def main():
    print("Running test evaluation script...")

    # Define dummy report paths
    dummy_report_paths = [
        "gptr-eval-process/test/finaldocs/report1.md",
        "gptr-eval-process/test/finaldocs/report2.md",
        "gptr-eval-process/test/finaldocs/report3.md",
    ]

    # Create dummy files if they don't exist for testing purposes
    for path in dummy_report_paths:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w") as f:
                f.write(f"# Dummy Report for {os.path.basename(path)}\n\nThis is a dummy report content.")
    
    print(f"Using dummy reports for evaluation: {dummy_report_paths}")

    output_directory = "gptr-eval-process/final_reports"
    try:
        best_report = await evaluate_reports_for_test(dummy_report_paths, output_dir=output_directory)
        print(f"Test evaluation completed. The best report is: {best_report}")
    except Exception as e:
        print(f"Test evaluation failed: {e}")
    finally:
        # Clean up dummy files after testing
        for path in dummy_report_paths:
            if os.path.exists(path):
                os.remove(path)
        # Remove dummy directories if empty
        for path in dummy_report_paths:
            try:
                os.removedirs(os.path.dirname(path))
            except OSError:
                pass # Directory might not be empty or already removed


if __name__ == "__main__":
    asyncio.run(main())