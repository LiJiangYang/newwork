''' 使用Bdir功能 '''
is_use_Bdir = True
''' 使用AERO功能 '''  # AER开的时候，Bdir须强制打开
is_use_AER = True

''' 突发流量阀值设置项 设置值为对应层节点process速率的倍率'''
tm_capacity_s: float = 100.0  # 数据分流时间阀值。 建议：综合考虑下方设置的节点运行速度，合理设置该时间区间
alarm_cap = [10,9,10,10,10]  # 时间阀值内，接收的数据条数（按条计，不论每条信息的长短）
aer_accelerate_cap: int = 15  # AER协同加速：共同加速阈值基础值
''' Assistant节点的数量，AER为True时会用到。使用协同打包，节点向同层节点求助 '''
assi_nodes_num: int = 2  # 限制每次的求助节点数量（协同打包的节点数量））

''' 数据打包（大包）：数据分流数据包大小限制（按条数）'''
package_size: int = 6  # 值为正数：表示每次强制打包特定尺寸（除非打包时间超时）；负数：根据目标节点带宽，智能调整
''' 协同打包(小包)：此为小数据包组装完成时大小 '''
small_package_size: int = 3  # 正数：每次强制打包特定尺寸（超时被打断）；负数：根据目标节点带宽，智能调整

''' 每个打包（大小包）的最长组装时间   设置值为对应层节点process速率的倍率'''
max_pack_time_s = 100.0  # 建议考虑节点的运行速率


# 以下为旧系统设置项

''' 速度基数 越大越慢 '''
speed_base = 1e-3
''' 数据产生速度（越小越快） '''
generate_speed = 1.0
generate_buffer = 20
''' 数据上传 速度（越小越快） '''
send_speed = 0.2
send_buffer = 20
''' 数据接收速度（越小越快） '''
receive_speed = 0.2
receive_buffer = 30
''' 数据处理速度（越小越快） '''
processing_speed = 1.0

''' 各层节点数量(第一层为cloud，最后层为IoT/user） '''
each_layer_nodes_num = [1, 3, 4, 6, 40]

''' 不同层CPU算力差值: 倍数关系（非指数级）(值越大，运算越慢） '''
diff_layers_cpu_performance = [1, 50, 80, 52, 40, 50, 60, 70, 80, 90, 100]

''' 定义各层距离cloud节点的半径距离 '''
diff_layer_radius = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]  # 定义各层节点所在圆的半径（距离云的距离）
''' 定义各层距离cloud节点的角度分布 '''
diff_layer_angle = [[60, 120], [30, 150], [30, 150], [30, 150], [30, 150], [30, 150],
                    [30, 150], [30, 150], [30, 150], [30, 150]]  # 定义云上各节点的方位分布范围（角度范围）

''' 设置最大距离通信成本，超出该值的节点无法建立连接 '''
max_distance_cost = 200

''' 同层CPU算力差值范围 倍数关系（非指数级）(值越大，运算越慢，1：为该层初始水平） '''
one_layer_cpu_performance = [0.5, 1.5]

''' 产生的数据总量(字节大小） '''
generate_totalSize = 1000

''' 不同层产生的数据总量: 倍数关系（非指数级） '''
diff_layer_generate_totalSize = None  ## 默认与 diff_layers_cpu_performance 一致

''' CPU算力（延时）公式 '''
get_delay_time = lambda layer_idx, rand_perf: speed_base * layer_idx * rand_perf

''' MDAR算法开关 '''
MDAR_BUTTON = True

''' ODAS 开关 '''
ODAS_BUTTON = True
ODAS_rate = 0.5

''' 负载均衡开关 '''
Balance = True

''' 数据种类数量 '''
data_class_num = 10

''' 相似度范围 '''
similar_range = [0, 1]

''' 数据保存文件名 '''
save_path = './log/'
