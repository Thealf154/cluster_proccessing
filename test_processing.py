from multiprocessing import Pool
import cv2
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor
import ffmpeg
import subprocess
import asciify
import time

font_size = 10
font = ImageFont.truetype("ibm.ttf", font_size)
original_dimensions = ()
new_dimensions = ()

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
    raw_frame_file = os.path.join('./', 'raw_frames/', frame_name)
    frame = Image.open(raw_frame_file)
    frame_art = asciify.do(frame, new_dimensions)
    img = Image.new('RGB', original_dimensions, color = (255, 255, 255))
    d1 = ImageDraw.Draw(img)
    d1.multiline_text((0, 0), frame_art, fill =(0, 0, 0), spacing=(0.0), font=font)
    print("Frame procesada: " + frame_name)
    processed_frame_file = os.path.join('./', 'processed_frames/', frame_name)
    img.save(processed_frame_file)

def write_ascii_to_image(frame_name, img):
    processed_frame_file = os.path.join('./', 'processed_frames/', frame_name)
    img.save(processed_frame_file)
    print("Frame escrito " + frame_name)

def get_raw_frames():
    raw_frames = []
    path = os.path.join('./', 'raw_frames/')
    frames_list = os.listdir(path=path)
    for frame in frames_list:
        raw_frames.append(frame) 
    return raw_frames

def get_new_dimensions(old_dimensions):
    (old_width, old_height) = old_dimensions
    new_width = old_width / (font_size - 4)
    new_height = int((old_height / font_size) - 3)
    new_dim = (int(new_width), int(new_height))
    return new_dim

def get_original_dimensions():
    frame_sample_path = os.path.join('./', 'raw_frames/', 'frame_0.png')
    frame_sample = Image.open(frame_sample_path)
    (old_width, old_height) = frame_sample.size
    return (old_width, old_height)

def join_frames(video_name):
    path = os.path.join('./', 'processed_frames')
    frames_list = [img for img in os.listdir(path) if img.endswith(".png")]
    # Sacado de https://stackoverflow.com/questions/44947505/how-to-make-a-movie-out-of-images-in-python
    video = cv2.VideoWriter(video_name, cv2.VideoWriter_fourcc(*'XVID'), 30, original_dimensions)
    for i in range(0, len(frames_list)):
        frame_name = 'frame_{}.png'.format(i)
        frame = cv2.imread(os.path.join(path, frame_name))
        video.write(frame)
        #video = cv2.VideoWriter(video_name, 0, 1, original_dimensions)
    video.release()


def extract_audio(original_video_name, output_video_name):
    path = os.path.join('./', original_video_name)
    command = "ffmpeg -i {} -ab 160k -ac 2 -ar 44100 {} -vn ".format(path, output_video_name)
    subprocess.call(command, shell=True)

def add_audio(video_name, audio_name):
    video_path = os.path.join('./', video_name)
    audio_path = os.path.join('./', audio_name)
    output_path = os.path.join('./', 'finished_video.avi')
    input_video = ffmpeg.input(video_path)
    input_audio = ffmpeg.input(audio_path)
    ffmpeg.concat(input_video, input_audio, v=1, a=1).output(output_path).run()

# Iniciamos el servidor de administración
if __name__ == '__main__':
    start_time = time.time()

    # Recolectar frames del video original
    original_video_name = 'bad_apple.mp4'
    recolect_frames(original_video_name)

    # Conseguir información del primer frame como base del vídeo
    original_dimensions = get_original_dimensions()
    new_dimensions = get_new_dimensions(original_dimensions)

    # Procesar los frames a ascii
    raw_frames = get_raw_frames()
    with Pool(5) as p:
        p.map(create_frame_ascii_art, raw_frames)

    extracted_audio_name = 'extracted_audio.wav'
    output_video_name = 'output.avi'

    # Unir los frames y añadir audio al vídeo
    join_frames(original_video_name)
    extract_audio(original_video_name)
    add_audio(output_video_name, extracted_audio_name)

    print("--- %s seconds ---" % (time.time() - start_time))