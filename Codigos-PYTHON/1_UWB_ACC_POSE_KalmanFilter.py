# -------------------------------------------------------------------------------------------------
# Autor: Alfredo Melendez
# Version: 0.1
# 
# Descripcion: Este código lee un dataset al igual que la V0.0 , se probó realizar el filtro de 
# kalman, cabe destacar que esta no fue la version final y fue de prueba ya que es en dos
# dimensiones y no se tuvo el comportamiento esperado. Sin embargo se pueden modificar valores para
# realizar pruebas, aunque no es del todo recomendable trabajar esta versión. Se trabajan filtros
# complementarios en esta version
#
# 
# -------------------------------------------------------------------------------------------------

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from scipy.linalg import block_diag

# Leer el archivo CSV
data = pd.read_csv('Test2_xy_acc_gyr_mag.csv')

# Obtener los valores de las columnas
uwb_x = data['x'].values
uwb_y = data['y'].values
ax = data['ax'].values * 9.81  # Convertir a m/s^2
ay = data['ay'].values * 9.81  # Convertir a m/s^2
az = data['az'].values * 9.81  # Convertir a m/s^2
gx = np.deg2rad(data['gx'].values)  # Convertir a rad/s
gy = np.deg2rad(data['gy'].values)  # Convertir a rad/s
gz = np.deg2rad(data['gz'].values)  # Convertir a rad/s

# Inicializar parámetros
dt = 0.1  # Intervalo de muestreo (10 Hz)
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

# Loop para aplicar filtro
for i in range(len(ax)):
    # Tomar valores actuales acc y gyro
    accel_x = ax[i]
    accel_y = ay[i]
    accel_z = az[i]
    
    gyro_x = gx[i]
    gyro_y = gy[i]
    gyro_z = gz[i]
    
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

# Aplicar el filtro pasa bajas a los ángulos del acelerómetro
accel_angle_x_lpf = filtfilt(b, a, accel_ang[:, 0])
accel_angle_y_lpf = filtfilt(b, a, accel_ang[:, 1])

# Aplicar el filtro pasa altas a los ángulos del giroscopio integrado
gyro_angle_x_hpf = filtfilt(d, c, gyro_ang[:, 0])
gyro_angle_y_hpf = filtfilt(d, c, gyro_ang[:, 1])

# Filtro complementario
filt_ang_x = gyro_angle_x_hpf + accel_angle_x_lpf
filt_ang_y = gyro_angle_y_hpf + accel_angle_y_lpf
filt_ang_z = gyro_ang[:, 2]  # Usar solo giroscopio para yaw

# Guardar ángulos filtrados
filt_ang[:, 0] = filt_ang_x
filt_ang[:, 1] = filt_ang_y
filt_ang[:, 2] = filt_ang_z

# Inicializar el filtro de Kalman para posición
Q_pos = block_diag(np.eye(2) * 0.1, np.eye(2) * 0.1)  # Matriz de ruido del proceso
R_pos = np.eye(2) * 1  # Matriz de ruido de la medida (10 cm de precisión UWB)
H_pos = np.eye(2, 4)  # Matriz de observación

# Estado inicial
x_pos = np.zeros(4)  # Estado [pos_x, pos_y, vel_x, vel_y]
P_pos = np.eye(4)  # Covarianza del estado

# Listas para almacenar resultados
positions = []

# Loop para aplicar el filtro de Kalman para la posición
for i in range(len(ax)):
    # Predicción del estado (doble integración del acelerómetro)
    F_pos = np.eye(4)
    F_pos[0, 2] = dt
    F_pos[1, 3] = dt
    x_pos = F_pos.dot(x_pos)
    x_pos[2] += ax[i] * dt
    x_pos[3] += ay[i] * dt
    P_pos = F_pos.dot(P_pos).dot(F_pos.T) + Q_pos

    # Medida (UWB)
    z_pos = np.array([uwb_x[i], uwb_y[i]])

    # Actualización
    y_pos = z_pos - H_pos.dot(x_pos)
    S_pos = H_pos.dot(P_pos).dot(H_pos.T) + R_pos
    K_pos = P_pos.dot(H_pos.T).dot(np.linalg.inv(S_pos))
    x_pos = x_pos + K_pos.dot(y_pos)
    P_pos = (np.eye(4) - K_pos.dot(H_pos)).dot(P_pos)

    # Almacenar posición
    positions.append(x_pos[:2])

# Convertir listas a arrays para facilitar el manejo
positions = np.array(positions)

# Guardar resultados en un archivo CSV
output_data = np.hstack((filt_ang, positions))
output_df = pd.DataFrame(output_data, columns=['angle_x', 'angle_y', 'angle_z', 'pos_x', 'pos_y'])
output_df.to_csv('output_navigation.csv', index=False)
print("Archivo output_navigation.csv guardado con éxito.")

# Animación
fig = plt.figure(figsize=(12, 6))

# Subplot para orientación
ax1 = fig.add_subplot(121, projection='3d')
ax1.set_title('Orientación')
ax1.set_xlim([-90, 90])
ax1.set_ylim([-90, 90])
ax1.set_zlim([-90, 90])
ax1.set_xlabel('X')
ax1.set_ylabel('Y')
ax1.set_zlabel('Z')

# Subplot para posición
ax2 = fig.add_subplot(122)
ax2.set_title('Posición')
ax2.set_xlim([min(uwb_x), max(uwb_x)])
ax2.set_ylim([min(uwb_y), max(uwb_y)])
ax2.set_xlabel('Posición X (m)')
ax2.set_ylabel('Posición Y (m)')

def update(i):
    # Limpiar ejes
    ax1.cla()
    ax2.cla()

    # Configurar ejes de orientación
    ax1.set_title('Orientación')
    ax1.set_xlim([-1.5, 1.5])
    ax1.set_ylim([-1.5, 1.5])
    ax1.set_zlim([-1.5, 1.5])
    ax1.set_xlabel('X')
    ax1.set_ylabel('Y')
    ax1.set_zlabel('Z')

    # Configurar ejes de posición
    ax2.set_title('Posición')
    ax2.set_xlim([min(uwb_x), max(uwb_x)])
    ax2.set_ylim([min(uwb_y), max(uwb_y)])
    ax2.set_xlabel('Posición X (m)')
    ax2.set_ylabel('Posición Y (m)')

    # Dibujar orientación
    angle_x = np.deg2rad(filt_ang[i, 0])
    angle_y = np.deg2rad(filt_ang[i, 1])
    angle_z = np.deg2rad(filt_ang[i, 2])
    R = np.array([[np.cos(angle_y) * np.cos(angle_z), -np.cos(angle_y) * np.sin(angle_z), np.sin(angle_y)],
                  [np.cos(angle_x) * np.sin(angle_z) + np.sin(angle_x) * np.sin(angle_y) * np.cos(angle_z),
                   np.cos(angle_x) * np.cos(angle_z) - np.sin(angle_x) * np.sin(angle_y) * np.sin(angle_z),
                   -np.sin(angle_x) * np.cos(angle_y)],
                  [np.sin(angle_x) * np.sin(angle_z) - np.cos(angle_x) * np.sin(angle_y) * np.cos(angle_z),
                   np.sin(angle_x) * np.cos(angle_z) + np.cos(angle_x) * np.sin(angle_y) * np.sin(angle_z),
                   np.cos(angle_x) * np.cos(angle_y)]])
    ax1.quiver(0, 0, 0, 1, 0, 0, color='r', linestyle='--', length=1.5)  # Eje X
    ax1.quiver(0, 0, 0, 0, 1, 0, color='g', linestyle='--', length=1.5)  # Eje Y
    ax1.quiver(0, 0, 0, 0, 0, 1, color='b', linestyle='--', length=1.5)  # Eje Z
    ax1.quiver(0, 0, 0, R[0, 0], R[1, 0], R[2, 0], color='r', length=1.5)  # Eje X rotado
    ax1.quiver(0, 0, 0, R[0, 1], R[1, 1], R[2, 1], color='g', length=1.5)  # Eje Y rotado
    ax1.quiver(0, 0, 0, R[0, 2], R[1, 2], R[2, 2], color='b', length=1.5)  # Eje Z rotado

    # Dibujar posición
    ax2.plot(positions[:i+1, 0], positions[:i+1, 1], 'r-')
    ax2.scatter(positions[i, 0], positions[i, 1], c='b', marker='o')

ani = FuncAnimation(fig, update, frames=len(ax), interval=dt*1000)
plt.show()
