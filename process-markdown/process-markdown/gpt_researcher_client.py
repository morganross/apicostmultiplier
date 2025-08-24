import asyncio
import functools
import os
import uuid
import shutil
from dotenv import load_dotenv # Import load_dotenv
from gpt_researcher import GPTResearcher # Import the GPTResearcher class

def generate_query_prompt(markdown_content, instructions_content):
    """
    Concatenates the markdown content and instructions content to form a query prompt.
    """
    return f"{instructions_content}\n\n{markdown_content}"

async def run_gpt_researcher_programmatic(query_prompt, report_type="research_report"):
    """
    Uses the gpt-researcher library programmatically to generate a report of the given type.
    Returns a tuple: (path_to_report, model_name_used).
    """
    # Load environment variables from .env file
    # Assuming .env is in the gpt-researcher-3.2.9 directory
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gpt-researcher-3.2.9', '.env')
    load_dotenv(dotenv_path) # Load environment variables from the specified .env file
    
    try:
        # Initialize the researcher with the query and requested report type.
        researcher = GPTResearcher(query=query_prompt, report_type=report_type)
        
        # Conduct research
        await researcher.conduct_research()
        
        # Write the report
        report_content = await researcher.write_report()

        # Check if report_content is None or empty
        if not report_content:
            raise ValueError("GPTResearcher.write_report() returned no content.")

        # Determine model name used (best-effort)
        model_name = None
        try:
            # Prefer config value if present
            cfg = getattr(researcher, "cfg", None)
            if cfg is not None:
                model_name = getattr(cfg, "smart_llm", None) or getattr(cfg, "SMART_LLM", None)
        except Exception:
            model_name = None

        # Try researcher.llm attributes
        if not model_name:
            try:
                llm = getattr(researcher, "llm", None)
                if llm is not None:
                    model_name = getattr(llm, "model", None) or getattr(llm, "name", None) or str(llm)
            except Exception:
                model_name = None

        # Fallback to env or unknown
        if not model_name:
            model_name = os.environ.get("SMART_LLM") or os.environ.get("FAST_LLM") or "unknown-model"

        # Create a temporary directory for reports if it doesn't exist
        temp_reports_dir = "temp_gpt_researcher_reports"
        os.makedirs(temp_reports_dir, exist_ok=True)

        # Generate a unique filename for the report
        report_filename = os.path.join(temp_reports_dir, f"research_report_{uuid.uuid4()}.md")

        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"Report saved to: {report_filename} (model: {model_name})")
        return os.path.abspath(report_filename), model_name

    except Exception as e:
        print(f"Error running gpt-researcher programmatically: {e}")
        raise Exception(f"gpt-researcher programmatic run failed: {e}")

async def run_concurrent_research(query_prompt, num_runs=3, report_type: str = "research_report"):
    """
    Runs run_gpt_researcher_programmatic multiple times concurrently using the specified report_type.
    Returns a list of paths to the generated reports.
    """
    loop = asyncio.get_running_loop()
    tasks = [
        loop.run_in_executor(
            None,
            functools.partial(asyncio.run, run_gpt_researcher_programmatic(query_prompt, report_type=report_type))
        )
        for _ in range(num_runs)
    ]

    # Wait for all tasks to complete and gather their results
    report_paths = await asyncio.gather(*tasks, return_exceptions=True)

    successful_paths = []
    for result in report_paths:
        if isinstance(result, Exception):
            print(f"One gpt-researcher run failed: {result}")
        else:
            successful_paths.append(result)

    if not successful_paths:
        raise Exception("All gpt-researcher runs failed.")

    return successful_paths

if __name__ == "__main__":
    # This part is for testing the client in isolation.
    
    # Dummy content for testing
    dummy_markdown = "This is a test markdown document about AI."
    dummy_instructions = "Write a brief research report on the given topic."

    test_query_prompt = generate_query_prompt(dummy_markdown, dummy_instructions)
    print(f"Generated Query Prompt:\n{test_query_prompt}\n")

    print("Running concurrent gpt-researcher calls (this might take a while)...")
    try:
        # Note: This will actually try to run gpt-researcher.
        # Ensure gpt-researcher is installed and configured with API keys.
        generated_report_paths = asyncio.run(run_concurrent_research(test_query_prompt, num_runs=1))
        print("\nGenerated Report Paths:")
        for path in generated_report_paths:
            print(path)
    except Exception as e:
        print(f"Failed to run concurrent research: {e}")
    finally:
        # Clean up temporary reports
        temp_reports_dir = "temp_gpt_researcher_reports"
        if os.path.exists(temp_reports_dir):
            shutil.rmtree(temp_reports_dir)
            print(f"Cleaned up temporary reports in {temp_reports_dir}")
