"""
EPANET-Turbo ModelContext (Open-Once / Run-Many)

Copyright (c) 2026 ES (Serein) - All Rights Reserved
Project UID: EPANET-TURBO-ES-2026-SEREIN93

调用顺序（固定，请勿修改）：
  __init__: EN_createproject → EN_open → EN_openH → _snapshot_baseline
  run_scenario: _reset_to_baseline → apply_params → EN_initH → run_loop
  close: EN_closeH → EN_close → EN_deleteproject
"""

import ctypes
import os
import shutil
import tempfile
from typing import Optional, Dict, List, Literal
import numpy as np
import pandas as pd
from pathlib import Path

from .engine import _load_dll, _ansi_bytes

EN_Project = ctypes.c_void_p

# EPANET 2.2 Constants
EN_NODECOUNT = 0
EN_LINKCOUNT = 2
EN_BASEDEMAND = 1
EN_PRESSURE = 11
EN_NOSAVE = 0
EN_INITSETTING = 10
EN_INITSTATUS = 11
EN_FLOW = 8  # Link flow rate

# Link Status
EN_CLOSED = 0
EN_OPEN = 1

# === Profiling API Bindings ===
class ENT_ProfileStats(ctypes.Structure):
    _fields_ = [
        ("total", ctypes.c_double),
        ("assemble", ctypes.c_double),
        ("linear_solve", ctypes.c_double),
        ("headloss", ctypes.c_double),
        ("convergence", ctypes.c_double),
        ("controls", ctypes.c_double),
        ("step_count", ctypes.c_int32),
        ("iter_count", ctypes.c_int32),
    ]

def _bind_turbo_apis(dll):
    """绑定 EPANET-Turbo 扩展 API"""
    try:
        # ENT_set_node_values(ph, prop, indices, values, n)
        dll.ENT_set_node_values.argtypes = [
            ctypes.c_void_p, ctypes.c_int32,
            ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_double),
            ctypes.c_int32
        ]
        dll.ENT_set_node_values.restype = ctypes.c_int32
        
        # ENT_set_link_values(ph, prop, indices, values, n)
        dll.ENT_set_link_values.argtypes = [
            ctypes.c_void_p, ctypes.c_int32,
            ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_double),
            ctypes.c_int32
        ]
        dll.ENT_set_link_values.restype = ctypes.c_int32
        
        # ENT_set_demand_multiplier(ph, factor)
        dll.ENT_set_demand_multiplier.argtypes = [ctypes.c_void_p, ctypes.c_double]
        dll.ENT_set_demand_multiplier.restype = ctypes.c_int32

        # ENT_get_profile(ph, out_struct_ptr)
        dll.ENT_get_profile.argtypes = [ctypes.c_void_p, ctypes.POINTER(ENT_ProfileStats)]
        dll.ENT_get_profile.restype = ctypes.c_int32
        
        # === Batch Getter APIs ===
        # ENT_get_node_values(ph, prop, indices, out, n)
        dll.ENT_get_node_values.argtypes = [
            ctypes.c_void_p, ctypes.c_int32,
            ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_double),
            ctypes.c_int32
        ]
        dll.ENT_get_node_values.restype = ctypes.c_int32
        
        # ENT_get_link_values(ph, prop, indices, out, n)
        dll.ENT_get_link_values.argtypes = [
            ctypes.c_void_p, ctypes.c_int32,
            ctypes.POINTER(ctypes.c_int32), ctypes.POINTER(ctypes.c_double),
            ctypes.c_int32
        ]
        dll.ENT_get_link_values.restype = ctypes.c_int32
        
        # ENT_get_all_node_values(ph, prop, out)
        dll.ENT_get_all_node_values.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.POINTER(ctypes.c_double)]
        dll.ENT_get_all_node_values.restype = ctypes.c_int32
        
        # ENT_get_all_link_values(ph, prop, out)
        dll.ENT_get_all_link_values.argtypes = [ctypes.c_void_p, ctypes.c_int32, ctypes.POINTER(ctypes.c_double)]
        dll.ENT_get_all_link_values.restype = ctypes.c_int32
        
        return True
    except AttributeError:
        return False  # DLL 不支持 turbo 扩展


class ModelContext:
    """
    EPANET 模型上下文管理器 (Open-Once / Run-Many)
    
    设计原则：
    1. 一个 Context = 一个独占的 EPANET 句柄（不支持多线程共享）
    2. EN_openH 只在 __init__ 调用一次，EN_closeH 只在 close() 调用一次
    3. 每个 run_scenario 默认先恢复 baseline，再应用本次 patch
    
    推荐并行方式：multiprocessing（每个进程各开一个 Context）
    """
    
    def __init__(self, inp_path: str, threads: int = None):
        """
        初始化模型上下文
        
        调用顺序: EN_createproject → EN_open → EN_openH → _snapshot_baseline
        
        Args:
            inp_path: INP 文件路径
            threads: OpenMP 线程数（None=auto）
        """
        self.inp_path = Path(inp_path).resolve()
        if not self.inp_path.exists():
            raise FileNotFoundError(f"INP file not found: {inp_path}")
        
        # 设置线程数
        if threads:
            os.environ["OMP_NUM_THREADS"] = str(threads)
            
        self._dll = _load_dll()
        self._ph = ctypes.c_void_p()
        self._hydraulics_opened = False
        self._turbo_enabled = _bind_turbo_apis(self._dll)
        
        # === Step 1: EN_createproject ===
        err = self._dll.EN_createproject(ctypes.byref(self._ph))
        if err != 0:
            raise RuntimeError(f"EN_createproject failed with error {err}")
            
        # === Step 2: EN_open ===
        self._temp_dir = tempfile.mkdtemp(prefix="epanet_turbo_ctx_")
        self._rpt_file = os.path.join(self._temp_dir, "model.rpt")
        self._out_file = os.path.join(self._temp_dir, "model.out")
        
        err = self._dll.EN_open(
            self._ph, 
            _ansi_bytes(str(self.inp_path)), 
            _ansi_bytes(self._rpt_file), 
            _ansi_bytes(self._out_file)
        )
        if err != 0:
            self._cleanup()
            raise RuntimeError(f"EN_open failed with error {err}")
            
        # 获取基本信息
        self.num_nodes = self._get_count(EN_NODECOUNT)
        self.num_links = self._get_count(EN_LINKCOUNT)
        
        # 预加载 ID 列表和映射
        self._node_ids = self._get_node_ids()
        self._link_ids = self._get_link_ids()
        self._node_map = {nid: i+1 for i, nid in enumerate(self._node_ids)}
        self._link_map = {lid: i+1 for i, lid in enumerate(self._link_ids)}
        
        # 预分配索引数组（用于未来 batch setter）
        self._all_node_indices = np.arange(1, self.num_nodes + 1, dtype=np.int32)
        self._all_link_indices = np.arange(1, self.num_links + 1, dtype=np.int32)
        
        # === Step 3: EN_openH (只调用一次!) ===
        err = self._dll.EN_openH(self._ph)
        if err != 0:
            self._cleanup()
            raise RuntimeError(f"EN_openH failed with error {err}")
        self._hydraulics_opened = True
        
        # === Step 4: Snapshot Baseline ===
        self._snapshot_baseline()
        
    def _get_count(self, code: int) -> int:
        val = ctypes.c_int()
        self._dll.EN_getcount(self._ph, code, ctypes.byref(val))
        return val.value
        
    @property
    def node_ids(self) -> List[str]:
        return self._node_ids
        
    @property
    def link_ids(self) -> List[str]:
        return self._link_ids
        
    def _get_node_ids(self) -> List[str]:
        ids = []
        buf = ctypes.create_string_buffer(64)
        for i in range(1, self.num_nodes + 1):
            self._dll.EN_getnodeid(self._ph, i, buf)
            ids.append(buf.value.decode(errors='ignore'))
        return ids

    def _get_link_ids(self) -> List[str]:
        ids = []
        buf = ctypes.create_string_buffer(64)
        for i in range(1, self.num_links + 1):
            self._dll.EN_getlinkid(self._ph, i, buf)
            ids.append(buf.value.decode(errors='ignore'))
        return ids
    
    def _snapshot_baseline(self):
        """
        快照初始状态（用于每次 scenario 前恢复）
        
        包含：
        - 节点 base demand
        - 管段 init status / init setting
        """
        val = ctypes.c_double()
        
        # 节点 base demand
        self._baseline_demands = np.zeros(self.num_nodes, dtype=np.float64)
        for i in range(1, self.num_nodes + 1):
            self._dll.EN_getnodevalue(self._ph, i, EN_BASEDEMAND, ctypes.byref(val))
            self._baseline_demands[i-1] = val.value
            
        # 管段 init status / init setting
        self._baseline_status = np.zeros(self.num_links, dtype=np.float64)
        self._baseline_settings = np.zeros(self.num_links, dtype=np.float64)
        for i in range(1, self.num_links + 1):
            self._dll.EN_getlinkvalue(self._ph, i, EN_INITSTATUS, ctypes.byref(val))
            self._baseline_status[i-1] = val.value
            self._dll.EN_getlinkvalue(self._ph, i, EN_INITSETTING, ctypes.byref(val))
            self._baseline_settings[i-1] = val.value
    
    def _reset_to_baseline(self):
        """恢复到初始快照 (使用 batch setter 优化)"""
        if self._turbo_enabled:
            # 使用 batch setter - 单次 ctypes 调用
            err = self._dll.ENT_set_node_values(
                self._ph, EN_BASEDEMAND,
                self._all_node_indices.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
                self._baseline_demands.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                self.num_nodes
            )
            if err != 0:
                raise RuntimeError(f"ENT_set_node_values failed: {err}")
            
            err = self._dll.ENT_set_link_values(
                self._ph, EN_INITSTATUS,
                self._all_link_indices.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
                self._baseline_status.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                self.num_links
            )
            if err != 0:
                raise RuntimeError(f"ENT_set_link_values (status) failed: {err}")
                
            err = self._dll.ENT_set_link_values(
                self._ph, EN_INITSETTING,
                self._all_link_indices.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
                self._baseline_settings.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                self.num_links
            )
            if err != 0 and err != 251:  # 251 = invalid param (Pipes 没有 setting)
                raise RuntimeError(f"ENT_set_link_values (setting) failed: {err}")
        else:
            # Fallback: Python 循环 (慢)
            for i in range(1, self.num_nodes + 1):
                self._dll.EN_setnodevalue(
                    self._ph, i, EN_BASEDEMAND, 
                    ctypes.c_double(self._baseline_demands[i-1])
                )
            for i in range(1, self.num_links + 1):
                self._dll.EN_setlinkvalue(
                    self._ph, i, EN_INITSTATUS, 
                    ctypes.c_double(self._baseline_status[i-1])
                )
                self._dll.EN_setlinkvalue(
                    self._ph, i, EN_INITSETTING, 
                    ctypes.c_double(self._baseline_settings[i-1])
                )

    def run_scenario(
        self, 
        demands: Optional[Dict[str, float]] = None,
        status: Optional[Dict[str, int]] = None,
        settings: Optional[Dict[str, float]] = None,
        duration: Optional[int] = None,
        reset: Literal["baseline", False] = "baseline"
    ) -> pd.DataFrame:
        """
        运行参数化场景
        
        调用顺序: _reset_to_baseline → apply_params → EN_initH → run_loop
        （注意：不调用 EN_openH 和 EN_closeH！）
        
        Args:
            demands: 节点需水量 {node_id: base_demand}
            status: 管段状态 {link_id: 0/1}
            settings: 阀门/泵设定值 {link_id: setting}
            duration: 仿真时长（秒），None=使用 INP 默认值
            reset: "baseline"=每次先恢复初始状态, False=继承上次状态（高级用户）
            
        Returns:
            pd.DataFrame: 压力结果 [Time, Nodes]
        """
        # === Step 1: Reset to baseline (默认) ===
        if reset == "baseline":
            self._reset_to_baseline()
        
        # === Step 2: Apply Params (必须在 EN_initH 之前!) ===
        self._apply_params_batch(demands, status, settings)

        # === Step 3: EN_initH (重置水力状态，不调用 openH!) ===
        err = self._dll.EN_initH(self._ph, EN_NOSAVE)
        if err != 0:
            raise RuntimeError(f"EN_initH failed with error {err}")
            
        # === Step 4: Solve Loop ===
        t = ctypes.c_long()
        tstep = ctypes.c_long(1)
        pressures_list = []
        times_list = []
        pbuf = (ctypes.c_double * self.num_nodes)()
        
        while tstep.value > 0:
            err = self._dll.EN_runH(self._ph, ctypes.byref(t))
            if err != 0:
                break
                
            # 提取结果
            if hasattr(self._dll, 'EN_getnodevalues'):
                try:
                    self._dll.EN_getnodevalues(self._ph, EN_PRESSURE, pbuf, self.num_nodes)
                except TypeError:
                    self._dll.EN_getnodevalues(self._ph, EN_PRESSURE, pbuf)
                p_arr = np.frombuffer(pbuf, dtype=np.float64, count=self.num_nodes).astype(np.float32)
            else:
                p_arr = np.zeros(self.num_nodes, dtype=np.float32)
                v = ctypes.c_double()
                for i in range(1, self.num_nodes+1):
                    self._dll.EN_getnodevalue(self._ph, i, EN_PRESSURE, ctypes.byref(v))
                    p_arr[i-1] = v.value
            
            pressures_list.append(p_arr.copy())
            times_list.append(t.value)
            
            # 检查 duration 截断
            if duration and t.value >= duration:
                break
            
            err = self._dll.EN_nextH(self._ph, ctypes.byref(tstep))
            if err != 0:
                break
            
        # 注意：不调用 EN_closeH！保持 hydraulics 打开
        
        return pd.DataFrame(
            pressures_list,
            index=times_list,
            columns=self._node_ids
        )
    
    def run_scenario_streaming(
        self,
        output_dir: str,
        demands: Optional[Dict[str, float]] = None,
        status: Optional[Dict[str, int]] = None,
        settings: Optional[Dict[str, float]] = None,
        duration: Optional[int] = None,
        report_step: Optional[int] = None,
        reset: Literal["baseline", False] = "baseline"
    ) -> str:
        """
        流式输出场景仿真 (低内存)
        
        每个 report_step 将结果直接写入 memmap，避免 Python 内存累积。
        结果包含：pressure.npy, flow.npy, times.npy, metadata.json
        
        Returns:
            str: 输出目录路径
        """
        from .streaming import StreamingSink
        
        # === Step 1: Reset to baseline ===
        if reset == "baseline":
            self._reset_to_baseline()
        
        # === Step 2: Apply Params ===
        self._apply_params_batch(demands, status, settings)
        
        # === Step 3: Get duration & report_step from INP ===
        if duration is None:
            dur_val = ctypes.c_long()
            self._dll.EN_gettimeparam(self._ph, 0, ctypes.byref(dur_val))  # EN_DURATION=0
            duration = dur_val.value
        if report_step is None:
            rstep_val = ctypes.c_long()
            self._dll.EN_gettimeparam(self._ph, 6, ctypes.byref(rstep_val))  # EN_REPORTSTEP=6
            report_step = rstep_val.value
            
        # Fallback to HYDSTEP if REPORTSTEP is 0
        if report_step <= 0:
            hstep_val = ctypes.c_long()
            self._dll.EN_gettimeparam(self._ph, 2, ctypes.byref(hstep_val))  # EN_HYDSTEP=2
            report_step = hstep_val.value if hstep_val.value > 0 else 3600  # 默认 1 小时
            
        num_steps = (duration // report_step) + 1 if report_step > 0 else 1
        
        # === Step 4: Create StreamingSink ===
        sink = StreamingSink(
            output_dir=output_dir,
            num_nodes=self.num_nodes,
            num_links=self.num_links,
            num_steps=num_steps,
            node_ids=self._node_ids,
            link_ids=self._link_ids,
            report_step_seconds=report_step,
            dtype=np.float32
        )
        
        # === Step 5: EN_initH ===
        err = self._dll.EN_initH(self._ph, EN_NOSAVE)
        if err != 0:
            raise RuntimeError(f"EN_initH failed with error {err}")
            
        # === Step 6: Simulation Loop with Streaming ===
        t = ctypes.c_long()
        tstep = ctypes.c_long(1)
        last_report = -report_step  # 确保第一步也记录
        
        while tstep.value > 0:
            err = self._dll.EN_runH(self._ph, ctypes.byref(t))
            if err >= 100:  # Only break on critical errors, not warnings (codes 1-99)
                break
            
            # 按 report_step 记录
            if (t.value - last_report) >= report_step:
                # 复用缓冲区，直接写入 sink 的 buffer
                self._dll.ENT_get_all_node_values(
                    self._ph, EN_PRESSURE,
                    sink.pressure_buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                )
                self._dll.ENT_get_all_link_values(
                    self._ph, EN_FLOW,
                    sink.flow_buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                )
                sink.write_step(t.value)
                last_report = t.value
                
            if duration and t.value >= duration:
                break
                
            err = self._dll.EN_nextH(self._ph, ctypes.byref(tstep))
            if err != 0:
                break
                
        # === Step 7: Finalize ===
        sink.finalize()
        sink.close()
        
        return output_dir

    def _apply_params_batch(self, demands, status, settings):
        """使用 batch setter 应用参数"""
        if demands:
            ids = list(demands.keys())
            indices = np.array([self._node_map[nid] for nid in ids if nid in self._node_map], dtype=np.int32)
            values = np.array([demands[nid] for nid in ids if nid in self._node_map], dtype=np.float64)
            
            if len(indices) > 0:
                if self._turbo_enabled:
                    err = self._dll.ENT_set_node_values(
                        self._ph, EN_BASEDEMAND,
                        indices.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
                        values.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                        len(indices)
                    )
                    if err != 0:
                        raise RuntimeError(f"ENT_set_node_values failed: {err}")
                else:
                    for i, idx in enumerate(indices):
                        self._dll.EN_setnodevalue(self._ph, int(idx), EN_BASEDEMAND, ctypes.c_double(values[i]))
                    
        if status:
            ids = list(status.keys())
            indices = np.array([self._link_map[lid] for lid in ids if lid in self._link_map], dtype=np.int32)
            values = np.array([float(status[lid]) for lid in ids if lid in self._link_map], dtype=np.float64)
            
            if len(indices) > 0:
                if self._turbo_enabled:
                    err = self._dll.ENT_set_link_values(
                        self._ph, EN_INITSTATUS,
                        indices.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
                        values.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                        len(indices)
                    )
                    if err != 0:
                        raise RuntimeError(f"ENT_set_link_values (status) failed: {err}")
                else:
                    for i, idx in enumerate(indices):
                        self._dll.EN_setlinkvalue(self._ph, int(idx), EN_INITSTATUS, ctypes.c_double(values[i]))

        if settings:
            ids = list(settings.keys())
            indices = np.array([self._link_map[lid] for lid in ids if lid in self._link_map], dtype=np.int32)
            values = np.array([settings[lid] for lid in ids if lid in self._link_map], dtype=np.float64)
            
            if len(indices) > 0:
                if self._turbo_enabled:
                    err = self._dll.ENT_set_link_values(
                        self._ph, EN_INITSETTING,
                        indices.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
                        values.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                        len(indices)
                    )
                    if err != 0 and err != 251:  # 251 = Pipe 没有 setting
                        raise RuntimeError(f"ENT_set_link_values (setting) failed: {err}")
                else:
                    for i, idx in enumerate(indices):
                        self._dll.EN_setlinkvalue(self._ph, int(idx), EN_INITSETTING, ctypes.c_double(values[i]))

    def get_profile(self) -> Optional[Dict]:
        """获取解算器耗时拆解数据"""
        if not self._turbo_enabled:
            return None
        stats = ENT_ProfileStats()
        err = self._dll.ENT_get_profile(self._ph, ctypes.byref(stats))
        if err != 0:
            return None
        return {
            "total_s": stats.total,
            "assemble_s": stats.assemble,
            "linear_solve_s": stats.linear_solve,
            "headloss_s": stats.headloss,
            "convergence_s": stats.convergence,
            "controls_s": stats.controls,
            "step_count": stats.step_count,
            "iter_count": stats.iter_count,
            "solve_efficiency": (stats.assemble + stats.linear_solve) / stats.total if stats.total > 0 else 0
        }
    
    def get_node_values(self, prop: int, node_ids: Optional[List[str]] = None) -> np.ndarray:
        """批量获取节点属性
        
        Args:
            prop: 属性枚举 (如 EN_PRESSURE)
            node_ids: 节点 ID 列表，若为 None 则获取全量 (Fast Path)
        """
        if not self._turbo_enabled:
            # Fallback to slow way if needed
            pass

        if node_ids is None:
            # Fast Path: 全量导出
            out = np.zeros(self.num_nodes, dtype=np.float64)
            err = self._dll.ENT_get_all_node_values(
                self._ph, prop, out.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
            )
            if err != 0: raise RuntimeError(f"ENT_get_all_node_values failed: {err}")
            return out
        else:
            # Flexible Path: 按需获取
            indices = np.array([self._node_map[nid] for nid in node_ids if nid in self._node_map], dtype=np.int32)
            out = np.zeros(len(indices), dtype=np.float64)
            err = self._dll.ENT_get_node_values(
                self._ph, prop,
                indices.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
                out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                len(indices)
            )
            if err != 0: raise RuntimeError(f"ENT_get_node_values failed: {err}")
            return out

    def get_link_values(self, prop: int, link_ids: Optional[List[str]] = None) -> np.ndarray:
        """批量获取管段属性"""
        if link_ids is None:
            out = np.zeros(self.num_links, dtype=np.float64)
            err = self._dll.ENT_get_all_link_values(
                self._ph, prop, out.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
            )
            if err != 0: raise RuntimeError(f"ENT_get_all_link_values failed: {err}")
            return out
        else:
            indices = np.array([self._link_map[lid] for lid in link_ids if lid in self._link_map], dtype=np.int32)
            out = np.zeros(len(indices), dtype=np.float64)
            err = self._dll.ENT_get_link_values(
                self._ph, prop,
                indices.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)),
                out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                len(indices)
            )
            if err != 0: raise RuntimeError(f"ENT_get_link_values failed: {err}")
            return out

    def _cleanup(self):
        """清理临时目录"""
        if hasattr(self, '_temp_dir') and self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
            except:
                pass

    def close(self):
        """
        释放资源
        
        调用顺序: EN_closeH → EN_close → EN_deleteproject
        """
        if self._ph:
            # === EN_closeH (只在 close() 调用一次!) ===
            if self._hydraulics_opened:
                try:
                    self._dll.EN_closeH(self._ph)
                except:
                    pass
                self._hydraulics_opened = False
                
            # === EN_close ===
            try:
                self._dll.EN_close(self._ph)
            except:
                pass
                
            # === EN_deleteproject ===
            try:
                self._dll.EN_deleteproject(self._ph)
            except:
                pass
            self._ph = None
            
        self._cleanup()

    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
