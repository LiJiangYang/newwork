import csv
import ast
import os

import routing_config as cf

node_layer_num = cf.each_layer_nodes_num
layer_num = len(node_layer_num)
mdar = cf.MDAR_BUTTON


def clear_data():
    for e in range(1):
        # k的数量是层数-1，他的值是固定的
        k = len(node_layer_num)-1
        avg_time = 0
        avg_hop = 0
        avg_back_dis = 0
        avg_up_dis = 0
        # 这里w的数量是rang(IOT层节点数)，因为读取数据只需要在IOT层的log中进行读取
        for w in range(node_layer_num[(layer_num-1)]):
            file_name = "./log/"+str(((k + 1) * (10**7) + (w + 1))) + "_node_log.csv"
            # print(file_name)
            # print(type(file_name))
            with open(file=file_name, mode="r") as f:
                read = csv.reader(f)
                #这里得到row直接把当前csv文件中所有内容以列表形式存放在里面
                row = [i for i in read]

            for id, i in enumerate(row):
                if id == 0:
                    sum_back_hop = 0
                    sum_up_hop = 0
                    sum_back_time = 0
                    sum_up_time = 0
                    sum_time = 0
                    sum_up_dis = 0
                    sum_back_dis = 0
                    sum_data = 0
                    back_time = 0
                    up_time = 0
                    continue
                sum = 0
                if id == 1:
                    #这里的i[1]是第一行数据的gener time
                    gener_time = float(i[1])

                #这里的len(row)-1是数据的行数，这里id定位到最后一行数据
                if id == len(row) - 1:
                    record_time = float(i[0])
                    old = int(i[2])
                    new = int(i[3])
                    odas = float(i[4])
                    sum_data = old + new
                    sum_time += (record_time - gener_time)
                    n1 = id

                back_nodes_and_time1 = i[5]
                up_nodes_and_time1 = i[6]
                back_nodes_and_time = ast.literal_eval(back_nodes_and_time1)
                up_nodes_and_time = ast.literal_eval(up_nodes_and_time1)

                back_dis = 0
                up_dis = 0
                back_time = 0
                up_time = 0

                if mdar == True:
                    back_hop = len(back_nodes_and_time)-1
                    up_hop = len(up_nodes_and_time)-1
                else:
                    group = []
                    group1 = []
                    for m in back_nodes_and_time:
                        group.append(m[0])
                    group = list(set(group))
                    back_hop = len(group)-1

                    for m in up_nodes_and_time:
                        group1.append(m[0])
                    group1 = list(set(group1))
                    up_hop = len(group1)-1

                sum_back_hop += back_hop
                sum_up_hop += up_hop

                for id, j in enumerate(back_nodes_and_time):
                    back_dis += int(j[1])
                    if id == 0:
                        back_time_begin = float(j[2])
                    if id == len(back_nodes_and_time) - 1:
                        back_time_end = float(j[2])

                back_time = back_time_end - back_time_begin
                sum_back_time += back_time
                sum_back_dis += back_dis

                for id, j in enumerate(up_nodes_and_time):
                    up_dis += int(j[1])
                    if id == 0:
                        up_time_begin = float(j[2])
                    if id == len(up_nodes_and_time) - 1:
                        up_time_end = float(j[2])

                up_time = up_time_end - up_time_begin
                sum_up_time += up_time
                sum_up_dis += up_dis


            sum_up_dis = sum_up_dis/n1
            sum_back_dis = sum_back_dis/n1
            sum_back_hop = sum_back_hop/n1
            sum_up_hop = sum_up_hop/n1
            avg_time = avg_time+sum_time/node_layer_num[(layer_num-1)]
            avg_hop = avg_hop+sum_up_hop/node_layer_num[(layer_num-1)]
            avg_back_dis = avg_back_dis+sum_up_dis/node_layer_num[(layer_num-1)]
            avg_up_dis = avg_up_dis+sum_back_dis/node_layer_num[(layer_num-1)]

            if not os.path.exists("clear_data"):
                os.mkdir("clear_data")  # 如果不存在这个logs文件夹，就自动创建一个
            with open("./clear_data/test.csv", "a", newline="") as csvfile:
                writer = csv.writer(csvfile)
                # 先写入columns_name
                if w == 0:
                    writer.writerow(
                        ["sum_time", "sum_up_time", "sum_back_time", "sum_up_hop", "sum_back_hop", "sum_data", "sum_up_dis","sum_back_dis","avg_time","avg_hop","avg_back_dis","avg_up_dis"])
                # 写入多行用writerows
                writer.writerows(
                    [[sum_time, sum_up_time, sum_back_time, sum_up_hop, sum_back_hop, sum_data, sum_up_dis, sum_back_dis,avg_time,avg_hop,avg_back_dis,avg_up_dis]])
    print("数据整理完成")

def clear_data2():

    for e in range(layer_num):
        sum_data = 0
        for w in range(node_layer_num[e]):
            file_name = "./log/"+str((e+1)*(10**7)+(w+1)) + "_node_log.csv"
            with open(file=file_name, mode="r") as f:
                read = csv.reader(f)
                row = [i for i in read]

                for id, i in enumerate(row):
                    if id == 0:
                        node_data = 0
                        ave_data = 0
                        odas_data = 0
                        continue
                    if id == len(row)-1:
                        odas_data = float(i[4])/(len(row)-1)
                        if e==4:
                            node_data = (int(i[2]) + int(i[3])- float(i[4]))*2/1000
                            sum_data += (int(i[2]) + int(i[3])-float(i[4]))*2/1000
                        else:
                            node_data = (int(i[2]) + int(i[3]) - float(i[4]))/1000
                            sum_data += (int(i[2]) + int(i[3]) - float(i[4]))/1000
                        ave_data = node_data/(len(row)-1)

                if not os.path.exists("clear_data"):
                    os.mkdir("clear_data")  # 如果不存在这个logs文件夹，就自动创建一个
                with open("./clear_data/node_data.csv", "a", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    # 先写入columns_name
                    if e == 0:
                        writer.writerow(["node_data","ave_data","odas_data"])
                        # 写入多行用writerows
                    writer.writerows([[node_data,ave_data,odas_data]])

        with open("./clear_data/sum_data.csv", "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            # 先写入columns_name
            if e == 0:
                writer.writerow(["sum_data"])
                # 写入多行用writerows
            writer.writerows([[sum_data]])

if __name__=="__main__":
    # 整合IOT层数据
    clear_data()
    # 整合各层流量
    clear_data2()