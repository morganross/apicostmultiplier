import yaml
import os

def load_config(config_path):
    """
    Loads and parses the configuration from the specified YAML file.
    """
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing YAML config file: {e}")
        return None

if __name__ == "__main__":
    # Example usage:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(current_dir, 'config.yaml')
    
    config = load_config(config_file_path)
    if config:
        print("Configuration loaded successfully:")
        print(f"Input Folder: {config.get('input_folder')}")
        print(f"Output Folder: {config.get('output_folder')}")
        print(f"Instructions File: {config.get('instructions_file')}")