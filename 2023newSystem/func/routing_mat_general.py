import math
import time
import numpy as np

from func.routing_node_mission import Routing_Node_CPU
from utils.buildThread import ThreadPool as ThreadPool


np.random.seed(10)

''' 随机定义多层路由的位置 Routing=[layer_idx:[idx,radius,angle]] 
    根据节点位置，计算各节点间的距离（通信成本）
'''


class Routing_general:
    def __init__(self, layer_num=4, mul_layer_radius=None, mul_layer_angle=None,
                 mul_layer_num=None):
        # self.mul_layer_radius = mul_layer_radius
        if mul_layer_radius is None:
            mul_layer_radius = []
            for i in range(layer_num):
                radius = 10 * i
                mul_layer_radius.append(radius)
            # self.mul_layer_radius = mul_layer_radius
        # self.mul_layer_angle = mul_layer_angle
        if mul_layer_angle is None:  ## 默认每层0-180
            mul_layer_angle = []
            for i in range(layer_num):
                angle = [0, 180]
                mul_layer_angle.append(angle)
            # self.mul_layer_angle = mul_layer_angle
        self.mul_layer_num = mul_layer_num
        if mul_layer_num is None:  ## 默认每层5个节点
            mul_layer_num = []
            for i in range(layer_num):
                num = 5
                mul_layer_num.append(num)
                self.mul_layer_num = mul_layer_num
        self.cloud_name = str(1 * (10**7)+1)
        self.routing_mat = []
        # print('mul_layer_num:', mul_layer_num)
        for i in range(layer_num):  # 逐层生成
            average_angle_apart = (mul_layer_angle[i][1]-mul_layer_angle[i][0])/mul_layer_num[i]  ## 节点平均分布
            start_angle = mul_layer_angle[i][0] + average_angle_apart/2 ## 节点起始位置（角度）
            one_layer_nodes_angle = np.array([start_angle+average_angle_apart*angle for angle in range(mul_layer_num[i])], np.float)  ##均衡分布在范围的中间
            try:
                one_layer_nodes_angle_adjust = np.random.randint(int(-average_angle_apart/4),
                                                    int(average_angle_apart/4),
                                                    mul_layer_num[i], np.int16)   ## 节点分布位置随机调整，范围是【average_angle_apart/2】
            except:
                one_layer_nodes_angle_adjust = np.zeros(mul_layer_num[i], np.int16)
            one_layer_angle = one_layer_nodes_angle + one_layer_nodes_angle_adjust
            # print('apart:', average_angle_apart, 'start:', start_angle, 'adjust:', one_layer_nodes_angle_adjust,
            #       'ori:', one_layer_nodes_angle,  'final:', one_layer_angle)
            point_dat = np.zeros([mul_layer_num[i], 3], np.int64)
            point_dat[:, 0] = [(i + 1) * (10**7) + name + 1 for name in range(mul_layer_num[i])]
            point_dat[:, 1] = mul_layer_radius[i]
            point_dat[:, 2] = one_layer_angle
            self.routing_mat.append(point_dat)
        self.routing_mat_price = []
        pass

    ''' 计算所有节点连接 '''
    def compute_pt_to_all_pt_distance(self, max_distance=1000):
        all_layer_distance = []
        for layer_idx in range(len(self.routing_mat)):
            # one_layer_distance = []
            one_layer_distance = {}
            for each_layer_idx in range(len(self.routing_mat[layer_idx])):
                name1 = self.routing_mat[layer_idx][each_layer_idx][0]
                R1 = self.routing_mat[layer_idx][each_layer_idx][1]
                angle1 = self.routing_mat[layer_idx][each_layer_idx][2]
                point_all_dis = {}
                for layer_idx2 in range(len(self.routing_mat)):
                    for each_layer_idx2 in range(len(self.routing_mat[layer_idx2])):
                        name2 = self.routing_mat[layer_idx2][each_layer_idx2][0]
                        if name1 == name2: continue
                        R2 = self.routing_mat[layer_idx2][each_layer_idx2][1]
                        angle2 = self.routing_mat[layer_idx2][each_layer_idx2][2]
                        distance = int(R1 ** 2 + R2 ** 2 - 2 * R1 * R2 * math.cos(math.fabs(angle1 - angle2)))
                        if distance < max_distance:
                            pt_dis = {str(name2): distance}
                            point_all_dis = dict(point_all_dis, **pt_dis)
                # one_layer_distance.append(point_all_dis)
                pt_all_dis = {str(name1): point_all_dis}
                one_layer_distance = dict(one_layer_distance, **pt_all_dis)
            all_layer_distance.append(one_layer_distance)
        self.routing_mat_price = all_layer_distance
        pass

    ''' 计算层间节点连接 '''
    def compute_pt_to_connectedLayer_pt_distance(self, max_distance=1000):
        all_layer_distance = []
        for layer_idx in range(len(self.routing_mat)):  # 每一层
            # one_layer_distance = []
            one_layer_distance = {}
            for each_layer_idx in range(len(self.routing_mat[layer_idx])):  # 层内点
                name1 = self.routing_mat[layer_idx][each_layer_idx][0]
                R1 = self.routing_mat[layer_idx][each_layer_idx][1]
                angle1 = self.routing_mat[layer_idx][each_layer_idx][2]
                point_all_dis = {}

                start = layer_idx-1 if layer_idx-1>=0 else 0
                end = layer_idx+1 if layer_idx+1<len(self.routing_mat) else layer_idx
                for layer_idx2 in range(start, end+1):
                    for each_layer_idx2 in range(len(self.routing_mat[layer_idx2])):
                        name2 = self.routing_mat[layer_idx2][each_layer_idx2][0]
                        if name1 == name2: continue
                        R2 = self.routing_mat[layer_idx2][each_layer_idx2][1]
                        angle2 = self.routing_mat[layer_idx2][each_layer_idx2][2]
                        distance = int(R1 ** 2 + R2 ** 2 - 2 * R1 * R2 * math.cos((angle1 - angle2)/180*math.pi))  #  math.fabs
                        # print(name1, '---', name2, ':', distance)
                        if distance < max_distance:
                            pt_dis = {str(name2): distance}
                            point_all_dis = dict(point_all_dis, **pt_dis)
                # one_layer_distance.append(point_all_dis)
                pt_all_dis = {str(name1): point_all_dis}
                one_layer_distance = dict(one_layer_distance, **pt_all_dis)
            all_layer_distance.append(one_layer_distance)
        self.routing_mat_price = all_layer_distance
        pass
    pass


''' 定义网络路由节点对应的处理单元（捆绑）'''  # Routing_Node_CPU
class Routing_Points_CPU():
    def __init__(self, mat:Routing_general, ThreadPool:ThreadPool, num_class=5, max_cost=500):
        self.routing_mat = []
        all_node_cpu_dict = {}
        for layer_idx, layer in enumerate(mat.routing_mat):
            # layer_idx += 1  ## 不能等于 0
            layer_idx = layer_idx*2 if layer_idx!=0 else 1    ## 层与层之间节点的算力水平差距
            # self.routing_mat.append((layer[:,0]))  #  np.array .tolist()
            # print(layer)
            for node_idx, node in enumerate(layer):
                rate = 1e-3*5
                node_cpu = Routing_Node_CPU(id=(node[0]), num_class=num_class, generate_rate=rate/layer_idx*1.0,
                                            recv_rate=rate/layer_idx*100,   ## 控住节点性能
                                            processing_rate=rate/layer_idx*3, max_data_size=5,
                                            gene_buf=12, recv_buf=12,  ## 设置节点缓存空间大小
                                            build_Thread=ThreadPool)
                # node_cpu.node_general_data_thread()
                # print('finish building bode cpu:', node[0])
                node_cpu_dict = {str(node[0]): node_cpu}
                all_node_cpu_dict = dict(all_node_cpu_dict, **node_cpu_dict)
                # node_cpu
        self.all_node_cpu_dict = all_node_cpu_dict
        for layer in mat.routing_mat_price:  ## 进入层内 dict
            # layer = dict()
            for nodes_in_layer in layer.keys():  ## 遍历层内节点
                node_connected_cpu = {}
                node_connected_cost = {}
                # print('eachlayer:', nodes_in_layer,  layer[nodes_in_layer])
                for nodes_connectes_dict in layer[nodes_in_layer]:  ## 遍历每一个节点的可连接节点
                    # print('connected node in layer:', nodes_connectes_dict, layer[nodes_in_layer][nodes_connectes_dict])
                    connect_cost = layer[nodes_in_layer][nodes_connectes_dict]
                    cost = {'ori': connect_cost}
                    for v in range(num_class):
                        co_class = {str(v): max_cost/2}
                        cost = dict(cost, **co_class)
                    node_cost = {nodes_connectes_dict: cost}  # 重新定义成本
                    node_connected_cost = dict(node_connected_cost, **node_cost)  # 各节点能连接的点的通信成本独立打包

                    node_cpu = {nodes_connectes_dict: all_node_cpu_dict[nodes_connectes_dict]}
                    node_connected_cpu = dict(node_connected_cpu, **node_cpu)  # 各节点能连接的点的发送地址独立打包 发给这个节点
                all_node_cpu_dict[nodes_in_layer].define_node_connected(cpu_dict=node_connected_cpu, cost_dict=node_connected_cost)
                time.sleep(1e-7)
        pass




if __name__ == '__main__':
    '''定义路由网络模型，网络节点呈扇形布置，云层在圆心处，其他层分布在不同半径圆上，层内节点随机分布在一定角度范围内'''
    layer_num = 4  # 定义层数
    mul_layer_radius = [ 0, 10, 20, 30, 40, 50, 60, 70, 80, 90]  # 定义各层节点所在圆的半径（距离云的距离）
    mul_layer_angle = [[60, 120], [30, 150], [30, 150], [30, 150], [30, 150], [30, 150],
                       [30, 150], [30, 150], [30, 150], [30, 150]]  # 定义云上各节点的方位分布范围（角度范围）
    mul_layer_num = [ 1, 30, 30, 4, 8, 10, 14, 18, 16, 14]  # 定义各层中节点的数量 在node_cost_sdjust_on_all中，限制了每层节点数量<99
    max_cost = 10000   ##限制初始状态的最大通信成本
    Routing_Mat = Routing_general(layer_num, mul_layer_radius=np.array(mul_layer_radius)*5,
                                  mul_layer_angle=mul_layer_angle, mul_layer_num=np.array(mul_layer_num))
    print(len(Routing_Mat.routing_mat), len(Routing_Mat.routing_mat[2]))
    # print((Routing_Mat.routing_mat))
    # Routing_Mat.compute_pt_to_all_pt_distance(1000)
    Routing_Mat.compute_pt_to_connectedLayer_pt_distance(max_cost)
    # print(Routing_Mat.routing_mat_price)
    for layer in Routing_Mat.routing_mat_price:
        print(layer)
    exit()


    num_thread = np.array(mul_layer_num)[:layer_num].sum()*4
    # print('thread num:', np.array(mul_layer_num)[:layer_num].sum(), num_thread)
    ThreadPool = ThreadPool(num_thread, real_thread=True)
    Routing_Pts_cpu = Routing_Points_CPU(mat=Routing_Mat, ThreadPool=ThreadPool, num_class=1, max_cost=max_cost )
    # del Routing_Mat
    #
    # ThreadPool.node_recv_run(Routing_Pts_cpu.all_node_cpu_dict['203'].node_recv_data_thread, args=(None,))

    # for i in range(60):
        # print('Now thread num=', len(ThreadPool.thread_list_general.generate_list),
        #                           len(ThreadPool.thread_list_send.generate_list),
        #                           len(ThreadPool.thread_list_recv.generate_list),
        #                           len(ThreadPool.thread_list_processing.generate_list))
        # print('Now thread alive=', ThreadPool.thread_list_general.generate_list[3].is_alive(),)
              # ThreadPool.thread_list_send.generate_list[1].is_alive(),
              # ThreadPool.thread_list_recv.generate_list[1].is_alive(),
              # ThreadPool.thread_list_processing.generate_list[1].is_alive())
        # time.sleep(2)

    from utils import visualization as vshow

    Data_show = vshow.SHOW_nodes_data_cv(Routing_Mat.routing_mat)
    # Data_show.node_data_show_figure('203', sign='send', dat='{"101": dd,geg,ewe,r,5,e,re,t,5f6sd5f6s5f6d565,56,56j,64,hj5,46hj6,5hj,er')
    # Data_show.node_data_show_figure('201', sign='recv', dat='{"101": dd,geg,ewe,r,5,e,re,t,er')
    Data_show.start_draw_nodes_data_dynamically_thread()
    a = 0
    for i in range(90):
        # self_id = '20' + str(i % 3 + 1)
        # # np.random.seed(np.random.randint(0,50000))
        # b = np.random.randint(0, 5000)
        # while b == a: b = np.random.randint(0, 5000)
        # a = b
        # name = '30' + str(a % 6 + 1)
        # da = {self_id: {'connect': name, 'class': '{}{}'.format(i, np.random.randint(0, 500)),
        #                 'recv_res': i * 20 % 1000, 'generate_res': i * 20 % 1000}}
        # vshow.qimg_add_data(dat=da)
        time.sleep(2)

    Data_show.close__draw_nodes_data_dynamically_thread()

    # ThreadPool.close_wait_Thread_end()
    ThreadPool.stop_Thread_now()
    for node_cpu in Routing_Pts_cpu.all_node_cpu_dict.values():
        node_cpu.close_all_thread()
    exit()