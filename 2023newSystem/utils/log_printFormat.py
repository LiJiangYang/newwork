# 程序运行过程打印输出的TXT文件路径（包含文件名）
import csv
import os
import numpy as np


# outprintTxt = "./imagefilelists"

def fprint(outprintTxt, mode, *data0):
    path = os.path.dirname(outprintTxt)  # 获取TXT文件的父级目录
    if os.path.isdir(path) != True:  # 目录不存在就创建
        os.makedirs(path)
    f = open(outprintTxt, mode)  # 以TXT文件末位继续打印内容的方式打开TXT文件
    for data in data0:  # 轮遍所有内容
        if type(data) == type('s'):
            f.write(data)
        else:
            f.write(str(data))
        f.write(' ')  # 以空格间隔每个内容
    f.write('\n')  # 打印完成将帧移到下一行
    f.close()  # 关闭文档


'''将多个数据保存在一个 csv 文件： '''
def node_record_alldata(filenamme, data, header=None, write_header=False):
    headers = ['record time', 'gener time', 'old', 'new', 'odas', 'back nodes and time', 'up nodes and time']
    if not header: header = list(data.keys())         # headers
    with open(filenamme, 'a', newline='') as fp:
        writer = csv.DictWriter(fp, header, restval='')
        if not write_header:
            writer.writerow(data)
        else:
            writer.writeheader()


'''将多个数据保存在一个 csv 文件： '''
def node_record_alldatawriteheader(filenamme, header=None):
    headers = ['record time', 'gener time', 'old', 'new', 'odas', 'back nodes and time', 'up nodes and time']
    if not header: header = headers
    with open(filenamme, 'w', newline='') as fp:
        writer = csv.DictWriter(fp, header, restval='')
        writer.writeheader()



def read_csv_file(path):
    global data
    with open(path,'r') as fp:
        # read = csv.reader(fp)
        read = csv.DictReader(fp)

        for da in read:
            # daa = {na: dat for na in name for dat in da.values()}
            daa = [ds for ds in da.values()]
            print(daa)

            data=daa
        # data = dict(data, **daa)
    return data



"""对工程文件夹内的数据txt文件进行批量处理：修改test的第三列数据"""
