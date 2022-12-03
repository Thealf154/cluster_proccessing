import socketio
import cv2
import os

# Crear el server de sockets
sio = socketio.Server()

# Amarrar el server de sockets con un WSIG, que es una interfaz para procesar
# las peticiones del web server por medio de Python
app = socketio.WSGIApp(sio)

# Lista de esclavos disponibles
esclavos = []

@sio.event
def connect(sid, environ, auth):
    """Evento que maneja la conexión de un esclavo al servidor de sockets

    Parameters
    ----------
    sid: str
        El id del socket
    environ: dictionary
        Continene la información de la petición HTTP y sus encabezados
    auth: str
        Detalles de autenticación
    Returns
    -------
    """

    esclavos.append(sid)
    print('Este esclavo está listo para trabajar: ', sid)

@sio.event
def disconnect(sid):
    print('disconnect ', sid)

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
    
# Iniciamos el servidor de administración
if __name__ == '__main__':
    recolect_frames('bad_apple.mp4')