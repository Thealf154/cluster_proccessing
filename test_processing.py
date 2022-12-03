from multiprocessing import Pool
import cv2
import os
import numpy as np
from PIL import Image
import concurrent.futures
import asciify

def recolect_frames(video_name):
    frame_count = 0
    # Cargamos el vídeo a a un objeto de Videocapture
    vidcap = cv2.VideoCapture(video_name)
    while True:
        ret, frame = vidcap.read()
        if ret == False:
            vidcap.release()
            break
        else:
            frame_name = 'frame_' + str(frame_count) + '.png'
            full_frame_name = os.path.join('./', 'raw_frames/', frame_name)
            cv2.imwrite(full_frame_name, frame)
            frame_count += 1

def create_frame_ascii_art(frame_name):
    raw_frame_path = os.path.join('./', 'raw_frames/')
    raw_frame_file = os.path.join(raw_frame_path, frame_name)
    ascii_art_frame = asciify.runner(raw_frame_file)
    print("Frame procesada: " + frame_name)
    return [frame_name, ascii_art_frame]

def write_ascii_to_image(frame_art, frame_name):
    processed_frame_path = os.path.join('./', 'processed_frames/')
    processed_frame_file = os.path.join(processed_frame_path, frame_name)
    print("Frame escrito " + frame_name)
    img = Image.new('RGB', (480, 360), color = (255, 255, 255))
    img.save(processed_frame_file, frame_art)

def get_raw_frames():
    raw_frames = []
    path = os.path.join('./', 'raw_frames/')
    frames_list = os.listdir(path=path)
    for frame in frames_list:
        raw_frames.append(frame) 
    return raw_frames

def get_processed_frames():
    processed_frames = []
    path = os.path.join('./', 'processed_frames/')
    frames_list = os.listdir(path=path)
    for frame in frames_list:
        processed_frames.append(frame) 
    return processed_frames

# Iniciamos el servidor de administración
if __name__ == '__main__':
    # recolect_frames('bad_apple.mp4')
    raw_frames = get_raw_frames()
    ascii_frames = []
    ascii_frame_names = []

    with Pool(5) as p:
        for result in p.map(create_frame_ascii_art, raw_frames):
            ascii_frames.append(result[0]) 
            ascii_frame_names.append(result[1]) 

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(write_ascii_to_image, ascii_frames, ascii_frame_names, 60)}
        for future in concurrent.futures.as_completed(future_to_url):
            frame = future_to_url[future]
            try:
                data = future.result()
            except Exception as exc:
                print('%r generated an exception: %s' % (frame, exc))