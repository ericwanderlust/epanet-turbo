"""
EPANET-Turbo 快速入门示例
Quick Start Example

Copyright (c) 2026 ES (Serein)
"""

from epanet_turbo import InpParser, simulate
import time

# 示例 INP 文件路径 (使用官方 Net1)
INP_FILE = "Net1.inp"

def main():
    print("="*50)
    print("🏎️ EPANET-Turbo Quick Start Demo")
    print("="*50)
    
    # 1. 解析 INP 文件
    print("\n📄 Parsing INP file...")
    t0 = time.perf_counter()
    parser = InpParser(INP_FILE, verbose=True)
    parse_time = time.perf_counter() - t0
    
    print(f"   Nodes: {parser.num_nodes}")
    print(f"   Links: {parser.num_links}")
    print(f"   Parse time: {parse_time:.3f}s")
    
    # 2. 运行仿真
    print("\n⚡ Running simulation...")
    t0 = time.perf_counter()
    pressures, flows = simulate(INP_FILE)
    sim_time = time.perf_counter() - t0
    
    print(f"   Time steps: {len(pressures)}")
    print(f"   Simulation time: {sim_time:.3f}s")
    
    # 3. 查看结果
    print("\n📊 Sample results (first 5 nodes, time step 0):")
    print(pressures.iloc[0, :5])
    
    print("\n" + "="*50)
    print("✅ Demo completed!")
    print("="*50)


if __name__ == "__main__":
    main()
