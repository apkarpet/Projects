#include <stdio.h>
#include <math.h>


int main() {
	int a;
	float result;
	
	printf("LogNumbers program running:\n");
	
	printf("Please enter an integer: ");
	scanf("%d", &a);
	
	result = log10(a);
	printf("log%d = %f", a, result);
	return 0;
}
