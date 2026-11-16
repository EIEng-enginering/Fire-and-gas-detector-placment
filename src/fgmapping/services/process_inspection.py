"""Conservative process liveness for stale-lock recovery; never kills a process.

ALIVE/UNKNOWN never authorise stale-lock cleanup. Native Windows integration
remains pending Windows acceptance; injectable probes allow offline refusal tests.
"""
import os
ALIVE='ALIVE';DEAD='DEAD';UNKNOWN='UNKNOWN'

def windows_process_state(pid,kernel=None):
 if type(pid) is not int or not 0<pid<=0xffffffff:return UNKNOWN
 if kernel is not None:
  # Offline probe contract mirrors Win32 outcomes without loading platform DLLs.
  handle,error=kernel.open_process(pid)
  if not handle:return DEAD if error==87 else UNKNOWN
  try:
   ok,code=kernel.exit_code(handle)
   return UNKNOWN if not ok else ALIVE if code==259 else DEAD
  finally:kernel.close_handle(handle)
 if os.name!='nt':return UNKNOWN
 import ctypes
 from ctypes import wintypes
 dll=ctypes.WinDLL('kernel32',use_last_error=True)
 dll.OpenProcess.argtypes=(wintypes.DWORD,wintypes.BOOL,wintypes.DWORD);dll.OpenProcess.restype=wintypes.HANDLE
 dll.GetExitCodeProcess.argtypes=(wintypes.HANDLE,ctypes.POINTER(wintypes.DWORD));dll.GetExitCodeProcess.restype=wintypes.BOOL
 dll.CloseHandle.argtypes=(wintypes.HANDLE,);dll.CloseHandle.restype=wintypes.BOOL
 handle=dll.OpenProcess(0x1000,False,pid)
 if not handle:return DEAD if ctypes.get_last_error()==87 else UNKNOWN
 try:
  code=wintypes.DWORD()
  if not dll.GetExitCodeProcess(handle,ctypes.byref(code)):return UNKNOWN
  return ALIVE if code.value==259 else DEAD
 finally:dll.CloseHandle(handle)

def process_state(pid):
 if type(pid) is not int or pid<=0:return UNKNOWN
 if os.name=='nt':return windows_process_state(pid)
 try:os.kill(pid,0)
 except ProcessLookupError:return DEAD
 except (PermissionError,OSError):return UNKNOWN
 return ALIVE
