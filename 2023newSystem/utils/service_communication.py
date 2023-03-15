import threading
import numpy as np
import time
import queue
from utils.utils import *
import routing_config as cf

class Node_Communication:
    def __init__(self, name=None, node_cpu=None):
        self.node_cpu = node_cpu
        self.recv_data_buf = queue.Queue(1000)
        self.ready_recv = AAA()  # threading.Lock()  # False:不可接收
        # print('creating {}\'s communication!'.format(name) )
        print('creating {}\'s communication!'.format(name), node_cpu.keys())
        pass

    def send_data(self, id, dat=None):
        if dat is not None and id in self.node_cpu.keys():
            while True:
                try:
                    self.get_recv_state(id)
                    # self.set_recv_state(id)  ## 设置为占用
                    time.sleep(cf.speed_base*1e-5)  # 网络消耗
                    self.node_cpu[id].node_connected_nodes.recv_data_buf.put(dat, timeout=0.1)  #, timeout=0.1
                    self.rset_recv_state(id)  ## 设置为不占用
                    return True
                except:
                    return FileNotFoundError('send fail: {} == {}'.format(id, dat))
                    pass
        return False
        pass

    def recv_data(self):
        self.ready_recv.acquire()  ## Lock=True, timeout=1
        if self.recv_data_buf.qsize()>0:
            dat = self.recv_data_buf.get(timeout=0.1)
        else:
            dat = None
            # self.recv_data_buf = None
        self.ready_recv.release()
        return dat
        pass

    def get_recv_state(self, id):
        return self.node_cpu[id].node_connected_nodes.ready_recv.acquire()  # False:不可接收
        pass

    def set_recv_state(self, id):
        # self.node_cpu[id].node_connected_nodes.ready_recv = False  # False:不可接收
        pass

    def rset_recv_state(self, id):
        self.node_cpu[id].node_connected_nodes.ready_recv.release()
        pass

