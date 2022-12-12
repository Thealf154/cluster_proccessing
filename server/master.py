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
max_peers = 3

# create a Socket.IO server
sio = socketio.Server(async_mode='threading')
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
    start_processing()

@sio.event
def disconnect(sid):
    peers_updated = [peer for peer in peers if peer['sid'] != sid]
    peers = peers_updated
    print('Este peer se ha desconectado: ', sid)


@sio.event
def handle_processed_image(sid, frame_data):
    try:
        processed_frame_file = os.path.join(
            './', 'processed_frames/', frame_data['frame_name'])
        with open(processed_frame_file, 'wb') as i:
            i.write(frame_data['frame'])
            logger.info('Frame {} fue guardado exitosamente'.format(
                frame_data['name']))
    except Exception as e:
        logger.error('Algo paso mal', e)


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
        peers[len(peers)].append(raw_frames[-residue])


def parse_workload(raw_frames):
    dividend, residue = divmod(len(raw_frames), len(peers))
    workload = []
    for i in range(0, len(peers)):
        if i == 0:
            for j in raw_frames[i:dividend]:
                workload.append({'sid': peers[i]['sid'], 'frame_name': j})
        else:
            start = (dividend * i) + 1
            end = dividend * (i + 1)
            for j in raw_frames[start:end]:
                workload.append({'sid': peers[i]['sid'], 'frame_name': j})
    if residue != 0:
        peers[len(peers)].append(raw_frames[-residue])

    return workload


def start_processing():
    # process_video_instance.recolect_frames()
    raw_frames = process_video_instance.get_raw_frames()
    workload = parse_workload(raw_frames)
    with ThreadPoolExecutor(max_workers=max_peers) as executor:
        future_to_send_frame = {executor.submit(
            send_raw_frame, work['sid'], work['frame_name']): work for work in workload}
        for future in concurrent.futures.as_completed(future_to_send_frame):
            url = future_to_send_frame[future]
        try:
            data = future.result()
        except Exception as exc:
            print('%r generated an exception: %s' % (url, exc))


def send_raw_frame(sid, raw_frame):
    try:
        raw_frame_path = os.path.join('./', 'raw_frames/', raw_frame)
        with open(raw_frame_path, 'rb') as frame:
            data = frame.read() 
            os.wait()
            sio.emit('on_raw_image', {
                     'frame_name': raw_frame, 'frame_data': data}, to=sid)
            print('Frame envíado: ', raw_frame)
            time.sleep(0.5)
    except Exception as exc:
        print('Error: ', exc)


if __name__ == '__main__':
    # web.run_app(app,port=5000)
    #eventlet.wsgi.server(eventlet.listen(('localhost', 5000)), app)
    app.run(port=5000)
