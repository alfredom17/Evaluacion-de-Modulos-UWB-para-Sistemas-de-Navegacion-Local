# -------------------------------------------------------------------------------------------------
# Autor: Alfredo Melendez
# Version: 0.5
#
# Tipo de código: obtención de datos 
#
#
# Descripción: -
# -------------------------------------------------------------------------------------------------

import socket
import time
import imufusion
import matplotlib.pyplot as plt
import numpy as np
from collections import deque
import threading

# Configuración de la conexión TCP
def esp32_connect(ip, port):
    try:
        tcp_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_obj.connect((ip, port))
        print(f"Conectado al ESP32 en {ip}:{port}")
        return tcp_obj
    except socket.error as e:
        print(f"Error al conectar al ESP32: {e}")
        return None

# Configuración de imufusion y frecuencia de muestreo
sample_rate = 100  # 100 Hz
ahrs = imufusion.Ahrs()

# Buffers para almacenar los datos en tiempo real
timestamp_buffer = deque(maxlen=500)
gyroscope_buffer = deque(maxlen=500)
accelerometer_buffer = deque(maxlen=500)
euler_buffer = deque(maxlen=500)

# Recibir y procesar datos del ESP32
def update_data(tcp_obj):
    start_time = time.time()
    
    try:
        while True:
            # Recibir datos del ESP32
            data = tcp_obj.recv(1024)
            if data:
                data_str = data.decode('utf-8').strip()
                lines = data_str.split('\n')
                
                for line in lines:
                    try:
                        values = [float(val) for val in line.split(',')]
                        
                        if len(values) >= 6:
                            # Extraer datos del giroscopio y acelerómetro
                            gx, gy, gz = values[0], values[1], values[2]
                            ax, ay, az = values[3], values[4], values[5]
                            
                            # Almacenar los datos en buffers
                            current_time = time.time() - start_time
                            timestamp_buffer.append(current_time)
                            gyroscope_buffer.append([gx, gy, gz])
                            accelerometer_buffer.append([ax, ay, az])
                            
                            # Actualizar AHRS y calcular los ángulos de Euler
                            gyroscope = np.array([gx, gy, gz], dtype=float)
                            accelerometer = np.array([ax, ay, az], dtype=float)
                            ahrs.update_no_magnetometer(gyroscope, accelerometer, 1 / sample_rate)
                            euler_angles = ahrs.quaternion.to_euler()
                            euler_buffer.append(euler_angles)
                            
                            # Imprimir datos para verificar
                            print(f"{current_time:.2f} | Gyro: {gx}, {gy}, {gz} | Accel: {ax}, {ay}, {az} | Euler: {euler_angles}")
                    except ValueError:
                        print("Error al convertir los valores, paquete inválido.")
                        continue
    except socket.error as e:
        print(f"Error de socket: {e}")
        tcp_obj.close()

# Graficar en tiempo real
def plot_real_time():
    plt.ion()
    fig, axes = plt.subplots(nrows=3, sharex=True, figsize=(10, 8))

    axes[0].set_title("Gyroscope")
    axes[0].set_ylabel("Degrees/s")
    axes[0].grid()
    
    axes[1].set_title("Accelerometer")
    axes[1].set_ylabel("g")
    axes[1].grid()
    
    axes[2].set_title("Euler angles")
    axes[2].set_xlabel("Seconds")
    axes[2].set_ylabel("Degrees")
    axes[2].grid()

    while True:
        if len(timestamp_buffer) > 1:
            timestamps = np.array(timestamp_buffer)
            gyroscope = np.array(gyroscope_buffer)
            accelerometer = np.array(accelerometer_buffer)
            euler = np.array(euler_buffer)

            # Graficar giroscopio
            axes[0].cla()
            axes[0].plot(timestamps, gyroscope[:, 0], "tab:red", label="X")
            axes[0].plot(timestamps, gyroscope[:, 1], "tab:green", label="Y")
            axes[0].plot(timestamps, gyroscope[:, 2], "tab:blue", label="Z")
            axes[0].legend()
            axes[0].grid()
            axes[0].set_title("Gyroscope")

            # Graficar acelerómetro
            axes[1].cla()
            axes[1].plot(timestamps, accelerometer[:, 0], "tab:red", label="X")
            axes[1].plot(timestamps, accelerometer[:, 1], "tab:green", label="Y")
            axes[1].plot(timestamps, accelerometer[:, 2], "tab:blue", label="Z")
            axes[1].legend()
            axes[1].grid()
            axes[1].set_title("Accelerometer")

            # Graficar ángulos de Euler
            axes[2].cla()
            axes[2].plot(timestamps, euler[:, 0], "tab:red", label="Roll")
            axes[2].plot(timestamps, euler[:, 1], "tab:green", label="Pitch")
            axes[2].plot(timestamps, euler[:, 2], "tab:blue", label="Yaw")
            axes[2].legend()
            axes[2].grid()
            axes[2].set_title("Euler angles")

            plt.pause(0.01)

# Bucle principal
if __name__ == "__main__":
    # Configuración de la IP y puerto del ESP32
    ip = '192.168.50.225'  # Cambia esto a la IP de tu ESP32
    port = 80              # Cambia esto al puerto que estás usando

    # Conectar al ESP32
    ESP32 = esp32_connect(ip, port)

    if ESP32:
        # Crear hilo para recibir y procesar los datos
        data_thread = threading.Thread(target=update_data, args=(ESP32,))
        data_thread.start()

        # Iniciar la visualización en tiempo real
        plot_real_time()
