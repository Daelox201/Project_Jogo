#Librerias necesarias para el proyecto
import string
import socket
import threading
import tkinter as tk
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from tkinter import scrolledtext
import os

import pygame

# Configuración del servidor
SERVER_HOST = '192.168.137.138'
SERVER_PORT = 5555

#Nombre del directorio de la musica
MUSIC_DIRECTORY = 'musica'

# Configuración de la base de datos MySQL (XAMPP)


uri = "mongodb+srv://Admin:Da3lox#2022@cluster0.qwry9o4.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
cliente = MongoClient(uri, server_api=ServerApi('1'))



# Configuración de la interfaz gráfica del servidor
server_window = tk.Tk()
server_window.title("Music Sharing Server")

log_text = scrolledtext.ScrolledText(server_window, wrap=tk.WORD, width=40, height=10)
log_text.pack(padx=10, pady=10)

start_button = tk.Button(server_window, text="Iniciar Servidor", command=lambda: threading.Thread(target=start_server).start())
start_button.pack(pady=10)

# Send a ping to confirm a successful connection
try:
    cliente.admin.command('ping')
    log_text.insert(tk.END,f'Conexion a base de datos exitosa\n')
    db = cliente["mydb"]
    music_collection = db["canciones"]
except Exception as e:
        log_text.insert(tk.END,f'Error: {e}\n')





# Función para manejar la conexión de un cliente
def handle_client(client_socket):

    user_address = None

    try:
        #Se detecta que el usario ingrese y se optene la direccion del dispositivo conectado
        user_address = client_socket.getpeername()
        log_text.insert(tk.END, f'Usuario conectado desde {user_address}\n')

        #Recibe las solicitudes del cliente, como subir canciones, obtener la lista, reproducir y 

        while True:
            #Recive datos del cliente del tipo 1024 bits y los tranforma en cadena de carateres
            request = client_socket.recv(1024).decode('latin-1')

            if not request:
                break

            
            if request.startswith('check_existence'):
                _, file_name = request.split(':', 1)
                
                file_name = clean_filename(file_name)
                file_path = os.path.join(MUSIC_DIRECTORY, file_name)

                if os.path.exists(file_path):
                    client_socket.send('EXISTS'.encode('utf-8'))
                else:
                    client_socket.send('OK'.encode('utf-8'))
                continue 


            #Comprueba que si el usuario a enviado la solicitud 
            if request.startswith('subir_cancion'):
                print("Subir Cancion")
                #Divide la solicitud para obtener el nombre del archivo y el tamaño
                _, file_name,file_size = request.split(':', 2)

                #cargar la funcion de limpiar el nombre del archivo para eliminar caracteres no deseados
                file_name = clean_filename(file_name)

                #tamaño del archivo
                file_size = int(file_size)
                file_path = os.path.join(MUSIC_DIRECTORY, file_name)

                
                                
                os.makedirs(os.path.dirname(file_path), exist_ok=True)#Crea el directorio si no existe con los archivos necesarios
                received_byte = 0
                with open(file_path, 'wb') as file:
                    #Escribir el archivo completo para pasarlos del cliente al servidor sin problemas
                    while received_byte < file_size:
                        data = client_socket.recv(1024)
                        received_byte += len(data)
                        file.write(data)
                  
                

                    

                    cancion = {
                        "Nom_Music": file_name,
                        "Ruta_Music": file_path
                    }

                    result = music_collection.insert_one(cancion)
                    print(result)

            if request.startswith('obtener_lista'):
                print('obtener')
                enviar_lista(client_socket)

            if request.startswith('reproducir_cancion'):
                print("reproducir")
                _, song_name = request.split(':', 1)
                # reproducir_cancion(song_name)
                print(song_name)
                reproducir_cancion(song_name)
                

    except ConnectionResetError:
        pass  # Manejar la desconexión del cliente

    finally:
        if user_address:
            # Cerrar la conexión del cliente
            log_text.insert(tk.END, f'Usuario desconectado desde {user_address}\n')
            client_socket.close()

def clean_filename(filename):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_filename = ''.join(c if c in valid_chars else '_' for c in filename)
    return cleaned_filename

def enviar_lista(client_socket):
    
    songs = [song["Nom_Music"] for song in music_collection.find()]
    client_socket.send(str(songs).encode('utf-8'))


connected_clients = []

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    log_text.insert(tk.END, f'Servidor escuchando en {SERVER_HOST}:{SERVER_PORT}\n')

    while True:
        client_socket, addr = server_socket.accept()
        connected_clients.append(client_socket)  # Agregar nuevo cliente a la lista
        threading.Thread(target=handle_client, args=(client_socket,)).start()


def reproducir_cancion(song_name):
    print('Reproducir 2')
    ruta = ''
    for song in music_collection.find():
        if(song["Nom_Music"] == song_name):
            ruta = song["Ruta_Music"]
    
    if ruta:
  
        pygame.mixer.init()
        pygame.init()
        pygame.mixer.music.load(ruta)
        pygame.mixer.music.play()

        clock = pygame.time.Clock()
        clock.tick(10)  # Ajusta el valor del tick a la velocidad de la canción
    
        while pygame.mixer.music.get_busy():
            pygame.event.poll()
            clock.tick(10)  # Controla la velocidad del bucle
        
        pygame.mixer.music.stop()
        


# Configuración para cerrar el programa correctamente

server_window.mainloop()
