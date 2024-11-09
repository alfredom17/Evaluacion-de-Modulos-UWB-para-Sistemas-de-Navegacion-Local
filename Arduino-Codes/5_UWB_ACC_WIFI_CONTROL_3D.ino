/*
Version: 0.5

Comentarios de version:
**************************************************************************************************************
-> Se agregó una dimensión más al sistema de captura de UWB para ser 3D

**************************************************************************************************************

Author: Alfredo Andres Meléndez

Acerca de:
Código para obtención de datos para sistema de captura de movimiento en 3D

Este código proporciona obtención y envío de datos mediante protocolos UART, I2C, Wi-Fi TCP
para obtener datos crudos de los siguientes módulos.

MICRO:

-> DOIT DevKit V1 ESP32

MÓDULOS:

-> MDEK1001 UWB, de Qorvo -> DATA: posición x,y
-> MPU9250 -> DATA: ax,ay,az,gx,gy,gz,mx,my,mz | Si es el módulo GY91 se puede obtener información de barómetro
-> HC05 -> movimiento de motores con pines digitales.

Integración:
-> PCB

*/

// **************************************************************************************************************

// LIBRERIAS
#include <WiFi.h>
#include <Wire.h>
#include <MPU9250_asukiaaa.h>
#include <SoftwareSerial.h>

// CREDENCIALES DE RED
const char* ssid = "Robotat";
const char* password = "iemtbmcit116";

// CONFIGURACION DEL SERVIDOR WI-FI
WiFiServer server(80);
WiFiClient client;

// CONFIGURACION DE COMUNICACION CON MPU9250
MPU9250_asukiaaa mySensor;  // Usamos la librería MPU9250_asukiaaa
const int I2C_SDA = 21;
const int I2C_SCL = 22;

// COMUNICACION CON HC-05
#define RX_PIN 26
#define TX_PIN 25
SoftwareSerial hc05Serial(RX_PIN, TX_PIN);

// PINES DE CONTROL DE MOTORES
const int pinL1 = 13, pinL2 = 12, pinR1 = 14, pinR2 = 27;

// CONSTANTES DE TIEMPO
const long UWB_INTERVAL = 100;   // Intervalo de 10 Hz para UWB y MPU9250
unsigned long previousMillis = 0;

// VARIABLES PARA LECTURA DE MODULOS UWB
int32_t xCoord = 0, yCoord = 0, zCoord = 0;
const uint8_t bytesEsperados = 18;   // Actualizado a 19 bytes esperados
uint8_t datos[bytesEsperados];       // Arreglo para almacenar los datos leídos
uint8_t bytesRecibidos = 0;          // Contador de bytes recibidos
uint8_t uwbQuality = 0;              // Variable para el factor de calidad UWB

// Definir rangos válidos para las coordenadas xCoord y yCoord
const int32_t MIN_COORD = -10000;  // Valor mínimo permitido para coordenadas
const int32_t MAX_COORD = 10000;   // Valor máximo permitido para coordenadas

// Variables para los datos del MPU9250
float aX, aY, aZ, aSqrt, gX, gY, gZ, mX, mY, mZ, mDirection;

// Offsets del acelerómetro, giroscopio y magnetómetro
// Estos se obtienen del codigo de calibracion
float accelOffsetX = 0.28, accelOffsetY = -0.06, accelOffsetZ = 1.0 - 0.87;
float gyroOffsetX = -0.33, gyroOffsetY = -0.35, gyroOffsetZ = 1.14;
float magOffsetX = -20.75, magOffsetY = 70.66, magOffsetZ = 74.70;

// Configuración inicial
void setup() {
    // Puerto Serial
    Serial.begin(115200);
    Serial2.begin(115200, SERIAL_8N1, 16, 17);

    // Configuración de pines de motores
    pinMode(pinL1, OUTPUT);
    pinMode(pinL2, OUTPUT);
    pinMode(pinR1, OUTPUT);
    pinMode(pinR2, OUTPUT);

    // Conexión a WiFi
    connectToWiFi();
    
    // Iniciar servidor WiFi
    server.begin();

    // Inicializar MPU9250
    Wire.begin(I2C_SDA, I2C_SCL);  // Inicializar I2C con los pines correctos
    mySensor.setWire(&Wire);  // Configurar la instancia de Wire para el sensor

    mySensor.beginAccel(ACC_FULL_SCALE_2_G);  // Iniciar acelerómetro a escala de +/- 2g
    mySensor.beginGyro(GYRO_FULL_SCALE_250_DPS);   // Iniciar giroscopio a escala de +/- 250 dps
    mySensor.beginMag();    // Iniciar magnetómetro

    // Configuración HC-05
    hc05Serial.begin(9600);
}

// Bucle principal
void loop() {
    processHC05Commands();
    DataFetch_Send();
}

// Conexión a la red WiFi
void connectToWiFi() {
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Conectando a WiFi...");
    }
    Serial.println("Conectado a WiFi");
    Serial.print("ESP32 IP: ");
    Serial.println(WiFi.localIP());
}

// Enviar datos del UWB y MPU a través de TCP
void DataFetch_Send() {
    if (millis() - previousMillis >= UWB_INTERVAL) {
        previousMillis = millis();
        requestDataFromUWB();

        // Si hemos recibido suficientes bytes, procesamos los datos del UWB
        if (bytesRecibidos >= bytesEsperados) {
            processUWBData();
            
            // Descomentar para debug si hay overflow de datos ->
            // Verificar si las coordenadas están dentro de los límites válidos
            /*
            if (!isValidCoord(xCoord) || !isValidCoord(yCoord)) {
                Serial.println("Datos de UWB fuera de rango, reseteando coordenadas a 0.");
                xCoord = 0;
                yCoord = 0;
            }
            */

            sendDataToServer();  // Enviar los datos al servidor
        }
    }
}

// Función para verificar si la coordenada es válida
bool isValidCoord(int32_t coord) {
    return (coord >= MIN_COORD && coord <= MAX_COORD);
}

// Solicitar datos al UWB
void requestDataFromUWB() {
    Serial2.write(0x02);  // Comando para solicitar datos al UWB -> chequear API de UWB para solicitar 0x02 0x00
    Serial2.write(0x00);  
    while (Serial2.available() > 0 && bytesRecibidos < bytesEsperados) {
        datos[bytesRecibidos++] = Serial2.read();
    }
}

// Procesar datos UWB
// Hacemos Shift de datos y formateamos para decodificar el little endian.
void processUWBData() {
    xCoord = ((int32_t)datos[8] << 24) | ((int32_t)datos[7] << 16) | ((int32_t)datos[6] << 8) | datos[5];
    yCoord = ((int32_t)datos[12] << 24) | ((int32_t)datos[11] << 16) | ((int32_t)datos[10] << 8) | datos[9];
    zCoord = ((int32_t)datos[16] << 24) | ((int32_t)datos[15] << 16) | ((int32_t)datos[14] << 8) | datos[13];
    uwbQuality = datos[17];  // El último byte es el factor de calidad
    bytesRecibidos = 0;
    //Serial.println(uwbQuality);
}

// Enviar datos a través de TCP
void sendDataToServer() {
    // Actualizar los datos del MPU9250
    if (mySensor.accelUpdate() == 0 && mySensor.gyroUpdate() == 0 && mySensor.magUpdate() == 0) {
        // Leer los valores del acelerómetro, giroscopio y magnetómetro con offsets aplicados
        aX = mySensor.accelX() - accelOffsetX;
        aY = mySensor.accelY() - accelOffsetY;
        aZ = mySensor.accelZ() - accelOffsetZ;

        gX = mySensor.gyroX() - gyroOffsetX;
        gY = mySensor.gyroY() - gyroOffsetY;
        gZ = mySensor.gyroZ()- gyroOffsetZ ;

        mX = mySensor.magX();
        mY = mySensor.magY();
        mZ = mySensor.magZ();
        mDirection = mySensor.magHorizDirection();  // Dirección horizontal del magnetómetro (sin offset)

        // Enviar los datos corregidos y el factor de calidad
        String data = String(xCoord) + "," + String(yCoord) + "," + String(zCoord) + "," + String(uwbQuality) + ",";        
        data += String(aX, 2) + "," + String(aY, 2) + "," + String(aZ, 2) + ",";
        data += String(gX, 2) + "," + String(gY, 2) + "," + String(gZ, 2) + ",";
        data += String(mX, 2) + "," + String(mY, 2) + "," + String(mZ, 2) + "\n";


        // Descomentar para ver que se imprima bien
        //Serial.println("Datos: " + data);

        if (client.connected()) {
            client.print(data);
        } else {
            client = server.available();
        }
    } else {
        Serial.println("Error al actualizar los valores del MPU9250."); // Aca nos aseguramos que el MPU si nos este mandando datos
    }
}

// Leemos y procesamos comandos del HC-05
void processHC05Commands() {
    if (hc05Serial.available()) {
        handleCommand(hc05Serial.read());
    }
}

// Manejar comandos recibidos para pines logicos del motor
void handleCommand(char command) {
    switch (command) {
        case 'B': moveBack(); break;
        case 'F': moveForward(); break;
        case 'R': moveRight(); break;
        case 'L': moveLeft(); break;
        case 'S': stopMovement(); break;
        default: stopMovement(); break;
    }
}

// Control de movimiento
void moveBack()    { controlMotors(HIGH, LOW, HIGH, LOW); }
void moveForward() { controlMotors(LOW, HIGH, LOW, HIGH); }
void moveRight()   { controlMotors(LOW, HIGH, HIGH, LOW); }
void moveLeft()    { controlMotors(HIGH, LOW, LOW, HIGH); }
void stopMovement(){ controlMotors(LOW, LOW, LOW, LOW); }

void controlMotors(int l1, int l2, int r1, int r2) {
    digitalWrite(pinL1, l1);
    digitalWrite(pinL2, l2);
    digitalWrite(pinR1, r1);
    digitalWrite(pinR2, r2);
}
