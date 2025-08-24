import os
import asyncio
import shutil # Added for rmtree
import config_parser
import file_manager
import gpt_researcher_client
import llm_doc_eval_client
import utils

async def main():
    # Step 2: Load configuration
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(current_dir, 'config.yaml')
    config = config_parser.load_config(config_file_path)

    if not config:
        print("Failed to load configuration. Exiting.")
        return

    input_folder = config.get('input_folder')
    output_folder = config.get('output_folder')
    instructions_file = config.get('instructions_file')
    one_file_only = config.get('one_file_only', False) # Default to False if not specified

    if not all([input_folder, output_folder, instructions_file]):
        print("Missing one or more required configuration parameters (input_folder, output_folder, instructions_file). Exiting.")
        return

    # Ensure paths are absolute for consistency
    input_folder = os.path.abspath(input_folder)
    output_folder = os.path.abspath(output_folder)
    instructions_file = os.path.abspath(instructions_file)
    instructions_file = os.path.abspath(instructions_file)

    print(f"Configuration loaded:")
    print(f"  Input Folder: {input_folder}")
    print(f"  Output Folder: {output_folder}")
    print(f"  Instructions File: {instructions_file}")

    # Read instructions content once
    try:
        with open(instructions_file, 'r') as f:
            instructions_content = f.read()
    except FileNotFoundError:
        print(f"Error: Instructions file not found at {instructions_file}. Exiting.")
        return
    except Exception as e:
        print(f"Error reading instructions file {instructions_file}: {e}. Exiting.")
        return

    # Step 3: File Discovery & Filtering
    markdown_files = file_manager.find_markdown_files(input_folder)
    print(f"\nFound {len(markdown_files)} markdown files in input folder.")

    # Apply one_file_only logic here
    if one_file_only and markdown_files:
        print("  'one_file_only' is true. Processing only the first found markdown file.")
        markdown_files = [markdown_files[0]] # Limit to only the first file

    for md_file_path in markdown_files:
        print(f"\nProcessing file: {md_file_path}")
        output_file_path = file_manager.get_output_path(md_file_path, input_folder, output_folder)

        if file_manager.output_exists(output_file_path):
            print(f"  Output file already exists for {md_file_path}. Skipping.")
            # If one_file_only is true and this file was skipped, the loop will naturally end
            # because markdown_files is already limited to one element.
            continue
        
        # The loop will naturally exit after processing the first file if one_file_only is true,
        # because markdown_files has been limited to a single element.

        try:
            with open(md_file_path, 'r') as f:
                markdown_content = f.read()
        except Exception as e:
            print(f"  Error reading input markdown file {md_file_path}: {e}. Skipping.")
            continue

        # Step 4: GPT-Researcher Integration
        query_prompt = gpt_researcher_client.generate_query_prompt(markdown_content, instructions_content)
        print(f"  Generated query prompt for {os.path.basename(md_file_path)}.")

        # Generate 3 candidate reports (standard research)
        print("  Running GPT-Researcher: 3 research_report runs...")
        try:
            research_reports = await gpt_researcher_client.run_concurrent_research(query_prompt, num_runs=3, report_type="research_report")
            print(f"  Generated {len(research_reports)} research_report(s).")
        except Exception as e:
            print(f"  Failed to generate research_report candidates for {md_file_path}: {e}")
            research_reports = []

        # Generate 3 deep research reports
        print("  Running GPT-Researcher: 3 deep research runs...")
        try:
            deep_reports = await gpt_researcher_client.run_concurrent_research(query_prompt, num_runs=3, report_type="deep")
            print(f"  Generated {len(deep_reports)} deep report(s).")
        except Exception as e:
            print(f"  Failed to generate deep research candidates for {md_file_path}: {e}")
            deep_reports = []

        # Generate 3 Multi-Agent reports using the MA runner (temp-copy)
        print("  Running Multi-Agent: 3 MA runs...")
        try:
            ma_reports = await ma_runner_wrapper.run_concurrent_ma(query_prompt, num_runs=3)
            print(f"  Generated {len(ma_reports)} MA report(s).")
        except Exception as e:
            print(f"  Failed to generate MA reports for {md_file_path}: {e}")
            ma_reports = []

        # Combine all generated candidates
        generated_report_paths = []
        for lst in (research_reports, deep_reports, ma_reports):
            if lst:
                generated_report_paths.extend(lst)

        if not generated_report_paths:
            print(f"  No reports generated for {md_file_path}. Skipping evaluation.")
            continue

        print(f"  Successfully generated {len(generated_report_paths)} total reports (research/deep/MA).")

        # Step 5: LLM-Doc-Eval Integration
        print("  Evaluating generated reports...")
        try:
            best_report_path = await llm_doc_eval_client.evaluate_reports(generated_report_paths)
            print(f"  Best report identified: {best_report_path}")
        except Exception as e:
            print(f"  Failed to evaluate reports for {md_file_path}: {e}. Skipping output.")
            continue

        # Step 6: Output Management
        print(f"  Creating output directories for {output_file_path}...")
        file_manager.create_output_dirs(output_file_path)
        
        print(f"  Copying best report to {output_file_path}...")
        try:
            file_manager.copy_file(best_report_path, output_file_path)
            print(f"  Successfully processed and saved {os.path.basename(md_file_path)} to {output_file_path}")
        except Exception as e:
            print(f"  Error copying best report {best_report_path} to {output_file_path}: {e}")
        finally:
            # Clean up the temporary directory after copying
            if best_report_path and os.path.exists(os.path.dirname(best_report_path)):
                temp_dir_to_clean = os.path.dirname(best_report_path)
                shutil.rmtree(temp_dir_to_clean)
                print(f"  Cleaned up temporary evaluation directory: {temp_dir_to_clean}")
        
        # The loop will naturally exit after processing the first file if one_file_only is true,
        # because markdown_files has been limited to a single element.

    print("\nProcess Markdown script finished.")

if __name__ == "__main__":
    asyncio.run(main())
