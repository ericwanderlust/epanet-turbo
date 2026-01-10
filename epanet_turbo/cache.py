import hashlib
import pickle
import os
from pathlib import Path
from typing import Optional, Any

class ModelCache:
    """
    通用模型缓存类
    
    使用 pickle 序列化任意 Python 对象。
    使用文件大小 + 修改时间作为签名进行极速验证。
    """
    def __init__(self, inp_path: str):
        self.inp_path = Path(inp_path)
        self.cache_path = self.inp_path.with_suffix('.inp.cache')
        
    def _calc_signature(self) -> str:
        """
        计算文件签名用于验证缓存有效性。
        使用 st_size + st_mtime 以达到极致速度 (< 0.1ms)。
        """
        try:
            stat = self.inp_path.stat()
            return f"{stat.st_size}_{stat.st_mtime}"
        except OSError:
            return ""

    def is_valid(self) -> bool:
        if not self.cache_path.exists():
            return False
        return True

    def save(self, data: Any):
        """保存数据到缓存"""
        try:
            with open(self.cache_path, 'wb') as f:
                signature = self._calc_signature()
                pickle.dump(signature, f)
                pickle.dump(data, f)
        except Exception as e:
            print(f"[ModelCache] Failed to save cache: {e}")

    def load(self) -> Optional[Any]:
        """
        从缓存加载数据。
        如果文件不存在或签名不匹配，返回 None。
        """
        if not self.cache_path.exists():
            return None
            
        try:
            with open(self.cache_path, 'rb') as f:
                saved_signature = pickle.load(f)
                current_signature = self._calc_signature()
                
                if saved_signature != current_signature:
                    # print(f"[ModelCache] Stale cache: {saved_signature} != {current_signature}")
                    return None # 缓存过期
                
                data = pickle.load(f)
                return data
        except (EOFError, pickle.UnpicklingError, OSError, ValueError) as e:
            # print(f"[ModelCache] Load error: {e}")
            return None
