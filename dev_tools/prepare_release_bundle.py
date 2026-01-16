import os
import shutil
import glob
import sys

# Configuration
VERSION = "2.0.0"
OUTPUT_ROOT = "Releases"
RELEASE_DIR = os.path.join(OUTPUT_ROOT, f"EPANET-Turbo_v{VERSION}_Release")
DIST_DIR = "dist"
EXAMPLES_DIR = "examples"
SETUP_SCRIPT = "setup_and_demo.py"

def create_bundle():
    print(f"📦 Creating Release Bundle in: {RELEASE_DIR}")
    
    # Ensure root release dir exists
    if not os.path.exists(OUTPUT_ROOT):
        os.makedirs(OUTPUT_ROOT)

    # 1. Create clean directory
    if os.path.exists(RELEASE_DIR):
        shutil.rmtree(RELEASE_DIR)
    os.makedirs(RELEASE_DIR)
    
    # 2. Copy Setup Script
    if os.path.exists(SETUP_SCRIPT):
        shutil.copy(SETUP_SCRIPT, RELEASE_DIR)
        print(f"   + Added {SETUP_SCRIPT}")
    else:
        print(f"   ❌ Missing {SETUP_SCRIPT}")
        
    # 3. Copy Wheel
    whl_files = glob.glob(os.path.join(DIST_DIR, "*.whl"))
    if whl_files:
        whl_path = whl_files[0] # Take the first one found
        target_whl = os.path.join(RELEASE_DIR, os.path.basename(whl_path))
        shutil.copy(whl_path, target_whl)
        print(f"   + Added {os.path.basename(whl_path)}")
    else:
        print(f"   ❌ Missing .whl in {DIST_DIR}")
        
    # 4. Copy Examples (Including Net1.inp)
    if os.path.exists(EXAMPLES_DIR):
        target_examples = os.path.join(RELEASE_DIR, "examples")
        shutil.copytree(EXAMPLES_DIR, target_examples)
        print(f"   + Added examples/ (including INP files)")
    else:
        print(f"   ❌ Missing {EXAMPLES_DIR}")

    # 5. Create README_RELEASE.txt
    readme_content = f"""
==================================================
   EPANET-Turbo v{VERSION} Release Package
==================================================

How to Install / 如何安装:
--------------------------
1. Double click or run `setup_and_demo.py` with Python.
   确保已安装 Python，直接运行 `setup_and_demo.py`。
   
   Command / 命令:
   python setup_and_demo.py

2. The script will automatically:
   - Create a virtual environment (epanet_env)
   - Install the high-performance engine
   - Fix dependencies (Polars compatibility)
   - Run a quick demo

How to Run Examples / 如何运行示例:
-----------------------------------
After installation, you can run the quickstart manually:

1. Open PowerShell/CMD in this folder.
2. Run:
   .\\epanet_env\\Scripts\\python.exe examples/quickstart.py

Support / 支持:
---------------
See GitHub repository or documentation.
"""
    with open(os.path.join(RELEASE_DIR, "README_RELEASE.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"   + Added README_RELEASE.txt")
    
    # 6. Create ZIP Archive
    print("\n🤐 Compressing to ZIP...")
    zip_filename = f"{RELEASE_DIR}"  # shutil adds .zip automatically
    shutil.make_archive(zip_filename, 'zip', RELEASE_DIR)
    print(f"   + Created {zip_filename}.zip")

    print("\n✅ Release Bundle Ready!")
    print(f"   Folder: {os.path.abspath(RELEASE_DIR)}")
    print(f"   Zip:    {os.path.abspath(zip_filename + '.zip')}")

if __name__ == "__main__":
    create_bundle()
