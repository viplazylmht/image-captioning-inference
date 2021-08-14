# download minianaconda: https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# https://github.com/HughKu/Im2txt.git

# install-pkg python3.7 python3-distutils

#https://notes.webutvikling.org/get-python-virtualenv-pip-without-sudo/
#/opt/virtualenvs/python3/bin/pip

#/home/runner/.apt/usr/bin/python3.7
#pip https://files.pythonhosted.org/packages/52/e1/06c018197d8151383f66ebf6979d951995cf495629fc54149491f5d157d0/pip-21.2.4.tar.gz

#setuptools https://files.pythonhosted.org/packages/db/e2/c0ced9ccffb61432305665c22842ea120c0f649eec47ecf2a45c596707c4/setuptools-57.4.0.tar.gz
# tar xvfz setuptools-0.6c11.tar.gz

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math
import os

from flask_cors import CORS
from flask import Flask, request, json, jsonify, send_from_directory, flash, redirect, render_template
import json
import io

from werkzeug.utils import secure_filename

import gc

UPLOAD_FOLDER = 'static/UPLOAD'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__, template_folder='templates',  # Name of html file folder
	static_folder='static')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '7d441f27d2174527567d441fasd1276a'

CORS(app)

import tensorflow as tf
#import error? : pip install numpy --upgrade
print(tf.__version__)

tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.INFO)
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

from im2txt import configuration, inference_wrapper

from im2txt.inference_utils import caption_generator, vocabulary

print("Import Done")

checkpoint_path = "./modelParameters/newmodel.ckpt-2000000"
vocab_file = "./im2txt/data/Hugh/word_counts.txt"

# Build the inference graph.
g = tf.Graph()
with g.as_default():
    model = inference_wrapper.InferenceWrapper()
    restore_fn = model.build_graph_from_config(configuration.ModelConfig(),
                                               checkpoint_path)
g.finalize()

# Create the vocabulary.
vocab = vocabulary.Vocabulary(vocab_file)

with tf.Session(graph=g) as sess:
    # Load the model from checkpoint.
    restore_fn(sess)

    # Prepare the caption generator. Here we are implicitly using the default
    # beam search parameters. See caption_generator.py for a description of the
    # available beam search parameters.
    generator = caption_generator.CaptionGenerator(model, vocab)

    def caption_file(filename):
        print(filename)
        with tf.gfile.GFile(f"./static/UPLOAD/{filename}", "rb") as f:
            image = f.read()
        captions = generator.beam_search(sess, image)

        result = []
        result.append(f"Captions for image {filename}:")

        for i, caption in enumerate(captions):
            # Ignore begin and end words.
            sentence = [vocab.id_to_word(w) for w in caption.sentence[1:-1]]
            sentence = " ".join(sentence)

            result.append({ str(i): [sentence, math.exp(caption.logprob)]})

        return result

    def allowed_file(filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route("/", methods=["GET"])
    def main():
        return render_template('index.html')

    @app.route("/api/prepare", methods=["POST"])
    def prepare():
        print('log prepare')
        
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            res = caption_file(filename)
            gc.collect()
            
            return json.dumps({"result": res})
    
    gc.collect()

    app.run(host='0.0.0.0', port=8080)