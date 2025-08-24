import os
import shutil # Import shutil for rmtree
import uuid # Import uuid for unique directory names
import asyncio # Import asyncio
import pandas as pd # Assuming pandas is used for data manipulation
from sqlalchemy import create_engine # Assuming sqlalchemy is used for DB access

from llm_doc_eval.api import run_pairwise_evaluation, get_best_report_by_elo, DOC_PATHS, DB_PATH

async def evaluate_reports(report_paths):
    """
    Evaluates reports using direct function calls to llm-doc-eval and identifies the best report.
    It creates a temporary directory, copies the reports into it, and passes the directory path
    to llm-doc-eval's run-pairwise command.
    """
    temp_eval_dir = os.path.join("temp_llm_eval_reports", str(uuid.uuid4()))
    os.makedirs(temp_eval_dir, exist_ok=True)
    
    # Clear DOC_PATHS before each run to ensure it only contains documents for the current evaluation
    DOC_PATHS.clear()

    try:
        # Copy reports to the temporary directory and prepare for evaluator
        documents_for_evaluator = []
        for report_path in report_paths:
            dest_path = os.path.join(temp_eval_dir, os.path.basename(report_path))
            shutil.copy(report_path, dest_path)
            
            with open(dest_path, 'r', encoding='utf-8') as f:
                content = f.read()
            doc_id = os.path.basename(dest_path) # Use filename as doc_id
            documents_for_evaluator.append((doc_id, content, dest_path)) # Pass dest_path as well
            # DOC_PATHS is now populated within run_pairwise_evaluation, so no need to populate it here.
            # However, we need to ensure the doc_paths_map for get_best_report_by_elo is correctly built.
            # The DOC_PATHS global in api.py will be populated by run_pairwise_evaluation.

        # Determine the path to results.db relative to llm_doc_eval_client.py
        # DB_PATH is now imported from llm_doc_eval.api
        
        # Ensure the database directory exists (this is handled by _create_tables in api.py)
        # os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) # No longer needed here

        # Run pairwise evaluation using the API function
        # The API function handles table creation, clearing, and persistence
        await run_pairwise_evaluation(folder_path=temp_eval_dir, db_path=DB_PATH)

        # Retrieve best report using the new utility function
        # DOC_PATHS from api.py will contain the mapping from the evaluation run
        best_report_path = get_best_report_by_elo(db_path=DB_PATH, doc_paths=DOC_PATHS)
        
        if best_report_path:
            print(f"Identified best report: {best_report_path}")
            return best_report_path
        else:
            raise Exception("Could not identify best report from evaluation results.")

    except Exception as e:
        print(f"An error occurred during evaluation: {e}")
        raise
    except Exception as e:
        print(f"An error occurred during evaluation: {e}")
        raise
    # Removed the finally block that cleans up temp_eval_dir.
    # Cleanup will now be handled by the calling script (process_markdown.py)
    # after the best report has been successfully copied.

if __name__ == "__main__":
    # This part is for testing the client in isolation.
    
    # Dummy report paths for testing
    # These paths should exist for a successful test run of llm-doc-eval
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

    print(f"Evaluating reports: {dummy_report_paths}")
    try:
        # Run the async function
        best_report = asyncio.run(evaluate_reports(dummy_report_paths))
        print(f"The best report is: {best_report}")
    except Exception as e:
        print(f"Failed to evaluate reports: {e}")
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