import time
import numpy as np
import threading
import os
from func.routing_node_mission import Routing_Node_CPU
from func.Bdir_node_mission import Routing_Node_CPU_New
from utils.buildThread import ThreadPool as ThreadPool
from func.routing_mat_general import Routing_general as Routing_Map
from utils import visualization as vshow
import routing_config as config

np.random.seed(10)


class Routing_Mul_layers_Config:
    def __init__(self, cf=config, num_thread=200, real_thread=True):
        self.all_node_cpu_dict = None
        routing_Map = Routing_Map(len(cf.each_layer_nodes_num), mul_layer_radius=cf.diff_layer_radius,
                                  mul_layer_angle=cf.diff_layer_angle, mul_layer_num=cf.each_layer_nodes_num)

        routing_Map.compute_pt_to_connectedLayer_pt_distance(cf.max_distance_cost)
        self.Routing_Map = routing_Map
        num_thread = np.array(cf.each_layer_nodes_num).sum()*4
        self.ThreadPool = ThreadPool(num_thread, real_thread=real_thread)

        self.layers_nodes_config_for_cpu_map(cf)


    ''' 配置各层节点算力属性，并发送路由网络地图和成本 '''
    def layers_nodes_config_for_cpu_map(self, cf):
        mat = self.Routing_Map
        nodes_map = {}
        for layer in mat.routing_mat:
            for node in layer:
                name, radius, theta = str(node[0]), node[1], node[2]
                node_dict = {name: [radius, theta]}
                nodes_map = dict(nodes_map, **node_dict)

        try:
            os.makedirs(cf.save_path)
        except:
            # os.remove()
            pass
        cloud_name = mat.cloud_name
        ''' 配置各层节点算力属性 '''
        all_node_cpu_dict = {}
        for layer_idx, layer in enumerate(mat.routing_mat):  ## 层与层之间节点的算力水平差距
            # print(layer)
            for node_idx, node in enumerate(layer):
                rand_speed = np.random.uniform(cf.one_layer_cpu_performance[0], cf.one_layer_cpu_performance[1])
                base_speed = cf.get_delay_time(cf.diff_layers_cpu_performance[layer_idx], rand_speed)
                generate_rate = base_speed * cf.generate_speed
                receive_speed = base_speed * cf.receive_speed
                send_speed = base_speed * cf.send_speed
                processing_speed = base_speed * cf.processing_speed
                if layer_idx+1 == len(mat.routing_mat): isIoT = True
                else:  isIoT = False
                # if str(node[0])[:-2] == str(len(cf.each_layer_nodes_num)):
                #     isIoT = True
                # else: isIoT = False
                # print(node[0], rand_speed, '\n\t\tbase_speed={}, generate_rate={}, receive_speed={},\n\t\t'
                #        ' send_speed={}, processing_speed={}'.format (base_speed, generate_rate,
                #        receive_speed, send_speed, processing_speed))
                # node_cpu = Routing_Node_CPU(id=(node[0]), num_class=cf.data_class_num,
                #                             generate_rate=generate_rate, recv_rate=receive_speed,
                #                             send_rate=send_speed, processing_rate=processing_speed,  ## 控住节点性能
                #                             max_data_size=30,  ## 单次产生数据最大长度
                #                             send_buf=cf.send_buffer, gene_buf=cf.generate_buffer,
                #                             recv_buf=cf.receive_buffer,  ## 设置节点缓存空间大小
                #                             isMDSR=cf.MDAR_BUTTON, isODAS=cf.ODAS_BUTTON, balance=cf.Balance,
                #                             alarm_buf_rate=0.1, ODAS_rate=cf.ODAS_rate,   # 内存告警线
                #                             build_Thread=self.ThreadPool, cloud_name = cloud_name,
                #                             isIoT=isIoT, logPath=cf.save_path, generate_total=cf.generate_totalSize,
                #                             nodes_map=nodes_map,
                #                             )
                node_cpu = Routing_Node_CPU_New(id=(node[0]), num_class=cf.data_class_num,
                                            generate_rate=generate_rate, recv_rate=receive_speed,
                                            send_rate=send_speed, processing_rate=processing_speed,  ## 控住节点性能
                                            max_data_size=30,  ## 单次产生数据最大长度
                                            send_buf=cf.send_buffer, gene_buf=cf.generate_buffer,
                                            recv_buf=cf.receive_buffer,  ## 设置节点缓存空间大小
                                            isMDSR=cf.MDAR_BUTTON, isODAS=cf.ODAS_BUTTON, balance=cf.Balance,
                                            alarm_buf_rate=0.1, ODAS_rate=cf.ODAS_rate,  # 内存告警线
                                            build_Thread=self.ThreadPool, cloud_name=cloud_name,
                                            isIoT=isIoT, logPath=cf.save_path, generate_total=cf.generate_totalSize,
                                            nodes_map=nodes_map,

                                                is_Bdir=cf.is_use_Bdir, is_AER=cf.is_use_AER,
                                                tm_capacity_s=cf.tm_capacity_s, alarm_cap=cf.alarm_cap[layer_idx],
                                                package_size=cf.package_size, small_package_size=cf.small_package_size,
                                                assi_nodes_num=cf.assi_nodes_num, max_pack_time_s=cf.max_pack_time_s,
                                                aer_accelerate_cap=cf.aer_accelerate_cap,

                                            )

                node_cpu_dict = {str(node[0]): node_cpu}
                all_node_cpu_dict = dict(all_node_cpu_dict, **node_cpu_dict)
                # node_cpu
        self.all_node_cpu_dict = all_node_cpu_dict

        self.start_time = time.time()
        for layer in mat.routing_mat_price:  ## 进入层内 dict
            # layer = dict()
            # print('layer\' node:',  layer)
            for nodes_in_layer in layer.keys():  ## 遍历层内节点
                node_connected_cpu = {}
                node_connected_cost = {}
                # print('eachlayer:', nodes_in_layer,  layer[nodes_in_layer])
                for nodes_connectes_dict in layer[nodes_in_layer]:  ## 遍历每一个节点的可连接节点
                    # print('connected node in layer:', nodes_connectes_dict, layer[nodes_in_layer][nodes_connectes_dict])
                    connect_cost = layer[nodes_in_layer][nodes_connectes_dict]
                    cost = {'ori': connect_cost}
                    for v in range(cf.data_class_num):
                        co_class = {str(v): cf.max_distance_cost / 2}
                        cost = dict(cost, **co_class)
                    node_cost = {nodes_connectes_dict: cost}  # 重新定义成本
                    node_connected_cost = dict(node_connected_cost, **node_cost)  # 各节点能连接的点的通信成本独立打包

                    node_cpu = {nodes_connectes_dict: all_node_cpu_dict[nodes_connectes_dict]}  # 只是为了传递服务器通信地址
                    node_connected_cpu = dict(node_connected_cpu, **node_cpu)  # 各节点能连接的点的发送地址独立打包 发给这个节点

                ''' 发送路由网络地图和成本, 并启动线程  '''
                all_node_cpu_dict[nodes_in_layer].define_node_connected(cpu_dict=node_connected_cpu,
                                                                        cost_dict=node_connected_cost)
                # print('nodes_in_layer:', nodes_in_layer)
                time.sleep(1e-10)   ##cf.speed_base/100
        # all_node_cpu_dict['404'].node_processing_data_thread(None, True)  ## 单独运行
        pass

    def wait_for_all_nodes_finish_processing(self, ishow=True):
        idx = 0
        mat = self.Routing_Map
        while True:
            num = 0
            each_layer_num = []
            for layer in mat.routing_mat_price:  ## 进入层内 dict
                each_layer_num.append(0)
                for nodes_in_layer in layer.keys():  ## 遍历层内节点
                    temp = self.all_node_cpu_dict[nodes_in_layer].get_all_data_processed()
                    num += temp
                    each_layer_num[-1] = each_layer_num[-1] + temp
            idx = idx+1 if idx+1<8 else 1
            each_layer_num = np.array(each_layer_num).tolist()
            if ishow: print('\r res buffer [ {} ]. {} thread is running! {}\t {}'.
                  format(each_layer_num, threading.active_count(), '.'*idx, time.time() - self.start_time), end='')
            time.sleep(0.1)
            num = np.array(num)
            if num.sum() == 0: break   # 所有节点数据都处理完了，没有内容
        used_time = time.time() - self.start_time
        print('\n\nprogram data processing time is {}\n\n'.format(used_time))
        self.close_all()

    def close_all(self):
        # return
        self.ThreadPool.stop_Thread_now()
        for node_cpu in self.all_node_cpu_dict.values():
            node_cpu.close_all_thread()

    def __del__(self):
        # self.close_all()
        # self.ThreadPool.thread_list_generate.close()
        # print('thread_list_generate all is close!')
        # self.ThreadPool.thread_list_send.close()
        # print('thread_list_send all is close!')
        # self.ThreadPool.thread_list_recv.close()
        # print('thread_list_recv all is close!')
        # self.ThreadPool.thread_list_processing.close()
        # print('thread_list_processing all is close!')
        pass



if __name__ == '__main__':

    Routing_layers_Config = Routing_Mul_layers_Config(config, 200, True)

    ''' 运行一下代码才有可视化 '''
    # Data_show = vshow.SHOW_nodes_data_cv(Routing_layers_Config.Routing_Map.routing_mat)
    # Data_show.start_draw_nodes_data_dynamically_thread()
    # time.sleep(50)

    print('Now alive thread num=', threading.active_count())
    Routing_layers_Config.wait_for_all_nodes_finish_processing(ishow=False)  ### 等待数据处理完成，并关闭程序
    print('Now alive thread num=', threading.active_count())

    time.sleep(60*10)
    # Data_show.close__draw_nodes_data_dynamically_thread()


    exit()
