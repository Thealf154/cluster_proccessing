from multiprocessing import Pool
import cv2
import os
import numpy as np
from PIL import Image, ImageDraw
from concurrent.futures import ThreadPoolExecutor
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

def write_ascii_to_image(frame_name, frame_art):
    processed_frame_path = os.path.join('./', 'processed_frames/')
    processed_frame_file = os.path.join(processed_frame_path, frame_name)
    print("Frame escrito " + frame_name)
    img = Image.new('RGB', (480 * 2, 360), color = (255, 255, 255))
    d1 = ImageDraw.Draw(img)
    d1.text((0, 0), frame_art, fill =(0, 0, 0))
    img.save(processed_frame_file)
    print("XD")

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
    ascii_frames_name = []
    ascii_frames = []

    with Pool(5) as p:
        for result in p.map(create_frame_ascii_art, raw_frames):
            ascii_frames_name.append(result[0]) 
            ascii_frames.append(result[1]) 

    with ThreadPoolExecutor() as executor:
        for i in range(0, len(ascii_frames)):
            _ = executor.submit(write_ascii_to_image, ascii_frames_name[i], ascii_frames[i])