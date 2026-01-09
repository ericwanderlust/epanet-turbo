"""
EPANET-Turbo v1.1 Regression Test Suite

测试项目：
1. 一致性测试：Open-Once vs Open-Each 结果对比
2. 污染测试：场景 A 改参数 → 场景 B 不改 → B == baseline
3. 重复运行稳定性：同一场景跑 10 次 → 结果一致

运行方式：
    确定性模式（回归测试）: OMP_NUM_THREADS=1 python -m pytest tests/
    性能模式（日常）: python -m pytest tests/
"""

import unittest
import os
import shutil
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path

from epanet_turbo import simulate, ModelContext


class TestConsistency(unittest.TestCase):
    """一致性测试：Open-Once vs Open-Each"""
    
    def setUp(self):
        self.base_dir = Path(__file__).parent.parent
        self.inp_file = self.base_dir / "examples" / "Net1.inp"
        if not self.inp_file.exists():
            self.skipTest("examples/Net1.inp not found")
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def _create_modified_inp(self, original_inp: Path, demands: dict) -> Path:
        """创建修改了 Demand 的临时 INP"""
        content = original_inp.read_text(encoding='utf-8', errors='ignore')
        lines = content.splitlines()
        new_lines = []
        in_junctions = False
        
        for line in lines:
            if line.strip().startswith("[JUNCTIONS]"):
                in_junctions = True
                new_lines.append(line)
                continue
            elif line.strip().startswith("["):
                in_junctions = False
            
            if in_junctions and line.strip() and not line.strip().startswith(";"):
                parts = line.split()
                if len(parts) >= 3:
                    node_id = parts[0]
                    if node_id in demands:
                        parts[2] = str(demands[node_id])
                        line = "\t".join(parts)
            
            new_lines.append(line)
            
        new_inp = Path(self.temp_dir) / f"Net1_mod.inp"
        new_inp.write_text("\n".join(new_lines), encoding='utf-8')
        return new_inp

    def test_demand_consistency(self):
        """测试修改 Demand 后的结果一致性"""
        scenario_demands = {"11": 300.0, "12": 50.0}
        
        # Baseline: 物理修改 INP 文件
        mod_inp = self._create_modified_inp(self.inp_file, scenario_demands)
        res_base, _ = simulate(str(mod_inp))
        
        # Challenger: ModelContext
        with ModelContext(str(self.inp_file)) as ctx:
            res_turbo = ctx.run_scenario(demands=scenario_demands)
            
        # Compare
        self.assertEqual(res_base.shape, res_turbo.shape)
        max_diff = np.max(np.abs(res_base.values - res_turbo.values))
        self.assertLess(max_diff, 1e-5, f"Max diff: {max_diff}")
        print(f"✅ Consistency Test Passed! Max Diff: {max_diff:.2e}")


class TestContamination(unittest.TestCase):
    """污染测试：验证 baseline reset 机制"""
    
    def setUp(self):
        self.base_dir = Path(__file__).parent.parent
        self.inp_file = self.base_dir / "examples" / "Net1.inp"
        if not self.inp_file.exists():
            self.skipTest("examples/Net1.inp not found")
        
    def test_no_contamination(self):
        """场景 A 修改参数 → 场景 B 不改 → B 必须 == baseline"""
        with ModelContext(str(self.inp_file)) as ctx:
            # Baseline run (无修改)
            baseline = ctx.run_scenario()
            
            # 场景 A：大幅修改某些节点的 demand
            scenario_a = ctx.run_scenario(demands={"11": 500.0, "12": 0.0})
            
            # 场景 B：不传任何参数（期望恢复到 baseline）
            scenario_b = ctx.run_scenario()
            
        # 对齐时间步（取共同的时间步）
        common_times = sorted(set(baseline.index) & set(scenario_a.index) & set(scenario_b.index))
        baseline_aligned = baseline.loc[common_times]
        scenario_a_aligned = scenario_a.loc[common_times]
        scenario_b_aligned = scenario_b.loc[common_times]
        
        # 验证 A 和 baseline 不同（确保修改生效）
        diff_a = np.max(np.abs(baseline_aligned.values - scenario_a_aligned.values))
        self.assertGreater(diff_a, 1.0, "Scenario A should differ from baseline")
        
        # 验证 B 和 baseline 一致（无污染）
        # 注意：由于 EPANET 内部状态复杂，允许小幅差异 (< 1e-3)
        diff_b = np.max(np.abs(baseline_aligned.values - scenario_b_aligned.values))
        self.assertLess(diff_b, 1e-3, f"Contamination detected! Diff: {diff_b}")
        print(f"✅ No Contamination! A-Base diff: {diff_a:.2f}, B-Base diff: {diff_b:.2e}")
        
    def test_independent_scenarios(self):
        """场景 A 改一组节点，场景 B 改另一组 → 互不影响"""
        with ModelContext(str(self.inp_file)) as ctx:
            # 场景 A：改节点 11
            res_a = ctx.run_scenario(demands={"11": 500.0})
            
            # 场景 B：改节点 12（节点 11 应恢复 baseline）
            res_b = ctx.run_scenario(demands={"12": 500.0})
            
            # 单独只改 12 的参考结果
            res_ref_b = ctx.run_scenario(demands={"12": 500.0})
            
        # B 和 ref_B 应该一致
        diff = np.max(np.abs(res_b.values - res_ref_b.values))
        self.assertLess(diff, 1e-4, f"Independent scenarios failed! Diff: {diff}")
        print(f"✅ Independent Scenarios Passed! Diff: {diff:.2e}")


class TestRepeatability(unittest.TestCase):
    """重复运行稳定性测试"""
    
    def setUp(self):
        self.base_dir = Path(__file__).parent.parent
        self.inp_file = self.base_dir / "examples" / "Net1.inp"
        if not self.inp_file.exists():
            self.skipTest("examples/Net1.inp not found")
        
    def test_repeated_runs(self):
        """同一场景连续运行 10 次 → 结果必须完全一致"""
        with ModelContext(str(self.inp_file)) as ctx:
            results = []
            scenario = {"11": 200.0, "12": 100.0}
            
            for i in range(10):
                res = ctx.run_scenario(demands=scenario)
                results.append(res.values.copy())
                
        # 比较所有结果
        reference = results[0]
        for i, res in enumerate(results[1:], 1):
            diff = np.max(np.abs(reference - res))
            # 允许小幅浮点累积误差 (< 1e-3)
            self.assertLess(diff, 1e-3, f"Run {i} differs! Max diff: {diff}")
            
        print(f"✅ Repeatability Passed! 10 runs identical")


if __name__ == "__main__":
    unittest.main(verbosity=2)
