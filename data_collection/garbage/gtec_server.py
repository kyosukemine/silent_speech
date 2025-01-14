import socket
from datetime import datetime
import pickle
import threading
import struct
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
import matplotlib.pyplot as plt
# import threading


class SocketServer():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.data = [[0] for i in range(8)]
    # サーバー起動

    def run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            # server_socket.setsockopt(socket.SQL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(1)
            print("[{}] run server".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            # while True:
            #     # クライアントから接続要求受け入れ
            #     client_socket, address = server_socket.accept()
            client_socket, address = server_socket.accept()

        print("[{0}] connect clinet -> address : {1}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), address))
        # クライアントごとにThread起動 send/recvのやり取りをする。
        # t_qtplot = threading.Thread(target=self.qtplot)
        t_socket = threading.Thread(target=self.conn_client, args=(client_socket, address))
        # t.setDaemon(True)
        # t_qtplot.start()
        self.qtplot()
        t_socket.start()
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(10)#ミリ秒単位
        pg.exec()
        # t.start()
        # print(client_socket.proto)
        # self.conn_client(client_socket, address)

    def conn_client(self, client_socket, address):
        # cnt = 0
        with client_socket:
            while True:
                # クライエントからデータ受信
                # rcv_data = client_socket.recv(DATASIZE)
                rcv_data = client_socket.recv(4096)
                if rcv_data:

                    # print(rcv_data)
                    # print(*struct.iter_unpack('<f', rcv_data))
                    rcv_data = [d[0] for d in struct.iter_unpack('<f', rcv_data)]
                    # print(len(rcv_data))
                    # cnt += len(rcv_data)
                    # print(rcv_data)
                    # rcv_data = struct.unpack('<f', rcv_data)
                    self.data[0].extend(rcv_data[::2])
                    self.data[1].extend(rcv_data[1::2])

                    # axs[0].clear()
                    # axs[1].clear()
                    # axs[0].plot(rcv_data[::2])
                    # axs[1].plot(rcv_data[1::2])
                    # fig.canvas.draw()
                    # fig.canvas.flush_events()
                    # print(rcv_data)
                    # rcv_dataをclientに送る。
                    # BM280_readData()はデータを出力する関数。出力はlist型。
                    # bme280_data = BME280_readData()
                    # client_socket.send(pickle.dumps(bme280_data))
                else:
                    break
        print("[{0}] disconnect client -> address : {1}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), address))
        # print(cnt)

    def qtplot(self):
        app = pg.mkQApp("gtec plot")
        #mw = QtWidgets.QMainWindow()
        # mw.resize(800,800)

        win = pg.GraphicsLayoutWidget(show=True, title="plot result")
        win.resize(1000, 600)
        win.setWindowTitle('pyqtgraph')

        self.win = win

        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        p_sin = win.addPlot(title="Updating plot sin")
        self.win.nextRow()
        p_cos = win.addPlot(title="Updating plot cos")
        p_sin.setYRange(700, -700)
        p_cos.setYRange(700, -700)
        # pg.show()
        curve_sin = p_sin.plot(pen='y')
        curve_cos = p_cos.plot(pen='y')
        self.p_sin = p_sin
        self.p_cos = p_cos
        self.curve_sin = curve_sin
        self.curve_cos = curve_cos
        # pg.exec()
        # def update():
        #     global curve, data, ptr, p_sin
        #     curve.setData(data[ptr%10])
        #     if ptr == 0:
        #         p_sin.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
        #     ptr += 1
    def update(self):
        self.curve_sin.setData(self.data[0][-2000:])
        self.curve_cos.setData(self.data[1][-2000:])


if __name__ == "__main__":
    HOST_IP = "192.168.100.6"
    SOCKET_PORT = 50000
    SocketServer(HOST_IP, SOCKET_PORT).run_server()
