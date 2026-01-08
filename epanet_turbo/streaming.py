# EPANET-Turbo Streaming Sink
# 用于40w节点长仿真的低内存结果输出

import os
import json
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path


class StreamingSink:
    """
    Memmap-based Streaming Sink for low-memory simulation output
    
    Layout: Time-Major [T, N] / [T, M]
    """
    
    def __init__(
        self,
        output_dir: str,
        num_nodes: int,
        num_links: int,
        num_steps: int,
        node_ids: list,
        link_ids: list,
        report_step_seconds: int,
        dtype: np.dtype = np.float32
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.num_nodes = num_nodes
        self.num_links = num_links
        self.num_steps = num_steps
        self.dtype = dtype
        self.current_step = 0
        
        # 预分配 memmap
        self.pressure_path = self.output_dir / "pressure.npy"
        self.flow_path = self.output_dir / "flow.npy"
        self.times_path = self.output_dir / "times.npy"
        
        self.pressure = np.memmap(
            self.pressure_path, dtype=dtype, mode='w+',
            shape=(num_steps, num_nodes)
        )
        self.flow = np.memmap(
            self.flow_path, dtype=dtype, mode='w+',
            shape=(num_steps, num_links)
        )
        self.times = np.memmap(
            self.times_path, dtype=np.int64, mode='w+',
            shape=(num_steps,)
        )
        
        # 元数据
        self.metadata = {
            "version": "1.0",
            "dtype": np.dtype(dtype).str,  # 使用 dtype.str 确保可反序列化
            "shape_pressure": [num_steps, num_nodes],
            "shape_flow": [num_steps, num_links],
            "report_step_seconds": report_step_seconds,
            "node_ids": node_ids,
            "link_ids": link_ids,
            "endianness": "<" if np.little_endian else ">",
            "completed": False
        }
        
        # 复用缓冲区 (float64 from DLL)
        self._pressure_buf = np.zeros(num_nodes, dtype=np.float64)
        self._flow_buf = np.zeros(num_links, dtype=np.float64)
        
    @property
    def pressure_buffer(self) -> np.ndarray:
        """返回可复用的 float64 压力缓冲区（DLL 写入用）"""
        return self._pressure_buf
        
    @property
    def flow_buffer(self) -> np.ndarray:
        """返回可复用的 float64 流量缓冲区（DLL 写入用）"""
        return self._flow_buf
        
    def write_step(self, time_seconds: int):
        """将缓冲区数据写入 memmap 并前进一步"""
        if self.current_step >= self.num_steps:
            return  # 超出预分配范围
            
        # float64 → float32 无拷贝转换 (如果 dtype 相同则直接写)
        self.pressure[self.current_step, :] = self._pressure_buf.astype(self.dtype, copy=False)
        self.flow[self.current_step, :] = self._flow_buf.astype(self.dtype, copy=False)
        self.times[self.current_step] = time_seconds
        
        self.current_step += 1
        
    def finalize(self):
        """刷新 memmap 并写入元数据"""
        self.pressure.flush()
        self.flow.flush()
        self.times.flush()
        
        self.metadata["completed"] = True
        self.metadata["actual_steps"] = self.current_step
        
        with open(self.output_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            
    def close(self):
        """释放 memmap 资源"""
        del self.pressure
        del self.flow
        del self.times


def load_streaming_result(output_dir: str) -> Dict[str, Any]:
    """加载 streaming 输出结果"""
    output_dir = Path(output_dir)
    
    with open(output_dir / "metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)
        
    dtype = np.dtype(metadata["dtype"])
    shape_p = tuple(metadata["shape_pressure"])
    shape_f = tuple(metadata["shape_flow"])
    actual = metadata.get("actual_steps", shape_p[0])
    
    pressure = np.memmap(
        output_dir / "pressure.npy", dtype=dtype, mode='r', shape=shape_p
    )[:actual]
    
    flow = np.memmap(
        output_dir / "flow.npy", dtype=dtype, mode='r', shape=shape_f
    )[:actual]
    
    times = np.memmap(
        output_dir / "times.npy", dtype=np.int64, mode='r', shape=(shape_p[0],)
    )[:actual]
    
    return {
        "metadata": metadata,
        "pressure": pressure,
        "flow": flow,
        "times": times,
        "node_ids": metadata["node_ids"],
        "link_ids": metadata["link_ids"]
    }
