import math
from time import sleep

from utils.service_communication import *
from utils.utils import *

from utils.buildThread import ThreadPool as ThreadPool
from routing_optism import routing_node_choice_optism as mat_optism
from utils import log_printFormat as logprint, visualization as Vishow

from func.routing_node_mission import Routing_Node_CPU
from func.bdir_aer import BDIR, DATA_Time_Capacity_Monitor





class Routing_Node_CPU_New(Routing_Node_CPU):
    def __init__(self, id, num_class=5, generate_rate=0.1, recv_rate=0.1, send_rate=0.1, processing_rate=0.1,
                 max_data_size=100, send_buf=500, gene_buf=500, recv_buf=500,
                 isMDSR=True, isODAS=False, balance=True, alarm_buf_rate=0.5, ODAS_rate=0.5,
                 build_Thread: ThreadPool = None, cloud_name='',
                 isIoT=False, logPath='', generate_total=0, nodes_map=None,
                 tm_capacity_s=1, alarm_cap=10000, is_Bdir=True, is_AER=False, package_size:int=6,
                 assi_nodes_num:int=3, small_package_size:int=3, max_pack_time_s=1, aer_accelerate_cap=200,
                 **kwargs):

        super(Routing_Node_CPU_New, self).__init__(id, num_class, generate_rate, recv_rate, send_rate,
                                                   processing_rate, max_data_size, send_buf, gene_buf, recv_buf,
                                                   isMDSR, isODAS, balance, alarm_buf_rate, ODAS_rate, build_Thread,
                                                   cloud_name,
                                                   isIoT, logPath, generate_total, nodes_map, **kwargs)

        self._thread_generate_data = None
        self._thread_send_data = None
        self._thread_recv_data = None
        self._thread_processing_data = None

        self.generate_total = generate_total
        self.generate_buffer = queue.Queue(gene_buf)  ##[]#
        self.recv_buffer = queue.Queue(recv_buf)  ##[] #
        self.send_buffer = queue.Queue(send_buf)  ##[]

        self.node_id = str(id)
        self.data_category_num = num_class

        self.generate_rate = generate_rate if generate_rate != 0 else 0.1
        self.recv_rate = recv_rate if recv_rate != 0 else 0.1
        self.send_rate = send_rate if send_rate != 0 else 0.1
        self.processing_rate = processing_rate if processing_rate != 0 else 0.1

        self.max_data_size = max_data_size if max_data_size != 0 else 1
        self.generate_buf_size = gene_buf if gene_buf != 0 else max_data_size
        self.recv_buf_size = recv_buf if recv_buf != 0 else max_data_size
        self.send_buf_size = send_buf if send_buf != 0 else max_data_size

        self.alarm_buf_rate = alarm_buf_rate

        self.node_connected_nodes = None

        self.mux_lock_connect_cost = threading.Lock()
        self.node_connect_cost_dict = None
        self.nodes_map = nodes_map

        self.__cloud_data_class = []
        self.recieve_a_same_sign = False

        self.build_Thread = build_Thread

        self.all_thread_run_mux = threading.Lock()
        self.all_thread_run_sta = True

        self.isIoT = isIoT
        self.cloud_name = cloud_name

        self.data_processing_size_lock = threading.Lock()
        self.data_processing_size_new = 0  ## 新数据的量（包括自身数据和服务节点的通信数据，但不包含旧数据）
        self.data_processing_size_old = 0  ## 旧数据（只包含处理接收到的（负载均衡转发的）旧数据）
        self.data_processing_size_ODAS = 0  ## ODAS优化之后，减少的数据量

        self.isMDSR = isMDSR  ##
        self.isODAS = isODAS
        self.isbalance = balance  ## 负载均衡开关
        self.ODAS_rate = ODAS_rate

        self.is_AER = is_AER
        self.package_size = package_size  # 数据打包尺寸， -1为自动计算
        self.small_package_size = small_package_size  # 数据打包尺寸， -1为自动计算
        self.assi_nodes_num = assi_nodes_num
        self.max_pack_time_s = max_pack_time_s*processing_rate
        self.unpack_recv_buffer = queue.Queue(recv_buf*3*max(package_size, small_package_size))

        self.ask_bdir = time.time()

        self.data_monitor_recv = DATA_Time_Capacity_Monitor(tm_capacity_s=tm_capacity_s*processing_rate, alarm_cap=alarm_cap, aer_accelerate_cap=aer_accelerate_cap)
        if is_Bdir or is_AER: self.bdir = BDIR()
        else: self.bdir = None


        # self.generate_data_format = {'did': self.node_id, 'class': '0', 'param': None, 'type': 'data',
        #                              'target': None, 'time': 0}

        self.log = logPath + self.node_id + '_node_log.csv'
        logprint.node_record_alldatawriteheader(self.log)
        headers = ['direction', 'start time', 'end time', 'pack time', 'pack num', 'pack chars', 'assistant num']
        self.bdir_log = logPath + self.node_id + '_node_Bdir_log.csv'
        logprint.node_record_alldatawriteheader(self.bdir_log, headers)


    def get_connected_nodes(self, diretion_s:[]=None):
        with self.mux_lock_connect_cost:
            cost_dict = self.node_connect_cost_dict
        self_name = self.node_id
        res = []
        for diretion in diretion_s:
            for name in cost_dict.keys():
                if diretion.lower()=='up':
                    if int(name[:-7]) + 1 == int(self_name[:-7]):  res.append(name)
                elif diretion.lower()=='dowm':
                    if int(name[:-7]) - 1 == int(self_name[:-7]):  res.append(name)
                elif diretion.lower()=='same':
                    if int(name[:-7]) == int(self_name[:-7]):  res.append(name)
        # if len(res)==0: return None
        return res

        pass

    def bdir_record_data(self, data):
        if not self.bdir: return False
        if not data: return False
        bdir = data['param']
        try:
            if bdir['type'] == 'bdir-query' or bdir['type'] == 'bdir-back': data = None
        except:
            pass
        self.data_monitor_recv.record_data(data)
        return True

    def bdir_ask_alarm_state(self, data=None):  # 此处需要允许同层连接
        ''' 不能高频率的询问 '''
        if time.time()-self.ask_bdir < self.processing_rate*5: return False
        if self.data_monitor_recv.is_alarm_cap()>0: return False
        self.ask_bdir = time.time()
        broadcast = self.generate_data_format()
        broadcast['type'] = 'bdir-query'

        assistant_nodes = self.get_connected_nodes(diretion_s=['up'])
        if self.is_AER and self.data_monitor_recv.is_need_assi_accelerate()<0:
            assistant_nodes += self.get_connected_nodes(diretion_s=['same'])
        # print('bdir_ask_alarm_state:', self.node_id, assistant_nodes)
        for node in assistant_nodes:
            broadcast['target'] = node
            self.node_send_data_(name_id=node, dat=broadcast)
        return True
        pass

    def bdir_feedback_state(self, query):
        """ 回答bdir的带宽咨询 """
        if not self.bdir: return False
        # data = self.decode_data_for_original_category(query)
        data = query['param']
        # print('bdir_feedback_state:', data)
        try:
            if data['type'] != 'bdir-query': return False  # 非此项信息
        except: return False
        # if self.data_monitor_recv.is_alarm_cap() <= 0: return True  # 带宽不足，拒绝回复
        ori_name = data['did']
        state = self.data_monitor_recv.is_alarm_cap()
        feed = self.generate_data_format()
        feed['type'] = 'bdir-back'
        feed['param'] = state
        feed['target'] = ori_name
        self.node_send_data_(name_id=ori_name, dat=feed)
        # print('bdir_feedback_state 2', self.node_id, ori_name, feed)
        return True
        pass

    def bdir_process_feedback(self, feedback):
        """ 其他节点反馈带宽信息后，将可用节点记录为辅助节点 """
        if not self.bdir: return False
        # data = self.decode_data_for_original_category(feedback)
        data = feedback['param']
        # print('bdir_process_feedback:', self.node_id, data)
        try:
            if data['type'] != 'bdir-back': return False
        except: return False
        ori_name = data['did']
        ori_tar = data['target']
        state = data['param']
        if ori_tar != self.node_id: return True  # 信息指向是自己
        if state > 0:
            with self.mux_lock_connect_cost:
                cost_dict = self.node_connect_cost_dict
            self.bdir.set_free_node(ori_name, state, cost_dict, self_node=self.node_id)
        else: self.bdir.remove_free_node(ori_name, self_node=self.node_id)
        return True
        pass

    def bdir_change_buffer(self):
        if self.unpack_recv_buffer.qsize()>0: return self.unpack_recv_buffer
        else: return self.recv_buffer

    def bdir_package_recv_iot_data(self):
        """ 将接收的数据打包，遇到已有数据包，则继续叠加包。非未处理数据则不处理，只打包未处理数据 """
        if not self.bdir: return False
        free_nodes = []
        if self.is_AER and  self.data_monitor_recv.is_need_assi_accelerate()<0:
            free_nodes += self.bdir.get_max_free_node(direction='same', num=self.assi_nodes_num) #协同打包
        BDIR_num = len(free_nodes)  # 用于记录 ARE 算法，确定前几个节点是协同打包节点，包大小限制
        if self.data_monitor_recv.is_alarm_cap()<0:
            free_nodes += self.bdir.get_max_free_node(direction='up', num=1)
        start_tm0 = time.time()
        pack_num, pack_cap, assi_num = 0, 0, []
        for idx, free_node_cost in enumerate(free_nodes):

            start_tm = time .time()
            free_node = free_node_cost[0]
            cap = free_node_cost[1][0]
            pack = {}
            if idx < BDIR_num: package_size = self.small_package_size
            else:  package_size = self.package_size
            if package_size<0: num = self.recv_buf_size*0.5*cap ## 动态调节速率
            else: num = package_size  # 固定速率
            i = 0
            while i < num:
                recv_buffer = self.bdir_change_buffer()
                if recv_buffer.qsize() <= 0: break
                data = recv_buffer.get(timeout=0.1)
                ''' 只有AER打开时，才会出现这种情况 '''
                try:
                    data_bdir = data['param']
                    if data_bdir['type'] == 'bdir-pack':
                        packed = data_bdir['param']
                        for cate in packed:
                            if cate not in pack.keys(): pack[cate] = packed[cate]  ## 每类数据独立打包
                            else: pack[cate] += packed[cate]
                        pack_cap += len(str(packed))
                        pack_num += 1
                        time.sleep(self.processing_rate*0.0001)  # 打包消耗
                        i += 1
                        continue
                except:
                    # print(self.node_id, 'unpack error!', data)
                    pass

                self.data_processing_size_add(data)  ## 数据处理量叠加
                # print('processing:[over recv]', self.node_id, data)
                # data = data['param']
                da = self.decode_data_for_original_category(data)
                cate = da['class']
                if da['type'] == 'data':  ## 只有未处理数据才打包
                    if cate not in pack.keys(): pack[cate]=[data]  ## 每类数据独立打包
                    else: pack[cate].append(data)
                    pack_cap += len(str(data))
                    pack_num += 1
                    time.sleep(self.processing_rate*0.0001)  # 打包消耗
                    i += 1
                else: self.unpack_recv_buffer.put(data)
                if time.time()-start_tm > self.max_pack_time_s:
                    print('bdir_package_recv_iot_data:',  self.node_id, 'package timeout!', f'target:{free_node} packed:{pack_num}', flush=True)
                    break  # 打包时间限制
                if time.time() - start_tm0 > (self.assi_nodes_num) * self.max_pack_time_s: break # 内存都是服务消息而非未处理数据--保护

            if len(list(pack.keys()))>0:
                format_data = self.generate_data_format()
                format_data['param'] = pack
                format_data['type'] = 'bdir-pack'
                self.node_send_data_(name_id=free_node, dat=format_data)
                assi_num += [free_node]
                print('\nbdir_package_recv_iot_data:', f'{self.node_id}-->{free_node}', f'capacity:{pack_cap}  pack:{i}/{num}   category:',
                      list(pack.keys()), flush=True)
            else:
                # print('bdir_package_recv_iot_data:',  self.node_id, 'package no ready!')
                pass
            self.node_processing_func_1_res_buff_vishow()
            if time.time()-start_tm0 > (self.assi_nodes_num)*self.max_pack_time_s: break
        if len(assi_num)>0:
            writedata = {'direction': 'send', 'start time':start_tm0, 'end time': time.time(), 'pack time':time.time()-start_tm0,
                         'pack num':pack_num, 'pack chars': pack_cap, 'assistant num':assi_num}
            logprint.node_record_alldata(self.bdir_log, writedata)
            # print('bdir_package_recv_iot_data：', writedata)
        return True
        pass

    def bdir_unpack_recv_package(self, data):
        ''' 数据包拆解，应在接收线程内调用 '''
        pack = queue.Queue()
        if self.unpack_recv_buffer.qsize() > (self.recv_buf_size * 2 * max(self.package_size, self.small_package_size)): return pack
        if not self.bdir: return pack
        data_format = {'id': data['id'], 'param': [], 'time': data['time']}
        ori_node = data['id']
        # bdir_data = self.decode_data_for_original_category(data)
        data = data['param']  # 提取发送的数据

        # if 'type' in bdir_data.keys() and 'bdir-pack' in bdir_data['type']: print('bdir_unpack_recv_package 1:', self.node_id, bdir_data)
        try:
            if data['type'] != 'bdir-pack': return pack
        except:
            # if 'type' in data.keys(): print('bdir_unpack_recv_package 2:', self.node_id, data.keys(), data)
            return pack
        # print('bdir_unpack_recv_package:', f'{self.node_id} <-- {ori_node}', data.keys(), data, flush=True)

        data = data['param']  ## 定位数据包
        start_tm0 = time.time()
        pack_num, pack_cap = 0, 0
        for cate in data.keys():
            cate_data = data[cate]   # 内部是[]
            for para in cate_data:
                data_format['param'] = para
                pack.put(data_format.copy())  ## 拆解放入接收内存中，等待处理
                pack_num += 1
                pack_cap += len(str(para))
                pass
            time.sleep(self.recv_rate*1e-5)
        writedata = {'direction': 'recv', 'start time': start_tm0, 'end time': time.time(),
                     'pack time': time.time() - start_tm0,
                     'pack num': pack_num, 'pack chars': pack_cap, 'assistant num': ori_node}
        logprint.node_record_alldata(self.bdir_log, writedata)
        print('bdir_unpack_recv_package:', f'{self.node_id} <-- {ori_node}', f'capacity:{pack_cap}  num={pack_num}', flush=True)
        for i in range(pack.qsize()):
            d = pack.get(timeout=0.00001)
            self.unpack_recv_buffer.put(d, timeout=0.0001)
        return pack
        pass


    def massage_processing(self, recv_data:{}):

        if self.bdir_feedback_state(recv_data): return True  ## 反馈带宽数据，不进入缓存
        if self.bdir_process_feedback(recv_data): return True
        # if self.bdir_unpack_recv_package(recv_data): return True  # 及时解压打包数据，分步存入缓存
        return False


    def node_recv_data_(self):
        recv_data = self.node_connected_nodes.recv_data()
        recv_data = str2dict(recv_data)
        if recv_data is not None:  ## 模拟有数据发送到缓存区
            self.data_processing_size_add(recv_data)  ## 数据处理量叠加
            size = 1  ## len(str(recv_data)) 数据格式： str {id: [data]}
            recv_data = str2dict(recv_data)  ## 数据格式：{id: [data]}

            # bdir_data = self.decode_data_for_original_category(recv_data)
            # sta = False
            # if 'type' in bdir_data.keys() and 'bdir-pack' in bdir_data['type']:
            #     print('bdir_unpack_recv_package 1:', self.node_id, bdir_data)
            #     sta = True
            # print( 'node_recv_data_:', self.node_id, bdir_data)

            if self.node_report_on_self(ori_dat=recv_data):  # 成本变更
                # print('recv:[report_self]', self.node_id, '<--', '：', recv_data)
                return True  ## 数据已处理，不再存入缓存
            if self.node_cost_adjust_on_all(ori_dat=recv_data):  # 成本变更
                # print('recv:[report_all]', self.node_id, '<--', '：', recv_data)
                return True  ## 数据已处理，不再存入缓存
            if self.Cloud_node_recv_callback(recv_data): return True

            if self.node_id != self.cloud_name and not self.isIoT:
                self.bdir_record_data(recv_data)
            if self.bdir_ask_alarm_state(): pass

            # if sta: print('bdir_unpack_recv_package 2:', self.node_id, bdir_data)
            # else: print(self.node_id, '----')

            len_size = self.recv_buffer.qsize()
            if len_size + size > self.recv_buf_size * self.alarm_buf_rate:
                rate = ((len_size + size) - self.recv_buf_size * self.alarm_buf_rate) / self.recv_buf_size * 300  ## 反馈调整成本大小可调
                self.node_report_back(ori_dat=recv_data, rate=rate)  ##数据太多，修正下方成本
                # print('recv:[report_back]', self.node_id, '<--', '：', recv_data)

            if len_size + size < self.recv_buf_size:
                self.recv_buffer.put(recv_data)
                # print('recv:', self.node_id, '<--', '：', recv_data)
                return True
            else:  # 接收缓存区不足，告警.待处理数据太多
                # raise EOFError('{}: the recv buffer do not have enough space!'.format(self.node_id))
                # print('recv:', '{}: the recv buffer do not have enough space!'.format(self.node_id))
                while True:
                    if self.recv_buffer.qsize()<self.recv_buf_size:
                        self.recv_buffer.put(recv_data)
                        return True
                    time.sleep(self.recv_rate*0.01)
                pass

        else:
            # print('recv:', self.node_id, '<--', 'None')
            time.sleep(self.recv_rate)
            pass
        # self.__node_processing_func_1_res_buff_vishow()

        return False

    def node_processing_data_thread(self, dat: {} = None, real_thread: bool = True):
        print(self.node_id, 'starting processing thread...')
        while True:
            sleep(self.processing_rate)  #

            ''' 自产数据自处理 '''
            gene_size = self.generate_buffer.qsize()
            if gene_size > 0 and not self.isIoT:
                dat = self.generate_buffer.get()
                self.data_processing_size_add(dat)  ## 数据处理量叠加
                sleep(self.processing_rate / 1000)  ## 代表数据处理消耗的时间
                # print('processing:[generate]', self.node_id, '[{}:{}]==='.format(gene_size, len(str(data))), data)
                ## 数据处理完成

            else:
                # print('processing:[generate]', self.node_id, '===', None)
                pass

            ## 统计缓存使用情况
            len_size = self.generate_buffer.qsize()
            # if len_size > self.generate_buf_size * self.alarm_buf_rate:  # 自身数据过多缓存告急
            if (len_size > 0 and self.isIoT) or len_size > self.generate_buf_size * self.alarm_buf_rate:  ###      iot数据一律上传    不仅是为了展示效果
                data = self.generate_buffer.get(
                    timeout=1)  # data = {'did': dat_id, 'class': num_class, 'param': dat0, 'type': 'data'}
                ## 交给上层处理
                self.data_processing_size_add(data)  ## 数据处理量叠加
                # print('processing:[over generate]', self.node_id, data)
                da = self.decode_data_for_original_category(data)
                idx_class = da['class']
                target = da['target']
                with self.mux_lock_connect_cost:
                    cost_dict = self.node_connect_cost_dict
                self.data_processing_size_add(cost_dict)  ## 数据处理量叠加
                name_id = mat_optism.mode_optimal_smart(self_name=self.node_id, idx_class=idx_class,
                                                        mat_cost=cost_dict, target=target, isMDAR=self.isMDSR)
                # if name_id not in cost_dict.keys():
                #     print('=======', self.node_id, name_id, target, cost_dict)
                if self.node_send_data_(name_id=name_id, dat=data):
                    pass
                else:
                    self.generate_buffer.put(data)
                    print('processing:', self.node_id,
                          'even self generate buff\'s memory size [{}/{}], send [{}]fail!'.format(len_size,
                                                                                                  self.generate_buf_size,
                                                                                                  name_id))


            # sta = False
            # # print('========3=========', self.node_id)
            # if self.recv_buffer.qsize() == self.recv_buf_size:
            #     print('recv buffer oversize!!', self.node_id, self.unpack_recv_buffer.qsize())
            #     sta = True

            self.node_processing_func_1_res_buff_vishow()
            if (self.recv_buffer.qsize()) > 0:
                dat = self.recv_buffer.get()
                da = self.bdir_unpack_recv_package(dat)  # 数据压缩包解压,非压缩包就重新存入self.unpack_recv_buffer
                if da.qsize() == 0: self.unpack_recv_buffer.put(dat)
                """ BDIR """
                self.bdir_package_recv_iot_data()

                if self.unpack_recv_buffer.qsize() > 0: buffer = self.unpack_recv_buffer
                else: buffer = self.recv_buffer

                if buffer.qsize()>0:
                    # if sta:
                    #     print('recv buffer oversize!!2', self.node_id, self.recv_buffer.qsize(), self.unpack_recv_buffer.qsize())
                    dat = buffer.get(timeout=1e-6)
                    if not self.massage_processing(dat):
                        if self.isIoT:
                            if not self.iot_data_processing(dat):  ## 不是目标数据，重新处理
                                self.recv_buffer.put(dat)
                        else:
                            if not self.service_nodes_processing(dat):  ## 不是目标数据，重新处理
                                self.recv_buffer.put(dat)
                        ## 数据处理
                        # sleep(self.processing_rate/1000)  ## 代表数据处理消耗的时间
                        ## 数据处理完成
                        # print('processing:[recv]', self.node_id, '===', data)
                        pass
            else:
                # if self.node_id != self.cloud_name and not self.isIoT :print('processing:[recv]', self.node_id, '===', None)
                pass

            ## 统计缓存使用情况
            len_size = self.recv_buffer.qsize()
            ''' cloud 和iot节点都没有再转发的必要'''
            if self.node_id != self.cloud_name and not self.isIoT and self.isbalance \
                    and len_size > self.recv_buf_size * self.alarm_buf_rate:  # 接收数据过多缓存告急
                # if len_size>0:  ## 为了展示效果，这里直接发送上层
                data = self.recv_buffer.get(timeout=0.1)
                da = self.bdir_unpack_recv_package(data)  # 数据压缩包解压
                if da.qsize()==0: self.unpack_recv_buffer.put(data)
                if self.unpack_recv_buffer.qsize()>0: buffer = self.unpack_recv_buffer
                else: buffer = self.recv_buffer

                data = buffer.get(timeout=1e-6)
                if not self.massage_processing(data):
                    ## 交给上层处理
                    self.data_processing_size_add(data)  ## 数据处理量叠加
                    # print('processing:[over recv]', self.node_id, data)
                    # data = data['param']
                    da = self.decode_data_for_original_category(data)
                    idx_class = da['class']
                    target = da['target']
                    if da['type'] == 'data':  ## 只有iot数据才能立即转发
                        with self.mux_lock_connect_cost:
                            cost_dict = self.node_connect_cost_dict
                        self.data_processing_size_add(cost_dict)  ## 数据处理量叠加
                        name_id = mat_optism.mode_optimal_smart(self_name=self.node_id, idx_class=idx_class,
                                                                mat_cost=cost_dict, target=target, isMDAR=self.isMDSR)
                        if self.node_send_data_(name_id=name_id, dat=data):  ## 给上层处理
                            pass
                        else:
                            self.recv_buffer.put(data)
                    else:
                        self.recv_buffer.put(data)

            if self.node_id == self.cloud_name:  ##云节点的无敌运算能力
                # while self.recv_buffer.qsize() > 0:
                #     # data = self.recv_buffer.get(timeout=1)
                #     # sleep(1e-12)
                #     pass
                while self.generate_buffer.qsize() > 0:
                    data = self.generate_buffer.get(timeout=0.1)
                    sleep(self.generate_rate)
                    pass
                    # while self.send_buffer.qsize() > 0:
                    #     data = self.send_buffer.get(timeout=1)
                    #     sleep(1e-12)
                    pass
            self.node_processing_func_1_res_buff_vishow()

            if not real_thread:
                break
        pass
