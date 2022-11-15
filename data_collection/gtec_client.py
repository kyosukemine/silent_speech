import socket
from datetime import datetime
import time
import pickle

DATESIZE = 1024 # 受信データバイト数
INTERVAL = 3 # ソケット接続時のリトライ待ち時間
RETRYTIMES = 5 # ソケット接続時のリトライ回数

class SocketClient():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = None

    def connect(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       
        # サーバーとの接続 RETRYTIMESの回数だけリトライ
        for x in range(RETRYTIMES):
            try:
                client_socket.connect((self.host, self.port))
                self.socket =  client_socket
                print('[{0}] server connect -> address : {1}:{2}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.host, self.port) )
                break
            except socket.error:
                # 接続を確立できない場合、INTERVAL秒待ってリトライ
                time.sleep(INTERVAL)
                print('[{0}] retry after wait{1}s'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), str(INTERVAL)) )
 
    # サーバーへデータ送信関数
    def send(self):
        # ターミナルから入力された文字を取得
        input_data = input()
        input_data = input_data.encode('utf-8')
        self.socket.send(input_data) # データ送信
    
    # サーバーからデータ受信関数
    def recv(self):
        rcv_data = self.socket.recv(DATESIZE) # データ受信
        rcv_data = rcv_data.decode('utf-8')
	data = pickle.loads(response)
	# temperature_bme280 = float(data[0])
        # relativehumidity_bme280 = float(data[1])
        # absolutehumidity_bme280 = float(data[2])
        # barometricpressure_bme280 = float(data[3])
        return data
    
    # 上記の送信/受信関数を順番に行う
    def send_rcv(self):
        self.send()
        return self.recv()

    # ソケットをクローズする関数
    def close(self):
        self.socket.close() # ソケットクローズ
        self.socket = None
             
if __name__ == '__main__':
    HOST_IP = "192.168.xx.xx"
    PORT = 50000
    client = SocketClient(HOST_IP, PORT)
    client.connect()
    while True:
        if client.socket is not None:
            client.send_rcv()
        else:
            break