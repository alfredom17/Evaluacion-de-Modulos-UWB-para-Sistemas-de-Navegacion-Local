#include <WiFi.h>
#include <Wire.h>
#include "MPU9250.h"
#include <SoftwareSerial.h>

// Definir directiva de depuración
#define debugSerial

// Credenciales de Red para ROBOTAT UVG - CIT 116
//const char* ssid = "Robotat";
//const char* password = "iemtbmcit116";
const char* ssid = "Familiamm2024";
const char* password = "familiamm2022";
//const char* ssid = "Alf_Phone";
//const char* password = "fetuccini177";

// Configuración del servidor
WiFiServer server(80); // Puerto 80
WiFiClient client;

const int bytesEsperados = 18;
byte datos[bytesEsperados];  // Arreglo para los bytes esperados
int bytesRecibidos = 0;      // Contador para número de bytes recibidos

long xCoord = 0;
long yCoord = 0;
unsigned long previousMillis = 0;
const long interval = 100;  // Intervalo 10 Hz

MPU9250 mpu;

// Pines para el control de motores
const int pinL1 = 13;
const int pinL2 = 12;
const int pinR1 = 14;
const int pinR2 = 27;

// Comunicación con HC-05
#define rxPin 26
#define txPin 25
SoftwareSerial hc05Serial(rxPin, txPin);

// Variables para muestreo de magnetómetro
unsigned long previousMagMillis = 0;
const long magInterval = 10;  // Intervalo 100 Hz
float magX = 0, magY = 0, magZ = 0;

void setup() {
    Serial.begin(115200);
    Serial2.begin(115200, SERIAL_8N1, 16, 17);  // RX2, TX2, COMUNICACION CON MDEK1001

    // Configuración de pines para los motores
    pinMode(pinL1, OUTPUT);
    pinMode(pinL2, OUTPUT);
    pinMode(pinR1, OUTPUT);
    pinMode(pinR2, OUTPUT);

    // Conexión a Wi-Fi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Estableciendo Conexion Wi-Fi...");
    }
    Serial.println("Conectado a WiFi");

    // Print the IP address
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
    delay(2000);
  
    // Empezamos el servidor
    server.begin();

    Serial.println("Esperando conexion DWM 2 secs");
    delay(2000);
    Serial.println("Chequear conexion, sino rebootear");

    // Configuración del MPU9250
    Wire.begin();
    delay(2000);
    
    if (!mpu.setup(0x68)) { 
        while (1) {
            Serial.println("MPU connection failed. Please check your connection with `connection_check` example.");
            delay(5000);
        }
    }

    // Configuración del HC-05
    hc05Serial.begin(9600);  // Velocidad estándar para HC-05
}

void loop() {
    // Muestreo del magnetómetro a 100 Hz
    unsigned long currentMillis = millis();
    if (currentMillis - previousMagMillis >= magInterval) {
        previousMagMillis = currentMillis;

        // Actualizar y almacenar la lectura del magnetómetro
        mpu.update();
        magX = mpu.getMagX();
        magY = mpu.getMagY();
        magZ = mpu.getMagZ();
    }

    // Verificamos si hay datos disponibles desde el HC-05
    if (hc05Serial.available()) {
        char command = hc05Serial.read();
        handleCommand(command);
    }

    // Enviar datos a 10 Hz
    DataFetch_Send();
}

// FUNCIONES
void DataFetch_Send(){
    unsigned long currentMillis = millis();
  
    if (currentMillis - previousMillis >= interval) {
        previousMillis = currentMillis;

        // Enviar solicitud de datos al UWB
        Serial2.write(0x02);
        Serial2.write(0x00);

        // Leemos si hay datos disponibles y lo guardamos en el arreglo
        while (Serial2.available() > 0 && bytesRecibidos < bytesEsperados) {
            datos[bytesRecibidos++] = Serial2.read();
        }

        // Convertimos bytes a long para x, y en Centímetros
        if (bytesRecibidos >= bytesEsperados) {
            xCoord = ((long)datos[8] << 24) | ((long)datos[7] << 16) | ((long)datos[6] << 8) | datos[5];
            yCoord = ((long)datos[12] << 24) | ((long)datos[11] << 16) | ((long)datos[10] << 8) | datos[9];

            // Reiniciamos el contador luego de procesar
            bytesRecibidos = 0;

            // Preparamos los datos para enviar mediante TCP
            String data = String(xCoord) + "," + String(yCoord) + ",";
            data += String(mpu.getAccX()) + "," + String(mpu.getAccY()) + "," + String(mpu.getAccZ()) + ",";
            data += String(mpu.getGyroX()) + "," + String(mpu.getGyroY()) + "," + String(mpu.getGyroZ()) + ",";
            data += String(magX) + "," + String(magY) + "," + String(magZ) + "\n";

            Serial.print("Datos: ");
            Serial.println(data);

            // Enviamos mediante TCP
            if (client.connected()) {
                client.print(data);
            } else {
                // Chequeamos por cliente nuevo conectado
                client = server.available();
            }
        }
    }
}

// Manejo de comandos recibidos desde el HC-05
void handleCommand(char command) {
    switch (command) {
        case 'B':  // Atrás
            digitalWrite(pinL1, HIGH);
            digitalWrite(pinL2, LOW);
            digitalWrite(pinR1, HIGH);
            digitalWrite(pinR2, LOW);
            break;
        case 'F':  // Adelante
            digitalWrite(pinL1, LOW);
            digitalWrite(pinL2, HIGH);
            digitalWrite(pinR1, LOW);
            digitalWrite(pinR2, HIGH);
            break;
        case 'R':  // Derecha
            digitalWrite(pinL1, LOW);
            digitalWrite(pinL2, HIGH);
            digitalWrite(pinR1, HIGH);
            digitalWrite(pinR2, LOW);
            break;
        case 'L':  // Izquierda
            digitalWrite(pinL1, HIGH);
            digitalWrite(pinL2, LOW);
            digitalWrite(pinR1, LOW);
            digitalWrite(pinR2, HIGH);
            break;
        case 'S':  // Detener
            digitalWrite(pinL1, LOW);
            digitalWrite(pinL2, LOW);
            digitalWrite(pinR1, LOW);
            digitalWrite(pinR2, LOW);
            break;
        default:
            // Comando no reconocido, detener por seguridad
            digitalWrite(pinL1, LOW);
            digitalWrite(pinL2, LOW);
            digitalWrite(pinR1, LOW);
            digitalWrite(pinR2, LOW);
            break;
    }
}
