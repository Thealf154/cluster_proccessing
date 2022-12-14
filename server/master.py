import logging
from process_video import ProcessVideo
from flask import Flask
from flask_cors import CORS
from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO
import sys
import os


logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s : %(message)s',
                    datefmt='%H:%M:%S', stream=sys.stdout)

# Manejar los peers
peers = []

# How many peers will work on the video
wanted_peers = 1
chunks = 0

# create a Socket.IO server
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger=True, engineio_logger=True)

process_video_instance = ProcessVideo('bad_apple.mp4')
logging.getLogger('flask_cors').level = logging.DEBUG


@socketio.event
def connect(auth):
    peer = {'sid': auth['sid'],
            'has_extracted_chunk': 0,
            'frames_to_process': []}
    peers.append(peer)
    print('Peer conectado: ', auth['sid'])


@socketio.event
def disconnect(sid):
    peers_updated = [peer for peer in peers if peer['sid'] != sid]
    peers = peers_updated
    print('Este peer se ha desconectado: ', sid)

    
@app.route("/request_chunk/<sid>")
def send_chunk(sid):
    raw_chunks_path = os.path.join('./', 'raw_chunks')
    raw_chunk_path = find_chunk(sid, os.listdir(raw_chunks_path))
    if raw_chunk_path:
        chunk = open_chunk(raw_chunk_path)
        return send_file(
            raw_chunk_path
        )
    else:
        return None

@app.route("/send_chunk/<sid>", methods=['POST'])
def receive_chunk(sid):
    chunk_path = os.path.join('./', 'processed_chunks/', str(str(sid) + '.zip'))
    if request.method == 'POST':
        f = request.files['file']
        f.save(dst=chunk_path, buffer_size=300)
        f.close()
        process_video_instance.extract_chunk(chunk_path, 'processed_frames')
        check_processed_chunks()


def check_processed_chunks():
    processed_chunks_path = os.path.join('./', 'processed_chunks')
    processed_chunks = os.listdir(processed_chunks_path)
    chunks_available = 0 
    for peer in peers:
        chunk_name = str(peer['sid']) + '.zip'
        if chunk_name in processed_chunks:
            chunks_available += 1
    if chunks_available == wanted_peers:
        make_final_video()

def make_final_video():
    process_video_instance.make_final_video()

def find_chunk(sid, dirs):
    chunk = None
    chunk_path = os.path.join('./', 'raw_chunks/')
    if (sid + '.zip') in dirs:
        chunk = os.path.join(chunk_path, (sid + '.zip'))
    return chunk

def open_chunk(chunk_path):
    with open(chunk_path, 'rb') as chunk:
        data = chunk.read() 
        return data

@socketio.event
def check_connected_peers():
    if len(peers) == wanted_peers:
        start_processing()

def divide_workload(raw_frames):
    dividend, residue = divmod(len(raw_frames), len(peers))
    workload = []
    for i in range(0, len(peers)):
        if i == 0:
            peers[i]['frames_to_process'] = raw_frames[i:dividend]
        else:
            start = (dividend * i) + 1
            end = dividend * (i + 1)
            peers[i]['frames_to_process'] = raw_frames[start:end]
    if residue != 0:
        peers[len(peers) - 1]['frames_to_process'].append(raw_frames[-residue])

def make_chunks():
    for peer in peers:
        chunk_name = str(peer['sid']) + '.zip'
        process_video_instance.divide_frames_in_chunks(
            chunk_name, 
            'raw_frames',
            'raw_chunks',
            peer['frames_to_process']
        )


def start_processing():
    #process_video_instance.recolect_frames()
    raw_frames = process_video_instance.get_raw_frames()
    divide_workload(raw_frames)
    #make_chunks()
    socketio.emit("chunks_ready")

if __name__ == '__main__':
    socketio.run(app, port=8000)