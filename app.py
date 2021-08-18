from flask_cors import CORS
from flask import Flask, request, json, jsonify, send_from_directory, flash, redirect, render_template
import json
import io
import os
import subprocess

from werkzeug.utils import secure_filename

from flask_sqlalchemy import SQLAlchemy

from worker import TfThread
from workerSync import TfThreadSync

UPLOAD_FOLDER = 'static/UPLOAD'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__, template_folder='templates',  # Name of html file folder
            static_folder='static')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '7d441f27d2174527567d441fasd1276a'

# app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

CORS(app)

# thread_task = TfThread(10, 'tfthread01')
thread_task = TfThreadSync(10, 'tfthreadSync01')
thread_task.start()


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_file_extension(filepath):
    ext = subprocess.check_output(f"file {filepath} | cut -d ',' -f 1 | cut -d ' ' -f 2", shell='True').decode('utf-8')[:-1]
    return ext.lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET"])
def main():
    return render_template('index.html')


@app.route("/api/v1/captionme", methods=["POST"])
def captionme():
    print('log captionme')

    if 'file' not in request.files:
        return json.dumps({'error': "File not found"}), 406
    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return json.dumps({'error': "File not found"}), 406
    if file and allowed_file(file.filename):

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if not check_file_extension(f"{UPLOAD_FOLDER}/{filename}"):
            # client have trick on file extension, reject
            os.system(f"rm {UPLOAD_FOLDER}/{filename}")
            print("file checker not pass, rejecting...")
            return json.dumps({'error': "File empty or not allowed"}), 406
    
        job_id = thread_task.pushJob(f"{UPLOAD_FOLDER}/{filename}")

        print(job_id)

        res = {'job_id': job_id}
        return json.dumps({"result": res})
    else:
        return json.dumps({'error': "File not found or not acceptable"}), 406


@app.route("/api/v1/results/<job_key>", methods=['GET'])
def get_results(job_key):

    job = thread_task.getResult(job_key)

    print(job)

    if job['status'] == 'completed':
        return json.dumps(job), 200
    else:
        return json.dumps(job), 202


@app.route("/cleanmee", methods=['GET', 'POST'])
def cleanmee():
    if request.method == 'GET':
        return render_template('clean.html')
    elif request.method == 'POST':
        text = request.form.get('text')
        print(text)

        res = {}

        if text:
            if text == os.getenv('CLEAN_PASSWORD'):
                # todo: clean all upload file
                os.system('rm {UPLOAD_FOLDER}/*')
                os.system('touch {UPLOAD_FOLDER}/dummy')

                res = {'message': "UPLOAD folder cleaned. Yay!"}

            elif text == os.getenv('SECRET_CODE'):
                res = {'message': "You got the secret. Yay!"}
            else:   
                res = {'message': f"Repeat with me: {text}" if len(text) < 100 else "Too much characters!" }
        else:
            res = {'message': "Why you send me nothing?"}

    return json.dumps(res)


def run():
    app.run(threaded=True, host='0.0.0.0', port=int(
        os.getenv('PORT') if os.getenv('PORT') else 5000))
    # app.run()


run()

thread_task.join()  # wait for all task done
