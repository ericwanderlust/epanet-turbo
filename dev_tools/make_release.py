import os
import shutil
import subprocess
import sys
import codecs

# Configuration
import time
VERSION = "2.0.0"
SRC_DIR = "src"
# Use a timestamp to avoid "File in use" errors on Windows
BUILD_SRC_DIR = f"build_src_{int(time.time())}"
OUTPUT_DIR = "epanet_turbo"
RESOURCES_DIR = "resources"
EXAMPLES_DIR = "examples"

def clean():
    print("🧹 Cleaning artifacts...")
    # Try to clean legacy build_src if possible, but don't fail
    for path in ["build_src", BUILD_SRC_DIR, OUTPUT_DIR, "dist", "build"]:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(f"⚠️  Warning: Could not clean {path}: {e}")
                
    if os.path.exists("epanet_turbo.egg-info"):
        try:
            shutil.rmtree("epanet_turbo.egg-info")
        except:
            pass

def prepare_source():
    print("📋 Preparing source code structure...")
    # Create build_temp/epanet_turbo to ensure PyArmor treats it as a package
    pkg_dir = os.path.join(BUILD_SRC_DIR, OUTPUT_DIR)
    if os.path.exists(BUILD_SRC_DIR):
        shutil.rmtree(BUILD_SRC_DIR)
    os.makedirs(pkg_dir)
    
    # Copy src contents into temp/epanet_turbo
    for item in os.listdir(SRC_DIR):
        s = os.path.join(SRC_DIR, item)
        d = os.path.join(pkg_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy(s, d)
    
    # 1. Strip BOM
    BOM = codecs.BOM_UTF8
    for root, _, files in os.walk(BUILD_SRC_DIR):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path, 'rb') as fp:
                    content = fp.read()
                if content.startswith(BOM):
                    with open(path, 'wb') as fp:
                        fp.write(content.lstrip(BOM))
                        
    # 2. Inject Version
    init_path = os.path.join(pkg_dir, "__init__.py")
    with open(init_path, "a", encoding="utf-8") as f:
        f.write(f"\n__version__ = '{VERSION}'\n")

    # 3. Clean any existing PyArmor artifacts in the COPIED source
    # This prevents PyArmor from hanging when it sees existing runtimes
    for root, dirs, _ in os.walk(pkg_dir):
        for d in dirs:
            if d.startswith("pyarmor_runtime"):
                print(f"🧹 Removing legacy runtime from build source: {d}")
                shutil.rmtree(os.path.join(root, d))

def encrypt():
    print(f"🔒 Encrypting package '{OUTPUT_DIR}' (Target: windows.x86_64)...")
    # Output goes to a temp dir first, then we'll move it
    target_output = "dist_obfuscated"
    if os.path.exists(target_output):
        shutil.rmtree(target_output)
        
    cmd = [
        sys.executable, "-m", "pyarmor.cli", "gen",
        "--platform", "windows.x86_64",
        "--output", target_output,
        OUTPUT_DIR # Obfuscate the WHOLE package directory
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=BUILD_SRC_DIR)
    
    # Move the obfuscated package to the final OUTPUT_DIR in project root
    print(f"🚚 Moving obfuscated package to {OUTPUT_DIR}...")
    dest_path = os.path.join(BUILD_SRC_DIR, target_output)
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    shutil.move(os.path.join(dest_path, OUTPUT_DIR), OUTPUT_DIR)
    
    # Also move the runtime folder(s) to the project root (next to epanet_turbo)
    for item in os.listdir(dest_path):
        if item.startswith("pyarmor_runtime"):
            print(f"📦 Including runtime: {item}")
            if os.path.exists(item):
                shutil.rmtree(item)
            shutil.move(os.path.join(dest_path, item), item)
            
    print("✅ Encryption successful.")

def finalize_package():
    print("📦 Finalizing package structure...")
    
    # 1. Examples
    dest_examples = os.path.join(OUTPUT_DIR, "examples")
    if os.path.exists(dest_examples):
        shutil.rmtree(dest_examples)
    shutil.copytree(EXAMPLES_DIR, dest_examples)
    
    # Ensure it's a package
    with open(os.path.join(dest_examples, "__init__.py"), "w") as f:
        f.write("# Examples package\n")
        
    # 2. DLLs (Synchronize from src/dll)
    dest_dll = os.path.join(OUTPUT_DIR, "dll")
    src_dll = os.path.join(SRC_DIR, "dll")
    if os.path.exists(src_dll):
        print(f"📁 Synchronizing binaries from {src_dll}...")
        # Clean destination if it exists from obfuscation step
        if os.path.exists(dest_dll):
            shutil.rmtree(dest_dll)
        shutil.copytree(src_dll, dest_dll)
    else:
        print(f"⚠️  WARNING: {src_dll} not found!")

def build_wheel():
    print("🚀 Building Wheel...")
    # Use --no-isolation to avoid hanging on "Installing build dependencies"
    # Use --wheel to skip sdist and avoid recursive invocation
    subprocess.check_call([sys.executable, "-m", "build", "--no-isolation", "--wheel"])

if __name__ == "__main__":
    try:
        clean()
        prepare_source()
        encrypt()
        finalize_package()
        build_wheel()
        print(f"\n✅ Build Complete! artifacts in dist/")
    except Exception as e:
        print(f"\n❌ Build Failed: {e}")
        sys.exit(1)
