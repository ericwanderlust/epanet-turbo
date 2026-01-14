import shutil
import os
import time

def force_remove(path, retries=5):
    if not os.path.exists(path):
        return True
    
    print(f"Attempting to remove {path}...")
    for i in range(retries):
        try:
            if os.path.isfile(path):
                os.remove(path)
            else:
                shutil.rmtree(path)
            print(f"✅ Removed {path}")
            return True
        except Exception as e:
            print(f"⚠️  Attempt {i+1} failed: {e}")
            time.sleep(1)
            
    return False

if __name__ == "__main__":
    import glob
    
    # 1. Clean Shadow Builds
    for p in glob.glob("build_src_*"):
        force_remove(p)
        
    # 2. Clean PyArmor artifacts
    for p in glob.glob("pyarmor_runtime*"):
        force_remove(p)
    force_remove("dist_obfuscated")
    
    # 3. Clean Standard Build Artifacts
    force_remove("build")
    force_remove("epanet_turbo")
    force_remove("epanet_turbo.egg-info")
    force_remove("__pycache__")
    
    # Note: We purposely KEEP 'dist/' (where the wheel is) and 'src/' (source code)
    print("\n✨ Cleanup Complete. Kept 'dist/' and 'src/'.")
