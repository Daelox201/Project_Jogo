import socket
import tkinter as tk
from tkinter import *  # Para la barra de progreso
from customtkinter import CTk
from customtkinter import *

SERVER_HOST = '192.168.137.127'
SERVER_PORT = 5555


# Iniciar la conexión al servidor
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_HOST, SERVER_PORT))

class ReproductorMusica:
    def __init__(self, ventana):
        
        self.ventana = ventana
        self.ventana.title("Reproductor de Música")

        self.ventana.geometry("900x400")
        self.ventana.resizable(False, False)
        i = 0 
        for i in range(9):
            self.ventana.grid_columnconfigure(i, weight=1)
        i = 0
        for i in range(6):
            self.ventana.grid_rowconfigure(i, weight=1)

        

        self.lista_canciones = tk.Listbox(ventana, selectmode=tk.SINGLE)
        self.lista_canciones.grid(row=0, column=0, rowspan=4, columnspan=8, sticky="nsew", padx=10, pady=10)



        # Botones
        self.boton_get_list = CTkButton(ventana, text="Get List", command=self.obtener_lista, width=150, height=30,corner_radius=90)
        self.boton_add_song = CTkButton(ventana, text="Add Song", command=self.subir_cancion, width=150, height=30,corner_radius=90)
        self.boton_move_song = CTkButton(ventana, text="Move Song", command="", width=150, height=30,corner_radius=90)
        self.boton_delete_song = CTkButton(ventana, text="Delete Song", command="", width=150, height=30,corner_radius=90)
        img = PhotoImage(file="iconos/play.png")

        self.boton_play = CTkButton(ventana,text='',image=img, command=self.reproducir_cancion,corner_radius=1000,height=60,width=60,)
        self.boton_prev = CTkButton(ventana, text="⏮ Prev", command="")
        self.boton_next = CTkButton(ventana, text="⏭ Next", command="")

        # Barra de progreso
        self.barra_progreso = CTkProgressBar(ventana, orientation="horizontal")
        self.barra_progreso.grid(row=4,column=0, sticky="ew",padx=5,columnspan=8)

        # Posicionamiento de elementos
        self.boton_get_list.grid(row=0, column=8, sticky="ew", padx=5, pady=5)
        self.boton_add_song.grid(row=1, column=8, sticky="ew", padx=5, pady=2)
        self.boton_move_song.grid(row=2, column=8, sticky="ew", padx=5, pady=2)
        self.boton_delete_song.grid(row=3, column=8, sticky="ew", padx=5, pady=2)

        
        self.boton_prev.grid(row=5, column=0, padx=0, columnspan=3)
        self.boton_play.grid(row=5, column=3, padx=0,  columnspan=3)
        self.boton_next.grid(row=5, column=6, padx=0,  columnspan=3)

        


        self.centrar_ventana()

    # Función para subir una canción al servidor
    def subir_cancion():
        file_path = filedialog.askopenfilename(title="Seleccionar Archivo", filetypes=[("Archivos de música", "*.mp3")])
        if file_path:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            client_socket.send(f'check_existence:{file_name}'.encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')

            if response == "EXISTS":
                print(f"Archivo{file_name} ya existe")
            else:
                with open(file_path, 'rb') as file:
                    # Enviar el nombre del archivo al servidor
                    client_socket.send(f'subir_cancion:{file_name}:{file_size}'.encode('utf-8'))
                    # Enviar los datos del archivo al servidor
                    sent_bytes = 0

                    while True:
                        chunk = file.read()
                        client_socket.send(chunk)
                        sent_bytes += len(chunk)
                        if sent_bytes >= file_size:
                            break
                # for chunk in iter(lambda: file.read(1024), b''):
                #     client_socket.send(chunk)
                # client_socket.send(b'DONE')  # Indicar al servidor que se completó la transferencia

    # Función para obtener la lista de canciones desde el servidor
    def obtener_lista(self):
        client_socket.send('obtener_lista'.encode('utf-8'))
        songs = eval(client_socket.recv(1024).decode('utf-8'))
        self.lista_canciones.delete(0, tk.END)
        for song in songs:
            self.lista_canciones.insert(tk.END, song)

    # Función para reproducir una canción desde el servidor
    def reproducir_cancion(self):
        selected_song = self.lista_canciones.get(tk.ACTIVE)
        if selected_song:
            # Enviar solicitud para reproducir la canción al servidor
            client_socket.send(f'reproducir_cancion:{selected_song}'.encode('utf-8'))

    def centrar_ventana(self):
        # Actualizar la ventana para obtener sus dimensiones reales
        self.ventana.update_idletasks()

        # Obtener el ancho y alto de la pantalla
        ancho_pantalla = self.ventana.winfo_screenwidth()
        alto_pantalla = self.ventana.winfo_screenheight()

        # Obtener el ancho y alto de la ventana
        ancho_ventana = self.ventana.winfo_reqwidth()
        alto_ventana = self.ventana.winfo_reqheight()

        # Calcular las coordenadas x e y para centrar la ventana
        x = (ancho_pantalla - ancho_ventana) // 2
        y = (alto_pantalla - alto_ventana) // 2

        # Establecer la geometría de la ventana para centrarla
        self.ventana.geometry("+{}+{}".format(x, y))

if __name__ == "__main__":
    ventana_principal = CTk()
    reproductor = ReproductorMusica(ventana_principal)
    reproductor.centrar_ventana()
    ventana_principal.mainloop()