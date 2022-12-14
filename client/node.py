import os
from process_video import ProcessVideo
import socketio

sio = socketio.Client()

# Instantiate the ProcessVideo Class
process_video_instance = ProcessVideo()

@sio.event
def connect():
    print("I'm connected!")

@sio.event
def disconnect():
    print('unu')


@sio.event
def on_zip_chunk(data):
    print('Se recibió el chunk: ', data['chunk_name'])
    chunk_path = os.path.join('./', 'raw_chunks/', data['chunk_name'])
    with open(chunk_path, 'wb') as zip:
        zip.write(data['chunk_data']) 
    process_video_instance.extract_chunk(chunk_path, 'raw_frames')
    print('Se extrajo chunk: ', data['chunk_name'])
    sio.emit('check_chunk', {'xd': 'xd'})

@sio.event
def start_processing_chunk(data):
    send_processed_chunk()

def send_processed_chunk():
    process_video_instance.run()
    chunk_name = 'procc-chunk-' + sio.sid + '.zip'
    process_video_instance.divide_frames_in_chunks(
        chunk_name,
        'processed_frames',
        'processed_chunks'
    )
    raw_chunk_path = os.path.join('./', 'processed_chunks/', chunk_name)
    with open(raw_chunk_path, 'rb') as zip:
        data = zip.read()
        sio.emit(
            'on_processed_chunk', 
            {'chunk_name': chunk_name, 'chunk_data': data}
        )
        zip.flush()
    sio.emit('check_processed_chunk', {'xd':'xd'})

def main():
    sio.connect('http://localhost:8000')
    sio.emit('check_connected_peers', {'xd':'xd'})
    #send_processed_chunk()

if __name__ == '__main__':
    main()
    #asyncio.run(main())