#include <stdio.h>
#include <stdlib.h>

int getNumber(void);
int sum(int n1, int n2);


int main(int argc, char *argv[]) {
	printf ("Programma Add2Numbers Vol2\n");
	int num1 =getInt("Dose arithmo:");
	int num2 =getInt("Dose arithmo:");
	int result=sum(num1, num2);
	printf ("%d + %d = %d", num1, num2, result);
	
	return 0;
}

int sum(int n1, int n2) {
	int sum;
	sum = n1+n2;
	return sum;
}

int getInt(char message[]) {
	int num;
	printf(message);
	scanf ("%d", &num);
	return num;
}
