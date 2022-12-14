import os
from process_video import ProcessVideo
import socketio
import requests
import math
import random

sio = socketio.Client()

# Instantiate the ProcessVideo Class
process_video_instance = ProcessVideo()
url = 'http://localhost:8000/'

@sio.event
def connect():
    print("I'm connected!")

@sio.event
def disconnect():
    print('Estoy desconectado')

@sio.event
def chunks_ready():
    url_with_sid = url + 'request_chunk/' + str(id)
    response = requests.get(
        url=url_with_sid
    )
    chunk_name = str(id) + '.zip'
    chunk_path = os.path.join('./', 'raw_chunks/', chunk_name)
    """
    save_chunk(chunk_path, response.content)
    extract_chunk_destination = os.path.join('./', 'raw_frames/')
    process_video_instance.extract_chunk(
        destination=extract_chunk_destination,
        chunk_path=chunk_path
    )
    """
    process_frames()

def save_chunk(chunk_path, chunk_data):
    with open(chunk_path, 'wb') as chunk:
        chunk.write(chunk_data)

def process_frames():
    process_video_instance.run()
    processed_frames = process_video_instance.get_processed_frames()
    process_video_instance.divide_frames_in_chunks(
        chunk_name,
        'processed_frames',
        'processed_chunks',
        processed_frames
    )   
    chunk_name = str(id) + '.zip'
    processed_chunk_path = os.path.join('./', 'processed_chunks/', chunk_name)
    with open(processed_chunk_path, 'rb') as zip:
        data = zip.read()
        url_with_sid = url + 'send_chunk/' + str(id)
        requests.post(
            url=url_with_sid,
            files={'file': data},
            headers={
               "enctype" : "multipart/form-data" 
            }
        )

def get_sid():
    sid = math.ceil(random.random() * 100)
    return sid

id = get_sid()

def main():
    sio.connect('http://localhost:8000', auth={'sid': id})
    sio.emit('check_connected_peers')


if __name__ == '__main__':
    main()