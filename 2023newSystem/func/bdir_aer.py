import time
import numpy as np
import threading


class BDIR:
    """ 新需求算法 """

    def __init__(self):
        self.assi_nodes_mux = threading.Lock()
        self.assi_nodes_up = {}
        self.assi_nodes_same = {}
        self.assi_nodes_down = {}
        # self.assi_nodes_state = []
        pass

    def set_free_node(self, node=None, state=None, cost_map=None, direction='up', self_node=None):
        if not node or not state: return

        if self_node != None:
            if self_node[:-7] > node[:-7]:
                direction = 'up'
            elif self_node[:-7] == node[:-7]:
                direction = 'same'
            else:
                direction = 'dowm'
        with self.assi_nodes_mux:
            if direction.lower() == 'up':
                self.assi_nodes_up[node] = [state, cost_map[node]['ori']]
            elif direction.lower() == 'same':
                self.assi_nodes_same[node] = [state, cost_map[node]['ori']]
            else:
                self.assi_nodes_down[node] = [state, cost_map[node]['ori']]
        pass

    def remove_free_node(self, node, direction='up', self_node=None):
        if self_node != None:
            if self_node[:-7] > node[:-7]:
                direction = 'up'
            elif self_node[:-7] == node[:-7]:
                direction = 'same'
            else:
                direction = 'dowm'
        with self.assi_nodes_mux:
            if direction.lower() == 'up':
                if node in self.assi_nodes_up.keys(): self.assi_nodes_up.pop(node)
            elif direction.lower() == 'same':
                if node in self.assi_nodes_same.keys(): self.assi_nodes_same.pop(node)
            else:
                if node in self.assi_nodes_down.keys(): self.assi_nodes_down.pop(node)
        pass

    pass

    def get_max_free_node(self, direction='up', num=3):

        with self.assi_nodes_mux:
            if direction.lower() == 'up': dic = self.assi_nodes_up.copy()
            elif direction.lower() == 'same': dic = self.assi_nodes_same.copy()
            else: dic = self.assi_nodes_down.copy()
        if len(list(dic.items()))<=0: return []
        dict = sorted(dic.items(), key=lambda d: d[1][0] * 2000 + d[1][1], reverse=False)  # 小->大
        # print(dict)
        num = num if num<len(dict) else len(dict)
        res=[dict[i] for i in range(num)]
        return res
        pass


class DATA_Time_Capacity_Monitor:
    def __init__(self, tm_capacity_s=1, alarm_cap=100, aer_accelerate_cap=120):
        self.tm_capacity_s = tm_capacity_s
        self.alarm_cap = alarm_cap
        self.aer_accelerate_cap = aer_accelerate_cap

        self.data_record_mux = threading.Lock()
        self.data_record = np.array([], np.int64)

        self.time_record_mux = threading.Lock()
        self.time_record = np.array([], np.float64)

        # self.id_read = time.time()
        pass

    def record_data(self, data=None):
        # if self.id_read == False: return
        if data: num = np.array([1], dtype=np.int64)
        else: num = np.array([0], dtype=np.int64)
        temp = np.array([time.time()], dtype=np.float64)
        with self.time_record_mux:
            self.time_record = np.concatenate((self.time_record, temp), axis=0)
        with self.data_record_mux:
            self.data_record = np.concatenate((self.data_record, num), axis=0)
        self.update_tm_record()
        # self.id_read = False
        pass

    def is_alarm_cap(self):
        with self.data_record_mux:
            size = self.data_record.sum()
        return (self.alarm_cap - size) / self.alarm_cap

    def is_need_assi_accelerate(self):
        with self.data_record_mux:
            size = self.data_record.sum()
        return (self.aer_accelerate_cap - size) / self.aer_accelerate_cap

    def update_tm_record(self):
        with self.time_record_mux:
            time_record = self.time_record
        with self.data_record_mux:
            data_record = self.data_record
        if len(time_record)<2: return
        tie_out = False
        while (time_record[-1] - time_record[0]) > self.tm_capacity_s:
            time_record = np.delete(time_record, 0, )  # axis=0
            data_record = np.delete(data_record, 0,)  # axis=0
            if time_record.shape[0] == 0: break
            tie_out = True
            pass
        if tie_out:
            with self.time_record_mux:
                self.time_record = time_record
            with self.data_record_mux:
                self.data_record = data_record

        # if size > self.alarm_cap: return True
        # else: return False
        pass

    def clear(self):
        with self.data_record_mux:
            self.data_record[:] = 0
