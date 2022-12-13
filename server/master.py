import socketio
import os
import logging
from process_video import ProcessVideo
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
from flask import Flask
import sys
import time

logger = logging.getLogger()
logging.basicConfig(format='%(asctime)s : %(message)s',
                    datefmt='%H:%M:%S', stream=sys.stdout)

# Manejar los peers
peers = []

# How many peers will work on the video
wanted_peers = 3

# create a Socket.IO server
sio = socketio.Server(async_mode='threading', max_http_buffer_size=(80_000_000))
app = Flask(__name__)
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

process_video_instance = ProcessVideo('bad_apple.mp4')


@sio.event
def connect(sid, environ):
    peer = {'sid': sid,
            'raw_frames_sent': 0,
            'processed_frames_received': 0,
            'frames_to_process': []}
    peers.append(peer)
    print('Peer conectad: ', sid)


@sio.event
def check_connected_peers(sid, data):
    if len(peers) == wanted_peers:
        start_processing()

def check_processed_chunks():
    processed_chunks_path = os.path.join('./', 'processed_chunks')
    if len(os.listdir(processed_chunks_path)) == len(peers):
        process_video_instance.make_final_video()

@sio.event
def disconnect(sid):
    peers_updated = [peer for peer in peers if peer['sid'] != sid]
    peers = peers_updated
    print('Este peer se ha desconectado: ', sid)

@sio.event
def on_processed_chunk(sid, data):
    print('Se recibió el chunk: ', data['chunk_name'])
    chunk_path = os.path.join('./', 'processed_chunks/', data['chunk_name'])
    with open(chunk_path, 'wb') as zip:
        zip.write(data['chunk_data']) 
    process_video_instance.extract_chunk(chunk_path, 'processed_frames')
    check_processed_chunks()

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
        peers[len(peers)]['frames_to_process'].append(raw_frames[-residue])


def start_processing():
    # process_video_instance.recolect_frames()
    raw_frames = process_video_instance.get_raw_frames()
    divide_workload(raw_frames)
    make_chunks()
    with ThreadPoolExecutor(max_workers=wanted_peers) as executor:
        chunk_path = os.path.join('./', 'raw_chunks/')
        executor.map(send_chunk, os.listdir(chunk_path))

def make_chunks():
    for peer in peers:
        chunk_name = str(peer['sid']) + '.zip'
        process_video_instance.divide_frames_in_chunks(
            chunk_name, 
            'raw_frames',
            'raw_chunks'
        )

def send_chunk(chunk_name):
    raw_chunk_path = os.path.join('./', 'raw_chunks/', chunk_name)
    with open(raw_chunk_path, 'rb') as zip:
        data = zip.read()
        sio.emit(
            'on_zip_chunk', 
            {'chunk_name': chunk_name, 'chunk_data': data},
            to=(str(chunk_name).split('.').pop(0))
        )
        zip.flush()

if __name__ == '__main__':
    # web.run_app(app,port=5000)
    #eventlet.wsgi.server(eventlet.listen(('localhost', 5000)), app)
    app.run(port=8000)