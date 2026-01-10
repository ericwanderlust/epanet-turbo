from pathlib import Path
from .parser import InpParser
from .engine import EppEngine, EN_NOSAVE, EN_LINKCOUNT, EN_NODECOUNT

class ModelContext:
    """
    Model Context Wrapper (M3-2 Specification)
    Replaces encrypted context.py with full interactive support.
    """
    def __init__(self, inp_path: str):
        self.inp_path = str(Path(inp_path).resolve())
        if not Path(self.inp_path).exists():
            raise FileNotFoundError(self.inp_path)
            
        # Use InpParser to get basic info
        self.parser = InpParser(self.inp_path)
        self.num_nodes = self.parser.num_nodes
        self.num_links = self.parser.num_links
        
        self.engine = EppEngine()
        self.ph = None # Project Handle (if supported)
        
        # Open Project
        # Note: EppEngine handles EN_open internally mostly, or we call it.
        # But verify script calls open_hydraulics manually.
        # usually ModelContext opens project in __enter__.
        self.is_open = False

    def __enter__(self):
        # We need to initialize the engine with the file
        # EppEngine EN_open requires rpt/bin files.
        import tempfile
        self.rpt_file = str(Path(tempfile.gettempdir()) / f"epanet_{id(self)}.rpt")
        self.bin_file = str(Path(tempfile.gettempdir()) / f"epanet_{id(self)}.bin")
        
        if self.engine.has_project_api:
             # Manually creating PH pointer just for this test context
             import ctypes
             self.ph = ctypes.c_void_p()
             self.engine._err(self.engine.EN_createproject(ctypes.byref(self.ph)))
             
             self.engine._err(self.engine.EN_open(
                self.ph,
                self.engine._ansi_bytes(self.inp_path),
                self.engine._ansi_bytes(self.rpt_file),
                self.engine._ansi_bytes(self.bin_file)
            ))
        else:
            self.engine._err(self.engine.EN_open(
                self.engine._ansi_bytes(self.inp_path),
                self.engine._ansi_bytes(self.rpt_file),
                self.engine._ansi_bytes(self.bin_file)
            ))
        self.is_open = True
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_open:
            if self.engine.has_project_api and self.ph:
                 self.engine.EN_close(self.ph)
                 self.engine.EN_deleteproject(self.ph)
            else:
                 self.engine.EN_close()
            self.is_open = False
            
    def run_scenario_streaming(self, output_dir: str, reset: bool = False) -> str:
        # Re-implemented to use internal engine logic if possible, 
        # or just delegate if engine has run_streaming
        return self.engine.run_streaming(self.inp_path, output_dir)

    def open_hydraulics(self):
        if self.engine.has_project_api and self.ph:
            self.engine._err(self.engine.EN_openH(self.ph))
        else:
            self.engine._err(self.engine.EN_openH())

    def init_hydraulics(self, save_flag):
        if self.engine.has_project_api and self.ph:
            self.engine._err(self.engine.EN_initH(self.ph, save_flag))
        else:
            self.engine._err(self.engine.EN_initH(save_flag))

    def run_hydraulics(self):
        import ctypes
        t = ctypes.c_long()
        if self.engine.has_project_api and self.ph:
            self.engine._err(self.engine.EN_runH(self.ph, ctypes.byref(t)))
        else:
            self.engine._err(self.engine.EN_runH(ctypes.byref(t)))
        return t.value

    def next_hydraulics(self):
        import ctypes
        tstep = ctypes.c_long()
        if self.engine.has_project_api and self.ph:
             self.engine._err(self.engine.EN_nextH(self.ph, ctypes.byref(tstep)))
        else:
             self.engine._err(self.engine.EN_nextH(ctypes.byref(tstep)))
        return tstep.value

    def close_hydraulics(self):
        if self.engine.has_project_api and self.ph:
            self.engine._err(self.engine.EN_closeH(self.ph))
        else:
            self.engine._err(self.engine.EN_closeH())
        
    def _get_func(self, name):
        # Helper to find function in DLL
        candidates = [name, name.replace("_", "")]
        for n in candidates:
            if hasattr(self.engine.ep, n):
                 return getattr(self.engine.ep, n)
        return None

    def get_link_index(self, link_id):
        func = self._get_func("EN_getlinkindex")
        if func:
            import ctypes
            idx = ctypes.c_int()
            if self.engine.has_project_api and self.ph:
                 self.engine._err(func(self.ph, self.engine._ansi_bytes(link_id), ctypes.byref(idx)))
            else:
                 self.engine._err(func(self.engine._ansi_bytes(link_id), ctypes.byref(idx)))
            return idx.value
        else:
            raise NotImplementedError("EN_getlinkindex not found")

    def set_link_value(self, index, param, value):
        func = self._get_func("EN_setlinkvalue")
        import ctypes
        if self.engine.has_project_api and self.ph:
            self.engine._err(func(self.ph, ctypes.c_int(index), ctypes.c_int(param), ctypes.c_double(value)))
        else:
            self.engine._err(func(ctypes.c_int(index), ctypes.c_int(param), ctypes.c_double(value)))

    def get_link_value(self, index, param):
        import ctypes
        val = ctypes.c_double()
        if self.engine.has_project_api and self.ph:
             self.engine._err(self.engine.EN_getlinkvalue(self.ph, ctypes.c_int(index), ctypes.c_int(param), ctypes.byref(val)))
        else:
             self.engine._err(self.engine.EN_getlinkvalue(ctypes.c_int(index), ctypes.c_int(param), ctypes.byref(val)))
        return val.value
        
    def enable_streaming(self, out_prefix):
         if not str(out_prefix).lower().endswith('.out'):
             self._streaming_prefix = f"{out_prefix}.out"
         else:
             self._streaming_prefix = out_prefix
         
    def solve(self):
         if hasattr(self, '_streaming_prefix') and self._streaming_prefix:
             # Use engine's streaming runner
             # Note: run_streaming takes full path usually, or prefix?
             # engine.py Step 491: run_streaming(inp, output_path)
             # context.run_scenario_streaming implementation calculates .out path.
             # verify_protocol_v2 passes "test_protocol_v2" as prefix.
             # engine.run_streaming uses it as 'output_path' which StreamingReporter uses to init sidecars.
             # So passing prefix directly is fine if StreamingReporter handles it.
             # StreamingReporter(output_path, ...)
             # It usually appends .nodes.arrow etc to output_path.
             self.engine.run_streaming(self.inp_path, self._streaming_prefix)
         else:
             # Just run simple simulation
             self.open_hydraulics()
             self.init_hydraulics(EN_NOSAVE)
             while True:
                 t = self.run_hydraulics()
                 step = self.next_hydraulics()
                 if step <= 0: break
             self.close_hydraulics()

def simulate(inp_file):
    with ModelContext(inp_file) as model:
        model.solve()
