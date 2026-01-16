import sys
import os
import subprocess
import glob
import shutil

# Color helper (if supported terminal)
def print_c(msg, color="INFO"):
    print(msg) # Keeping it simple for Windows compat without colorama

def is_venv():
    """Check if running inside a virtual environment."""
    return (hasattr(sys, 'real_prefix') or
            (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

def ask_user(question_en, question_cn, default="y"):
    """Bilingual Yes/No prompt."""
    prompt = f"{question_en}\n{question_cn} [Y/n]: "
    try:
        choice = input(prompt).strip().lower()
    except EOFError:
        choice = default
        
    if not choice:
        choice = default
    return choice.startswith('y')

def get_python_exe(venv_path):
    """Get path to python executable in venv."""
    if sys.platform == "win32":
        return os.path.join(venv_path, "Scripts", "python.exe")
    return os.path.join(venv_path, "bin", "python")

def find_wheel():
    """Find the latest wheel file in current dir or dist."""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Priority 1: Script directory (Release mode)
    # Search relative to the SCRIPT, not the CWD
    wheels = glob.glob(os.path.join(script_dir, "*.whl"))
    
    # Priority 2: dist directory (Dev mode) relative to script
    if not wheels:
        wheels = glob.glob(os.path.join(script_dir, "dist", "*.whl"))
        
    if not wheels:
        return None
        
    # Sort by modification time, newest first
    wheels.sort(key=os.path.getmtime, reverse=True)
    return wheels[0]

def main():
    print("\n" + "="*60)
    print(" 📦 EPANET-Turbo v2.0.0 Setup Assistant / 安装向导")
    print("="*60 + "\n")

    # --- Step -1: System Diagnostic ---
    import platform
    arch = platform.machine().lower()
    py_arch = platform.architecture()[0].lower()
    system = platform.system()
    print(f"Diagnostic Info:")
    print(f"  OS: {system} {platform.release()}")
    print(f"  Machine: {platform.machine()}")
    print(f"  Python: {sys.version.split()[0]} ({platform.architecture()[0]})")
    
    # Check Python version (Must be 3.10, 3.11, or 3.12)
    py_ver = sys.version_info
    if not (3, 10) <= py_ver[:2] <= (3, 12):
        print("\n" + "!"*60)
        print("❌ CRITICAL ERROR: Unsupported Python Version")
        print(f"Detected: Python {py_ver.major}.{py_ver.minor}")
        print("Required: Python 3.10, 3.11, or 3.12")
        print("EPANET-Turbo binary extensions are compiled for specific Python versions.")
        print("Using Python 3.13+ or <3.10 will cause 'DLL load failed'.")
        print("❌ 严重错误: 不支持的 Python 版本")
        print(f"检测到: Python {py_ver.major}.{py_ver.minor}")
        print("要求: Python 3.10, 3.11, 或 3.12")
        print("!"*60 + "\n")
        sys.exit(1)

    is_mac = system == "Darwin"
    if ("arm" in arch or "aarch" in arch) and not is_mac:
        print("\n" + "!"*60)
        print("⚠️  WARNING: ARM Architecture Detected")
        print("EPANET-Turbo relies on x64 optimized DLLs (Intel/AMD).")
        print("Running on ARM64 Native Python might fail to load the core engine.")
        print("Recommendation: Use an x64 version of Python (running via emulation on Windows ARM).")
        print("警告: 检测到 ARM 架构。本项目依赖 x64 优化的 DLL。")
        print("使用原生 ARM64 Python 可能无法加载核心引擎。建议使用 x64 版本的 Python (通过仿真运行)。")
        print("!"*60 + "\n")
        # Give user a chance to abort if they know it won't work, but proceed if they want to try.
        # But if this IS the cause of pandas failure, we should note it.
    elif is_mac and "arm" in arch:
        print("✅ Apple Silicon (ARM64) detected. Native support enabled.")
        
    if "64" not in py_arch:
        print("❌ CRITICAL: 32-bit Python detected. This project requires 64-bit Python (x64).")
        sys.exit(1)

    # --- Step 0: Check Environment (Environment Check) ---
    in_venv = is_venv()
    # Safety guard: Check if we already relaunched ourselves
    is_relaunched = os.environ.get("EPANET_SETUP_RELAUNCHED") == "1"
    
    print(f"Current Environment Status: {'[Virtual Env]' if in_venv else '[System/Global]'}")
    print(f"当前环境状态: {'[虚拟环境]' if in_venv else '[系统全局]'}")
    
    # Check for Venv creation request if not already in one AND not relaunched
    if not in_venv and not is_relaunched:
        print("\n" + "-"*40)
        create_venv = ask_user(
            "Do you want to create a clean isolated environment? (Recommended)",
            "您是否想创建一个干净的隔离环境? (推荐)",
            default="y"
        )
        
        if create_venv:
            venv_name = "epanet_env"
            print(f"\n🚀 Creating virtual environment '{venv_name}'... / 正在创建虚拟环境...")
            try:
                import venv
                # clear=True ensures we wipe any existing stale/corrupted env
                venv.create(venv_name, with_pip=True, clear=True)
                print("✅ Environment created (Clean Slate). / 干净的虚拟环境创建成功。")
                
                # Re-launch self inside venv
                print("🔄 Restarting script inside the new environment... / 正在新环境中重启脚本...")
                python_exe = get_python_exe(venv_name)
                
                # Upgrade pip first just in case
                try:
                    subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
                except:
                    pass

                # Pass original args
                cmd = [python_exe] + sys.argv
                env = os.environ.copy()
                env["EPANET_SETUP_RELAUNCHED"] = "1"
                subprocess.check_call(cmd, env=env)
                return # Exit this parent process
            except Exception as e:
                print(f"❌ Failed to create environment: {e}")
                print("⚠️  Proceeding in current environment. / 将在当前环境中继续。")
    
    if not in_venv and not is_relaunched:
        print("\n" + "!"*60)
        print("⚠️  WARNING: Installing to GLOBAL/EXISTING Environment")
        print("   You chose NOT to create an isolated virtual environment.")
        print("   This might pollute your system Python or conflict with other packages.")
        print("⚠️  警告: 即将安装到 全局/现有 环境")
        print("   您选择了不创建隔离的虚拟环境。")
        print("   这可能会污染您的系统 Python 或与其他包发生冲突。")
        print("!"*60 + "\n")
        # Optional: Add a pause or confirmation here if desired, but user already said "No" to venv.

    # --- Step 1: Network Configuration (Mirror) ---
    print("\n" + "-"*40)
    use_mirror = ask_user(
        "Are you in Mainland China (and NOT using VPN)?",
        "您是否在中国大陆 (且 **未开启** VPN/代理)?",
        default="n"
    )
    
    pip_opts = ""
    if use_mirror:
        print("🇨🇳 Using Tsinghua PyPI Mirror. / 已启用清华镜像源。")
        pip_opts = "-i https://pypi.tuna.tsinghua.edu.cn/simple"

    # --- Step 2: Locate Wheel ---
    print("\n" + "-"*40)
    print("🔍 Searching for installation package... / 正在寻找安装包...")
    wheel_path = find_wheel()
    
    if not wheel_path:
        print("❌ Error: No .whl file found!")
        print("❌ 错误: 未找到 .whl 文件!")
        print("Please place the .whl file in the same folder as this script.")
        print("请将 .whl 文件放在此脚本同一目录下。")
        input("Press Enter to exit... (按回车键退出)")
        sys.exit(1)
        
    print(f"✅ Found Package / 找到包: {wheel_path}")

    # --- Step 3: Install ---
    print("\n" + "-"*40)
    print("🛠️  Installing... / 正在安装...")
    
    # Environment Check for CPU features (AVX2/Rosetta support)
    polars_variant = "polars>=0.20.0" # Default to standard polars
    needs_compat = False
    try:
        # 1. Quick check via platform string
        import platform
        proc = platform.processor().lower()
        
        # Special case for macOS ARM: Native polars works fine, so we don't strictly need rtcompat
        # unless user specifically wants it. For now, we trust the logic but note that 
        # macOS ARM wheels for polars are generally 'standard' but work.
        # But let's stick to 'polars>=0.20.0' for macOS ARM to avoid issues with rtcompat variants missing.
        is_mac_arm = platform.system() == "Darwin" and ("arm" in platform.machine().lower())
        if is_mac_arm:
             polars_variant = "polars>=0.20.0" 
        elif "apple" in proc or "virtual" in proc: # Other Apple/Virtual machines might need compat
            needs_compat = True
        
        # 2. Definitive check via Windows API (AVX2 support)
        # PF_AVX2_INSTRUCTIONS_AVAILABLE = 40
        if not needs_compat and platform.system() == "Windows": # Only check AVX2 on Windows
            import ctypes
            if hasattr(ctypes, "windll") and hasattr(ctypes.windll.kernel32, "IsProcessorFeaturePresent"):
                if ctypes.windll.kernel32.IsProcessorFeaturePresent(40) == 0:
                    needs_compat = True
            
        if needs_compat:
            print("💡 Detected Limited CPU Features / 检测到 CPU 指令集受限 (如 ARM/Rosetta)")
            print("   Using 'polars[rtcompat]' for better stability. / 将使用兼容版 Polars。")
            polars_variant = "polars[rtcompat]>=0.20.0"
    except Exception as e:
        # Fallback to high-perf if check fails, to avoid blocking valid installs
        pass

    # Construct pip command
    # Use --upgrade instead of --force-reinstall to be safer by default
    # Explicitly install 'numpy' to ensure we have VC Runtimes (in numpy.libs) for Self-Healing
    # use --prefer-binary to avoid building pandas/polars from source if a binary is available
    base_install_cmd = [sys.executable, "-m", "pip", "install", wheel_path, polars_variant, "requests", "numpy"]
    if use_mirror:
        base_install_cmd += ["-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
    base_install_cmd += ["--force-reinstall", "--prefer-binary"]

    print(f"Running: {' '.join(base_install_cmd)}")
    try:
        # Use subprocess.run to capture output for diagnostic and repair
        result = subprocess.run(base_install_cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        print("✅ Installation Complete. / 安装完成。")
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        
        # Check for specific "uninstall-no-record-file" error (often seen with polars-runtime-32)
        if "uninstall-no-record-file" in e.stderr or "no RECORD file was found" in e.stderr:
            print("\n" + "!"*40)
            print("⚠️  DETECTED CORRUPTED PIP ENVIRONMENT / 检测到环境元数据损坏")
            print("Attempting Self-Repair: Force-reinstalling polars-runtime-32...")
            
            repair_cmd = [sys.executable, "-m", "pip", "install", "--force-reinstall", "--no-deps", "polars-runtime-32"]
            if use_mirror:
                repair_cmd += ["-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
            
            print(f"Running Repair: {' '.join(repair_cmd)}")
            try:
                subprocess.run(repair_cmd, check=True)
                print("🛠️  Repair attempt 1 done. Retrying main installation...")
                # Retry the main install one more time
                subprocess.run(base_install_cmd, check=True)
                print("✅ Installation Fixed and Completed! / 安装修复并成功。")
            except Exception as repair_err:
                print(f"❌ Auto-repair failed: {repair_err}")
                print("Please try manually: pip install --force-reinstall --no-deps polars-runtime-32")
                sys.exit(1)
        else:
            print("❌ Installation Failed. / 安装失败。")
            print("Tip: If usage permission error occurs, try running as Administrator.")
            print("提示: 如果出现权限错误，请尝试以管理员身份运行。")
            sys.exit(1)

    # --- Step 4: Verification Demo ---
    print("\n" + "-"*40)
    print("🧪 Running Verification / 运行验证...")
    
    # Pre-inject the DLL fixer code into the demo script
    # This ensures the demo run itself attempts to self-heal
    # Inject the current CWD (where setup_and_demo.py is running) into the script
    # so it can find Net1.inp even when running from temp
    current_run_dir = os.getcwd().replace("\\", "\\\\") # Escape for string literal
    
    demo_header_template = """
import sys
import os
import platform
import ctypes
from glob import glob
from pathlib import Path

INP_FILENAME = "Net1.inp"
SEARCH_DIR = r"__SEARCH_DIR_PLACEHOLDER__"

if not os.path.exists(INP_FILENAME):
    # Try finding it in the parent release folder using the injected path
    potential_path = os.path.join(SEARCH_DIR, "Net1.inp")
    if os.path.exists(potential_path):
        INP_FILENAME = potential_path
    
print(f"Debug: Final INP path = {INP_FILENAME}")

def fix_dll_environment():
    \"\"\"
    Attempt to find missing VC Runtime DLLs in common locations
    and add them to PATH to fix 'DLL load failed'.
    \"\"\"
    if platform.system() != "Windows":
        return

    required_dlls = ["vcruntime140.dll", "msvcp140.dll"]
    
    # 1. Check if already loadable
    missing = []
    for dll in required_dlls:
        try:
            ctypes.cdll.LoadLibrary(dll)
        except OSError:
            missing.append(dll)
            
    if not missing:
        return # All good

    print(f"⚠️  Detected missing Runtime DLLs: {missing}")
    print("🔎 Scanning system for compatible DLLs (Self-Healing)...")
    
    # 2. Search Paths
    search_paths = [
        # Current Directory (Last Resort: User puts DLL here)
        os.getcwd(),
        ".",
        # Common Anaconda/Python paths
        os.path.join(sys.prefix, "Library", "bin"),
        os.path.join(os.path.dirname(sys.executable), "Library", "bin"),
        # Standard Program Files
        r"C:\\Program Files\\EPANET 2.2",
        r"C:\\Program Files (x86)\\EPANET 2.2",
        r"C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\VC\\Redist\\MSVC",
        # Windows System (Dynamic)
        os.path.join(os.environ.get("SystemRoot", r"C:\\Windows"), "System32"),
    ]
    
    # + Try finding via WNTR/NumPy (since they bundle DLLs)
    try:
        import numpy
        # Numpy often has a .libs folder with runtimes
        numpy_path = os.path.dirname(numpy.__file__)
        search_paths.append(os.path.join(numpy_path, ".libs"))
        search_paths.append(os.path.join(numpy_path, "core"))
    except:
        pass
        
    try:
        import wntr
        # Just in case wntr has something
        wntr_path = os.path.dirname(wntr.__file__)
        search_paths.append(wntr_path)
    except:
        pass

    found_path = None
    print(f"🔎 Scanning for DLLs (Process Arch: {platform.machine()})...")
    
    # Debug: Check if we are on a network share which might block DLL loading
    cwd = os.getcwd()
    if cwd.startswith("\\\\"):
        print(f"⚠️  WARNING: Running from Network Share: {cwd}")
        print("    DLL loading might be blocked by Windows Security.")
    
    # Debug: Try importing numpy first
    try:
        import numpy
        print(f"✅ NumPy imported successfully: {numpy.__file__}")
        numpy_path = os.path.dirname(numpy.__file__)
        search_paths.append(os.path.join(numpy_path, ".libs"))
        search_paths.append(os.path.join(numpy_path, "core"))
    except ImportError as e:
        print(f"⚠️  NumPy Import Failed: {e}")

    for base_path in search_paths:
        if not os.path.exists(base_path):
            # print(f"   [Skip] Not found: {base_path}")
            continue
            
        print(f"   📂 Checking: {base_path}")
        # Check if this path has the missing DLL
        all_exist = True
        for dll in missing:
            dll_path = os.path.join(base_path, dll)
            if not os.path.exists(dll_path):
                all_exist = False
            else:
                # File exists, try to load it specifically to test validity
                try:
                    ctypes.cdll.LoadLibrary(dll_path)
                    print(f"      ✅ Validated load: {dll}")
                except OSError as err:
                    print(f"      ❌ Found but failed to load: {dll_path}")
                    print(f"         Error: {err}")
                    # If we found it but can't load it, it's likely architecture mismatch (ARM64 vs x64)
                    all_exist = False

        if all_exist:
            found_path = base_path
            break
            
    if found_path:
        print(f"✅ Found Runtime DLLs in: {found_path}")
        print("🚑 Injecting into PATH...")
        os.environ["PATH"] = found_path + os.pathsep + os.environ["PATH"]
        # Allow immediate loading
        try:
            os.add_dll_directory(found_path)
        except AttributeError:
            pass # Python < 3.8
    else:
        print("❌ Could not auto-find Runtime DLLs. Install VC_Redist.x64.exe if this fails.")

# Run the fix
fix_dll_environment()
"""

    # Inject the search directory
    demo_header = demo_header_template.replace("__SEARCH_DIR_PLACEHOLDER__", current_run_dir)

    demo_code = demo_header + """
print("⏳ Importing epanet_turbo... / 正在导入库...")
try:
    import epanet_turbo
    print(f"🎉 LIBRARY LOADED / 库加载成功: v{epanet_turbo.__version__}")
except ImportError as e:
    # Check for specific DLL missing error (Windows)
    str_e = str(e).lower()
    print(f"Debug: Full Error Details: {e}") 
    if "dll load failed" in str_e and "pyarmor" in str_e:
        print("\\n" + "!"*60)
        print("❌ CRITICAL ERROR: Microsoft Visual C++ Redistributable is missing!")
        print("❌ 严重错误: 您的电脑缺失必要的运行库 (VC++ Redist)。")
        print("!"*60)
        print("\\n🔧 Solution / 解决方法:")
        print("Please download and install the official Microsoft patch:")
        print("请下载并安装微软官方补丁:")
        print("👉 https://aka.ms/vs/17/release/vc_redist.x64.exe")
        print("\\n(After installing, RESTART your IDE/Terminal and try again)")
        print("(安装补丁后，请务必【重启 PyCharm/终端】再重试)")
    else:
        print(f"💀 CRITICAL ERROR / 严重错误: {e}")
    sys.exit(1)

print("\\n[Telemetry Check / 遥测检查]")
print("Status: Active (Best Effort).")
print("状态: 激活 (尽力而为模式)。")

print("\\n[Quick Simulation / 快速模拟]")
try:
    from epanet_turbo.examples import quickstart
    # Run the demo and check results
    pressures, flows = quickstart.main()
    if pressures is not None and not pressures.empty:
        print(f"✅ Simulation Passed. / 模拟测试通过。 ({len(pressures)} steps)")
        print(f"📊 Sample Pressure:\\n{pressures.iloc[:3, :3]}")
    else:
        print("❌ Simulation failed: Empty results. / 仿真失败：结果为空。")
        sys.exit(1)
except Exception as e:
    print(f"💀 Simulation Error / 仿真错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    
    import tempfile
    
    # Create verification script in a TEMP directory to avoid importing local folder by mistake
    # This solves "ImportError" if user runs script inside source code folder
    fd, demo_file_path = tempfile.mkstemp(suffix=".py", prefix="turbo_verify_")
    os.close(fd) # Close low-level handle
    
    # Write content
    with open(demo_file_path, "w", encoding="utf-8") as f:
        f.write(demo_code)
        
    print(f"📄 Generated verification script at: {demo_file_path}")
        
    try:
        # Run verification from the temp dir
        # We pass the absolute path to python and the script
        subprocess.check_call([sys.executable, demo_file_path], cwd=os.path.dirname(demo_file_path))
        print("\n✨ ALL SYSTEMS GO! / 所有系统准备就绪! ✨")
    except:
        print("\n⚠️  Verification reported issues. / 验证报告了问题。")
    finally:
        if os.path.exists(demo_file_path):
            try:
                os.remove(demo_file_path)
            except:
                pass

    if not in_venv:
        # Pause so user can see output if they double-clicked
        input("\nPress Enter to close... (按回车键关闭)")

if __name__ == "__main__":
    main()
