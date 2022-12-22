import sys
import os
import logging

import torch
from torch import nn

from architecture import Model
from transduction_model import test, save_output
from read_emg import EMGDataset
from asr_evaluation import evaluate
from data_utils import phoneme_inventory, print_confusion
from vocoder import Vocoder

from absl import flags
FLAGS = flags.FLAGS
flags.DEFINE_list('models', [], 'identifiers of models to evaluate')
flags.DEFINE_boolean('dev', False, 'evaluate dev insead of test')
flags.DEFINE_boolean('train', False, 'evaluate train instead of test')

class EnsembleModel(nn.Module):
    def __init__(self, models):
        super().__init__()
        self.models = nn.ModuleList(models)

    def forward(self, x, x_raw, sess):
        ys = []
        ps = []
        for model in self.models:
            y, p = model(x, x_raw, sess)
            ys.append(y)
            ps.append(p)
        return torch.stack(ys, 0).mean(0), torch.stack(ps, 0).mean(0)

from collections import OrderedDict
def fix_key(state_dict):
    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        if k.startswith('module.'):
            k = k[7:]
        new_state_dict[k] = v
    return new_state_dict

def main():
    os.makedirs(FLAGS.output_directory, exist_ok=True)
    logging.basicConfig(handlers=[
        logging.FileHandler(os.path.join(FLAGS.output_directory, 'eval_log.txt'), 'w'),
        logging.StreamHandler()
    ], level=logging.INFO, format="%(message)s")

    dev = FLAGS.dev
    testset = EMGDataset(dev=dev, test=not dev)
    if FLAGS.train:
        testset = EMGDataset(dev=False, test=False)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    models = []
    for fname in FLAGS.models:
        state_dict = fix_key(torch.load(fname))
        model = Model(testset.num_features, testset.num_speech_features, len(phoneme_inventory)).to(device)
        model.load_state_dict(state_dict)
        models.append(model)
    ensemble = EnsembleModel(models)
    ensemble = torch.nn.DataParallel(ensemble)

    _, _, confusion = test(ensemble, testset, device)
    print_confusion(confusion)

    vocoder = Vocoder()

    for i, datapoint in enumerate(testset):
        save_output(ensemble, datapoint, os.path.join(FLAGS.output_directory, f'example_output_{i}.wav'), device, testset.mfcc_norm, vocoder)

    evaluate(testset, FLAGS.output_directory)


if __name__ == "__main__":
    FLAGS(sys.argv)
    main()
