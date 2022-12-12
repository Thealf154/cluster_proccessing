import os
from process_video import ProcessVideo
import asyncio
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
def xd(data):
    print('xd')

@sio.event
def on_raw_image(data):
    raw_frame_path = os.path.join('./', 'raw_frames/', data['frame_name'])
    with open(raw_frame_path, 'wb') as i:
        i.write(data['frame_data'])
        print('Frame escrito: ', data['frame_name'])

def main():
    sio.connect('http://localhost:8000')
    sio.emit('check_connected_peers', {'xd':'xd'})

if __name__ == '__main__':
    main()
    #asyncio.run(main())