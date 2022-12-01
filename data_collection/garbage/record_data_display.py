import time
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
import scipy.signal
import threading
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore
from multiprocessing import Process
import queue
import sys
from importlib import reload  # >= python 3.4
import gtecdevice as gd
reload(gd)

# import brainflow
# from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, IpProtocolType
# from brainflow.data_filter import DataFilter, FilterTypes, AggOperations


def remove_drift(signal, fs):
    b, a = scipy.signal.butter(3, 2, 'highpass', fs=fs)
    return scipy.signal.filtfilt(b, a, signal)


def notch(signal, freq, sample_frequency):
    b, a = scipy.signal.iirnotch(freq, 30, sample_frequency)
    return scipy.signal.filtfilt(b, a, signal)


def notch_harmonics(signal, freq, sample_frequency):
    for f in range(freq, sample_frequency//2, freq):
        signal = notch(signal, f, sample_frequency)
    return signal


def filter_signal(signals, fs):
    """ signals is 2d: time, channels """
    result = np.zeros_like(signals)
    for i in range(signals.shape[1]):
        x = signals[:, i]
        x = notch_harmonics(x, 60, fs)
        x = remove_drift(x, fs)
        result[:, i] = x
    return result


def get_last_sequence(chunk_list, n, k, do_filtering, fs):
    cumulative_size = 0
    selected_chunks = [np.zeros((0, k))]
    for chunk in reversed(chunk_list):
        selected_chunks.append(chunk)
        cumulative_size += chunk.shape[0]
        if cumulative_size > n:
            break
    selected_chunks.reverse()
    result = np.concatenate(selected_chunks, 0)[-n:, :]
    if do_filtering and result.shape[0] > 12:
        result = filter_signal(result, fs)

    if result.shape[0] < n:
        result_padded = np.concatenate([np.zeros((n-result.shape[0], result.shape[1])), result], 0)
    else:
        result_padded = result
    return result_padded


class Recorder(object):
    def __init__(self, debug=False, display=True, num_channels=8, wifi=True):

        self.queue_audio = queue.Queue()

        def audio_callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            if status:
                print(status, file=sys.stderr)
            # Fancy indexing with mapping creates a (necessary!) copy:
            self.queue_audio.put(indata.copy())
        # make audio stream
        print(sd.query_devices())
        print(sd.query_devices(1))
        print(sd.query_devices(3))
        print(sd.DeviceList())
        self.audio_stream = sd.InputStream(device=0, channels=1, samplerate=16000, latency="low", callback=audio_callback)

        # make emg stream
        self.emg_channels = num_channels
        self.EMG_strem = gd.InputStream(channnels=self.emg_channels, self_ip="192.168.100.6", passthrough_data=True, sink_ip="192.168.100.74")

        # params = BrainFlowInputParams()
        # if debug:
        #     board_id = -1 # synthetic
        #     sample_rate = 256
        # elif not wifi:
        #     board_id = BoardIds.CYTON_BOARD.value
        #     params.serial_port = '/dev/ttyUSB0'
        #     sample_rate = 250
        # else:
        #     board_id = BoardIds.CYTON_WIFI_BOARD.value
        #     params.ip_port = 8001
        #     params.ip_address = '192.168.4.1'
        # sample_rate = 1000
        # self.emg_channels = BoardShim.get_emg_channels(board_id)
        # if num_channels is not None:
        #     self.emg_channels = self.emg_channels[:num_channels]

        # board = BoardShim(board_id, params)
        # board.prepare_session()
        # board.config_board('/3') # configure for digital read
        # board.start_stream()
        # self.board = board

        # config and make data holders
        self.sample_rate = 1200

        self.audio_multiplier = int(16000/self.sample_rate)
        self.window = self.sample_rate*5

        self.audio_data = []
        self.emg_data = []
        self.button_data = []

        self.debug = debug
        self.previous_sample_number = -1

        # self.audio_data_toplot = []

        if display:
            # plot setup
            self.qtplot(num_channels)

            # thread
            self.t_update = threading.Thread(target=self.update)
            self.t_update.start()
            # self.t_getdata = Process(target=self.getdata)
            self.timer = QtCore.QTimer()
            # self.timer.timeout.connect(self.update)
            self.timer.timeout.connect(self.plot_update)
            self.timer.start(60)  # ミリ秒単位
            # pg.exec()

        # plot setup

    def qtplot(self, EMG_num_channels):
        app = pg.mkQApp("gtec plot")
        #mw = QtWidgets.QMainWindow()
        # mw.resize(800,800)

        win = pg.GraphicsLayoutWidget(show=True, title="plot result")

        win.resize(2000, 1200)
        win.setWindowTitle('pyqtgraph')

        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)
        p_audio = win.addPlot(title="audio")
        curve_audio = p_audio.plot(pen=0)
        p_audio.setYRange(0.5, -0.5)
        # self.win.nextRow()
        p_EMGlist = []
        curve_EMGlist = []
        for i in range(EMG_num_channels):
            _p = win.addPlot(row=i//2+1, col=i % 2, title=f"EMG_channel_{i}")
            _p.setYRange(500, -500)
            _curve = _p.plot(pen=i+1)
            p_EMGlist.append(_p)
            curve_EMGlist.append(_curve)
        self.win = win
        self.p_audio = p_audio
        self.curve_audio = curve_audio
        self.p_EMGlist = p_EMGlist
        self.curve_EMGlist = curve_EMGlist
        # p_sin.setYRange(1, -1)
        # p_cos.setYRange(1, -1)
        # pg.show()

    def update(self):
        '''
        time until data is filled by gtec > audio

        '''
        while True:
            time1 = time.time()
            # if self.display:
            #     # next two lines seem to be a better alternative to plt.pause(0.005)
            #     # https://github.com/matplotlib/matplotlib/issues/11131
            #     plt.gcf().canvas.draw_idle()
            #     plt.gcf().canvas.start_event_loop(0.005)
            # else:
            #     time.sleep(0.005)

            current_emg = []
            _data = self.EMG_strem.q_data.get()
            # print(_data.shape)
            current_emg.append(_data.T)
            # if not self.EMG_strem.q_data.empty():
            #     _data = self.EMG_strem.q_data.get()
            #     current_emg.append(_data.T)
            # print(current_emg)
            # while True:  # 9 µsec
            #     try:
            #         _data = self.EMG_strem.q_data.get_nowait()
            #         # self.emg_data
            #         current_emg.append(_data.T)
            #         # self.cnt += 1
            #     except queue.Empty:
            #         break

            current_audio = []
            # for _ in range(self.queue_audio.qsize()):
            #     current_audio.append(self.queue_audio.get_nowait())
            #     # print(current_audio[-1])
            while True:  # 40 μsec
                try:
                    _data = self.queue_audio.get_nowait()
                    # self.emg_data
                    current_audio.append(_data)
                    # self.cnt += 1
                except queue.Empty:
                    break

            if len(current_audio) > 0:
                self.audio_data.append(np.concatenate(current_audio, 0))
            # print(current_emg)
            # print(len(current_emg) > 0)
            # print(current_emg[0])
            if len(current_emg) > 0:
                # data = self.board.get_board_data() # get all data and remove it from internal buffer
                self.emg_data.append(np.concatenate(current_emg, 0))
            # print(time.time()-time1)

            # if not self.debug:
            #     for sn in data[0,:]:
            #         if self.previous_sample_number != -1 and sn != (self.previous_sample_number+1)%256:
            #             print(f'skip from {self.previous_sample_number} to {sn}')
            #         self.previous_sample_number = sn

            #     is_digital_inputs = data[12,:] == 193
            #     button_data = data[16,is_digital_inputs].astype(np.bool)
            #     self.button_data.append(button_data)
            #     if sum(button_data) != 0:
            #         print('button pressed')

    def get_data(self):
        emg = np.concatenate(self.emg_data, 0)
        audio = np.concatenate(self.audio_data, 0).squeeze(1)
        button = np.concatenate(self.button_data, 0)
        chunk_sizes = [(e.shape[0], a.shape[0], b.shape[0]) for e, a, b in zip(self.emg_data, self.audio_data, self.button_data)]
        self.emg_data = []
        self.audio_data = []
        self.button_data = []
        return emg, audio, button, chunk_sizes

    def plot_update(self):

        # print(self.audio_data)

        audio_to_plot = get_last_sequence(self.audio_data, self.window*self.audio_multiplier, 1, False, self.sample_rate)
        audio_to_plot = audio_to_plot.squeeze(1)
        # print(sum(audio_to_plot))
        emg_to_plot = get_last_sequence(self.emg_data, self.window, self.emg_channels, True, self.sample_rate)
        # print(emg_to_plot.shape)
        for i, _curve in enumerate(self.curve_EMGlist):
            _curve.setData(emg_to_plot[:, i])
        # audio_lines[0].set_ydata(audio_to_plot)
        self.curve_audio.setData(audio_to_plot)
        # self.curve_cos.setData()

    def __enter__(self):
        self.audio_stream.start()
        self.EMG_strem.start()
        return self

    def __exit__(self, type, value, traceback):
        self.audio_stream.stop()
        self.audio_stream.close()

        self.EMG_strem.stop()

        # self.board.stop_stream()
        # self.board.release_session()

        # plt.close()
        print("exit")
        pg.exit()


if __name__ == '__main__':
    with Recorder(debug=True, wifi=True, num_channels=8, display=True) as r:
        pg.exec()
        # while True:
        #     # r.update()
        #     pass
