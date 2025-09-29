import os
import shutil
import subprocess
import sys
import json


def run_command(command, working_dir="."):
    """Runs a command in a specified directory and checks for errors."""
    print(f"\n>> RUNNING: '{command}' in '{working_dir}'")
    try:
        subprocess.run(command, shell=True, check=True, text=True, cwd=working_dir)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(
            f"Command not found. Make sure Git is installed and in your PATH.",
            file=sys.stderr,
        )
        sys.exit(1)


def process_repository(repo_config, parent_dir):
    """
    Clones/sparse-checks-out a repository if it doesn't exist,
    or pulls updates if it already exists.
    """
    repo_dir = repo_config.get("dir")
    git_url = repo_config.get("git_url")
    branch = repo_config.get("branch", "main")
    is_sparse = repo_config.get("sparse", False)

    if not repo_dir or not git_url:
        print(f"Skipping entry, missing 'dir' or 'git_url': {repo_config}")
        return

    full_repo_path = os.path.join(parent_dir, repo_dir)

    # --- 1. Check if repository exists and pull updates ---
    if os.path.exists(full_repo_path) and os.path.exists(
        os.path.join(full_repo_path, ".git")
    ):
        # If the directory exists and is a Git repo, just pull the latest changes.
        print(f"\n--- Directory '{repo_dir}' exists. Attempting to pull updates. ---")
        try:
            # First, a quick check to see if there are local changes
            run_command("git diff --quiet", working_dir=full_repo_path)
            run_command(f"git pull origin {branch}", working_dir=full_repo_path)
        except subprocess.CalledProcessError:
            print(
                f"Warning: Could not pull updates for '{repo_dir}'. There might be local changes.",
                file=sys.stderr,
            )
            print("Please commit or stash your changes and try again.", file=sys.stderr)

    else:
        # --- 2. If not, perform the initial clone or sparse checkout ---
        print(
            f"\n--- Directory '{repo_dir}' not found or is not a Git repo. Starting fresh setup. ---"
        )

        # Clean up any existing non-repo directory
        if os.path.exists(full_repo_path):
            shutil.rmtree(full_repo_path)

        os.makedirs(full_repo_path, exist_ok=True)

        if is_sparse:
            print(f"--- Performing SPARSE CHECKOUT for {repo_dir} ---")
            checkout_dirs = repo_config.get("directories_checkout", [])
            if not checkout_dirs:
                print(
                    f"Warning: Sparse checkout is true but no directories are specified for {repo_dir}."
                )
                return

            run_command(f"git init -b {branch}", working_dir=full_repo_path)
            run_command(f"git remote add origin {git_url}", working_dir=full_repo_path)
            run_command(
                "git config core.sparseCheckout true", working_dir=full_repo_path
            )

            sparse_checkout_file = os.path.join(
                full_repo_path, ".git", "info", "sparse-checkout"
            )
            with open(sparse_checkout_file, "w") as f:
                for directory in checkout_dirs:
                    f.write(f"{directory}\n")

            print(f"Configured sparse-checkout for: {checkout_dirs}")
            run_command(f"git pull origin {branch}", working_dir=full_repo_path)

        else:
            print(f"--- Performing FULL CLONE for {repo_dir} ---")
            run_command(
                f"git clone --branch {branch} {git_url} .", working_dir=full_repo_path
            )

    print(f"--- Successfully processed {repo_dir} ---")


def main():
    """
    Main function to validate location, load config, and process repositories.
    """
    config_file = "plugin_phai.json"

    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    # --- 1. Validate the current location ---
    must_be_in = config_data.get("must_be_in", [])
    current_path = os.path.normpath(os.getcwd())
    path_parts = current_path.split(os.path.sep)

    # Find the index of the last required directory in the current path
    last_found_index = -1
    for i, part in enumerate(path_parts):
        if part in must_be_in:
            last_found_index = i
            
    # Check if all required directories were found in order
    path_validator = [part for part in path_parts if part in must_be_in]
    if path_validator != must_be_in:
        print("Validation Error: Script is not running from the expected directory structure.")
        print(f"Expected to be inside a path containing: {' -> '.join(must_be_in)}")
        print(f"Current path: {current_path}")
        sys.exit(1)
        
    # --- 2. Adapt the plugins directory path ---
    # Reconstruct the base path up to the last required directory found
    base_path = os.path.sep.join(path_parts[:last_found_index + 1])
    plugins_dir = os.path.join(base_path, "plugins")
    
    print(f"Validation successful. Setting plugins directory to: {plugins_dir}")
    os.makedirs(plugins_dir, exist_ok=True)
    
    # --- 3. Process each repository defined in the config ---
    for key, repo_config in config_data.items():
        if isinstance(repo_config, dict):
            process_repository(repo_config, plugins_dir)

    print("\n\nScript finished successfully.")


if __name__ == "__main__":
    main()
