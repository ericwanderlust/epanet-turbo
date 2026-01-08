"""
EPANET-Turbo 发布加密脚本

使用 PyArmor 加密核心模块后再发布
运行前请先安装: pip install pyarmor

Copyright (c) 2026 ES (Serein)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 配置
SRC_DIR = Path(__file__).parent / "epanet_turbo"
DIST_DIR = Path(__file__).parent / "dist_encrypted"
MODULES_TO_ENCRYPT = ["parser.py", "engine.py", "telemetry.py"]


def check_pyarmor():
    """检查 PyArmor 是否安装"""
    try:
        result = subprocess.run(["pyarmor", "--version"], capture_output=True, text=True)
        print(f"PyArmor version: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ PyArmor not installed. Run: pip install pyarmor")
        return False


def encrypt_modules():
    """加密核心模块"""
    if not check_pyarmor():
        return False
    
    # 创建输出目录
    out_pkg = DIST_DIR / "epanet_turbo"
    out_pkg.mkdir(parents=True, exist_ok=True)
    
    # 复制 DLL 和 __init__.py
    shutil.copytree(SRC_DIR / "dll", out_pkg / "dll", dirs_exist_ok=True)
    shutil.copy(SRC_DIR / "__init__.py", out_pkg / "__init__.py")
    
    # 加密指定模块
    for mod in MODULES_TO_ENCRYPT:
        src_file = SRC_DIR / mod
        if not src_file.exists():
            print(f"⚠️  Skip missing: {mod}")
            continue
        
        print(f"🔐 Encrypting {mod}...")
        
        # PyArmor 加密命令
        cmd = [
            "pyarmor", "gen",
            "--output", str(out_pkg),
            "--platform", "windows.x86_64",
            str(src_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed: {result.stderr}")
            return False
        
        print(f"   ✅ Done")
    
    # 复制其他文件
    for f in ["README.md", "LICENSE", "pyproject.toml", "requirements.txt"]:
        src = Path(__file__).parent / f
        if src.exists():
            shutil.copy(src, DIST_DIR / f)
    
    shutil.copytree(Path(__file__).parent / "examples", DIST_DIR / "examples", dirs_exist_ok=True)
    
    print(f"\n🎉 Encrypted package ready at: {DIST_DIR}")
    return True


def main():
    print("="*60)
    print("🔐 EPANET-Turbo Encryption Script")
    print("="*60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--encrypt":
        encrypt_modules()
    else:
        print("""
Usage:
  python build_encrypted.py --encrypt    # 加密并打包

Requirements:
  pip install pyarmor

Note:
  PyArmor 免费版有限制，商业发布建议购买许可证。
  加密后的代码无法被直接阅读或修改。
""")


if __name__ == "__main__":
    main()
