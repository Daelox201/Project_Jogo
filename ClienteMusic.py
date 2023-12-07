import queue
import socket
import threading
from tkinter import ttk
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter.simpledialog import askstring  # Para la barra de progreso
from customtkinter import CTk
from customtkinter import *
import pygame

SERVER_HOST = '192.168.137.1'
SERVER_PORT = 5555

CLIENT_MUSIC_DIRECTORY = 'cliente_musica'

# Iniciar la conexión al servidor
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_HOST, SERVER_PORT))

class ReproductorMusica:
    def __init__(self, ventana):

        self.usuario = askstring("Nombre de Usuario", "Ingrese su nombre de usuario:")
        if self.usuario:
            # Envía el nombre de usuario al servidor
            client_socket.send(self.usuario.encode('utf-8'))
        
        self.playing_thread = None  # Para almacenar el hilo de reproducción actual
        self.paused = False
        self.play_event = threading.Event()  # Evento para controlar la reproducción
        
        style = ttk.Style()

    # Estilo para el encabezado
        style.configure("Treeview.Heading", font=('Arial', 18), background='#BDB2C7', foreground='black')

        # Estilo para las celdas
        style.configure("Treeview", font=('Helvetica', 16), background='lightgray', foreground='black', padding=(10, 5))

        # Estilo de selección
        style.map("Treeview", background=[('selected', 'blue')], foreground=[('selected', 'white')])

        # Estilo de enfoque
        style.configure("Treeview", highlightbackground='red', highlightcolor='green', takefocus=True)

        self.ventana = ventana
        
        self.cola_reproduccion = queue.Queue()
        self.cola_borrar = queue.Queue()
        self.cola_actual = queue.Queue()
        
        #Definimos la columnas y filas que tendra la ventana dandoles dimensiones iguales
        i = 0 
        for i in range(9):
            self.ventana.grid_columnconfigure(i, weight=1)
        i = 0
        for i in range(6):
            self.ventana.grid_rowconfigure(i, weight=1)

        
        #Lista de caciones
        self.lista_musica = ttk.Treeview(ventana, columns=("Canciones",), show="headings", selectmode="extended")
        self.lista_musica.bind("<<TreeviewSelect>>", self.actualizar_seleccion)
        self.lista_musica.heading("Canciones", text="Canciones")

        # Estilo para las filas normales
        self.lista_musica.tag_configure("normal", background="#BDB2C7",font=('Arial', 18))

        self.mensajes = CTkLabel(ventana,text="")
        
        # Cargar imagen para botones
        self.img_play = PhotoImage(file="iconos/play.png")
        self.img_pause= PhotoImage(file="iconos/pause.png")


        # Botones
        self.boton_get_list = CTkButton(ventana, text="Get List", command=self.obtener_lista, width=150, height=30,corner_radius=90)
        self.boton_add_song = CTkButton(ventana, text="Add Song", command=self.subir_cancion, width=150, height=30,corner_radius=90)

        self.boton_delete_song = CTkButton(ventana, text="Delete Song", command=self.borrar_cancion, width=150, height=30,corner_radius=90)
        self.boton_play = CTkButton(ventana, text="",image=self.img_play, command=self.reproducir_cancion, corner_radius=1000, height=60, width=60)
        self.boton_pause = CTkButton(ventana, text="",image=self.img_pause, command=self.pausar_cancion, corner_radius=1000, height=60, width=60)

        # self.boton_prev = CTkButton(ventana, text="⏮ Prev", command="")
        # self.boton_next = CTkButton(ventana, text="⏭ Next", command=self.siguiente_cancion)

        

        self.barra_progreso_reproduccion = CTkProgressBar(ventana, orientation="horizontal", mode="determinate")
        

        # Posicionamiento de elementos en las columnas

        
        self.mensajes.grid(row=4,column=3)
      
        self.lista_musica.grid(row=0,column=0,columnspan=8,rowspan=4, sticky="nsew",padx=10,pady=10)

        self.boton_get_list.grid(row=0, column=8,rowspan=1,sticky="ew", padx=5, pady=5,)
        self.boton_add_song.grid(row=1, column=8,rowspan=1, sticky="ew", padx=5, pady=2)
        self.boton_delete_song.grid(row=2, column=8, rowspan=1,sticky="ew", padx=5, pady=2)

        
        # self.boton_prev.grid(row=5, column=0, padx=0)
        self.boton_play.grid(row=4, column=3,columnspan=2 ,padx=5)
        self.boton_pause.grid(row=4, column=5,columnspan=2, padx=5)
        # self.boton_next.grid(row=5, column=6, padx=0)

         # Atributos adicionales
        self.playing_thread = None  # Para almacenar el hilo de reproducción actual
        self.paused = False

        self.centrar_ventana()

    def actualizar_seleccion(self, event):
        item = self.lista_musica.selection()[0] if self.lista_musica.selection() else None

        if item:
            cancion = self.lista_musica.item(item, "values")[0]
            if cancion not in self.cola_reproduccion.queue:
                self.cola_reproduccion.put(cancion)
                self.lista_musica.tag_configure(cancion, background='lightgreen')
                self.lista_musica.item(item, tags=(cancion,))
    # Función para subir una canción al servidor
    def subir_cancion(self):
        file_path = filedialog.askopenfilename(title="Seleccionar Archivo", filetypes=[("Archivos de música", "*.mp3")])
        if file_path:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            client_socket.send(f'check_existence:{file_name}'.encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')

            if response == "EXISTS":
                messagebox.showinfo("Error", f"El archivo {file_name} ya existe en el servidor")
                self.obtener_lista()
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
                
        self.obtener_lista
                
    # Función para obtener la lista de canciones desde el servidor
    def obtener_lista(self):
        self.lista_musica.delete(*self.lista_musica.get_children())
        client_socket.send('obtener_lista'.encode('utf-8'))
        songs = eval(client_socket.recv(1024).decode('utf-8'))
        for song in songs:
            self.lista_musica.insert("", "end", values=(song,))
  

    def pausar_cancion(self):
        if not self.paused:
            pygame.mixer.music.pause()
            self.paused = True
            

    def reanudar_cancion(self):
        if self.paused:
            pygame.mixer.music.unpause()
            self.paused = False
            # Cambiar el ícono del botón a "pause" cuando la música se reanuda
            self.boton_play.configure(image=self.img_play)


    def siguiente_cancion(self):
        siguiente_cancion = self.cola_reproduccion.get()
        print(siguiente_cancion)
        self.cola_actual.put(siguiente_cancion)

        if not self.cola_reproduccion.empty():
            # Obtener la siguiente canción de la cola
            
            

            # # Configurar el estilo de la fila seleccionada
            # self.lista_musica.tag_configure(siguiente_cancion, background='lightgreen')
            # item = next(item for item in self.lista_musica.get_children() if self.lista_musica.item(item, "values")[0] == siguiente_cancion)
            # self.lista_musica.item(item, tags=(siguiente_cancion,))

            # Enviar la cola actualizada al servidor para reproducir en orden
            client_socket.send(f'reproducir_cancion:{self.cola_reproduccion.get()}'.encode('utf-8'))
            self.descargar_y_reproducir()
        else:
            messagebox.showinfo("Error", "No hay más canciones en la cola de reproducción")
    # Funcion reanudar cancion
  


    # Funcion principal para reproducir la canciones iniciando la descarga del archivo si es necesario 
    def reproducir_cancion(self):
        if self.paused:
            self.reanudar_cancion()
        else:
            selecciones = self.lista_musica.selection()

            if not selecciones:
                messagebox.showinfo("Error", "Selecciona al menos una canción.")
                return
            if self.cola_reproduccion.empty():
                messagebox.showinfo("Error", "No hay mas elementos en la cola de reproduccion")
            else:
                # Enviar la cola al servidor para reproducir en el orden exacto
                client_socket.send(f'reproducir_cancion:{self.cola_reproduccion.get()}'.encode('utf-8'))
                self.descargar_y_reproducir()
            # Usar una cola para mantener el orden FIFO de las canciones seleccionadas
            for seleccion in selecciones:
                cancion = self.lista_musica.item(seleccion, "values")[0]
                self.cola_reproduccion.put(cancion)

                # Configurar el estilo de la fila seleccionada
                self.lista_musica.tag_configure(cancion, background='lightgreen')
                self.lista_musica.item(seleccion, tags=(cancion,))
                
            # Limpiar la selección actual en el Treeview
            for seleccion in selecciones:
                self.lista_musica.tag_configure(self.lista_musica.item(seleccion, "values")[0], background='#BDB2C7')
                self.lista_musica.item(seleccion, tags=("normal",))

            

            # Limpiar la selección actual en el Treeview
            for seleccion in selecciones:
                self.lista_musica.tag_configure(self.lista_musica.item(seleccion, "values")[0], background='#BDB2C7')
                self.lista_musica.item(seleccion, tags=("normal",))

    
    def borrar_cancion(self):
        selecciones = self.lista_musica.selection()

        if not selecciones:
            messagebox.showinfo("Error", "Selecciona al menos una canción.")
            return

        for seleccion in selecciones:
            cancion = self.lista_musica.item(seleccion, "values")[0]
            self.cola_borrar.put(cancion)
            name = self.cola_borrar.get()
            if messagebox.askokcancel("Borrar cancion", f"¿Estás seguro de que quieres borrar la cancion {name}del servidor?"):
                client_socket.send(f'borrar_cancion:{name}'.encode('utf-8'))
        self.obtener_lista()

    # ...

    def recibir_archivo(self, file_size, destination_path):
        print(file_size)
        if os.path.exists(destination_path):
            print(f"El archivo {destination_path} ya existe. No es necesario recibirlo de nuevo.")
            return
        received_bytes = 0
        with open(destination_path, 'wb') as file:
            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break  # Si no se recibe ningún byte, salir del bucle
                received_bytes += len(chunk)
                file.write(chunk)

                if received_bytes >= file_size:
                    break  # Si se han recibido todos los bytes, salir del bucle

        print(f"Bytes recibidos: {received_bytes}, Tamaño total esperado: {file_size}")

        # Verificar si se han recibido todos los datos
        if received_bytes != file_size:
            print("¡Advertencia! No se recibieron todos los datos del archivo.")
        else:
            print("Archivo recibido y guardado correctamente.")

        # Enviar confirmación al servidor
        client_socket.send("Confirmed".encode())
        print("Terminó de recibir el archivo")

    
    def descargar_y_reproducir(self):
        song = client_socket.recv(1024).decode('utf-8')
        # Recibir el tamaño del archivo del servidor
        file_size_bytes = client_socket.recv(1024)
        file_size = int(file_size_bytes.decode('utf-8'))
        play_path = os.path.join(CLIENT_MUSIC_DIRECTORY, song)

        os.makedirs(os.path.dirname(play_path), exist_ok=True)
        # print(play_path)

        if play_path:
            self.recibir_archivo( file_size, play_path)

        reproducir_hilo = threading.Thread(target=self.reproducir_cancion_en_hilo, args=(play_path,))
        reproducir_hilo.daemon = True
        reproducir_hilo.start()

    


    # Reproducir cacncion por medio de un hilo para no parar los procesos de
    def reproducir_cancion_en_hilo(self, play_path):
        pygame.mixer.init()
        try:
            pygame.mixer.music.load(play_path)
            pygame.mixer.music.play()

            clock = pygame.time.Clock()

            while pygame.mixer.music.get_busy() or not self.play_event.is_set():
                self.ventana.update_idletasks()
                clock.tick(10)  # Ajusta el reloj pygame
        except pygame.error as e:
            messagebox.showerror("Error", f"Error al reproducir la canción: {e}")
        pygame.mixer.music.stop()

    
        
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
    ventana_principal.configure(bg='black')
    ventana_principal.title("Reproductor de Música")
    ventana_principal.geometry("900x400")
    ventana_principal.resizable(False, False)
    reproductor = ReproductorMusica(ventana_principal)
    reproductor.centrar_ventana()
    ventana_principal.mainloop()