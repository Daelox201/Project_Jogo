#Librerias necesarias para el proyecto
import string
import socket
import threading
import tkinter as tk
from tkinter import messagebox
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from tkinter import scrolledtext
import os

import pygame

# Configuración del servidor
SERVER_HOST = '192.168.137.1'
SERVER_PORT = 5555

#Nombre del directorio de la musica
MUSIC_DIRECTORY = 'musica'

server_socket = None

# Crear un Lock para sincronización
lock = threading.Lock()


uri = "mongodb+srv://Admin:Da3lox#2022@cluster0.qwry9o4.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
cliente = MongoClient(uri, server_api=ServerApi('1'))



# Configuración de la interfaz gráfica del servidor
server_window = tk.Tk()
server_window.title("Music Sharing Server")

texto = tk.Label(server_window,text="Clientes conectados")
texto.pack()
log_text = scrolledtext.ScrolledText(server_window, wrap=tk.WORD, width=40, height=10)
log_text.pack(padx=10, pady=10)


texto2 = tk.Label(server_window,text="Solicitudes")
texto2.pack(padx=10, pady=10)
mensajes = scrolledtext.ScrolledText(server_window, wrap=tk.WORD, width=40, height=10)
mensajes.pack(padx=10, pady=10)

start_button = tk.Button(server_window, text="Iniciar Servidor", command=lambda: threading.Thread(target=start_server).start())
start_button.pack(pady=10)

#Conexion a la base de datos no relacional
try:
    cliente.admin.command('ping')
    log_text.insert(tk.END,f'Conexion a base de datos exitosa\n')
    db = cliente["mydb"]
    music_collection = db["canciones"]
except Exception as e:
        log_text.insert(tk.END,f'Error: {e}\n')


clientes = {}


# Función para manejar la conexión de un cliente
def manejar_cliente(client_socket):

    uuser_address = None
    user_name = None

    try:
        with lock:
            connected_clients.append(client_socket)

        # Se detecta que el usuario ingrese y se obtiene la dirección del dispositivo conectado
        user_address = client_socket.getpeername()

        # Solicitar el nombre de usuario al cliente
        user_name = client_socket.recv(1024).decode('utf-8')
        clientes[client_socket] = user_name

        log_text.insert(tk.END, f'Usuario {user_name} conectado desde {user_address}\n')

        while True:
            #Recive datos del cliente del tipo 1024 bits y los tranforma en cadena de carateres
            request = client_socket.recv(1024).decode('latin-1')

            
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
                mensajes.insert(tk.END,f'Usuario {clientes[client_socket]} agregro musica')
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

            # En la función manejar_cliente, modifica la sección de reproducir_cancion
            if request.startswith('reproducir_cancion'):
                print("reproducir")
                _, song = request.split(':', 1)
                print("Siguientes")
                print(song)
                enviar_cancion(client_socket, song)

            if request.startswith('borrar_cancion'):
                _, song_name = request.split(':', 1)
                # reproducir_cancion(song_name)
                print(song_name)
                borrar_cancion(client_socket,song_name)
                
    except ConnectionResetError:
        pass  # Manejar la desconexión del cliente

    finally:
        with lock:
            connected_clients.remove(client_socket)  # Eliminar cliente de la lista
            if user_address:
                log_text.insert(tk.END, f'Usuario {clientes[client_socket]} desconectado desde {user_address}\n')
            client_socket.close()

def clean_filename(filename):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    cleaned_filename = ''.join(c if c in valid_chars else '_' for c in filename)
    return cleaned_filename

def enviar_lista(client_socket):
    
    songs = [song["Nom_Music"] for song in music_collection.find()]
    client_socket.send(str(songs).encode('utf-8'))

#Guarda los clientes conectados
connected_clients = []

#Inicializa el seervidor y la conexion por el socket y el canal de escucha
def start_server():
    global server_socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    log_text.insert(tk.END, f'Servidor escuchando en {SERVER_HOST}:{SERVER_PORT}\n')

    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=manejar_cliente, args=(client_socket,)).start()

#Envia la cancion al usuario solicitado para poder reproducirla
# ...

def enviar_cancion(client_socket, song_name):
    music = song_name
    ruta = ''
    for song in music_collection.find():
        if song["Nom_Music"] == song_name:
            ruta = song["Ruta_Music"]

    if ruta:
        with open(ruta, 'rb') as file:
            # Enviar el nombre de la canción al cliente
            client_socket.send(music.encode('utf-8'))

            # Enviar el tamaño del archivo al cliente
            tam = str(os.path.getsize(ruta))
            print(tam)
            client_socket.send(tam.encode('utf-8'))

            send_byte = 0

            while True:
                chunk = file.read(1024)
                if not chunk:
                    break
                client_socket.send(chunk)
                send_byte += len(chunk)
                if send_byte >= int(tam):
                    break

            # Esperar confirmación del cliente antes de enviar "Ready"
            confirmation = client_socket.recv(1024).decode('utf-8')

            if confirmation == "Ready":
                client_socket.send("Ready".encode())
                print("Terminó el envío")

                
def borrar_cancion(client_socket, song_name):
    # Eliminar archivo del directorio
    file_path = os.path.join(MUSIC_DIRECTORY, song_name)
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Archivo {song_name} eliminado del directorio")

    # Eliminar registro de la base de datos
    condicion = {"Nom_Music": song_name}
    result = music_collection.delete_one(condicion)
    if result.deleted_count > 0:
        print(f"Registro de {song_name} eliminado de la base de datos")
    else:
        print(f"No se encontró el registro de {song_name} en la base de datos")


def on_closing():
    if messagebox.askokcancel("Cerrar servidor", "¿Estás seguro de que quieres cerrar el servidor?"):
        # Cerrar todos los sockets y finalizar el programa
        with lock:
            for client_socket in connected_clients:
                client_socket.close()
        server_socket.close()
        server_window.destroy()

# Configuración del evento de cierre de la ventana principal
server_window.protocol("WM_DELETE_WINDOW", on_closing)

# ...

# Bucle principal de tkinter
server_window.mainloop()