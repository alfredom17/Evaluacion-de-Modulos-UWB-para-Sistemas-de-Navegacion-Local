# -------------------------------------------------------------------------------------------------
# Autor: Alfredo Melendez
# Version: 0.0
# 
# Descripcion: Este código lee un archivo .csv con el cual se extrae la data de posicion,
# aceleracion, giroscopio y magnetómetro para visualizar los movimientos de la trayectoria del
# DWM1001 + MPU9250
#
# * Esta versión es funcional, se debe recolectar primero un dataset, y dentro de la misma carpeta
#   que este codigo se debe ejecutar, sino colocar la ruta del archivo y extraer los valores
# * Tomar en cuenta que en este codigo las columnas ya tienen un nombre asignado, esto cambia
#   para otras versiones.
# -------------------------------------------------------------------------------------------------
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D

# Leer el archivo CSV
try:
    data = pd.read_csv('TestPCB_xy_acc_gyr_mag.csv') # NOMBRE O RUTA DEL ARCHIVO

    # Obtener los valores de las columnas
    x = data['x'].values
    y = data['y'].values
    ax = data['ax'].values
    ay = data['ay'].values
    az = data['az'].values
    gx = data['gx'].values
    gy = data['gy'].values
    gz = data['gz'].values
    mx = data['mx'].values
    my = data['my'].values
    mz = data['mz'].values

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

    # Loop para aplicar filtro
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
            ax3d.cla()  # Limpiar el eje

            # Configurar la vista
            ax3d.view_init(elev=20., azim=30)
            ax3d.set_xlim([-1, 1])
            ax3d.set_ylim([-1, 1])
            ax3d.set_zlim([-1, 1])

            # Dibujar el marco de rotación
            ax3d.quiver(0, 0, 0, 1, 0, 0, color='r', label='X')  # Eje X
            ax3d.quiver(0, 0, 0, 0, 1, 0, color='g', label='Y')  # Eje Y
            ax3d.quiver(0, 0, 0, 0, 0, 1, color='b', label='Z')  # Eje Z

            # Obtener ángulos de rotación
            angle_x = np.deg2rad(filt_ang[i, 0])
            angle_y = np.deg2rad(filt_ang[i, 1])
            angle_z = np.deg2rad(filt_ang[i, 2])

            # Matriz de rotación
            R = np.array([[np.cos(angle_y) * np.cos(angle_z), -np.cos(angle_y) * np.sin(angle_z), np.sin(angle_y)],
                          [np.cos(angle_x) * np.sin(angle_z) + np.sin(angle_x) * np.sin(angle_y) * np.cos(angle_z),
                           np.cos(angle_x) * np.cos(angle_z) - np.sin(angle_x) * np.sin(angle_y) * np.sin(angle_z),
                           -np.sin(angle_x) * np.cos(angle_y)],
                          [np.sin(angle_x) * np.sin(angle_z) - np.cos(angle_x) * np.sin(angle_y) * np.cos(angle_z),
                           np.sin(angle_x) * np.cos(angle_z) + np.cos(angle_x) * np.sin(angle_y) * np.sin(angle_z),
                           np.cos(angle_x) * np.cos(angle_y)]])

            # Dibujar el marco de rotación transformado
            ax3d.quiver(0, 0, 0, R[0, 0], R[1, 0], R[2, 0], color='r', linestyle='--')  # Eje X rotado
            ax3d.quiver(0, 0, 0, R[0, 1], R[1, 1], R[2, 1], color='g', linestyle='--')  # Eje Y rotado
            ax3d.quiver(0, 0, 0, R[0, 2], R[1, 2], R[2, 2], color='b', linestyle='--')  # Eje Z rotado

            ax3d.legend()

            # Mostrar número de muestras y tiempo en segundos
            time_elapsed = i * dt
            ax3d.text2D(0.05, 0.95, f'Muestra: {i+1}, Tiempo: {time_elapsed:.2f} s', transform=ax3d.transAxes)
            
            # Dibujar x, y
            ax_xy.scatter(x[i], y[i], c='r', marker='o')
            ax_xy.set_xlim([min(x), max(x)])
            ax_xy.set_ylim([min(y), max(y)])
            ax_xy.set_xlabel('x')
            ax_xy.set_ylabel('y')

    # Función para pausar/continuar la animación
    def on_key(event):
        global is_paused
        if event.key == ' ':
            is_paused = not is_paused

    # Crear la figura y el eje 3D
    fig = plt.figure()
    ax3d = fig.add_subplot(121, projection='3d')
    ax_xy = fig.add_subplot(122)

    # Vincular la función de manejo de teclas
    fig.canvas.mpl_connect('key_press_event', on_key)

    # Crear la animación
    ani = FuncAnimation(fig, update, frames=len(ax), interval=dt * 1000)

    # Mostrar la animación
    plt.show()

except FileNotFoundError:
    print("El archivo no se encontró. Verifique la ruta del archivo y vuelva a intentarlo.")
