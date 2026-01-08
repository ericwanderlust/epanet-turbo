"""
EPANET-Turbo Engine Module
OpenMP 多线程水力仿真引擎封装

Copyright (c) 2026 ES (Serein) - All Rights Reserved
Project UID: EPANET-TURBO-ES-2026-SEREIN93
"""

import os
import sys
import time
import tempfile
import shutil
import ctypes
from ctypes import c_int, c_long, c_double, c_char_p, byref, create_string_buffer, POINTER
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd

# EPANET 2.2 常量
EN_NODECOUNT = 0
EN_LINKCOUNT = 2
EN_DURATION = 0
EN_HYDSTEP = 1
EN_REPORTSTEP = 5
EN_NOSAVE = 0
EN_PRESSURE = 11
EN_FLOW = 8

# DLL 路径 (相对于本模块)
_DLL_DIR = Path(__file__).parent / "dll"
_DLL_PATH = _DLL_DIR / "epanet2_openmp.dll"


def _ansi_bytes(s: str) -> bytes:
    """转换为 ANSI 编码 (Windows 兼容)"""
    try:
        return s.encode('mbcs', errors='ignore')
    except:
        return s.encode(errors='ignore')


def _load_dll() -> ctypes.CDLL:
    """加载 EPANET DLL"""
    if not _DLL_PATH.exists():
        raise FileNotFoundError(f"EPANET DLL not found: {_DLL_PATH}")
    
    # 设置 OpenMP 线程
    threads = max(1, os.cpu_count() or 1)
    os.environ["OMP_NUM_THREADS"] = str(threads)
    os.environ.setdefault("OMP_WAIT_POLICY", "PASSIVE")
    os.environ.setdefault("KMP_BLOCKTIME", "0")
    
    # 添加 DLL 目录
    if hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(str(_DLL_DIR))
        except:
            pass
    
    try:
        return ctypes.WinDLL(str(_DLL_PATH))
    except:
        return ctypes.CDLL(str(_DLL_PATH))


def simulate(
    inp_path: str,
    dll_path: Optional[str] = None,
    omp_threads: str = 'auto'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    运行 EPANET 水力仿真
    
    Args:
        inp_path: INP 文件路径
        dll_path: 自定义 DLL 路径 (可选)
        omp_threads: OpenMP 线程数 ('auto' 或数字)
    
    Returns:
        (pressures, flows): 压力和流量 DataFrame
        - pressures: (时间步 x 节点数), 单位 m
        - flows: (时间步 x 管道数), 单位 m³/s
    
    Example:
        >>> pressures, flows = simulate("network.inp")
        >>> print(pressures.shape)
        (25, 1000)
    """
    # 🔒 许可证验证 (必须通过才能继续)
    from . import telemetry as _t
    _t.require_license()
    
    return run_simulation(inp_path, dll_path, omp_threads)


def run_simulation(
    inp_path: str,
    dll_path: Optional[str] = None,
    omp_threads: str = 'auto'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    运行 EPANET 水力仿真 (详细版)
    
    Copyright (c) 2026 ES (Serein)
    """
    dll = _load_dll() if dll_path is None else ctypes.WinDLL(str(dll_path))
    
    def _sym(*names):
        for nm in names:
            if hasattr(dll, nm):
                return getattr(dll, nm)
        return None
    
    # 绑定 API
    EN_Project = ctypes.c_void_p
    EN_createproject = _sym("EN_createproject", "ENcreateproject")
    
    if not EN_createproject:
        raise RuntimeError("DLL does not have project API")
    
    EN_createproject.argtypes = [POINTER(EN_Project)]
    EN_createproject.restype = c_int
    
    EN_deleteproject = _sym("EN_deleteproject", "ENdeleteproject")
    EN_open = _sym("EN_open", "ENopen")
    EN_open.argtypes = [EN_Project, c_char_p, c_char_p, c_char_p]
    EN_open.restype = c_int
    
    EN_close = _sym("EN_close", "ENclose")
    EN_close.argtypes = [EN_Project]
    EN_close.restype = c_int
    
    EN_openH = _sym("EN_openH", "ENopenH")
    EN_openH.argtypes = [EN_Project]
    EN_openH.restype = c_int
    
    EN_initH = _sym("EN_initH", "ENinitH")
    EN_initH.argtypes = [EN_Project, c_int]
    EN_initH.restype = c_int
    
    EN_runH = _sym("EN_runH", "ENrunH")
    EN_runH.argtypes = [EN_Project, POINTER(c_long)]
    EN_runH.restype = c_int
    
    EN_nextH = _sym("EN_nextH", "ENnextH")
    EN_nextH.argtypes = [EN_Project, POINTER(c_long)]
    EN_nextH.restype = c_int
    
    EN_closeH = _sym("EN_closeH", "ENcloseH")
    EN_closeH.argtypes = [EN_Project]
    EN_closeH.restype = c_int
    
    EN_getcount = _sym("EN_getcount", "ENgetcount")
    EN_getcount.argtypes = [EN_Project, c_int, POINTER(c_int)]
    EN_getcount.restype = c_int
    
    EN_getnodeid = _sym("EN_getnodeid", "ENgetnodeid")
    EN_getnodeid.argtypes = [EN_Project, c_int, c_char_p]
    EN_getnodeid.restype = c_int
    
    EN_getnodevalue = _sym("EN_getnodevalue", "ENgetnodevalue")
    EN_getnodevalue.argtypes = [EN_Project, c_int, c_int, POINTER(c_double)]
    EN_getnodevalue.restype = c_int
    
    EN_getnodevalues = _sym("EN_getnodevalues", "ENgetnodevalues", "EN_GetNodeValues")
    
    # 创建临时目录 (避免中文路径问题)
    temp_dir = tempfile.mkdtemp(prefix="epanet_turbo_")
    temp_inp = os.path.join(temp_dir, "model.inp")
    temp_rpt = os.path.join(temp_dir, "model.rpt")
    temp_out = os.path.join(temp_dir, "model.out")
    
    try:
        shutil.copy(str(inp_path), temp_inp)
        
        # 创建项目
        ph = EN_Project()
        if EN_createproject(byref(ph)) != 0:
            raise RuntimeError("EN_createproject failed")
        
        # 打开模型
        if EN_open(ph, _ansi_bytes(temp_inp), _ansi_bytes(temp_rpt), _ansi_bytes(temp_out)) != 0:
            raise RuntimeError("EN_open failed")
        
        # 获取节点数
        nNodes = c_int()
        EN_getcount(ph, EN_NODECOUNT, byref(nNodes))
        nNodes = nNodes.value
        
        # 获取节点 ID
        node_ids = []
        buf = create_string_buffer(64)
        for i in range(1, nNodes + 1):
            EN_getnodeid(ph, i, buf)
            node_ids.append(buf.value.decode(errors='ignore'))
        
        # 运行水力分析
        if EN_openH(ph) != 0:
            raise RuntimeError("EN_openH failed")
        if EN_initH(ph, EN_NOSAVE) != 0:
            raise RuntimeError("EN_initH failed")
        
        t = c_long()
        tstep = c_long()
        pressures_list = []
        times_list = []
        
        pbuf = (c_double * nNodes)()
        
        while True:
            EN_runH(ph, byref(t))
            
            # 批量获取压力
            if EN_getnodevalues:
                try:
                    EN_getnodevalues(ph, EN_PRESSURE, pbuf)
                except TypeError:
                    EN_getnodevalues(ph, EN_PRESSURE, pbuf, nNodes)
                p_arr = np.frombuffer(pbuf, dtype=np.float64, count=nNodes).astype(np.float32)
            else:
                p_arr = np.zeros(nNodes, dtype=np.float32)
                val = c_double()
                for i in range(1, nNodes + 1):
                    EN_getnodevalue(ph, i, EN_PRESSURE, byref(val))
                    p_arr[i-1] = val.value
            
            pressures_list.append(p_arr.copy())
            times_list.append(t.value)
            
            EN_nextH(ph, byref(tstep))
            if tstep.value <= 0:
                break
        
        EN_closeH(ph)
        EN_close(ph)
        
        # 构建 DataFrame
        pressures = pd.DataFrame(
            np.array(pressures_list),
            index=times_list,
            columns=node_ids
        )
        
        # 流量暂时返回空 DataFrame (可后续扩展)
        flows = pd.DataFrame()
        
        return pressures, flows
        
    finally:
        if EN_deleteproject:
            try:
                EN_deleteproject(ph)
            except:
                pass
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
