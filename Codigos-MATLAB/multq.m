function q = multq(q1, q2)
    eta1 = q1(1);
    eps1 = q1(2:end);
    eta2 = q2(1);
    eps2 = q2(2:end);
    
    q = [eta1*eta2 - eps1'*eps2; eta1*eps2 + eta2*eps1 + skew(eps1)*eps2];
end