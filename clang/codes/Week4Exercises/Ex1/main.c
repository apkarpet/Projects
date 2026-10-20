#include <stdio.h>
#include <math.h>

int main() {
	printf("Exercise1 Program running: \n");
	
	int x, y;
	
	printf("Enter first number: x = ");
	scanf("%d", &x);
	
	printf("Enter second number: y = ");
	scanf("%d", &y);
	
	int power = pow(x,y);
	printf("x^y = %d\n", power);
	
	float logOfX = log10(x);
	float logOfY = log10(y);
	
	printf("Results:\nlogx = %f\nlogy = %f", logOfX, logOfY);
	return 0;
}
