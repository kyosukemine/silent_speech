import os
import logging
import whisper
import jiwer
import soundfile as sf
import numpy as np
from unidecode import unidecode
import librosa
from tqdm import tqdm
from collections import defaultdict
model = whisper.load_model("large")


def evaluate(testset, audio_directory):
    # model = deepspeech.Model('deepspeech-0.7.0-models.pbmm')
    # model.enableExternalScorer('deepspeech-0.7.0-models.scorer')
    predictions = defaultdict(lambda: {"silent": [], "voiced": []})
    targets = defaultdict(lambda: {"silent": [], "voiced": []})
    # targets = {"silent": [], "voiced": []}
    for i, datapoint in tqdm(enumerate(testset), total=len(testset)):
        # audio, rate = sf.read(os.path.join(audio_directory, f'example_output_{i}.wav'))
        # if rate != 16000:
        #     audio = librosa.resample(audio, orig_sr=rate, target_sr=16000)
        # assert model.sampleRate() == 16000, 'wrong sample rate'
        # audio_int16 = (audio*(2**15)).astype(np.int16)
        # text = model.stt(audio_int16)
        silent_or_voiced = "silent" if datapoint["silent"] else "voiced"
        result = model.transcribe(os.path.join(audio_directory, f'example_output_{i}_{silent_or_voiced}_{datapoint["id"]}.wav'), language="ja")
        predict_text = result["text"]
        target_text = unidecode(datapoint['text'])
        target_text = datapoint['text']
        predict_text = predict_text.replace(" ", "").replace("、", "").replace("。", "")
        target_text = target_text.replace(" ", "").replace("、", "").replace("。", "")
        print(predict_text, target_text)
        if (not target_text) or target_text == ".":
            print(target_text)
            continue

        predictions[datapoint["id"]][silent_or_voiced].append(predict_text)
        targets[datapoint["id"]][silent_or_voiced].append(target_text)
    # transformation = jiwer.Compose([jiwer.RemovePunctuation(), jiwer.ToLowerCase()])
    # targets = transformation(targets)
    # predictions = transformation(predictions)
    print("target prediction")
    silent_pre = []
    silent_tar = []
    voiced_pre = []
    voiced_tar = []
    for id in predictions.keys():
        silent_pre.extend(predictions[id]["silent"])
        silent_tar.extend(targets[id]["silent"])
        voiced_pre.extend(predictions[id]["voiced"])
        voiced_tar.extend(targets[id]["voiced"])
        print(id)
        logging.info(f'id: {id}')
        [print(t, p) for t, p in zip(targets[id]["silent"], predictions[id]["silent"])]
        [print(t, p) for t, p in zip(targets[id]["voiced"], predictions[id]["voiced"])]
        logging.info(f'targets[silent]: {targets[id]["silent"]}')
        logging.info(f'predictions[silent]: {predictions[id]["silent"]}')
        logging.info(f'targets[voiced]: {targets[id]["voiced"]}')
        logging.info(f'predictions[voiced]: {predictions[id]["voiced"]}')
    for id in predictions.keys():
        print(id)
        logging.info(f'cer[{id}][silent]: {jiwer.cer(targets[id]["silent"], predictions[id]["silent"])}')
        logging.info(f'cer[{id}][voiced]: {jiwer.cer(targets[id]["voiced"], predictions[id]["voiced"])}')
    # logging.info(f'wer: {jiwer.wer(targets, predictions)}')
    # print(predictions)
    # print(silent_pre, predictions["100"]["silent"])
    # print(len(silent_pre), len(predictions[100]["silent"]))
    # print(silent_tar, targets["100"]["silent"])
    # print(len(silent_tar), len(targets["100"]["silent"]))
    # print(voiced_pre, predictions["100"]["voiced"])
    # print(len(voiced_pre), len(predictions["100"]["voiced"]))
    logging.info(f'cer[silent]: {jiwer.cer(silent_pre, silent_tar)}')
    logging.info(f'cer[voiced]: {jiwer.cer(voiced_pre, voiced_tar)}')
    # logging.info(f'cer: {jiwer.cer(targets["silent"] + targets["voiced"], predictions["silent"] + predictions["voiced"])}')
