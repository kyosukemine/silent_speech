import sys
import os
import shutil
import numpy as np

import soundfile as sf
import librosa

import torch
from torch import nn

from architecture import Model
from transduction_model import get_aligned_prediction
from read_emg import EMGDataset
from data_utils import phoneme_inventory

from absl import flags
FLAGS = flags.FLAGS
flags.DEFINE_string('model', None, 'checkpoint of model to run')

from collections import OrderedDict
def fix_key(state_dict):
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        if k.startswith('module.'):
            k = k[7:]
        new_state_dict[k] = v
    return new_state_dict

def main():
    trainset = EMGDataset(dev=False, test=False)
    devset = EMGDataset(dev=True)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    n_phones = len(phoneme_inventory)
    model = Model(devset.num_features, devset.num_speech_features, n_phones).to(device)
    state_dict = fix_key(torch.load(FLAGS.model))
    model.load_state_dict(state_dict)

    os.makedirs(os.path.join(FLAGS.output_directory, 'mels'), exist_ok=True)
    os.makedirs(os.path.join(FLAGS.output_directory, 'wavs'), exist_ok=True)

    for dataset, name_prefix in [(trainset, 'train'), (devset, 'dev')]:
        with open(os.path.join(FLAGS.output_directory, f'{name_prefix}_filelist.txt'), 'w') as filelist:
            for i, datapoint in enumerate(dataset):
                spec = get_aligned_prediction(model, datapoint, device, dataset.mfcc_norm)
                spec = spec.T[np.newaxis, :, :].detach().cpu().numpy()
                np.save(os.path.join(FLAGS.output_directory, 'mels', f'{name_prefix}_output_{i}.npy'), spec)
                audio, r = sf.read(datapoint['audio_file'])
                if r != 22050:
                    audio = librosa.resample(audio, r, 22050, res_type='kaiser_fast')
                audio = np.clip(audio, -1, 1)  # because resampling sometimes pushes things out of range
                sf.write(os.path.join(FLAGS.output_directory, 'wavs', f'{name_prefix}_output_{i}.wav'), audio, 22050)
                filelist.write(f'{name_prefix}_output_{i}\n')


if __name__ == "__main__":
    FLAGS(sys.argv)
    main()
