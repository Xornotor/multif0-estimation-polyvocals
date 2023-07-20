"""
File modified by André Paiva
"""

from __future__ import print_function
import models
import utils
import utils_train

import hdf5plugin
import numpy as np
import pandas as pd

import os
import argparse

def get_single_test_prediction(model, audio_file=None):
    """Generate output from a model given an input numpy file.
       Part of this function is part of deepsalience
    """

    if audio_file is not None:

        pump = utils.create_pump_object()
        features = utils.compute_pump_features(pump, audio_file)
        input_hcqt = features['dphase/mag'][0]
        input_dphase = features['dphase/dphase'][0]

    else:
        raise ValueError("One audio_file must be specified")

    input_hcqt = input_hcqt.transpose(1, 2, 0)[np.newaxis, :, :, :]
    input_dphase = input_dphase.transpose(1, 2, 0)[np.newaxis, :, :, :]

    n_t = input_hcqt.shape[3]
    t_slices = list(np.arange(0, n_t, 5000))
    output_list = []

    for t in t_slices:
        p = model.predict([np.transpose(input_hcqt[:, :, :, t:t+5000], (0, 1, 3, 2)),
                           np.transpose(input_dphase[:, :, :, t:t+5000], (0, 1, 3, 2))]
                          )[0, :, :]

        output_list.append(p)

    predicted_output = np.hstack(output_list).astype(np.float32)
    return predicted_output


def main(args):

    model_name = args.model_name
    audiofile = args.audiofile
    audio_folder = args.audio_folder

    save_key = 'exp3multif0'
    model_path = "./models/{}.pkl".format(save_key)
    model = models.build_model3()
    model.load_weights(model_path)
    thresh = 0.5

    # compile model

    model.compile(
        loss=utils_train.bkld, metrics=['mse', utils_train.soft_binary_accuracy],
        optimizer='adam'
    )
    print("Model compiled")

    # select operation mode and compute prediction
    if audiofile != "0":

        # predict using trained model
        predicted_output = get_single_test_prediction(
            model, audio_file=audiofile
        )

        df = pd.DataFrame(predicted_output.T)
        df.to_hdf(audiofile.replace('wav', 'h5'), 'mix', mode='a', complevel=9, complib='blosc', append=True, format='table')
        
        print(" > > > Multiple F0 prediction for {} exported as {}.".format(
            audiofile, audiofile.replace('wav', 'h5'))
        )

    elif audio_folder != "0":

        for audiofile in os.listdir(audio_folder):

            if not audiofile.endswith('wav'): continue

            # predict using trained model
            predicted_output = get_single_test_prediction(
                 model, audio_file=os.path.join(
                    audio_folder, audiofile)
            )

            df = pd.DataFrame(predicted_output.T)
            df.to_hdf(os.path.join(audio_folder, audiofile.replace('wav', 'h5')), 'mix', mode='a', complevel=9, complib='blosc', append=True, format='table')

            print(" > > > Multiple F0 prediction for {} exported as {}.".format(
                audiofile, os.path.join(
                    audio_folder, audiofile.replace('wav', 'h5')
                ))
            )
    else:
        raise ValueError("One of audiofile and audio_folder must be specified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Predict multiple F0 output of an input audio file or all the audio files inside a folder.")

    parser.add_argument("--model",
                        dest='model_name',
                        type=str,
                        help="Specify the ID of the model"
                             "to use for the prediction: model1 (Early/Deep) / "
                             "model2 (Early/Shallow) / "
                             "model3 (Late/Deep, recommended)")

    parser.add_argument("--audiofile",
                        dest='audiofile',
                        default="0",
                        type=str,
                        help="Path to the audio file to analyze. If using the folder mode, this should be skipped.")

    parser.add_argument("--audio_folder",
                        dest='audio_folder',
                        default="0",
                        type=str,
                        help="Directory with audio files to analyze. If using the audiofile mode, this should be skipped.")

    main(parser.parse_args())
