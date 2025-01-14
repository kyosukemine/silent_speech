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


class Display(object):
    def __init__(self, debug=False, num_channels=8):
        self.queue_audio = queue.Queue()

        def audio_callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            if status:
                print(status, file=sys.stderr)
            # Fancy indexing with mapping creates a (necessary!) copy:
            self.queue_audio.put(indata.copy())

        # make audio stream
        print(sd.query_devices())
        # print(sd.query_devices(6))
        # print(sd.query_devices(3))
        print(sd.check_output_settings())
        print(sd.DeviceList())
        self.audio_sample_rate = 16000
        self.audio_stream = sd.InputStream(device=0, channels=1, samplerate=self.audio_sample_rate,latency="low", callback=audio_callback)

        # make emg stream
        self.emg_channels = num_channels
        self.EMG_strem = gd.InputStream(channnels=self.emg_channels, self_ip="192.168.135.2")  # IP address of PC for display (pc run this file)

        # config and make data holders
        self.EMG_sample_rate = 1200
        self.slice_num = 10
        self.audio_multiplier = int(self.audio_sample_rate/2400)
        self.window = self.EMG_sample_rate*5

        self.audio_data = []
        self.emg_data = []
        self.button_data = []

        # self.debug = debug
        # self.previous_sample_number = -1

        # plot setup
        self.qtplot(num_channels)
        # thread
        self.t_update = threading.Thread(target=self.update)
        self.t_update.start()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.plot_update)
        self.timer.start(60)  # ミリ秒単位

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
        while self.EMG_strem.q_data.empty():
            pass
        while True:
            current_emg = []
            try:
                _data = self.EMG_strem.q_data.get(timeout=3)
            except queue.Empty:
                print("Empty queue")
                exit()
                # pg.exit()
                break
            current_emg.append(_data.T)
            current_audio = []
            while True:  # 40 μsec
                try:
                    _data = self.queue_audio.get_nowait()
                    current_audio.append(_data)
                except queue.Empty:
                    break

            if len(current_audio) > 0:
                self.audio_data.append(np.concatenate(current_audio, 0))
            if len(current_emg) > 0:
                self.emg_data.append(np.concatenate(current_emg, 0))

    # def get_data(self):
    #     emg = np.concatenate(self.emg_data, 0)
    #     audio = np.concatenate(self.audio_data, 0).squeeze(1)
    #     button = np.concatenate(self.button_data, 0)
    #     chunk_sizes = [(e.shape[0], a.shape[0], b.shape[0]) for e, a, b in zip(self.emg_data, self.audio_data, self.button_data)]
    #     self.emg_data = []
    #     self.audio_data = []
    #     self.button_data = []
    #     return emg, audio, button, chunk_sizes

    def plot_update(self):
        audio_to_plot = get_last_sequence(self.audio_data, self.window*self.audio_multiplier, 1, False, self.EMG_sample_rate)
        audio_to_plot = audio_to_plot.squeeze(1)
        emg_to_plot = get_last_sequence(self.emg_data, self.window, self.emg_channels, True, self.EMG_sample_rate)
        for i, _curve in enumerate(self.curve_EMGlist):
            _curve.setData(emg_to_plot[:, i][::self.slice_num])
        self.curve_audio.setData(audio_to_plot[::self.slice_num])

    def __enter__(self):
        self.audio_stream.start()
        self.EMG_strem.start()
        return self

    def __exit__(self, type, value, traceback):
        self.audio_stream.stop()
        self.audio_stream.close()
        self.EMG_strem.stop()
        print("exit")
        pg.exit()


if __name__ == '__main__':
    with Display(debug=True, wifi=True, num_channels=8, display=True) as r:
        pg.exec()
