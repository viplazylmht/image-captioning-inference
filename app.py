from flask_cors import CORS
from flask import Flask, request, json, jsonify, send_from_directory, flash, redirect, render_template
import json
import io
import os

from werkzeug.utils import secure_filename

from flask_sqlalchemy import SQLAlchemy

from worker import TfThread

UPLOAD_FOLDER = 'static/UPLOAD'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__, template_folder='templates',  # Name of html file folder
	static_folder='static')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '7d441f27d2174527567d441fasd1276a'

#app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)

CORS(app)

thread_task = TfThread(10, 'tfthread01')
thread_task.start()

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=["GET"])
def main():
    return render_template('index.html')

@app.route("/api/v1/captionme", methods=["POST"])
def captionme():
    print('log captionme')
    
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
        # this import solves a rq bug which currently exists
        from models import heavy_task

        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        job_id = thread_task.pushJob(f"{UPLOAD_FOLDER}/{filename}")

        print(job_id)
        
        res = {'job_id': job_id}
        return json.dumps({"result": res})
    else:
        return "File not found or not acceptable", 406

@app.route("/api/v1/results/<job_key>", methods=['GET'])
def get_results(job_key):

    job = thread_task.getResult(job_key)
    
    print(job)

    if job['status'] == 'completed':
        return str(job), 200
    else:
        return str(job), 202

def run():
    app.run(threaded=True, host='0.0.0.0', port=int(os.getenv('PORT') if os.getenv('PORT') else 5000))
    #app.run()

run()

thread_task.join() # wait for all task done
