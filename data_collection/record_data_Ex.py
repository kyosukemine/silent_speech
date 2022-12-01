import time
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
import scipy.signal
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
    # print(selected_chunks)
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
        # make audio stream

        self.queue_audio = queue.Queue()

        def audio_callback(indata, frames, time, status):
            """This is called (from a separate thread) for each audio block."""
            if status:
                print(status, file=sys.stderr)
            # Fancy indexing with mapping creates a (necessary!) copy:
            self.queue_audio.put(indata.copy())
        # make audio stream
        print(sd.query_devices())
        print(sd.query_devices(6))
        print(sd.query_devices(19))
        print(sd.DeviceList())
        self.audio_sample_rate = 16000
        self.audio_stream = sd.InputStream(device=19, channels=1, samplerate=self.audio_sample_rate, latency="low", callback=audio_callback)


        # make emg stream

        # self.queue_EMG = queue.Queue()
        self.emg_channels = num_channels
        self.EMG_strem = gd.InputStream(channnels=self.emg_channels, self_ip="192.168.135.10", passthrough_data=True, sink_ip="192.168.135.2")
        # config and make data holders
        EMG_sample_rate = 1200

        audio_multiplier = int(self.audio_sample_rate/EMG_sample_rate)
        window = EMG_sample_rate*5

        self.audio_data = []
        self.emg_data = []
        self.button_data = []

        self.debug = debug
        self.previous_sample_number = -1

        # plot setup

        self.display = display
        if display:
            plt.ion()
            fig, (audio_ax, emg_ax) = plt.subplots(2)
            audio_ax.axis((0, window*audio_multiplier, -1, 1))
            emg_ax.axis((0, window, -300, 300))
            audio_lines = audio_ax.plot(np.zeros(window*audio_multiplier))
            emg_lines = emg_ax.plot(np.zeros((window, self.emg_channels)))
            for l, c in zip(emg_lines, ['grey', 'mediumpurple', 'blue', 'green', 'yellow', 'orange', 'red', 'sienna']):
                l.set_color(c)
            text = emg_ax.text(50, -250, 'RMS: 0')

            for ax in (audio_ax, emg_ax):
                ax.set_yticks([0])
                ax.yaxis.grid(True)
                ax.tick_params(bottom=False, top=False, labelbottom=False,
                               right=False, left=False, labelleft=False)
            fig.tight_layout(pad=0)

            def update_plot(frame):
                """ This is called by matplotlib for each plot update. """
                audio_to_plot = get_last_sequence(self.audio_data, window*audio_multiplier, 1, False, EMG_sample_rate)
                audio_to_plot = audio_to_plot.squeeze(1)
                audio_lines[0].set_ydata(audio_to_plot)

                emg_to_plot = get_last_sequence(self.emg_data, window, self.emg_channels, True, EMG_sample_rate)
                # print(emg_to_plot)
                for column, line in enumerate(emg_lines):
                    line.set_ydata(emg_to_plot[:, column])
                text.set_text('RMS: '+str(emg_to_plot[-EMG_sample_rate*2:-EMG_sample_rate//2].std()))
                return audio_lines + emg_lines

            self.ani = FuncAnimation(fig, update_plot, interval=10)

    def update(self):
        '''
        time until data is filled by gtec > audio

        '''
        time1 = time.time()
        if self.display:
            # next two lines seem to be a better alternative to plt.pause(0.005)
            # https://github.com/matplotlib/matplotlib/issues/11131
            plt.gcf().canvas.draw_idle()
            plt.gcf().canvas.start_event_loop(0.005)
        else:
            time.sleep(0.005)

        current_emg = []
        _data = self.EMG_strem.q_data.get(timeout=1)
        current_emg.append(_data.T)

        current_audio = []
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

    def reset(self):
        '''
        reset data and time Synchronize each data
        '''
        self.EMG_strem.q_data.get()
        # while True:
        #     try:
        #         self.EMG_strem.q_data.get()
        #     except queue.Empty:
        #         break

        while True:
            try:
                self.queue_audio.get_nowait()
            except queue.Empty:
                break

        self.emg_data = []
        self.audio_data = []

    def get_data(self):
        emg = np.concatenate(self.emg_data, 0)
        # audio = np.concatenate(self.audio_data, 0).squeeze(1)
        audio = np.concatenate(self.audio_data, 0).flatten()
        # button = np.concatenate(self.button_data, 0)
        chunk_sizes = [(e.shape[0], a.shape[0]) for e, a in zip(self.emg_data, self.audio_data)]  # , b.shape[0] b. , self.button_data
        self.emg_data = []
        self.audio_data = []
        self.button_data = []
        return emg, audio, chunk_sizes  # button,

    def __enter__(self):
        self.audio_stream.start()
        self.EMG_strem.start()
        return self

    def __exit__(self, type, value, traceback):
        self.audio_stream.stop()
        self.audio_stream.close()

        self.EMG_strem.stop()
        # self.EMG_strem.close()


        plt.close()



if __name__ == '__main__':
    with Recorder(debug=False, display=True,  wifi=True, num_channels=8) as r:
        r.reset()
        while True:
            r.update()
            # emg, audio, chunk_sizes = r.get_data()
            # print(len(emg), len(audio), chunk_sizes)
