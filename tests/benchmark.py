"""
EPANET-Turbo 性能基准测试

对比 Open-Once/Run-Many + Batch Setter 与传统方式的性能差异
"""

import time
import numpy as np
from pathlib import Path

from epanet_turbo import simulate, ModelContext

def benchmark_open_once(inp_path: str, n_scenarios: int = 100):
    """使用 Open-Once/Run-Many 模式运行多场景"""
    print(f"\n🚀 Open-Once/Run-Many Mode ({n_scenarios} scenarios)")
    
    t0 = time.perf_counter()
    with ModelContext(inp_path) as ctx:
        # 获取前两个节点 ID
        node_ids = ctx._node_ids[:2]
        for i in range(n_scenarios):
            # 随机修改需水量
            demands = {
                nid: 100 + np.random.rand() * 200 for nid in node_ids
            }
            res = ctx.run_scenario(demands=demands)
    
    elapsed = time.perf_counter() - t0
    per_scenario = elapsed / n_scenarios * 1000
    print(f"   Total: {elapsed:.3f}s")
    print(f"   Per scenario: {per_scenario:.2f}ms")
    return elapsed

def benchmark_open_each(inp_path: str, n_scenarios: int = 100):
    """传统方式：每次都重新打开文件"""
    print(f"\n🐌 Open-Each Mode ({n_scenarios} scenarios)")
    print("   (需要修改 INP 文件，这里用简化测试)")
    
    t0 = time.perf_counter()
    for i in range(n_scenarios):
        # 每次都重新打开
        with ModelContext(inp_path) as ctx:
            node_ids = ctx._node_ids[:2]
            demands = {
                nid: 100 + np.random.rand() * 200 for nid in node_ids
            }
            res = ctx.run_scenario(demands=demands, reset=False)
    
    elapsed = time.perf_counter() - t0
    per_scenario = elapsed / n_scenarios * 1000
    print(f"   Total: {elapsed:.3f}s")
    print(f"   Per scenario: {per_scenario:.2f}ms")
    return elapsed

def main():
    print("=" * 60)
    print("  EPANET-Turbo v1.1 Performance Benchmark")
    print("=" * 60)
    
    # 首选大规模网络
    large_inp = Path(r"d:\Project\开发项目\EPANET\Example\gz_clean.inp")
    small_inp = Path(__file__).parent.parent / "examples" / "Net1.inp"
    
    if large_inp.exists():
        inp_path = large_inp
        n_scenarios = 5  # 非常大的网络，跑 5 个场景以节省时间
        print(f"\n📁 Large Network: {inp_path.name}")
    elif small_inp.exists():
        inp_path = small_inp
        n_scenarios = 100
        print(f"\n📁 Small Network: {inp_path.name}")
    else:
        print("❌ No INP file found")
        return
    
    # 预热
    print("\n⏳ Warming up...")
    with ModelContext(str(inp_path)) as ctx:
        ctx.run_scenario()
    
    # 运行基准测试
    t_once = benchmark_open_once(str(inp_path), n_scenarios)
    t_each = benchmark_open_each(str(inp_path), n_scenarios)
    
    # 计算提速比
    speedup = t_each / t_once
    
    print("\n" + "=" * 60)
    print(f"  📊 Result: Open-Once is {speedup:.1f}x faster")
    print("=" * 60)
    
    # 检查 batch setter 是否启用
    with ModelContext(str(inp_path)) as ctx:
        if ctx._use_batch_setter:
            print("\n✅ Batch Setter: ENABLED")
        else:
            print("\n⚠️  Batch Setter: DISABLED (fallback mode)")

if __name__ == "__main__":
    main()
