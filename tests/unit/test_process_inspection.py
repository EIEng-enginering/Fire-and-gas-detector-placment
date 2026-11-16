import unittest
from fgmapping.services.process_inspection import *
class Kernel:
 def __init__(self,handle,error=0,ok=True,code=259):self.handle=handle;self.error=error;self.ok=ok;self.code=code;self.closed=[]
 def open_process(self,pid):return self.handle,self.error
 def exit_code(self,handle):return self.ok,self.code
 def close_handle(self,handle):self.closed.append(handle)
class WindowsProbe(unittest.TestCase):
 def test_live_exited_and_handles_closed(self):
  for code,expected in ((259,ALIVE),(0,DEAD),(1,DEAD)):
   k=Kernel(123,code=code);self.assertEqual(windows_process_state(999,k),expected);self.assertEqual(k.closed,[123])
 def test_access_denied_and_query_failure_never_dead(self):
  for k in (Kernel(None,error=5),Kernel(123,ok=False)):
   self.assertEqual(windows_process_state(999,k),UNKNOWN)
 def test_not_found_and_invalid_pid(self):
  self.assertEqual(windows_process_state(999,Kernel(None,error=87)),DEAD)
  for p in (0,-1,True,'123',2**33):self.assertEqual(windows_process_state(p,Kernel(1)),UNKNOWN)
