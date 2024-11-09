# -------------------------------------------------------------------------------------------------
# Autor: Alfredo Melendez
# Version: 0.3
#
# Tipo de código: obtención de datos y generación datasets
# 
# Descripcion: Esta versión funciona para poder obtener datos crudos y luego Post-Procesarlos
# en MATLAB. Hay dos opciones se puede obtener los datos en tiempo real como opción 1, ahora con
# opción 2 se puede obtener un número determinado de muestras para tener más control. Con este
# código generamos datasets de .csv obteniendo todos los datos que nos puede dar DWM1001 como
# posición y factor de calidad, también los 9 DOF del MPU9250 y el cuaternión del sistema Optitrack
#
#  
# -------------------------------------------------------------------------------------------------

import socket
import time
import csv
import json
import numpy as np
import keyboard  # Necesario para detectar teclas (requiere instalar el módulo keyboard)
import os  # Para manejar los directorios y rutas de archivos

# Conexión y funciones de obtención de datos del ESP32
def esp32_connect(ip, port):
    try:
        tcp_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_obj.connect((ip, port))
        print('Conectado al servidor ESP32-UWB.')
        return tcp_obj
    except Exception as e:
        print(f'ERROR: No se pudo conectar al servidor ESP32-UWB: {e}')
        return None

def esp32_get_pose(tcp_obj):
    if tcp_obj is None:
        raise ValueError('El objeto TCP está vacío. Conectarse al ESP32 primero.')

    data_esp32 = []
    data = tcp_obj.recv(1024)
    if data:
        data_str = data.decode('utf-8').strip()
        lines = data_str.split('\n')
        for line in lines:
            try:
                values = [float(val) for val in line.split(',')]
                if len(values) == 12: #recibimos 12 valores, esto porque se agrego el factor de calidad de medicion del UWB
                    data_esp32.append(values)
                    break
            except ValueError:
                continue
    return data_esp32

def esp32_disconnect(tcp_obj):
    if tcp_obj is not None:
        tcp_obj.close()
        print('Desconectado del servidor ESP32-UWB.')

# Conexión y funciones de obtención de datos del Robotat
def robotat_connect(ip='192.168.50.200', port=1883):
    try:
        tcp_obj = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_obj.connect((ip, port))
        print('Conectado al servidor Robotat.')
        return tcp_obj
    except Exception as e:
        print(f'ERROR: No se pudo conectar al servidor Robotat: {e}')
        return None

def robotat_disconnect(tcp_obj):
    if tcp_obj is not None:
        try:
            tcp_obj.sendall(b'EXIT')
            print('Desconectado del servidor Robotat.')
        finally:
            tcp_obj.close()
    else:
        print('ERROR: No se pudo desconectar porque no hay conexión activa.')

def q2eul(q, seq='xyz'):
    """Convierte un cuaternión en ángulos de Euler según la secuencia proporcionada."""
    q0, q1, q2, q3 = q
    if seq == 'xyz':
        sinr_cosp = 2 * (q0 * q1 + q2 * q3)
        cosr_cosp = 1 - 2 * (q1 * q1 + q2 * q2)
        roll = np.degrees(np.arctan2(sinr_cosp, cosr_cosp))

        sinp = 2 * (q0 * q2 - q3 * q1)
        if abs(sinp) >= 1:
            pitch = np.degrees(np.sign(sinp) * np.pi / 2)  # Gimbal lock
        else:
            pitch = np.degrees(np.arcsin(sinp))

        siny_cosp = 2 * (q0 * q3 + q1 * q2)
        cosy_cosp = 1 - 2 * (q2 * q2 + q3 * q3)
        yaw = np.degrees(np.arctan2(siny_cosp, cosy_cosp))

        return roll, pitch, yaw
    else:
        raise ValueError('Invalid Euler angle sequence.')

def robotat_get_pose(tcp_obj, agents_ids, rotrep='xyz'):
    if tcp_obj is None:
        raise ValueError('El objeto TCP está vacío. Conectarse al Robotat primero.')

    s = {
        "dst": 1,  # DST_ROBOTAT
        "cmd": 1,  # CMD_GET_POSE
        "pld": agents_ids
    }

    try:
        tcp_obj.sendall(json.dumps(s).encode('utf-8'))
        data = tcp_obj.recv(1024)
        if not data:
            print("ERROR: No se recibieron datos del servidor Robotat.")
            return None

        # Verificar si el mensaje es un JSON válido
        try:
            mocap_data = json.loads(data.decode('utf-8'))
            if not mocap_data:
                print("ERROR: Los datos del JSON están vacíos.")
                return None

            mocap_data = [mocap_data[i:i + 7] for i in range(0, len(mocap_data), 7)]

            for pose in mocap_data:
                position = pose[:3]
                quaternion = pose[3:7]  # Capturar los 4 elementos del cuaternión
                euler_angles = q2eul(quaternion, seq=rotrep)
                position_mm = [p * 1000 for p in position]  # Convertir XYZ a mm
                return list(position_mm) + list(euler_angles)

        except json.JSONDecodeError:
            # Si no es un JSON válido, solo lo ignoramos
            print(f'Datos no válidos recibidos del servidor Robotat: {data.decode("utf-8")}')
            return None

    except socket.error as e:
        print(f'Error de socket: {e}')
        return None

    return None

# Imprimir datos en tiempo real con formato fijo
def print_formatted_data(sample_num, timestamp, esp32_data, robotat_data):
    # Definir un formato fijo para que todos los números tengan el mismo ancho
    header_format = "| {:>10} | {:>10} |"
    esp32_format = "| {:>10.2f} | {:>10.2f} | {:>10.2f} | {:>10.2f} | {:>10.2f} | {:>10.2f} | {:>10.2f} | {:>10.2f} | {:>10.2f} | {:>10.2f} | {:>10.2f} | {:>10.2f} |"
    robotat_format = "| {:>10.2f} | {:>10.2f} | {:>10.2f} | {:>10.2f} | {:>10.2f} | {:>10.2f} |"
    
    # Imprimir número de muestra y tiempo de la muestra
    print(header_format.format(f"Sample {sample_num}", f"Time {timestamp:.0f} ms"))
    # Imprimir datos del ESP32 y Robotat con separadores "|"
    print(esp32_format.format(*esp32_data[0]))
    print(robotat_format.format(*robotat_data))
    print("-" * 144)  # Línea separadora

# Guardar datos en un archivo CSV
def save_data_to_csv(csv_writer, sample_num, timestamp, esp32_data, robotat_data):
    # Combinar los datos del ESP32 y Robotat
    combined_data = [sample_num, timestamp] + esp32_data[0] + robotat_data
    csv_writer.writerow(combined_data)

# Función para capturar datos hasta presionar una tecla
def capture_real_time(ESP32, Robotat, csv_writer):
    sample_num = 0
    start_time = time.perf_counter()

    while not keyboard.is_pressed('q'):  # Presiona "q" para detener
        sample_num += 1
        # Tiempo desde el inicio en milisegundos
        current_time = (time.perf_counter() - start_time) * 1000

        # Obtener datos del ESP32
        esp32_sample = esp32_get_pose(ESP32)
        # Obtener datos del Robotat
        robotat_sample = robotat_get_pose(Robotat, [20], 'xyz')

        if esp32_sample and robotat_sample:
            print_formatted_data(sample_num, current_time, esp32_sample, robotat_sample)
            save_data_to_csv(csv_writer, sample_num, current_time, esp32_sample, robotat_sample)

        time.sleep(0.1)  # Mantener frecuencia de 10 Hz

# Función para capturar un número fijo de muestras
def capture_fixed_samples(ESP32, Robotat, num_samples, csv_writer):
    start_time = time.perf_counter()

    for sample_num in range(1, num_samples + 1):
        # Tiempo desde el inicio en milisegundos
        current_time = (time.perf_counter() - start_time) * 1000

        # Obtener datos del ESP32
        esp32_sample = esp32_get_pose(ESP32)
        # Obtener datos del Robotat
        robotat_sample = robotat_get_pose(Robotat, [20], 'xyz')

        if esp32_sample and robotat_sample:
            print_formatted_data(sample_num, current_time, esp32_sample, robotat_sample)
            save_data_to_csv(csv_writer, sample_num, current_time, esp32_sample, robotat_sample)

        time.sleep(0.1)  # Mantener frecuencia de 10 Hz

# Función para crear y abrir el archivo CSV
def create_csv_file(directory, filename):
    # Crear el directorio si no existe
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    # Generar la ruta completa del archivo
    file_path = os.path.join(directory, filename + '.csv')
    
    # Crear el archivo CSV
    file = open(file_path, mode='w', newline='')
    csv_writer = csv.writer(file)
    
    # Escribir las cabeceras
    headers = ['Sample', 'Time (ms)', 'ESP32_X', 'ESP32_Y', 'UWB_QF','ESP32_Ax', 'ESP32_Ay', 'ESP32_Az',
               'ESP32_Gx', 'ESP32_Gy', 'ESP32_Gz', 'ESP32_Mx', 'ESP32_My', 'ESP32_Mz',
               'Robotat_X_mm', 'Robotat_Y_mm', 'Robotat_Z_mm', 'Robotat_Roll', 'Robotat_Pitch', 'Robotat_Yaw']
    csv_writer.writerow(headers)
    
    return file, csv_writer

# Ejecución principal
if __name__ == "__main__":
    # Conectar a ESP32
    esp32_ip = '192.168.50.225'
    esp32_port = 80
    ESP32 = esp32_connect(esp32_ip, esp32_port)

    # Conectar al Robotat
    robotat_ip = '192.168.50.200'
    robotat_port = 1883
    Robotat = robotat_connect(robotat_ip, robotat_port)

    if ESP32 and Robotat:
        # Solicitar directorio y nombre del archivo para guardar las muestras
        directory = input("Ingrese el directorio donde se guardará el archivo CSV: ")
        filename = input("Ingrese el nombre del archivo (sin extensión): ")

        # Crear el archivo CSV y el escritor
        csv_file, csv_writer = create_csv_file(directory, filename)

        try:
            # Mostrar menú
            print("Opciones:")
            print("1. Capturar datos en tiempo real (presione 'q' para salir)")
            print("2. Capturar un número fijo de muestras")
            option = input("Seleccione una opción (1 o 2): ")

            if option == '1':
                print("Captura de datos en tiempo real. Presione 'q' para detener.")
                capture_real_time(ESP32, Robotat, csv_writer)

            elif option == '2':
                num_samples = int(input("Ingrese el número de muestras que desea capturar: "))
                capture_fixed_samples(ESP32, Robotat, num_samples, csv_writer)

        finally:
            # Cerrar el archivo CSV al terminar
            csv_file.close()

    # Desconectar de ambos servidores
    esp32_disconnect(ESP32)
    robotat_disconnect(Robotat)
