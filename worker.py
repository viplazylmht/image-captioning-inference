import os

from models import heavy_task

import queue
import threading
import time

import hashlib
import gdown

exitFlag = 0
queueLock = threading.Lock()


class TfThread (threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = queue.Queue()

        self.results = {}

    def run(self):
        print("Starting " + self.name)

        print("Downloading model parameters")
        gdown.download(
            'https://drive.google.com/uc?id=1r4-9FEIbOUyBSvA-fFVFgvhFpgee6sF5')

        os.system('tar -xf im2txt_model_parameters.tar.gz')
        os.system('rm im2txt_model_parameters.tar.gz')

        while True:
            process_data(self, self.q)
            time.sleep(1)

        print("Exiting " + self.name)

    def updateStatus(self, job_id, status):
        if job_id in self.results:
            self.results[job_id] = status

            return self.results[job_id]
        else:
            return {'result': 'error', 'message': 'job not found'}

    def getResult(self, job_id):
        if job_id in self.results:
            return self.results[job_id]
        else:
            return {'result': 'error', 'message': 'job not found'}

    def md5(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def pushJob(self, filepath):
        # return job_id
        # create job_id first
        job_id = self.md5(filepath)

        queueLock.acquire()

        self.q.put({'job_id': job_id, 'filepath': filepath})

        queueLock.release()

        self.results[job_id] = {'status': 'queued', 'result': ''}

        return job_id


def process_data(thread_task, q):
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
        res = heavy_task(filepath)

        if res:
            thread_task.updateStatus(
                job_id, {'status': 'completed', 'result': res})

    time.sleep(1)

    return None
