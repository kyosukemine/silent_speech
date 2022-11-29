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
import queue
import time


class InputStream():
    def __init__(self, channnels=2, host_ip="", port=50000, number_of_scan=64, passthrough_data=False) -> None:
        if host_ip == "":
            address_list = socket.gethostbyname_ex(socket.gethostname() + ".local")[2]  # gethostbyname_ex return (hostname, aliases and list of IP addresses.)
            host_ip = [ip_address for ip_address in address_list if "192" in ip_address][0]
        self.host_ip = host_ip
        self.channels = channnels
        self.port = port
        self.number_of_scan = number_of_scan
        self.q_data = queue.Queue()
        # self.data = [[] for _ in range(channnels)]
        # self.cnt = 0
        self.passthrough_data = passthrough_data
        if passthrough_data:
            self.pass_q = queue.Queue()
            self.recv_frg = False

    def start(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            # client_socket.setsockopt(socket.SQL_SOCKET, socket.SO_REUSEADDR, 1)
            # サーバーとの接続 RETRYTIMESの回数だけリトライ
            RETRYTIMES = 10
            INTERVAL = 1
            for x in range(RETRYTIMES):
                try:
                    client_socket.connect((self.host_ip, self.port))
                    self.client_socket = client_socket
                    print('[{0}] server connect -> address : {1}:{2}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.host_ip, self.port))
                    break
                except socket.error:
                    # 接続を確立できない場合、INTERVAL秒待ってリトライ
                    time.sleep(INTERVAL)
                    print('[{0}] retry after wait {1} sec'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), str(INTERVAL)))
            if client_socket:
                exit()

        self.t_client_socket = threading.Thread(target=self._conn_client)
        # t.setDaemon(True)
        self.t_client_socket.start()
        # self.t_socket = threading.Thread(target=_start)
        # self.t_socket.start()

        if self.passthrough_data:
            self.t_pass_through = threading.Thread(target=self.pass_data)
            self.t_pass_throufh.start()

    def pass_data(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            # server_socket.setsockopt(socket.SQL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host_ip, self.port))
            server_socket.listen(1)
            print("[{}] run server ip {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.host_ip))
            self.server_socket, self.address = server_socket.accept()

        print("[{0}] connect clinet -> address : {1}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.address))
        # self._conn_server()
        while self.server_socket():
            while True:
                if self.recv_frg:
                    self.server_socket.send(self.pass_q.pop())
                    self.recv_frg = False

    def _conn_client(self):
        # cnt = 0

        while self.client_socket:
            recv_numbytes = self.channels*self.number_of_scan*4
            while True:
                # サーバーからデータ受信
                # rcv_data = client_socket.recv(DATASIZE)
                rcv_data = self.client_socket.recv(recv_numbytes)
                if len(rcv_data) < recv_numbytes:  # 4=float32
                    rcv_data += self.client_socket.recv(recv_numbytes-len(rcv_data))
                # print(len(rcv_data))
                if rcv_data:
                    _data = [[] for _ in range(self.channels)]
                    # print(rcv_data)
                    # print(*struct.iter_unpacpk('<f', rcv_data))
                    for i, d in enumerate(struct.iter_unpack('<f', rcv_data)):
                        _data[i % self.channels].append(d[0])
                    # _data = np.array([d[0] for d in struct.iter_unpack('<f', rcv_data)])
                    np_data = np.array(_data)
                    self.q_data.put(np_data)
                    if self.passthrough_data:
                        self.pass_q.put(rcv_data)
                        self.recv_frg = True
                    # rcv_data = struct.unpack('<f', rcv_data)

                else:
                    break
        print("[{0}] disconnect client -> address : {1}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.address))
        # print(cnt)

    # def get(self):
    #     while True:
    #         try:
    #             _data = self.q.get()
    #             self.data[self.cnt % self.channels].append(_data)
    #             self.cnt += 1
    #         except queue.Empty:
    #             break

    def stop(self):
        self.client_socket.close()
        if self.passthrough_data:
            self.server_socket.close()


if __name__ == "__main__":
    s = InputStream()
    s.start()
