#include <stdio.h>
#include <stdlib.h>

int getInt (char message[]);
int numOfTerms, sum, num, i;
float avg;

int main(int argc, char *argv[]) {
	int i = 0;
	
	numOfTerms = getInt ("Enter number of terms: ");
	for (i=0; i<numOfTerms; i++) {
		num = getInt("Enter integer: ");
		sum += num;
	}
	avg = sum/numOfTerms;
	printf ("Average is %f\n", avg);
	return 0;
}

int getInt(char message[]) {
	int num;
	printf (message);
	scanf ("%d", num);
	return num;
}

