# -------------------------------------------------------------------------------------------------
# Autor: Alfredo Melendez
# Version: 0.4
#
# Tipo de código: obtención de datos y graficación en tiempo real
# 
# Descripcion: Esta versión implementa la obtención de datos en tiempo real y graficarla con 
# 3 ejes que se desplazan en una grilla. Tiene la funcionalidad de poder mover la camara
# respecto del centro de la grilla y observar los movimientos en 2D y las rotaciones.
# 
# * Este código es más útil para poder visualizar posición y orientación
# * Aqui se aplica la matriz de homografía que se obtuvo en MATLAB del código Homografia.m
# 
# -------------------------------------------------------------------------------------------------

import socket
import time
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

# Variables para almacenar la posición y orientación
pos_x, pos_y = 0.0, 0.0  # Posición en el plano XY
angle_x, angle_y, angle_z = 0.0, 0.0, 0.0  # Orientación
int_gyr_ang_x, int_gyr_ang_y, int_gyr_ang_z = 0.0, 0.0, 0.0  # Integración giroscopio
alpha_pos = 0.9

alpha = 0.96  # Constante del filtro complementario para acelerómetro y giroscopio
alpha_yaw = 0.85  # Constante del filtro complementario para el yaw (giroscopio y magnetómetro)

# Matriz de homografía (como en la imagen de MATLAB)
H = np.array([[0.9806, 0.0487, -2036.3],
              [-0.0347, 1.0527, -2511.9],
              [-1.8418e-06, 1.0074e-05, 1]])

# Variables para controlar la cámara (paneo y rotación)
camera_x, camera_y = 0.0, 0.0  # Posición de la cámara (paneo)
camera_rotation_x, camera_rotation_y = 0.0, 0.0  # Rotación de la cámara
last_mouse_x, last_mouse_y = 0, 0  # Última posición del mouse
is_panning = False  # Estado de paneo con el mouse
is_rotating = False  # Estado de rotación con el mouse
pan_speed = 0.005  # Velocidad del paneo con el mouse
rotation_speed = 0.5  # Velocidad de la rotación de la cámara

def apply_homography(x, y, H):
    # Crear el vector homogéneo [x, y, 1]
    point = np.array([x, y, 1])
    
    # Aplicar la transformación usando la matriz H
    transformed_point = H @ point
    
    # Dividir por w' para obtener las coordenadas reales
    x_final = transformed_point[0] / transformed_point[2]
    y_final = transformed_point[1] / transformed_point[2]

    x_final = x_final/1000 #Convertimos a metros
    y_final = y_final/1000
    
    return x_final, y_final

# Conectar al ESP32
def esp32_connect(ip, port):
    tcp_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_obj.connect((ip, port))
    return tcp_obj

# Actualizar la posición y los ángulos usando los datos recibidos del ESP32

def update_position_and_orientation(tcp_obj, dt):
    global pos_x, pos_y, angle_x, angle_y, angle_z, int_gyr_ang_x, int_gyr_ang_y, int_gyr_ang_z

    try:
        # Intentar recibir datos del ESP32
        data = tcp_obj.recv(1024)
        if data:
            data_str = data.decode('utf-8').strip()
            lines = data_str.split('\n')  # Dividir en líneas, ya que puede haber más de un paquete
            #print(lines)
            for line in lines:
                try:
                    # Convertir los datos de la línea a flotantes
                    values = [float(val) for val in line.split(',')]
                    print(values)
                    
                    # Verificar que el paquete tenga el número correcto de valores (mínimo 11)
                    if len(values) >= 10:
                        
                        # Actualizar posición (x, y)
                        pos_x, pos_y = values[0], values[1]  # Primeros dos valores son x, y

                        # Aplicar la homografía a las coordenadas
                        pos_x, pos_y = apply_homography(pos_x, pos_y, H)

                        # Acelerómetros y giroscopios
                        ax, ay, az = values[3], values[4], values[5]
                        gx, gy, gz = values[6], values[7], values[8]
                        mx, my = values[9], values[10]

                        # Cálculo de los ángulos a partir del acelerómetro (tilt)
                        accel_angle_x = np.rad2deg(np.arctan2(ay, np.sqrt(ax**2 + az**2)))
                        accel_angle_y = np.rad2deg(np.arctan2(-ax, np.sqrt(ay**2 + az**2)))

                        # Integración de giroscopio para obtener los ángulos
                        int_gyr_ang_x += gx * dt
                        int_gyr_ang_y += gy * dt
                        int_gyr_ang_z += gz * dt

                        # Filtro complementario para combinar acelerómetro y giroscopio
                        angle_x = alpha * (angle_x + gx * dt) + (1 - alpha) * accel_angle_x
                        angle_y = alpha * (angle_y + gy * dt) + (1 - alpha) * accel_angle_y

                        # Calcular yaw usando el magnetómetro
                        mag_yaw = np.rad2deg(np.arctan2(my, mx))

                        # Filtro complementario para el yaw (combinar giroscopio y magnetómetro)
                        angle_z = alpha_yaw * (int_gyr_ang_z) + (1 - alpha_yaw) * mag_yaw

                        # Filtro complementario para posicion

                        # Para explicar las mediciones
                        # -> pos_x se transforma a metros en la función de homografia.
                        # -> ax es +/- 1g, se multiplica por 9.8 m/s^2
                        pos_x = pos_x*alpha_pos + (1-alpha_pos)*ax*9.8
                        pos_y = pos_y*alpha_pos + (1-alpha_pos)*ay*9.8

                        #print(f"Posición -> X: {pos_x:.2f}, Y: {pos_y:.2f}")
                        #print(f"acc -> X: {ax*(1-alpha_pos)*9.8:.4f}, Y: {ay*(1-alpha_pos)*9.8:.4f}")
                        #print(f"Ángulos -> X: {angle_x:.2f}, Y: {angle_y:.2f}, Z (yaw): {angle_z:.2f}")
                    else:
                        # El paquete no tiene suficientes valores
                        print("Paquete incompleto recibido, esperando el siguiente...")

                except ValueError:
                    # Si ocurre un error de conversión en los datos, lo ignoramos
                    print("Error al convertir los valores, paquete inválido.")
                    continue

    except socket.error as e:
        # En caso de un error de socket (como desconexión), manejamos el error
        print(f"Error de socket: {e}")
        time.sleep(1)  # Esperar un momento antes de intentar recibir de nuevo


# Función para dibujar los ejes X, Y, Z en OpenGL
def draw_axes():

    glLineWidth(3)  # Establecer el grosor de las líneas

    glBegin(GL_LINES)

    # Eje X - Rojo (en el plano horizontal, hacia la derecha)
    glColor3fv([1, 0, 0])
    glVertex3fv([0, 0, 0])
    glVertex3fv([0.5, 0, 0])

    # Eje Y - Verde (en el plano horizontal, hacia arriba)
    glColor3fv([0, 1, 0])
    glVertex3fv([0, 0, 0])
    glVertex3fv([0, 0.5, 0])

    # Eje Z - Azul (en el plano vertical, hacia arriba o abajo)
    glColor3fv([0, 0, 1])
    glVertex3fv([0, 0, 0])
    glVertex3fv([0, 0, 0.5])

    glEnd()

# Función para dibujar una grilla en el plano XY
def draw_grid():
    glColor3fv([0.75, 0.75, 0.75])  # Color gris claro para la grilla
    glBegin(GL_LINES)

    # Dibujar líneas paralelas al eje X (a lo largo de Y)
    for y in np.arange(-2.5, 2.51, 0.5):
        glVertex3fv([-2, y, 0])  # Desde X = -2 a X = 2 en el plano XY
        glVertex3fv([2, y, 0])

    # Dibujar líneas paralelas al eje Y (a lo largo de X)
    for x in np.arange(-2, 2.01, 0.5):
        glVertex3fv([x, -2.5, 0])  # Desde Y = -2.5 a Y = 2.5 en el plano XY
        glVertex3fv([x, 2.5, 0])

    glEnd()

# Inicializar Pygame y OpenGL
def init_pygame():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -10)  # Alejar la "cámara" un poco más para una mejor perspectiva

# Dibujar el objeto (ejes) con rotaciones y movimiento
def draw_axes_with_movement_and_rotation():
    global pos_x, pos_y

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Aplicar las rotaciones de la cámara antes de mover la cámara o la escena
    glPushMatrix()

    # Rotar la cámara si es necesario
    glRotatef(camera_rotation_x, 1, 0, 0)  # Rotar en X
    glRotatef(camera_rotation_y, 0, 1, 0)  # Rotar en Y

    # Aplicar el paneo (movimiento de la cámara)
    glTranslatef(camera_x, camera_y, 0)

    # Dibujar la grilla en el plano XY
    draw_grid()

    # Aplicar las rotaciones basadas en los ángulos calculados
    glPushMatrix()

    # Mover el objeto en el plano XY según los valores recibidos
    glTranslatef(pos_x, pos_y, 0)  # Mover en X e Y, el Z se mantiene en 0 (plano 2D)

    # Aplicar las rotaciones (orientación) calculadas
    glRotatef(angle_x, -1, 0, 0)  # Rotación en X
    glRotatef(angle_y, 0, 1, 0)  # Rotación en Y
    glRotatef(angle_z, 0, 0, -1)  # Rotación en Z (yaw)

    # Dibujar los ejes
    draw_axes()

    glPopMatrix()
    glPopMatrix()

    pygame.display.flip()

# Manejar los eventos de mouse para el paneo y la rotación
def handle_mouse_events():
    global last_mouse_x, last_mouse_y, is_panning, is_rotating, camera_x, camera_y, camera_rotation_x, camera_rotation_y

    mouse_buttons = pygame.mouse.get_pressed()
    mouse_x, mouse_y = pygame.mouse.get_pos()
    keys = pygame.key.get_pressed()

    # Paneo con el botón derecho del mouse
    if mouse_buttons[2]:  # Botón derecho
        if not is_panning:  # Al empezar a panear
            last_mouse_x, last_mouse_y = mouse_x, mouse_y
            is_panning = True
        else:  # Continuar el paneo
            dx = (mouse_x - last_mouse_x) * pan_speed
            dy = (mouse_y - last_mouse_y) * pan_speed
            camera_x += dx
            camera_y -= dy  # Invertimos el eje Y para que el movimiento sea natural
            last_mouse_x, last_mouse_y = mouse_x, mouse_y
    else:
        is_panning = False  # Dejar de panear cuando se suelta el botón derecho

    # Rotación con Ctrl + click izquierdo del mouse
    if keys[K_LCTRL] and mouse_buttons[0]:  # Ctrl + click izquierdo
        if not is_rotating:  # Al empezar a rotar
            last_mouse_x, last_mouse_y = mouse_x, mouse_y
            is_rotating = True
        else:  # Continuar la rotación
            dx = (mouse_x - last_mouse_x) * rotation_speed
            dy = (mouse_y - last_mouse_y) * rotation_speed
            camera_rotation_y += dx  # Rotar alrededor del eje Y
            camera_rotation_x += dy  # Rotar alrededor del eje X
            last_mouse_x, last_mouse_y = mouse_x, mouse_y
    else:
        is_rotating = False  # Dejar de rotar cuando se suelta el click o Ctrl

# Bucle principal
def main_loop(tcp_obj):
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # Manejar los eventos del mouse para el paneo y la rotación
        handle_mouse_events()

        # Actualizar posición y ángulos según los datos del ESP32
        update_position_and_orientation(tcp_obj, 0.1)

        # Dibujar los ejes con movimiento, rotación y grilla
        draw_axes_with_movement_and_rotation()

        clock.tick(60)  # Limitar a 60 FPS

if __name__ == "__main__":
    # Conectar al ESP32
    ip = '192.168.50.225'
    port = 80
    ESP32 = esp32_connect(ip, port)

    # Inicializar Pygame y OpenGL
    init_pygame()

    # Iniciar el bucle principal
    main_loop(ESP32)
