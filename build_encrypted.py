import os
import sys
import shutil
import subprocess
from pathlib import Path

# 配置
SRC_DIR = Path("epanet_turbo")
DIST_DIR = Path("dist_encrypted")

def check_pyarmor():
    try:
        result = subprocess.run([sys.executable, "-m", "pyarmor.cli", "--version"], 
                               capture_output=True, text=True)
        print(f"PyArmor version: {result.stdout.strip()}")
        return True
    except Exception:
        print(" PyArmor not installed. Run: pip install pyarmor")
        return False

def encrypt_modules():
    print("="*60)
    print(" EPANET-Turbo Encryption Script")
    print("="*60)
    if not check_pyarmor():
        return False
    
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir()

    out_pkg = DIST_DIR / "epanet_turbo"
    out_pkg.mkdir(parents=True, exist_ok=True)

    # 复制 DLL 和 __init__.py
    shutil.copytree(SRC_DIR / "dll", out_pkg / "dll", dirs_exist_ok=True)       
    shutil.copy(SRC_DIR / "__init__.py", out_pkg / "__init__.py")

    # 加密模块
    modules = ["engine.py", "parser.py", "telemetry.py", "streaming.py", "context.py"]
    for mod in modules:
        src_file = SRC_DIR / mod
        if not src_file.exists():
            print(f"  Skip missing: {mod}")
            continue
        print(f" Encrypting {mod}...")
        subprocess.run([sys.executable, "-m", "pyarmor.cli", "gen", "-O", str(DIST_DIR), str(src_file)], check=True)
    
    # 整理加密后的文件
    for mod in modules:
        encrypted_file = DIST_DIR / mod
        if encrypted_file.exists():
            shutil.move(encrypted_file, out_pkg / mod)
    
    # 移动运行时环境
    runtime_dirs = list(DIST_DIR.glob("pyarmor_runtime_*"))
    for rdir in runtime_dirs:
        shutil.move(rdir, out_pkg / rdir.name)

    print(f" Encryption complete! Files saved to: {DIST_DIR}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--encrypt":
        encrypt_modules()
    else:
        print("Usage: python build_encrypted.py --encrypt")
