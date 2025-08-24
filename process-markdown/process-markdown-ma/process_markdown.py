import os
import asyncio
import shutil
import config_parser
import file_manager
import utils
from ma_runner import run_ma_for_query

async def main():
    # Load configuration (reuse original process-markdown config)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(current_dir, '..', 'process-markdown', 'config.yaml')
    config = config_parser.load_config(config_file_path)

    if not config:
        print("Failed to load configuration. Exiting.")
        return

    input_folder = config.get('input_folder')
    output_folder = config.get('output_folder')
    instructions_file = config.get('instructions_file')
    one_file_only = config.get('one_file_only', False)

    if not all([input_folder, output_folder, instructions_file]):
        print("Missing one or more required configuration parameters (input_folder, output_folder, instructions_file). Exiting.")
        return

    input_folder = os.path.abspath(input_folder)
    output_folder = os.path.abspath(output_folder)
    instructions_file = os.path.abspath(instructions_file)

    print(f"Configuration loaded:")
    print(f"  Input Folder: {input_folder}")
    print(f"  Output Folder: {output_folder}")
    print(f"  Instructions File: {instructions_file}")

    try:
        with open(instructions_file, 'r', encoding='utf-8') as f:
            instructions_content = f.read()
    except FileNotFoundError:
        print(f"Error: Instructions file not found at {instructions_file}. Exiting.")
        return
    except Exception as e:
        print(f"Error reading instructions file {instructions_file}: {e}. Exiting.")
        return

    markdown_files = file_manager.find_markdown_files(input_folder)
    print(f"\nFound {len(markdown_files)} markdown files in input folder.")

    if one_file_only and markdown_files:
        print("  'one_file_only' is true. Processing only the first found markdown file.")
        markdown_files = [markdown_files[0]]

    for md_file_path in markdown_files:
        print(f"\nProcessing file: {md_file_path}")
        output_file_path = file_manager.get_output_path(md_file_path, input_folder, output_folder)

        if file_manager.output_exists(output_file_path):
            print(f"  Output file already exists for {md_file_path}. Skipping.")
            continue

        try:
            with open(md_file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
        except Exception as e:
            print(f"  Error reading input markdown file {md_file_path}: {e}. Skipping.")
            continue

        # Build query prompt (instructions + markdown)
        query_prompt = f"{instructions_content}\n\n{markdown_content}"
        print(f"  Generated query prompt for {os.path.basename(md_file_path)}.")

        # Run the Multi-Agent flow (single run) via ma_runner
        print("  Running Multi-Agent (MA) to generate one report...")
        try:
            # You can pass overrides here, e.g., {"model":"openai/o3-mini", "max_sections":2}
            generated_report_path = await run_ma_for_query(query_prompt, task_overrides=None)
            if not generated_report_path or not os.path.exists(generated_report_path):
                print(f"  MA did not produce a report for {md_file_path}. Skipping evaluation.")
                continue
            print(f"  Successfully generated MA report: {generated_report_path}")
        except Exception as e:
            print(f"  Failed to run MA for {md_file_path}: {e}. Skipping.")
            continue

        # Optional: evaluate MA report using llm-doc-eval (not modified here)
        # For now, copy the MA-produced report to the output location
        print(f"  Creating output directories for {output_file_path}...")
        file_manager.create_output_dirs(output_file_path)

        print(f"  Copying MA report to {output_file_path}...")
        try:
            file_manager.copy_file(generated_report_path, output_file_path)
            print(f"  Successfully processed and saved {os.path.basename(md_file_path)} to {output_file_path}")
        except Exception as e:
            print(f"  Error copying MA report {generated_report_path} to {output_file_path}: {e}")
        finally:
            # Clean up the temporary MA report file if exists
            try:
                if generated_report_path and os.path.exists(generated_report_path):
                    os.remove(generated_report_path)
            except Exception:
                pass

        if one_file_only:
            break

    print("\nProcess Markdown MA script finished.")

if __name__ == "__main__":
    asyncio.run(main())
