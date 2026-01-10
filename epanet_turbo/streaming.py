import struct
import json
import time
import shutil
import numpy as np
import polars as pl
from pathlib import Path
from typing import BinaryIO, List, Dict, Any, Union

# M3-2 Output Protocol Constants
HEADER_SIZE = 512
MAGIC = b'EPST'  # EPANET Streaming
VERSION = 2      # Bumped for Hybrid Sidecar Protocol

class StreamingReporter:
    """
    流式结果写入器 (Protocol V2)
    
    生成文件结构：
    1. {filename}.out:        二进制数据文件 (Time-Major Matrix: [Time|Pressure|Flow] blocks)
    2. {filename}.meta.json:  元数据文件 (Config, Counts, File Refs)
    3. {filename}.nodes.arrow: 节点ID列表 (Arrow IPC)
    4. {filename}.links.arrow: 管段ID列表 (Arrow IPC)
    5. {filename}.times.npy:   时间步索引 (Int32 Array)
    """
    def __init__(self, output_path: str, node_ids: List[str], link_ids: List[str], rpt_step: int):
        self.output_path = Path(output_path)
        # Derived paths
        self.meta_path = self.output_path.with_suffix('.meta.json')
        self.nodes_path = self.output_path.with_name(f"{self.output_path.stem}.nodes.arrow")
        self.links_path = self.output_path.with_name(f"{self.output_path.stem}.links.arrow")
        self.times_path = self.output_path.with_name(f"{self.output_path.stem}.times.npy")
        
        self.node_ids = node_ids
        self.link_ids = link_ids
        self.rpt_step = rpt_step
        
        self.n_nodes = len(node_ids)
        self.n_links = len(link_ids)
        self.file: BinaryIO = None
        self.times_cache: List[int] = []
        
        # 确保目录存在
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        self._write_sidecars()
        self._write_meta()
        self._open_bin()

    def _write_sidecars(self):
        """写入 ID 列表到 Arrow IPC 文件"""
        # Nodes
        pl.DataFrame({"id": self.node_ids}).write_ipc(self.nodes_path)
        # Links
        pl.DataFrame({"id": self.link_ids}).write_ipc(self.links_path)

    def _write_meta(self):
        """写入轻量级元数据文件 (JSON)"""
        meta = {
            'version': VERSION,
            'created_at': time.time(),
            'rpt_step': self.rpt_step,
            'counts': {
                'nodes': self.n_nodes,
                'links': self.n_links
            },
            'files': {
                'ids_nodes': self.nodes_path.name,
                'ids_links': self.links_path.name,
                'times': self.times_path.name
            }
        }
        with open(self.meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2)

    def _open_bin(self):
        """打开二进制文件并写入 Protocol Header"""
        self.file = open(self.output_path, 'wb')
        
        # Header Structure (512 bytes)
        # magic(4s) | version(i) | n_nodes(i) | n_links(i) | start_time(q) | rpt_step(i)
        # reserved (484 bytes)
        header = struct.pack(
            '<4si ii q i',
            MAGIC,
            VERSION,
            self.n_nodes,
            self.n_links,
            int(time.time()),
            int(self.rpt_step)
        )
        
        # Padding
        padding = b'\x00' * (HEADER_SIZE - len(header))
        self.file.write(header + padding)
        self.file.flush()

    def write_step(self, t: int, pressures: np.ndarray, flows: np.ndarray):
        """
        写入一个时间步的数据
        
        Args:
            t: 仿真时刻 (秒)
            pressures: 节点压力数组 (float32 compatible)
            flows: 管段流量数组 (float32 compatible)
        """
        if self.file is None:
            raise RuntimeError("StreamingReporter is closed")
            
        # Update times cache
        self.times_cache.append(int(t))

        # 格式: Time(4B int) | NodePressures(...) | LinkFlows(...)
        # 数据强制转为 float32 以节省空间
        t_bytes = struct.pack('<i', int(t))
        p_bytes = pressures.astype(np.float32).tobytes()
        f_bytes = flows.astype(np.float32).tobytes()
        
        self.file.write(t_bytes)
        self.file.write(p_bytes)
        self.file.write(f_bytes)

    def close(self):
        if self.file:
            self.file.flush()
            self.file.close()
            self.file = None
            
            # Save times.npy
            np.save(self.times_path, np.array(self.times_cache, dtype=np.int32))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def load_streaming_result(result_dir_or_file: Union[str, Path]) -> Dict[str, Any]:
    """
    加载流式结果文件 (M3-2 Reader V2 Hybrid)
    
    Args:
        result_dir_or_file: 结果目录 或 .out 文件路径
        
    Returns:
        Dict 包含:
        - pressure: np.ndarray (nT, nN) float32
        - flow: np.ndarray (nT, nL) float32
        - times: np.ndarray (nT,) int32
        - node_ids: List[str]
        - link_ids: List[str]
    """
    path = Path(result_dir_or_file)
    if path.is_dir():
        # 如果是目录，假设里面有 .out 文件
        candidates = list(path.glob("*.out"))
        if not candidates:
            raise FileNotFoundError(f"No .out files found in {path}")
        out_path = max(candidates, key=lambda p: p.stat().st_mtime)
    else:
        out_path = path if path.suffix == '.out' else path.with_suffix('.out')
        
    meta_path = out_path.with_suffix('.meta.json')
    
    if not out_path.exists():
        raise FileNotFoundError(f"Output file not found: {out_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")
        
    # 1. Load Metadata (Slim)
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    version = meta.get('version', 1)
    n_nodes = meta['counts']['nodes']
    n_links = meta['counts']['links']
    
    # 2. Load IDs (Support V1 and V2)
    if version >= 2:
        # Load from Arrow Sidecars
        # Resolve paths relative to meta file
        files = meta.get('files', {})
        nodes_file = files.get('ids_nodes', out_path.with_name(f"{out_path.stem}.nodes.arrow").name)
        links_file = files.get('ids_links', out_path.with_name(f"{out_path.stem}.links.arrow").name)
        
        nodes_path = out_path.parent / nodes_file
        links_path = out_path.parent / links_file
        
        if not nodes_path.exists() or not links_path.exists():
             raise FileNotFoundError(f"Sidecar ID files missing: {nodes_path} or {links_path}")

        node_ids = pl.read_ipc(nodes_path)['id'].to_list()
        link_ids = pl.read_ipc(links_path)['id'].to_list()
    else:
        # Legacy V1: IDs in JSON
        node_ids = meta['ids']['nodes']
        link_ids = meta['ids']['links']
    
    # 3. Load Binary Data
    times = []
    
    with open(out_path, 'rb') as f:
        # Read Header
        header_data = f.read(HEADER_SIZE)
        if len(header_data) < HEADER_SIZE:
            raise ValueError("File too short for header")
            
        magic, ver, nn, nl, start_t, rpt_s = struct.unpack('<4si ii q i', header_data[:28])
        
        if magic != MAGIC:
            raise ValueError(f"Invalid magic: {magic}")
            
        # Calculate chunk size
        # Step: t(4) + p(N*4) + f(L*4)
        step_size = 4 + (n_nodes * 4) + (n_links * 4)
        
        file_size = out_path.stat().st_size
        data_size = file_size - HEADER_SIZE
        n_steps = data_size // step_size
        
        dtype = np.dtype([
            ('t', '<i4'),
            ('p', f'<{n_nodes}f4'),
            ('f', f'<{n_links}f4')
        ])
        
        # Efficient bulk read using numpy
        raw_data = np.fromfile(f, dtype=dtype, count=n_steps)
        
        times = raw_data['t']
        pressures = raw_data['p']  # shape (nT, nN)
        flows = raw_data['f']      # shape (nT, nL)
        
    return {
        'times': times,
        'pressure': pressures,
        'flow': flows,
        'node_ids': node_ids,
        'link_ids': link_ids
    }
