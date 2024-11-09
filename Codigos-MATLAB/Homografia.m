% -------------------------------------------------------
% Autor: Alfredo Meléndez
% 
% Descripción: Este código sirve para extraer la matriz de homografía
% para la correspondencia de puntos entre UWB y Optitrack
% De este modo se puede proyectar los puntos fijos y móviles
% Para mejorar la exactitud de la medición respecto del Optitrack. Este
% código utiliza los datasets generados de los códigos de Python.
%
% * Se agregó la implementación de filtros complementarios para observar
% la mejora en la precisión en las pruebas estáticas
% -------------------------------------------------------

% Directorio de los archivos CSV de los datasets
baseDir = 'D:\DATOS_TESIS\Datasets\Calibracion\CALIB_2_with_QF\';

% Inicializar matrices para los puntos móviles y fijos
movingPoints = [];
fixedPoints = [];

% Cargar y procesar cada archivo CSV
for i = 1:24
    % Construir el nombre del archivo
    filename = sprintf('%sCALIB_PCB%d_combined_data_STATIC_R2.csv', baseDir, i);
    
    % Cargar los datos con la regla de nombres de columnas preservada
    data = readtable(filename, 'VariableNamingRule', 'preserve');
    
    % Extraer las columnas necesarias
    x = data.('ESP32_X');  % UWB en milímetros
    y = data.('ESP32_Y');  % UWB en milímetros
    xr = data.('Robotat_X_mm');  % Optitrack en milímetros
    yr = data.('Robotat_Y_mm');  % Optitrack en milímetros
    
    % Acumular los puntos
    movingPoints = [movingPoints; [x, y]];
    fixedPoints = [fixedPoints; [xr, yr]];
end

% Verificar el número de filas acumuladas
numPoints = size(movingPoints, 1);
disp(['Total de filas acumuladas: ', num2str(numPoints)]);

% Si el número de puntos es suficiente, calcular la homografía
if numPoints > 4500
    tform = fitgeotform2d(movingPoints, fixedPoints, 'projective');
    
    % Mostrar los resultados
    disp('Homografía calculada:');
    disp(tform);
    
    % Aplicar la homografía a los puntos UWB
    movingPoints_corrected = transformPointsForward(tform, movingPoints);
    
    % Mostrar 10 puntos de cada dataset
    numMostrar = 10;
    disp('Datos crudos UWB (primeros 10 puntos):');
    disp(movingPoints(1:numMostrar, :));
    
    disp('Datos UWB corregidos (primeros 10 puntos):');
    disp(movingPoints_corrected(1:numMostrar, :));
    
    disp('Datos del Optitrack (primeros 10 puntos):');
    disp(fixedPoints(1:numMostrar, :));
    
    % Guardamos la homografía para usarla en otros códigos
    save('Homografia.mat', 'tform');
else
    warning('El número de filas acumuladas no es el esperado. Verifique los datasets.');
end

% -----------------------------------------------------------------
%% Visualización de los puntos crudos, transformados y del Optitrack
% -----------------------------------------------------------------

figure;
hold on;
axis equal;
grid on;

% Puntos corregidos UWB en color verde
scatter(movingPoints_corrected(:, 1), movingPoints_corrected(:, 2), 20, 'g', 'filled', 'DisplayName', 'UWB transformados');

% Puntos Optitrack en color azul
scatter(fixedPoints(:, 1), fixedPoints(:, 2), 20, 'b', 'filled', 'DisplayName', 'Optitrack');

% Mostrar la leyenda
legend;

ancho = 4000;
largo = 5000;

% Dibujar el rectángulo grande
rectangle('Position', [-ancho/2, -largo/2, ancho, largo], 'EdgeColor', 'k', 'LineWidth', 2);

% Dividir el rectángulo en 6 partes: 2 columnas y 3 filas
% Ancho y largo de cada subdivisión
ancho_subrect = ancho / 2;  % Dos columnas
largo_subrect = largo / 3;  % Tres filas

% Dibujar las líneas verticales para dividir en 2 columnas
for i = 1:1  % Una línea vertical
    x = -ancho/2 + i * ancho_subrect;  % Posición de la línea
    plot([x, x], [-largo/2, largo/2], 'k', 'LineWidth', 2, 'HandleVisibility', 'off');
end

% Dibujar las líneas horizontales para dividir en 3 filas
for i = 1:2  % Dos líneas horizontales
    y = -largo/2 + i * largo_subrect;  % Posición de la línea
    plot([-ancho/2, ancho/2], [y, y], 'k', 'LineWidth', 2, 'HandleVisibility', 'off');
end

% Etiquetas y título del gráfico
xlabel('X (mm)');
ylabel('Y (mm)');
title('Comparación de puntos UWB Corregidos y Optitrack GT');

% Añadir etiquetas de puntos numerados (solo para los puntos de Optitrack)
numPointsPerSet = size(fixedPoints, 1) / 24;  % Asumimos que hay 24 grupos de puntos
for i = 1:24
    % Coordenadas del punto central para cada conjunto de puntos de Optitrack
    idxStart = round((i-1)*numPointsPerSet + 1);  % Índice inicial del grupo
    idxEnd = round(i*numPointsPerSet);            % Índice final del grupo
    xPos = mean(fixedPoints(idxStart:idxEnd, 1))-200;  % X promedio
    yPos = mean(fixedPoints(idxStart:idxEnd, 2))+150;  % Y promedio
    % Añadir texto con el número de punto
    text(xPos, yPos, num2str(i), 'Color', 'black', 'FontSize', 10, 'FontWeight', 'bold', ...
        'HorizontalAlignment', 'center', 'BackgroundColor', 'white', 'EdgeColor', 'black');
end

% Mostrar la figura final
hold off;


% -------------------------------------------------------
%% Generación de tablas de estadísticas separadas para los ejes X e Y
% -------------------------------------------------------

% Inicializar matrices para almacenar estadísticas de cada dataset
media_uwb_x = [];
media_uwb_y = [];
media_opti_x = [];
media_opti_y = [];
std_uwb_x = [];
std_uwb_y = [];
std_opti_x = [];
std_opti_y = [];
diff_mean_x_corr = [];
diff_mean_y_corr = [];
error_x_corr = [];
error_y_corr = [];

% Procesar cada uno de los 24 datasets
for i = 1:24
    % Construir el nombre del archivo
    filename = sprintf('%sCALIB_PCB%d_combined_data_STATIC_R2.csv', baseDir, i);
    
    % Cargar los datos con la regla de nombres de columnas preservada
    data = readtable(filename, 'VariableNamingRule', 'preserve');
    
    % Extraer las columnas necesarias
    x = data.('ESP32_X');  % UWB en milímetros
    y = data.('ESP32_Y');  % UWB en milímetros
    xr = data.('Robotat_X_mm');  % Optitrack en milímetros
    yr = data.('Robotat_Y_mm');  % Optitrack en milímetros
    
    % Calcular la homografía (si ya no la tienes calculada antes)
    movingPoints = [x, y];
    fixedPoints = [xr, yr];
    
    % Aplicar la homografía previamente calculada
    movingPoints_corrected = transformPointsForward(tform, movingPoints);
    
    % Cálculo de las estadísticas para este dataset
    mean_xr = mean(fixedPoints(:,1));
    mean_yr = mean(fixedPoints(:,2));
    mean_corr_x = mean(movingPoints_corrected(:,1));
    mean_corr_y = mean(movingPoints_corrected(:,2));
    std_xr = std(fixedPoints(:,1));
    std_yr = std(fixedPoints(:,2));
    std_corr_x = std(movingPoints_corrected(:,1));
    std_corr_y = std(movingPoints_corrected(:,2));
    diff_mean_x = abs(mean_corr_x - mean_xr);
    diff_mean_y = abs(mean_corr_y - mean_yr);
    error_x = (diff_mean_x / abs(mean_xr)) * 100;
    error_y = (diff_mean_y / abs(mean_yr)) * 100;
    
    % Acumular los resultados
    media_uwb_x = [media_uwb_x; mean_corr_x];
    media_uwb_y = [media_uwb_y; mean_corr_y];
    media_opti_x = [media_opti_x; mean_xr];
    media_opti_y = [media_opti_y; mean_yr];
    std_uwb_x = [std_uwb_x; std_corr_x];
    std_uwb_y = [std_uwb_y; std_corr_y];
    std_opti_x = [std_opti_x; std_xr];
    std_opti_y = [std_opti_y; std_yr];
    diff_mean_x_corr = [diff_mean_x_corr; diff_mean_x];
    diff_mean_y_corr = [diff_mean_y_corr; diff_mean_y];
    error_x_corr = [error_x_corr; error_x];
    error_y_corr = [error_y_corr; error_y];
end

% Crear columna de puntos numerados
Punto = (1:24)';

% Crear tabla para eje X
T_X = table(Punto, media_uwb_x, media_opti_x, diff_mean_x_corr, error_x_corr, std_uwb_x, std_opti_x, ...
    'VariableNames', {'Punto', 'Media_UWB_Transformada_X_mm', 'Media_Optitrack_X_mm', ...
                      'Diferencia_Medias_mm', 'Error_Porcentual_X_%', 'Std_UWB_Transformada_X_mm', 'Std_Optitrack_X_mm'});

% Crear tabla para eje Y
T_Y = table(Punto, media_uwb_y, media_opti_y, diff_mean_y_corr, error_y_corr, std_uwb_y, std_opti_y, ...
    'VariableNames', {'Punto', 'Media_UWB_Transformada_Y_mm', 'Media_Optitrack_Y_mm', ...
                      'Diferencia_Medias_mm', 'Error_Porcentual_Y_%', 'Std_UWB_Transformada_Y_mm', 'Std_Optitrack_Y_mm'});

% Mostrar tablas
disp('Tabla para el Eje X (mm):');
disp(T_X);

disp('Tabla para el Eje Y (mm):');
disp(T_Y);

% -------------------------------------------------------
%% Exportar tablas a formato LaTeX con símbolos y ajustes de formato
% -------------------------------------------------------

% Redondear las medias a 2 decimales y los errores y desviaciones a 3 decimales
media_uwb_x = round(media_uwb_x, 2);
media_opti_x = round(media_opti_x, 2);
diff_mean_x_corr = round(diff_mean_x_corr, 2);
error_x_corr = round(error_x_corr, 3);
std_uwb_x = round(std_uwb_x, 3);
std_opti_x = round(std_opti_x, 3);

media_uwb_y = round(media_uwb_y, 2);
media_opti_y = round(media_opti_y, 2);
diff_mean_y_corr = round(diff_mean_y_corr, 2);
error_y_corr = round(error_y_corr, 3);
std_uwb_y = round(std_uwb_y, 3);
std_opti_y = round(std_opti_y, 3);

% Crear columna de puntos numerados
Punto = (1:24)';

% Crear tabla para eje X con símbolos matemáticos para la media y desviación
T_X = table(Punto, media_uwb_x, media_opti_x, diff_mean_x_corr, error_x_corr, std_uwb_x, std_opti_x, ...
    'VariableNames', {'Pt.', '$\bar{x}$ UWB', '$\bar{x}$ Optitrack', ...
                      'Diff $\bar{x}$', 'e(\%)', '$\sigma$ UWB', '$\sigma$ Optitrack'});

% Crear tabla para eje Y con símbolos matemáticos para la media y desviación
T_Y = table(Punto, media_uwb_y, media_opti_y, diff_mean_y_corr, error_y_corr, std_uwb_y, std_opti_y, ...
    'VariableNames', {'Pt.', '$\bar{x}$ UWB', '$\bar{x}$ Optitrack', ...
                      'Diff $\bar{x}$', 'e(\%)', '$\sigma$ UWB', '$\sigma$ Optitrack'});

% -------------------------------------------------------
%% Exportar tablas usando `table2latex`
% -------------------------------------------------------

% Guardar la tabla para el Eje X en un archivo LaTeX
table2latex(T_X, 'tabla_X_con_simbolos.tex');

% Guardar la tabla para el Eje Y en un archivo LaTeX
table2latex(T_Y, 'tabla_Y_con_simbolos.tex');


% -------------------------------------------------------
%% Filtro Complementario Butterworth
% -------------------------------------------------------

% Directorio de los archivos CSV de los datasets
%baseDir = 'D:\DATOS_TESIS\Datasets\Calibracion\'; 

% Parámetros de filtrado Butterworth
dt = 0.1;  % Intervalo de tiempo fijo (100 ms)
Fs = 1 / dt;  % Frecuencia de muestreo en Hz
fc_lpf = 0.6;  % Frecuencia de corte para el filtro pasa bajas (LPF)
fc_hpf = 0.5;  % Frecuencia de corte para el filtro pasa altas (HPF)

% Filtros Butterworth
[b_lpf, a_lpf] = butter(2, fc_lpf / (Fs / 2), 'low');  % Filtro pasa bajas
[d_hpf, c_hpf] = butter(2, fc_hpf / (Fs / 2), 'high');  % Filtro pasa altas

% Graficar los resultados
figure;
hold on;
axis equal;
grid on;

% Inicializamos las variables para guardar las handles de las leyendas
h1 = [];
h2 = [];
h3 = [];

% Ciclo para procesar cada uno de los 24 datasets
for i = 1:24
    % Construir el nombre del archivo CSV de cada dataset
    filename = sprintf('%sCALIB_PCB%d_combined_data_STATIC_R2.csv', baseDir, i);
    
    % Cargar los datos desde el CSV
    data = readtable(filename, 'VariableNamingRule', 'preserve');
    
    % Extraer los datos necesarios: UWB y Optitrack
    x = data.('ESP32_X');  % UWB en X
    y = data.('ESP32_Y');  % UWB en Y
    xr = data.('Robotat_X_mm');  % Optitrack en X
    yr = data.('Robotat_Y_mm');  % Optitrack en Y
    ax = data.('ESP32_Ax');  % Aceleración en X
    ay = data.('ESP32_Ay');  % Aceleración en Y

    % Puntos dinámicos
    movingPoints_dynamic = [x, y];  % Puntos dinámicos UWB
    fixedPoints_dynamic = [xr, yr];  % Puntos dinámicos Optitrack

    % Aplicar la homografía a los puntos UWB
    movingPoints_dynamic_corrected = transformPointsForward(tform, movingPoints_dynamic);

    % Filtrado de datos UWB corregidos por homografía
    x_corr_lpf = filtfilt(b_lpf, a_lpf, movingPoints_dynamic_corrected(:,1));  % Filtro LPF para X corregida
    y_corr_lpf = filtfilt(b_lpf, a_lpf, movingPoints_dynamic_corrected(:,2));  % Filtro LPF para Y corregida

    % Doble integración de acelerómetro con filtros HPF
    vx = cumtrapz(ax * 1000 * 9.8) * dt;  % Integración de la aceleración para obtener velocidad en X
    vy = cumtrapz(ay * 1000 * 9.8) * dt;  % Integración de la aceleración para obtener velocidad en Y

    vx_hpf = filtfilt(d_hpf, c_hpf, vx);  % Filtrado HPF de la velocidad en X
    vy_hpf = filtfilt(d_hpf, c_hpf, vy);  % Filtrado HPF de la velocidad en Y

    px_hpf = cumtrapz(vx_hpf) * dt;  % Integración de la velocidad filtrada para obtener posición en X
    py_hpf = cumtrapz(vy_hpf) * dt;  % Integración de la velocidad filtrada para obtener posición en Y

    % Filtrado HPF final en la posición
    px_hpf_final = filtfilt(d_hpf, c_hpf, px_hpf);  % Filtrado HPF final en la posición X
    py_hpf_final = filtfilt(d_hpf, c_hpf, py_hpf);  % Filtrado HPF final en la posición Y

    % Combinación de señales (LPF UWB corregido + HPF Acelerómetro)
    x_final_trans = x_corr_lpf + px_hpf_final;
    y_final_trans = y_corr_lpf + py_hpf_final;

    % Graficar solo los puntos del primer dataset para la leyenda
    if i == 1
        h1 = scatter(movingPoints_dynamic_corrected(:, 1), movingPoints_dynamic_corrected(:, 2), 20, 'g', 'filled', 'DisplayName', 'UWB transformados');
        h2 = scatter(x_final_trans, y_final_trans, 20, 'm', 'filled', 'DisplayName', 'UWB transformados filtrados (LPF+HPF) Butterworth');
        h3 = scatter(fixedPoints_dynamic(:, 1), fixedPoints_dynamic(:, 2), 20, 'b', 'filled', 'DisplayName', 'Optitrack');
    else
        % Graficar sin la leyenda para los otros puntos
        scatter(movingPoints_dynamic_corrected(:, 1), movingPoints_dynamic_corrected(:, 2), 20, 'g', 'filled');
        scatter(x_final_trans, y_final_trans, 20, 'm', 'filled');
        scatter(fixedPoints_dynamic(:, 1), fixedPoints_dynamic(:, 2), 20, 'b', 'filled');
    end
    
    % Etiquetar los puntos para cada uno de los 24 datasets
    text(mean(fixedPoints_dynamic(:,1))-200, mean(fixedPoints_dynamic(:,2))+150, num2str(i), ...
        'Color', 'black', 'FontSize', 10, 'FontWeight', 'bold', 'HorizontalAlignment', 'center', ...
        'BackgroundColor', 'white', 'EdgeColor', 'black');
end

% Añadir solo las leyendas que queremos
legend([h1, h2, h3]);

% Etiquetas y título del gráfico
xlabel('X (mm)');
ylabel('Y (mm)');
title('Comparación de puntos UWB Crudos, Transformados, Transformados Filtrados y Optitrack GT');

% Dibujar el rectángulo grande
rectangle('Position', [-ancho/2, -largo/2, ancho, largo], 'EdgeColor', 'k', 'LineWidth', 2);

% Dibujar las líneas verticales y horizontales para dividir el área
for i = 1:1  % Una línea vertical
    x = -ancho/2 + i * ancho_subrect;  % Posición de la línea
    plot([x, x], [-largo/2, largo/2], 'k', 'LineWidth', 2, 'HandleVisibility', 'off');
end
for i = 1:2  % Dos líneas horizontales
    y = -largo/2 + i * largo_subrect;  % Posición de la línea
    plot([-ancho/2, ancho/2], [y, y], 'k', 'LineWidth', 2, 'HandleVisibility', 'off');
end

% Mostrar la figura final
hold off;

% -------------------------------------------------------
%% Generación de tablas de estadísticas comparando UWB Transformado y Filtrado
% -------------------------------------------------------

% Inicializar matrices para almacenar estadísticas de cada dataset
media_uwb_transformada_x = [];
media_uwb_transformada_y = [];
media_uwb_filtrada_x = [];
media_uwb_filtrada_y = [];
std_uwb_transformada_x = [];
std_uwb_transformada_y = [];
std_uwb_filtrada_x = [];
std_uwb_filtrada_y = [];
diff_mean_x_uwb = [];
diff_mean_y_uwb = [];
mejora_x_uwb = [];
mejora_y_uwb = [];

% Procesar cada uno de los 24 datasets
for i = 1:24
    % Construir el nombre del archivo
    filename = sprintf('%sCALIB_PCB%d_combined_data_STATIC_R2.csv', baseDir, i);
    
    % Cargar los datos con la regla de nombres de columnas preservada
    data = readtable(filename, 'VariableNamingRule', 'preserve');
    
    % Extraer las columnas necesarias
    x = data.('ESP32_X');  % UWB en milímetros (crudos)
    y = data.('ESP32_Y');  % UWB en milímetros (crudos)
    
    % Calcular la homografía para obtener los puntos transformados
    movingPoints = [x, y];
    movingPoints_corrected = transformPointsForward(tform, movingPoints);
    
    % Filtro LPF (pasa bajas) en los puntos UWB corregidos
    x_corr_lpf = filtfilt(b_lpf, a_lpf, movingPoints_corrected(:,1));  % Filtro LPF para X corregida
    y_corr_lpf = filtfilt(b_lpf, a_lpf, movingPoints_corrected(:,2));  % Filtro LPF para Y corregida
    
    % Obtener medias y desviaciones estándar para UWB transformado (crudo transformado)
    mean_uwb_transformada_x = mean(movingPoints_corrected(:,1));  % Media transformada en X
    mean_uwb_transformada_y = mean(movingPoints_corrected(:,2));  % Media transformada en Y
    std_uwb_transformada_x_i = std(movingPoints_corrected(:,1));  % Desviación estándar transformada en X
    std_uwb_transformada_y_i = std(movingPoints_corrected(:,2));  % Desviación estándar transformada en Y
    
    % Obtener medias y desviaciones estándar para UWB filtrado
    mean_uwb_filtrada_x = mean(x_corr_lpf);  % Media filtrada en X
    mean_uwb_filtrada_y = mean(y_corr_lpf);  % Media filtrada en Y
    std_uwb_filtrada_x_i = std(x_corr_lpf);  % Desviación estándar filtrada en X
    std_uwb_filtrada_y_i = std(y_corr_lpf);  % Desviación estándar filtrada en Y
    
    % Diferencia de medias entre UWB transformado y filtrado
    diff_mean_x = abs(mean_uwb_transformada_x - mean_uwb_filtrada_x);
    diff_mean_y = abs(mean_uwb_transformada_y - mean_uwb_filtrada_y);
    
    % Calcular porcentaje de mejora en la desviación estándar
    mejora_x_std = (std_uwb_transformada_x_i - std_uwb_filtrada_x_i) / std_uwb_transformada_x_i * 100;
    mejora_y_std = (std_uwb_transformada_y_i - std_uwb_filtrada_y_i) / std_uwb_transformada_y_i * 100;
    
    % Acumular los resultados
    media_uwb_transformada_x = [media_uwb_transformada_x; mean_uwb_transformada_x];
    media_uwb_transformada_y = [media_uwb_transformada_y; mean_uwb_transformada_y];
    media_uwb_filtrada_x = [media_uwb_filtrada_x; mean_uwb_filtrada_x];
    media_uwb_filtrada_y = [media_uwb_filtrada_y; mean_uwb_filtrada_y];
    std_uwb_transformada_x = [std_uwb_transformada_x; std_uwb_transformada_x_i];
    std_uwb_transformada_y = [std_uwb_transformada_y; std_uwb_transformada_y_i];
    std_uwb_filtrada_x = [std_uwb_filtrada_x; std_uwb_filtrada_x_i];
    std_uwb_filtrada_y = [std_uwb_filtrada_y; std_uwb_filtrada_y_i];
    diff_mean_x_uwb = [diff_mean_x_uwb; diff_mean_x];
    diff_mean_y_uwb = [diff_mean_y_uwb; diff_mean_y];
    mejora_x_uwb = [mejora_x_uwb; mejora_x_std];
    mejora_y_uwb = [mejora_y_uwb; mejora_y_std];
end

% Crear columna de puntos numerados
Punto = (1:24)';

% Crear tabla para eje X
T_X = table(Punto, media_uwb_transformada_x, media_uwb_filtrada_x, diff_mean_x_uwb, std_uwb_transformada_x, std_uwb_filtrada_x, mejora_x_uwb, ...
    'VariableNames', {'Punto', 'Media_UWB_Transformada_X_mm', 'Media_UWB_Filtrada_X_mm', ...
                      'Diferencia_Medias_X_mm', 'Std_UWB_Transformada_X_mm', 'Std_UWB_Filtrada_X_mm', 'Mejora_Desviacion_X_%'});

% Crear tabla para eje Y
T_Y = table(Punto, media_uwb_transformada_y, media_uwb_filtrada_y, diff_mean_y_uwb, std_uwb_transformada_y, std_uwb_filtrada_y, mejora_y_uwb, ...
    'VariableNames', {'Punto', 'Media_UWB_Transformada_Y_mm', 'Media_UWB_Filtrada_Y_mm', ...
                      'Diferencia_Medias_Y_mm', 'Std_UWB_Transformada_Y_mm', 'Std_UWB_Filtrada_Y_mm', 'Mejora_Desviacion_Y_%'});

% Mostrar tablas
disp('Tabla para el Eje X (mm):');
disp(T_X);

disp('Tabla para el Eje Y (mm):');
disp(T_Y);

% -------------------------------------------------------
%% Exportar tablas a formato LaTeX usando `table2latex`
% -------------------------------------------------------

% Exportar tabla para el eje X
table2latex(T_X, 'tabla_X_filtrado_Butter.tex');

% Exportar tabla para el eje Y
table2latex(T_Y, 'tabla_Y_filtrado_Butter.tex');

% -------------------------------------------------------
%% Sección 1: Aplicación del Filtro Complementario Normal con Homografía y Líneas Divisorias
% -------------------------------------------------------

% Parámetros del Filtro Complementario
dt = 0.1;  % Intervalo de tiempo (100 ms)
tau = 1;   % Constante de tiempo
alpha = tau / (tau + dt);  % Constante del filtro (~0.91)

% Graficar los resultados
figure;
hold on;
axis equal;
grid on;

% Inicialización de handles para las leyendas
h1 = [];
h2 = [];
h3 = [];

% Procesar cada uno de los 24 datasets
for i = 1:24
    % Construir el nombre del archivo CSV de cada dataset
    filename = sprintf('%sCALIB_PCB%d_combined_data_STATIC_R2.csv', baseDir, i);
    
    % Cargar los datos desde el CSV
    data = readtable(filename, 'VariableNamingRule', 'preserve');
    
    % Extraer los datos necesarios: UWB y Optitrack
    x = data.('ESP32_X');  % UWB en X
    y = data.('ESP32_Y');  % UWB en Y
    xr = data.('Robotat_X_mm');  % Optitrack en X
    yr = data.('Robotat_Y_mm');  % Optitrack en Y
    ax = data.('ESP32_Ax');  % Aceleración en X
    ay = data.('ESP32_Ay');  % Aceleración en Y

    % Convertir aceleraciones de g a mm/s²
    ax = (ax - mean(ax)) * 9800;
    ay = (ay - mean(ay)) * 9800;

    % Aplicar homografía a los puntos crudos UWB
    uwbPoints = [x, y];  % Crear matriz con los puntos UWB crudos
    uwbPoints_corrected = transformPointsForward(tform, uwbPoints);  % Aplicar homografía

    % Inicializar variables de integración y filtrado
    n = length(ax);
    vel_x_acc = zeros(1, n);
    vel_y_acc = zeros(1, n);
    pos_x_filtered = zeros(1, n);
    pos_y_filtered = zeros(1, n);

    % Usamos la posición inicial corregida por homografía
    vel_x_acc(1) = 0;  % Suponemos reposo
    vel_y_acc(1) = 0;
    pos_x_filtered(1) = uwbPoints_corrected(1, 1);  % Posición inicial corregida por homografía
    pos_y_filtered(1) = uwbPoints_corrected(1, 2);  % Posición inicial corregida por homografía

    % Aplicación del filtro complementario
    for k = 2:n
        % Filtro pasa altas para la velocidad (derivado de la aceleración)
        vel_x_acc(k) = alpha * (vel_x_acc(k-1) + ax(k) * dt);
        vel_y_acc(k) = alpha * (vel_y_acc(k-1) + ay(k) * dt);
        
        % Integración para obtener la posición desde la velocidad
        pos_x_acc = pos_x_filtered(k-1) + vel_x_acc(k) * dt;
        pos_y_acc = pos_y_filtered(k-1) + vel_y_acc(k) * dt;
        
        % Filtro pasa bajas en UWB (Filtro Complementario)
        pos_x_filtered(k) = alpha * pos_x_acc + (1 - alpha) * uwbPoints_corrected(k, 1);
        pos_y_filtered(k) = alpha * pos_y_acc + (1 - alpha) * uwbPoints_corrected(k, 2);
    end

    % Aplicar la homografía a los puntos filtrados (ya están corregidos por homografía)
    filteredPoints_corrected = [pos_x_filtered', pos_y_filtered'];  % Matriz con los puntos filtrados y corregidos

    % Graficar solo los puntos del primer dataset para la leyenda
    if i == 1
        h1 = scatter(uwbPoints_corrected(:,1), uwbPoints_corrected(:,2), 20, 'g', 'filled', 'DisplayName', 'UWB transformados');
        h2 = scatter(filteredPoints_corrected(:,1), filteredPoints_corrected(:,2), 20, 'm', 'filled', 'DisplayName', 'UWB transformados filtrados (LPF+HPF) F. Complementario');
        h3 = scatter(xr, yr, 20, 'b', 'filled', 'DisplayName', 'Optitrack');
    else
        % Graficar sin la leyenda para los otros puntos
        scatter(uwbPoints_corrected(:,1), uwbPoints_corrected(:,2), 20, 'g', 'filled');
        scatter(filteredPoints_corrected(:,1), filteredPoints_corrected(:,2), 20, 'm', 'filled');
        scatter(xr, yr, 20, 'b', 'filled');
    end
    
    % Etiquetar los puntos para cada uno de los 24 datasets
    text(mean(xr)-200, mean(yr)+150, num2str(i), 'Color', 'black', 'FontSize', 10, ...
         'FontWeight', 'bold', 'HorizontalAlignment', 'center', ...
         'BackgroundColor', 'white', 'EdgeColor', 'black');
end

% Añadir solo las leyendas necesarias
legend([h1, h2, h3]);

% Límites del área de visualización
ancho = 4000;  % En mm
largo = 5000;  % En mm

% Dibujar el rectángulo grande
rectangle('Position', [-ancho/2, -largo/2, ancho, largo], 'EdgeColor', 'k', 'LineWidth', 2);

% Dividir el rectángulo en 6 partes: 2 columnas y 3 filas
ancho_subrect = ancho / 2;  % Dos columnas
largo_subrect = largo / 3;  % Tres filas

% Dibujar las líneas verticales para dividir en 2 columnas
for i = 1:1  % Una línea vertical
    x = -ancho/2 + i * ancho_subrect;  % Posición de la línea
    plot([x, x], [-largo/2, largo/2], 'k', 'LineWidth', 2, 'HandleVisibility', 'off');
end

% Dibujar las líneas horizontales para dividir en 3 filas
for i = 1:2  % Dos líneas horizontales
    y = -largo/2 + i * largo_subrect;  % Posición de la línea
    plot([-ancho/2, ancho/2], [y, y], 'k', 'LineWidth', 2, 'HandleVisibility', 'off');
end

% Etiquetas y título del gráfico
xlabel('X (mm)');
ylabel('Y (mm)');
title('Comparación de puntos UWB Crudos, Transformados, Transformados Filtrados y Optitrack GT');
grid on;
hold off;

% -------------------------------------------------------
%% Sección 2: Generación de Estadísticas Comparativas
% -------------------------------------------------------

% Inicializar matrices para almacenar estadísticas de cada dataset
media_uwb_x = [];
media_uwb_y = [];
media_filtrada_x = [];
media_filtrada_y = [];
std_uwb_x = [];
std_uwb_y = [];
std_filtrada_x = [];
std_filtrada_y = [];
diff_media_x = [];
diff_media_y = [];
mejora_x = [];
mejora_y = [];

% Procesar cada uno de los 24 datasets
for i = 1:24
    % Construir el nombre del archivo
    filename = sprintf('%sCALIB_PCB%d_combined_data_STATIC_R2.csv', baseDir, i);
    
    % Cargar los datos
    data = readtable(filename, 'VariableNamingRule', 'preserve');
    
    % Extraer los datos necesarios
    x = data.('ESP32_X');  % UWB en milímetros (crudos)
    y = data.('ESP32_Y');
    
    % Aplicar la homografía a los puntos crudos UWB
    uwbPoints = [x, y];  % Crear matriz con los puntos UWB crudos
    uwbPoints_corrected = transformPointsForward(tform, uwbPoints);  % Aplicar homografía

    % Aplicar el filtro complementario (igual que en la Sección 1)
    n = length(x);
    vel_x_acc = zeros(1, n);
    vel_y_acc = zeros(1, n);
    pos_x_filtered = zeros(1, n);
    pos_y_filtered = zeros(1, n);
    
    % Usamos la posición inicial corregida por homografía
    vel_x_acc(1) = 0;
    vel_y_acc(1) = 0;
    pos_x_filtered(1) = uwbPoints_corrected(1, 1);
    pos_y_filtered(1) = uwbPoints_corrected(1, 2);

    for k = 2:n
        % Filtro pasa altas para la velocidad (derivado de la aceleración)
        ax = (data.('ESP32_Ax') - mean(data.('ESP32_Ax'))) * 9800;
        ay = (data.('ESP32_Ay') - mean(data.('ESP32_Ay'))) * 9800;
        
        vel_x_acc(k) = alpha * (vel_x_acc(k-1) + ax(k) * dt);
        vel_y_acc(k) = alpha * (vel_y_acc(k-1) + ay(k) * dt);
        
        % Integración para obtener la posición desde la velocidad
        pos_x_acc = pos_x_filtered(k-1) + vel_x_acc(k) * dt;
        pos_y_acc = pos_y_filtered(k-1) + vel_y_acc(k) * dt;
        
        % Filtro pasa bajas en UWB
        pos_x_filtered(k) = alpha * pos_x_acc + (1 - alpha) * uwbPoints_corrected(k, 1);
        pos_y_filtered(k) = alpha * pos_y_acc + (1 - alpha) * uwbPoints_corrected(k, 2);
    end

    % Calcular estadísticas con los puntos corregidos por homografía
    media_uwb_x = [media_uwb_x; mean(uwbPoints_corrected(:,1))];
    media_uwb_y = [media_uwb_y; mean(uwbPoints_corrected(:,2))];
    media_filtrada_x = [media_filtrada_x; mean(pos_x_filtered)];
    media_filtrada_y = [media_filtrada_y; mean(pos_y_filtered)];
    
    std_uwb_x = [std_uwb_x; std(uwbPoints_corrected(:,1))];
    std_uwb_y = [std_uwb_y; std(uwbPoints_corrected(:,2))];
    std_filtrada_x = [std_filtrada_x; std(pos_x_filtered)];
    std_filtrada_y = [std_filtrada_y; std(pos_y_filtered)];
    
    % Diferencias y mejora en la desviación estándar
    diff_media_x = [diff_media_x; abs(mean(uwbPoints_corrected(:,1)) - mean(pos_x_filtered))];
    diff_media_y = [diff_media_y; abs(mean(uwbPoints_corrected(:,2)) - mean(pos_y_filtered))];
    
    mejora_x = [mejora_x; (std(uwbPoints_corrected(:,1)) - std(pos_x_filtered)) / std(uwbPoints_corrected(:,1)) * 100];
    mejora_y = [mejora_y; (std(uwbPoints_corrected(:,2)) - std(pos_y_filtered)) / std(uwbPoints_corrected(:,2)) * 100];
end

% Crear columna de puntos numerados
Punto = (1:24)';

% Crear tabla para el eje X
T_X = table(Punto, media_uwb_x, media_filtrada_x, diff_media_x, std_uwb_x, std_filtrada_x, mejora_x, ...
    'VariableNames', {'Punto', 'Media_UWB_X_mm', 'Media_Filtrada_X_mm', ...
                      'Dif_Media_X_mm', 'Std_UWB_X_mm', 'Std_Filtrada_X_mm', 'Mejora_Desv_X_%'});

% Crear tabla para el eje Y
T_Y = table(Punto, media_uwb_y, media_filtrada_y, diff_media_y, std_uwb_y, std_filtrada_y, mejora_y, ...
    'VariableNames', {'Punto', 'Media_UWB_Y_mm', 'Media_Filtrada_Y_mm', ...
                      'Dif_Media_Y_mm', 'Std_UWB_Y_mm', 'Std_Filtrada_Y_mm', 'Mejora_Desv_Y_%'});

% Mostrar tablas
disp('Tabla para el Eje X (mm):');
disp(T_X);

disp('Tabla para el Eje Y (mm):');
disp(T_Y);


% -------------------------------------------------------
%% Exportar las tablas a LaTeX
% -------------------------------------------------------
table2latex(T_X, 'tabla_X_filtrado_compfilt.tex');
table2latex(T_Y, 'tabla_Y_filtrado_compfilt.tex');


%% Funciones locales

% -------------------------------------------------------
% Función auxiliar para exportar tabla a LaTeX con mejor formato
% -------------------------------------------------------
function table2latex(T, filename)
    % Abrir archivo para escribir
    fid = fopen(filename, 'w');
    
    % Escribir encabezado de la tabla en LaTeX
    fprintf(fid, '\\begin{table}[H]\n\\centering\n\\begin{tabular}{');
    
    % Especificar el formato de las columnas (centrado)
    cols = width(T);
    for i = 1:cols
        fprintf(fid, 'c ');
    end
    fprintf(fid, '}\n\\hline\n');
    
    % Escribir nombres de las columnas, escapando caracteres especiales
    varNames = T.Properties.VariableNames;
    for i = 1:cols
        varNames{i} = strrep(varNames{i}, '_', '\_');  % Escapar guiones bajos
        fprintf(fid, '%s', varNames{i});
        if i < cols
            fprintf(fid, ' & ');  % Agregar '&' solo si no es la última columna
        end
    end
    fprintf(fid, '\\\\ \\hline\n');
    
    % Escribir las filas de la tabla
    for i = 1:height(T)
        row = T(i,:);
        for j = 1:cols
            fprintf(fid, '%s', num2str(row{1,j}));
            if j < cols
                fprintf(fid, ' & ');  % Agregar '&' solo si no es la última columna
            end
        end
        fprintf(fid, '\\\\ \n');  % Fin de la fila
    end
    
    % Cerrar la tabla en LaTeX
    fprintf(fid, '\\hline\n\\end{tabular}\n\\caption{Comparación de medias y desviación estándar de sistema UWB crudo y transformado contra Optitrack para el eje textit{eje}}\n\\end{table}\n');
    
    % Cerrar el archivo
    fclose(fid);
end
