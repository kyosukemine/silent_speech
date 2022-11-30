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
    def __init__(self, channnels=2, self_ip="", port=50000, number_of_scan=64, passthrough_data=False, sink_ip="") -> None:
        if self_ip == "":
            # address_list = socket.gethostbyname_ex(socket.gethostname() + ".local") [2] # gethostbyname_ex return (hostname, aliases and list of IP addresses.)
            # self_ip = [ip_address for ip_address in address_list if "192" in ip_address][0]
            print("enter self ip ", end=":")
            self_ip = input()
        self.self_ip = self_ip
        self.sink_ip = sink_ip
        self.channels = channnels
        self.port = port
        self.number_of_scan = number_of_scan
        self.q_data = queue.Queue()
        # self.data = [[] for _ in range(channnels)]
        # self.cnt = 0
        self.passthrough_data = passthrough_data
        if passthrough_data:
            if sink_ip == "":
                print("enter sink ip ", end=":")
                self.sink_ip = input()
            self.pass_q = queue.Queue()
            self.recv_frg = False

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as source_socket:
            # source_socket.setsockopt(socket.SQL_SOCKET, socket.SO_REUSEADDR, 1)
            print(self.self_ip)
            source_socket.bind((self.self_ip, self.port))
            source_socket.listen(1)
            print("[{}] run self ip {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.self_ip))
            self.source_socket, self.address = source_socket.accept()

        self.t_source_socket = threading.Thread(target=self._conn_source)
        # t.setDaemon(True)
        self.t_source_socket.start()
        # self.t_socket = threading.Thread(target=_start)
        # self.t_socket.start()

        if self.passthrough_data:
            self.t_pass_through = threading.Thread(target=self.pass_data)
            self.t_pass_through.start()

    def pass_data(self):
        # サーバーとの接続 RETRYTIMESの回数だけリトライ
        while 1:
            sink_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("try connecting")
            while self.source_socket:
                try:
                    sink_socket.connect((self.sink_ip, self.port))
                    self.sink_socket = sink_socket
                    print('[{0}] sink connect -> address : {1}:{2}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.sink_ip, self.port))
                    break
                except socket.error:
                    # 接続を確立できない場合、INTERVAL秒待ってリトライ
                    time.sleep(1)
                    # print('[{0}] retry after wait{1}s'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), str(INTERVAL)) )
                    pass

            while self.sink_socket:
                # while True:
                # if self.recv_frg:
                try:
                    self.sink_socket.send(self.pass_q.get(timeout=3))
                except queue.Empty:
                    exit()
                    # self.recv_frg = False
                except IOError:
                    break

    def _conn_source(self):
        # cnt = 0

        while self.source_socket:
            recv_numbytes = self.channels*self.number_of_scan*4
            # while True:
            # サーバーからデータ受信
            # rcv_data = source_socket.recv(DATASIZE)
            rcv_data = self.source_socket.recv(recv_numbytes)
            if len(rcv_data) < recv_numbytes:  # 4=float32
                rcv_data += self.source_socket.recv(recv_numbytes-len(rcv_data))
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
                    self.pass_q.put_nowait(rcv_data)
                    # self.recv_frg = True
                # rcv_data = struct.unpack('<f', rcv_data)
            else:
                break
        print("[{0}] disconnect source -> address : {1}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.address))
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
        self.source_socket.close()
        if self.passthrough_data:
            self.sink_socket.close()


if __name__ == "__main__":
    # s = InputStream(self_ip="192.168.0.169", passthrough_data=True, sink_ip="192.168.0.165")
    s = InputStream(passthrough_data=True, sink_ip="192.168.0.165")
    s.start()
