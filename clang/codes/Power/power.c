#include <stdio.h>
#include <math.h>


int main() {
	int num1, num2;
	double result;
	
	printf("Give base value: ");
	scanf("%d", &num1);
	
	printf("Give exponential value: ");
	scanf("%d", &num2);
	
	result = pow(num1, num2);
	printf("Results: %d ^ %d = %.1f", num1, num2, result);
	
	return 0;
}


