import numpy as np
import sys
'''向上层传递（编号小==上层）'''
'''MDAR算法开'''
def node_optimal_to_up0(self_name, idx_class, mat_cost:dict=None):
    global best_choice
    # print('optism:', self_name, ':', mat_cost)
    min_cost = float('inf')  # ((0xffffffff)*1.0)
    best_choice = None
    for name in mat_cost.keys():
        # print('optism:', self_name, 'aver:', name)
        # if int(name[0]) < int(self_name[0]):  ## 传给下面的层
        if int(name[0]) +1 == int(self_name[0]):  ## 传给下1层
            # mat_cost[name] = [初始距离成本, 各类数据成本...]
            if idx_class in mat_cost[name].keys():
                cost = mat_cost[name]['ori']+mat_cost[name][idx_class]   ## 同类数据可能暴增，其他类可能空闲
                # print('optism:', self_name, '[{}]cost:'.format(name), cost)
            else:
                co = np.array([mat_cost[name][idx] for idx in mat_cost[name].keys()])  ##同类数据可能暴增，其他类可能空闲
                cost = mat_cost[name]['ori']+np.min(co)  ## 取全局最小
                # print('optism:', self_name, '[{}]total cost:'.format(name), cost)
            if float(min_cost) >= float(cost):
                min_cost = float(cost)
                best_choice = name
    # print('optism res:', self_name, '[{}]total min_cost:'.format(best_choice), min_cost)
    return best_choice


'''MDAR算法开'''
def mode_optimal_smart(self_name, idx_class, mat_cost:dict=None, target=None, isMDAR=True):
    if target in mat_cost.keys(): return target
    if target is not None:
        if int(target[:-7]) > int(self_name[:-7]):  ## 目标是向下
            back = mode_optimal_to_down(self_name, idx_class, mat_cost, target, isMDAR)

        else:
            back = mode_optimal_to_up(self_name, idx_class, mat_cost, target, isMDAR)

    else:
        back = mode_optimal_to_up(self_name, idx_class, mat_cost, target, isMDAR)

    # if back not in mat_cost.keys():
    #     print('====mode_optimal_smart [{}]===='.format('sign'), self_name, back, target, mat_cost)

    return back
    pass


'''MDAR算法开'''
def mode_optimal_to_up(self_name, idx_class, mat_cost:dict=None, target=None, isMDAR=True):
    # global best_choice, min_cost
    # print('optism:', self_name, ':', mat_cost)
    min_cost = float('inf')  # ((0xffffffff)*1.0)
    best_choice = None
    if target is not None:
        if target in mat_cost.keys():
            # print('mode_optimal_to_up:', self_name, mat_cost.keys())
            return target
    for name in mat_cost.keys():
        # print('optism:', self_name, 'aver:', name)
        # if int(name[0]) < int(self_name[0]):  ## 传给下面的层
        if int(name[:-7]) + 1 == int(self_name[:-7]):  ## 传给下1层
            # mat_cost[name] = [初始距离成本, 各类数据成本...]
            if idx_class in mat_cost[name].keys() and isMDAR:
                cost = mat_cost[name]['ori'] + mat_cost[name][idx_class]  ## 同类数据可能暴增，其他类可能空闲
                # print('optism:', self_name, '[{}]cost:'.format(name), cost)
            else:
                co = np.array([mat_cost[name][idx] for idx in mat_cost[name].keys()])  ##同类数据可能暴增，其他类可能空闲
                cost = mat_cost[name]['ori'] + np.min(co)  ## 取全局最小
                # print('optism:', self_name, '[{}]total cost:'.format(name), cost)
            if float(min_cost) > float(cost):
                min_cost = float(cost)
                best_choice = name
                # print('best_choice==', best_choice, name)
    # print('optism res:', self_name, '[{}]total min_cost:'.format(best_choice), min_cost)
    # if best_choice not in mat_cost.keys():
    #     print('====mode_optimal_smart [{}]===='.format('up'), self_name, best_choice, target, mat_cost)
    return best_choice


'''MDAR算法开'''
def mode_optimal_to_down(self_name, idx_class, mat_cost:dict=None, target=None, isMDAR=True):
    # global best_choice, min_cost
    # print('optism:', self_name, ':', mat_cost)
    min_cost = float('inf')  # ((0xffffffff)*1.0)
    best_choice = None
    if target is not None:
        if target in mat_cost.keys():
            # print('mode_optimal_to_down:', self_name, mat_cost.keys())
            return target
    for name in mat_cost.keys():
        # print('optism:', self_name, 'aver:', name)
        # if int(name[0]) < int(self_name[0]):  ## 传给下面的层
        if int(name[0]) - 1 == int(self_name[0]):  ## 传给下1层
            # mat_cost[name] = [初始距离成本, 各类数据成本...]
            if idx_class in mat_cost[name].keys() and isMDAR:
                cost = mat_cost[name]['ori'] + mat_cost[name][idx_class]  ## 同类数据可能暴增，其他类可能空闲
                # print('optism:', self_name, '[{}]cost:'.format(name), cost)
            else:
                co = np.array([mat_cost[name][idx] for idx in mat_cost[name].keys()])  ##同类数据可能暴增，其他类可能空闲
                cost = mat_cost[name]['ori'] + np.min(co)  ## 取全局最小
                # print('optism:', self_name, '[{}]total cost:'.format(name), cost)
            if float(min_cost) >= float(cost):
                min_cost = float(cost)
                best_choice = name
    # print('optism res:', self_name, '[{}]total min_cost:'.format(best_choice), min_cost)
    # if self_name == best_choice: print('mode_optimal_to_up:', self_name, mat_cost.keys())
    return best_choice








