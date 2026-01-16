import os
import shutil
import subprocess
import sys

def run_command(cmd, cwd=None):
    print(f"Executing: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Error: Command failed with exit code {result.returncode}")
        sys.exit(1)

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("=== EPANET-Turbo Release Packager ===")
    
    # 1. Cleanup old build artifacts
    dirs_to_clean = ['build', 'dist', 'epanet_turbo.egg-info', 'temp_verify']
    for d in dirs_to_clean:
        path = os.path.join(root_dir, d)
        if os.path.exists(path):
            print(f"Cleaning {d}...")
            shutil.rmtree(path)

    # 2. Ensure PyArmor runtime is correctly structured
    # The runtime must be at the root level for the encrypted files to find it
    nested_runtime = os.path.join(root_dir, 'epanet_turbo', 'pyarmor_runtime_000000')
    root_runtime = os.path.join(root_dir, 'pyarmor_runtime_000000')
    
    if os.path.exists(nested_runtime) and not os.path.exists(root_runtime):
        print("Moving nested PyArmor runtime to root...")
        shutil.move(nested_runtime, root_runtime)
    elif os.path.exists(nested_runtime) and os.path.exists(root_runtime):
        print("Merging nested PyArmor runtime into root...")
        shutil.rmtree(nested_runtime) # Root version takes precedence

    # 3. Create/Fix __init__.py for runtime (Force UTF-8)
    runtime_init = os.path.join(root_runtime, '__init__.py')
    print("Standardizing pyarmor_runtime_000000/__init__.py (UTF-8)...")
    content = "from .pyarmor_runtime import __pyarmor__\n"
    with open(runtime_init, "w", encoding="utf-8") as f:
        f.write(content)

    # 4. Run the build
    print("Building wheel artifact...")
    # Use global python if in a broken venv, otherwise use sys.executable
    python_exe = sys.executable
    run_command(f'"{python_exe}" -m build', cwd=root_dir)

    print("\n✅ Build Complete!")
    dist_dir = os.path.join(root_dir, 'dist')
    if os.path.exists(dist_dir):
        files = os.listdir(dist_dir)
        for f in files:
            if f.endswith('.whl'):
                print(f"📦 Final Package: {os.path.join('dist', f)}")

if __name__ == "__main__":
    main()
