% -------------------------------------------------------
% Autor: Alfredo Meléndez
%
% Descripción: Este código para comparar datos UWB crudos, corregidos por 
% homografía, y datos filtrados con Butterworth, con los
% datos de referencia del sistema Optitrack. Además se 
% incluye el acelerómetro para realizar un filtrado 
% complementario (LPF+HPF).
% -------------------------------------------------------
close all; clc; clear;
% Directorio de los archivos CSV de los datasets dinámicos
dynamicFile = 'D:\DATOS_TESIS\Datasets\Dinamico\MOV_PCB16_combined_data_DYNAMIC_R2.csv';

% Cargar la homografía previamente calculada
load('Homografia.mat', 'tform');
%robotat_get_pose(robotat,12,'xyz');
% Cargar los datos dinámicos con la regla de nombres de columnas preservada
data = readtable(dynamicFile, 'VariableNamingRule', 'preserve');

% Extraer las columnas necesarias
x = data.('ESP32_X');  % UWB en milímetros
y = data.('ESP32_Y');  % UWB en milímetros
xr = data.('Robotat_X_mm');  % Optitrack en milímetros
yr = data.('Robotat_Y_mm');  % Optitrack en milímetros

ax = data.('ESP32_Ax');  % Aceleración en X
ay = data.('ESP32_Ay');  % Aceleración en Y

% Acumular los puntos del sistema UWB y del Optitrack
movingPoints_dynamic = [x, y];  % Puntos dinámicos UWB
fixedPoints_dynamic = [xr, yr];  % Puntos dinámicos Optitrack

% Aplicar la homografía a los puntos UWB
movingPoints_dynamic_corrected = transformPointsForward(tform, movingPoints_dynamic);

% Parámetros de filtrado Butterworth
dt = 0.1;  % Intervalo de tiempo (100 ms)
Fs = 1 / dt;  % Frecuencia de muestreo

fc_lpf = 0.6;  % Frecuencia de corte para el filtro pasa bajas (LPF) para UWB
fc_hpf = 0.5;  % Frecuencia de corte para el filtro pasa altas (HPF) para acelerómetro

% Filtros Butterworth
[b_lpf, a_lpf] = butter(2, fc_lpf / (Fs / 2), 'low');  % Filtro pasa bajas
[d_hpf, c_hpf] = butter(2, fc_hpf / (Fs / 2), 'high');  % Filtro pasa altas

% Filtrado de datos UWB crudos
x_lpf = filtfilt(b_lpf, a_lpf, x);  % Aplicación del filtro LPF en x
y_lpf = filtfilt(b_lpf, a_lpf, y);  % Aplicación del filtro LPF en y

% Filtrado de datos UWB corregidos por homografía
x_corr_lpf = filtfilt(b_lpf, a_lpf, movingPoints_dynamic_corrected(:,1));  % Filtro LPF para X corregida
y_corr_lpf = filtfilt(b_lpf, a_lpf, movingPoints_dynamic_corrected(:,2));  % Filtro LPF para Y corregida

% Doble integración de acelerómetro con filtros HPF
vx = cumtrapz(ax * 1000 * 9.8) * dt;  % Integración de la aceleración para obtener velocidad
vy = cumtrapz(ay * 1000 * 9.8) * dt;

vx_hpf = filtfilt(d_hpf, c_hpf, vx);  % Filtrado HPF de la velocidad en x
vy_hpf = filtfilt(d_hpf, c_hpf, vy);  % Filtrado HPF de la velocidad en y

px_hpf = cumtrapz(vx_hpf) * dt;  % Integración de la velocidad para obtener posición
py_hpf = cumtrapz(vy_hpf) * dt;

% Filtrado HPF final en la posición
px_hpf_final = filtfilt(d_hpf, c_hpf, px_hpf);  % Filtrado HPF final en la posición x
py_hpf_final = filtfilt(d_hpf, c_hpf, py_hpf);  % Filtrado HPF final en la posición y

% Combinación de señales (LPF UWB crudo + HPF Acelerómetro)
x_final = x_lpf + px_hpf_final;
y_final = y_lpf + py_hpf_final;

% Combinación de señales (LPF UWB crudo + HPF Acelerómetro)
x_final_trans = x_corr_lpf + px_hpf_final;
y_final_trans = y_corr_lpf + py_hpf_final;

% Graficar los resultados
figure;
hold on;

% Cargar y superponer la imagen de fondo (Robotat)
%img = imread('Robotat.png');  % Cargar la imagen
xImage = [-2500 2500];  % Limites en X donde se ajustará la imagen (en milímetros)
yImage = [-2500 2500];  % Limites en Y donde se ajustará la imagen (en milímetros)
%imagesc(xImage, yImage, flipud(img));  % Superponer la imagen ajustada
%colormap gray;  % Opción para mostrar la imagen en escala de grises (opcional)
%set(gca,'YDir','normal');  % Asegurarse de que el eje Y está en la dirección correcta

% Graficar los puntos del Optitrack (en azul)
plot(fixedPoints_dynamic(:,1), fixedPoints_dynamic(:,2), 'b-', 'DisplayName', 'Optitrack','LineWidth',2);

% Graficar los puntos UWB crudos (en rojo)
plot(movingPoints_dynamic(:,1), movingPoints_dynamic(:,2), 'r--', 'DisplayName', 'UWB Crudo');

% Graficar los puntos UWB corregidos por homografía (en verde)
plot(movingPoints_dynamic_corrected(:,1), movingPoints_dynamic_corrected(:,2), 'g-', 'DisplayName', 'UWB Corregido','LineWidth',2);

% Graficar los puntos UWB corregidos filtrados (en magenta)
plot(x_final_trans, y_final_trans, 'm-', 'DisplayName', 'UWB Corregido Filtrado (LPF+HPF)','LineWidth',2);

% Graficar los puntos combinados con acelerómetro (en negro)
plot(x_final, y_final, 'k-', 'DisplayName', 'Filtrado Complementario (LPF+HPF)');

% Añadir etiquetas y leyenda
xlabel('X [mm]');
ylabel('Y [mm]');
title('Comparación entre UWB, Optitrack y Filtrado Complementario');
legend('show', 'Location', 'best');

% Ajustar límites y cuadrícula
axis equal;
xlim([-3000 3000]);  % Ajustar límites de X
ylim([-3000 3000]);  % Ajustar límites de Y
grid on;
hold off;

% Guardar la gráfica como archivo PNG
% saveas(gcf, 'Comparacion_UWB_Optitrack_Filtrado_Complementario_con_fondo.png');

%% Calcular el coeficiente de determinación (R^2) para la
% trayectoria UWB filtrada respecto a Optitrack
% -------------------------------------------------------

% Error total de los datos Optitrack respecto a su media
SStot = sum((fixedPoints_dynamic(:,1) - mean(fixedPoints_dynamic(:,1))).^2 + ...
            (fixedPoints_dynamic(:,2) - mean(fixedPoints_dynamic(:,2))).^2);

% Error residual entre la trayectoria UWB filtrada y la de Optitrack
SSres = sum((x_final_trans - fixedPoints_dynamic(:,1)).^2 + ...
            (y_final_trans - fixedPoints_dynamic(:,2)).^2);

% Calcular el R^2
R2_filtered_vs_optitrack = 1 - (SSres / SStot);

% Mostrar el resultado
fprintf('R^2 de UWB Filtrado vs Optitrack: %.4f\n', R2_filtered_vs_optitrack);

