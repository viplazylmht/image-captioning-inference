from __future__ import absolute_import, generators
from __future__ import division
from __future__ import print_function

from worker import TfThread
import time
import os
import gdown
import threading

from im2txt.inference_utils import caption_generator, vocabulary
from im2txt import configuration, inference_wrapper

import math
import io

import tensorflow as tf
print(tf.__version__)

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.INFO)
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

queueLock = threading.Lock()

class TfThreadSync (TfThread):

    def run(self):
        print("Starting " + self.name)

        print("Downloading model parameters")
        gdown.download(
            'https://drive.google.com/uc?id=1r4-9FEIbOUyBSvA-fFVFgvhFpgee6sF5')

        os.system('tar -xf im2txt_model_parameters.tar.gz')
        os.system('rm im2txt_model_parameters.tar.gz')

        checkpoint_path = "./modelParameters/newmodel.ckpt-2000000"
        vocab_file = "./im2txt/data/Hugh/word_counts.txt"

        g = tf.Graph()
        with g.as_default():
            model = inference_wrapper.InferenceWrapper()
            restore_fn = model.build_graph_from_config(configuration.ModelConfig(),
                                                    checkpoint_path)
        g.finalize()

        print("G done")

        # Create the vocabulary.
        vocab = vocabulary.Vocabulary(vocab_file)

        print("vocab done")

        with tf.Session(graph=g) as sess:
            # Load the model from checkpoint.

            print("tf session sync opened")
            restore_fn(sess)

            # Prepare the caption generator. Here we are implicitly using the default
            # beam search parameters. See caption_generator.py for a description of the
            # available beam search parameters.
            generator = caption_generator.CaptionGenerator(model, vocab)

            print("generator sync initalized")

            while True:
                process_data_session(self, self.q, sess, generator, vocab)
                time.sleep(1)

        print("Exiting " + self.name)

def process_data_session(thread_task, q, sess, generator, vocab):
    data = None

    queueLock.acquire()
    if not q.empty():
        data = q.get()
    queueLock.release()

    if data:
        print(f"{thread_task.name} processing {data}...")
        # todo
        job_id, filepath = data['job_id'], data['filepath']

        thread_task.updateStatus(job_id, {'status': 'ongoing', 'result': ''})
        res = predict_task(sess, generator, vocab, filepath)

        if res:
            thread_task.updateStatus(
                job_id, {'status': 'completed', 'result': res})

    time.sleep(1)

    return None

def predict_task(sess, generator, vocab, filepath):
    with tf.gfile.GFile(filepath, "rb") as f:
        image = f.read()
    captions = generator.beam_search(sess, image)

    result = []
    result.append(f"Captions for image {os.path.basename(filepath)}:")

    for i, caption in enumerate(captions):
        # Ignore begin and end words.
        sentence = [vocab.id_to_word(w) for w in caption.sentence[1:-1]]
        sentence = " ".join(sentence)

        result.append({str(i): [sentence, math.exp(caption.logprob)]})

    return result