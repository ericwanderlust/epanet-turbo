import os
import shutil

PACKAGE_ROOT = "epanet_turbo"
SRC_NESTED = os.path.join(PACKAGE_ROOT, "src")

def flatten():
    if not os.path.exists(SRC_NESTED):
        print(f"No nested src dir found at {SRC_NESTED}")
        return

    print(f"Flattening {SRC_NESTED} into {PACKAGE_ROOT}...")
    
    for item in os.listdir(SRC_NESTED):
        s = os.path.join(SRC_NESTED, item)
        d = os.path.join(PACKAGE_ROOT, item)
        
        if os.path.exists(d):
            if os.path.isdir(d):
                # If it's pyarmor_runtime, we might want to keep the one that works?
                # Usually pyarmor gen creates it in both places or one.
                # Let's assume the one within the generation (src) is fresh.
                print(f"Removing existing dir {d} to replace with {s}")
                try:
                    shutil.rmtree(d)
                except Exception as e:
                    print(f"Failed to remove {d}: {e}")
                    continue
            else:
                print(f"Overwriting file {d}")
                os.remove(d)
        
        print(f"Moving {s} -> {d}")
        shutil.move(s, d)
    
    # Remove empty src dir
    try:
        os.rmdir(SRC_NESTED)
        print("Removed empty nested src dir")
    except:
        pass
        
    # Patch __init__.py
    init_file = os.path.join(PACKAGE_ROOT, "__init__.py")
    if os.path.exists(init_file):
        print("Patching __version__ into __init__.py")
        with open(init_file, "a") as f:
            f.write("\n__version__ = '2.0.0'\n")
    else:
        print("ERROR: __init__.py not found after flattening!")

if __name__ == "__main__":
    flatten()
