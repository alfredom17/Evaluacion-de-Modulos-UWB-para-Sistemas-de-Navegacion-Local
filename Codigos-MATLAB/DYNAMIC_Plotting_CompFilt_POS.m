% -------------------------------------------------------
% Código para aplicar filtro complementario normal en UWB y acelerómetro
% Filtro pasa bajas en los datos UWB y pasa altas en los datos de aceleración (velocidad).
% Además, se aplican los puntos UWB crudos transformados por homografía.
% -------------------------------------------------------
close all; clc; clear;

% Directorio de los archivos CSV de los datasets dinámicos
dynamicFile = 'D:\DATOS_TESIS\Datasets\Dinamico\MOV_PCB16_combined_data_DYNAMIC_R2.csv';

% Cargar la homografía previamente calculada
load('Homografia.mat', 'tform');

% Cargar los datos dinámicos con la regla de nombres de columnas preservada
data = readtable(dynamicFile, 'VariableNamingRule', 'preserve');

% Extraer las columnas necesarias
x = data.('ESP32_X');  % UWB en milímetros
y = data.('ESP32_Y');  % UWB en milímetros
xr = data.('Robotat_X_mm');  % Optitrack en milímetros (Ground Truth)
yr = data.('Robotat_Y_mm');  % Optitrack en milímetros (Ground Truth)

ax = data.('ESP32_Ax');  % Aceleración en X (en g)
ay = data.('ESP32_Ay');  % Aceleración en Y (en g)

% Convertir aceleración de g a mm/s² (1g = 9.8 m/s² = 9800 mm/s²)
ax = (ax - mean(ax)) * 9800;  % Convertir a mm/s² y quitar el sesgo (ruido estático)
ay = (ay - mean(ay)) * 9800;  % Convertir a mm/s² y quitar el sesgo (ruido estático)

%% Parámetros del Filtro Complementario
dt = 0.1;  % Intervalo de tiempo (100 ms)
tau = 1;   % Constante de tiempo del filtro complementario
alpha = tau / (tau + dt);  % Constante del filtro pasa altas (~0.91)

% Inicialización de variables para las integraciones
n = length(ax);
vel_x_acc = zeros(1, n);  % Velocidad derivada de la aceleración (filtrada)
vel_y_acc = zeros(1, n);
pos_x_filtered = zeros(1, n);  % Posición combinada UWB y aceleración (filtrada)
pos_y_filtered = zeros(1, n);

% Condiciones iniciales (posición inicial de UWB como referencia)
vel_x_acc(1) = 0;  % Suponemos que empezamos en reposo (sin velocidad inicial)
vel_y_acc(1) = 0;
pos_x_filtered(1) = x(1);  % Inicialización con la primera posición medida por UWB
pos_y_filtered(1) = y(1);

%% Aplicación del Filtro Complementario en la Velocidad y en los Datos UWB

for k = 2:n
    % Filtro pasa altas en la integración de la aceleración para obtener la velocidad
    vel_x_acc(k) = alpha * (vel_x_acc(k-1) + ax(k) * dt);  % Velocidad en X
    vel_y_acc(k) = alpha * (vel_y_acc(k-1) + ay(k) * dt);  % Velocidad en Y
    
    % Integración para obtener la posición a partir de la velocidad filtrada
    pos_x_acc = pos_x_filtered(k-1) + vel_x_acc(k) * dt;
    pos_y_acc = pos_y_filtered(k-1) + vel_y_acc(k) * dt;
    
    % Filtro pasa bajas aplicado a UWB (Filtro Complementario: LPF UWB + HPF aceleración)
    pos_x_filtered(k) = alpha * pos_x_acc + (1 - alpha) * x(k);  % Combinación X
    pos_y_filtered(k) = alpha * pos_y_acc + (1 - alpha) * y(k);  % Combinación Y
end

%% Aplicar la homografía a los puntos crudos y filtrados

% Puntos UWB crudos transformados por homografía
uwbPoints = [x, y];  % Crear matriz con los puntos UWB crudos
uwbPoints_corrected = transformPointsForward(tform, uwbPoints);  % Aplicar homografía

% Puntos UWB filtrados por el filtro complementario
filteredPoints = [pos_x_filtered', pos_y_filtered'];  % Puntos filtrados por el filtro complementario
filteredPoints_corrected = transformPointsForward(tform, filteredPoints);  % Aplicar homografía

%% Graficar los resultados

figure;
hold on;

% Graficar los puntos del Optitrack (en azul)
plot(xr, yr, 'b-', 'DisplayName', 'Optitrack (Ground Truth)', 'LineWidth', 2);

% Graficar los puntos UWB crudos (en rojo)
plot(x, y, 'r--', 'DisplayName', 'UWB Crudo', 'LineWidth', 2);

% Graficar los puntos UWB crudos transformados (en verde)
plot(uwbPoints_corrected(:, 1), uwbPoints_corrected(:, 2), 'g-', 'DisplayName', 'UWB Crudo Transformado (Homografía)', 'LineWidth', 2);

% Graficar los puntos UWB crudos filtrados por filtro complementario (en negro)
plot(pos_x_filtered, pos_y_filtered, 'k-', 'DisplayName', 'UWB Crudo Filtrado (LPF)', 'LineWidth', 2);

% Graficar los puntos corregidos por homografía y filtrados (en magenta)
plot(filteredPoints_corrected(:, 1), filteredPoints_corrected(:, 2), 'm-', 'DisplayName', 'UWB Corregido Filtrado (LPF+HPF)', 'LineWidth', 2);

% Añadir etiquetas y leyenda
xlabel('X [mm]');
ylabel('Y [mm]');
title('Comparación entre UWB Crudo, Filtrado, UWB Transformado y Optitrack');
legend('show', 'Location', 'best');

% Ajustar límites y cuadrícula
axis equal;
xlim([-3000 3000]);  % Ajustar límites de X
ylim([-3000 3000]);  % Ajustar límites de Y
grid on;
hold off;

% Guardar la gráfica como archivo PNG (opcional)
% saveas(gcf, 'Comparacion_UWB_Filtrado_Homografia_vs_Optitrack.png');


%% Calcular el coeficiente de determinación (R^2) para la
% trayectoria UWB filtrada (después de homografía) respecto a Optitrack
% -------------------------------------------------------

% Error total de los datos Optitrack respecto a su media
SStot = sum((xr - mean(xr)).^2 + (yr - mean(yr)).^2);

% Error residual entre la trayectoria UWB filtrada (corregida y transformada) y la de Optitrack
SSres = sum((filteredPoints_corrected(:, 1) - xr).^2 + (filteredPoints_corrected(:, 2) - yr).^2);

% Calcular el R^2
R2_filtered_vs_optitrack = 1 - (SSres / SStot);

% Mostrar el resultado
fprintf('R^2 de UWB Filtrado y Corregido vs Optitrack: %.4f\n', R2_filtered_vs_optitrack);

