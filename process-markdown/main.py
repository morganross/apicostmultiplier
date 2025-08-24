import asyncio
import os
import sys
import subprocess

# Define the path to the installed.txt file
INSTALLED_FLAG_FILE = "installed.txt"
REQUIREMENTS_FILE = "requirements.txt"

async def install_dependencies():
    """
    Installs dependencies from requirements.txt if installed.txt does not exist.
    Creates installed.txt upon successful installation.
    """
    if os.path.exists(INSTALLED_FLAG_FILE):
        print(f"'{INSTALLED_FLAG_FILE}' found. Skipping dependency installation.")
        return

    print(f"'{INSTALLED_FLAG_FILE}' not found. Installing dependencies from '{REQUIREMENTS_FILE}'...")
    try:
        # Use sys.executable to ensure pip from the current environment is used
        process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"Error installing dependencies:\n{stderr.decode()}")
            raise Exception(f"Dependency installation failed.")
        else:
            print(f"Dependencies installed successfully:\n{stdout.decode()}")
            with open(INSTALLED_FLAG_FILE, "w") as f:
                f.write("Dependencies installed on first run.\n")
            print(f"Created '{INSTALLED_FLAG_FILE}' to mark installation.")

    except FileNotFoundError:
        print(f"Error: '{sys.executable}' or 'pip' command not found. Ensure Python and pip are installed and in PATH.")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during dependency installation: {e}")
        raise

# Add the process-markdown directory to the Python path
# This allows importing modules from process-markdown as if they were packages
current_dir = os.path.dirname(os.path.abspath(__file__))
process_markdown_path = os.path.join(current_dir, 'process-markdown')
sys.path.insert(0, process_markdown_path)

# Now we can import process_markdown
import process_markdown # This imports the process_markdown.py module directly

async def main():
    print("Starting gptr-eval-process main script...")
    
    # Install dependencies on first run
    await install_dependencies()

    await process_markdown.main() # Call the main function within the imported module
    print("gptr-eval-process main script finished.")

if __name__ == "__main__":
    asyncio.run(main())