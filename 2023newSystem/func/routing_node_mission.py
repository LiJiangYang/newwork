import math
from time import sleep

from utils.service_communication import *
from utils.utils import *

from utils.buildThread import ThreadPool as ThreadPool
from routing_optism import routing_node_choice_optism as mat_optism
from utils import log_printFormat as logprint, visualization as Vishow

# np.random.seed(12)


''' 定义节点间的发送/接受方式'''

''' 定义各路由节点的CPU计算单元，设置其数据生成和发送能力，数据处理能力。'''


class Routing_Node_CPU(object):
    def __init__(self, id, num_class=5, generate_rate=0.1, recv_rate=0.1, send_rate=0.1, processing_rate=0.1,
                 max_data_size=100, send_buf=500, gene_buf=500, recv_buf=500,
                 isMDSR=True, isODAS=False, balance=True, alarm_buf_rate=0.5, ODAS_rate=0.5,
                 build_Thread: ThreadPool = None, cloud_name = '',
                 isIoT=False, logPath='', generate_total=0, nodes_map=None, **kwargs):

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

        self.isMDSR = isMDSR   ##
        self.isODAS = isODAS
        self.isbalance = balance  ## 负载均衡开关
        self.ODAS_rate = ODAS_rate

        # self.generate_data_format = {'did': self.node_id, 'class': '0', 'param': None, 'type': 'data',
        #                              'target': None, 'time': 0}

        self.log = logPath + self.node_id + '_node_log.csv'
        # logprint.node_record_alldatawriteheader(self.log)  ## 被继承后，这里不需要先创建log

    ''' 定义数据格式 '''

    def generate_data_format(self):
        generate_data_format = {'did': self.node_id, 'class': '0', 'param': None, 'type': 'data',
                                'target': None, 'time': time.time(), 'similar': np.random.random()}
        return generate_data_format
        pass

    def all_thread_run(self, sta=None):
        if sta is None:
            with self.all_thread_run_mux:
                sta = self.all_thread_run_sta
            return sta
        elif not sta:
            with self.all_thread_run_mux:
                self.all_thread_run_sta = False
        else:
            with self.all_thread_run_mux:
                self.all_thread_run_sta = True

    def define_node_connected(self, cpu_dict=None, cost_dict=None):
        self.node_connected_nodes = Node_Communication(name=self.node_id, node_cpu=cpu_dict)  ## 传送能连接的节点地址
        self.node_connect_cost_dict = cost_dict  ## 传送能连接的节点的成本
        # print(str(self.node_id), 'cost:', self.node_connect_cost_dict)

        if self.build_Thread is not None:
            # print('===0===========', self.node_id)
            build_Thread = self.build_Thread
            self._thread_generate_data = build_Thread.node_generate_run(func=self.node_generate_data_thread,
                                                                        args=(None,),
                                                                        callback=self.thread_callback_g,
                                                                        name=self.node_id)
            # print('===1===========', self.node_id)
            self._thread_send_data = build_Thread.node_send_run(func=self.node_send_data_thread, args=(None,),
                                                                callback=self.thread_callback_s, name=self.node_id)
            # print('===2===========', self.node_id)
            self._thread_recv_data = build_Thread.node_recv_run(func=self.node_recv_data_thread, args=(None,),
                                                                callback=self.thread_callback_r, name=self.node_id)
            # print('===3===========', self.node_id)
            self._thread_processing_data = build_Thread.node_processing_run(self.node_processing_data_thread,
                                                                            args=(None,),
                                                                            callback=self.thread_callback_p,
                                                                            name=self.node_id)
            # print('===4===========', self.node_id)
        pass

    def node_generate_data_thread(self, dat: {} = None, real_thread: bool = True):
        print(self.node_id, 'starting generate thread...')
        # k = 1.0
        his_ssid = 0
        while self.all_thread_run():
            sleep(float(self.generate_rate))
            if not self.isIoT:
                # print(self.node_id, 'isiot=', self.isIoT)
                break  ### 非iot节点，不产生数据
            dat_size = np.random.randint(1, self.max_data_size)
            dat0 = np.random.randint(0, 1000, int(dat_size), np.int16)
            ssid = np.random.randint(0, 1000)
            # print('generate:',self.node_id, '-------------------', ssid, his_ssid)
            while ssid == his_ssid:
                ssid = np.random.randint(0, 100000)  # 避免id连续重复
                # print('generate:',self.node_id, '-----repeat--------------', ssid, his_ssid)
            his_ssid = ssid
            dat_id = self.node_id + '_' + str(ssid)
            num_class = str(np.random.randint(0, self.data_category_num))
            data = self.generate_data_format()
            data['did'] = dat_id
            data['class'] = num_class
            data['param'] = dat0.tolist()
            data['type'] = 'data'
            data['target'] =  self.cloud_name  ## 默认数据传送目标的 cloud
            # data = {'did': dat_id, 'class': num_class, 'param': dat0.tolist(), 'type': 'data'}

            len_size = self.generate_buffer.qsize()
            if len_size < self.generate_buf_size - 1:  # dat_size
                self.generate_buffer.put(data)
                self.generate_total -= len(str(data))  ## 数据产生量控制。 可以自己改
            else:  # 发送缓存区不足，告警
                # raise EOFError('{}: the send buffer do not have enough space!'.format(self.node_id))
                # print('generate:', '{}: the generate buffer do not have enough space! [{}/{}]'.format(self.node_id,
                #                                                                                   len_size+dat_size,
                #                                                                                   self.generate_buf_size))
                pass
            if len_size > self.generate_buf_size * self.alarm_buf_rate:  ## 内存告急
                k = 1 + (len_size - self.generate_buf_size * self.alarm_buf_rate) / self.generate_buf_size # 生产速率调整
                if k > 0: sleep(float(self.generate_rate * k))
            self.__node_processing_func_1_res_buff_vishow()
            if not real_thread:
                break
            if self.generate_total <= 0: break  ## 数据总量满足，不再产生数据

        pass

    def node_send_data_thread(self, dat=None, real_thread: bool = True):
        print(self.node_id, 'starting send thread...')
        num = time.time()
        while True:  # self.all_thread_run():
            sleep(float(self.send_rate))
            if self.send_buffer.qsize()==0:
                # if time.time()-num>(1e6*self.processing_rate)  : break  # 长时间没有数据就退出线程
                # and self.node_id == self.cloud_name
                pass
            elif self.send_buffer.qsize() > 0:
                num=time.time()
                (dat, target) = self.send_buffer.get()
                # if self.node_id == '304':
                #     print()
                # (dat, target) = data
                if dat is None: continue
                self.data_processing_size_add(dat)  ## 数据处理量叠加
                ori_param = self.decode_data_for_original_category(dat)
                idx_class = ori_param['class']
                target2 = ori_param['target']
                # print('node_send_data_thread', (dat, target))
                if target is None:
                    with self.mux_lock_connect_cost:
                        cost_dict = self.node_connect_cost_dict
                    self.data_processing_size_add(cost_dict)  ## 数据处理量叠加
                    target = mat_optism.mode_optimal_smart(self_name=self.node_id, idx_class=idx_class,
                                                           mat_cost=cost_dict, target=target2, isMDAR=self.isMDSR)

                # if abs(int(self.node_id[:-2]) - int(target[:-2]))>1:
                #     print(self.node_id, 'send:', target, 'tart:', target2, cost_dict.keys())

                if target is None:
                    # self.send_buffer.put((dat, target))  # cloud点不能再放回
                    if self.node_id != self.cloud_name:
                        print('node_send_data_thread', self.node_id, (target, dat))
                    pass
                else:
                    params = {'id': self.node_id, 'param': dat, 'time': time.time()}
                    self.__node_processing_func_2_connnect_vishow(node_id=target, num_class=idx_class)
                    ## 发送数据：对象，数据
                    retry = 5
                    while retry > 0:
                        if self.node_connected_nodes.send_data(target, dat=dict2str(params)): break
                        retry -= 1
                    if retry > 0:  ## 发送成功
                        # print('send:', self.node_id, '-->', target, 'successful！ ：', dat, flush=True)
                        # if 'type' in dat.keys() and 'bdir-pack' in dat['type']: print('send:', self.node_id, '-->', target, 'successful！', dat)
                        pass
                    else:  ## 发送失败
                        self.send_buffer.put((dat, target))
                        print('send:', self.node_id, '-->', target, 'fail！ ：', dat, flush=True)

                # self.__node_processing_func_1_res_buff_vishow()
            if not real_thread:
                break
        print(self.node_id, 'ending send thread...')
        pass

    def node_send_data_(self, name_id, dat: {} = None):
        try:
            self.send_buffer.put((dat, name_id),  timeout=0.1)
            return True
        except:  ## 内存超出，等待录入
            while True:
                try:
                    self.send_buffer.put((dat, name_id), timeout=0.1)
                    time.sleep(self.send_rate)
                    return True
                except:pass
            return False

    def node_recv_data_thread(self, dat=None, real_thread: bool = True):
        print(self.node_id, 'starting recv thread...')
        while self.all_thread_run():
            sleep(float(self.recv_rate))
            if self.node_recv_data_():
                self.__node_processing_func_1_res_buff_vishow()
            if not real_thread:
                break

            pass

    def node_recv_data_(self):
        recv_data = self.node_connected_nodes.recv_data()
        recv_data = str2dict(recv_data)
        if recv_data is not None:  ## 模拟有数据发送到缓存区
            self.data_processing_size_add(recv_data)  ## 数据处理量叠加
            size = 1  ## len(str(recv_data)) 数据格式： str {id: [data]}
            recv_data = str2dict(recv_data)  ## 数据格式：{id: [data]}

            if self.node_report_on_self(ori_dat=recv_data):  # 成本变更
                # print('recv:[report_self]', self.node_id, '<--', '：', recv_data)
                return True  ## 数据已处理，不再存入缓存
            if self.node_cost_adjust_on_all(ori_dat=recv_data):  # 成本变更
                # print('recv:[report_all]', self.node_id, '<--', '：', recv_data)
                return True  ## 数据已处理，不再存入缓存
            if self.__Cloud_node_recv_callback(recv_data): return True
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
                    time.sleep(self.recv_rate*2)
                pass

        else:
            # print('recv:', self.node_id, '<--', 'None')
            time.sleep(self.recv_rate*2)
            pass
        # self.__node_processing_func_1_res_buff_vishow()

        return False

    '''模拟数据被处理'''

    def node_processing_data_thread(self, dat: {} = None, real_thread: bool = True):
        print(self.node_id, 'starting processing thread...')
        while True:
            sleep(self.processing_rate)  #
            if (self.recv_buffer.qsize()) > 0:
                dat = self.recv_buffer.get()
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
                # print('processing:[recv]', self.node_id, '===', None)
                pass

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
                data = self.generate_buffer.get(timeout=1)  # data = {'did': dat_id, 'class': num_class, 'param': dat0, 'type': 'data'}
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

            # print('========3=========', self.node_id)

            ## 统计缓存使用情况
            len_size = self.recv_buffer.qsize()
            ''' cloud 和iot节点都没有再转发的必要'''
            if self.node_id!=self.cloud_name and not self.isIoT and self.isbalance\
                    and len_size > self.recv_buf_size * self.alarm_buf_rate:  # 接收数据过多缓存告急
                # if len_size>0:  ## 为了展示效果，这里直接发送上层
                data = self.recv_buffer.get(timeout=0.1)
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
            self.__node_processing_func_1_res_buff_vishow()

            if not real_thread:
                break
        pass

    ''' 服务节点运行的函数：遇到原生数据(包括被转发的）立即处理（反向发送） '''

    def service_nodes_processing(self, dat):
        # dat = {'id': self.node_id, 'param': dat, 'time': 15663334.555}  ## 被转发的数据格式
        # dat = {'did': dat_id, 'class': 'k', 'param': 200 * rate, 'type': 'data', 'time': 15663334.555}  ## 原生数据格式
        dat00 = dat
        self.data_processing_size_add(dat00)
        communicate_path = []
        target, tm = None, None
        while True:
            # try:
            if 'type' in dat.keys(): break
            # except:
            #     print('service_nodes_processing:', self.node_id,  dat)
            #     raise
            ori_node = str(dat['id'])
            if target is None:
                target = self.node_id
                tm = time.time()
            R1, angle1 = self.nodes_map[ori_node]
            R2, angle2 = self.nodes_map[target]
            distance = int(R1 ** 2 + R2 ** 2 - 2 * R1 * R2 * math.cos((angle1 - angle2) / 180 * math.pi))

            node_dict = [target, distance, tm]
            tm = dat['time']
            # communicate_path = dict(communicate_path, **node_dict)
            communicate_path.append(node_dict)
            target = ori_node  ## 保存最后一次的id，就是数据出生地
            dat = dat['param']
        node_dict = [target, 0, tm]
        communicate_path.append(node_dict)
        communicate_path.reverse()
        self.data_processing_size_add(dat00)

        ''' 中间节点 数据处理完后，返回'结果' '''
        if self.node_id != self.cloud_name and not self.isIoT and dat['type'] == 'back':  ## 边缘节点只负责传递处理结果
            # self.node_send_data_(None, dat00)## 自动巡航会导致进入死胡同，无法传递给目标点
            next_node = None
            if dat['target'] != self.cloud_name:
                back_path = dat['param']['up']
                is_in = False
                for node in back_path:
                    if node[0] == self.node_id:
                        is_in = True
                        break
                    else:
                        next_node = node[0]
                if not is_in: next_node = None
                # if dat['target'] == '401':
                #     print(self.node_id, target, dat00, '\n\t', next_node, back_path)
            self.node_send_data_(next_node, dat00)  ## 原路返回，保证信息可达，且路径优
            writedata = {'record time': time.time(), 'gener time': None, 'old': self.data_processing_size_old,
                         'new': self.data_processing_size_new, 'odas': self.data_processing_size_ODAS,
                         'back nodes and time': dat, 'up nodes and time': communicate_path}
            self.data_processing_size_add(writedata)
            logprint.node_record_alldata(self.log, writedata)

            ''' 云节点收到数据后，处理并返回 '''
        elif self.node_id == self.cloud_name and dat['type'] == 'back':  #云接收到处理结果后，返回数据
            gener_time = dat['time']
            send_data = self.generate_data_format()
            communicate_path = dat['param']['up'] + communicate_path
            send_data['param'] = {'up': communicate_path, 'generTime': gener_time}
            send_data['class'] = dat['class']
            send_data['target'] = dat['did']
            send_data['type'] = 'back'  # 处理过的标志，

            writedata = {'record time': time.time(), 'gener time': gener_time, 'old': self.data_processing_size_old,
                         'new': self.data_processing_size_new, 'odas': self.data_processing_size_ODAS,
                         'back nodes and time': dat, 'up nodes and time': communicate_path}
            self.data_processing_size_add(writedata)
            logprint.node_record_alldata(self.log, writedata)

            # self.node_send_data_(None, send_data)  ## 自动巡航会导致进入死胡同，无法传递给目标点
            next_node = None
            for node in communicate_path:
                if node[0] == self.node_id:
                    break
                else:
                    next_node = node[0]
            self.node_send_data_(next_node, send_data)  ## 原路返回，保证信息可达，且路径优
            # if dat['target'] == '401':
            #     print(self.node_id, target, dat00, '\n\t', send_data)


        if dat['type'] == 'data':
            gener_time = dat['time']
            if self.isMDSR:  ## 开：直接返回处理结果，不传cloud
                send_data = self.generate_data_format()
                send_data['param'] = {'up': communicate_path, 'generTime': gener_time}
                send_data['class'] = dat['class']
                send_data['target'] = target
                send_data['type'] = 'back'

                writedata = {'record time': time.time(), 'gener time': gener_time, 'old': self.data_processing_size_old,
                             'new': self.data_processing_size_new, 'odas': self.data_processing_size_ODAS,
                             'back nodes and time': None, 'up nodes and time': communicate_path}
                self.data_processing_size_add(writedata)
                logprint.node_record_alldata(self.log, writedata)

                self.node_send_data_(None, send_data)
            else: ## MDSR关 ， 处理结果先发送给cloud
                data = dat
                data['did'] = target  ## 保存该条数据的最原始来源
                data['type'] = 'back'  ## 修改标志：处理过
                data['time'] = time.time()
                data['target'] = self.cloud_name
                data['param'] = {'up': communicate_path, 'param': dat['param'] }
                if self.node_send_data_(None, data):  ## MDSR关 ， 先发送给cloud
                    # self.generate_buffer.put((None, dat))
                    pass
                writedata = {'record time': time.time(), 'gener time': gener_time, 'old': self.data_processing_size_old,
                             'new': self.data_processing_size_new, 'odas': self.data_processing_size_ODAS,
                             'back nodes and time': None, 'up nodes and time': communicate_path}
                self.data_processing_size_add(writedata)
                logprint.node_record_alldata(self.log, writedata)


        return True  # 处理完了本条指令

    ''' iot节点运行的函数：记录自身从产生到返回结果的全过程 '''

    def iot_data_processing(self, dat):
        # ori_dat = {'id': self.node_id, 'param': dat, 'time': 15663334.555}
        # dat = {'did': dat_id, 'class': 'k', 'param': 200 * rate, 'type': 'cost'}
        # return False
        dat00 = dat
        communicate_path = []
        target, tm = None, None
        while True:
            if 'type' in dat.keys(): break
            ori_node = str(dat['id'])
            if target is None:
                target = self.node_id
                tm = time.time()

            R1, angle1 = self.nodes_map[ori_node]
            R2, angle2 = self.nodes_map[target]
            distance = int(R1 ** 2 + R2 ** 2 - 2 * R1 * R2 * math.cos((angle1 - angle2) / 180 * math.pi))
            node_dict = [target, distance, tm]
            tm = dat['time']
            # communicate_path = dict(communicate_path, **node_dict)
            communicate_path.append(node_dict)
            target = ori_node  ## 保存最后一次的id，就是数据出生地
            dat = dat['param']
        node_dict = [target, 0, tm]
        communicate_path.append(node_dict)

        self.data_processing_size_add(dat00)
        if dat['type'] != 'back':
            # print(self.node_id, dat00)
            return False
        up_path = dat['param']['up']
        gener_time = dat['param']['generTime']
        communicate_path.reverse()
        writedata = {'record time': time.time(), 'gener time': gener_time, 'old': self.data_processing_size_old,
                     'new': self.data_processing_size_new, 'odas': self.data_processing_size_ODAS,
                     'back nodes and time': communicate_path, 'up nodes and time': up_path}
        logprint.node_record_alldata(self.log, writedata)
        return True  # 没处理本条指令

    def node_report_back(self, ori_dat: {} = None, rate: float = 0):
        ''' 传输代价更新（主动） '''
        if not self.isbalance:
            # print(self.node_id, ori_dat)
            return True
        # params = {'id': self.node_id, 'param': dat}
        node_id = ori_dat['id']
        dat = self.decode_data_for_original_category(ori_dat)
        self.data_processing_size_add(dat)  ## 数据处理量叠加
        idx_class = dat['class']
        dat_id = np.random.randint(0, 1000)
        dat_id = self.node_id + '_' + str(dat_id)
        # dat = {'did': dat_id, 'class': idx_class, 'param': rate, 'type': 'cost'}
        dat = self.generate_data_format()
        dat['did'] = dat_id
        dat['class'] = idx_class
        dat['param'] = rate
        dat['type'] = 'cost'
        dat['target'] = str(node_id)  ## 数据传送目标
        ## 自身信息也需要修改
        with self.mux_lock_connect_cost:
            self.node_connect_cost_dict[node_id][idx_class] = int(
                self.node_connect_cost_dict[node_id][idx_class]) + int(
                rate)  # 调整k类数据通信成本
        self.node_send_data_(node_id, dat=dat)  # 调整k类数据通信成本
        return True

    def node_report_on_self(self, ori_dat: {} = None):
        # ori_dat = {'id': self.node_id, 'param': dat}
        # dat = {'did': dat_id, 'class': 'k', 'param': 200 * rate, 'type': 'cost'}
        ori_id = ori_dat['id']
        dat = self.decode_data_for_original_category(ori_dat)
        self.data_processing_size_add(dat)  ## 数据处理量叠加
        # print('recv:', self.node_id, 'node_report_on_self:', ori_dat, dat)
        if 'cost' == dat['type']:  # 调整k类数据通信成本
            value = dat['param']
            idx_class = dat['class']
            with self.mux_lock_connect_cost:
                self.node_connect_cost_dict[ori_id][idx_class] = int(
                    self.node_connect_cost_dict[ori_id][idx_class]) + int(
                    value)
            return True  # 处理完了本条指令
        return False  # 没处理本条指令

    def node_cost_adjust_on_all(self, ori_dat: {} = None):
        # ori_dat = {'id': self.node_id, 'param': dat}
        # dat = {'did': dat_id, 'class': 'k', 'param': 200 * rate, 'type': 'cost'}
        ori_id = ori_dat['id']
        dat = self.decode_data_for_original_category(ori_dat)
        self.data_processing_size_add(dat)  ## 数据处理量叠加
        if 'same' == dat['type']:  # 调整k类数据通信成本
            value = int(dat['param'])
            idx_class = dat['class']
            target = dat['target']
            # if int(target[:-2]) + 1 > int(self.node_id[:-2]):  # 上层跨层传递给自己的，不修改
            #     return False
            # print('self.node_connect_cost_dict:[1]', self.node_id, self.node_connect_cost_dict)
            if int(target[:-7]) == int(ori_id[:-7]):  # 同层 ，则只修改不转发
                # print('recv:', self.node_id, 'node_cost_adjust_on_all:', ori_dat, '*',  dat)
                with self.mux_lock_connect_cost:
                    self.node_connect_cost_dict[ori_id][idx_class] = int(
                        self.node_connect_cost_dict[ori_id][idx_class]) + value
                self.recieve_a_same_sign = True
                # print('self.node_connect_cost_dict:[2]', self.node_id, self.node_connect_cost_dict)
                return True  # 处理完了本条指令
            elif target == self.node_id:  # 上层传递给自己的（修改的目标是自己），遍历修改成本,并转发
                with self.mux_lock_connect_cost:
                    self.node_connect_cost_dict[ori_id][idx_class] = int(
                        self.node_connect_cost_dict[ori_id][idx_class]) + value
                for node in self.node_connect_cost_dict.keys():  ## 所有节点的该类成本调整
                    if int(node[:-7]) - 1 == int(self.node_id[:-7]):  # 默认每层节点数量<99  # 只向下层节点传递，避免重复发送降本指令，造成网络震荡
                        with self.mux_lock_connect_cost:
                            self.node_connect_cost_dict[node][idx_class] = int(
                                self.node_connect_cost_dict[node][idx_class]) + int(
                                value)
                        dat['did'] = self.node_id
                        dat['target'] = node
                        self.node_send_data_(name_id=node, dat=dat)
                        # print('node_cost_adjust_on_all', self.node_id, '-->', node)
                # print('self.node_connect_cost_dict:[3]', self.node_id, self.node_connect_cost_dict)
                return True  # 处理完了本条指令
            elif target != self.node_id:  ### 误发
                # print(self.node_id, ori_dat)
                return True
        return False  # 没处理本条指令

    '''只有云节点有权跑这个函数，最先主动锁定各类数据的传输路径'''

    def __Cloud_node_recv_callback(self, ori_dat: {} = None):
        if (self.node_id == self.cloud_name or self.recieve_a_same_sign) and self.isMDSR:  ##MDSR开才有这操作
            # return False
            node_id = ori_dat['id']
            dat = self.decode_data_for_original_category(ori_dat)
            self.data_processing_size_add(dat)  ## 数据处理量叠加
            try:
                # print('recv:[1]', self.node_id, '__Cloud_node_recv_callback:', ori_dat, dat)
                if 'data' == dat['type']:  # 调整k类数据通信成本
                    idx_class = dat['class']
                    if idx_class in self.__cloud_data_class:
                        return True
                    self.__cloud_data_class.append(idx_class)
                    # dat = {'did': node_id, 'class': idx_class, 'param': -100, 'type': 'same'}  ##该类数据上传节点的该类通信成本降低200
                    dat = self.generate_data_format()
                    dat['did'] = node_id
                    dat['class'] = idx_class
                    dat['param'] = -500
                    dat['type'] = 'same'
                    dat['target'] = str(node_id)
                    self.data_processing_size_add(dat)  ## 数据处理量叠加
                    self.node_send_data_(name_id=node_id, dat=dat)
                    with self.mux_lock_connect_cost:
                        self.node_connect_cost_dict[node_id][idx_class] = int(
                            self.node_connect_cost_dict[node_id][idx_class]) + int(
                            -500)
                    # print('recv:[2]', self.node_id, '__Cloud_node_recv_callback:', ori_dat, dat)
                    return True
            except:
                pass
        return False
        pass

    def Cloud_node_recv_callback(self, ori_dat: {} = None):
        return self.__Cloud_node_recv_callback( ori_dat)

    def __node_processing_func_1_res_buff_vishow(self, dat: {} = None, **kwargs):
        size = self.recv_buffer.qsize()
        recv_size = [size, self.recv_buf_size]
        size = self.generate_buffer.qsize()
        gene_size = [size, self.generate_buf_size]
        size = self.send_buffer.qsize()
        send_size = [size, self.send_buf_size]
        dat = {str(self.node_id): {'recv_res': recv_size, 'generate_res': gene_size, 'send_res': send_size}}
        Vishow.qimg_add_data(dat=dat)
        pass

    def node_processing_func_1_res_buff_vishow(self):
        return self.__node_processing_func_1_res_buff_vishow()

    def __node_processing_func_2_connnect_vishow(self, node_id=None, num_class=None):
        dat = {self.node_id: {'connect': str(node_id), 'class': str(num_class)}}
        Vishow.qimg_add_data(dat=dat)
        pass

    def node_processing_func_2_connnect_vishow(self, node_id=None, num_class=None):
        self.__node_processing_func_2_connnect_vishow( node_id, num_class)

    def decode_data_for_original_category(self, dat):
        key = 'type'
        # key = str(list(key)[0])
        while True:
            try:
                param = dat[key]
                return dat
            except:
                dat = dat['param']

    def data_processing_size_add(self, dat=None, num: int = 0):
        is_new = False
        try:
            if 'type' in dat['param'].keys():  ##数据未经转发，视为新数据
                is_new = True
        except:  ## 报错则说明数据类型不是网络传输数据格式，属于自身数据（新）
            is_new = True

        try:
            d = self.decode_data_for_original_category(dat)
            if d['type']=='back': is_new=True
        except: pass

        if dat is not None:  ## dat==None, 默认为旧数据的累加
            num = num + len(str(dat))
        if self.isODAS:
            try:
                dat2 = self.decode_data_for_original_category(dat)
                similar = dat2['similar']
                self.data_processing_size_ODAS += num * similar * self.ODAS_rate
            except:  ## 有可能不是原生数据。而是通信数据
                pass

        if is_new:
            with self.data_processing_size_lock:
                self.data_processing_size_new += num
        else:
            with self.data_processing_size_lock:
                self.data_processing_size_old += num

    ''' 判断数据是否处理完成'''

    def get_all_data_processed(self):
        num = []
        num.append(self.recv_buffer.qsize())
        num.append(self.generate_buffer.qsize())
        num .append( self.send_buffer.qsize() )
        num = np.array(num)
        return num

    def thread_callback_g(self, status, result):
        if status:
            # print(self.node_id, 'thread backcall:', result)
            pass
        else:
            print('\033[31m thread ERROR:[generate]', self.node_id, ':', result, '\033[0m')
        pass

    def thread_callback_s(self, status, result):
        if status:
            # print(self.node_id, 'thread backcall:', result)
            pass
        else:
            print('\033[31m thread ERROR:[send]', self.node_id, ':', result, '\033[0m')
        pass

    def thread_callback_r(self, status, result):
        if status:
            # print(self.node_id, 'thread backcall:', result)
            pass
        else:
            print('\033[31m thread ERROR:[recv]', self.node_id, ':', result, '\033[0m')
        pass

    def thread_callback_p(self, status, result):
        if status:
            # print(self.node_id, 'thread backcall:', result)
            pass
        else:
            print('\033[31m thread ERROR:[processing]', self.node_id, ':', result, '\033[0m')
        pass

    def close_all_thread(self):
        self.all_thread_run(False)


''' 定义节点间的发送/接受方式'''
