import os
import shutil

def find_markdown_files(input_dir):
    """
    Recursively finds all Markdown (.md) files within the specified input directory.
    Returns a list of absolute paths to the Markdown files.
    """
    markdown_files = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".md"):
                markdown_files.append(os.path.abspath(os.path.join(root, file)))
    return markdown_files

def get_output_path(input_file_path, input_base_dir, output_base_dir):
    """
    Constructs the corresponding output file path, maintaining the relative directory structure.
    """
    relative_path = os.path.relpath(input_file_path, input_base_dir)
    output_file_path = os.path.join(output_base_dir, relative_path)
    return output_file_path

def output_exists(output_file_path):
    """
    Checks if a file exists at the specified output file path.
    """
    return os.path.exists(output_file_path)

def create_output_dirs(output_file_path):
    """
    Creates necessary parent directories for the output file path if they don't exist.
    """
    output_dir = os.path.dirname(output_file_path)
    print(f"Attempting to create directories: {output_dir}")
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Successfully created directories: {output_dir}")
    except Exception as e:
        print(f"Error creating directories {output_dir}: {e}")
        raise # Re-raise the exception to propagate it

def copy_file(source_path, destination_path):
    """
    Copies a file from source_path to destination_path.
    """
    shutil.copy2(source_path, destination_path)

if __name__ == "__main__":
    # Example Usage:
    # Assuming a test structure like:
    # /tmp/input_docs/
    # ├── doc1.md
    # └── sub_dir/
    #     └── doc2.md

    # Create dummy files for testing
    os.makedirs("./test_input/sub_dir", exist_ok=True)
    with open("./test_input/doc1.md", "w") as f:
        f.write("This is doc1.")
    with open("./test_input/sub_dir/doc2.md", "w") as f:
        f.write("This is doc2.")

    input_base = "./test_input"
    output_base = "./test_output"

    print(f"Finding markdown files in {input_base}...")
    md_files = find_markdown_files(input_base)
    for md_file in md_files:
        print(f"Found: {md_file}")
        output_path = get_output_path(md_file, input_base, output_base)
        print(f"Corresponding output path: {output_path}")
        create_output_dirs(output_path)
        print(f"Created output directories for {output_path}")
        # Simulate copying a file
        # copy_file(md_file, output_path)
        # print(f"Copied {md_file} to {output_path}")

    # Clean up dummy files
    shutil.rmtree("./test_input")
    shutil.rmtree("./test_output")