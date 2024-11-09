#include <WiFi.h>
#include <Wire.h>
#include "MPU9250.h"
#include <SoftwareSerial.h>

// Credenciales de Red para ROBOTAT UVG - CIT 116
const char* ssid = "Robotat";
const char* password = "iemtbmcit116";

//const char* ssid = "Familiamm2024";
//const char* password = "familiamm2022";

//const char* ssid = "Alf_Phone";
//const char* password = "fetuccini177";

// Configuración del servidor WiFi
WiFiServer server(80);
WiFiClient client;

// Configuración de comunicación con MPU9250
MPU9250 mpu;
const int I2C_SDA = 21;
const int I2C_SCL = 22;

// Comunicación con HC-05
#define RX_PIN 26
#define TX_PIN 25
SoftwareSerial hc05Serial(RX_PIN, TX_PIN);

// Pines para control de motores
const int pinL1 = 13, pinL2 = 12, pinR1 = 14, pinR2 = 27;

// Constantes de tiempo
const long UWB_INTERVAL = 100;   // Intervalo de 10 Hz para UWB y MPU9250
const long MAG_INTERVAL = 10;    // Intervalo de 100 Hz para magnetómetro

// Variables de tiempo y coordenadas
unsigned long previousMillis = 0;
unsigned long previousMagMillis = 0;
int32_t xCoord = 0, yCoord = 0; 
float magX = 0, magY = 0, magZ = 0;

// Variables para la lectura de datos del UWB
const uint8_t bytesEsperados = 18;   // Cantidad de bytes que se esperan leer
uint8_t datos[bytesEsperados];       // Arreglo para almacenar los datos leídos
uint8_t bytesRecibidos = 0;          // Contador de bytes recibidos

// Declinacion magnetica Guatemala
float declinationAngle = 0.2333;  // 0° 14' -> 0.2333 grados

// Configuración inicial
void setup() {
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
    setupMPU9250();

    // Configuración HC-05
    hc05Serial.begin(9600);
}

// Bucle principal
void loop() {
    sampleMagnetometer();
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

// Configuración de MPU9250
void setupMPU9250() {
    Wire.begin(I2C_SDA, I2C_SCL);
    delay(2000);
    if (!mpu.setup(0x68)) { 
        Serial.println("Error en la conexión con el MPU9250.");
        while (1) delay(1000);
    }
}

// Muestreo del magnetómetro
void sampleMagnetometer() {
    if (millis() - previousMagMillis >= MAG_INTERVAL) {
        previousMagMillis = millis();
        mpu.update();
        magX = mpu.getMagX();
        magY = mpu.getMagY();
        magZ = mpu.getMagZ();
    }
}

// Enviar datos del UWB y MPU a través de TCP
void DataFetch_Send() {
    if (millis() - previousMillis >= UWB_INTERVAL) {
        previousMillis = millis();
        requestDataFromUWB();
        if (bytesRecibidos >= bytesEsperados) {
            processUWBData();
            sendDataToClient();
        }
    }
}

// Solicitar datos al UWB
void requestDataFromUWB() {
    Serial2.write(0x02);
    Serial2.write(0x00);
    while (Serial2.available() > 0 && bytesRecibidos < bytesEsperados) {
        datos[bytesRecibidos++] = Serial2.read();
    }
}

// Procesar datos UWB
void processUWBData() {
    xCoord = ((int32_t)datos[8] << 24) | ((int32_t)datos[7] << 16) | ((int32_t)datos[6] << 8) | datos[5];
    yCoord = ((int32_t)datos[12] << 24) | ((int32_t)datos[11] << 16) | ((int32_t)datos[10] << 8) | datos[9];
    bytesRecibidos = 0;
}

// Enviar datos a través de TCP
void sendDataToClient() {
    String data = String(xCoord) + "," + String(yCoord) + ",";
    data += String(mpu.getAccX()) + "," + String(mpu.getAccY()) + "," + String(mpu.getAccZ()) + ",";
    data += String(mpu.getGyroX()) + "," + String(mpu.getGyroY()) + "," + String(mpu.getGyroZ()) + ",";
    data += String(magX/10.0) + "," + String(magY/10.0) + "," + String(magZ/10.0) + "\n";

    Serial.println("Datos: " + data);

    if (client.connected()) {
        client.print(data);
    } else {
        client = server.available();
    }
}

// Procesar comandos del HC-05
void processHC05Commands() {
    if (hc05Serial.available()) {
        handleCommand(hc05Serial.read());
    }
}

// Manejar comandos recibidos
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
