#include <WiFi.h>
#include <Wire.h>
#include "MPU9250.h"

// Credenciales de Red para ROBOTAT UVG - CIT 116
const char* ssid = "Robotat";
const char* password = "iemtbmcit116";

// Configuracion del servidor
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

void setup() {
    Serial.begin(115200);
    Serial2.begin(115200, SERIAL_8N1, 16, 17);  // RX2, TX2, COMUNICACION CON MDEK1001

    // Conexion a Wi-Fi
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

    Serial.println("Esperando conexion DWM 20 secs");
    delay(5000);
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
}

void loop() {
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

        // Convertimos bytes a long para x, y en Centimetros
        if (bytesRecibidos >= bytesEsperados) {
            xCoord = ((long)datos[8] << 24) | ((long)datos[7] << 16) | ((long)datos[6] << 8) | datos[5];
            yCoord = ((long)datos[12] << 24) | ((long)datos[11] << 16) | ((long)datos[10] << 8) | datos[9];

            // Reiniciamos el contador luego de procesar
            bytesRecibidos = 0;
      
            // Imprimimos coordenadas
            Serial.print("X: ");
            Serial.print(xCoord);
            Serial.print(" Y: ");
            Serial.println(yCoord);

            // Actualizamos los datos del MPU9250
            mpu.update();

            // Preparamos los datos para enviar mediante TCP
            String data = String(xCoord) + "," + String(yCoord) + ",";
            data += String(mpu.getAccX()) + "," + String(mpu.getAccY()) + "," + String(mpu.getAccZ()) + ",";
            data += String(mpu.getGyroX()) + "," + String(mpu.getGyroY()) + "," + String(mpu.getGyroZ()) + ",";
            data += String(mpu.getMagX()) + "," + String(mpu.getMagY()) + "," + String(mpu.getMagZ()) + "\n";

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
