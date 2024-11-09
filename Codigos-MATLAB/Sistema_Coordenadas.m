% Agregar el Toolbox de Robótica
clc;
clear;
close all;

% Dimensiones del área (4x5 metros)
ancho = 4;  % metros (dimensión en X)
largo = 5;  % metros (dimensión en Y)

% El centro del marco de referencia está en (0, 0)
% Por lo tanto, las posiciones de los puntos deben ser relativas a este nuevo origen.

% Posiciones de los marcos de referencia y cámaras
pos_UWB = [-ancho/2, -largo/2];  % Esquina inferior izquierda respecto al nuevo origen (centro)
pos_OptiTrack = [0, 0];          % Centro del rectángulo es el origen (0, 0)

% Puntos adicionales (cámaras en las esquinas y en los lados izquierdo y derecho)
punto_izq = [-ancho/2-0.2, 0];     % Punto en el lado izquierdo (mitad, con respecto al nuevo origen)
punto_der = [ancho/2+0.2, 0];      % Punto en el lado derecho (mitad)

% Cámaras en las cuatro esquinas
punto_esq1 = [-ancho/2, -largo/2];   % Esquina inferior izquierda
punto_esq2 = [ancho/2, -largo/2];    % Esquina inferior derecha
punto_esq3 = [-ancho/2, largo/2];    % Esquina superior izquierda
punto_esq4 = [ancho/2, largo/2];     % Esquina superior derecha

% Crear una figura
figure;
hold on;
axis equal;
grid on;
xlim([-ancho/2-1, ancho/2+1]);
ylim([-largo/2-1, largo/2+1]);

% Etiquetas y título
xlabel('X (metros)');
ylabel('Y (metros)');
title('Visualización de Poses - UWB y OptiTrack (Centrado en 0,0)');

% Dibuja el rectángulo
%rectangle('Position', [-ancho/2, -largo/2, ancho, largo], 'EdgeColor', 'k', 'LineWidth', 2);

% Crear la matriz homogénea 3x3 manualmente para cada marco de referencia
% Matriz de rotación (identidad 2x2, ya que no hay rotación)
R = eye(2);

% Marco de referencia UWB (en la esquina inferior izquierda)
H_UWB = [R, pos_UWB'; 0 0 1];  % Matriz homogénea para UWB
trplot2(H_UWB, 'frame', 'UWB', 'color', 'r', 'length', 0.8); % Marco UWB

% Marco de referencia OptiTrack (en el centro del rectángulo, que es el origen (0, 0))
H_OptiTrack = [R, pos_OptiTrack'; 0 0 1];  % Matriz homogénea para OptiTrack
trplot2(H_OptiTrack, 'frame', 'OptiTrack', 'color', 'b', 'length', 0.8); % Marco OptiTrack

% Graficar los puntos de las cámaras (cuatro esquinas, lado izquierdo y derecho)
plot(punto_izq(1), punto_izq(2), 'go', 'MarkerSize', 10, 'MarkerFaceColor', 'g'); % Cámara izquierda
plot(punto_der(1), punto_der(2), 'go', 'MarkerSize', 10, 'MarkerFaceColor', 'g'); % Cámara derecha

% Graficar cámaras en las esquinas
plot(punto_esq1(1), punto_esq1(2), 'go', 'MarkerSize', 10, 'MarkerFaceColor', 'g'); % Esquina inferior izquierda
plot(punto_esq2(1), punto_esq2(2), 'go', 'MarkerSize', 10, 'MarkerFaceColor', 'g'); % Esquina inferior derecha
plot(punto_esq3(1), punto_esq3(2), 'go', 'MarkerSize', 10, 'MarkerFaceColor', 'g'); % Esquina superior izquierda
plot(punto_esq4(1), punto_esq4(2), 'go', 'MarkerSize', 10, 'MarkerFaceColor', 'g'); % Esquina superior derecha

% Colocar etiquetas para los puntos (cámaras y esquinas)
text(punto_izq(1)-0.2, punto_izq(2), '6', 'HorizontalAlignment', 'right');
text(punto_der(1)+0.2, punto_der(2), '3', 'HorizontalAlignment', 'left');

text(punto_esq1(1)-0.3, punto_esq1(2)-0.0, '5', 'HorizontalAlignment', 'right');
text(punto_esq2(1)+0.2, punto_esq2(2)-0.2, '4', 'HorizontalAlignment', 'left');
text(punto_esq3(1)-0.2, punto_esq3(2)+0.2, '1', 'HorizontalAlignment', 'right');
text(punto_esq4(1)+0.2, punto_esq4(2)+0.2, '2', 'HorizontalAlignment', 'left');

% Mostrar la figura final
hold off;
