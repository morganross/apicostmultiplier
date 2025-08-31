import sys

# Import the GUI launcher from functions.py (same directory)
try:
    from functions import launch_gui
except Exception as e:
    # Fallback: adjust sys.path to include this directory, then import
    import os
    sys.path.append(os.path.dirname(__file__))
    from functions import launch_gui  # type: ignore


if __name__ == "__main__":
    sys.exit(launch_gui())
