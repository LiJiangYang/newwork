import ctypes
import inspect
import queue
import threading
import time
import contextlib


class AAA:
    def __init__(self):
        pass

    def acquire(self):
        return True

    def release(self):
        return True


A = threading.Lock()


# B = threading.Lock()


class ThreadPool_one_class(object):
    def __init__(self, max_num, real_thread=True):
        self.StopEvent = object()
        self.mux_queue = threading.Lock()  # AAA()          #  A  #
        self.mux_threead_list = threading.Lock()  # AAA()     #   A  #

        self.timeout = 1  # 1e-1
        self.q = queue.Queue(max_num+100)  # 最多创建的线程数（线程池最大容量）
        self.max_num_thread = max_num

        self.real_thread = real_thread
        self.terminal = False  # 如果为True 终止所有线程，不在获取新任务
        self.generate_list = []  # 真实创建的线程列表
        self.free_list = []  # 空闲线程数量

    def run(self, func, args, callback=None, name=None):
        """
        线程池执行一个任务
        :param name: named thread
        :param func: 任务函数
        :param args: 任务函数所需参数
        :param callback: 任务执行失败或成功后执行的回调函数，回调函数有两个参数1、任务函数执行状态；2、任务函数返回值（默认为None，即：不执行回调函数）
        :return: 如果线程池已经终止，则返回True否则None
        """

        w = (func, args, callback,)  # 把参数封装成元祖
        self.q.put(w)  # 添加到任务队列

        if len(self.generate_list) < self.max_num_thread:
            self.generate_thread(name=name)  # 创建线程

    def generate_thread(self, name=None):
        """
        创建一个线程
        """
        if self.real_thread:
            t = threading.Thread(target=self.call, name=name)
            t.start()
        else:
            if len(self.generate_list) == 0:
                t = threading.Thread(target=self.call, name=name)
                t.start()
        # print('======t========', name)


    def call(self):
        """
        循环去获取任务函数并执行任务函数
        """
        current_thread = threading.currentThread()  # 获取当前线程
        if self.q.qsize() <= 0:
            print('\033[31m thread out empty:', current_thread.name, '\033[0m')
            return
        # print('\033[31m thread start!!', current_thread.name, '\033[0m')

        self.generate_list.append(current_thread)  # 添加到已经创建的线程里

        timeout = self.timeout
        event = self.q.get(timeout=timeout)  # 取任务并执行

        while event != self.StopEvent:  # 是元组=》是任务；如果不为停止信号  执行任务

            func, arguments, callback = event  # 解开任务包； 分别取出值
            # try:
            result = func(real_thread=self.real_thread, *arguments)  # *arguments运行函数，把结果赋值给result
            status = True  # 运行结果是否正常
            # except Exception as e:
            #     status = False  # 表示运行不正常
            #     result = e  # 结果为错误信息
            #     print('\033[31m thread target ERROR:', e, '\033[0m')
            #     self.mux_queue.acquire()
            #     self.q.put(event)  # 出错了重新运行
            #     self.mux_queue.release()

            if callback is not None:  # 是否存在回调函数
                try:
                    callback(status, result)  # 执行回调函数
                except Exception as e:
                    print('\033[31m thread callback ERROR:', e, '\033[0m')
                    pass

            if self.terminal:  # 默认为False，如果调用terminal方法
                event = self.StopEvent  # 等于全局变量，表示停止信号
                # break
            else:
                # with self.worker_state(self.free_list, current_thread):
                if self.q.qsize() > 0:
                    event = self.q.get(timeout=timeout)
                else:
                    event = self.StopEvent
                    # break
                    pass
            if not self.real_thread:
                self.mux_queue.acquire()
                self.q.put(event, timeout=timeout)  # 重新添加到任务队列， 循环执行
                self.mux_queue.release()

        self.mux_threead_list.acquire()
        self.generate_list.remove(current_thread)  # 如果收到终止信号，就从已经创建的线程列表中删除
        self.mux_threead_list.release()
        print('\033[31m thread out:', current_thread.name, '\033[0m')

    def close(self):  # 终止线程
        num = len(self.generate_list)  # 获取总共创建的线程数
        self.mux_queue.acquire()
        while num:
            self.q.put(self.StopEvent, timeout=self.timeout)  # 添加停止信号，有多少线程添加多少表示终止的信号
            num -= 1
        self.mux_queue.release()
        while True:
            isalive = False
            for thre in self.generate_list:
                if thre.isAlive(): isalive=True
            if not isalive: break

    '''强制关闭线程'''

    @staticmethod
    def _async_raise(tid, exctype):
        """raises the exception, performs cleanup if needed"""
        tid = ctypes.c_long(tid)
        if not inspect.isclass(exctype):
            exctype = type(exctype)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
        if res == 0:
            raise ValueError("invalid thread id")
        elif res != 1:
            # """if it returns a number greater than one, you're in trouble,
            # and you should call it again with exc=NULL to revert the effect"""
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise SystemError("PyThreadState_SetAsyncExc failed")

    '''强制关闭所有线程'''

    def stop_all_thread(self):
        for threa in self.generate_list:
            try:
                self._async_raise(threa.ident, SystemExit)
                # self.close()
            except:
                pass

    ''' 等待线程自动终止， 不再添加超出线程数量的任务'''

    def terminate(self):  # 终止线程（清空队列）
        self.terminal = True  # 把默认的False更改成True
        while self.generate_list != []:  # 如果有已经创建线程存活
            self.mux_queue.acquire()
            self.q.put(self.StopEvent)  # 有几个线程就发几个终止信号
            self.mux_queue.release()
            time.sleep(1e-5)
        # print('all out!')
        self.mux_queue.acquire()
        self.q.empty()  # 清空队列
        self.mux_queue.release()

    @contextlib.contextmanager
    def worker_state(self, state_list, worker_thread):
        state_list.append(worker_thread)
        try:
            yield
        finally:
            state_list.remove(worker_thread)


class ThreadPool:
    def __init__(self, max_num=20, real_thread=True):
        # super().__init__(max_num, real_thread)
        num = int(max_num / 4) + 1
        # print('num=', num)
        self.thread_list_generate = ThreadPool_one_class(num, real_thread)
        self.thread_list_send = ThreadPool_one_class(num, real_thread)
        self.thread_list_recv = ThreadPool_one_class(num, real_thread)
        self.thread_list_processing = ThreadPool_one_class(num, real_thread)

    def node_generate_run(self, func, args, callback=None, name=''):
        self.thread_list_generate.run(func, args, callback, name='gener' + name)
        # print('total thread num=', len(self.thread_list_generate.generate_list),
        #       len(self.thread_list_send.generate_list),
        #       len(self.thread_list_recv.generate_list),
        #       len(self.thread_list_processing.generate_list))
        pass

    def node_send_run(self, func, args, callback=None, name=''):
        self.thread_list_send.run(func, args, callback, name='send' + name)
        pass

    def node_recv_run(self, func, args, callback=None, name=''):
        self.thread_list_recv.run(func, args, callback, name='recv' + name)
        pass

    def node_processing_run(self, func, args, callback=None, name=''):
        self.thread_list_processing.run(func, args, callback, name='proc' + name)
        pass

    def close_wait_Thread_end(self):
        self.thread_list_generate.close()
        self.thread_list_send.close()
        self.thread_list_recv.close()
        self.thread_list_processing.close()
        pass

    def stop_Thread_now(self):
        self.thread_list_generate.stop_all_thread()
        self.thread_list_send.stop_all_thread()
        self.thread_list_recv.stop_all_thread()
        self.thread_list_processing.stop_all_thread()
        # self.thread_list_processing.generate_list
        print(' all thread stop!')
        pass

    def __del__(self):
        self.thread_list_generate.stop_all_thread()
        self.thread_list_send.stop_all_thread()
        self.thread_list_recv.stop_all_thread()
        self.thread_list_processing.stop_all_thread()

        print(' all thread stop!')
        pass


num = [0]


def work(i=0, real_thread=True):
    mux = threading.Lock()
    if mux.acquire():
        # print('mux success')
        pass
    # else:
    # print('mux fail')
    for y in range(2000000):
        num[0] += 1
        # print(i, ':', num[0])
        # time.sleep(0.05)

        # time.sleep(2)
    print(i, ':', num[0])
    mux.release()


class TEST:
    def __init__(self):
        self.pool = ThreadPool(500 * 4, True)
        self.mux = threading.Lock()
        for item in range(2):
            self.pool.node_recv_run(func=self.work2, args=(item,))
            # time.sleep(0.01)
            pass

    def work2(self, i=0, real_thread=True):
        mux = self.mux
        if mux.acquire():
            # print('mux success')
            pass
        # else:
        # print('mux fail')
        for y in range(2000000):
            num[0] += 1
            # print(i, ':', num[0])
            # time.sleep(0.05)

            # time.sleep(2)
        print(i, ':', num[0], 'real_thread:', real_thread)
        mux.release()
        return 0


if __name__ == '__main__':
    # pool = ThreadPool(500*4, True)
    # for item in range(2):
    #     pool.node_recv_run(func=work, args=(item,))
    #     # time.sleep(0.01)
    #     pass
    # 将任务放在队列中
    #      着手开始处理任务
    #         - 创建线程
    #                 - 有空闲线程，择不再创建线程
    #                 - 不能高于线程池的限制
    #                 - 根据任务个数判断
    #         - 线程去队列中取任务
    print('close all')
    # pool.close()
    # pool.terminate()

    a = TEST()
    # time.sleep(10)

    exit()
    aa = threading.Thread(target=work, args=(3, True))
    aa.start()

    aa.join()
    time.sleep(2)
    print('restart..')
    aa.run()
