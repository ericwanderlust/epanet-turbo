import os
import shutil
import time
import numpy as np
import polars as pl
from epanet_turbo import InpParser, simulate

INP_FILE = "Example/Net3.inp"
OUT_PREFIX = "test_protocol_v2"

def verify_protocol_v2():
    print(f"Testing with {INP_FILE}...")
    if not os.path.exists(INP_FILE):
        print(f"Error: {INP_FILE} not found.")
        return

    # Clean previous results
    if os.path.exists(f"{OUT_PREFIX}.out"):
        os.remove(f"{OUT_PREFIX}.out")
    if os.path.exists(f"{OUT_PREFIX}.nodes.arrow"):
        os.remove(f"{OUT_PREFIX}.nodes.arrow")

    start = time.time()
    # Run simulation with result prefix
    # Note: simulate() signature might vary, check engine.py if needed.
    # Assuming simulate(inp_file, out_prefix) or similar.
    # If not supported, we might need to modify engine.py or use lower level API.
    # For now, assuming the new engine supports it or we use context.
    
    # Actually, legacy simulate() takes 'report_file', 'binary_file'.
    # Streaming Protocol V2 hooks into the binary file generation?
    # No, StreamingReporter is separate.
    # Let's check how to invoke StreamingReporter.
    # It usually requires using the Context Manager.
    
    from epanet_turbo import ModelContext
    
    with ModelContext(INP_FILE) as model:
        print("Model loaded.")
        print(f"Nodes: {model.num_nodes}, Links: {model.num_links}")
        
        # Configure streaming
        model.enable_streaming(OUT_PREFIX)
        
        # Run simulation
        model.solve()
        
    print(f"Simulation finished in {time.time() - start:.3f}s")
    
    # Verify outputs
    meta_json = f"{OUT_PREFIX}.meta.json"
    nodes_arrow = f"{OUT_PREFIX}.nodes.arrow"
    links_arrow = f"{OUT_PREFIX}.links.arrow"
    out_bin = f"{OUT_PREFIX}.out"
    time_npy = f"{OUT_PREFIX}.times.npy"
    
    files = [meta_json, nodes_arrow, links_arrow, out_bin, time_npy]
    for f in files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            print(f"✅ Generated {f} ({size} bytes)")
        else:
            print(f"❌ Missing {f}")
            exit(1)
            
    # Check sidecar content
    try:
        df_nodes = pl.read_ipc(nodes_arrow)
        print("Nodes Sidecar Head:")
        print(df_nodes.head(3))
        
        if "id" not in df_nodes.columns:
            print("❌ 'id' column missing in nodes sidecar")
            exit(1)
            
        times = np.load(time_npy)
        print(f"Times shape: {times.shape}")
        
    except Exception as e:
        print(f"❌ Read error: {e}")
        exit(1)
        
    print("✅ Protocol V2 Verification PASSED.")

if __name__ == "__main__":
    verify_protocol_v2()
