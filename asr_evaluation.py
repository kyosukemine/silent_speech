import os
import logging

import deepspeech
import jiwer
import soundfile as sf
import numpy as np
from unidecode import unidecode
import librosa
from tqdm import tqdm


def evaluate(testset, audio_directory):
    model = deepspeech.Model('deepspeech-0.7.0-models.pbmm')
    model.enableExternalScorer('deepspeech-0.7.0-models.scorer')
    predictions = []
    targets = []
    for i, datapoint in tqdm(enumerate(testset), total=99):
        audio, rate = sf.read(os.path.join(audio_directory, f'example_output_{i}.wav'))
        if rate != 16000:
            audio = librosa.resample(audio, orig_sr=rate, target_sr=16000)
        assert model.sampleRate() == 16000, 'wrong sample rate'
        audio_int16 = (audio*(2**15)).astype(np.int16)
        text = model.stt(audio_int16)
        target_text = unidecode(datapoint['text'])
        if (not target_text) or target_text == ".":
            print(target_text)
            continue

        predictions.append(text)
        targets.append(target_text)
    transformation = jiwer.Compose([jiwer.RemovePunctuation(), jiwer.ToLowerCase()])
    targets = transformation(targets)
    predictions = transformation(predictions)
    logging.info(f'targets: {targets}')
    logging.info(f'predictions: {predictions}')
    logging.info(f'wer: {jiwer.wer(targets, predictions)}')
