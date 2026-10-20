#include <stdio.h>
#include "i2p.h"

//V1

bool getExpressionV1(char *operatorPtr, int *ar1p, int *par1p, int *ar2p, int *par2p); 

void add(int ar1, int par1, int ar2, int par2, int *resultAr, int *resultPar);
void sub(int ar1, int par1, int ar2, int par2, int *resultAr, int *resultPar);
void mul(int ar1, int par1, int ar2, int par2, int *resultAr, int *resultPar);
void div(int ar1, int par1, int ar2, int par2, int *resultAr, int *resultPar);

int main() {
    int ar1, par1, ar2, par2;
    int resultAr, resultPar;
    char operator;

    if (getExpressionV1(&operator, &ar1, &par1, &ar2, &par2)) {
        if (operator == '*') {
            mul(ar1, par1, ar2, par2, &resultAr, &resultPar);
            simplify(&resultAr, &resultPar);
            printf("Result: %d/%d * %d/%d = %d/%d\n", ar1, par1, ar2, par2, resultAr, resultPar);
        } else if (operator == '+') {
            add(ar1, par1, ar2, par2, &resultAr, &resultPar);
            simplify(&resultAr, &resultPar);
            printf("Result: %d/%d + %d/%d = %d/%d\n", ar1, par1, ar2, par2, resultAr, resultPar);
        } else if (operator == '-') {
            sub(ar1, par1, ar2, par2, &resultAr, &resultPar);
            simplify(&resultAr, &resultPar);
            printf("Result: %d/%d - %d/%d = %d/%d\n", ar1, par1, ar2, par2, resultAr, resultPar);
        } else if (operator == '/') {
            if (ar2 == 0) {
                printf("Cannot divide with 0.\n");
            } else {
                div(ar1, par1, ar2, par2, &resultAr, &resultPar);
                simplify(&resultAr, &resultPar);
                printf("Result: %d/%d / %d/%d = %d/%d\n", ar1, par1, ar2, par2, resultAr, resultPar);
            }
        } else {
            printf("Error: Unsupported action.\n");
        }
    } else {
        printf("Invalid fractions entered.\n");
    }

    return 0;
}

void mul(int ar1, int par1, int ar2, int par2, int *resultAr, int *resultPar) {
    *resultAr = ar1 * ar2;  
    *resultPar = par1 * par2;  
}

void add(int ar1, int par1, int ar2, int par2, int *resultAr, int *resultPar) {
    *resultAr = (ar1 * par2) + (ar2 * par1);  
    *resultPar = par1 * par2;  
}

void sub(int ar1, int par1, int ar2, int par2, int *resultAr, int *resultPar) {
    *resultAr = (ar1 * par2) - (ar2 * par1);  
    *resultPar = par1 * par2;  
}

void div(int ar1, int par1, int ar2, int par2, int *resultAr, int *resultPar) {
    *resultAr = ar1 * par2;  
    *resultPar = par1 * ar2;  
}

int gcd(int a, int b) {
    if (b == 0) return a;
    return gcd(b, a % b);
}

void simplify(int *ar, int *par) {
    int commonDivisor = gcd(*ar, *par);
    *ar /= commonDivisor;
    *par /= commonDivisor;
}
