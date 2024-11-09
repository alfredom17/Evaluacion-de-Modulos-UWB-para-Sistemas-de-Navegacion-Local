# -------------------------------------------------------------------------------------------------
# Autor: Alfredo Melendez
# Version: 0.2
# 
# Descripcion: Al igual que las versiones pasadas, este código obtiene información de DWM1001 
# + MPU9250 y un marcador de sistema de acptura Optitrack que se denomina yr_robotat para 
# comparar YAW de ambos sistemas. Muestra 3 ejes de cada sistema y la comparación de trayectorias
# de Optitrack y DWM1001
# 
# -------------------------------------------------------------------------------------------------

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

# Leer el archivo CSV
try:
    data = pd.read_csv('TestPCB1_combined_data_STATIC_600.csv')  # Asegúrate de que el archivo esté en el directorio correcto

    # Obtener los valores de las columnas
    x = data['x'].values
    y = data['y'].values
    xr = data['xr'].values  # Coordenadas Robotat
    yr = data['yr'].values
    ax = data['ax'].values
    ay = data['ay'].values
    az = data['az'].values
    gx = data['gx'].values
    gy = data['gy'].values
    gz = data['gz'].values
    mx = data['mx'].values
    my = data['my'].values
    mz = data['mz'].values
    yr_robotat = data['ry'].values  # Orientación yaw del Robotat

    # Inicializar parámetros
    dt = 0.1  # Muestreo (100 ms)
    Fs = 1 / dt  # Frecuencia de muestreo

    # Diseñar los filtros Butterworth
    fc = 0.1  # Frecuencia de corte (Hz)
    b, a = butter(2, fc / (Fs / 2), 'low')  # Filtro pasa bajas
    d, c = butter(2, fc / (Fs / 2), 'high')  # Filtro pasa altas

    # Inicializar ángulos de giroscopio previos para integrar
    int_gyr_ang_x = 0
    int_gyr_ang_y = 0
    int_gyr_ang_z = 0

    # Guardar ángulos para visualizar luego
    filt_ang = np.zeros((len(ax), 3))
    accel_ang = np.zeros((len(ax), 3))
    gyro_ang = np.zeros((len(ax), 3))
    mag_ang = np.zeros((len(ax), 3))

    # Inicializar listas para las líneas de seguimiento
    x_trail = []
    y_trail = []
    xr_trail = []
    yr_trail = []

    # Flag para inicialización del yaw UWB
    yaw_initialized = False

    # Loop para aplicar filtro y transformar coordenadas UWB
    for i in range(len(ax)):
        # Tomar valores actuales acc, gyro y mag
        accel_x = ax[i]
        accel_y = ay[i]
        accel_z = az[i]
        
        gyro_x = gx[i]
        gyro_y = gy[i]
        gyro_z = gz[i]
        
        mag_x = mx[i]
        mag_y = my[i]
        mag_z = mz[i]

        # Transformar coordenadas UWB a Robotat
        x[i] = -(x[i] / 1000 - 2.0)
        y[i] = -(y[i] / 1000 - 2.5)
        
        # Calcular tilt del acelerómetro
        accel_angle_x = np.rad2deg(np.arctan2(accel_y, np.sqrt(accel_x**2 + accel_z**2)))
        accel_angle_y = np.rad2deg(np.arctan2(-accel_x, np.sqrt(accel_y**2 + accel_z**2)))
        accel_angle_z = 0  # Ignorar z ya que queremos el tilt para correcciones
        
        # Guardar ángulos del acelerómetro
        accel_ang[i, :] = [accel_angle_x, accel_angle_y, accel_angle_z]
        
        # Integración de giroscopio
        int_gyr_ang_x += gyro_x * dt
        int_gyr_ang_y += gyro_y * dt
        int_gyr_ang_z += gyro_z * dt
        
        # Guardar ángulos del giroscopio
        gyro_ang[i, :] = [int_gyr_ang_x, int_gyr_ang_y, int_gyr_ang_z]
        
        # Calcular ángulo de yaw del magnetómetro
        mag_angle_z = np.rad2deg(np.arctan2(mag_y, mag_x))
        
        # Guardar ángulos del magnetómetro
        mag_ang[i, :] = [0, 0, mag_angle_z]

        # Inicializar yaw del UWB con el yaw del Robotat en la primera iteración
        if not yaw_initialized:
            int_gyr_ang_z = yr_robotat[i]  # Igualar el yaw del UWB al yaw del Robotat
            yaw_initialized = True

    # Aplicar el filtro pasa bajas a los ángulos del acelerómetro
    accel_angle_x_lpf = filtfilt(b, a, accel_ang[:, 0])
    accel_angle_y_lpf = filtfilt(b, a, accel_ang[:, 1])

    # Aplicar el filtro pasa altas a los ángulos del giroscopio integrado
    gyro_angle_x_hpf = filtfilt(d, c, gyro_ang[:, 0])
    gyro_angle_y_hpf = filtfilt(d, c, gyro_ang[:, 1])

    # Aplicar el filtro pasa bajas a los ángulos del magnetómetro
    mag_angle_z_lpf = filtfilt(b, a, mag_ang[:, 2])

    # Filtro complementario extendido
    filt_ang_x = gyro_angle_x_hpf + accel_angle_x_lpf
    filt_ang_y = gyro_angle_y_hpf + accel_angle_y_lpf
    filt_ang_z = gyro_ang[:, 2] * 0.98 + mag_angle_z_lpf * 0.02  # Filtro complementario para yaw

    # Guardar ángulos filtrados
    filt_ang[:, 0] = filt_ang_x
    filt_ang[:, 1] = filt_ang_y
    filt_ang[:, 2] = filt_ang_z

    # Variable de estado para animación
    is_paused = False

    # Función para actualizar la animación
    def update(i):
        if not is_paused:
            # Limpiar los ejes
            ax3d_UWB.cla()
            ax3d_Robotat.cla()
            ax_xy.cla()

            # Configurar la vista
            ax3d_UWB.view_init(elev=20., azim=30)
            ax3d_UWB.set_xlim([-1, 1])
            ax3d_UWB.set_ylim([-1, 1])
            ax3d_UWB.set_zlim([-1, 1])

            ax3d_Robotat.view_init(elev=20., azim=30)
            ax3d_Robotat.set_xlim([-1, 1])
            ax3d_Robotat.set_ylim([-1, 1])
            ax3d_Robotat.set_zlim([-1, 1])

            # Dibujar el marco de rotación UWB
            ax3d_UWB.quiver(0, 0, 0, 1, 0, 0, color='r', label='X (UWB)')
            ax3d_UWB.quiver(0, 0, 0, 0, 1, 0, color='g', label='Y (UWB)')
            ax3d_UWB.quiver(0, 0, 0, 0, 0, 1, color='b', label='Z (UWB)')

            # Dibujar el marco de rotación Robotat
            ax3d_Robotat.quiver(0, 0, 0, 1, 0, 0, color='orange', label='Xr (Robotat)')
            ax3d_Robotat.quiver(0, 0, 0, 0, 1, 0, color='purple', label='Yr (Robotat)')
            ax3d_Robotat.quiver(0, 0, 0, 0, 0, 1, color='cyan', label='Zr (Robotat)')

            # Obtener ángulos de rotación UWB
            angle_x_UWB = np.deg2rad(filt_ang[i, 0])
            angle_y_UWB = np.deg2rad(filt_ang[i, 1])
            angle_z_UWB = np.deg2rad(filt_ang[i, 2])

            # Matriz de rotación UWB
            R_UWB = np.array([[np.cos(angle_y_UWB) * np.cos(angle_z_UWB), -np.cos(angle_y_UWB) * np.sin(angle_z_UWB), np.sin(angle_y_UWB)],
                              [np.cos(angle_x_UWB) * np.sin(angle_z_UWB) + np.sin(angle_x_UWB) * np.sin(angle_y_UWB) * np.cos(angle_z_UWB),
                               np.cos(angle_x_UWB) * np.cos(angle_z_UWB) - np.sin(angle_x_UWB) * np.sin(angle_y_UWB) * np.sin(angle_z_UWB),
                               -np.sin(angle_x_UWB) * np.cos(angle_y_UWB)],
                              [np.sin(angle_x_UWB) * np.sin(angle_z_UWB) - np.cos(angle_x_UWB) * np.sin(angle_y_UWB) * np.cos(angle_z_UWB),
                               np.sin(angle_x_UWB) * np.cos(angle_z_UWB) + np.cos(angle_x_UWB) * np.sin(angle_y_UWB) * np.sin(angle_z_UWB),
                               np.cos(angle_x_UWB) * np.cos(angle_y_UWB)]])

            # Dibujar el marco de rotación transformado UWB
            ax3d_UWB.quiver(0, 0, 0, R_UWB[0, 0], R_UWB[1, 0], R_UWB[2, 0], color='r', linestyle='--')  # Eje X rotado UWB
            ax3d_UWB.quiver(0, 0, 0, R_UWB[0, 1], R_UWB[1, 1], R_UWB[2, 1], color='g', linestyle='--')  # Eje Y rotado UWB
            ax3d_UWB.quiver(0, 0, 0, R_UWB[0, 2], R_UWB[1, 2], R_UWB[2, 2], color='b', linestyle='--')  # Eje Z rotado UWB

            # Obtener el ángulo de yaw (yr) del Robotat
            angle_z_Robotat = np.deg2rad(yr_robotat[i])

            # Matriz de rotación Robotat (solo yaw)
            R_Robotat = np.array([[np.cos(angle_z_Robotat), -np.sin(angle_z_Robotat), 0],
                                  [np.sin(angle_z_Robotat),  np.cos(angle_z_Robotat), 0],
                                  [0, 0, 1]])

            # Dibujar el marco de rotación transformado Robotat
            ax3d_Robotat.quiver(0, 0, 0, R_Robotat[0, 0], R_Robotat[1, 0], R_Robotat[2, 0], color='orange', linestyle='--')  # Eje X rotado Robotat
            ax3d_Robotat.quiver(0, 0, 0, R_Robotat[0, 1], R_Robotat[1, 1], R_Robotat[2, 1], color='purple', linestyle='--')  # Eje Y rotado Robotat
            ax3d_Robotat.quiver(0, 0, 0, R_Robotat[0, 2], R_Robotat[1, 2], R_Robotat[2, 2], color='cyan', linestyle='--')  # Eje Z rotado Robotat

            ax3d_UWB.legend()
            ax3d_Robotat.legend()

            # Agregar el punto actual a la línea de seguimiento
            x_trail.append(x[i])
            y_trail.append(y[i])
            xr_trail.append(xr[i])
            yr_trail.append(yr[i])

            # Dibujar x, y del UWB y Robotat superpuestos con líneas de seguimiento
            ax_xy.plot(x_trail, y_trail, c='r', label='UWB', linestyle='-', marker='o')
            ax_xy.plot(xr_trail, yr_trail, c='b', label='Robotat', linestyle='-', marker='x')

            # Definir límites específicos para el plot `xy`
            ax_xy.set_xlim([-2.0, 2.0])
            ax_xy.set_ylim([-2.5, 2.5])

            ax_xy.set_xlabel('x (metros)')
            ax_xy.set_ylabel('y (metros)')
            ax_xy.legend()

            # Mostrar número de muestras y tiempo en segundos
            time_elapsed = i * dt
            ax3d_UWB.text2D(0.05, 0.95, f'Muestra: {i+1}, Tiempo: {time_elapsed:.2f} s', transform=ax3d_UWB.transAxes)
            ax3d_Robotat.text2D(0.05, 0.95, f'Muestra: {i+1}, Tiempo: {time_elapsed:.2f} s', transform=ax3d_Robotat.transAxes)

    # Función para pausar/continuar la animación
    def on_key(event):
        global is_paused
        if event.key == ' ':
            is_paused = not is_paused

    # Crear la figura y los ejes 3D para UWB y Robotat
    fig = plt.figure()
    ax3d_UWB = fig.add_subplot(221, projection='3d')
    ax3d_Robotat = fig.add_subplot(222, projection='3d')
    ax_xy = fig.add_subplot(212)

    # Vincular la función de manejo de teclas
    fig.canvas.mpl_connect('key_press_event', on_key)

    # Crear la animación
    ani = FuncAnimation(fig, update, frames=len(ax), interval=dt * 1000)

    # Mostrar la animación
    plt.show()

except FileNotFoundError:
    print("El archivo no se encontró. Verifique la ruta del archivo y vuelva a intentarlo.")
