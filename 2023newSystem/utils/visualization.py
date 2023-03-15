import time
import queue
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.lines as line
import math
import threading

# from matplotlib.ticker import MultipleLocator
import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg

enable_cv = False
try:
    import cv2 as cv

    enable_cv = True
except:
    enable_cv = False
    pass

qimg_data = queue.Queue(10000000)


def qimg_add_data(dat=None):
    if dat is None:
        return False
    # {self_id: {'connect': name, 'class': '2', 'recv_res': 23, 'generate_res': 65}}
    try:
        qimg_data.put(dat, timeout=1e-10)
    except: pass


class SHOW_nodes_data_cv:
    def __init__(self, mat):
        self.ori_img_background = 0  ## 黑:0  白: 255
        self.nodes_mat_show_img = np.full_like(np.zeros([1200, 2000, 3]), self.ori_img_background)
        self.nodes_data_show_img = np.full_like(np.zeros([200, 300, 3]), self.ori_img_background)  ## 内容不够显示，可以增加行数rows
        self.figSize = (1000, 600)  ##定义最终显示的图片大小行列刚好相反
        self.color_node_point = [255, 0, 0]
        self.color_node_name = [0, 0, 255]
        self.color_node_recv = [100, 0, 155]
        self.color_node_gene = [0, 100, 200]
        self.color_node_send = [50, 100, 0]

        self.node_history_data = {}  # 保存各节点前一次的画图信息
        self.keep_run = True  ## 动态画图线程控制。
        self.mux = threading.Lock()

        self.layers_position, _, self.node_pos_in_fig = self.calculate_routing_nodes_mat(mat)
        self.draw_mat_nodes()  ## 绘制节点二维空间布局图
        # print('self.max_radius:', self.max_radius)

        pass

    def calculate_routing_nodes_mat(self, mat):
        global radius
        layers_position = []
        layers_radius = []
        subplot = {}
        img = self.nodes_mat_show_img
        y_rows, x_cols = img.shape[:2]
        y_move_rate = 0.09  ## 画图点的上下留白
        max_radius = np.max(np.array(mat[len(mat) - 1][:, 1]))
        for l_idx, layer in enumerate(mat):
            one_layer = []
            # num_nodes = len(layer)
            for node_name_r_alp_idx, _ in enumerate(layer):
                name, radius, alp = layer[node_name_r_alp_idx, :]
                radius = radius / max_radius  # 归一化到半径为1的圆内
                x = radius * math.cos(alp / 180 * math.pi)
                y = radius * math.sin(alp / 180 * math.pi)
                x, y = int((1 + x) * x_cols / 2), int((y) * y_rows * (1 - y_move_rate * 2)) + int(y_rows * y_move_rate)
                node = [name, x, y]
                one_layer.append(node)
                pos = [x, y]
                # pos = [num_layers, num_nodes, node_name_r_alp_idx + 1 + (num_nodes * (num_layers - l_idx - 1))]
                subplot_pos = {str(name): pos}
                subplot = dict(subplot, **subplot_pos)
            layers_position.append(one_layer)
            layers_radius.append(radius)
        # print('layers_position:', layers_position)
        return layers_position, layers_radius, subplot

    def node_data_show_figure(self, name, sign='send', dat=None):
        if enable_cv:
            img = self.nodes_data_show_img.copy()
            y_rows, x_cols = img.shape[:2]

            size = 25
            fontSize = 0.6
            if sign == 'send':
                # 添加文字,第一个参数是x轴坐标，第二个参数是y轴坐标，以数据的刻度为基准
                # x, y = x_cols, y_rows
                cv.putText(img, str('send:'), org=(2, 12), fontFace=cv.FONT_HERSHEY_COMPLEX, fontScale=fontSize,
                           color=(0, 0, 255), thickness=1)
                idx = 0
                while len(dat) > size:
                    cv.putText(img, str(dat[:size]), org=(10, 30 + idx * 22), fontFace=cv.FONT_HERSHEY_COMPLEX,
                               fontScale=fontSize,
                               color=(255, 255, 0), thickness=1)
                    idx += 1
                    dat = dat[size:]
                cv.putText(img, str(dat[:size]), org=(10, 30 + idx * 22), fontFace=cv.FONT_HERSHEY_COMPLEX,
                           fontScale=fontSize,
                           color=(255, 255, 0), thickness=1)
            else:
                # 添加文字,第一个参数是x轴坐标，第二个参数是y轴坐标，以数据的刻度为基准
                cv.putText(img, str('recv:'), org=(2, int(y_rows / 2)), fontFace=cv.FONT_HERSHEY_COMPLEX,
                           fontScale=fontSize,
                           color=(0, 0, 255), thickness=1)
                idx = 0
                while len(dat) > size:
                    cv.putText(img, str(dat[:size]), org=(10, int(y_rows / 2) + 20 + idx * 22),
                               fontFace=cv.FONT_HERSHEY_COMPLEX,
                               fontScale=fontSize,
                               color=(255, 255, 0), thickness=1)
                    idx += 1
                    dat = dat[size:]
                cv.putText(img, str(dat[:size]), org=(10, int(y_rows / 2) + 20 + idx * 22),
                           fontFace=cv.FONT_HERSHEY_COMPLEX, fontScale=fontSize,
                           color=(255, 255, 0), thickness=1)
            cv.imshow(str(name), img)
            cv.waitKey(5)  # 10**3*
            # cv.waitKey(0)
        pass

    def draw_mat_nodes(self):
        if enable_cv:
            layers_position = self.layers_position
            img = self.nodes_mat_show_img
            # y_rows, x_cols = img.shape[:2]
            # y_move_rate =0.05
            for idx, one_layer in enumerate(layers_position):
                for node in one_layer:
                    # name, x, y = node[0], int((1 + node[1]) * x_cols / 2), int((node[2]) * y_rows*(1-y_move_rate*2))+int(y_rows*y_move_rate)
                    name, x, y = node[0], int(node[1]), int(node[2])
                    cv.circle(img, (x, y), radius=14, color=self.color_node_point, thickness=-1)  # plot nodes
                    # 添加文字,第一个参数是x轴坐标，第二个参数是y轴坐标，以数据的刻度为基准
                    cv.putText(img, str(name), org=(x - 33, y - 30), fontFace=cv.FONT_HERSHEY_COMPLEX, fontScale=1.2,
                               color=self.color_node_name, thickness=1)
            # cv.imshow('nodes_mat', img)
            # cv.waitKey(10)
            # cv.waitKey(0)
            cv.putText(img, str('recv'), org=(30, 30), fontFace=cv.FONT_HERSHEY_COMPLEX, fontScale=1.2,
                       color=self.color_node_recv, thickness=1)
            cv.putText(img, str('generate'), org=(30, 56), fontFace=cv.FONT_HERSHEY_COMPLEX, fontScale=1.2,
                       color=self.color_node_gene, thickness=1)
            cv.putText(img, str('send'), org=(30, 90), fontFace=cv.FONT_HERSHEY_COMPLEX, fontScale=1.2,
                       color=self.color_node_send, thickness=1)
            self.nodes_mat_show_img = img

    def draw_2_nodes_line(self, img, A_node, B_node, color):
        node = self.node_pos_in_fig[A_node]
        x1, y1 = int(node[0]), int(node[1])
        node = self.node_pos_in_fig[B_node]
        x2, y2 = int(node[0]), int(node[1])
        # cv.arrowedLine(img, pt1=(x1, y1), pt2=(x2, y2), color=color, thickness=1,
        #                line_type=cv.LINE_4, shift=0, tipLength=0.1)  #
        cv.line(img, pt1=(x1, y1), pt2=(x2, y2), color=color, thickness=1)  #
        cv.circle(img, (x1, y1), radius=10, color=self.color_node_point, thickness=-1)  # plot nodes
        cv.circle(img, (x2, y2), radius=10, color=self.color_node_point, thickness=-1)  # plot nodes

        return img

    def draw_node_text_recv(self, img, A_node, text):
        node = self.node_pos_in_fig[A_node]
        x, y = int(node[0]), int(node[1])
        # 添加文字,第一个参数是x轴坐标，第二个参数是y轴坐标，以数据的刻度为基准
        # cv.rectangle(img, (x - 63, y + 20), (x + 13, y + 43), color=self.ori_img_background, thickness=-1)
        # cv.putText(img, str(text), org=(x - 63, y + 43), fontFace=cv.FONT_HERSHEY_COMPLEX, fontScale=1.0,
        #            color=self.color_node_recv, thickness=1)
        size = (len(text)+1) * 20  ## x + 63
        cv.rectangle(img, (x - 63, y + 20), (x-63+size, y + 43), color=self.ori_img_background, thickness=-1)  # ori_img_background
        cv.putText(img, str(text), org=(x - 63, y + 43), fontFace=cv.FONT_HERSHEY_COMPLEX, fontScale=1.0,
                   color=self.color_node_recv, thickness=1)
        return img

    def draw_node_text_generate(self, img, A_node, text):
        node = self.node_pos_in_fig[A_node]
        x, y = int(node[0]), int(node[1])
        # cv.rectangle(img, (x + 13, y + 20), (x + 73, y + 43), color=self.ori_img_background, thickness=-1)
        # # 添加文字,第一个参数是x轴坐标，第二个参数是y轴坐标，以数据的刻度为基准
        # cv.putText(img, str(text), org=(x + 13, y + 43), fontFace=cv.FONT_HERSHEY_COMPLEX, fontScale=1.0,
        #            color=self.color_node_gene, thickness=1)
        size = (len(text)+1)*20   ## x + 83
        cv.rectangle(img, (x - 63, y + 50), (x-63+size, y + 73), color=self.ori_img_background, thickness=-1)
        # 添加文字,第一个参数是x轴坐标，第二个参数是y轴坐标，以数据的刻度为基准
        cv.putText(img, str(text), org=(x - 63, y + 73), fontFace=cv.FONT_HERSHEY_COMPLEX, fontScale=1.0,
                   color=self.color_node_gene, thickness=1)
        return img

    def draw_node_text_send(self, img, A_node, text):
        node = self.node_pos_in_fig[A_node]
        x, y = int(node[0]), int(node[1])
        size = (len(text) + 1) * 20  ## x + 63
        cv.rectangle(img, (x - 63, y + 80), (x-63+size, y + 103), color=self.ori_img_background, thickness=-1)
        # 添加文字,第一个参数是x轴坐标，第二个参数是y轴坐标，以数据的刻度为基准
        cv.putText(img, str(text), org=(x - 63, y + 103), fontFace=cv.FONT_HERSHEY_COMPLEX, fontScale=1.0,
                   color=self.color_node_send, thickness=1)

        return img

    def draw_nodes_data_dynamically(self, a=0, **kwargs):
        img = self.nodes_mat_show_img
        print(' start draw all nodes\' data ..........', )
        img2 = cv.resize(img, self.figSize)
        cv.imshow('routing_mat', img2)
        cv.waitKey(1)
        num = 0
        while True:
            self.mux.acquire()
            if not self.keep_run: break
            self.mux.release()
            if qimg_data.qsize() == 0:
                cv.waitKey(5)
                continue
            nodes_draw_data = qimg_data.get()
            # print('==========', nodes_draw_data)
            ## {self_id: {'connect': name, 'class':'2', 'recv_res':23, 'generate_res':65}}
            for ori_node_name in nodes_draw_data.keys():  ##实质上不允许捆绑多个数据
                # node_draw_data = nodes_draw_data[ori_node_name]
                ## {'connect': name, 'class':'2', 'recv_res':23, 'generate_res':65}

                node_draw_data = nodes_draw_data[ori_node_name]
                try:
                    node_to = node_draw_data['connect']  # 需要更新连线
                    k = node_draw_data['class']

                    try:
                        # print('vision:', ori_node_name, ':', self.node_history_data[str(ori_node_name)], '---',
                        #                                     node_draw_data)
                        node_draw_data_his = self.node_history_data[str(ori_node_name)]
                        try:
                            node_to_his = node_draw_data_his['connect']
                            img = self.draw_2_nodes_line(img, ori_node_name, node_to_his, self.ori_img_background)
                            self.node_history_data[str(ori_node_name)] = nodes_draw_data[ori_node_name]  ##历史数据更新
                        except:
                            pass
                    except:  ##KeyError as key 当前节点不存在历史数据，需要新添加
                        self.node_history_data = dict(self.node_history_data, **nodes_draw_data)
                        pass

                    seed = np.array([ord(d) for d in k]).sum()
                    np.random.seed(seed)  # 随机颜色。可以保存每次相同类别的数据的颜色分量相同
                    c = np.random.randint(0, 255, 3)
                    # print('color:', c)
                    img = self.draw_2_nodes_line(img, ori_node_name, node_to, c.tolist())  # (c[0], c[1], c[2])

                except:
                    pass

                try:
                    dat = node_draw_data['recv_res']
                    text = '{}:{}'.format(dat[0],dat[1])
                    img = self.draw_node_text_recv(img, ori_node_name, text)
                except:
                    pass
                try:
                    dat = node_draw_data['generate_res']
                    text = '{}:{}'.format(dat[0], dat[1])
                    img = self.draw_node_text_generate(img, ori_node_name, text)
                except:
                    pass
                try:
                    dat = node_draw_data['send_res']
                    text = '{}:{}'.format(dat[0], dat[1])
                    img = self.draw_node_text_send(img, ori_node_name, text)
                except:
                    pass

                num += 1
                if num < 10:
                    continue
                else:
                    num = 0
                    text = str(qimg_data.qsize())
                    size = (len(text) + 1) * 20  ## x + 83
                    xx, yy = 1800, 40
                    cv.rectangle(img, (xx, 0), (xx + size, yy), color=self.ori_img_background,
                                 thickness=-1)
                    # 添加文字,第一个参数是x轴坐标，第二个参数是y轴坐标，以数据的刻度为基准
                    cv.putText(img, str(text), org=(xx, yy), fontFace=cv.FONT_HERSHEY_COMPLEX, fontScale=1.0,
                               color=self.color_node_send, thickness=1)

                    img2 = cv.resize(img, dsize=self.figSize)
                    cv.imshow('routing_mat', img2)
                    # print('==========')
                    cv.waitKey(1)
            # cv.waitKey(1000)
            # time.sleep(1e-5)
        print(' draw all nodes data\' thread is end..........')

    def start_draw_nodes_data_dynamically_thread(self):
        t = threading.Thread(target=self.draw_nodes_data_dynamically, args=(None,))
        # print(' start draw all nodes\' data ..........')
        t.start()

    def close__draw_nodes_data_dynamically_thread(self):
        self.mux.acquire()
        self.keep_run = False
        self.mux.release()

    def __del__(self):
        self.mux.acquire()
        self.keep_run = False
        self.mux.release()


def fig2data(fig):
    """
    fig = plt.figure()
    image = fig2data(fig)
    @brief Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
    @param fig a matplotlib figure
    @return a numpy 3D array of RGBA values
    """
    import PIL.Image as Image
    # draw the renderer
    fig.canvas.draw()

    # Get the RGBA buffer from the figure
    w, h = fig.canvas.get_width_height()
    buf = np.fromstring(fig.canvas.tostring_argb(), dtype=np.uint8)
    buf.shape = (w, h, 4)

    # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
    buf = np.roll(buf, 3, axis=2)
    image = Image.frombytes("RGBA", (w, h), buf.tostring())
    image = np.asarray(image)
    return image


class SHOW_nodes_data_plt:
    def __init__(self, mat):
        self.layers_position, _, self.node_fig_pos = self.calculate_routing_nodes_mat(mat)
        self.fig = plt.figure(str('node_detail'), figsize=(8, 6))
        # self.draw_mat_nodes()
        pass

    def calculate_routing_nodes_mat(self, mat):
        global radius
        layers_position = []
        layers_radius = []
        subplot = {}
        num_layers = len(mat)
        max_radius = np.max(np.array(mat[len(mat) - 1][:, 1]))
        for l_idx, layer in enumerate(mat):
            one_layer = []
            num_nodes = len(layer)
            for node_name_r_alp_idx, _ in enumerate(layer):
                name, radius, alp = layer[node_name_r_alp_idx, :]
                # radius = radius / max_radius  # 归一化到半径为1的圆内
                x = radius * math.cos(alp / 180 * math.pi)
                y = radius * math.sin(alp / 180 * math.pi)
                node = [name, x, y]
                one_layer.append(node)

                pos = [num_layers, num_nodes, node_name_r_alp_idx + 1 + (num_nodes * (num_layers - l_idx - 1))]
                subplot_pos = {str(name): pos}
                subplot = dict(subplot, **subplot_pos)
            layers_position.append(one_layer)
            layers_radius.append(radius)
        # print('layers_position:', layers_position)
        return layers_position, layers_radius, subplot

    def data_show_figure(self, name, sign='send', dat=None):
        if name is not None:
            pos = self.node_fig_pos[str(name)]
            # print('pos:', pos)
            # ax = SubplotZero(fig, 1, 1, 1)
            # plt.ion()
            fig = self.fig.add_subplot(pos[0], pos[1], pos[2])
            # plt.clf()
            # plt.cla()
            # plt.subplot(pos[0], pos[1], pos[2])
            plt.plot(0, 0)
            plt.plot(6, 5)
            size = 24
            # plt.xticks([0,5,0,6])
            plt.xticks([])
            plt.yticks([])
            plt.title(str(name), fontdict={'size': '10', 'color': 'k'})
            if sign == 'send':
                # 添加文字,第一个参数是x轴坐标，第二个参数是y轴坐标，以数据的刻度为基准
                plt.text(0, 4.6, str('send'), fontdict={'size': '8', 'color': 'b'})
                # plt.text(1, 4.6, dat[:size], fontdict={'size': '8', 'color': 'k'})
                idx = 0
                while len(dat) > size:
                    plt.text(1, 4.6 - idx * 0.8, dat[:size], fontdict={'size': '8', 'color': 'k'})
                    idx += 1
                    dat = dat[size:]
                plt.text(1, 4.6 - idx * 0.8, dat[:size], fontdict={'size': '8', 'color': 'k'})
            else:
                # 添加文字,第一个参数是x轴坐标，第二个参数是y轴坐标，以数据的刻度为基准
                plt.text(0, 2, str('recv'), fontdict={'size': '8', 'color': 'b'})
                idx = 0
                while len(dat) > size:
                    plt.text(1, 2 - idx * 0.8, dat[:size], fontdict={'size': '8', 'color': 'k'})
                    idx += 1
                    dat = dat[size:]
                plt.text(1, 2 - idx * 0.8, dat[:size], fontdict={'size': '8', 'color': 'k'})
            # plt.pause(0.00001)
            plt.draw()
            # 关闭交互模式
            # plt.ioff()
            # plt.savefig('temp_nodes_data.jpg')
            # 转化为numpy数据
            # canvas = FigureCanvasAgg(plt.gcf())
            # canvas.draw()
            # img = np.array(canvas.renderer.buffer_rgba())
            img = fig2data(fig)
            cv.imshow('f', img)

    def draw_mat_nodes(self):
        layers_position = self.layers_position
        fig = plt.figure('routing mat', figsize=(10, 6))
        fig.tight_layout()
        # plt.ion()
        for idx, one_layer in enumerate(layers_position):
            for node in one_layer:
                name, x, y = node
                plt.plot(x, y, 'bo')
                # 添加文字,第一个参数是x轴坐标，第二个参数是y轴坐标，以数据的刻度为基准
                plt.text(x, y, str(name), fontdict={'size': '10', 'color': 'r'})
            # plt.scatter(0, 0, color='w', marker='o', edgecolors='r', s=(layers_radius[idx]*23)**2*math.pi, alpha=0.1)
            # plt.pause(1e-10)
            # plt.draw()

        plt.draw()  # 注意此函数需要调用
        plt.pause(0.00000000001)
        # t = threading.Thread(target=plt.show, args=())
        # t.start()


def update(Data_show):
    for i in range(400):
        print('i=', i)
        Data_show.node_data_show_figure('203', sign='send',
                                        dat='{"101-%d": dd,geg,ewe,r,5,e,re,t,5f6sd5f6s5f6d565er}' % i)
        Data_show.node_data_show_figure('201', sign='recv', dat='{"101-%d": dd,geg,ewe,r,5,e,re,t,er}' % i)
        # plt.draw()
        # plt.pause(0.01)
        cv.waitKey(50)
        # time.sleep(1)


if __name__ == '__main__':
    a = np.full_like(np.zeros([100, 100, 3]), 0)
    cv.imshow('dfdg', a)
    cv.waitKey(10 ** 3 * 5)
    cv.destroyAllWindows()
    print(a)
