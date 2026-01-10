import os
import time
import ctypes
import numpy as np
from ctypes import c_int, c_long, c_double, c_char_p, byref, create_string_buffer, POINTER
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from .streaming import StreamingReporter

# ---- EPANET enums (2.2) ----
EN_NODECOUNT   = 0
EN_LINKCOUNT   = 2
EN_DURATION    = 0
EN_HYDSTEP     = 1
EN_REPORTSTEP  = 5
EN_NOSAVE      = 0
EN_PRESSURE    = 11
EN_FLOW        = 8
EN_STATUS      = 11
EN_CLOSED      = 0
EN_OPEN        = 1

class EppEngine:
    """
    EPANET Engine Wrapper (ctypes based)
    Replaces encrypted engine.py
    """
    def __init__(self, dll_path: Optional[str] = None):
        if dll_path is None:
            # Default to bundled DLL
            dll_path = Path(__file__).parent / "epanet2.dll"
        
        self.dll_path = Path(dll_path).resolve()
        if not self.dll_path.exists():
            raise FileNotFoundError(f"DLL not found: {self.dll_path}")
            
        self._load_dll()
        
    def _load_dll(self):
        if hasattr(os, "add_dll_directory"):
            try: os.add_dll_directory(str(self.dll_path.parent))
            except FileNotFoundError: pass
        try:
            self.ep = ctypes.WinDLL(str(self.dll_path))
        except Exception:
            self.ep = ctypes.CDLL(str(self.dll_path))

        def _sym(*names):
            for nm in names:
                if hasattr(self.ep, nm): return getattr(self.ep, nm)
            return None

        # project API?
        self.EN_createproject = _sym("EN_createproject","ENcreateproject")
        self.has_project_api = self.EN_createproject is not None

        # error handler setup
        self.EN_geterror = _sym("EN_geterror","ENgeterror")
        self.WARN_CODES = set(range(1,11))
        
        if self.EN_geterror:
            self.EN_geterror.argtypes = [c_int, ctypes.c_char_p, c_int]
            self.EN_geterror.restype  = c_int

        # bind base API
        if self.has_project_api:
            self.EN_Project = ctypes.c_void_p
            self.EN_createproject.argtypes=[POINTER(self.EN_Project)]; self.EN_createproject.restype=c_int
            self.EN_deleteproject = _sym("EN_deleteproject","ENdeleteproject")
            if self.EN_deleteproject:
                self.EN_deleteproject.argtypes=[self.EN_Project]; self.EN_deleteproject.restype=c_int

            self.EN_open   = _sym("EN_open","ENopen");   self.EN_open.argtypes  = [self.EN_Project, c_char_p, c_char_p, c_char_p]; self.EN_open.restype  = c_int
            self.EN_close  = _sym("EN_close","ENclose"); self.EN_close.argtypes = [self.EN_Project];                                 self.EN_close.restype = c_int
            self.EN_openH  = _sym("EN_openH","ENopenH"); self.EN_openH.argtypes = [self.EN_Project];                                 self.EN_openH.restype = c_int
            self.EN_initH  = _sym("EN_initH","ENinitH"); self.EN_initH.argtypes = [self.EN_Project, c_int];                          self.EN_initH.restype = c_int
            self.EN_runH   = _sym("EN_runH","ENrunH");   self.EN_runH.argtypes  = [self.EN_Project, POINTER(c_long)];         self.EN_runH.restype  = c_int
            self.EN_nextH  = _sym("EN_nextH","ENnextH"); self.EN_nextH.argtypes = [self.EN_Project, POINTER(c_long)];         self.EN_nextH.restype = c_int
            self.EN_closeH = _sym("EN_closeH","ENcloseH"); self.EN_closeH.argtypes=[self.EN_Project];                                self.EN_closeH.restype= c_int
            self.EN_getcount     = _sym("EN_getcount","ENgetcount");     self.EN_getcount.argtypes     = [self.EN_Project, c_int, POINTER(c_int)]; self.EN_getcount.restype=c_int
            self.EN_getnodeid    = _sym("EN_getnodeid","ENgetnodeid");   self.EN_getnodeid.argtypes    = [self.EN_Project, c_int, ctypes.c_char_p];       self.EN_getnodeid.restype=c_int
            self.EN_getlinkid    = _sym("EN_getlinkid","ENgetlinkid");   self.EN_getlinkid.argtypes    = [self.EN_Project, c_int, ctypes.c_char_p];       self.EN_getlinkid.restype=c_int
            self.EN_getnodevalue = _sym("EN_getnodevalue","ENgetnodevalue"); self.EN_getnodevalue.argtypes=[self.EN_Project,c_int,c_int,POINTER(c_double)]; self.EN_getnodevalue.restype=c_int
            self.EN_getlinkvalue = _sym("EN_getlinkvalue","ENgetlinkvalue"); self.EN_getlinkvalue.argtypes=[self.EN_Project,c_int,c_int,POINTER(c_double)]; self.EN_getlinkvalue.restype=c_int
            self.EN_gettimeparam = _sym("EN_gettimeparam","ENgettimeparam"); self.EN_gettimeparam.argtypes=[self.EN_Project,c_int,POINTER(c_long)]; self.EN_gettimeparam.restype=c_int
        else:
            self.EN_open   = _sym("EN_open","ENopen");   self.EN_open.argtypes  = [c_char_p, c_char_p, c_char_p]; self.EN_open.restype  = c_int
            self.EN_close  = _sym("EN_close","ENclose"); self.EN_close.argtypes = [];                              self.EN_close.restype = c_int
            self.EN_openH  = _sym("EN_openH","ENopenH"); self.EN_openH.argtypes = [];                              self.EN_openH.restype = c_int
            self.EN_initH  = _sym("EN_initH","ENinitH"); self.EN_initH.argtypes = [c_int];                         self.EN_initH.restype = c_int
            self.EN_runH   = _sym("EN_runH","ENrunH");   self.EN_runH.argtypes  = [POINTER(c_long)];        self.EN_runH.restype  = c_int
            self.EN_nextH  = _sym("EN_nextH","ENnextH"); self.EN_nextH.argtypes = [POINTER(c_long)];        self.EN_nextH.restype = c_int
            self.EN_closeH = _sym("EN_closeH","ENcloseH"); self.EN_closeH.argtypes=[];                             self.EN_closeH.restype= c_int
            self.EN_getcount     = _sym("EN_getcount","ENgetcount");     self.EN_getcount.argtypes     = [c_int, POINTER(c_int)]; self.EN_getcount.restype=c_int
            self.EN_getnodeid    = _sym("EN_getnodeid","ENgetnodeid");   self.EN_getnodeid.argtypes    = [c_int, ctypes.c_char_p];       self.EN_getnodeid.restype=c_int
            self.EN_getlinkid    = _sym("EN_getlinkid","ENgetlinkid");   self.EN_getlinkid.argtypes    = [c_int, ctypes.c_char_p];       self.EN_getlinkid.restype=c_int
            self.EN_getnodevalue = _sym("EN_getnodevalue","ENgetnodevalue"); self.EN_getnodevalue.argtypes=[c_int,c_int,POINTER(c_double)]; self.EN_getnodevalue.restype=c_int
            self.EN_getlinkvalue = _sym("EN_getlinkvalue","ENgetlinkvalue"); self.EN_getlinkvalue.argtypes=[c_int,c_int,POINTER(c_double)]; self.EN_getlinkvalue.restype=c_int
            self.EN_gettimeparam = _sym("EN_gettimeparam","ENgettimeparam"); self.EN_gettimeparam.argtypes=[c_int,POINTER(c_long)]; self.EN_gettimeparam.restype=c_int

        # Bulk API
        self.GetNodeVals = _sym("EN_getnodevalues","ENgetnodevalues","EN_GetNodeValues")
        self.GetLinkVals = _sym("EN_getlinkvalues","ENgetlinkvalues","EN_GetLinkValues")
        if self.GetNodeVals:
            try: self.GetNodeVals.restype = c_int
            except: pass
        if self.GetLinkVals:
            try: self.GetLinkVals.restype = c_int
            except: pass

    def _err(self, ret, where=""):
        if ret == 0: return
        if ret in self.WARN_CODES:
            print(f"[WARN] EPANET warning {ret} at {where}")
            return
        buf = create_string_buffer(256)
        msg = ""
        if self.EN_geterror:
            try: self.EN_geterror(ret, buf, 255); msg=buf.value.decode(errors="ignore")
            except: pass
        raise RuntimeError(f"EPANET error {ret} at {where}: {msg}")

    def _ansi_bytes(self, s: str) -> bytes:
        try:    return s.encode("mbcs", errors="ignore")
        except: return s.encode(errors="ignore")

    def run_streaming(self, inp_path: str, output_path: str):
        """
        Run simulation with streaming output.
        """
        inp_path = str(Path(inp_path).resolve())
        # output_path is prefix name or full path. StreamingReporter expects full path .out
        # But user might pass a directory or a file prefix.
        # Let's assume output_path is the TARGET .out file path for now.
        
        # Temp files
        import tempfile
        rpt_file = os.path.join(tempfile.gettempdir(), f"epanet_{os.getpid()}.rpt")
        out_file = os.path.join(tempfile.gettempdir(), f"epanet_{os.getpid()}.bin")
        
        ph = ctypes.c_void_p() if self.has_project_api else None
        
        try:
            if self.has_project_api:
                self._err(self.EN_createproject(byref(ph)), "EN_createproject")
                self._err(self.EN_open(ph, self._ansi_bytes(inp_path), self._ansi_bytes(rpt_file), self._ansi_bytes(out_file)), "EN_open")
            else:
                self._err(self.EN_open(self._ansi_bytes(inp_path), self._ansi_bytes(rpt_file), self._ansi_bytes(out_file)), "EN_open")

            # Get Counts
            n_nodes = c_int(0); n_links = c_int(0)
            if self.has_project_api:
                self._err(self.EN_getcount(ph, EN_NODECOUNT, byref(n_nodes)))
                self._err(self.EN_getcount(ph, EN_LINKCOUNT, byref(n_links)))
            else:
                self._err(self.EN_getcount(EN_NODECOUNT, byref(n_nodes)))
                self._err(self.EN_getcount(EN_LINKCOUNT, byref(n_links)))
            
            nN, nL = n_nodes.value, n_links.value
            
            # Get IDs
            node_ids = []
            link_ids = []
            buf = create_string_buffer(64)
            for i in range(1, nN+1):
                if self.has_project_api: self._err(self.EN_getnodeid(ph, i, buf))
                else:                    self._err(self.EN_getnodeid(i, buf))
                node_ids.append(buf.value.decode(errors="ignore"))
                
            for k in range(1, nL+1):
                if self.has_project_api: self._err(self.EN_getlinkid(ph, k, buf))
                else:                    self._err(self.EN_getlinkid(k, buf))
                link_ids.append(buf.value.decode(errors="ignore"))

            # Time parameters
            dur = c_long(0); hydstep = c_long(0); rptstep = c_long(0)
            if self.has_project_api:
                self._err(self.EN_gettimeparam(ph, EN_DURATION, byref(dur)))
                self._err(self.EN_gettimeparam(ph, EN_HYDSTEP, byref(hydstep)))
                self._err(self.EN_gettimeparam(ph, EN_REPORTSTEP, byref(rptstep)))
            else:
                self._err(self.EN_gettimeparam(EN_DURATION, byref(dur)))
                self._err(self.EN_gettimeparam(EN_HYDSTEP, byref(hydstep)))
                self._err(self.EN_gettimeparam(EN_REPORTSTEP, byref(rptstep)))

            _hyd = max(1, int(hydstep.value))
            _rpt = int(rptstep.value)
            sample_every = 1 if _rpt <= 0 else max(1, _rpt // _hyd)

            # Initialize Streaming Reporter
            with StreamingReporter(output_path, node_ids, link_ids, _rpt) as reporter:
                # Buffers
                pbuf = (c_double * nN)()
                fbuf = (c_double * nL)()
                
                # Run Hydraulics
                t = c_long(0); tstep = c_long(0)
                if self.has_project_api:
                    self._err(self.EN_openH(ph)); self._err(self.EN_initH(ph, EN_NOSAVE))
                else:
                    self._err(self.EN_openH()); self._err(self.EN_initH(EN_NOSAVE))
                
                step_index = 0
                while True:
                    if self.has_project_api: self._err(self.EN_runH(ph, byref(t)))
                    else:                    self._err(self.EN_runH(byref(t)))
                    
                    need_sample = (step_index % sample_every == 0) or (t.value >= dur.value)
                    
                    if need_sample:
                        # Fetch Data
                        # Use bulk API if available
                        got_nodes = False
                        if self.GetNodeVals:
                            try:
                                if self.has_project_api: res = self.GetNodeVals(ph, EN_PRESSURE, pbuf, nN)
                                else:                    res = self.GetNodeVals(EN_PRESSURE, pbuf, nN)
                                if res == 0: got_nodes = True
                            except: pass
                        
                        if not got_nodes:
                            dv = c_double(0)
                            for i in range(1, nN+1):
                                if self.has_project_api: self.EN_getnodevalue(ph, i, EN_PRESSURE, byref(dv))
                                else:                    self.EN_getnodevalue(i, EN_PRESSURE, byref(dv))
                                pbuf[i-1] = dv.value

                        got_links = False
                        if self.GetLinkVals:
                            try:
                                if self.has_project_api: res = self.GetLinkVals(ph, EN_FLOW, fbuf, nL)
                                else:                    res = self.GetLinkVals(EN_FLOW, fbuf, nL)
                                if res == 0: got_links = True
                            except: pass
                            
                        if not got_links:
                            dv = c_double(0)
                            for k in range(1, nL+1):
                                if self.has_project_api: self.EN_getlinkvalue(ph, k, EN_FLOW, byref(dv))
                                else:                    self.EN_getlinkvalue(k, EN_FLOW, byref(dv))
                                fbuf[k-1] = dv.value

                        # Convert to numpy and write
                        p_arr = np.frombuffer(pbuf, dtype=np.float64, count=nN)
                        f_arr = np.frombuffer(fbuf, dtype=np.float64, count=nL)
                        
                        reporter.write_step(t.value, p_arr, f_arr)

                    if self.has_project_api: self._err(self.EN_nextH(ph, byref(tstep)))
                    else:                    self._err(self.EN_nextH(byref(tstep)))
                    
                    step_index += 1
                    if tstep.value <= 0:
                        break

                if self.has_project_api:
                    self._err(self.EN_closeH(ph))
                    self._err(self.EN_close(ph))
                else:
                    self._err(self.EN_closeH())
                    self._err(self.EN_close())
                    
        finally:
            if self.has_project_api and ph:
                if self.EN_deleteproject: self.EN_deleteproject(ph)
            try:
                if os.path.exists(rpt_file): os.remove(rpt_file)
                if os.path.exists(out_file): os.remove(out_file)
            except: pass
