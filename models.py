from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
import os
import io

import tensorflow as tf
#import error? : pip install numpy --upgrade
print(tf.__version__)

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.INFO)
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

from im2txt import configuration, inference_wrapper

from im2txt.inference_utils import caption_generator, vocabulary

def heavy_task(filepath):
    # Build the inference graph.
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

        print("tf session opened")
        restore_fn(sess)

        # Prepare the caption generator. Here we are implicitly using the default
        # beam search parameters. See caption_generator.py for a description of the
        # available beam search parameters.
        generator = caption_generator.CaptionGenerator(model, vocab)

        print("generator initalized")

        with tf.gfile.GFile(filepath, "rb") as f:
            image = f.read()
        captions = generator.beam_search(sess, image)

        result = []
        result.append(f"Captions for image {os.path.basename(filepath)}:")

        for i, caption in enumerate(captions):
            # Ignore begin and end words.
            sentence = [vocab.id_to_word(w) for w in caption.sentence[1:-1]]
            sentence = " ".join(sentence)

            result.append({ str(i): [sentence, math.exp(caption.logprob)]})

        return result
