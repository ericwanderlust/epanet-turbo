"""
高性能 INP 文件解析器 (基于 Polars)

针对超大规模管网文件（10万-40万节点）优化，相比 WNTR 预计提升 10-50 倍性能。

主要功能：
1. 快速分段定位 INP 文件各 section
2. 使用 Polars 并行解析表格数据
3. 提供与 WNTR 兼容的接口用于坐标和拓扑访问
4. 集成 ModelCache 用于冷启动加速
"""

import os
import re
import io
import time
import mmap
import pickle
from typing import Iterator, Optional, Dict, Tuple, List, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    HAS_POLARS = False
    print("[WARN] Polars not installed, falling back to pandas")
    import pandas as pd

from .cache import ModelCache

class InpParser:
    """高性能 INP 文件解析器（基于 Polars）"""
    
    # 需要解析的 section 列表
    REQUIRED_SECTIONS = {
        'JUNCTIONS', 'RESERVOIRS', 'TANKS', 'PIPES', 'PUMPS', 'VALVES', 'COORDINATES'
    }
    
    def __init__(self, inp_path: str, verbose: bool = False):
        """
        解析 INP 文件，提取关键数据
        
        Args:
            inp_path: INP 文件路径
            verbose: 是否打印调试信息
        """
        self.inp_path = Path(inp_path)
        self.verbose = verbose
        self._section_bounds: Dict[str, Tuple[int, int]] = {}  # section -> (start_line, end_line)
        self._cache_mgr = ModelCache(str(self.inp_path))  # 初始化缓存管理器
        
        t0 = time.perf_counter()
        
        # 尝试从缓存加载
        if self._load_from_cache():
            if self.verbose:
                print(f"[InpParser] Loaded from cache in {time.perf_counter()-t0:.2f}s")
            return

        # 缓存未命中，执行完整解析
        try:
            self._scan_sections()
            self._parse_all()
            
            # 解析完成后保存到缓存
            self._save_to_cache()
            
        finally:
            self._close_mmap()
        
        if self.verbose:
            print(f"[InpParser] Parsed {self.inp_path.name} in {time.perf_counter()-t0:.2f}s")
            # print(f"  Junctions: {len(self._junctions_df)}, "
            #       f"Reservoirs: {len(self._reservoirs_df)}, "
            #       f"Pipes: {len(self._pipes_df)}, "
            #       f"Valves: {len(self._valves_df)}, "
            #       f"Coordinates: {len(self._coordinates_df)}")

    def _load_from_cache(self) -> bool:
        """尝试从缓存加载状态"""
        data = self._cache_mgr.load()
        if data is None:
            return False
            
        try:
            # 恢复所有关键属性
            self._junctions_df = data['junctions']
            self._reservoirs_df = data['reservoirs']
            self._tanks_df = data['tanks']
            self._pipes_df = data['pipes']
            self._valves_df = data['valves']
            self._pumps_df = data['pumps']
            self._coordinates_df = data['coordinates']
            
            self._coord_dict = data['coord_dict']
            self._node_list = data['node_list']
            self._reservoir_ids = data['reservoir_ids']
            self._tank_ids = data['tank_ids']
            return True
        except KeyError as e:
            if self.verbose:
                print(f"[InpParser] Cache corrupted or incompatible: {e}")
            return False

    def _save_to_cache(self):
        """保存当前状态到缓存"""
        data = {
            'junctions': self._junctions_df,
            'reservoirs': self._reservoirs_df,
            'tanks': self._tanks_df,
            'pipes': self._pipes_df,
            'valves': self._valves_df,
            'pumps': self._pumps_df,
            'coordinates': self._coordinates_df,
            
            'coord_dict': self._coord_dict,
            'node_list': self._node_list,
            'reservoir_ids': self._reservoir_ids,
            'tank_ids': self._tank_ids
        }
        self._cache_mgr.save(data)

    def _scan_sections(self):
        """扫描文件，定位各 section 的字节偏移并保持 mmap 开启"""
        self._section_bytes: Dict[str, Tuple[int, int]] = {}
        
        self._f = open(self.inp_path, 'rb')
        try:
            self._mm = mmap.mmap(self._f.fileno(), 0, access=mmap.ACCESS_READ)
        except ValueError:
            # 空文件
            self._f.close()
            return

        # 正则匹配 [SECTION]
        pattern = re.compile(rb'(?:^|\n|\r\n)\s*\[([A-Z]+)\]', re.IGNORECASE)
        match_objs = list(pattern.finditer(self._mm))
        
        for i, m in enumerate(match_objs):
            name = m.group(1).decode('utf-8', errors='ignore').upper()
            if name not in self.REQUIRED_SECTIONS:
                continue
            
            content_start = m.end()
            if i + 1 < len(match_objs):
                content_end = match_objs[i+1].start()
            else:
                content_end = len(self._mm)
            
            self._section_bytes[name] = (content_start, content_end)

    def _close_mmap(self):
        """关闭文件和 mmap"""
        if hasattr(self, '_mm'):
            self._mm.close()
        if hasattr(self, '_f'):
            self._f.close()
            
        if self.verbose:
             pass
             # print(f"[Parser] Section bytes: {self._section_bytes}")

    def _parse_all(self):
        """使用线程池并行解析所有需要的 section"""
        tasks = [
            ('_junctions_df', self._parse_junctions),
            ('_reservoirs_df', self._parse_reservoirs),
            ('_tanks_df', self._parse_tanks),
            ('_pipes_df', self._parse_pipes),
            ('_valves_df', self._parse_valves),
            ('_pumps_df', self._parse_pumps),
            ('_coordinates_df', self._parse_coordinates),
        ]
        
        # 并行执行：利用 Polars 的多线程优势，同时处理不同 section
        with ThreadPoolExecutor(max_workers=min(len(tasks), os.cpu_count() or 1)) as executor:
            future_to_attr = {executor.submit(func): attr for attr, func in tasks}
            for future in future_to_attr:
                attr = future_to_attr[future]
                setattr(self, attr, future.result())
        
        # 构建坐标字典用于快速查找
        self._build_coord_dict()
        # 构建节点列表
        self._build_node_list()

    def _get_section_lazy(self, section: str, min_cols: int) -> Optional[pl.LazyFrame]:
        """复用全局 mmap 提取数据并返回 LazyFrame"""
        if section not in self._section_bytes:
            return None
            
        start, end = self._section_bytes[section]
        if start >= end:
            return None
        
        # 直接从持久化的 mmap 切片，避免重复 I/O
        data = self._mm[start:end]
        if not data:
            return None
            
        buf = io.BytesIO(data)
        
        # 读取
        # separator='\0' hack 读取整行
        try:
            lf = pl.read_csv(
                buf, 
                separator='\0', 
                has_header=False, 
                quote_char=None, 
                new_columns=['raw'],
                truncate_ragged_lines=True
            ).lazy()
        except:
            return None
            
        # 过滤和分割
        lf = (lf
            .filter(
                 (~pl.col('raw').str.starts_with(';')) & 
                 (pl.col('raw').str.len_bytes() > 1)
            )
            .with_columns(
                pl.col('raw').str.extract_all(r'[^\s;]+').alias('parts')
            )
            .filter(pl.col('parts').list.len() >= min_cols)
        )
        return lf

    def _parse_junctions(self) -> pl.DataFrame:
        lf = self._get_section_lazy('JUNCTIONS', 1)
        if lf is None:
            return pl.DataFrame({'id': [], 'elevation': [], 'demand': []})
            
        parts = pl.col('parts')
        return (lf.select([
            parts.list.get(0).alias('id'),
            parts.list.get(1, null_on_oob=True).cast(pl.Float32, strict=False).fill_null(0.0).alias('elevation'),
            parts.list.get(2, null_on_oob=True).cast(pl.Float32, strict=False).fill_null(0.0).alias('demand')
        ]).collect())

    def _parse_reservoirs(self) -> pl.DataFrame:
        lf = self._get_section_lazy('RESERVOIRS', 1)
        if lf is None:
            return pl.DataFrame({'id': [], 'head': [], 'pattern': []})
            
        parts = pl.col('parts')
        return (lf.select([
            parts.list.get(0).alias('id'),
            parts.list.get(1, null_on_oob=True).cast(pl.Float32, strict=False).fill_null(0.0).alias('head'),
            parts.list.get(2, null_on_oob=True).fill_null("").alias('pattern')
        ]).collect())
        
    def _parse_tanks(self) -> pl.DataFrame:
        lf = self._get_section_lazy('TANKS', 1)
        if lf is None:
            return pl.DataFrame({'id': [], 'elevation': [], 'init_level': []})
            
        parts = pl.col('parts')
        return (lf.select([
            parts.list.get(0).alias('id'),
            parts.list.get(1, null_on_oob=True).cast(pl.Float32, strict=False).fill_null(0.0).alias('elevation'),
            parts.list.get(2, null_on_oob=True).cast(pl.Float32, strict=False).fill_null(0.0).alias('init_level')
        ]).collect())

    def _parse_pipes(self) -> pl.DataFrame:
        lf = self._get_section_lazy('PIPES', 3)
        if lf is None:
             return pl.DataFrame({'id': [], 'node1': [], 'node2': [], 'length': [], 'diameter': []})
             
        # Pipes format: ID Node1 Node2 Length Diameter ...
        parts = pl.col('parts')
        return (lf.select([
            parts.list.get(0).alias('id'),
            parts.list.get(1).alias('node1'),
            parts.list.get(2).alias('node2'),
            parts.list.get(3, null_on_oob=True).cast(pl.Float32, strict=False).fill_null(0.0).alias('length'),
            parts.list.get(4, null_on_oob=True).cast(pl.Float32, strict=False).fill_null(0.0).alias('diameter')
        ]).collect())
        
    def _parse_valves(self) -> pl.DataFrame:
        lf = self._get_section_lazy('VALVES', 3)
        if lf is None:
             return pl.DataFrame({'id': [], 'node1': [], 'node2': [], 'diameter': [], 'valve_type': []})
             
        # Valves format: ID Node1 Node2 Diameter Type ...
        parts = pl.col('parts')
        return (lf.select([
            parts.list.get(0).alias('id'),
            parts.list.get(1).alias('node1'),
            parts.list.get(2).alias('node2'),
            parts.list.get(3, null_on_oob=True).cast(pl.Float32, strict=False).fill_null(0.0).alias('diameter'),
            parts.list.get(4, null_on_oob=True).fill_null("").alias('valve_type')
        ]).collect())
        
    def _parse_pumps(self) -> pl.DataFrame:
        lf = self._get_section_lazy('PUMPS', 3)
        if lf is None:
             return pl.DataFrame({'id': [], 'node1': [], 'node2': []})
             
        parts = pl.col('parts')
        return (lf.select([
            parts.list.get(0).alias('id'),
            parts.list.get(1).alias('node1'),
            parts.list.get(2).alias('node2')
        ]).collect())
        
    def _parse_coordinates(self) -> pl.DataFrame:
        lf = self._get_section_lazy('COORDINATES', 3)
        if lf is None:
             return pl.DataFrame({'id': [], 'x': [], 'y': []})
             
        parts = pl.col('parts')
        return (lf.select([
            parts.list.get(0).alias('id'),
            parts.list.get(1, null_on_oob=True).cast(pl.Float32, strict=False).fill_null(0.0).alias('x'),
            parts.list.get(2, null_on_oob=True).cast(pl.Float32, strict=False).fill_null(0.0).alias('y')
        ]).collect())

    # _scan_sections_simple, _read_section_lines 等旧方法不再需要
    
    def _build_coord_dict(self):
        """构建坐标字典用于 O(1) 查找 - 向量化版本"""
        if len(self._coordinates_df) == 0:
            self._coord_dict = {}
            return
            
        # 向量化提取：比 iter_rows 快 10-50x
        ids = self._coordinates_df['id'].to_list()
        xs = self._coordinates_df['x'].to_list()
        ys = self._coordinates_df['y'].to_list()
        self._coord_dict = dict(zip(ids, zip(xs, ys)))
    
    def _build_node_list(self):
        """构建节点 ID 列表 - 向量化版本"""
        # 直接用 Polars concat + unique 替代 Python set
        all_ids = pl.concat([
            self._junctions_df.select('id'),
            self._reservoirs_df.select('id'),
            self._tanks_df.select('id')
        ])['id'].unique().sort().to_list()
        
        self._node_list = all_ids
        
        # 构建快速查找集合
        self._reservoir_ids = set(self._reservoirs_df['id'].to_list())
        self._tank_ids = set(self._tanks_df['id'].to_list())
    
    # ============= 公共接口 (兼容 WNTR) =============
    
    @property
    def junctions(self) -> pl.DataFrame:
        """[JUNCTIONS] DataFrame: id, elevation, demand"""
        return self._junctions_df
    
    @property
    def coordinates(self) -> pl.DataFrame:
        """[COORDINATES] DataFrame: id, x, y"""
        return self._coordinates_df
    
    @property
    def pipes(self) -> pl.DataFrame:
        """[PIPES] DataFrame: id, node1, node2, length, diameter"""
        return self._pipes_df
    
    @property
    def valves(self) -> pl.DataFrame:
        """[VALVES] DataFrame: id, node1, node2, diameter, valve_type"""
        return self._valves_df
    
    @property
    def pumps(self) -> pl.DataFrame:
        """[PUMPS] DataFrame: id, node1, node2"""
        return self._pumps_df
    
    @property
    def reservoirs(self) -> pl.DataFrame:
        """[RESERVOIRS] DataFrame: id, head, pattern"""
        return self._reservoirs_df
    
    @property
    def tanks(self) -> pl.DataFrame:
        """[TANKS] DataFrame: id, elevation, init_level"""
        return self._tanks_df
    
    @property
    def node_name_list(self) -> List[str]:
        """所有节点 ID 列表"""
        return self._node_list
    
    @property
    def reservoir_name_list(self) -> List[str]:
        """所有水库 ID 列表"""
        return sorted(list(self._reservoir_ids))
    
    @property
    def num_nodes(self) -> int:
        """节点总数"""
        return len(self._node_list)
    
    @property
    def num_links(self) -> int:
        """管道总数（包括 pipes, valves, pumps）"""
        return len(self._pipes_df) + len(self._valves_df) + len(self._pumps_df)
    
    def get_node_coordinates(self, node_id: str) -> Tuple[float, float]:
        """
        获取单个节点坐标
        
        Args:
            node_id: 节点 ID
            
        Returns:
            (x, y) 坐标元组
            
        Raises:
            KeyError: 如果节点不存在
        """
        if node_id not in self._coord_dict:
            raise KeyError(f"Node '{node_id}' not found in coordinates")
        return self._coord_dict[node_id]
    
    def iter_nodes(self) -> Iterator[Tuple[str, float, float]]:
        """
        迭代所有有坐标的节点
        
        Yields:
            (node_id, x, y) 元组
        """
        if HAS_POLARS:
            for row in self._coordinates_df.iter_rows(named=True):
                yield (row['id'], row['x'], row['y'])
        else:
            for _, row in self._coordinates_df.iterrows():
                yield (row['id'], row['x'], row['y'])
    
    def iter_links(self) -> Iterator[Tuple[str, str, str]]:
        """
        迭代所有管道（包括 pipes, valves, pumps）
        
        Yields:
            (link_id, start_node, end_node) 元组
        """
        # Pipes
        if HAS_POLARS:
            for row in self._pipes_df.iter_rows(named=True):
                yield (row['id'], row['node1'], row['node2'])
            for row in self._valves_df.iter_rows(named=True):
                yield (row['id'], row['node1'], row['node2'])
            for row in self._pumps_df.iter_rows(named=True):
                yield (row['id'], row['node1'], row['node2'])
        else:
            for _, row in self._pipes_df.iterrows():
                yield (row['id'], row['node1'], row['node2'])
            for _, row in self._valves_df.iterrows():
                yield (row['id'], row['node1'], row['node2'])
            for _, row in self._pumps_df.iterrows():
                yield (row['id'], row['node1'], row['node2'])
    
    def nodes(self) -> Iterator[Tuple[str, 'NodeProxy']]:
        """
        WNTR 兼容接口: 迭代节点
        
        Yields:
            (node_id, NodeProxy) 元组
        """
        for node_id in self._node_list:
            if node_id in self._coord_dict:
                yield (node_id, NodeProxy(node_id, self._coord_dict[node_id], self))
    
    def links(self) -> Iterator[Tuple[str, 'LinkProxy']]:
        """
        WNTR 兼容接口: 迭代管道
        
        Yields:
            (link_id, LinkProxy) 元组
        """
        for link_id, node1, node2 in self.iter_links():
            yield (link_id, LinkProxy(link_id, node1, node2))
    
    def get_node(self, node_id: str) -> 'NodeProxy':
        """
        WNTR 兼容接口: 获取节点对象
        
        Args:
            node_id: 节点 ID
            
        Returns:
            NodeProxy 对象
        """
        if node_id not in self._coord_dict:
            raise KeyError(f"Node '{node_id}' not found")
        return NodeProxy(node_id, self._coord_dict[node_id], self)


class NodeProxy:
    """节点代理对象，提供 WNTR 兼容接口"""
    
    def __init__(self, node_id: str, coords: Tuple[float, float], parser: InpParser):
        self._id = node_id
        self._coords = coords
        self._parser = parser
    
    @property
    def name(self) -> str:
        return self._id
    
    @property
    def coordinates(self) -> Tuple[float, float]:
        return self._coords
    
    @property
    def node_type(self) -> str:
        if self._id in self._parser._reservoir_ids:
            return 'Reservoir'
        elif self._id in self._parser._tank_ids:
            return 'Tank'
        else:
            return 'Junction'


class LinkProxy:
    """管道代理对象，提供 WNTR 兼容接口"""
    
    def __init__(self, link_id: str, start_node: str, end_node: str):
        self._id = link_id
        self._start = start_node
        self._end = end_node
    
    @property
    def name(self) -> str:
        return self._id
    
    @property
    def start_node_name(self) -> str:
        return self._start
    
    @property
    def end_node_name(self) -> str:
        return self._end


# ============= 便捷函数 =============

def load_inp(inp_path: str, verbose: bool = False) -> InpParser:
    """
    加载 INP 文件的便捷函数
    
    Args:
        inp_path: INP 文件路径
        verbose: 是否打印调试信息
        
    Returns:
        InpParser 实例
    """
    return InpParser(inp_path, verbose=verbose)


# ============= 测试 =============

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python parser.py <inp_file>")
        print("Example: python parser.py ../Example/HF_10w.inp")
        sys.exit(1)
    
    inp_file = sys.argv[1]
    
    print(f"Parsing {inp_file}...")
    t0 = time.perf_counter()
    parser = InpParser(inp_file, verbose=True)
    elapsed = time.perf_counter() - t0
    
    print(f"\n=== Summary ===")
    print(f"Parse time: {elapsed:.2f}s")
    print(f"Nodes: {parser.num_nodes}")
    print(f"Links: {parser.num_links}")
    print(f"Reservoirs: {len(parser.reservoir_name_list)}")
    
    # 测试坐标访问
    if parser.num_nodes > 0:
        first_node = parser.node_name_list[0]
        try:
            x, y = parser.get_node_coordinates(first_node)
            print(f"\nFirst node '{first_node}': ({x:.2f}, {y:.2f})")
        except KeyError:
            print(f"\nFirst node '{first_node}' has no coordinates")
    
    print("\nDone!")
