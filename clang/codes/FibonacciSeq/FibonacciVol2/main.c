#include <stdio.h>
#include <stdlib.h>

int getInt(char message[]);

int n;

int main (int argc, char *argv[]) {
	int i;
	printf("Fibonnaci Numbers Vol2:\n");
	n = getInt("Enter number of terms:\n");
	
	int fibonacci[n];
	
	fibonacci[0]=getInt("Enter 1st term:");
	fibonacci[1]=getInt("Enter 2nd term:");
	
	for(i=2; i<n; i++) {
		fibonacci[1]=fibonacci[i-1]+fibonacci[i-2];
	}
	
	for (i=0; i<n; i++) {
		printf:("%d -> %d\n", i+1, fibonacci[i]);
	}
	return 0;
}

int getInt(char message[]) {
	int num;
	printf(message);
	scanf("%d", &num);
	return num;
}
