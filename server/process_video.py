from PIL import Image, ImageDraw, ImageFont
from multiprocessing import Pool
import cv2
import os
import ffmpeg
import subprocess
import asciify
import time
import logging
from zipfile import ZipFile

font_size = 10
font_path = os.path.join(os.getcwd(), 'ibm.ttf')
font = ImageFont.truetype(font_path, font_size)
original_dimensions = ()
new_dimensions = ()


class ProcessVideo:
    font = ImageFont.truetype("ibm.ttf", font_size)
    font_size = 10
    extracted_audio_name = 'extracted_audio.wav'
    output_video_name = 'output.avi'
    raw_frames = []
    original_dimensions = ()
    new_dimensions = ()
    logging.basicConfig(format='{asctime} [{levelname:<8}]: {message}', level=logging.DEBUG, style='{')
    logger = logging.getLogger('process-video')

    def __init__(self, video_name=None):
        self.original_video = video_name

    def run(self):
        self.raw_frames = self.get_raw_frames()
        self.original_dimensions = self.get_original_dimensions()
        self.new_dimensions = self.get_new_dimensions()

        with Pool(5) as p:
            p.map(self.create_frame_ascii_art, self.raw_frames)

    def make_final_video(self):
        self.raw_frames = self.get_raw_frames()
        self.original_dimensions = self.get_original_dimensions()
        self.new_dimensions = self.get_new_dimensions()
        self.join_frames()
        self.extract_audio()
        self.add_audio()

    def recolect_frames(self):
        frame_count = 0
        # Cargamos el vídeo a a un objeto de Videocapture
        vidcap = cv2.VideoCapture(self.original_video)
        while True:
            ret, frame = vidcap.read()
            if ret == False:
                vidcap.release()
                break
            else:
                frame_name = 'frame_' + str(frame_count) + '.png'
                full_frame_name = os.path.join('./', 'raw_frames/', frame_name)
                cv2.imwrite(full_frame_name, frame)
                #print("Frame extraído: " + frame_name)
                self.logger.debug('Frame {} extraído'.format(frame_name))
                frame_count += 1

    def create_frame_ascii_art(self, frame_name):
        raw_frame_file = os.path.join('./', 'raw_frames/', frame_name)
        frame = Image.open(raw_frame_file)
        frame_art = asciify.do(frame, self.new_dimensions)
        img = Image.new('RGB', self.original_dimensions, color=(255, 255, 255))
        d1 = ImageDraw.Draw(img)
        d1.multiline_text((0, 0), frame_art, fill=(
            0, 0, 0), spacing=(0.0), font=font)
        #print("Frame procesada: " + frame_name)
        self.logger.debug('Frame {} procesada'.format(frame_name))
        processed_frame_file = os.path.join(
            './', 'processed_frames/', frame_name)
        img.save(processed_frame_file)

    def write_ascii_to_image(self, frame_name, img):
        processed_frame_file = os.path.join(
            './', 'processed_frames/', frame_name)
        img.save(processed_frame_file)
        #print("Frame escrito " + frame_name)
        self.logger.debug('Frame {} convertido a ASCII'.format(frame_name))

    def get_raw_frames(self):
        raw_frames = []
        path = os.path.join('./', 'raw_frames/')
        frames_list = os.listdir(path=path)
        for frame in frames_list:
            raw_frames.append(frame)
        return raw_frames

    def get_processed_frames(self):
        processed_frames = []
        path = os.path.join('./', 'processed_frames/')
        frames_list = os.listdir(path=path)
        for frame in frames_list:
            processed_frames.append(frame)
        return processed_frames

    def get_new_dimensions(self):
        (old_width, old_height) = self.original_dimensions
        new_width = old_width / (font_size - 4)
        new_height = int((old_height / font_size) - 3)
        new_dim = (int(new_width), int(new_height))
        return new_dim

    def get_original_dimensions(self):
        frame_sample_path = os.path.join('./', 'raw_frames/', 'frame_0.png')
        frame_sample = Image.open(frame_sample_path)
        (old_width, old_height) = frame_sample.size
        return (old_width, old_height)

    def join_frames(self):
        path = os.path.join('./', 'processed_frames')
        frames_list = [img for img in os.listdir(path) if img.endswith(".png")]
        # Sacado de https://stackoverflow.com/questions/44947505/how-to-make-a-movie-out-of-images-in-python
        video = cv2.VideoWriter(self.output_video_name, cv2.VideoWriter_fourcc(
            *'XVID'), 30, self.original_dimensions)
        for i in range(0, len(frames_list)):
            frame_name = 'frame_{}.png'.format(i)
            frame = cv2.imread(os.path.join(path, frame_name))
            video.write(frame)
        video.release()

    def extract_audio(self):
        path = os.path.join('./', self.original_video)
        command = "ffmpeg -i {} -ab 160k -ac 2 -ar 44100 -vn {}".format(
            path, self.extracted_audio_name)
        subprocess.call(command, shell=True)

    def add_audio(self):
        video_path = os.path.join('./', self.output_video_name)
        audio_path = os.path.join('./', self.extracted_audio_name)
        output_path = os.path.join('./', 'finished_video.avi')
        input_video = ffmpeg.input(video_path)
        input_audio = ffmpeg.input(audio_path)
        ffmpeg.concat(input_video, input_audio, v=1,
                      a=1).output(output_path).run()

    def divide_frames_in_chunks(self, chunk_name, frame_type, chunk_destination):
        self.logger.debug('Se está haciendo el chunk: ', chunk_name)
        zip_path = os.path.join('./', str(chunk_destination))
        zip_path = os.path.join(zip_path, chunk_name)
        file_path = os.path.join('./', frame_type)
        frames = self.get_all_file_paths(file_path)
        with ZipFile(zip_path, 'w') as zip:
            for frame in frames:
                zip.write(frame, os.path.relpath(frame, file_path))
        self.logger.debug('Se terminó el chunk: ', chunk_name)

    @staticmethod
    def get_all_file_paths(directory):
          # initializing empty file paths list
        file_paths = []
    
        # crawling through directory and subdirectories
        for root, directories, files in os.walk(directory):
            for filename in files:
                # join the two strings in order to form the full filepath.
                filepath = os.path.join(root, filename)
                file_paths.append(filepath)
    
        # returning all file paths
        return file_paths   

    @staticmethod
    def extract_chunk(chunk_path, destination):
        with ZipFile(chunk_path) as zip:
            extract_path = os.path.join('./', str(destination) + '/')
            zip.extractall(extract_path)

    @staticmethod
    def clean():
        processed_chunks_path
        processed_chunks_path

if __name__ == '__main__':
    start_time = time.time()
    xd = ProcessVideo('bad_apple.mp4')
    #xd.run()
    #xd.say_hello()
    print("--- %s seconds ---" % (time.time() - start_time))
