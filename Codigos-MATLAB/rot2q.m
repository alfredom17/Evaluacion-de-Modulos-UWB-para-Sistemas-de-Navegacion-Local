function q = rot2q(R)
    % tol = 1e-5; % to eval a zero value in eta
    % eta = sqrt(1+R(1,1)+R(2,2)+R(3,3))/2;
    % if(eta <= tol)
    %     eps = [0; 0; 0];
    %     eps(1) = sqrt(1+R(1,1)-R(2,2)-R(3,3))/2;
    %     eps(2:end) = (1/(4*eps(1))) * [R(1,2)+R(2,1); R(1,3)+R(3,1) ];
    %     eta = (1/(4*eps(1))) * (R(3,2)-R(2,3));
    % else
    %     eps = (1/(4*eta)) * [R(3,2)-R(2,3); R(1,3)-R(3,1); R(2,1)-R(1,2)];
    % end
    % q = [eta; eps];

    % De las lecture notes del curso de Robot Dynamics en el ETHZ
    % q = 0.5 * [ sqrt(R(1,1) + R(2,2) + R(3,3) + 1);
    %                  sign(R(3,2) - R(2,3)) * sqrt(R(1,1) - R(2,2) - R(3,3) + 1);
    %                  sign(R(1,3) - R(3,1)) * sqrt(R(2,2) - R(3,3) - R(1,1) + 1);
    %                  sign(R(2,1) - R(1,2)) * sqrt(R(3,3) - R(1,1) - R(2,2) + 1) ];
end