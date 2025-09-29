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


def process_repository(repo_config, target_dir):
    """
    Clones/initializes a repository, or pulls updates if it already exists.
    """
    git_url = repo_config.get("git_url")
    branch = repo_config.get("branch", "main")
    is_sparse = repo_config.get("sparse", False)
    cwd = os.getcwd()

    if not git_url:
        print(f"Skipping entry, missing 'git_url': {repo_config}")
        return

    # --- 1. If it's already a Git repo, just pull updates ---
    if os.path.exists(os.path.join(target_dir, ".git")):
        print(
            f"--- Directory exists as a Git repo. Attempting to pull updates in '{target_dir}' ---"
        )
        try:
            run_command(f"git pull origin {branch}", working_dir=target_dir)
        except subprocess.CalledProcessError:
            print(
                f"Warning: Could not pull updates for '{target_dir}'. There might be local changes.",
                file=sys.stderr,
            )

    # --- 2. If it's not a Git repo, perform the initial setup ---
    else:
        print(f"--- Setting up new repository in '{target_dir}' ---")

        # Conditional Cleanup: Only delete the directory if it's NOT the one we're currently in.
        if os.path.exists(target_dir) and not os.path.samefile(target_dir, cwd):
            print(f">> Deleting existing non-repo directory: {target_dir}")
            shutil.rmtree(target_dir)

        # Ensure the directory exists (this is safe to run even if it's the CWD)
        os.makedirs(target_dir, exist_ok=True)

        if is_sparse:
            # The sparse checkout flow (init, remote, pull) is safe for an existing, non-empty directory.
            print(f"--- Performing SPARSE CHECKOUT for {target_dir} ---")
            checkout_dirs = repo_config.get("directories_checkout", [])
            run_command(f"git init -b {branch}", working_dir=target_dir)
            run_command(f"git remote add origin {git_url}", working_dir=target_dir)
            run_command("git config core.sparseCheckout true", working_dir=target_dir)
            sparse_checkout_file = os.path.join(
                target_dir, ".git", "info", "sparse-checkout"
            )
            with open(sparse_checkout_file, "w") as f:
                for directory in checkout_dirs:
                    f.write(f"{directory}\n")
            run_command(f"git pull origin {branch}", working_dir=target_dir)
        else:
            # A full clone requires the target directory to be empty.
            print(f"--- Performing FULL CLONE for {target_dir} ---")
            if len(os.listdir(target_dir)) > 0:
                print(
                    f"Error: Cannot perform a full clone into '{os.path.basename(target_dir)}' because it is not empty.",
                    file=sys.stderr,
                )
                print(
                    "Please run the script from an empty folder or the parent directory.",
                    file=sys.stderr,
                )
                return  # Stop processing this repository

            run_command(
                f"git clone --branch {branch} {git_url} .", working_dir=target_dir
            )

    print(f"--- Successfully processed '{os.path.basename(target_dir)}' ---")


def main():
    """
    Main function to check context and dispatch repository processing.
    """
    config_file = "config.json"
    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found.", file=sys.stderr)
        sys.exit(1)

    with open(config_file, "r") as f:
        config_data = json.load(f)

    must_be_in = config_data.get("must_be_in", [])
    cwd = os.getcwd()
    current_dir_name = os.path.basename(cwd)

    # --- Dispatcher Logic ---

    # Scenario A: Check if we are inside a specific plugin directory
    target_repo_config = None
    for key, config in config_data.items():
        if isinstance(config, dict) and config.get("dir") == current_dir_name:
            target_repo_config = config
            break

    if target_repo_config:
        # We are inside a specific plugin dir, so sync in-place.
        print(f"== Mode: Sync-in-place for '{current_dir_name}' ==")
        process_repository(target_repo_config, cwd)  # Target is the current directory

    # Scenario B: Check if we are in the parent container directory
    elif must_be_in and current_dir_name == must_be_in[-1]:
        # We are in the main container, so sync all configured repos.
        print(f"== Mode: Batch Sync in '{current_dir_name}' ==")
        for key, config in config_data.items():
            if isinstance(config, dict) and "dir" in config:
                # Target is a new subdirectory for each plugin
                target_dir = os.path.join(cwd, config["dir"])
                process_repository(config, target_dir)
    else:
        # Invalid Location
        print(
            "Validation Error: Script not run from a recognized directory.",
            file=sys.stderr,
        )
        expected_parent = (
            f"'{must_be_in[-1]}'" if must_be_in else "a configured container"
        )
        print(
            f"Please run this script from within a specific plugin directory or from the main container directory ({expected_parent}).",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\nScript finished successfully at 6:05 PM on Sunday in Copenhagen.")


if __name__ == "__main__":
    main()
    