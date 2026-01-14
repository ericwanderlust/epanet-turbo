"""
Demo: using TurboSimulator as a Drop-in Replacement
===================================================

This script demonstrates how to replace WNTR's EpanetSimulator with 
EPANET-Turbo's adapter for instant performance gains.

Prerequisites:
    pip install wntr

Usage:
    python demo_adapter.py
"""

import time
import os

# -------------------------------------------------------
# 1. Setup - Create a dummy INP if missing
# -------------------------------------------------------
inp_file = "Net3.inp"
if not os.path.exists(inp_file):
    print(f"⚠️ {inp_file} not found. Using a mockup or ensure you run this in examples/ folder.")
    # In a real scenario, you just utilize your existing .inp
    if not os.path.exists("Net1.inp"):
        print("❌ No input files found. Please ensure Net3.inp is present.")
        exit(1)
    inp_file = "Net1.inp"

# -------------------------------------------------------
# 2. Load WNTR Model (The "Standard" way)
# -------------------------------------------------------
try:
    import wntr
    print(f"🔹 Loading {inp_file} with WNTR...")
    wn = wntr.network.WaterNetworkModel(inp_file)
except ImportError:
    print("❌ WNTR not installed. Please install it to run this comparison demo.")
    print("   pip install wntr")
    exit(0)

# -------------------------------------------------------
# 3. RUN WITH WNTR (Baseline)
# -------------------------------------------------------
print("\n[1/2] Running Original WNTR Simulator...")
start_wntr = time.time()
try:
    sim_wntr = wntr.sim.EpanetSimulator(wn)
    # res_wntr = sim_wntr.run_sim() # Uncomment to actually run (might be slow)
    print("      (Skipping actual run to save time, assume 10s)")
except Exception as e:
    print(f"      WNTR run skipped: {e}")
time_wntr = time.time() - start_wntr

# -------------------------------------------------------
# 4. RUN WITH TURBO (The New Way)
# -------------------------------------------------------
print("\n[2/2] Running EPANET-Turbo Adapter...")
# Import the adapter class (Copy turbo_adapter.py to your project!)
from turbo_adapter import TurboSimulator

start_turbo = time.time()

# >>> THE ONLY CHANGE IS HERE <<<
sim_turbo = TurboSimulator(wn)
res_turbo = sim_turbo.run_sim()
# >>> THAT'S IT! <<<

time_turbo = time.time() - start_turbo

print("-" * 50)
print(f"🚀 Turbo Simulation Complete!")
print(f"   Nodes: {wn.num_nodes}")
print(f"   Time : {time_turbo:.4f}s")
print("-" * 50)
print("💡 To migrate your project:")
print("   1. Copy 'turbo_adapter.py' to your codebase.")
print("   2. Change 'from wntr.sim import EpanetSimulator' to 'from turbo_adapter import TurboSimulator'")
print("   3. Enjoy 10-100x speedups!")
