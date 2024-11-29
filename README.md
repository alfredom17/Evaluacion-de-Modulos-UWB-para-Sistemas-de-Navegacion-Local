+![](GIFs/Navigation_Module.gif)

### Descripción

Este repositorio es producto del trabajo de graduación titulado "Evaluación de Módulos Ultra Wide Band (UWB) para Sistemas de Navegación Local" en el cual se busca resolver la problemática de la navegación que consiste en localización en 2D. Los módulos UWB (MDEK1001) de la empresa Qorvo son útiles para montar un sistema de localización, sin embargo la localización tiene precisión de +/- 100 mm y carecen de orientación. Haciendo uso de fusión de sensores de módulos MDEK1001 con una unidad de medición inercial (IMU) MPU9250 de 9 DOF, se mejora la precisión de los módulos por debajo de +/- 25 mm con filtros complementarios. La exactitud se mejora haciendo uso de un sistema de captura de movimiento Optitrack, en donde se toman puntos en paralelo del sistema UWB y Optitrack con la finalidad de corresponder puntos y hacer transormación por medio de Homografía proyectiva. Este estudio encontró porcentajes de error bajos alrededor de 5.5% de error en los ejes X y Y. Se realizaron pruebas dinámicas con trayectorias en paralelo UWB con Optitrack obteniendo R^2 superiores a 0.9 para ambos filtros complementarios. Dados los resultados se empleó una visualización en tiempo real con PyGame mediante Wi-Fi TCP. Adicional a los objetivos se agregó orientación al Módulo de Navegación (Fusión UWB con MPU9250 por medio de un DOIT Devkit V1 ESP32)

### Elementos usados

- DOIT Devkit V1 ESP32
- MPU9250
- MDEK1001 (Kit de 12 sensores o más)
- Placa PCB fabricada para colocar elementos
- Carro de pruebas para mantener LOS (Line of Sight)
- Sistema de captura Optitrack

### Características Principales

- Ejecución en tiempo real de fusión de sensores como DWM1001 (UWB), MPU9250 (IMU), utilizando un DOIT DevKit V1 ESP32.
- Fusión de sensores con filtros complementarios.
- Aplicación de homografía proyectiva para calibración y mapeo de un sistema de coordenadas UWB a un sistema de captura de cámaras Optitrack.

### Uso de Carpetas y archivos importantes

¿Para qué se usan los distintos lenguajes de programación?

- C++ -> Se utilizó en la IDE de ARDUINO para programar el ESP32 y obtener datos crudos de posición del MDEK1001 y el MPU9250 así como el control del carro.
- Python -> Se utilizó para obtención de datos mediante Wi-Fi TCP, generación de archivos .CSV de datos crudos, procesamiento y graficación en tiempo real.
- MATLAB -> Se utilizó para obtención de estadísticas y plots para validar el uso de filtro complementarios y homografía proyectiva.

Se muestra el siguiente diagrama de arquitectura de obtención y procesamiento de datos.
![Arquitectura de Proyecto](Fotos/DataFetch_Processing.jpg)



| Carpeta  | Descripción |
| ------------- | ------------- |
| Archivos-CAD | Contiene enclosure de MDEK1001 y piezas para ensamblaje de carro de pruebas, esto incluye todos los elementos como módulos o placas PCB utilizadas  |
| Códigos-ARDUINO  | Contiene iteraciones de código para lograr la obtención de datos crudos y envío de los mismos |

### Links

- [PCB](https://oshwlab.com/mel20310/uwb_mpu9250_esp32_integration)

- [Playlist Youtube](https://www.youtube.com/playlist?list=PLJCfE4ERlMfTEnHDD8o-vjXzkgCI-jniX)





