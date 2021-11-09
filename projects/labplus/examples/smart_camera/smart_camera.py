import json
import time
from machine import UART

class camera():
    IDLE = const(0)
    INIT = const(1)
    RUN_ONESHOT = const(2)
    RUN_CONTINUS = const(3)
    DEINIT = const(4)

    def __init__(self, pin_tx, pin_rx):
        self.uart = UART(1, 115200, tx=pin_tx, rx=pin_tx, timeout=200)
        
    def _call_rpc(self, func, g, l):
        cmd = {'f':func, 'g':g, 'l':l}
        ret = False
        msg = None
        code = None
        # 发送命令
        self.uart.write('@' + json.dumps(cmd))
        # 等待应答,重复五次
        retry = 5
        while retry > 0:
            r = self.uart.readline()
            if r != None:
                break
            retry = retry - 1
        if retry == 0:
            raise OSError('device no response')     # 超时无响应
        # 解析返回结果
        try:
            resp = json.load(r)
            ret = resp['return']
            msg = resp['msg']
            code = resp['code']
        except Exception as e:
            ret = False
            msg = None
            code = None
        return (ret, msg, code)

    def set_mode(self, mode):
        r = self._call_rpc('ai_set_mode(x)', None, {'x':0})
        return r[0]
    
    def start(self, oneshot=False):
        r = self._call_rpc('ai_start(x)', None, {'x':oneshot})
        return r[0]
    
    def stop(self):
        r = self._call_rpc('ai_stop()', None, None)
        return r[0]
    
    def get_result(self):
        r = self._call_rpc('ai_get_result()', None, None)
        if r[0] == True:
            return r[1]
        else:
            return None
    
    def get_status(self):
        r = self._call_rpc('ai_get_state()', None, None)

        if r[0] == True:
            self.state = r[1][0]
            self.ready = r[1][1]
            self.modle = r[1][2]
            self.error = r[1][3]
            return True
        else:
            return False

    def light(self, on_off):
        if on_off == True:
            r = self._call_rpc('led.value(x)', None, {'x':1})
        else:
            r = self._call_rpc('led.value(x)', None, {'x':0})
        return r[0]
    

