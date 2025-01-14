
"""
PROGRAMA FINAL
"""
import random
import time
import tkinter
from tkinter import *
from datetime import datetime
from matplotlib import style
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar2TkAgg
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from PIL import Image
from tkinter import filedialog
import os, sys
import threading
from tkinter import messagebox as MessageBox
import numpy as np
print("here is the mistake")
from fpdf import FPDF
import customtkinter as ctk
import xlsxwriter
import webbrowser
import socket
from scipy import interpolate

from os import urandom
from getpass import getpass
import base64

print("holii")

host = "192.168.0.10"
print(host)
port = 65432
BUFFER_SIZE = 16
MESSAGE = 'Hola, mundo!' # Datos que queremos enviar

port = 65432
BUFFER_SIZE = 16
MESSAGE = 'Hola, mundo!' # Datos que queremos enviar
cont = 0

extension = ""

ctk.set_appearance_mode("light")  # Modes: system (default), light, dark

def get_resource_path(relative_path):
    # Verifica si está empaquetado en un ejecutable
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        # Ruta base del script cuando se ejecuta normalmente
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

tema = get_resource_path("citdi_theme.json")
imagen = get_resource_path("CITDI_LOGO_SINFONDO.png")

try:
    ctk.set_default_color_theme(tema)
except:
    print("estás en local")
    ctk.set_default_color_theme("./citdi_theme.json")
    print("listo")
# Funcionalidades

ruta_data_inicial = ""
cuerpo_ruta = ""
archivo = ""
numero_grafica_actual = 1
archivos_existentes = []
frecuencia_muestreo = [50]
orden_sensores = []
pile_area = 10
EM_valor_original = 10
ET_valor_original = 453
ruta_guardado = ""
ruta_guardado_pdf = ""
tipo_review = ""
estado_continuidad = ""
zooms_graficas = []
zoom_x_general_arriba = ""
zoom_y_general_arriba = ""
zoom_x_general_abajo = ""
zoom_y_general_abajo = ""
magnitud_antigua_arriba = "aceleracion"
magnitud_antigua_abajo = "deformacion"
unidad_original = ""
unidad_antigua = ""
numero_grafica_antiguo_arriba = 1
numero_grafica_antiguo_abajo = 1
valor_actual_sistema_metrico = "SI"


F1 = []
F2 = []
F = []
V1 = []
V2 = []
V = []
E = []
D1 = []
D2 = []
D = []
V_Transformado = []
V_Transformado_valor_real = []


contador_grafica_arriba = 1
contador_grafica_abajo = 1

# NUEVAS FÓRMULAS OPTIMIZADAS

def def2fuerza(deformacion, modulo_elasticidad = 206842.6833, area = 7.805946):
    
    factor = modulo_elasticidad*area
    fuerza = deformacion*factor/10000000   #Fuerza en kN

    return np.round(fuerza,10)

def correccion_triangular(data_array, first_dv = 498, second_dv = 10000):

    # Velocidad primer intervalo
    V_1 = data_array[:first_dv]
    # Velocidad segundo intervalo
    V_2 = data_array[first_dv:]
    # Velocidad tercer intervalo
    V_3 = []
    valor_maximo = data_array[second_dv]

    for i,data in enumerate(V_2):
        valor = data - i*valor_maximo/(second_dv - first_dv)
        V_3.append(valor)

    # Concatenating again
    velocidad_corregida = np.concatenate((V_1, V_3))

    return np.round(velocidad_corregida,6)

def correccion_inicial(deformacion,freq=50,before_time=10):
    deformacion = np.array(deformacion)
    idx_impact = int((before_time)*freq)
    deformacion_partida = np.array(deformacion)[:idx_impact]

    def_corregida = deformacion - np.mean(deformacion_partida)

    return def_corregida

def velocidad_nuevo_metodo(acel, freq=50):
    # Convertir aceleraciones a unidades SI y calcular h
    acel_si = [a * 9.80665 for a in acel]
    h = 1 / (freq * 1000)
    print(h)
    # Calcular velocidad
    velocidad = [0]
    for i in range(1, len(acel_si)):
        velocidad.append(acel_si[i] * h + velocidad[i - 1])
    
    # Calcular índices para la corrección triangular
    idx_impact = int(0.01 * freq * 1000) - 1
    last_impact = len(acel) - 2
    
    velocidad_corregida = correccion_triangular(velocidad, idx_impact, last_impact)
    print("velocidad maxima:", max(acel))
    return np.array(velocidad_corregida)

def desplazamiento_tesis(vel_tesis, freq = 50):
    
    dezpla_tesis = [0]

    h = 1/(freq*1000)

    for data_velt in vel_tesis[1:]:
        dezpla_tesis.append(data_velt*h)

    desplaza_1 = [0]

    for i,data_desp in enumerate(dezpla_tesis):
        if i > 0:
            desplaza_1.append(data_desp + desplaza_1[i-1])

    des_redondeado = []

    for des_aun in desplaza_1:
        des_redondeado.append(round(des_aun,6))

    return np.array(des_redondeado)

def limpieza_cuentas(cuentas):
    cuentas_limpias = []
    for index,data in enumerate(cuentas):
        if data>30000 or data<-30000:
            try:
                new_data = (cuentas[index-1] + cuentas[index+1])/2
            except:
                new_data = data
        else:
            new_data = data
        cuentas_limpias.append(new_data)
    
    return np.array(cuentas_limpias)

import numpy as np
from scipy.signal import detrend, butter, filtfilt

def cuentas2magnitud(cuentas, tipo, freq=50):
    nuevas_cuentas = limpieza_cuentas(cuentas)

    ganancia = [2, 2, 16, 16, 2, 2]
    primeros_400 = nuevas_cuentas.copy()[:400]
    
    # Calcula el promedio
    promedio = sum(primeros_400) / len(primeros_400)
    offset = promedio

    vref = 2.863
    resolucion = 16

    voltaje_array = (np.array(nuevas_cuentas) - offset) * vref / (2**(resolucion-1)) / ganancia[tipo-1] * 1000000
    
    voltaje_array = detrend(voltaje_array, type='constant')
    
    # Filtro paso bajo a 5 kHz
    nyquist = 0.5 * freq * 1000  # Frecuencia de Nyquist
    low = 5000 / nyquist
    b, a = butter(4, low, btype='low')  # Filtro Butterworth de 4 polos
    data = filtfilt(b, a, voltaje_array)
    
    # Corrección inicial (asumiendo que existe una función correccion_inicial)
    data_x = correccion_inicial(data)

    if tipo == 1 or tipo == 2:
        idx_impact = int(10 * freq)

        # Aceleración antes del impacto
        A_ai = detrend(data[:idx_impact], type='constant')
        
        # Aceleración después del impacto
        tr_partido = detrend(data[idx_impact:], type='constant')

        # Concatenar
        D_linea_cero = np.concatenate((A_ai, tr_partido))
        data_x = D_linea_cero

    # Calibración
    calibracion = [65.3125, 58.51, 6.46, 6.35]
    
    return data_x / calibracion[tipo-1]

def energia_original(F, V, freq = 50):

    h = 1 / (freq * 1000)
    energia_resul = [0]
    print("ancho de linea",h)
    for i in range(1, len(F)):
        energia_resul.append(round(F[i] * V[i] * h * 1000,6) + energia_resul[i-1])
    
    return energia_resul

matriz_data_archivos = []
orden = ""
Switch_sistema_metrico = ""

def browseFiles():
    global tipo_review, orden, unidad_antigua, valor_actual_sistema_metrico, unidad_original
    global ruta_data_inicial, contador_grafica_abajo, contador_grafica_arriba, matriz_data_archivos, orden_sensores
    global Switch_sistema_metrico
    global zoom_x_general_arriba, zoom_y_general_arriba, zoom_x_general_abajo, zoom_y_general_abajo
    global estado_continuidad
    global key


    
    estado_continuidad = ""
    zoom_x_general_arriba, zoom_y_general_arriba, zoom_x_general_abajo, zoom_y_general_abajo = "", "", "", ""
    print("esta es la ruta inicial: ", ruta_data_inicial)
    matriz_data_archivos = []
    ruta_data_inicial = filedialog.askopenfilename(initialdir = "/", title = "Select a File", filetypes = [("CT files", "*.ct*")])   
    tipo_review = "solo_review"
    try:
        with open(ruta_data_inicial, "r") as file:
            lineas = file.readlines()
            matriz_data_archivos.append(str(lineas[0]).replace("\n", ""))
            vector = []
            estado = "noleyendo"
            j = 0
            for i in range(1,len(lineas)):
                linea = str(lineas[i]).replace("\n", "")
                if linea == 'INICIO_ARCHIVO':
                    estado = "leyendo"
                elif linea == 'FIN_ARCHIVO':
                    estado = "finalizado"
                if estado == "leyendo":
                    if j == 1:
                        n_archivo = linea[8:]
                    if j == 2:
                        orden_sensores.append(linea)
                    if j > 2:
                        vector.append(linea)
                    j += 1    
                if estado == "finalizado":
                    if vector != []:
                        matriz_data_archivos.append(vector)
                    vector = []
                    j = 0
    except Exception as e:
        print(e, 1)
        print("error2")   
    orden = str(orden_sensores[-1]).replace(" ","").split("|")
    try:
        unidad_original = orden[8]
        unidad_antigua = unidad_original
        valor_actual_sistema_metrico = unidad_original
        Switch_sistema_metrico.set(unidad_original)
        
    except Exception as e:
        print(e, 2)
        unidad_original = "SI"
        unidad_antigua = "SI"
        valor_actual_sistema_metrico = "SI" 
        Switch_sistema_metrico.set("SI")     
    contador_grafica_arriba = 1
    contador_grafica_abajo = 1

# Posiciones

ultima_grafica_seleccionada = "arriba"
ultima_magnitud_arriba = "aceleracion"
ultima_magnitud_abajo = "deformacion"

def Obtencion_data_serial(num):
    global extension, unidad_antigua, orden
    global frecuencia_muestreo, matriz_data_archivos, pile_area, EM_valor_original, ET_valor_original, segundo_final, segundo_inicial
    global orden_sensores, ruta_data_inicial
    global bpm_list
    global S1, S2, A3, A4
    segundos = []
    S1, S2, A3, A4, SIN1, SIN2, SIN3, SIN4, NULL = [], [], [], [], [], [], [], [], []

    dic_orden_sensores = {"1":A3, "2":A4, "3":S1, "4":S2, "5":S1, "6":S2, "0":NULL}
    dic_orden_sensores2 = {"1":SIN1, "2":SIN2, "3":SIN3, "4":SIN4, "5":SIN3, "6":SIN4, "0": NULL}

    #print("el orden de los sensores es ", orden_sensores, "el orden es ", orden)
    orden = orden_sensores[-1].split('|')
    bpm_list = []
    try:
        if len(orden[4])>1:
            frecuencia_muestreo.append(int(orden[4]))
    except Exception as e:
        print(e, 3)
        print(orden)
        frecuencia_muestreo.append(50)
    try:
        pile_area = orden[5]
    except Exception as e:
        print(e, 4)
        pile_area = "7.80595"
    try:
        EM_valor_original = orden[6]
    except Exception as e:
        print(e, 5)
        EM_valor_original = "206843"
    try:
        ET_valor_original = orden[7]
    except Exception as e:
        print(e, 6)
        ET_valor_original = 473.269
    try:
        ET_valor_original = orden[7]
    except Exception as e:
        print(e, 6)
        ET_valor_original = 473.269
    contadoresss = 0
    for orden_bpm in orden_sensores:
        
        try:
            
            orden_prueba = orden_bpm.split('|')
            print("Es orden: ", orden_bpm)
            bpm_list.append(float(orden_prueba[9]))
        except Exception as e:
            bpm_list.append(round(1.94+contadoresss*(random.random()*3+12),2))
            print(e, 6)
        contadoresss=1

    #print("el orden de los sensores es ", orden_sensores, "el orden es ", orden)
    extension = ruta_data_inicial.split("/")[-1].split(".")[-1]
    if extension == "ctn":
        data = matriz_data_archivos[num]
        
        for linea in data:
            linea = linea.split("|")
            segundos.append(float(linea[0])/10)
            for j in range(4):
                dic_orden_sensores2[orden[j]].append(round(float(linea[j+1]),2))
        segundo_inicial = segundos[0]
        segundo_final = segundos[-1]

        for i in range(4):

            if ((int(orden[i]) == 1)) or (int(orden[i]) == 2):
                for datos in dic_orden_sensores2[orden[i]]:
                    dic_orden_sensores[orden[i]].append(datos)
            elif (int(orden[i])!=0):
                for datos in dic_orden_sensores2[orden[i]]:               
                    dic_orden_sensores[orden[i]].append(datos)
        
        frecuencia = int(frecuencia_muestreo[-1])

        print("Longitud: ",len(segundos))
        intervalo_tiempo = 1/(frecuencia)
        longit = len(segundos)
        init_val = segundos[0]*100
        segundos_2 = [init_val + x*intervalo_tiempo for x in range(0,len(segundos))]
        #segundos_2 = np.arange(segundos[0]*1000, segundos[-1]*1000+intervalo_tiempo/1000,intervalo_tiempo)
        print("Longitud: ",len(segundos_2))

    else:
        for index,linea in enumerate(matriz_data_archivos[num]):
            linea = linea.split("|")
            if index > 0 and index < len(matriz_data_archivos[num])-1:
                segundos.append(float(linea[0])/1000000)
                for i in range(4):
                    dic_orden_sensores2[orden[i]].append(float(linea[i+1]))
            else:
                pass
        segundo_inicial = segundos[0]
        segundo_final = segundos[-1]

        frecuencia = int(frecuencia_muestreo[-1])
        for i in range(4):
            lugar = int(orden[i])
            if ((lugar== 1)) or (lugar == 2):
                #for datos in dic_orden_sensores2[orden[i]]:
                for datos in cuentas2magnitud(dic_orden_sensores2[orden[i]], lugar, frecuencia):
                    dic_orden_sensores[orden[i]].append(datos)
            
            elif (lugar!=0):
                #for datos in dic_orden_sensores2[orden[i]]:
                for datos in cuentas2magnitud(dic_orden_sensores2[orden[i]], lugar, frecuencia):
                    dic_orden_sensores[orden[i]].append(datos)
        
        print("Longitud: ",len(segundos))
        intervalo_tiempo = 1/(frecuencia)
        longit = len(segundos)
        init_val = segundos[0]*100
        segundos_2 = [init_val + x*intervalo_tiempo for x in range(0,len(segundos))]
        #segundos_2 = np.arange(segundos[0]*1000, segundos[-1]*1000+intervalo_tiempo/1000,intervalo_tiempo)
        print("Longitud: ",len(segundos_2))
    #print("Estoy aquí1")

    return segundos_2, S1, S2, A3, A4


# Interfaz

def raise_frame(frame):
    Menup.grid_forget()
    Review.grid_forget()
    Collect_Wire.grid_forget()
    frame.grid(row=0, column=0, sticky='nsew')
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)


root = Tk()
ruta_logo = get_resource_path("logo_kp.ico")
root.title("Kallpa Processor")  # Cambia "Nombre de la Ventana" por el título que desees

root.iconbitmap(ruta_logo)  # Asegúrate de que la ruta al ícono sea correcta
root.state("zoomed")
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

menubar = Menu(root)
root.config(menu=menubar)
filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="Open", command=lambda:[browseFiles(), Creacion_Grafica("arriba","aceleracion", 1, "original", "NO", "NO"), Creacion_Grafica("abajo", "deformacion", 1, "original", "NO", "NO"), eliminar_columna_muestreo(), raise_frame(Review)])
filemenu.add_command(label="Exit", command=root.quit)
editmenu = Menu(menubar, tearoff=0)
editmenu.add_command(label="Delete Impact", command=lambda: eliminar_grafica())
editmenu.add_command(label="Go to First Impact", command=lambda: cambiar_grafica_exacto("primero"))
editmenu.add_command(label="Go to Last Impact", command=lambda: cambiar_grafica_exacto("ultimo"))
editmenu.add_command(label="Sync up", command=lambda: creador_sincronizacion())
editmenu.add_command(label="Export", command=lambda: Seleccionar_ruta_guardado_pdf())
helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="About", command=lambda:create_toplevel_about())
helpmenu.add_separator()
helpmenu.add_command(label="Manual", command=lambda:abrir_manual())
menubar.add_cascade(label="File", menu=filemenu)
menubar.add_cascade(label="Menu", menu=editmenu)
menubar.add_cascade(label="Help", menu=helpmenu)


Review = ctk.CTkFrame(root)
Menup = ctk.CTkFrame(root)
Collect_Wire = ctk.CTkFrame(root)
    
# FRAME INICIAL
container4a = ctk.CTkFrame(master= Menup, corner_radius = 20)

container4a.grid_rowconfigure(0, weight=1)
container4a.grid_rowconfigure(1, weight=1)
container4a.grid_columnconfigure(0, weight=1)
container4a.grid(row=0, column=0, sticky='nsew', padx=40, pady=40)

container4b = ctk.CTkFrame(container4a, corner_radius=20, fg_color=["#f1f1f0","#091d36"])
container4b.grid(row=0, column=0, sticky='nsew', padx=40, pady=(40,0))

container4b.grid_rowconfigure(0, weight=10)
container4b.grid_rowconfigure(1, weight=2)
container4b.grid_columnconfigure(0, weight=1)
container4b.grid_columnconfigure(1, weight=10)
container4b.grid_columnconfigure(2, weight=1)


container4c = ctk.CTkFrame(container4a, width=200,height=200,corner_radius=10, fg_color = ["#f1f1f0","#091d36"])
container4c.grid(row=1, column=0, sticky='nsew', padx=20, pady=(10,20))
container4c.grid_rowconfigure(0, weight=1)
# Botones
lista_botones = ["EXIT", "REVIEW", "JOIN FILES", "COLLECT WIRE", "MANUAL", "ABOUT"]

for i in range(len(lista_botones)):
    container4c.grid_columnconfigure(i, weight=1)

Entry_Profundidad_inicial = ''
Entry_Profundidad_final = ''

def limpiar_entrys():
    global Entry_Profundidad_inicial, Entry_Profundidad_final, tipo_review
    try:
        Entry_Profundidad_inicial.configure.delete(0, END)
        Entry_Profundidad_final.configure.delete(0, END)
    except Exception as e:
        print(e, 7)
    tipo_review = "collectwire"

def abrir_manual():
    ruta_pdf = os.environ["PROGRAMFILES"] + "\kallpa_app\MANUAL DE SOFTWARE.pdf"
    print(ruta_pdf)
    url = 'file://' + ruta_pdf
    webbrowser.open(url)

#Fuentes

fontTITULO = ctk.CTkFont(family='FRanklin Gothic Book',size=100, weight="bold")
fontBARRA = ('FRanklin Gothic Book',40)
#fontSUBcoll = ('FRanklin Gothic Book',26)
fontSUBcoll = ctk.CTkFont(family='FRanklin Gothic Book',size=30, weight="bold")
fontTEXTcoll = ctk.CTkFont(family='FRanklin Gothic Book',size=22)
fontBARRAleft = ('FRanklin Gothic Book',14)
family_barra_derecha = 'FRanklin Gothic Book'

fontABOUTtitulo = ctk.CTkFont(family='FRanklin Gothic Book',size=40, weight="bold")
fontABOUTtexto = ctk.CTkFont(family='FRanklin Gothic Book',size=35)

font_barra_derecha = ctk.CTkFont(family='FRanklin Gothic Book',size=35, weight="bold")
font_barra_cambio_magnitud = ctk.CTkFont(family='FRanklin Gothic Book',size=20)



#Button(container4, text=lista_botones[0], bg=azul_oscuro, font=fontBARRA, fg='#FFFFFF',command=lambda:root.destroy()).grid(row=4,column=0, sticky='nsew')
ancho_barra_abajo = 10
ctk.CTkButton(container4c, text=lista_botones[0], font=fontBARRA, command=lambda:root.destroy()).grid(row=0,column=0, sticky='nsew', padx=10, pady=10)
ctk.CTkButton(container4c, text=lista_botones[1], font=fontBARRA, command=lambda:[browseFiles(), Creacion_Grafica("arriba","aceleracion", 1, "original", "NO", "NO"), Creacion_Grafica("abajo", "deformacion", 1, "original", "NO", "NO"), eliminar_columna_muestreo(), raise_frame(Review)]).grid(row=0,column=1, sticky='nsew', pady=10, padx=(0,10))
ctk.CTkButton(container4c, text=lista_botones[2], font=fontBARRA, command=lambda:create_toplevel_preparar()).grid(row=0,column=2, sticky='nsew', pady=10, padx=(0,10))
ctk.CTkButton(container4c, text=lista_botones[3], font=fontBARRA, command=lambda:[raise_frame(Collect_Wire), limpiar_entrys()]).grid(row=0,column=3, sticky='nsew', pady=10, padx=(0,10))
ctk.CTkButton(container4c, text=lista_botones[4], font=fontBARRA, command=lambda:abrir_manual()).grid(row=0,column=4, sticky='nsew', pady=10, padx=(0,10))
ctk.CTkButton(container4c, text=lista_botones[5], font=fontBARRA, command=lambda:create_toplevel_about()).grid(row=0,column=5, sticky='nsew', pady=10, padx=(0,10))

# Mostrar Hora
def Obtener_hora_actual():
    return datetime.now().strftime("%H:%M:%S\n%d/%m/%y")

def refrescar_reloj():
    hora_actual.set(Obtener_hora_actual())
    container4b.after(300, refrescar_reloj)

hora_actual = StringVar(container4b, value=Obtener_hora_actual())

refrescar_reloj()

# AÑADIR PORTADA

try:
    nombre_archivo_portada = imagen
    imagen = PhotoImage(file=nombre_archivo_portada)
except:
    imagen = "./CITDI_LOGO_SINFONDO.png"
    nombre_archivo_portada = imagen
    imagen = PhotoImage(file=nombre_archivo_portada)

imagen = imagen.zoom(2, 2)
new_imagen = imagen.subsample(5, 5)

container_imagen = ctk.CTkLabel(container4b, image=new_imagen, text="")
container_imagen.grid(row=0,column=1, columnspan=2, padx=(40), pady=40)

ctk.CTkLabel(container4b, font=fontTITULO, text="KALLPA PROCESSOR").grid(row=0, column=0, sticky='nsw', padx=(40,0), pady=20)

switch_var = ctk.StringVar(value="off")

def cambiar_tema(color):
    ctk.set_appearance_mode(color)

switch_1 = ""

def switch_event():
    global switch_1
    print(str(switch_var.get()))
    if str(switch_var.get()) == "on":
        cambiar_tema("dark")
        switch_1.configure(text="LIGHT THEME")
    else:
        cambiar_tema("light")
        switch_1.configure(text="DARK THEME")

switch_1 = ctk.CTkSwitch(container4b, text="DARK THEME", font=fontBARRA, command=switch_event, variable=switch_var, onvalue="on", offvalue="off")

switch_1.grid(row=2, column=2, sticky='nse', padx= 40, pady=20)
ctk.CTkLabel(container4b, textvariable=hora_actual, font=fontBARRA).grid(row=2, column=0, sticky='nsw', padx= 20, pady=20)

# FRAME DE OPERACIONES

container = ctk.CTkFrame(Review)
container.grid(row=0, column=0, sticky='nsew')

container.grid_rowconfigure(0,weight=1)
container.grid_columnconfigure(0, weight=1)
container.grid_columnconfigure(1, weight=10)


#---------------------------------------------------------------
# Frame de la izquierda

container1 = ctk.CTkFrame(container)
container1.grid(row=0, column=0, sticky='nsew')
container1.grid_columnconfigure(0, weight=1)

# Frames internos

container1_0 = ctk.CTkFrame(container1)

container1_0.grid(row=0, column=0, padx=20, pady=(40,10), sticky='new')

ctk.CTkButton(container1_0, font=fontTEXTcoll, text='Return', command=lambda:raise_frame(Menup)).grid(row=0,column=0, sticky='nsew', padx=(5,0) , pady=5)

container1_1 = ctk.CTkFrame(container1, width=230, height=120)
container1_1.grid(row=1, column=0, padx=20, pady=(0,10), sticky='new')
container1_1.grid_columnconfigure(0, weight=1)
container1_1.grid_columnconfigure(1, weight=1)
container1_1.grid_propagate("False")

container1_2 = ctk.CTkFrame(container1, width=230, height=550)
container1_2.grid(row=2, column=0, padx=20, pady=10, sticky='nsew')
container1_2.grid_columnconfigure(0, weight=1)
container1_2.grid_columnconfigure(1, weight=1)
container1_2.grid_propagate("False")

# Textos y Entrys Primer FrameMACIÓN
textos_primer_frame = ["Area", "Elasticity Modulus", "Theoretical energy"]

#ET_Entry

ctk.CTkLabel(container1_1, font=fontBARRAleft, text=textos_primer_frame[0]).grid(row=0,column=0, padx=10, pady=5, sticky='nw')
pile_area_label = ctk.CTkLabel(container1_1, font=fontBARRAleft, text=str(round(float(pile_area),2)))
pile_area_label.grid(row=0, column=1, padx=10, pady=5, sticky='nw')
ctk.CTkLabel(container1_1, font=fontBARRAleft, text=textos_primer_frame[1]).grid(row=1,column=0, padx=10, pady=5, sticky='nw') 
EM_label = ctk.CTkLabel(container1_1, font=fontBARRAleft, text=str(round(float(EM_valor_original),2)))
EM_label.grid(row=1, column=1, padx=10, pady=5, sticky='nw')
ctk.CTkLabel(container1_1, font=fontBARRAleft, text=textos_primer_frame[2]).grid(row=2,column=0, padx=10, pady=5, sticky='nw')
ET_label = ctk.CTkLabel(container1_1, font=fontBARRAleft, text=str("0"))
ET_label.grid(row=2, column=1, padx=10, pady=5, sticky='nw')

# Textos y Entrys Segundo Frame
#textos_segundo_frame = ["BL #", "RSP(kN)", "RMX(kN)", "RSU(kN)", "FMX(kN)", "VMX(m/s)", "EMX(kN.m)", "DMX(mm)", "DFN(mm)", "CSX(MPa)", "TSX(MPa)", "BTA"]

Button_Num_Grafica = ctk.CTkButton(container1_2, font=fontBARRAleft, text="")
Button_Num_Grafica.grid(row=0,column=0, padx=10, pady=5, sticky='new') 

def create_toplevel_ayuda_unidades():
    ayuda_unidades_frame = ctk.CTkToplevel()
    ayuda_unidades_frame.title("Ayuda Unidades")
    ayuda_unidades_frame.resizable(False, False) 
    ayuda_unidades_frame.grab_set()
    ayuda_unidades_frame.focus()
    # create label on CTkToplevel window
    container9 = ctk.CTkFrame((ayuda_unidades_frame))
    container9.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
    container9.grid_rowconfigure(0, weight=1)
    container9.grid_columnconfigure(0, weight=1)
    container9.grid_columnconfigure(1, weight=5)
    
    container9_1 = ctk.CTkFrame(container9)
    container9_1.grid(row=0, column=0, padx=10, pady=10)
    for i in range(10):
        container9_1.grid_rowconfigure(i, weight=1)
    ctk.CTkLabel(container9_1, text='CSX').grid(row=0, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_1, text='DMX').grid(row=1, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_1, text='EFV').grid(row=2, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_1, text='ETR').grid(row=3, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_1, text='BPM').grid(row=4, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_1, text='VMX').grid(row=5, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_1, text='FMX').grid(row=6, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_1, text='DFN').grid(row=7, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_1, text='MEX').grid(row=8, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_1, text='AMX').grid(row=9, column=0, padx=5, pady=5)

    container9_2 = ctk.CTkFrame(container9)
    container9_2.grid(row=0, column=1, padx=(0,10), pady=10)
    for i in range(10):
        container9_2.grid_rowconfigure(i, weight=1)
    ctk.CTkLabel(container9_2, text='Maximum measured compressive stress').grid(row=0, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_2, text='Maximum displacement').grid(row=1, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_2, text='Energy measured by Force-Velocity method').grid(row=2, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_2, text='Transferred energy ratio (efficiency)').grid(row=3, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_2, text='Blows per minute').grid(row=4, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_2, text='Maximum Velocity').grid(row=5, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_2, text='Maximum Force').grid(row=6, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_2, text='Last measurement of Displacement').grid(row=7, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_2, text='Maximum Deformation').grid(row=8, column=0, padx=5, pady=5)
    ctk.CTkLabel(container9_2, text='Maximum Acceleration').grid(row=9, column=0, padx=5, pady=5)


boton_ayuda_unidades = ctk.CTkButton(container1_2, width=80, text="?", command=lambda:create_toplevel_ayuda_unidades(), font=fontTEXTcoll).grid(row=0, column=1, padx=5, pady=5)

textos_segundo_frame = ["FMX", "VMX", "EFV", "DMX", "ETR", "CE", "CSX", "DFN", "MEX1", "MEX2", "MEX", "AMX"]
unidades_segundo_frame = [[" kN"," kip"], [" m/s", " ft/s"], [" J", " ft-lbs"], [" mm", " in"], [" %", " %"], ["", ""], [" MPa", " ksi"], [" mm", " in"], [" µe", " µe"], [" µe", " µe"], [" µe", " µe"], [" g's", " g's"]]
unidades_primer_frame = [[" cm²", " in²"], [" MPa", " ksi"], [" J", " ft-lbs"]]
valores_segundo_frame_arriba = ["", "", "", "", "", "", "", "", "", "", "", ""]
valores_segundo_frame_abajo = ["", "", "", "", "", "", "", "", "", "", "", ""]
# labels fijos de texto
for i in range(len(textos_segundo_frame)):
    ctk.CTkLabel(container1_2, font=fontBARRAleft, text=textos_segundo_frame[i]).grid(row=i+1,column=0, padx=10, pady=5, sticky='nw') 

L_FMX = ctk.CTkLabel(container1_2, font=fontBARRAleft, text=valores_segundo_frame_arriba[0])
L_FMX.grid(row=1, column=1,padx=10, pady=5, sticky='nw')

L_VMX = ctk.CTkLabel(container1_2, font=fontBARRAleft, text=valores_segundo_frame_arriba[1])
L_VMX.grid(row=2, column=1,padx=10, pady=5, sticky='nw')

L_EMX = ctk.CTkLabel(container1_2, font=fontBARRAleft, text=valores_segundo_frame_arriba[2])
L_EMX.grid(row=3, column=1,padx=10, pady=5, sticky='nw')

L_DMX = ctk.CTkLabel(container1_2, font=fontBARRAleft, text=valores_segundo_frame_arriba[3])
L_DMX.grid(row=4, column=1,padx=10, pady=5, sticky='nw')  
 
L_ETR = ctk.CTkLabel(container1_2, font=fontBARRAleft, text=valores_segundo_frame_arriba[4])
L_ETR.grid(row=5, column=1,padx=10, pady=5, sticky='nw')

L_CE = ctk.CTkLabel(container1_2, font=fontBARRAleft, text=valores_segundo_frame_arriba[5])
L_CE.grid(row=6, column=1,padx=10, pady=5, sticky='nw')  

L_CSX = ctk.CTkLabel(container1_2, font=fontBARRAleft, text=valores_segundo_frame_arriba[6])
L_CSX.grid(row=7, column=1,padx=10, pady=5, sticky='nw')

L_DFN = ctk.CTkLabel(container1_2, font=fontBARRAleft, text=valores_segundo_frame_arriba[7])
L_DFN.grid(row=8, column=1,padx=10, pady=5, sticky='nw')

L_MEX1 = ctk.CTkLabel(container1_2, font=fontBARRAleft, text=valores_segundo_frame_arriba[8])
L_MEX1.grid(row=9, column=1,padx=10, pady=5, sticky='nw')  

L_MEX2 = ctk.CTkLabel(container1_2, font=fontBARRAleft, text=valores_segundo_frame_arriba[9])
L_MEX2.grid(row=10, column=1,padx=10, pady=5, sticky='nw') 

L_MEX = ctk.CTkLabel(container1_2, font=fontBARRAleft, text=valores_segundo_frame_arriba[10])
L_MEX.grid(row=11, column=1,padx=10, pady=5, sticky='nw')

L_AMX = ctk.CTkLabel(container1_2, font=fontBARRAleft, text=valores_segundo_frame_arriba[11])
L_AMX.grid(row=12, column=1,padx=10, pady=5, sticky='nw')  

frame_sistema_metrico = ctk.CTkFrame(container1_2)
frame_sistema_metrico.grid(row=13, column=0, columnspan=2, padx=10, pady=10, sticky='nwe')

def Switch_sistema_metrico_callback(nuevo_valor):
    global valor_actual_sistema_metrico, unidad_antigua, ultima_grafica_seleccionada
    valor_actual_sistema_metrico = nuevo_valor
    if ultima_grafica_seleccionada == "arriba":
        print("----", dic_ultima_grafica["abajo"])
        Creacion_Grafica("abajo", dic_ultima_grafica_magnitud["abajo"], dic_ultima_grafica["abajo"], "original", "SI", "NO")
        print("----", dic_ultima_grafica["arriba"])
        Creacion_Grafica("arriba", dic_ultima_grafica_magnitud["arriba"], dic_ultima_grafica["arriba"], "original", "SI", "NO")
    else:
        print("----", dic_ultima_grafica["arriba"])
        Creacion_Grafica("arriba", dic_ultima_grafica_magnitud["arriba"], dic_ultima_grafica["arriba"], "original", "SI", "NO")
        print("----", dic_ultima_grafica["abajo"])
        Creacion_Grafica("abajo", dic_ultima_grafica_magnitud["abajo"], dic_ultima_grafica["abajo"], "original", "SI", "NO")

    unidad_antigua = valor_actual_sistema_metrico

Switch_sistema_metrico = ctk.CTkSegmentedButton(frame_sistema_metrico, values=["SI", "EN"], command=Switch_sistema_metrico_callback)

Switch_sistema_metrico.grid_rowconfigure(0, weight=1)
Switch_sistema_metrico.grid_columnconfigure(0, weight=1)
Switch_sistema_metrico.grid(row=0, column=0, sticky='nwe', padx=5, pady=5)

dic_metrico = {"SI":0, "EN":1}

def modificar_datos_segundo_frame(posicion,texto_label_num_grafica, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE, V_CSX, V_DFN, V_MEX1, V_MEX2, V_MEX, V_AMX):
    global valores_segundo_frame_arriba, valores_segundo_frame_abajo, unidades_segundo_frame
    global Button_Num_Grafica, valor_actual_sistema_metrico
    global L_FMX, L_VMX, L_EMX, L_DMX, L_ETR, L_CE, L_CSX, L_DFN, L_MEX1, L_MEX2, L_MEX, L_AMX
    global pile_area, pile_area_label, EM_valor_original, EM_label, ET_valor_original, ET_label
    Button_Num_Grafica.configure(text= str(texto_label_num_grafica), font=fontTEXTcoll)

    
    AR = round(float(pile_area),2)
    EM = round(float(EM_valor_original),2)
    ET = round(float(ET_valor_original),2)
    if unidad_original != valor_actual_sistema_metrico:
        dic_transformacion_ar_em_et = {"SI":[1/0.15500031000062,1/0.14503773800722,1/0.7375621493], "EN":[0.15500031000062, 0.14503773800722, 0.7375621493]}
        AR = round(AR * dic_transformacion_ar_em_et[valor_actual_sistema_metrico][0],2)
        EM = round(EM * dic_transformacion_ar_em_et[valor_actual_sistema_metrico][1],2)
        ET = round(ET * dic_transformacion_ar_em_et[valor_actual_sistema_metrico][2],2)
    
    valores = [AR, EM, ET, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE, V_CSX, V_DFN, V_MEX1, V_MEX2, V_MEX, V_AMX]
    valores2 = valores.copy()
    print("------------------------------",valores2)

    for index, i in enumerate(valores2):
        
        if index > 1:
            try:
                if i=="":
                    valores2[index] = "0.00"
                else:
                    parte_entera = int(i)
                    parte_decimal = round(abs(i) - abs(int(i)),2)
                    if len(str(parte_decimal)) < 4:
                        valores2[index] = str(i)+"0"
                    else:
                        valores2[index] = str(i)
            except Exception as e:
                print(e, 8)

    pile_area_label.configure(text=str(valores2[0]) + unidades_primer_frame[0][dic_metrico[valor_actual_sistema_metrico]])
    EM_label.configure(text=str(valores2[1]) + unidades_primer_frame[1][dic_metrico[valor_actual_sistema_metrico]])
    ET_label.configure(text=str(valores2[2]) + unidades_primer_frame[2][dic_metrico[valor_actual_sistema_metrico]])


    L_FMX.configure(text = str(valores2[3])+unidades_segundo_frame[0][dic_metrico[valor_actual_sistema_metrico]])
    L_VMX.configure(text = str(valores2[4])+unidades_segundo_frame[1][dic_metrico[valor_actual_sistema_metrico]])
    L_EMX.configure(text = str(valores2[5])+unidades_segundo_frame[2][dic_metrico[valor_actual_sistema_metrico]])
    L_DMX.configure(text = str(valores2[6])+unidades_segundo_frame[3][dic_metrico[valor_actual_sistema_metrico]]) # cambiado a milimetros
    L_ETR.configure(text = str(valores2[7])+unidades_segundo_frame[4][dic_metrico[valor_actual_sistema_metrico]])
    L_CE.configure(text = str(valores2[8])+unidades_segundo_frame[5][dic_metrico[valor_actual_sistema_metrico]])
    L_CSX.configure(text = str(valores2[9])+unidades_segundo_frame[6][dic_metrico[valor_actual_sistema_metrico]])
    L_DFN.configure(text = str(valores2[10])+unidades_segundo_frame[7][dic_metrico[valor_actual_sistema_metrico]])
    L_MEX1.configure(text = str(valores2[11])+unidades_segundo_frame[8][dic_metrico[valor_actual_sistema_metrico]])
    L_MEX2.configure(text = str(valores2[12])+unidades_segundo_frame[9][dic_metrico[valor_actual_sistema_metrico]])
    L_MEX.configure(text = str(valores2[13])+unidades_segundo_frame[10][dic_metrico[valor_actual_sistema_metrico]])
    L_AMX.configure(text = str(valores2[14])+unidades_segundo_frame[11][dic_metrico[valor_actual_sistema_metrico]])

    if posicion == 'arriba':
        valores_segundo_frame_arriba = [texto_label_num_grafica, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE, V_CSX, V_DFN, V_MEX1, V_MEX2, V_MEX, V_AMX]
    else:
        valores_segundo_frame_abajo = [texto_label_num_grafica, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE, V_CSX, V_DFN, V_MEX1, V_MEX2, V_MEX, V_AMX]

#--------------------------------------------------
# Frame Principal del medio
container2 = ctk.CTkFrame(container)
container2.grid_columnconfigure(0, weight=30)
container2.grid_columnconfigure(1, weight=1)
container2.grid_rowconfigure(0, weight=1)
container2.grid_rowconfigure(1, weight=1)

container2.grid(row=0,column=1, padx=(30,10), pady=(30), sticky='nswe')


# rectangulos principales

# frame de arriba
container2_1 = ctk.CTkFrame(container2)
container2_1.grid_columnconfigure(0, weight=1)
container2_1.grid_rowconfigure(0, minsize= 40, weight=1)
container2_1.grid_rowconfigure(1, weight=20)
container2_1.grid_rowconfigure(2, minsize=40, weight=1)
container2_1.grid(row=0, column=0, padx=10, pady=(10,5), sticky='nsew')

container2_1_1 = ctk.CTkFrame(container2_1, corner_radius=0)
container2_1_1.grid(row=0, column=0, sticky='new')
#for i in range(7):
#    container2_1_1.grid_columnconfigure(i, weight=8)
container2_1_1.grid_columnconfigure(0, weight=1)
container2_1_1.grid_columnconfigure(1, weight=20)
container2_1_1.grid_rowconfigure(0, weight=1)

container2_1_2 = ctk.CTkFrame(container2_1, fg_color="#21bb13")
container2_1_2.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0,5))
container2_1_3 = ctk.CTkFrame(container2_1)
container2_1_3.grid(row=2, column=0, sticky='nsew', padx=10, pady=(0,5))

container2_1_3.grid_rowconfigure(0, weight=1)
container2_1_3.grid_columnconfigure(0, weight=1)

# frame de abajo
container2_2 = ctk.CTkFrame(container2)
container2_2.grid_columnconfigure(0, weight=1)
container2_2.grid_rowconfigure(0, minsize=40, weight=1)
container2_2.grid_rowconfigure(1, weight=20)
container2_2.grid_rowconfigure(2, minsize=40, weight=1)
container2_2.grid(row=1, column=0, padx=10, pady=(5,10), sticky='new')

container2_2_1 = ctk.CTkFrame(container2_2, corner_radius=0)
container2_2_1.grid(row=0, column=0, sticky='new')
#for i in range(7):
#    container2_2_1.grid_columnconfigure(i, weight=8)
container2_2_1.grid_columnconfigure(0, weight=1)
container2_2_1.grid_columnconfigure(1, weight=20)
container2_2_1.grid_columnconfigure(2, weight=1)
container2_2_1.grid_rowconfigure(0, weight=1)

container2_2_2 = ctk.CTkFrame(container2_2, fg_color="#94e7ff")
container2_2_2.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0,5))
container2_2_3 = ctk.CTkFrame(container2_2)
container2_2_3.grid(row=2, column=0, sticky='nsew', padx=10, pady=(0,5))

container2_2_3.grid_rowconfigure(0, weight=1)
container2_2_3.grid_columnconfigure(0, weight=250)
container2_2_3.grid_columnconfigure(1, weight=1)

dic_inverso = {"arriba":"abajo", "abajo":"arriba"}

def actualizar_magnitud(posicion,i):
    global ultima_magnitud_abajo
    global ultima_magnitud_arriba
    dic_ultima_grafica_magnitud[posicion] = dic_magnitud_botones[i]

texto_botones_frame= ["ACCELERATION", "VELOCITY", "DEFORMATION", "FORCE", "DISPLACEMENT", "F vs V", "Avg E", "WU", "WD"]

# Estos botones están fuera de un bucle for por usar una función lambda dentro de sus comandos, los cuales dan i como 3 siempre que se ejecutan

def actualizacion_magnitud_sincronizada(magnitud):
    print("la magnitud insertada es", magnitud)
    global fig1, fig2, ax1, ax2, ultima_grafica_seleccionada, canvas1, canvas2
    global A3, A4, S1, S2, F1, F2, V1, V2, E, D1, D2, F, V_Transformado, segundos, WU, WD, Z
    global numero_anterior

    if dic_ultima_grafica[ultima_grafica_seleccionada] != numero_anterior:
        A3, A4, S1, S2, F1, F2, V1, V2, E, D1, D2, F, V_Transformado, segundos, t, t, t, t, t, t, t, t, WU, WD, t, t, t, t, t, t = Creacion_Datos_Graficas(dic_ultima_grafica_magnitud[ultima_grafica_seleccionada],  dic_ultima_grafica[ultima_grafica_seleccionada], "original", "SI")
    else:
        pass

    numero_anterior = dic_ultima_grafica[ultima_grafica_seleccionada]

    if ultima_grafica_seleccionada == "arriba":
        Button_num_grafica_abajo.configure(text=str(numero_anterior))
        dic_ultima_grafica["abajo"] = numero_anterior
    else:
        Button_num_grafica_arriba.configure(text=str(numero_anterior))
        dic_ultima_grafica["arriba"] = numero_anterior

    dic_magnitud_sincronizacion = {'aceleracion':[A3, A4], 'deformacion':[S1, S2], 'fuerza':[F1, F2], 'velocidad':[V1, V2], 'avged':[E, E], 'desplazamiento':[D1, D2], 'fuerzaxvelocidad':[F,V_Transformado], 'wu':[WU, WU], 'wd':[WD, WD]}
    dic_legenda = {'aceleracion':["A3", "A4"], 'deformacion':["S1", "S2"], 'fuerza':["F1", "F2"], 'velocidad':["V1", "V2"], 'avged':["E", "E"], 'desplazamiento':["D1", "D2"], 'fuerzaxvelocidad':["F", str(round(Z, 2))+"*V"], 'wu':['WU', 'WU'], 'wd':['WD', 'WD']}

    if ultima_grafica_seleccionada == "arriba":
        fig2.clear()
        ax2 = fig2.add_subplot(111)
        t, = ax2.plot(segundos, dic_magnitud_sincronizacion[dic_ultima_grafica_magnitud[dic_inverso[ultima_grafica_seleccionada]]][0])
        t2, = ax2.plot(segundos, dic_magnitud_sincronizacion[dic_ultima_grafica_magnitud[dic_inverso[ultima_grafica_seleccionada]]][1])
        ax2.set_xlim(ax1.get_xlim())
        canvas2.draw()

    elif ultima_grafica_seleccionada == "abajo":
        fig1.clear()
        ax1 = fig1.add_subplot(111)
        t, = ax1.plot(segundos, dic_magnitud_sincronizacion[dic_ultima_grafica_magnitud[dic_inverso[ultima_grafica_seleccionada]]][0])
        t2, = ax1.plot(segundos, dic_magnitud_sincronizacion[dic_ultima_grafica_magnitud[dic_inverso[ultima_grafica_seleccionada]]][1])
        ax1.set_xlim(ax2.get_xlim())
        canvas1.draw()

# botones de los frames

dic_magnitud_botones = {0:'aceleracion', 1:'velocidad', 2:'deformacion', 3:'fuerza', 4:'desplazamiento', 5:'fuerzaxvelocidad', 6:'avged', 7:'wu', 8:'wd'}
dic_ultima_grafica_magnitud = {"arriba": ultima_magnitud_arriba, "abajo": ultima_magnitud_abajo}

def segmented_button_callback1(value):
    global texto_botones_frame, estado_sincro, Button_num_grafica_arriba, dic_ultima_grafica_magnitud
    print("el valor seleccionado arriba es: ",value)
    print("********arriba***********")
    if estado_sincro == "desincronizado" or ultima_grafica_seleccionada == "arriba":
        colorear_botones_seleccion_grafica(1)
        match value:
            case "ACCELERATION":
                cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
                actualizar_magnitud("arriba", texto_botones_frame.index(value))
            case "VELOCITY":
                cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
                actualizar_magnitud("arriba", texto_botones_frame.index(value))
            case "DEFORMATION":
                cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
                actualizar_magnitud("arriba", texto_botones_frame.index(value))
            case "FORCE":
                cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
                actualizar_magnitud("arriba", texto_botones_frame.index(value))
            case "DISPLACEMENT":
                cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
                actualizar_magnitud("arriba", texto_botones_frame.index(value))
            case "F vs V":
                cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
                actualizar_magnitud("arriba", texto_botones_frame.index(value))
            case "Avg E":
                cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
                actualizar_magnitud("arriba", texto_botones_frame.index(value))
            case "WU":
                cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
                actualizar_magnitud("arriba", texto_botones_frame.index(value))
            case "WD":
                cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
                actualizar_magnitud("arriba", texto_botones_frame.index(value))
    else:
        print("-----------arriba-----------")
        Button_num_grafica_arriba.invoke()
        match value:
            case "ACCELERATION":
                dic_ultima_grafica_magnitud["arriba"] = "aceleracion"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "VELOCITY":
                dic_ultima_grafica_magnitud["arriba"] = "velocidad"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "DEFORMATION":
                dic_ultima_grafica_magnitud["arriba"] = "deformacion"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "FORCE":
                dic_ultima_grafica_magnitud["arriba"] = "fuerza"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "DISPLACEMENT":
                dic_ultima_grafica_magnitud["arriba"] = "desplazamiento"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "F vs V":
                dic_ultima_grafica_magnitud["arriba"] = "fuerzaxvelocidad"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "Avg E":
                dic_ultima_grafica_magnitud["arriba"] = "aceleracion"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "WU":
                dic_ultima_grafica_magnitud["arriba"] = "wu"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "WD":
                dic_ultima_grafica_magnitud["arriba"] = "wd"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
       
def segmented_button_callback2(value):
    global texto_botones_frame, estado_sincro, Button_num_grafica_abajo
    print("el valor seleccionado abajo es: ",value)
    
    if estado_sincro == "desincronizado" or ultima_grafica_seleccionada == "abajo":
        colorear_botones_seleccion_grafica(2)
        print("********abajo***********")
        match value:
            case "ACCELERATION":
                cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
                actualizar_magnitud("abajo", texto_botones_frame.index(value))
            case "VELOCITY":
                cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
                actualizar_magnitud("abajo", texto_botones_frame.index(value))
            case "DEFORMATION":
                cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
                actualizar_magnitud("abajo", texto_botones_frame.index(value))
            case "FORCE":
                cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
                actualizar_magnitud("abajo", texto_botones_frame.index(value))
            case "DISPLACEMENT":
                cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
                actualizar_magnitud("abajo", texto_botones_frame.index(value))
            case "F vs V":
                cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
                actualizar_magnitud("abajo", texto_botones_frame.index(value))
            case "Avg E":
                cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
                actualizar_magnitud("abajo", texto_botones_frame.index(value))
            case "WU":
                cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
                actualizar_magnitud("abajo", texto_botones_frame.index(value))
            case "WD":
                cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
                actualizar_magnitud("abajo", texto_botones_frame.index(value))    
    else:
        print("-----------abajo-----------")
        Button_num_grafica_abajo.invoke()
        match value:
            case "ACCELERATION":
                dic_ultima_grafica_magnitud["abajo"] = "aceleracion"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "VELOCITY":
                dic_ultima_grafica_magnitud["abajo"] = "velocidad"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "DEFORMATION":
                dic_ultima_grafica_magnitud["abajo"] = "deformacion"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "FORCE":
                dic_ultima_grafica_magnitud["abajo"] = "fuerza"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "DISPLACEMENT":
                dic_ultima_grafica_magnitud["abajo"] = "desplazamiento"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "F vs V":
                dic_ultima_grafica_magnitud["abajo"] = "fuerzaxvelocidad"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "Avg E":
                dic_ultima_grafica_magnitud["abajo"] = "avged"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "WU":
                dic_ultima_grafica_magnitud["abajo"] = "wu"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])
            case "WD":
                dic_ultima_grafica_magnitud["abajo"] = "wd"
                actualizacion_magnitud_sincronizada(dic_magnitud_botones[texto_botones_frame.index(value)])

container_num_2_1_1 = ctk.CTkFrame(container2_1_1)
container_num_2_1_1.grid(row=0, column=0, sticky='nsw', pady=5)
container_num_2_1_1.grid_columnconfigure(0, weight=1)
container_num_2_1_1.grid_columnconfigure(1, weight=1)
container_num_2_1_1.grid_rowconfigure(0, weight=1)

Button_num_grafica_arriba = ctk.CTkButton(container_num_2_1_1, text="1", width=30, command=lambda:[colorear_botones_seleccion_grafica(1), cambiar_grafica_exacto(Entry_num_grafica_exacto_arriba.get(), "arriba")])
Button_num_grafica_arriba.grid(row=0, column=0, sticky='nsw', pady=2, padx=2)

Entry_num_grafica_exacto_arriba = ctk.CTkEntry(container_num_2_1_1, width=50)
Entry_num_grafica_exacto_arriba.grid(row=0, column=1, sticky='nsw', pady=2, padx=(0,2))

container_num_2_2_1 = ctk.CTkFrame(container2_2_1)
container_num_2_2_1.grid(row=0, column=0, sticky='nsw', pady=5)
container_num_2_2_1.grid_columnconfigure(0, weight=1)
container_num_2_2_1.grid_columnconfigure(1, weight=1)
container_num_2_2_1.grid_rowconfigure(0, weight=1)

Button_num_grafica_abajo = ctk.CTkButton(container_num_2_2_1, text="1", width=30, command=lambda:[colorear_botones_seleccion_grafica(2), cambiar_grafica_exacto(Entry_num_grafica_exacto_abajo.get(), "abajo")])
Button_num_grafica_abajo.grid(row=0, column=0, sticky='nsw', pady=2, padx=2)

Entry_num_grafica_exacto_abajo = ctk.CTkEntry(container_num_2_2_1, width=50)
Entry_num_grafica_exacto_abajo.grid(row=0, column=1, sticky='nsw', pady=2, padx=(0,2))

segemented_button_var1 = ctk.StringVar(value="ACCELERATION")
segemented_button = ctk.CTkSegmentedButton(container2_1_1, font=font_barra_cambio_magnitud, values=texto_botones_frame, command=segmented_button_callback1, variable=segemented_button_var1)
segemented_button.grid(row=0,column=1, sticky='nsew', pady=5, padx=(0))

segemented_button_var2 = ctk.StringVar(value="DEFORMATION")
segemented_button2 = ctk.CTkSegmentedButton(container2_2_1,font=font_barra_cambio_magnitud, values=texto_botones_frame, command=segmented_button_callback2, variable=segemented_button_var2)
segemented_button2.grid(row=0,column=1, sticky='nsew', pady=5, padx=(0))

# Barra lateral de la columna de la derecha

container2_3 = ctk.CTkFrame(container2, corner_radius=0)
container2_3.grid(row=0, rowspan=2, column=1, sticky='nsew')
container2_3.grid_rowconfigure(0, weight=1)
container2_3.grid_columnconfigure(0, weight=1)

def colorear_botones_seleccion_grafica(num):
    global ultima_grafica_seleccionada, valores_segundo_frame_arriba, valores_segundo_frame_abajo, container2_1_2, container2_2_2
    global estado_sincro
    if estado_sincro == "desincronizado":
        if num == 1:
            ultima_grafica_seleccionada = 'arriba'
            container2_1_2.configure(fg_color="#1359BB")
            container2_2_2.configure(fg_color="#94e7ff")
            v_vec = valores_segundo_frame_arriba.copy()
            modificar_datos_segundo_frame('arriba', v_vec[0], v_vec[1], v_vec[2], v_vec[3], v_vec[4], v_vec[5], v_vec[6], v_vec[7], v_vec[8], v_vec[9], v_vec[10], v_vec[11], v_vec[12])
        else:
            ultima_grafica_seleccionada = 'abajo'
            container2_2_2.configure(fg_color="#1359BB")
            container2_1_2.configure(fg_color="#94e7ff")
            v_vec = valores_segundo_frame_abajo.copy()
            modificar_datos_segundo_frame('abajo', v_vec[0], v_vec[1], v_vec[2], v_vec[3], v_vec[4], v_vec[5], v_vec[6], v_vec[7], v_vec[8], v_vec[9], v_vec[10], v_vec[11], v_vec[12])


# cambiar magnitudes

def cambiar_magnitud_grafica(posicion,magnitud):

    if magnitud == 6:
        Creacion_Grafica(posicion, dic_magnitud_botones[magnitud], dic_ultima_grafica[posicion], "original", "NO", "SI")

    else:
        Creacion_Grafica(posicion, dic_magnitud_botones[magnitud], dic_ultima_grafica[posicion], "original", "NO", "NO")

dic_posicion = {"arriba":[container2_1_2, container2_1_3], "abajo":[container2_2_2, container2_2_3]}

class Toolbar(NavigationToolbar2TkAgg):
    def set_message(self, s):
        pass


def calculo_wu(F, V_transformado):
    suma = []
    for i in range(len(F)):
        suma.append((F[i]-V_transformado[i])/2)
    return suma

def calculo_wd(F, V_transformado):
    suma = []
    for i in range(len(F)):
        suma.append((F[i]+V_transformado[i])/2)
    return suma

def integrate(tr_00):
    tr_0 = tr_00.copy()
    tr_0.integrate(method = "cumtrapz")
    return tr_0

def Creacion_Datos_Graficas(magnitud, num, direccion, mantener_limites):
    global frecuencia_muestreo, pile_area, EM_valor_original, ET_valor_original 
    global x_zoom_grafica_abajo, y_zoom_grafica_abajo, x_zoom_grafica_arriba, y_zoom_grafica_arriba
    global p_primera_marca, p_segunda_marca, segundo_inicial, segundo_final, Button_Num_Grafica
    global unidad_original, valor_actual_sistema_metrico
    
    F1, F2, F, V1, V2, V, E, D1, D2, D, WU, WD = [], [], [], [], [], [], [], [], [], [], [], []

    V_Transformado = []
    V_Transformado_valor_real = []
    global L_EMX, L_FMX, L_VMX, L_DMX, L_CE, L_ETR

    #print("el gráfico que se hace es ", num)
    segundos, S1, S2, A3, A4 = Obtencion_data_serial(num)

    Z = 0
    EM = float(EM_valor_original)
    AR = float(pile_area)
    ET = float(ET_valor_original)
    #print("El EM y AR son", EM, AR)
    if unidad_original != "SI":
        AR = AR * (1/0.15500031000062)
        EM = EM * (1/0.14503773800722)
        ET = ET * (1/0.7375621493)
    factor = EM * AR
    longitud = max(len(S1), len(S2))
    longitud2 = max(len(A3), len(A4))

    m1 = 0
    m2 = 0
    for i in range(longitud):
        try:
            m1 = S1[i]*factor/10000000
        except:
            pass
        try:
            m2 = S2[i]*factor/10000000
        except:
            pass
        promedio = (m1+m2)/2
        if S1 != [] and len(S1) == longitud:
            F1.append(m1)
        if S2 != [] and len(S2) == longitud:
            F2.append(m2)
        F.append(promedio)
    
    
    if len(S1) != longitud:
        S1 = S2
        F = F2
        F1 = F2
    if len(S2) != longitud:
        S2 = S1
        F = F1
        F2 = F1

    #print("valores de máxima deformación", max(S1), max(S2))

    MEX1 = round(max(S1),2)
    MEX2 = round(max(S2),2)
    MEX = round((MEX1+MEX2)/2, 2)
    print(f"Longitud1 es {longitud} y Longitud2 es {longitud2}")
    if len(A3) != longitud2:
        A3 = A4
    if len(A4) != longitud2:
        A4 = A3
    AMX = round(max(max(A3), max(A4)),2) 
    
    if S1 == []:
        F = F2
    elif S2 == []:
        F = F1
    Fmax = round(max(F), 2)
    Fmax_original = max(F)
    
    longitud = max(len(A3), len(A4))

    # Calculando velocidad 1
    try:
        print("Esta es la frecuencia:",int(frecuencia_muestreo[-1]))
        
        V1 = velocidad_nuevo_metodo(np.array(A3[:longitud]), int(frecuencia_muestreo[-1]))
    except Exception as e:
        print(f"Error al calcular la velocidad V1 {e}")
    
    try:
        print("Esta es la frecuencia:",int(frecuencia_muestreo[-1]))
        V2 = velocidad_nuevo_metodo(np.array(A4[:longitud]), int(frecuencia_muestreo[-1]))
    except Exception as e:
        print(f"Error al calcular la velocidad V2 {e}")

    if A3 == []:
        print("Ingrese A3")
        V = V2
    elif A4 == []:
        print("Ingrese A4")
        V = V1
    else:
        print("Ingrese ELSE")
        V = (V1 + V2)/2

    Vmax = round(max(V), 2)

    Vmax_original = max(V)

    longitud = max(len(S1), len(S2))

    try:
        D1 = desplazamiento_tesis(V1, int(frecuencia_muestreo[-1]))
    except Exception as e:
        print(f"Error al calcular el desplazamiento D1 {e}")
    
    try:
        D2 = desplazamiento_tesis(V2, int(frecuencia_muestreo[-1]))
    except Exception as e:
        print(f"Error al calcular el desplazamiento D2 {e}")

    if len(V1) == 0:
        D = D2
    elif len(V2) == 0:
        D = D1
    elif len(V1) == len(V2):
        D = (D1 + D2)/2
    else:
        D = D1 if len(V1) > len(V2) else D2

    Dmax = round(1000*max(D), 2)

    DFN = round(1000*D[-1],2)
   
    Z = ((AR*(1000000))*EM*(0.0001))/(5103.44*1000)

    imax = F.index(Fmax_original)
    
    for i in range(len(V)):
        valor = V[i]*Z
        V_Transformado.append(valor)
        V_Transformado_valor_real.append(V[i])

    dic_desplazamiento = {'izquierda': -1, 'derecha': 1, 'mantener': 0}
    
    if magnitud == 'avged':
        condicion = 'NO'
    else:
        condicion = 'SI'
    try:
        E = energia_original(F,V, int(frecuencia_muestreo[-1]))
        print("freq:ssss",int(frecuencia_muestreo[-1]))
    except Exception as e:
        print(f"Error al calcular la Energía E {E}")
    j = 0
    segundos_Transformado = []
    for i in range(len(segundos)):
        n = round(j/(int(frecuencia_muestreo[-1])),2)
        j+=1
        segundos_Transformado.append(n)
    
    Emax = round(max(E), 2)

    # anadiendo el calculo de wu
    try:
        WU = calculo_wu(F, V_Transformado)
    except Exception as e:
        print("Error al calcular el wu", e)
    try:
        WD = calculo_wd(F, V_Transformado)
    except Exception as e:
        print("Error al calcular el wd", e)
    
    if magnitud == 'avged':
        segundos = segundos_Transformado
    
    ETR = round(100*(Emax/ET),2)
    CE = round(ETR/60,2) # dividir
    CSX = round(Fmax*10/AR,2)

    #print("los valores de unidades son", unidad_original, "|", valor_actual_sistema_metrico)

    if valor_actual_sistema_metrico != "SI":
        valores_de_transformacion = {"EN":[0.0393700787401574, 0.22480894387096, 3.28083989501312, 0.7375621493, 0.1450377377],
                                     "SI":[1, 1, 1, 1, 1]}   
        #cambiando la fuerza
        F1 = np.dot(F1, valores_de_transformacion[valor_actual_sistema_metrico][1])
        F2 = np.dot(F2, valores_de_transformacion[valor_actual_sistema_metrico][1])
        F = np.dot(F, valores_de_transformacion[valor_actual_sistema_metrico][1])
        #cambiando la velocidad
        V1 = np.dot(V1, valores_de_transformacion[valor_actual_sistema_metrico][2])
        V2 = np.dot(V2, valores_de_transformacion[valor_actual_sistema_metrico][2])
        V_Transformado = np.dot(V_Transformado, valores_de_transformacion[valor_actual_sistema_metrico][1])
        #camiando energía
        E = np.dot(E, valores_de_transformacion[valor_actual_sistema_metrico][3])
        #cambiando desplazamiento
        D1 = np.dot(D1, 1000*valores_de_transformacion[valor_actual_sistema_metrico][0])
        D2 = np.dot(D2, 1000*valores_de_transformacion[valor_actual_sistema_metrico][0])
        #cambiando valores
        ET = ET * valores_de_transformacion[valor_actual_sistema_metrico][3]
        Fmax = round(Fmax * valores_de_transformacion[valor_actual_sistema_metrico][1],2)
        Vmax = round(Vmax * valores_de_transformacion[valor_actual_sistema_metrico][2],2)
        Emax = round(Emax * valores_de_transformacion[valor_actual_sistema_metrico][3],2)
        Dmax = round(Dmax * valores_de_transformacion[valor_actual_sistema_metrico][0],2)
        CSX = round(CSX * valores_de_transformacion[valor_actual_sistema_metrico][4],2)
        DFN = round(DFN * valores_de_transformacion[valor_actual_sistema_metrico][0], 2)
    
    return A3, A4, S1, S2, F1, F2, V1, V2, E, D1, D2, F, V_Transformado, segundos, ET, ETR, CE, Fmax, Vmax, Emax, Dmax, Z, WU, WD, CSX, DFN, MEX1, MEX2 ,MEX, AMX

def onclick1(event):
    Button_num_grafica_arriba.invoke()

def onclick2(event):
    Button_num_grafica_abajo.invoke()

style.use('seaborn-v0_8-whitegrid')

# grafica 1
fig1 = Figure(figsize=(10, 5), dpi=100)

ax1 = fig1.add_subplot(111)

canvas1 = FigureCanvasTkAgg(fig1, dic_posicion['arriba'][0])
canvas1.draw()
canvas1.get_tk_widget().pack(side=TOP, expand=1, fill=BOTH, padx=10, pady=10)
canvas1.mpl_connect('button_press_event', onclick1)

toolbar = Toolbar(canvas1, dic_posicion['arriba'][1])
toolbar.config(background="#2A2A2A")
toolbar.update()
canvas1._tkcanvas.pack()
fig1.subplots_adjust(left=0.1,bottom=0.15,right=0.98,top=0.96)

t1, = ax1.plot(np.arange(1, 8001), np.zeros(8000))
t2, = ax1.plot(np.arange(1, 8001), np.zeros(8000))

# grafica 2
fig2 = Figure(figsize=(10, 5), dpi=100)

ax2 = fig2.add_subplot(111)

canvas2 = FigureCanvasTkAgg(fig2, dic_posicion['abajo'][0])
canvas2.draw()
canvas2.get_tk_widget().pack(side=TOP, expand=1, fill=BOTH, padx=10, pady=10)
canvas2.mpl_connect('button_press_event', onclick2)

toolbar = Toolbar(canvas2, dic_posicion['abajo'][1])
toolbar.config(background="#2A2A2A")
toolbar.update()
canvas2._tkcanvas.pack()
fig2.subplots_adjust(left=0.1,bottom=0.15,right=0.98,top=0.96)

t3, = ax2.plot(np.arange(1, 8001), np.zeros(8000))
t4, = ax2.plot(np.arange(1, 8001), np.zeros(8000))

estado = "aceleracion"
Z = ""

def Creacion_Grafica(posicion, magnitud, num, direccion, mantener_relacion_aspecto, mantener_limites):
    
    print("---------1el numero de gráfica que se hace es", num)
    global zoom_x_general_arriba, zoom_x_general_abajo, zooms_graficas, magnitud_antigua_arriba, magnitud_antigua_abajo, zoom_y_general_arriba, zoom_y_general_abajo
    global t1, t2, t3, t4, ax1, fig1, canvas1, ax2, fig2, canvas2
    global unidad_original, valor_actual_sistema_metrico, unidad_antigua, Z
    global A3, A4, S1, S2, F1, F2, V1, V2, E, D1, D2, WU, WD
    A3, A4, S1, S2, F1, F2, V1, V2, E, D1, D2, F, V_Transformado, segundos, ET, ETR, CE, Fmax, Vmax, Emax, Dmax, Z, WU, WD, CSX, DFN, MEX1, MEX2, MEX, AMX = Creacion_Datos_Graficas(magnitud, num, direccion, mantener_limites)
    dic_magnitud = {'aceleracion':[A3, A4], 'deformacion':[S1, S2], 'fuerza':[F1, F2], 'velocidad':[V1, V2], 'avged':[E, E], 'desplazamiento':[D1, D2], 'fuerzaxvelocidad':[F,V_Transformado], 'wu':[WU, WU], 'wd':[WD, WD]}
    dic_legenda = {'aceleracion':["A3", "A4"], 'deformacion':["S1", "S2"], 'fuerza':["F1", "F2"], 'velocidad':["V1", "V2"], 'avged':["E", "E"], 'desplazamiento':["D1", "D2"], 'fuerzaxvelocidad':["F", str(round(Z, 2))+"*V"], 'wu':['WU', 'WU'], 'wd':['WD', 'WD']}
    dic_unidades = {'aceleracion':[["ms", "g's"], ["ms", "g's"]], 'deformacion':[["ms", "uE"], ["ms", "uE"]], 'fuerza':[["ms", "kN"], ["ms", "kips"]], 'velocidad':[["ms", "m/s"], ["ms", "ft/s"]], 'avged':[["ms", "(J)"], ["ms", "ft-lbs"]],
                    'desplazamiento':[["ms", "mm"],["ms", "in"]], 'fuerzaxvelocidad':[["ms", ""], ["ms", ""]], 'wu':[['ms', 'kN'], ['ms', 'kips']], 'wd':[['ms', 'kN'], ['ms', 'kip']]}

    texto_label_num_grafica = str(dic_ultima_grafica[posicion])+"/"+str(len(matriz_data_archivos)-1)
    
    print("---------2el numero de gráfica que se hace es", num)
    if posicion == 'arriba': 
        Button_num_grafica_arriba.configure(text=dic_ultima_grafica[posicion])
    elif posicion == 'abajo': 
        Button_num_grafica_abajo.configure(text=dic_ultima_grafica[posicion])
    
    modificar_datos_segundo_frame(posicion, texto_label_num_grafica, Fmax, Vmax, Emax, Dmax, ETR, CE, CSX, DFN, MEX1, MEX2, MEX, AMX)
    print("---------3el numero de gráfica que se hace es", num)
    if posicion == 'arriba':
        if magnitud_antigua_arriba == magnitud:
            if zoom_y_general_arriba != "":
                zoom_y_general_antiguo_arriba = ax1.get_ylim()
            else:
                zoom_y_general_antiguo_arriba = ""
        
        if zoom_x_general_arriba != "":
            zoom_x_general_antiguo_arriba = ax1.get_xlim()
        else:
            zoom_x_general_antiguo_arriba = ""
        fig1.clear()
        ax1 = fig1.add_subplot(111)
        t1, = ax1.plot(segundos, dic_magnitud[magnitud][0], label=dic_legenda[magnitud][0])
        t2, = ax1.plot(segundos, dic_magnitud[magnitud][1], label=dic_legenda[magnitud][1])
        ax1.set_xlabel(dic_unidades[magnitud][dic_metrico[valor_actual_sistema_metrico]][0])
        ax1.set_ylabel(dic_unidades[magnitud][dic_metrico[valor_actual_sistema_metrico]][1])
        zoom_x_general_arriba = ax1.get_xlim()
        zoom_y_general_arriba = ax1.get_ylim()
        if zoom_x_general_antiguo_arriba != zoom_x_general_arriba and zoom_x_general_antiguo_arriba != "":
            ax1.set_xlim(zoom_x_general_antiguo_arriba)
        if magnitud_antigua_arriba == magnitud :
            if unidad_antigua != valor_actual_sistema_metrico or numero_grafica_antiguo_arriba != num:
                pass
            else:
                if zoom_y_general_antiguo_arriba != zoom_y_general_arriba and zoom_y_general_antiguo_arriba != "":
                    ax1.set_ylim(zoom_y_general_antiguo_arriba)
        try:
            ax1.legend(handles=[t1, t2])
        except:
            try:
                ax1.legend(handles=[t1])
            except:
                try:
                    ax1.legend(handles=[t2])
                except Exception as e:
                    print(e, 11)
        magnitud_antigua_arriba = magnitud
        
        canvas1.draw()

    elif posicion == 'abajo':
        if magnitud_antigua_abajo == magnitud:
            if zoom_y_general_abajo != "":
                zoom_y_general_antiguo_abajo = ax2.get_ylim()
            else:
                zoom_y_general_antiguo_abajo = ""
        if zoom_x_general_abajo != "":
            zoom_x_general_antiguo_abajo = ax2.get_xlim()
        else:
            zoom_x_general_antiguo_abajo = ""
        fig2.clear()
        ax2 = fig2.add_subplot(111)
        t3, = ax2.plot(segundos, dic_magnitud[magnitud][0], label=dic_legenda[magnitud][0])
        t4, = ax2.plot(segundos, dic_magnitud[magnitud][1], label=dic_legenda[magnitud][1])
        ax2.set_xlabel(dic_unidades[magnitud][dic_metrico[valor_actual_sistema_metrico]][0])
        ax2.set_ylabel(dic_unidades[magnitud][dic_metrico[valor_actual_sistema_metrico]][1])
        zoom_x_general_abajo = ax2.get_xlim()
        zoom_y_general_abajo = ax2.get_ylim()
        if zoom_x_general_antiguo_abajo != zoom_x_general_abajo and zoom_x_general_antiguo_abajo != "":
            ax2.set_xlim(zoom_x_general_antiguo_abajo)
        if magnitud_antigua_abajo == magnitud:
            if unidad_antigua != valor_actual_sistema_metrico or numero_grafica_antiguo_abajo != num:
                pass
            else:
                if zoom_y_general_antiguo_abajo != zoom_y_general_abajo and zoom_y_general_antiguo_abajo != "":
                    ax2.set_ylim(zoom_y_general_antiguo_abajo)
        try:
            ax2.legend(handles=[t3, t4])
        except:
            try:
                ax2.legend(handles=[t3])
            except:
                try:
                    ax2.legend(handles=[t4])
                except Exception as e:
                    print(e, 12)
        magnitud_antigua_abajo = magnitud
        canvas2.draw()

# Configuración de los botones comandos

dic_direccion = {'derecha': 1, 'izquierda': -1, 'derecha+' :3, 'izquierda+': -3, 'nulo':0}
dic_ultima_grafica = {"arriba": contador_grafica_arriba, "abajo": contador_grafica_abajo}

numero_anterior= 0
cid, cid2 = "", ""
estado_sincro = "desincronizado"


def switch_sincro(event):
    global canvas1, canvas2, ultima_grafica_seleccionada, cid, estado_sincro
    global ultima_grafica_seleccionada, Button_num_grafica_arriba, Button_num_grafica_abajo, cid, cid2
    print("el estado sincro cuando se quiere switchear es:", estado_sincro)
    if estado_sincro == "sincronizado_arriba" :
        print("inicié esto arriba")
        canvas1.mpl_disconnect(cid)
        canvas2.mpl_disconnect(cid2)
        estado_sincro = "desincronizado"
        print("intermedio arriba")
        cid = canvas2.mpl_connect('motion_notify_event', sincronizar_grafica_principal)
        cid2 = canvas1.mpl_connect('motion_notify_event', switch_sincro)
        Button_num_grafica_abajo.invoke()
        estado_sincro = "sincronizado_abajo"
        print("acabé esto arriba")
    elif estado_sincro == "sincronizado_abajo":
        print("inicié esto abajo")
        canvas2.mpl_disconnect(cid)
        canvas1.mpl_disconnect(cid2)
        estado_sincro = "desincronizado"
        print("intermedio abajo")
        cid = canvas1.mpl_connect('motion_notify_event', sincronizar_grafica_principal)
        cid2 = canvas2.mpl_connect('motion_notify_event', switch_sincro)
        Button_num_grafica_arriba.invoke()
        estado_sincro = "sincronizado_arriba"
        print("acabé esto abajo")
    print("estoy cambiando la sincro")
    

def creador_sincronizacion():
    global boton_sincro
    global canvas1, canvas2, ultima_grafica_seleccionada, cid, estado_sincro, cid2

    if estado_sincro == "desincronizado":
        #colorear boton 
        boton_sincro.configure(fg_color = ["#58D68D", "#1D8348"], hover_color= ["#27AE60", "#196F3D"])
        if ultima_grafica_seleccionada == "arriba":
            estado_sincro = "sincronizado_arriba"
        else:
            estado_sincro = "sincronizado_abajo"

        if ultima_grafica_seleccionada == "arriba":
            cid = canvas1.mpl_connect('motion_notify_event', sincronizar_grafica_principal)
            cid2 = canvas2.mpl_connect('motion_notify_event', switch_sincro)
        else:
            cid = canvas2.mpl_connect('motion_notify_event', sincronizar_grafica_principal)
            cid2 = canvas1.mpl_connect('motion_notify_event', switch_sincro)
  
    else:
        boton_sincro.configure(fg_color = ["#003785", "#0a0a0a"], hover_color= ["#001448", "#323a53"])
        if estado_sincro == "sincronizado_arriba":
            canvas1.mpl_disconnect(cid)
            canvas2.mpl_disconnect(cid2)
        elif estado_sincro == "sincronizado_abajo":
            canvas2.mpl_disconnect(cid)
            canvas1.mpl_disconnect(cid2)
        estado_sincro = "desincronizado"
    print("cambia a ", estado_sincro)

def sincronizar_grafica_principal(event):
    global fig1, fig2, ax1, ax2, ultima_grafica_seleccionada, canvas1, canvas2, Z
    global A3, A4, S1, S2, F1, F2, V1, V2, E, D1, D2, F, V_Transformado, segundos, WU, WD
    global numero_anterior, Button_num_grafica_arriba, Button_num_grafica_abajo

    if dic_ultima_grafica[ultima_grafica_seleccionada] != numero_anterior:
        A3, A4, S1, S2, F1, F2, V1, V2, E, D1, D2, F, V_Transformado, segundos, t, t, t, t, t, t, t, t, WU, WD, t, t, t, t, t, t = Creacion_Datos_Graficas(dic_ultima_grafica_magnitud[ultima_grafica_seleccionada],  dic_ultima_grafica[ultima_grafica_seleccionada], "original", "SI")
    else:
        pass
    numero_anterior = dic_ultima_grafica[ultima_grafica_seleccionada]

    if ultima_grafica_seleccionada == "arriba":
        Button_num_grafica_abajo.configure(text=str(numero_anterior))
        dic_ultima_grafica["abajo"] = numero_anterior
    else:
        Button_num_grafica_arriba.configure(text=str(numero_anterior))
        dic_ultima_grafica["arriba"] = numero_anterior

    dic_magnitud_sincronizacion = {'aceleracion':[A3, A4], 'deformacion':[S1, S2], 'fuerza':[F1, F2], 'velocidad':[V1, V2], 'avged':[E, E], 'desplazamiento':[D1, D2], 'fuerzaxvelocidad':[F,V_Transformado], 'wu':[WU, WU], 'wd':[WD, WD]}
    dic_legenda = {'aceleracion':["A3", "A4"], 'deformacion':["S1", "S2"], 'fuerza':["F1", "F2"], 'velocidad':["V1", "V2"], 'avged':["E", "E"], 'desplazamiento':["D1", "D2"], 'fuerzaxvelocidad':["F", str(round(Z, 2))+"*V"], 'wu':['WU', 'WU'], 'wd':['WD', 'WD']}
    dic_unidades = {'aceleracion':[["ms", "g's"], ["ms", "g's"]], 'deformacion':[["ms", "ue"], ["ms", "ue"]], 'fuerza':[["ms", "kN"], ["ms", "kips"]], 'velocidad':[["ms", "m/s"], ["ms", "ft/s"]], 'avged':[["ms", "J"], ["ms", "ft-lbs"]],
                    'desplazamiento':[["ms", "mm"],["ms", "in"]], 'fuerzaxvelocidad':[["ms", ""], ["ms", ""]], 'wu':[['ms', 'kN'], ['ms', 'kips']], 'wd':[['ms', 'kN'], ['ms', 'kip']]}
    #print("estamos en el bucle", ultima_grafica_seleccionada, dic_ultima_grafica_magnitud[dic_inverso[ultima_grafica_seleccionada]], dic_ultima_grafica_magnitud[ultima_grafica_seleccionada])

    if ultima_grafica_seleccionada == "arriba":
        try:
            fig2.clear()
            ax2 = fig2.add_subplot(111)
            t, = ax2.plot(segundos, dic_magnitud_sincronizacion[dic_ultima_grafica_magnitud[dic_inverso["arriba"]]][0], label=dic_legenda[dic_ultima_grafica_magnitud[dic_inverso["arriba"]]][0])
            t2, = ax2.plot(segundos, dic_magnitud_sincronizacion[dic_ultima_grafica_magnitud[dic_inverso["arriba"]]][1], label=dic_legenda[dic_ultima_grafica_magnitud[dic_inverso["arriba"]]][1] )
            ax2.set_xlim(ax1.get_xlim())
            print(dic_ultima_grafica_magnitud[dic_inverso["arriba"]], dic_ultima_grafica_magnitud[dic_inverso["arriba"]])
            ax2.set_xlabel(dic_unidades[dic_ultima_grafica_magnitud[dic_inverso["arriba"]]][dic_metrico[valor_actual_sistema_metrico]][0])
            ax2.set_ylabel(dic_unidades[dic_ultima_grafica_magnitud[dic_inverso["arriba"]]][dic_metrico[valor_actual_sistema_metrico]][1])
            canvas2.draw()
        except Exception as e:
            print(e, 50)

    elif ultima_grafica_seleccionada == "abajo":
        try:
            fig1.clear()
            ax1 = fig1.add_subplot(111)
            t, = ax1.plot(segundos, dic_magnitud_sincronizacion[dic_ultima_grafica_magnitud[dic_inverso["abajo"]]][0], label=dic_legenda[dic_ultima_grafica_magnitud[dic_inverso["abajo"]]][0])
            t2, = ax1.plot(segundos, dic_magnitud_sincronizacion[dic_ultima_grafica_magnitud[dic_inverso["abajo"]]][1], label=dic_legenda[dic_ultima_grafica_magnitud[dic_inverso["abajo"]]][1])
            ax1.set_xlim(ax2.get_xlim())
            print(dic_ultima_grafica_magnitud[dic_inverso["abajo"]], dic_ultima_grafica_magnitud[dic_inverso["abajo"]])
            ax1.set_xlabel(dic_unidades[dic_ultima_grafica_magnitud[dic_inverso["abajo"]]][dic_metrico[valor_actual_sistema_metrico]][0])
            ax1.set_ylabel(dic_unidades[dic_ultima_grafica_magnitud[dic_inverso["abajo"]]][dic_metrico[valor_actual_sistema_metrico]][1])
            canvas1.draw()
        except Exception as e:
            print(e, 51)
    

def eliminar_grafica():
    global ultima_grafica_seleccionada, matriz_data_archivos, Button_Num_Grafica, ruta_data_inicial, orden_sensores
    #respuesta = MessageBox.askyesno(message="Se eliminará una gráfica, ¿Desea continuar?", title="Alerta")
    respuesta = True
    if respuesta == True:
        matriz_relacion_num = [i for i in range(1,len(matriz_data_archivos))]
        matriz_data_archivos.pop(dic_ultima_grafica[ultima_grafica_seleccionada])
        matriz_relacion_num2 = matriz_relacion_num[:]
        
        matriz_relacion_num2.pop(dic_ultima_grafica[ultima_grafica_seleccionada]-1)
        matriz_relacion_num.pop(dic_ultima_grafica[ultima_grafica_seleccionada]-1)
        for i in range(len(matriz_relacion_num)):
            if i >= dic_ultima_grafica[ultima_grafica_seleccionada]-1:
                matriz_relacion_num2[i]=matriz_relacion_num2[i]-1
            
        with open(ruta_data_inicial, "w") as file:
            file.write(str(matriz_data_archivos[0]) + "\n")
            
            for index, num in enumerate(matriz_relacion_num):
                print(num)
                lines = []
                lines.append('INICIO_ARCHIVO\nARCHIVO:' + str(index + 1) + "\n" + str(orden_sensores[-1]))
                
                for fila in matriz_data_archivos[index + 1]:
                    lines.append(fila)
                
                lines.append('FIN_ARCHIVO\n')
                
                file.write('\n'.join(lines))

        cambiar_grafica("nulo")
    else:
        pass

def cambiar_grafica(direccion):
    global matriz_data_archivos, estado_continuidad
    global ultima_grafica_seleccionada
    global ultima_magnitud_arriba, ultima_magnitud_abajo
    global numero_grafica_antiguo_arriba, numero_grafica_antiguo_abajo
    print(dic_direccion[direccion])
    print(dic_ultima_grafica[ultima_grafica_seleccionada])
    dic_ultima_grafica[ultima_grafica_seleccionada] += dic_direccion[direccion]
    print(dic_ultima_grafica[ultima_grafica_seleccionada])
    if dic_ultima_grafica[ultima_grafica_seleccionada] >= len(matriz_data_archivos):
        dic_ultima_grafica[ultima_grafica_seleccionada] = len(matriz_data_archivos)-1
        estado_continuidad = "tiempo_real"
    elif dic_ultima_grafica[ultima_grafica_seleccionada] <= 1:
        dic_ultima_grafica[ultima_grafica_seleccionada] = 1
        estado_continuidad = "especifico"
    else:
        estado_continuidad = "especifico"
    
    Creacion_Grafica(ultima_grafica_seleccionada, dic_ultima_grafica_magnitud[ultima_grafica_seleccionada], dic_ultima_grafica[ultima_grafica_seleccionada], "original", "SI", "NO")
    print("en cambiar gráfica el num de gráfica es: ", dic_ultima_grafica[ultima_grafica_seleccionada])
    
    if ultima_grafica_seleccionada == "arriba":
        numero_grafica_antiguo_arriba = dic_ultima_grafica["arriba"]
    else:
        numero_grafica_antiguo_abajo = dic_ultima_grafica["abajo"]
    
    if direccion == 'nulo':
        if ultima_grafica_seleccionada == 'arriba':
            Creacion_Grafica('abajo', dic_ultima_grafica_magnitud['abajo'], dic_ultima_grafica['abajo'], "original", "SI", "NO")
        else:
            Creacion_Grafica('arriba', dic_ultima_grafica_magnitud['arriba'], dic_ultima_grafica['arriba'], "original", "SI", "NO")
    
    
def cambiar_grafica_exacto(numero, pos="ninguna"):
    global matriz_data_archivos, ultima_grafica_seleccionada, ultima_magnitud_arriba, ultima_magnitud_abajo
    global Entry_num_grafica_exacto_abajo, Entry_num_grafica_exacto_arriba

    dic_entry_num_grafica = {"arriba":Entry_num_grafica_exacto_arriba, "abajo":Entry_num_grafica_exacto_abajo}

    if numero == "ultimo":
        dic_ultima_grafica[ultima_grafica_seleccionada] = len(matriz_data_archivos)-1
        Creacion_Grafica(ultima_grafica_seleccionada, dic_ultima_grafica_magnitud[ultima_grafica_seleccionada], dic_ultima_grafica[ultima_grafica_seleccionada], "original", "SI", "NO")    
    elif numero == "primero":
        dic_ultima_grafica[ultima_grafica_seleccionada] = 1
        Creacion_Grafica(ultima_grafica_seleccionada, dic_ultima_grafica_magnitud[ultima_grafica_seleccionada], dic_ultima_grafica[ultima_grafica_seleccionada], "original", "SI", "NO")  
    else:
        try:
            if int(numero) > 0 and int(numero) < len(matriz_data_archivos) and pos != "ninguna":
                dic_ultima_grafica[ultima_grafica_seleccionada] = int(numero)
                Creacion_Grafica(ultima_grafica_seleccionada, dic_ultima_grafica_magnitud[ultima_grafica_seleccionada], dic_ultima_grafica[ultima_grafica_seleccionada], "original", "SI", "NO")
                dic_entry_num_grafica[pos].delete(0, END)
        except Exception as e:
            print(e, 13)

botones_barra_lateral = ['DEL','>','<','>>','<<', 'SYNC', 'FIRST', 'LAST', 'EXPORT']

for i in range(len(botones_barra_lateral)+1):
    container2_3.grid_rowconfigure(i, weight=1)

ctk.CTkButton(container2_3, text=botones_barra_lateral[0], font=font_barra_derecha, command=lambda: eliminar_grafica()).grid(row=0,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5,0)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[1], font=font_barra_derecha, command=lambda: cambiar_grafica("derecha")).grid(row=1,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5,0)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[2], font=font_barra_derecha, command=lambda: cambiar_grafica("izquierda")).grid(row=2,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5,0)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[3], font=font_barra_derecha, command=lambda: cambiar_grafica("derecha+")).grid(row=3,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5,0)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[4], font=font_barra_derecha, command=lambda: cambiar_grafica("izquierda+")).grid(row=4,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5)) 
boton_sincro = ctk.CTkButton(container2_3, text=botones_barra_lateral[5], font=font_barra_derecha, command=lambda: [creador_sincronizacion()])
boton_sincro.grid(row=5,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[6], font=font_barra_derecha, command=lambda: [cambiar_grafica_exacto("primero")]).grid(row=6,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[7], font=font_barra_derecha, command=lambda: [cambiar_grafica_exacto("ultimo")]).grid(row=7,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[8], font=font_barra_derecha, command=lambda: [Seleccionar_ruta_guardado_pdf() ]).grid(row=8,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5)) 


#----------------------------------------------------
# Frame de la derecha 

def preparaciones_exportar(label_cantidad_golpes, label_inicio, label_final):
    global matriz_data_archivos
    # este "," no debe ser reemplazado a ";" debido a que es para identificar las profundidades
    longitudes = matriz_data_archivos[0][12:].split(",")
    print(longitudes)
    label_cantidad_golpes.configure(text='Number of Impacts:'+str(len(matriz_data_archivos)-1))
    label_inicio.configure(text='Initial Depth:'+str(longitudes[0]))
    label_final.configure(text='Final Depth:'+str(longitudes[1]))

#--------------------FRAME2------------------------------------------------------------

container5 = ctk.CTkFrame((Collect_Wire))
container5.grid(row=0, column=0, sticky='nsew')
container5.grid_rowconfigure(0, weight=1)
container5.grid_rowconfigure(1, weight=10)
container5.grid_rowconfigure(2, weight=1)
container5.grid_rowconfigure(3, weight=10)
container5.grid_columnconfigure(0, weight=1)
container5.grid_columnconfigure(1, weight=1)
container5.grid_columnconfigure(2, weight=1)


puertos=[""]
estado_puerto = False

def detectar_puertos():

    global socket_tcp, estado_puerto
    host = "192.168.0.10"
    port = 65432
    
    if estado_puerto == False:
        try:
            socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_tcp.connect((host, port))
            estado_puerto = True
            MessageBox.showinfo(title="Conectado", message="The connection was successful")
        except:
            MessageBox.showerror("Error", "Error")
        print("Conectado al puerto")
        print(host)
    else:
        print("el socket ya existe")
    verificacion_orden_sensores()
    Generar_Tabla_Sensores()

def detener_conexion_puerto():

    global socket_tcp, estado_puerto
    
    try:
        estado_puerto = False
        socket_tcp.close()
    except Exception as e:
        print(e, 14)

bandera = True

def detener_loop():
    global bandera
    bandera = False

conexion =""

def verificacion_orden_sensores():
    global bandera
    global conexion
    global orden_sensores
    global socket_tcp
    
    # socket_tcp.listen()
    # Convertimos str a bytes
    MESSAGE = "S"
    socket_tcp.send(MESSAGE.encode('utf-8'))
    BUFFER_SIZE = 1
    #data = socket_tcp.recv(BUFFER_SIZE)
    
    print("S")
    bandera = True
    #time.sleep(0.2)
    ordenes = ""
    while bandera == True:
        linea = socket_tcp.recv(1).decode()
        print(type(linea))
        print(linea)
        if linea == " ":
            orden_sensores.append(ordenes)
            print("ORDENES RECIBIDOS")
            break
        if linea != "":
            ordenes = ordenes + linea
            



dic_sensores = {'1':'Acceleration sensor 1', '2':'Acceleration sensor 2', '3':'Strain gauge SPT 1', '4':'Strain Gauge SPT 2', '5':'Strain Gauge DPT 1', '6':'Strain Gauge DPT 2', '0':'No encontrado'}
    
container5_1 = ctk.CTkFrame(container5)

container5_1.grid(row=1, column=0, sticky='nsew', padx=20, pady=(20,10))
container5_1.grid_rowconfigure(0, weight=1)
container5_1.grid_rowconfigure(1, weight=8)
container5_1.grid_columnconfigure(0, weight=1)

container5_1_0 = ctk.CTkFrame(container5)

container5_1_0.grid(row=0, column=0, sticky='nsew', padx=20, pady=(10))
container5_1_0.grid_rowconfigure(0, weight=1)
container5_1_0.grid_rowconfigure(1, weight=1)
container5_1_0.grid_rowconfigure(2, weight=1)
container5_1_0.grid_columnconfigure(0, weight=1)

Label_titulo_1 = ctk.CTkLabel(container5_1_0, text='SENSOR SELECTION', font=fontSUBcoll)
Label_titulo_1.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

container5_1_1 = ctk.CTkFrame(container5_1)
container5_1_1.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10,0))
container5_1_1.grid_rowconfigure(0, weight=1)
container5_1_1.grid_columnconfigure(0, weight=1)
container5_1_1.grid_columnconfigure(1, weight=1)


container5_1_2 = ctk.CTkFrame(container5_1)
container5_1_2.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
container5_1_2.grid_rowconfigure(0, weight=1)
container5_1_2.grid_rowconfigure(1, weight=1)
container5_1_2.grid_rowconfigure(2, weight=1)
container5_1_2.grid_rowconfigure(3, weight=1)
container5_1_2.grid_columnconfigure(0, weight=1)
container5_1_2.grid_columnconfigure(1, weight=3)

def Generar_Tabla_Sensores():
    global orden_sensores
    time.sleep(0.3)
    detener_loop()
    time.sleep(0.3)
    try:
        print(orden_sensores[-1])
        orden = str(orden_sensores[-1]).replace(" ","").split("|")

        try:
            pass
            # Label_sensor1_data.configure(text=dic_sensores[orden[0]], font=fontTEXTcoll)
            # Label_sensor2_data.configure(text=dic_sensores[orden[1]], font=fontTEXTcoll)
            # Label_sensor3_data.configure(text=dic_sensores[orden[2]], font=fontTEXTcoll)
            # Label_sensor4_data.configure(text=dic_sensores[orden[3]], font=fontTEXTcoll)
        except Exception as e:
            print(e, 15)
    except Exception as e:
        print(e, 16)

Label_sensor1 = ctk.CTkLabel(container5_1_2, text="Sensor 1:", font=fontTEXTcoll)
Label_sensor1.grid(row=0, column=0, sticky='nsew', padx=(20,0), pady=(20,10))
Label_sensor2 = ctk.CTkLabel(container5_1_2, text="Sensor 2:", font=fontTEXTcoll)
Label_sensor2.grid(row=1, column=0, sticky='nsew', padx=(20,0), pady=(10,10))
Label_sensor3 = ctk.CTkLabel(container5_1_2, text="Sensor 3:", font=fontTEXTcoll)
Label_sensor3.grid(row=2, column=0, sticky='nsew', padx=(20,0), pady=(10,10))
Label_sensor4 = ctk.CTkLabel(container5_1_2, text="Sensor 4:", font=fontTEXTcoll)
Label_sensor4.grid(row=3, column=0, sticky='nsew', padx=(20,0), pady=(10,20))

# Opciones para las listas desplegables
opciones = ["Not available", "Acc. PR - K11670", "Acc. PR - K13548", "Strain Gauge 1 - SPT", "Strain Gauge 2 - SPT", "Strain Gauge 1 - DPT", "Strain Gauge 2 - DPT"]
# Crear variables de control separadas para cada lista desplegable
var_sensor_1 = ctk.StringVar(value="Not available")
var_sensor_2 = ctk.StringVar(value="Not available")
var_sensor_3 = ctk.StringVar(value="Not available")
var_sensor_4 = ctk.StringVar(value="Not available")

# Crear listas desplegables con las variables de control adecuadas
combobox_sensor_1 = ctk.CTkOptionMenu(container5_1_2, values=opciones, variable=var_sensor_1)
combobox_sensor_1.grid(row=0, column=1, sticky='nsew', padx=(0, 20), pady=(20 if i == 0 else 10, 20))

combobox_sensor_2 = ctk.CTkOptionMenu(container5_1_2, values=opciones, variable=var_sensor_2)
combobox_sensor_2.grid(row=1, column=1, sticky='nsew', padx=(0, 20), pady=(20 if i == 0 else 10, 20))

combobox_sensor_3 = ctk.CTkOptionMenu(container5_1_2, values=opciones, variable=var_sensor_3)
combobox_sensor_3.grid(row=2, column=1, sticky='nsew', padx=(0, 20), pady=(20 if i == 0 else 10, 20))

combobox_sensor_4 = ctk.CTkOptionMenu(container5_1_2, values=opciones, variable=var_sensor_4)
combobox_sensor_4.grid(row=3, column=1, sticky='nsew', padx=(0, 20), pady=(20 if i == 0 else 10, 20))



ctk.CTkButton(container5_1_1, text="Connect to server", font=fontTEXTcoll, command=lambda: [detectar_puertos()]).grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
ctk.CTkButton(container5_1_1, text="Update sensor order", font=fontTEXTcoll,command=lambda: [verificacion_orden_sensores(), Generar_Tabla_Sensores()]).grid(row=0, column=1, sticky='nsew', padx=(0,5), pady=5)

container5_2 = ctk.CTkFrame(container5)
container5_2.grid(row= 1, column=1, sticky='nsew', padx=(10,20), pady=20)
container5_2.grid_rowconfigure(0, weight=1)
container5_2.grid_columnconfigure(0, weight=1)

container5_2_0 = ctk.CTkFrame(container5)
container5_2_0.grid(row=0, column=1, sticky='nsew', padx=(10,20), pady=(10))
container5_2_0.grid_rowconfigure(0, weight=1)
container5_2_0.grid_rowconfigure(1, weight=1)
container5_2_0.grid_rowconfigure(2, weight=1)
container5_2_0.grid_columnconfigure(0, weight=1)


Label_titulo_2 = ctk.CTkLabel(container5_2_0, text='ROD PARAMETERS', font=fontSUBcoll)
Label_titulo_2.grid(row=1, column=0, sticky='nsew', padx=10)

container5_2_2 = ctk.CTkFrame(container5_2)
container5_2_2.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

container5_2_2.grid_rowconfigure(0, weight=1)
container5_2_2.grid_rowconfigure(1, weight=1)
container5_2_2.grid_columnconfigure(0, weight=1)

container5_2_2_1 = ctk.CTkFrame(container5_2_2)
container5_2_2_1.grid(row=0, column=0, sticky='nsew', padx=(40), pady=(80,40))
container5_2_2_1.grid_rowconfigure(0, weight=1)
container5_2_2_1.grid_rowconfigure(1, weight=1)
container5_2_2_1.grid_rowconfigure(2, weight=1)
container5_2_2_1.grid_columnconfigure(0, weight=3)
container5_2_2_1.grid_columnconfigure(1, weight=2)
container5_2_2_1.grid_columnconfigure(2, weight=1)

container5_2_2_2 = ctk.CTkFrame(container5_2_2)
container5_2_2_2.grid(row=1, column=0, sticky='nsew', padx=(40), pady=(40,80))
container5_2_2_2.grid_rowconfigure(0, weight=1)
container5_2_2_2.grid_rowconfigure(1, weight=1)
container5_2_2_2.grid_rowconfigure(2, weight=1)
container5_2_2_2.grid_columnconfigure(0, weight=3)
container5_2_2_2.grid_columnconfigure(1, weight=2)
container5_2_2_2.grid_columnconfigure(2, weight=1)

Label_Area = ctk.CTkLabel(container5_2_2_1, text="Area", font=fontTEXTcoll, width=120).grid(row=1, column=0, sticky='nsew')
Entry_Area = ctk.CTkEntry(container5_2_2_1, font=fontTEXTcoll)
Entry_Area.grid(row=1, column=1, sticky='nsew')
Entry_Area.insert(0, "7.80595")
Label_Area_unidad = ctk.CTkLabel(container5_2_2_1, text="cm²", font=fontTEXTcoll)
Label_Area_unidad.grid(row=1, column=2, sticky='nsew', padx=(0,5))

Label_Modulo_Elasticidad = ctk.CTkLabel(container5_2_2_2, text="Elasticity \nModulus", font=fontTEXTcoll, width=120).grid(row=1, column=0, sticky='nsew')
Entry_modulo_elasticidad = ctk.CTkEntry(container5_2_2_2, font=fontTEXTcoll)
Entry_modulo_elasticidad.grid(row=1, column=1, sticky='nsew')
Entry_modulo_elasticidad.insert(0, "206843")
Label_Modulo_Elasticidad_unidad = ctk.CTkLabel(container5_2_2_2, text="MPa", font=fontTEXTcoll)
Label_Modulo_Elasticidad_unidad.grid(row=1, column=2, sticky='nsew', padx=(0,5))


container5_3 = ctk.CTkFrame(container5)
container5_3.grid(row=3, column=0, sticky='nsew', padx=20, pady=(20))
container5_3.grid_rowconfigure(0, weight=1)
container5_3.grid_columnconfigure(0, weight=1)

conteiner5_3_0 = ctk.CTkFrame(container5)
conteiner5_3_0.grid(row=2, column=0, sticky='nsew', padx=20, pady=(10))
conteiner5_3_0.grid_rowconfigure(0, weight=1)
conteiner5_3_0.grid_rowconfigure(1, weight=1)
conteiner5_3_0.grid_rowconfigure(2, weight=1)
conteiner5_3_0.grid_columnconfigure(0, weight=1)

Label_titulo_3 = ctk.CTkLabel(conteiner5_3_0, text='DEPTH', font=fontSUBcoll)
Label_titulo_3.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

container5_3_1 = ctk.CTkFrame(container5_3)
container5_3_1.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
container5_3_1.grid_rowconfigure(0, weight=2)
container5_3_1.grid_rowconfigure(1, weight=2)
container5_3_1.grid_rowconfigure(2, weight=1)
container5_3_1.grid_columnconfigure(0, weight=1)
container5_3_1.grid_columnconfigure(1, weight=1)

container5_3_1_1 = ctk.CTkFrame(container5_3_1)
container5_3_1_1.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=10, pady=(60))
container5_3_1_1.grid_rowconfigure(0, weight=1)
container5_3_1_1.grid_columnconfigure(0, weight=5)
container5_3_1_1.grid_columnconfigure(1, weight=2)
container5_3_1_1.grid_columnconfigure(2, weight=1)
container5_3_1_1.grid_columnconfigure(3, weight=2)

Label_titulo_4 = ctk.CTkLabel(container5_3_1_1, text="Range of \nDepths\n(m)", font=fontTEXTcoll)
Label_titulo_4.grid(row=0, column=0, sticky='nsew', padx=(10,0), pady=(30,20))

Entry_Profundidad_inicial = ctk.CTkEntry(container5_3_1_1, font=fontTEXTcoll, height=10)
Entry_Profundidad_inicial.grid(row=0, column=1, sticky='nsew', pady=(50,20))

ctk.CTkLabel(container5_3_1_1, text="-", font=fontTEXTcoll).grid(row=0, column=2, sticky='nsew', pady=(50,20))

Entry_Profundidad_final = ctk.CTkEntry(container5_3_1_1, font=fontTEXTcoll, height=10)
Entry_Profundidad_final.grid(row=0, column=3, sticky='nsew', padx=(0,10), pady=(50,20))

container5_3_1_2 = ctk.CTkFrame(container5_3_1)
container5_3_1_2.grid(row=1, column=0, sticky='nsew', padx=(10,5))
container5_3_1_2.grid_rowconfigure(0, weight=1)
container5_3_1_2.grid_columnconfigure(0, weight=3)
container5_3_1_2.grid_columnconfigure(1, weight=2)
container5_3_1_2.grid_columnconfigure(2, weight=1)

LabelLE = ctk.CTkLabel(container5_3_1_2, text="LE", font=fontTEXTcoll)
LabelLE.grid(row=0, column=0, sticky='nsew')
EntryLE = ctk.CTkEntry(container5_3_1_2, font=fontTEXTcoll)
EntryLE.insert(0, "0")
EntryLE.grid(row=0, column=1, sticky='nsew')
LabelLE_unidades = ctk.CTkLabel(container5_3_1_2, text="m", font=fontTEXTcoll)
LabelLE_unidades.grid(row=0, column=2, sticky='nsew')

container5_3_1_3 = ctk.CTkFrame(container5_3_1)
container5_3_1_3.grid(row=1, column=1, sticky='nsew', padx=(5,10))
container5_3_1_3.grid_rowconfigure(0, weight=1)
container5_3_1_3.grid_columnconfigure(0, weight=3)
container5_3_1_3.grid_columnconfigure(1, weight=2)
container5_3_1_3.grid_columnconfigure(2, weight=1)

LabelLR = ctk.CTkLabel(container5_3_1_3, text="LP", font=fontTEXTcoll)
LabelLR.grid(row=0, column=0, sticky='nsew')
EntryLR = ctk.CTkEntry(container5_3_1_3, font=fontTEXTcoll)
EntryLR.insert(0, "5")
EntryLR.grid(row=0, column=1, sticky='nsew')
LabelLR_unidades = ctk.CTkLabel(container5_3_1_3, text="m", font=fontTEXTcoll)
LabelLR_unidades.grid(row=0, column=2, sticky='nsew')

ctk.CTkButton(container5_3_1, text="Back", font=fontTEXTcoll, command=lambda: [detener_conexion_puerto(), raise_frame(Menup)]).grid(row=2, column=0, sticky='nsew', pady=(40,10))

container5_4 = ctk.CTkFrame(container5)
container5_4.grid(row=3, column=1, sticky='nsew', padx=(10,20), pady=20)
container5_4.grid_rowconfigure(0, weight=1)
container5_4.grid_columnconfigure(0, weight=1)

container5_4_0 = ctk.CTkFrame(container5)
container5_4_0.grid(row=2, column=1, sticky='nsew', padx=(10,20), pady=10)
container5_4_0.grid_rowconfigure(0, weight=1)
container5_4_0.grid_rowconfigure(1, weight=1)
container5_4_0.grid_rowconfigure(0, weight=1)
container5_4_0.grid_columnconfigure(0, weight=1)

ctk.CTkLabel(container5_4_0, text="HAMMER PARAMETERS", font = fontSUBcoll).grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

container5_4_1 = ctk.CTkFrame(container5_4)
container5_4_1.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
container5_4_1.grid_rowconfigure(0, weight=1)
container5_4_1.grid_columnconfigure(0, weight=1)

container5_4_1_1 = ctk.CTkFrame(container5_4_1)
container5_4_1_1.grid(row=0, column=0, sticky='nsew', padx=10, pady=(60,30))
container5_4_1_1.grid_rowconfigure(0, weight=1)
container5_4_1_1.grid_rowconfigure(1, weight=1)
container5_4_1_1.grid_rowconfigure(2, weight=1)
container5_4_1_1.grid_rowconfigure(3, weight=1)
container5_4_1_1.grid_columnconfigure(0, weight=2)
container5_4_1_1.grid_columnconfigure(1, weight=2)
container5_4_1_1.grid_columnconfigure(2, weight=1)
container5_4_1_1.grid_columnconfigure(3, weight=3)

Label_Masa = ctk.CTkLabel(container5_4_1_1, text="Mass", font=fontTEXTcoll).grid(row=1, column=0, sticky='nsew', pady=(0,10))
Entry_masa = ctk.CTkEntry(container5_4_1_1, font=fontTEXTcoll)
Entry_masa.grid(row=1, column=1, sticky='nsew', pady=(0,10))
Entry_masa.insert(0, "63.5")
Label_Masa_unidades = ctk.CTkLabel(container5_4_1_1, text='kg', font=fontTEXTcoll)
Label_Masa_unidades.grid(row=1, column=2, sticky='nsew', pady=(0,10))

Label_Altura = ctk.CTkLabel(container5_4_1_1, text="Height", font=fontTEXTcoll).grid(row=2, column=0, sticky='nsew', pady=(10,0))
Entry_altura = ctk.CTkEntry(container5_4_1_1, font=fontTEXTcoll)
Entry_altura.grid(row=2, column=1, sticky='nsew', pady=(10,0))
Entry_altura.insert(0, "0.76")
Label_Altura_unidades = ctk.CTkLabel(container5_4_1_1, text="m", font=fontTEXTcoll)
Label_Altura_unidades.grid(row=2, column=2, sticky='nsew', pady=(10,0))

Boton_calcular_energia = ctk.CTkButton(container5_4_1_1, text="Calculate Energy", font=fontTEXTcoll, command=lambda:calcular()).grid(row=1, column=3, rowspan=2, sticky='nsew', padx=10)

container5_4_1_2 = ctk.CTkFrame(container5_4_1)
container5_4_1_2.grid(row=1, column=0, sticky='nsew', padx=10, pady=(30,60))
container5_4_1_2.grid_rowconfigure(0, weight=1)
container5_4_1_2.grid_rowconfigure(1, weight=1)
container5_4_1_2.grid_rowconfigure(2, weight=1)
container5_4_1_2.grid_columnconfigure(0, weight=1)
container5_4_1_2.grid_columnconfigure(1, weight=1)
container5_4_1_2.grid_columnconfigure(2, weight=1)

Label_Energia = ctk.CTkLabel(container5_4_1_2, text="Energy", font=fontTEXTcoll).grid(row=1, column=0, sticky='nsew', padx=(10,0), pady=10)
Label_Energia_valor = ctk.CTkLabel(container5_4_1_2, text="473", font=fontTEXTcoll)
Label_Energia_valor.grid(row=1, column=1, sticky='nsew', pady=10)
Label_Energia_unidades = ctk.CTkLabel(container5_4_1_2, text="J", font=fontTEXTcoll)
Label_Energia_unidades.grid(row=1, column=2, sticky='nsew', padx=(0,10), pady=10)

def calcular():
    global Entry_masa, Entry_altura, producto, Label_Energia_valor
    producto = int(float(Entry_masa.get())* float(Entry_altura.get())*9.81)
    Label_Energia_valor.configure(text=str(producto))

container5_5 = ctk.CTkFrame(container5)
container5_5.grid(row=1, column=2, rowspan=3, sticky='nsew', padx=(10,20), pady=20)
container5_5.grid_rowconfigure(0, weight=1)
container5_5.grid_columnconfigure(0, weight=1)

container5_5_0 = ctk.CTkFrame(container5)
container5_5_0.grid(row=0, column=2, sticky='nsew', padx=(10,20), pady=10)
container5_5_0.grid_rowconfigure(0, weight=1)
container5_5_0.grid_rowconfigure(1, weight=1)
container5_5_0.grid_rowconfigure(2, weight=1)
container5_5_0.grid_columnconfigure(0, weight=1)

Label_titulo_5 = ctk.CTkLabel(container5_5_0, text="SAMPLING PARAMETERS", font=fontSUBcoll).grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

container5_5_1 = ctk.CTkFrame(container5_5)
container5_5_1.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

container5_5_1.grid_rowconfigure(0, weight=1)
container5_5_1.grid_rowconfigure(1, weight=4)
container5_5_1.grid_rowconfigure(2, weight=4)
container5_5_1.grid_columnconfigure(0, weight=1)
container5_5_1.grid_columnconfigure(1, weight=1)

ctk.CTkLabel(container5_5_1,height=60, text='Sampling Rate', font=fontTEXTcoll).grid(row=0, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)

container5_5_1_1 = ctk.CTkFrame(container5_5_1)
container5_5_1_1.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5)
container5_5_1_1.grid_rowconfigure(0, weight=2)
container5_5_1_1.grid_rowconfigure(1, weight=2)
container5_5_1_1.grid_columnconfigure(0, weight=1)
container5_5_1_1.grid_columnconfigure(1, weight=1)

def mod_frecuencia_muestreo(n):
    global frecuencia_muestreo
    frecuencia_muestreo.append(n)

def colorear_botones(n):
    dic_colorear_botones = {50:B_50, 100:B_100, 150:B_150, 200:B_200}
    for boton in [B_50, B_100, B_150, B_200]:
        if boton == dic_colorear_botones[n]:
            boton.configure(fg_color = ["#27AE60", "#27AE60"], hover_color= ["#27AE60", "#27AE60"])
        else:
            boton.configure(fg_color = ["#091d36", "#091d36"], hover_color= ["#58D68D", "#58D68D"])
ancho_boton = 80
B_50 = ctk.CTkButton(container5_5_1_1,height=ancho_boton, text="50 kHz", command=lambda:[mod_frecuencia_muestreo(50), colorear_botones(50)], font=fontTEXTcoll)
B_50.grid(row=0, column=0, padx=(20,10), pady=(10,5), sticky='nsew')
B_100 = ctk.CTkButton(container5_5_1_1,height=ancho_boton, text="100 kHz", command=lambda:[mod_frecuencia_muestreo(100), colorear_botones(100)], font=fontTEXTcoll)
B_100.grid(row=0, column=1, padx=(10,20), pady=(10,5), sticky='nsew')
B_150 = ctk.CTkButton(container5_5_1_1,height=ancho_boton, text="150 kHz", command=lambda:[mod_frecuencia_muestreo(150), colorear_botones(150)], font=fontTEXTcoll)
B_150.grid(row=1, column=0, padx=(20,10), pady=(5,10), sticky='nsew')
B_200 = ctk.CTkButton(container5_5_1_1,height=ancho_boton, text="200 kHz", command=lambda:[mod_frecuencia_muestreo(200), colorear_botones(200)], font=fontTEXTcoll)
B_200.grid(row=1, column=1, padx=(10,20), pady=(5,10), sticky='nsew')

B_50.invoke()

container5_5_1_2 = ctk.CTkFrame(container5_5_1)
container5_5_1_2.grid(row=2, column=0, columnspan=2, sticky='nsew', padx =10, pady=10)

container5_5_1_2.grid_rowconfigure(0, weight=4)
container5_5_1_2.grid_rowconfigure(1, weight=4)
container5_5_1_2.grid_rowconfigure(2, weight=1)
container5_5_1_2.grid_rowconfigure(3, weight=1)
container5_5_1_2.grid_rowconfigure(4, weight=2)
container5_5_1_2.grid_rowconfigure(5, weight=2)
container5_5_1_2.grid_columnconfigure(0, weight=3)
container5_5_1_2.grid_columnconfigure(1, weight=2)
container5_5_1_2.grid_columnconfigure(2, weight=1)

ctk.CTkLabel(container5_5_1_2, height=60,text="Sampling \ntime:", font=fontTEXTcoll).grid(row=0, column=0, sticky='nsew', pady=(10,5))
Entry_tiempo_muestreo = ctk.CTkEntry(container5_5_1_2, font=fontTEXTcoll)
Entry_tiempo_muestreo.grid(row=0, column=1, sticky='nsew', pady=(10,5))
Entry_tiempo_muestreo.insert(0, "100")
ctk.CTkLabel(container5_5_1_2, text='ms', font=fontTEXTcoll).grid(row=0, column=2, sticky='nsew', pady=(10,5), padx=(0,10))

ctk.CTkLabel(container5_5_1_2,height=60, text="Delay \ntime", font=fontTEXTcoll).grid(row=1, column=0, sticky='nsew', pady=(20,20))
Entry_tiempo_Retardo = ctk.CTkEntry(container5_5_1_2, font=fontTEXTcoll)
Entry_tiempo_Retardo.grid(row=1, column=1, sticky='nsew', pady=(20,20))
Entry_tiempo_Retardo.insert(0, "10")
ctk.CTkLabel(container5_5_1_2, text='ms', font=fontTEXTcoll).grid(row=1, column=2, sticky='nsew', pady=(20,20), padx=(0,10))

container5_5_1_2_unidades = ctk.CTkFrame(container5_5_1_2)
container5_5_1_2_unidades.grid(row=2, column=0, columnspan=3, sticky='nsew', padx=20, pady=20)
container5_5_1_2_unidades.grid_rowconfigure(0, weight=1)
container5_5_1_2_unidades.grid_rowconfigure(1, weight=1)
container5_5_1_2_unidades.grid_columnconfigure(0, weight=1)
container5_5_1_2_unidades.grid_columnconfigure(1, weight=1)

def boton_cambio_unidades_collectwire(valor):
    print(valor)
    global valor_actual_sistema_metrico, unidad_original, Button_EN, Button_SI
    dic_colorear_botones_unidades = {'EN':Button_EN, 'SI':Button_SI}
    for boton in [Button_EN, Button_SI]:
        if boton == dic_colorear_botones_unidades[valor]:
            print(691)
            boton.configure(fg_color = ["#27AE60", "#27AE60"], hover_color= ["#27AE60", "#27AE60"])
            valor_actual_sistema_metrico = valor
            unidad_original = valor
            Cambiar_Unidades_CollectWire()
        else:
            print(892)
            boton.configure(fg_color = ["#091d36", "#091d36"], hover_color= ["#58D68D", "#58D68D"])

def Cambiar_Unidades_CollectWire():
    global valor_actual_sistema_metrico
    global Label_titulo_4, LabelLE_unidades, EntryLE, EntryLR, LabelLR_unidades, Label_Modulo_Elasticidad_unidad
    global Entry_modulo_elasticidad, Entry_Area, Label_Area_unidad, Label_Modulo_Elasticidad_unidad, Entry_masa, Label_Masa_unidades, Entry_altura, Label_Altura_unidades, Label_Energia_valor, Label_Energia_unidades 
    dic_unidades_collectwire = [["Range of \nDepths\n(m)", "Range of \nDepths\n(ft)"], ["m", "ft"], ["cm²", "in²"], ["Mpa", "ksi"], ["kg", "kg"], ["m", "ft"], ["J", "kip"]]
    dic_valores_unidades_collectwire = [["0", "0"], ["5", ""], ["7.80595", ""], ["206843", ""], ["63.5", ""], ["0.76", ""], ["473", "473"]]
    if valor_actual_sistema_metrico == "SI":
        num =  0
    else:
        num = 1
    #cambiando labels
    Label_titulo_4.configure(text=dic_unidades_collectwire[0][num])
    LabelLE_unidades.configure(text=dic_unidades_collectwire[1][num])
    LabelLR_unidades.configure(text=dic_unidades_collectwire[1][num])
    Label_Area_unidad.configure(text=dic_unidades_collectwire[2][num])
    Label_Modulo_Elasticidad_unidad.configure(text=dic_unidades_collectwire[3][num])
    Label_Masa_unidades.configure(text=dic_unidades_collectwire[4][num])
    Label_Altura_unidades.configure(text=dic_unidades_collectwire[5][num])
    Label_Energia_unidades.configure(text=dic_unidades_collectwire[6][num])
    Label_Energia_valor.configure(text=dic_valores_unidades_collectwire[6][num])         

    
    #cambiando Entrys
    """valores_anteriores = [EntryLE.cget("text"), EntryLR.cget("text"), Entry_Area.cget("text"), Entry_modulo_elasticidad.cget("text"), Entry_masa.cget("text"), Entry_altura.cget("text")]
    EntryLE.delete(0, END)
    EntryLR.delete(0, END)
    Entry_Area.delete(0, END)
    Entry_modulo_elasticidad.delete(0, END)
    Entry_masa.delete(0, END)
    Entry_altura.delete(0, END)
    
    EntryLE.insert(0, valores_anteriores[0])
    EntryLR.insert(0, valores_anteriores[1])
    Entry_Area.insert(0, valores_anteriores[2])
    Entry_modulo_elasticidad.insert(0, valores_anteriores[3])
    Entry_masa.insert(0, valores_anteriores[4])
    Entry_altura.insert(0, valores_anteriores[5])"""
    




ctk.CTkLabel(container5_5_1_2_unidades, text='System of Units', font=fontTEXTcoll).grid(row=0, column=0, columnspan=2, sticky='nsew', pady=10, padx=10)

Button_SI = ctk.CTkButton(container5_5_1_2_unidades, text='SI', font=fontTEXTcoll, command=lambda:boton_cambio_unidades_collectwire('SI'))
Button_SI.grid(row=1, column=0, sticky='nsew', pady=10, padx=10)
Button_EN = ctk.CTkButton(container5_5_1_2_unidades, text='EN', font=fontTEXTcoll, command=lambda:boton_cambio_unidades_collectwire('EN'))
Button_EN.grid(row=1, column=1, sticky='nsew', pady=10, padx=[0,10])
Button_SI.invoke()

ctk.CTkButton(container5_5_1_2, text= "Select save path", font=fontTEXTcoll, command=lambda: [escoger_ruta_guardado()]).grid(row=3, column=1, columnspan=2, sticky='nsew', padx=20, pady=(20,10))

entry_ruta_guardado = ctk.CTkEntry(container5_5_1_2, font=fontTEXTcoll)
entry_ruta_guardado.grid(row=4, column=1, columnspan=2, sticky='nsew', padx=20, pady=(10))



ctk.CTkButton(container5_5_1_2, text= "Next", font=fontTEXTcoll, command=lambda: [mostrar_alertas()]).grid(row=5, column=1, columnspan=2, sticky='nsew', padx=20, pady=(10,200))

def escoger_ruta_guardado():
    global ruta_guardado
    ruta_guardado = filedialog.askdirectory(initialdir = "/", title = "Selecciona una carpeta")
    ruta_guardado += "/"
    entry_ruta_guardado.insert(0, ruta_guardado)


# Container creado solo para la vista Collect Wire

def mostrar_alertas():
    global orden_sensores
    global frecuencia_muestreo, ruta_guardado, estado_continuidad
    global socket_tcp
    try:
        orden = str(orden_sensores[-1]).replace(" ","").split("|")
    except Exception as e:
        print(e, 17)
    if int(Entry_tiempo_muestreo.get()) <50 or int(Entry_tiempo_muestreo.get()) >300:
        MessageBox.showerror("Error", "El tiempo de muestreo tiene que estar entre 50 y 300")
        pass
    elif int(Entry_tiempo_Retardo.get()) <10 or int(Entry_tiempo_Retardo.get()) >50:
        MessageBox.showerror("Error", "El tiempo de retardo tiene que estar entre 10 y 50")
        pass
    elif frecuencia_muestreo[-1] == []:
        MessageBox.showerror("Error", "Escoja una frecuencia")
        pass
    elif len(orden_sensores) == 0:
        MessageBox.showerror("Error", "Seleccione un puerto")
    
    elif not(("1" in orden or "2" in orden) and ("3" in orden or "4" in orden or "5" in orden or "6" in orden)):
        MessageBox.showerror("Error", "Se necesitan al menos un sensor de aceleración y un sensor de DPT o SPT")
    
    elif float(Entry_Profundidad_final.get()) < float(Entry_Profundidad_inicial.get()):
        MessageBox.showerror("Error", "La profundidad inicial es mayor que la final")
    elif ruta_guardado == "":
        MessageBox.showerror("Selecciona una carpeta para guardar el .ct")
    else:

        orden_1 = combobox_sensor_1.get()
        orden_2 = combobox_sensor_2.get()
        orden_3 = combobox_sensor_3.get()
        orden_4 = combobox_sensor_4.get()
        orden_entrada = [orden_1, orden_2, orden_3, orden_4]
        opciones = ["Not available", "Acc. PR - K11670", "Acc. PR - K13548", "Strain Gauge 1 - SPT", "Strain Gauge 2 - SPT", "Strain Gauge 1 - DPT", "Strain Gauge 2 - DPT"]

        posible_orden = []
        print(orden_entrada)
        for opcion_sensor in orden_entrada:
            for index, orden_enviada in enumerate(opciones):
                if orden_enviada == opcion_sensor:
                    posible_orden.append(index)
                    break
        cadena = ''
        for crear_orden in posible_orden:
            cadena = cadena + str(crear_orden) + '|'
        orden_sensores = [cadena]
        print("adsfasddfdasfsfaddafasdf")
        print(orden_sensores)
        print(type(orden_sensores))
        
        socket_tcp.send("P".encode('utf-8'))
        time.sleep(0.2)
        valor = str(str(frecuencia_muestreo[-1])+"|"+str(Entry_tiempo_muestreo.get())+"|"+str(Entry_tiempo_Retardo.get())+"|")
        print(valor)
        socket_tcp.send(valor.encode('utf-8'))
        time.sleep(0.1)
        print("enviando datos de frecuencia")
        limpiar_review()
        raise_frame(Review)
        estado_continuidad = "tiempo_real"
        crear_columna_muestreo()

def limpiar_review():
    global t1, t2, t3, t4, fig1, fig2, canvas1, canvas2
    modificar_datos_segundo_frame('arriba', "", "", "", "", "", "", "", "", "", "", "", "", "")
    modificar_datos_segundo_frame('abajo', "", "", "", "", "", "", "", "", "", "", "", "", "")
    # arriba
    fig1.clear()
    ax1 = fig1.add_subplot(111)
    t1, = ax1.plot(np.arange(1, 8001), np.zeros(8000))
    t2, = ax1.plot(np.arange(1, 8001), np.zeros(8000))
    canvas1.draw()
    # abajo
    fig2.clear()
    ax2 = fig2.add_subplot(111)
    t3, = ax2.plot(np.arange(1, 8001), np.zeros(8000))
    t4, = ax2.plot(np.arange(1, 8001), np.zeros(8000))
    canvas2.draw()
    #clear_container('arriba')
    #clear_container('abajo')
    

def eliminar_columna_muestreo():
    global tipo_review
    global pile_area, pile_area_label, EM_valor_original, EM_label, ET_valor_original, ET_label, Button_num_grafica_arriba, Button_num_grafica_abajo, segemented_button, segemented_button2
    global segmented_button_callback1, segmented_button_callback2
    dic_ultima_grafica["abajo"] = 1
    dic_ultima_grafica["arriba"] = 1
    Button_num_grafica_arriba.configure(text=str(dic_ultima_grafica["arriba"]))
    Button_num_grafica_abajo.configure(text=str(dic_ultima_grafica["abajo"]))
    segemented_button2.set("DEFORMATION")
    segmented_button_callback2("DEFORMATION")
    segemented_button.set("ACCELERATION")
    segmented_button_callback1("ACCELERATION")
    
    try:
        if len(container1.grid_slaves()) > 3:
            for index,l in enumerate(container1.grid_slaves()):
                if index == 0:
                    l.destroy()
    except Exception as e:
        print(e, 18)
    print(tipo_review)
    if tipo_review == "collectwire":
        for boton in container2_3.grid_slaves():
            if boton.cget("text") == "EXPORT":
                boton.destroy()
    else:
        validador_exportar = 0
        for boton in container2_3.grid_slaves():
            if boton.cget("text") == "EXPORT":
                validador_exportar = 1
        if validador_exportar == 0:
            ctk.CTkButton(container2_3, text=botones_barra_lateral[7], font=font_barra_derecha, command=lambda: [Seleccionar_ruta_guardado_pdf() ]).grid(row=7,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5)) 


numero_grafica_insertada = 0

marca = False

tipo_señal = ""
bandera_grafica = False

def crear_columna_muestreo():
    global frecuencia_muestreo, ruta_guardado, font_barra_derecha
    global pile_area_label, EM_label, ET_label, container2_3
    global numero_grafica_insertada, marca, tipo_señal, bandera_grafica, matriz_data_archivos, Entry_Profundidad_inicial, Entry_Profundidad_final
    global Entry_altura, Entry_Area, Entry_masa, Entry_modulo_elasticidad, estado_continuidad
    matriz_data_archivos = []


    pile_area_label.configure(text=str(round(float(Entry_Area.get()),2)))
    EM_label.configure(text=str(round(float(Entry_modulo_elasticidad.get()),2)))
    ET_label.configure(text=str(round(int(float(Entry_masa.get())* float(Entry_altura.get())*9.81),2)))

    container1_3 = ctk.CTkFrame(container1)
    container1_3.grid(row=3, column=0, padx=20, pady=10, sticky='new')
    container1_3.grid_columnconfigure(0, weight=10)
    container1_3.grid_columnconfigure(1, weight=1)
    container1_3.grid_rowconfigure(0, weight=1)
    container1_3.grid_rowconfigure(1, weight=1)
    container1_3.grid_rowconfigure(2, weight=1)

    ctk.CTkLabel(container1_3, text="Sample Rate:", font=fontTEXTcoll).grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
    ctk.CTkLabel(container1_3, text="Time Rate:", font=fontTEXTcoll).grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
    ctk.CTkLabel(container1_3, text="Delay Time:", font=fontTEXTcoll).grid(row=2, column=0, padx=10, pady=10, sticky='nsew')
    
    L_Frecuencia = ctk.CTkLabel(container1_3, text=str(frecuencia_muestreo[-1])+" khz", font=fontTEXTcoll)
    L_Frecuencia.grid(row=0, column=1, padx=10, pady=10, sticky='ns')
    L_T_Muestreo = ctk.CTkLabel(container1_3, text=Entry_tiempo_muestreo.get()+" ms", font=fontTEXTcoll)
    L_T_Muestreo.grid(row=1, column=1, padx=10, pady=10, sticky='ns')
    L_T_Retardo = ctk.CTkLabel(container1_3, text=Entry_tiempo_Retardo.get()+" ms", font=fontTEXTcoll)
    L_T_Retardo.grid(row=2, column=1, padx=10, pady=10, sticky='ns')
    matriz_data_archivos.append(str(Entry_Profundidad_inicial.get())+","+str(Entry_Profundidad_final.get()))
    orden_sensores2 = []
    orden_sensores2.append(str(orden_sensores[-1].replace("\n", ""))+str(frecuencia_muestreo[-1])+"|"+str(Entry_Area.get())+"|"+str(Entry_modulo_elasticidad.get())+"|"+str(int(float(Entry_masa.get())* float(Entry_altura.get())*9.81)))
    
    
    Boton_play = ctk.CTkButton(container2_3, text="►", font=ctk.CTkFont(size=20, weight="bold"), command=lambda:[cambio_boton_play()])
    Boton_play.grid(row=7,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5)) 

    def graficas_tiempo_real(num):
        global bandera_grafica, matriz_data_archivos
        global marca
        
        print(marca, bandera_grafica)
        
        def graficar():
            global bandera_grafica, marca
            while bandera_grafica and marca:
                #time.sleep(0.2)
                try:
                    marca = False
                    
                    print("Intentando graficar2 ", num)
                    #try:
                    print(1)
                    dic_ultima_grafica['arriba'] = int(num)
                    print(2)
                    Creacion_Grafica("arriba",dic_ultima_grafica_magnitud["arriba"], int(num), "original", "NO", "NO")
                    #except Exception as e:
                    #    print("error en grafica arriba", e)
                    try:
                        dic_ultima_grafica['abajo'] = int(num)
                        Creacion_Grafica("abajo",dic_ultima_grafica_magnitud["abajo"], int(num), "original", "NO", "NO")
                    except Exception as e:
                        print("error en grafica abajo", e)
                except:
                    print("no hay Data")
        threading.Thread(target=graficar).start()


    def inicio_secuencia_grabado():
        global bandera_grafica, marca,señal_continua, matriz_data_archivos, estado_continuidad
        global socket_tcp

        def lectura():
            global bandera_grafica, marca, señal_continua
            global socket_tcp
            time.sleep(2)
            MESSAGE = "M"
            socket_tcp.send(MESSAGE.encode('utf-8'))

            print("M")
            num = 0

            while señal_continua == True: 
                print("conexion abierta por inicio")
                bandera_grafica = True
                bandera3 = 0

                string = ""
                vector = []
                acumulado = ""

                while ((bandera3 == 0 ) and (señal_continua == True)):
                    
                    print("recibiendo")
                    cata = socket_tcp.recv(10000).decode("cp437")
                   
                    if cata != "":
                        acumulado += cata


                    if acumulado[-5:] == "FINAL":
                        acumulado = acumulado[:-5]
                        bandera3 = 1
                        data = acumulado.split("\n")
                        for linea in data:
                            vector.append(linea)
                        matriz_data_archivos.append(vector)
                        print("una data registrada")
                        num = len(matriz_data_archivos) -1
                        vector = []
                        break
                print("conexion cerrada")
                
                marca = True
                print("intentado graficar")
                if estado_continuidad == "tiempo_real":
                    print("se están graficando las nuevas gráficas")
                    graficas_tiempo_real(num)
                else:
                    print("ya no se grafican las nuevas gráficas")

            bandera_grafica = False

        threading.Thread(target=lectura).start()


    def mandar_alerta_boton_stop():
        global señal_continua, matriz_data_archivos, Entry_Profundidad_inicial, Entry_Profundidad_final, ruta_guardado
        global socket_tcp
        respuesta = MessageBox.askyesno(message="¿Desea continuar?, se detendrá el recibimiento de data.", title="Alerta")
        if respuesta == True:
            eliminar_botones()
            socket_tcp.send("F".encode('utf-8'))
            señal_continua = False
            nombre_archivo = "profundidad_" + str(Entry_Profundidad_inicial.get())+"-"+str(Entry_Profundidad_final.get())+".ct"
            
            """
            with open(ruta_guardado+nombre_archivo, "w") as archivo:
                string = "profundidad:"+str(Entry_Profundidad_inicial.get())+","+str(Entry_Profundidad_final.get())+" \n"
                for i in range(1,len(matriz_data_archivos)):
                    string += "INICIO_ARCHIVO\n"
                    string += "ARCHIVO:"+str(i)+"\n"
                    string += orden_sensores2[-1]+ "\n"
                    for fila in matriz_data_archivos[i]:
                        string += fila + "\n"
                    string += "FIN_ARCHIVO\n"
                archivo.write(string)
            """

            lines = []
            lines.append("profundidad:{},{}\n".format(Entry_Profundidad_inicial.get(), Entry_Profundidad_final.get()))

            for i in range(1, len(matriz_data_archivos)):
                lines.append("INICIO_ARCHIVO\n")
                lines.append("ARCHIVO:{}\n".format(i))
                lines.append(orden_sensores2[-1] + "\n")
                lines.extend([fila + "\n" for fila in matriz_data_archivos[i]])
                lines.append("FIN_ARCHIVO\n")

            with open(ruta_guardado + nombre_archivo, "w") as archivo:
                archivo.write("".join(lines))
            print("ARCHIVO GUARDADO CON EXITO")
            MessageBox.showinfo(title="Saved", message="File saved succesfully.")
            #Boton_play = ctk.CTkButton(container2_3, text="►", font=ctk.CTkFont(size=20, weight="bold"), command=lambda:[cambio_boton_play()])
            #Boton_play.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=(30), pady=(150,10))
            #.grid(row=7,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5)) 
            
        elif respuesta == False:
            pass

    def eliminar_botones():
        print("eliminar botones")
        for boton in container2_3.grid_slaves():
            print(boton.cget("text"))
            if boton.cget("text") == "STOP" or boton.cget("text") == "►" or boton.cget("text") == "EXPORT":
                boton.destroy()
                print("eliminado")

    def cambio_boton_play():
        global señal_continua, tipo_señal, conexion, container2_3, font_barra_derecha
        if tipo_señal == "F":
            print("vengo del pause")
            tipo_señal = "M" 
        else:
            print("primera señal")
            tipo_señal = "M"
            
        señal_continua = True
        eliminar_botones()

        Boton_stop = ctk.CTkButton(container2_3, text="STOP", font=font_barra_derecha, command=lambda:[cambio_boton_stop()])
        Boton_stop.grid(row=7,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5))
        
        inicio_secuencia_grabado()

    def cambio_boton_pausa():
        global señal_continua, tipo_señal
        señal_continua = False
        tipo_señal = "F"
        eliminar_botones()
        time.sleep(3)
        socket_tcp.send("F".encode('utf-8'))
        #time.sleep(0.2)
        conexion.close()

        Boton_play = ctk.CTkButton(container2_3, text="►", font=font_barra_derecha, command=lambda:[cambio_boton_play()])
        Boton_play.grid(row=7, column=0, columnspan=2, sticky='nsew', padx=(30), pady=(150,10))

    def cambio_boton_stop():
        mandar_alerta_boton_stop()


Num_golpes = []
Num_golpes_modificado = []

container6_1_1 = ""

def Eliminar_Fila():
        global filas
        for i in range(len(filas[-1])):
            filas[-1][i].destroy()
        filas.pop()
    
def Eliminar_todas_filas():
    for i in range(10):
        try:
            Eliminar_Fila()
        except Exception as e:
            print(e, 19)

filas = []
contador_fila = 1
fila_grabada = []

def Insertar_Fila(container6_1_1):
    global filas, contador_fila
    fila_grabada = []
    try:
        for i in range(7):
            fila_grabada.append(ctk.CTkEntry(container6_1_1)) 
            fila_grabada[i].grid(row=contador_fila, column=i, sticky='nsew')
        filas.append(fila_grabada)
        contador_fila +=1
    except Exception as e:
        print(e, 20)

def Seleccionar_ruta_guardado_pdf():
    global ruta_guardado_pdf
    try:
        ruta_guardado_pdf = filedialog.askdirectory(initialdir = "/", title = "Selecciona una carpeta")
        print("la ruta de guardado es ", ruta_guardado_pdf)
        if ruta_guardado_pdf != "":
            create_toplevel_export()
    except Exception as e:
        print(e, 21)

boton_exportar_pdf_excel = ""

def create_toplevel_export():
    global Num_golpes, Num_golpes_modificado, filas, contador_fila, fila_grabada, filas, contador_fila, ruta, boton_exportar_pdf_excel
    export_frame = ctk.CTkToplevel()
    export_frame.resizable(False, False) 
    export_frame.grab_set()
    export_frame.focus()
    export_frame.title("Export")
    # create label on CTkToplevel window
    container6 = ctk.CTkFrame(export_frame)

    container6.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
    container6.grid_rowconfigure(0, weight=1)
    container6.grid_rowconfigure(1, weight=2)
    container6.grid_rowconfigure(2, weight=1)
    container6.grid_columnconfigure(0, weight=1)

    container6_0 = ctk.CTkFrame(container6)
    container6_0.grid(row=0, column=0, padx=(30), pady=(30,15), sticky= 'nsew')
    container6_0.grid_rowconfigure(0, weight=1)
    container6_0.grid_columnconfigure(0, weight=1)
    container6_0.grid_columnconfigure(1, weight=1)
    container6_0.grid_columnconfigure(2, weight=1)


    label_cantidad_golpes = ctk.CTkLabel(container6_0)
    label_cantidad_golpes.grid(row=0, column=0, padx=20, pady=10)

    label_inicio = ctk.CTkLabel(container6_0)
    label_inicio.grid(row=0, column=1, pady=10)

    label_final = ctk.CTkLabel(container6_0)
    label_final.grid(row=0, column=2, padx=20, pady=10)

    container6_1 = ctk.CTkFrame(container6)
    container6_1.grid(row=1, column=0, padx=(30), pady=(15), sticky= 'nsew')
    container6_1.grid_columnconfigure(0, weight=1)

    container6_1_1 = ctk.CTkFrame(container6_1)
    container6_1_1.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)

    texto_columnas_export = ["Depth (m)", "Number of impacts", "Increase (m)", "BN remainder", "Hit rate (bl/m)", "Set/blow (mm/bl)", "Elevation (m)"]

    for i in range(7):
        container6_1_1.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(container6_1_1, text=texto_columnas_export[i]).grid(row=0, column=i, sticky='nsew')

    container6_2 = ctk.CTkFrame(container6)
    container6_2.grid(row=2, column=0, padx=(30), pady=(15,30), sticky= 'nsew')
    container6_2.grid_rowconfigure(0, weight=1)

    for i in range(5):
        container6_2.grid_columnconfigure(i, weight=1)

    ctk.CTkButton(container6_2, text="Insert row", command=lambda:Insertar_Fila(container6_1_1)).grid(row=0, column=0, sticky='nsew', padx=(10,0), pady=10)
    ctk.CTkButton(container6_2, text="Delete row", command=lambda:Eliminar_Fila()).grid(row=0, column=1, sticky='nsew', padx=(10,0), pady=10)
    ctk.CTkButton(container6_2, text="Complete", command=lambda:Completar_Filas()).grid(row=0, column=2, sticky='nsew', padx=(10,0), pady=10)
    
    boton_exportar_pdf = ctk.CTkButton(container6_2, text="Export PDF", command=lambda: [mostrar_alertas_exportar("pdf")])
    boton_exportar_pdf.grid(row=0, column=3, sticky='nsew', padx=(10), pady=10)

    boton_exportar_excel = ctk.CTkButton(container6_2, text="Export Excel", command=lambda: [mostrar_alertas_exportar("excel")])
    boton_exportar_excel.grid(row=0, column=4, sticky='nsew', padx=(10), pady=10)

    filas = []
    contador_fila = 1
    fila_grabada = []

    Num_golpes = []
    Num_golpes_modificado = []

    preparaciones_exportar(label_cantidad_golpes, label_inicio, label_final)

    for i in range(4):
        Insertar_Fila(container6_1_1)

    def mostrar_alertas_exportar(tipo_archivo):
        global filas, Num_golpes, Num_golpes_modificado, matriz_data_archivos, ruta_guardado_pdf, boton_exportar_pdf_excel
        global longitudes
        contador = 0
        if tipo_archivo == "pdf":
            longitudes = matriz_data_archivos[0][12:].split(",")
            for fila in filas:
                for i in range(len(fila)):
                    if str(fila[i].get()) != "":
                        contador += 1
            print(filas[0][0].get(), filas[-1][0].get())
            print("las longitudes son:", longitudes)
            if contador  != len(filas)*len(filas[0]):
                MessageBox.showerror("Error", "Inserte todos los datos") 
            elif str(float(filas[0][0].get())) != str(float(longitudes[1])) or str(float(filas[-1][0].get())) != str(float(longitudes[0])):
                MessageBox.showerror("Error", "Las longitudes iniciales y finales no coinciden")
            elif sum(Num_golpes) != len(matriz_data_archivos)-1:
                MessageBox.showerror("Error", "La cantidad de golpes insertada no concuerda con la del archivo")
            elif ruta_guardado_pdf == "":
                MessageBox.showerror("Error", "Seleccione una ruta de guardado")
            else:
                Calcular_Promedios("pdf")
        else:
            Num_golpes = [len(matriz_data_archivos)-1, 0, 0, 0]
            Calcular_Promedios("excel")
            
    def Completar_Filas():
        global filas, Num_golpes, Num_golpes_modificado
        Num_golpes = []
        Num_golpes_modificado = []
        contador = 0
        
        for fila in filas:
            if fila[0].get() != "" and fila[1].get() != "":
                contador += 1 
        if contador == len(filas):
            for i in range(len(filas)):
                Num_golpes.append(int(filas[i][1].get()))
            Num_golpes_modificado = []
            total = sum(Num_golpes)

            for i in range(len(filas)):
                # proceso de borrado de las últimas columnas:
                for j in range(2, len(filas[0])):
                    filas[i][j].delete(0, END)

            for i in range(len(Num_golpes)):
                print(i, total, Num_golpes[i])
                Num_golpes_modificado.append(total)
                total = total-Num_golpes[i]
            print(Num_golpes_modificado)
            

            for i in range(len(Num_golpes)):
                try:
                    filas[i][2].insert(0, str(round(float(filas[i][0].get())-float(filas[i+1][0].get()),2)))
                except:
                    filas[i][2].insert(0, 0)
                filas[i][3].insert(0, Num_golpes_modificado[i])
                try:
                    filas[i][4].insert(0, str(round(Num_golpes[i]/float(filas[i][2].get()),3)))
                except:
                    filas[i][4].insert(0, 0)
                try:
                    filas[i][5].insert(0, str(round(float(filas[i][2].get())/Num_golpes[i],5)))
                except:
                    filas[i][5].insert(0, 0)
                try:    
                    filas[i][6].insert(0, str(float(filas[i][0].get())*-1))
                except:
                    filas[i][6].insert(0, 0)
        print(Num_golpes)

fila_resumen = []

Energias = []
Fuerzas = []
Velocidades = []
Energias_teoricas = []
Impedancias = []

def Calcular_Promedios(tipo_archivo):
    global Energias, Fuerzas, Velocidades, Energias_teoricas, orden_sensores, frecuencia_muestreo, pile_area, EM_valor_original, ET_valor_original, matriz_data_archivos, Num_golpes, Num_golpes_modificado, segundo_inicial, segundo_final, fila_resumen
    global ET_valor_original, valor_actual_sistema_metrico
    global bpm_list
    orden = str(orden_sensores[-1]).replace(" ","").split("|")

    print("CREANDO EL PDF")
    if len(orden[4])>1:
        frecuencia_muestreo.append(orden[4])

    try:
        pile_area = orden[5]
    except Exception as e:
        print(e, 25)
        pile_area = "15.6"
        print("algo está mal")
    try:
        EM_valor_original = orden[6]
    except Exception as e:
        print(e, 26)
        EM_valor_original = "207000"
        
    Energias = []
    Fuerzas = []
    Velocidades = [] 
    Energias_teoricas = []
    Aceleraciones_data = []
    Deformaciones_data = []
    Fuerzas_data = []
    Segundos_data = []
    Energias_data = []
    Velocidades_data = []
    Desplazamientos_data = []
    print("nESTA ES LA Longitud de matriz data archivos: ", len(matriz_data_archivos))
    for j in range(1, len(matriz_data_archivos)):
        A, t, S, t, t, t, V, t, E, D, t, F, V_Transformado, segundos, ET, ETR, t, Fmax, Vmax, Emax, t, Z, t, t, t, t, t, t, t, t = Creacion_Datos_Graficas("fuerzaxvelocidad", j, "original", "SI")
        Energias.append(Emax)
        Fuerzas.append(Fmax)
        Velocidades.append(Vmax)
        Energias_teoricas.append(ETR)
        Aceleraciones_data.append(A)
        Deformaciones_data.append(S)
        Fuerzas_data.append(F)
        #print("LA FUERZA EN ", j, "ES:", F[20])
        segundos_corregidos = []
        for i in segundos:
            segundos_corregidos.append(float(i)/10)
        Segundos_data.append(segundos_corregidos)
        Energias_data.append(E)
        Velocidades_data.append(V)
        Desplazamientos_data.append(D)
    
    #Aquí se añade una fila más a cada variable de arriba Energias, fuerzas, etc, por lo cual se le quita una fila a cada una abajo
    t, t, t, t, t, t, t, t, t, t, t, Fuerzas_impedancia_maxima, Velocidades_impedancia_maxima, segundos, t, t, t, t, t, t, t, t, t, t, t, t, t, t, t, t = Creacion_Datos_Graficas("fuerzaxvelocidad", 1, "original", "SI")
    #print("las energías recién sacadas son las siguientes", Energias, Energias_teoricas)

    if valor_actual_sistema_metrico == "SI":
        datas = [[["", "BL#", "BC", "FMX", "VMX", "BPM", "EFV", "ETR"], ["", "", "/150mm", "kN", "m/s", "bpm", "J", "%"]], [], []]
    elif valor_actual_sistema_metrico == "EN":
        datas = [[["", "BL#", "BC", "FMX", "VMX", "BPM", "EFV", "ETR"], ["", "", "/5.90in", "kips", "ft/s", "bpm", "ft-lbs", "%"]], [], []]

    Num_golpes_modificado2 = []
    Num_golpes_modificado2.append(0)
    acumulado = 0
    
    for i in range(len(Num_golpes)):
        acumulado += Num_golpes[len(Num_golpes)-i-2]
        Num_golpes_modificado2.append(acumulado)
        
    Energias_recortadas = Energias[Num_golpes[-2]:]
    Velocidades_recortadas = Velocidades[Num_golpes[-2]:]
    Fuerzas_recortadas = Fuerzas[Num_golpes[-2]:]
    Energias_teoricas_recortadas = Energias_teoricas[Num_golpes[-2]:]
    #print(Energias_recortadas)
    orden_golpes = []
    for i in range(len(Num_golpes)):
        orden_golpes.append(Num_golpes[len(Num_golpes)-i-2])
    fila_resumen = []
    rn_prof = str(longitudes[0]) + " - " + str(longitudes[1])
    fila_resumen.append(rn_prof)# primera columna del resumen
    fila_resumen.append(str(orden_golpes[:-1])) # los golpes en orden
    fila_resumen.append(str(sum(Num_golpes[:-2]))) # total de golpes
    fila_resumen.append(str(round((sum(Num_golpes[:-2])*sum(Energias_teoricas_recortadas))/(len(Energias_teoricas_recortadas)*60),0))) # 
    fila_resumen.append(str(round(sum(Fuerzas_recortadas)/len(Fuerzas_recortadas),1)))
    fila_resumen.append(str(round(sum(Velocidades_recortadas)/len(Velocidades_recortadas),1)))
    fila_resumen.append(str(round(sum(bpm_list)/len(bpm_list),1)))
    fila_resumen.append(str(round(sum(Energias_recortadas)/len(Energias_recortadas),1)))
    fila_resumen.append(str(round(sum(Energias_teoricas_recortadas)/len(Energias_teoricas_recortadas),1)))
    #print("las energias recortadas son", Energias_recortadas)

    for j in range(3):
        for i in range(Num_golpes_modificado2[j],Num_golpes_modificado2[j+1]):
            print("ESTUVO BIEN: ", i)
            datas[j].append(["",str(i+1),str(orden_golpes[j]),str(Fuerzas[i]), str(Velocidades[i]), str(bpm_list[i]), str(round(float(Energias[i]),2)),str(round(float(Energias_teoricas[i]),2))])

    #Graficar y convertirla en imagen
    
    f = Figure(figsize=(15,5), dpi=300)
    a = f.add_subplot(111)

    segundos_grafica = []
    Fuerzas_impedancia_maxima_grafica = []
    Velocidades_impedancia_maxima_grafica = []

    

    for i in range(len(segundos)):
        if segundos[i] < 22 and segundos[i] >7: 
            segundos_grafica.append(segundos[i])
            Fuerzas_impedancia_maxima_grafica.append(Fuerzas_impedancia_maxima[i])
            Velocidades_impedancia_maxima_grafica.append(Velocidades_impedancia_maxima[i])

    t1, = a.plot(segundos_grafica, Fuerzas_impedancia_maxima_grafica, label= "F",linewidth=2.0, color="#8B0000")

    desfase = 0.15
    
    segundos_grafica_desfasada = [t - desfase for t in segundos_grafica]
    t2, = a.plot(segundos_grafica_desfasada, Velocidades_impedancia_maxima_grafica, label=str(round(Z, 2))+"*V", linewidth=2.0, color="#0f2f76")

    a.set_facecolor("#EEEEEE")
    #t2, = a.plot(segundos_grafica, Velocidades_impedancia_maxima_grafica, label=str(round(Z, 2))+"*V")
    
    #a.axis('off')
    tamaño_leyenda = 18
    try:
        a.legend(handles=[t1, t2], prop={'size': tamaño_leyenda})
    except:
        try:
            a.legend(handles=[t1], prop={'size': tamaño_leyenda})
        except:
            try:
                a.legend(handles=[t2], prop={'size': tamaño_leyenda})
            except Exception as e:
                print(e, 27)

    a.tick_params (left = False ,
                 bottom = False,
                 labelleft = False ,
                 labelbottom = False )
    canvas = FigureCanvas(f)
    canvas.draw()
    img = Image.fromarray(np.asarray(canvas.buffer_rgba()))
    
    if tipo_archivo == "excel":
        crear_excel(Segundos_data, Aceleraciones_data, Deformaciones_data, Fuerzas_data, Velocidades_data, Energias_data, Desplazamientos_data)
    elif tipo_archivo == "pdf": 
        crear_pdf(datas, img)
    MessageBox.showinfo(title="Exportado", message="Se ha exportado con éxito el "+tipo_archivo)


def crear_excel(Segundos, A, S, F, V, E, D):
    global ruta_guardado_pdf, ruta_data_inicial

    data = [Segundos, A, S, F, V, E, D]
    cadenas =ruta_data_inicial.split("/")[-1][:-3]
    nombre_archivo = 'Reporte_' + cadenas + '.xlsx'

    workbook = xlsxwriter.Workbook(ruta_guardado_pdf + "/" + nombre_archivo)
    
    for i in range(len(F)):
        worksheet = workbook.add_worksheet('Datos del impacto '+str(i+1))

        cell_format4 = workbook.add_format()
        cell_format4.set_align('center')
        cell_format4.set_align('vcenter')
        cell_format4.set_text_wrap()

        cell_format3 = workbook.add_format()
        cell_format3.set_text_wrap()
        cell_format3.set_align('center')
        cell_format3.set_align('vcenter')
        cell_format3.set_font_color('white')
        cell_format3.set_bold()
        cell_format3.set_bg_color('#1F246D')

        for j in range(len(data)):
            for k in range(len(data[j][i])):
                worksheet.write(k+2, j+1, data[j][i][k], cell_format4)
        
        columnas = ["Seconds", "Acceleration", "Deformation", "Force", "Velocity", "Energy", "Displacement"]

        worksheet.set_column("A:A",5)
        worksheet.set_column("B:B",25)#
        worksheet.set_column("C:C",25)
        worksheet.set_column("D:D",25)
        worksheet.set_column("E:E",25)
        worksheet.set_column("F:F",25)#
        worksheet.set_column("G:G",25)
        worksheet.set_column("H:H",25)

        for i in range(1, len(columnas)+1):
            worksheet.write(1, i ,columnas[i-1], cell_format3)
        
    workbook.close()

def crear_pdf(datas, img):
    global pile_area, EM_valor_original, ET_valor_original, fila_resumen, ruta_data_inicial, ruta_guardado_pdf, extension
    global valor_actual_sistema_metrico
    global bpm_list
    nombre_archivo = ""
    num_extension = -1 * (len(extension)+1)
    cadenas =ruta_data_inicial.split("/")[-1][:num_extension]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12)
    line_height = pdf.font_size * 1.5
    pdf.set_margin(20)
    pdf.cell(0, 10, "SPT - ENERGY ANALIZER")
    pdf.set_font("Times", size=8)

    pdf.set_line_width(0.1)
    pdf.line(x1=20, y1=28, x2=185, y2=28)

    pdf.ln(line_height)
    pdf.cell(0, 10, "AR: "+ str(pile_area) + " cm²")
    pdf.ln(line_height*0.5)
    pdf.cell(0, 10, "EM: "+ str(EM_valor_original) + " MPa")
    pdf.ln(line_height*0.5)
    pdf.cell(0, 10, "ET: "+ str(ET_valor_original) + " J")
    pdf.ln(line_height*2)
    
    pdf.set_margin(10)

    pdf.line(x1=20, y1=40, x2=185, y2=40)

    pdf.image(img, w=pdf.epw, h=70, x=5)

    pdf.set_margin(20)
    col_width = pdf.epw / 2
    sensores = [["F1 : [590AW1] 204.51 PDICAL", "F2 : [590AW2] 203.63 PDICAL"],["A3 (PR): [K13548] 374.7 mv/6.4v/5000g", "A4 (PR): [K13959] 399.0 mv/6.4v/5000g"]]
    for row in sensores:
        for datum in row:
            pdf.multi_cell(col_width, line_height, datum, border=0,
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
        pdf.ln(line_height)
    col_width = pdf.epw / 5
    legendas = ["FMX: Maximun Force", "VMX: Maximum Velocity", "BPM: Blows/Minute", "EFV: Maximun Energy", "ETR: Theoric Energy"]
    for datum in legendas:
        pdf.multi_cell(col_width, line_height, datum, border=0,
                new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
    pdf.ln(10)
    pdf.set_draw_color(r=0, g=0, b=0)

    pdf.set_line_width(0.1)
    pdf.line(x1=20, y1=138, x2=185, y2=138)

    col_width = pdf.epw / 8
    for row in datas[0]:
        for datum in row:
            pdf.multi_cell(col_width, line_height, datum, border=0,
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
        pdf.ln(line_height)
    pdf.set_line_width(0.1)
    y = 138+len(datas[0])*line_height
    print(y)
    pdf.line(x1=20, y1=y, x2=185, y2=y)
    dic_sistema_metrico_pdf = {"SI":0, "EN": 1}
    for row in datas[1]:
        for datum in row:
            pdf.multi_cell(col_width, line_height, datum, border=0,
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
        pdf.ln(line_height)
    for row in datas[2]:
        for datum in row:
            pdf.multi_cell(col_width, line_height, datum, border=0,
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
        pdf.ln(line_height)
    pdf.set_line_width(0.1)
    y= pdf.get_y()
    pdf.line(x1=20, y1=y, x2=185, y2=y)

    pdf.ln(10)
    pdf.cell(0, 10, "Summary result")
    pdf.ln(line_height)

    y= pdf.get_y()
    pdf.line(x1=20, y1=y, x2=185, y2=y)
    col_width = pdf.epw / 9
    
    if valor_actual_sistema_metrico == "SI":
        cabezera_resumen = [["Instr.", "Blows", "N", "N60", "Average", "Average", "Average", "Average", "Average"], 
        ["Length", "Applied", "Value", "Value", "FMX", "VMX", "BPM", "EFV", "ETR"], ["m", "/150mm", "", "", "kN", "m/s", "bpm", "J", "%"]]
    elif valor_actual_sistema_metrico == "EN":
        cabezera_resumen = [["Instr.", "Blows", "N", "N60", "Average", "Average", "Average", "Average", "Average"], 
        ["Length", "Applied", "Value", "Value", "FMX", "VMX", "BPM", "EFV", "ETR"], ["ft", "/5.90in", "", "", "kips", "ft/s", "bpm", "ft-lbs", "%"]]

    for row in cabezera_resumen:
        for datum in row:
            pdf.multi_cell(col_width, line_height, datum, border=0,
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
        pdf.ln(line_height)
    
    y= pdf.get_y()
    pdf.line(x1=20, y1=y, x2=185, y2=y)
    print(fila_resumen)
    for column in fila_resumen:
        pdf.multi_cell(col_width, line_height, column, border=0,
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
    pdf.ln(line_height)
    
    y= pdf.get_y()
    pdf.line(x1=20, y1=y, x2=185, y2=y)
    
    pdf.set_font("Times", size=12)
    # Cuadro Resumen

    nombre_archivo = 'Report_' + cadenas + '.pdf'
    print(nombre_archivo)
    pdf.output(ruta_guardado_pdf + "/" + nombre_archivo)

def create_toplevel_about():
    about_frame = ctk.CTkToplevel()
    #about_frame.geometry("800x400")
    about_frame.title("About")
    about_frame.resizable(False, False) 
    about_frame.grab_set()
    about_frame.focus()
    # create label on CTkToplevel window
    container7 = ctk.CTkFrame((about_frame))
    container7.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)

    container7.grid_rowconfigure(0, weight=1)
    container7.grid_rowconfigure(1, weight=2)
    container7.grid_columnconfigure(0, weight=1)

    label1 = ctk.CTkLabel(container7, text="Kallpa Procesor made by CITDI", font=fontABOUTtitulo)
    label1.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
    label2 = ctk.CTkLabel(container7, text="Created in collaboration with:\n\nCarmen Eleana Ortiz Salas\nGrover Riveros Soto\nRoberto Freddy Raucana Sulca\nAlejandrina Nelly Huarcaya Junes\nJoseph Mottoccanche Tantaruna", font=fontABOUTtexto)
    label2.grid(row=1, column=0, sticky='nsew', padx=20, pady=(20))

# programa convertir rpn a ctn

def escoger_ruta_guardado2():
    archivos = filedialog.askopenfilenames(initialdir = "/", title = "Select the files to convert")
    #ruta_guardado += "/"
    return archivos

def leer_data_cabecera(ruta, identificador):
    with open(ruta) as file:
        filas = file.readlines()
    for index, fila in enumerate(filas):
        fila = fila.replace("\n", "").split(identificador)
        if index < 15:
            print(fila)
        if fila[0] == "AR":
            ar_pos = index
        if fila[0] == "EM":
            em_pos = index
        if fila[0] == "EFV":
            efv_pos = index
        if fila[0] == "ETR":
            etr_pos = index
        if fila[0] == "BPM":
            bpm_pos = index  
        if fila[0] == "Record":
            frecuencia_post = index+3
    

    ar = round(float(filas[ar_pos].replace("\n", "").split(identificador)[1]),2)
    em = round(float(filas[em_pos].replace("\n", "").split(identificador)[1]),2)
    efv = float(filas[efv_pos].replace("\n", "").split(identificador)[1])
    etr = float(filas[etr_pos].replace("\n", "").split(identificador)[1])
    bpm_real = round(float(filas[bpm_pos].replace("\n", "").split(identificador)[1]),2)
    et = round((efv/etr)*100,2)

    frecuencia = round(1/float(filas[frecuencia_post].replace("\n", "").split(identificador)[1])/1000)

    fila_orden = filas[frecuencia_post-3].replace("\n", "").split(identificador)
    print(fila_orden)
    orden = [fila_orden[2].split("@")[0], fila_orden[3].split("@")[0]]
    try:
        orden.append(fila_orden[4].split("@")[0])
    except Exception as e:
        print(e, 28)
        orden.append("0")

    try:
        orden.append(fila_orden[5].split("@")[0])
    except Exception as e:
        print(e, 29)
        orden.append("0")
        
    dic_orden = {"S3":"3", "S4":"4", "S1":"3", "S2":"4", "A1":"1", "A2":"2", "A3":"1", "A4":"2", "0":"0"}
    cant_strain = 0
    cant_acel = 0

    orden_string = ""
    for index, elemento in enumerate(orden):
        if (dic_orden[elemento] == "3" or dic_orden[elemento] == "4"):
            if cant_strain<1:
                orden_string += "3" +"|"
                cant_strain += 1
            else:
                orden_string += "4" +"|"

        elif (dic_orden[elemento] == "1" or dic_orden[elemento] == "2"):
            if cant_acel<1:
                orden_string += "1" +"|"
                cant_acel += 1
            else:
                orden_string += "2" +"|"
        
        else:
            orden_string += "0" +"|"

    print(orden_string)
    print(frecuencia)
    print(ar, em, et)
    return frecuencia_post, filas, orden_string, frecuencia, ar, em, et, bpm_real

    # lectura de la data 
def lectura_data(frecuencia_post, filas, identificador):
    string_data = ""
    for i in range(frecuencia_post-1, len(filas)):
        fila = filas[i].replace("\n", "").split(identificador)
        segundos = round(float(fila[1])*10000,2)
        V1 = float(fila[2])
        V2 = float(fila[3])
        try:
            V3 = float(fila[4])
        except Exception as e:
            print(e, 30)
        try:
            V4 = float(fila[5])
        except Exception as e:
            print(e, 31)
        try:
            nueva_fila = str(segundos) + "|" + str(V1) + "|" + str(V2) + "|" + str(V3) + "|" + str(V4) + "|"
        except:
            try:
                nueva_fila = str(segundos) + "|" + str(V1) + "|" + str(V2) + "|" + str(V3) + "|0|"
            except Exception as e:
                print(e, 32)
                nueva_fila = str(segundos) + "|" + str(V1) + "|" + str(V2) + "|0|0|"
        string_data+=nueva_fila+"\n"
    return string_data

def crear_ctn(profundidad, ruta_guardado_combinado, identificador, sistema_unidades):
    texto = ""
    for index in range(len(ruta_guardado_combinado)):
        if index == 0:
            texto += "profundidad:"+profundidad
        frecuencia_post, filas, orden_string, frecuencia, ar, em, et, bpm_real = leer_data_cabecera(ruta_guardado_combinado[index], identificador)
        #et = 467.46     # Martillo de Puerto Maldonado
        cabecera = orden_string+str(frecuencia)+"|"+str(ar)+"|"+str(em)+"|"+str(et)+"|"+sistema_unidades+"|"+str(bpm_real)
        texto+="\nINICIO_ARCHIVO\nARCHIVO:"+str(index+1)+"\n"+cabecera+"\n"
        texto+=lectura_data(frecuencia_post, filas, identificador)
        texto+="FIN_ARCHIVO"
    return texto, str(frecuencia), str(ar), str(em), str(et)

label_frecuencia = ""
label_AR = ""
label_EM = ""
label_ET = ""
Entry_archivo_inicio = ""
Entry_archivo_final = ""
ruta_guardado_combinado = ""
ruta_combinados = ""
scrollable_frame = ""
ruta_guardado_label_combinado = ""

def boton_escoger_archivos_combinar():
    global ruta_combinados
    ruta_combinados =  escoger_ruta_guardado2()
    string = ""
    for i in ruta_combinados:
        string += i +"\n"

    scrollable_frame.insert(0.0, string)

def boton_preparar(inicio, fin, identificador, sistema_unidades):
    global scrollable_frame, label_frecuencia, label_AR, label_EM, label_ET, ruta_guardado_combinado

    nombre = str(inicio) +","+str(fin)
    texto, frecuencia, ar, em, et = crear_ctn(nombre, ruta_combinados, identificador, sistema_unidades)

    label_frecuencia.configure(text=frecuencia)
    label_AR.configure(text=ar)
    label_EM.configure(text=em)
    label_ET.configure(text=et)

    with open(ruta_guardado_combinado+"\profundidad_"+str(inicio)+"-"+str(fin)+".ctn", "w") as file:
        file.write(texto)
    
    MessageBox.showinfo(message="Exportado con éxito", title="Éxito")

def escoger_ruta_combinado():
    global ruta_guardado_combinado, Entry_archivo_inicio, Entry_archivo_final, ruta_guardado_label_combinado
    ruta_guardado_combinado = filedialog.askdirectory(initialdir = "/", title = "Selecciona una carpeta")
    ruta_guardado_label_combinado.insert(0,ruta_guardado_combinado+"/profundidad_"+str(Entry_archivo_inicio.get())+"-"+str(Entry_archivo_final.get())+".ctn") 

def create_toplevel_preparar():
    global scrollable_frame, label_frecuencia, label_AR, label_EM, label_ET, Entry_archivo_final, Entry_archivo_inicio, ruta_guardado_label_combinado

    preparar_frame = ctk.CTkToplevel()

    preparar_frame.title("Join Files")
    preparar_frame.resizable(False, False) 
    preparar_frame.grab_set()
    preparar_frame.focus()
    # create label on CTkToplevel window
    container8 = ctk.CTkFrame((preparar_frame))
    container8.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)

    for i in range(7):
        container8.grid_rowconfigure(i, weight=1)
    container8.grid_columnconfigure(0, weight=1)
    container8.grid_columnconfigure(1, weight=1)
    container8.grid_columnconfigure(2, weight=1)

    ctk.CTkLabel(container8, text="Indicate the start and end of the depth").grid(row=0, column=0, sticky='nsew', padx=20, pady=10)

    container8_0 = ctk.CTkFrame(container8)
    container8_0.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
    container8_0.grid_columnconfigure(0, weight=2)
    container8_0.grid_columnconfigure(1, weight=1)
    container8_0.grid_columnconfigure(2, weight=2)

    Entry_archivo_inicio = ctk.CTkEntry(container8_0)
    Entry_archivo_inicio.grid(row=0, column=0, sticky='nsew', padx=20, pady=(10))

    Entry_archivo_final = ctk.CTkEntry(container8_0)
    Entry_archivo_final.grid(row=0, column=2, sticky='nsew', padx=20, pady=10)

    ctk.CTkLabel(container8_0, text=" - ").grid(row=0, column=1, sticky='nsew', padx=5, pady=20)

    button_escoger_archivos = ctk.CTkButton(container8, text="Select Files", font=fontTEXTcoll, command=lambda:[boton_escoger_archivos_combinar()])
    button_escoger_archivos.grid(row=2, column=0, sticky='nsew', padx=20, pady=(10,20))

    scrollable_frame = ctk.CTkTextbox(container8, width=150, height=200)
    scrollable_frame.grid(row=3, column=0, rowspan=4, sticky='nsew', padx=20, pady=(0,20))


    container8_1 = ctk.CTkFrame(container8)
    container8_1.grid(row=0, column=1, columnspan=2, rowspan=3, sticky='nsew', padx=(0,20), pady=20)
    container8_1.grid_rowconfigure(0, weight=1)
    container8_1.grid_rowconfigure(1, weight=1)
    container8_1.grid_rowconfigure(2, weight=1)
    container8_1.grid_rowconfigure(3, weight=1)
    container8_1.grid_columnconfigure(0, weight=1)
    container8_1.grid_columnconfigure(1, weight=1)

    container8_1_1 = ctk.CTkFrame(container8_1)
    container8_1_1.grid(row=0, column=0, sticky='nsew', padx=20, pady=(20,10))
    container8_1_1.grid_columnconfigure(0, weight=3)
    container8_1_1.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(container8_1_1, text="Frequency: ", width=60).grid(row=0, column=0, sticky='nsw', padx=20, pady=(20))
    label_frecuencia = ctk.CTkLabel(container8_1_1, text="")
    label_frecuencia.grid(row=0, column=1, sticky='nswe', padx=20, pady=(20))


    container8_1_2 = ctk.CTkFrame(container8_1)
    container8_1_2.grid(row=1, column=0, sticky='nsw', padx=20, pady=(10,20))
    container8_1_2.grid_columnconfigure(0, weight=3)
    container8_1_2.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(container8_1_2, text="Area: ", width=60).grid(row=0, column=0, sticky='nswe', padx=20, pady=(20))
    label_AR = ctk.CTkLabel(container8_1_2, text="")
    label_AR.grid(row=0, column=1, sticky='nswe', padx=20, pady=(20))

  
    container8_1_3 = ctk.CTkFrame(container8_1)
    container8_1_3.grid(row=0, column=1, sticky='nsw', padx=20,  pady=(20,10))
    container8_1_3.grid_columnconfigure(0, weight=3)
    container8_1_3.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(container8_1_3, text="EM: ", width=60).grid(row=0, column=0, sticky='nswe', padx=20, pady=20)
    label_EM = ctk.CTkLabel(container8_1_3, text="")
    label_EM.grid(row=0, column=1, sticky='nswe', padx=20, pady=10)

   
    container8_1_4 = ctk.CTkFrame(container8_1)
    container8_1_4.grid(row=1, column=1, sticky='nsw', padx=20, pady=(10,20))
    container8_1_4.grid_columnconfigure(0, weight=3)
    container8_1_4.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(container8_1_4, text="ET: ", width=60).grid(row=0, column=0, sticky='nswe', padx=20, pady=(20))
    label_ET = ctk.CTkLabel(container8_1_4, text="")
    label_ET.grid(row=0, column=1, sticky='nswe', padx=20, pady=(10,20))

    ctk.CTkLabel(container8, text="CSV separator:").grid(row=3, column=1, padx=20, pady=20)

    var_identificador = ctk.StringVar(value=",")
    boton_identificador = ctk.CTkSegmentedButton(container8, values=[",", ";"], variable=var_identificador)
    boton_identificador.grid(row=3, column=2, padx=20, pady=20)

    ctk.CTkLabel(container8, text="System of Units:").grid(row=4, column=1, padx=20, pady=20)
    
    var_identificador_unidades = ctk.StringVar(value="SI")
    boton_unidades_unir = ctk.CTkSegmentedButton(container8, values=["SI", "EN"], variable=var_identificador_unidades)
    boton_unidades_unir.grid(row=4, column=2, padx=20, pady=20)

    ruta_guardado_label_combinado = ctk.CTkEntry(container8)
    ruta_guardado_label_combinado.grid(row=5, column=1, columnspan=2, sticky='nsew', padx=20, pady=10)

    ctk.CTkButton(container8, text="Choose save path", command=lambda:[escoger_ruta_combinado()]).grid(row=6, column=1, padx=20, pady=(20))
    ctk.CTkButton(container8, text="Join", command=lambda:[boton_preparar(Entry_archivo_inicio.get(), Entry_archivo_final.get(), boton_identificador.get(), boton_unidades_unir.get())]).grid(row=6, column=2, padx=20, pady=(20))


Menup.grid(row=0, column=0, sticky='nsew')
Menup.grid_rowconfigure(0, weight=1)
Menup.grid_columnconfigure(0, weight=1)

root.mainloop()