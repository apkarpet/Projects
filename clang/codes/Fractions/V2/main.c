#include <stdio.h>
#include "i2p.h"

//V2

Fraction add(Fraction f1, Fraction f2);
Fraction sub(Fraction f1, Fraction f2);
Fraction mul(Fraction f1, Fraction f2);
Fraction div(Fraction f1, Fraction f2);
Fraction simplify(Fraction f);
void display(Fraction f);

int main() {
    Expression expr;
    Fraction result;

    printf("Fraction Calculator\n");
    printf("Enter an expression of the format: + 1/2 3/4\n");

    expr = getExpressionV2();

    switch (expr.oprtr) {
        case '+':
            result = add(expr.op1, expr.op2);
            break;
        case '-':
            result = sub(expr.op1, expr.op2);
            break;
        case '*':
            result = mul(expr.op1, expr.op2);
            break;
        case 'q':
        	printf("Program terminated.");
        	return 1;
        	break;
        case '/':
            if (expr.op2.ar == 0) {
                printf("Error: Cannot divide by zero.\n");
                return 1;
            }
            result = div(expr.op1, expr.op2);
            break;
        default:
            printf("Error: Unsupported operator '%c'.\n", expr.oprtr);
            return 1;
    }

    result = simplify(result);

    printf("Result: %d/%d %c %d/%d = ", 
        expr.op1.ar, expr.op1.par, expr.oprtr, expr.op2.ar, expr.op2.par);
    display(result);

    return 0;
}


Fraction add(Fraction f1, Fraction f2) {
    Fraction result;
    result.ar = (f1.ar * f2.par) + (f2.ar * f1.par);
    result.par = f1.par * f2.par;
    return simplify(result);
}

Fraction sub(Fraction f1, Fraction f2) {
    Fraction result;
    result.ar = (f1.ar * f2.par) - (f2.ar * f1.par);
    result.par = f1.par * f2.par;
    return simplify(result);
}

Fraction mul(Fraction f1, Fraction f2) {
    Fraction result;
    result.ar = f1.ar * f2.ar;
    result.par = f1.par * f2.par;
    return simplify(result);
}

Fraction div(Fraction f1, Fraction f2) {
    Fraction result;
    result.ar = f1.ar * f2.par;
    result.par = f1.par * f2.ar;
    return simplify(result);
}

Fraction simplify(Fraction f) {
    int gcd(int a, int b) {
        if (b == 0) return a;
        return gcd(b, a % b);
    }
    int divisor = gcd(f.ar, f.par);
    f.ar /= divisor;
    f.par /= divisor;

    if (f.par < 0) {
        f.ar = -f.ar;
        f.par = -f.par;
    }
    return f;
}

void display(Fraction f) {
    printf("%d/%d\n", f.ar, f.par);
}
