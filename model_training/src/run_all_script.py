import os
import subprocess
import sys
import argparse
from dotenv import load_dotenv
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

def parse_arguments():
    parser = argparse.ArgumentParser(description="Run all scripts with specified environment")
    parser.add_argument('--env', type=str, required=True, help="Environment to use (level1, level2, level3)")
    return parser.parse_args()

def load_env(env_file):
    load_dotenv(env_file)

def run_script(script_name):
    relative_path = os.path.relpath(script_name, BASE_DIR)
    module_name = os.path.splitext(relative_path)[0].replace(os.sep, ".")
    try:
        subprocess.run(
            [sys.executable, "-m", module_name],
            cwd=BASE_DIR,
            check=True,
        )
        print(f"Successfully ran {script_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        sys.exit(1)

scripts = [
    # os.path.join(SRC_DIR, "environment.py"),
    # os.path.join(SRC_DIR, "datastore.py"),
    # os.path.join(SRC_DIR, "register_components.py"),
    os.path.join(SRC_DIR, "pipeline.py"),

]


if __name__ == "__main__":
    args = parse_arguments()
    env_file = os.path.join(BASE_DIR, "environment_variables", f"{args.env}.env")
    load_env(env_file)
    
    for i, script in enumerate(scripts):
        run_script(script)
        
        # Introduce delay after setup_environment.py
        if script == os.path.join(SRC_DIR, "environment.py"):
            print("Waiting for environment to be fully registered...")
            time.sleep(5)
