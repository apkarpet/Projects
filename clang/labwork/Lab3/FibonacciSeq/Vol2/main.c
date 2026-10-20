#include <stdio.h>
#include <stdlib.h>

//V2
int getInt (char message[]);

int numOfTerms;

int main (int argc, char *argv[]) {
	int i;
	printf("Fibonnaci Vol2\n");
	numOfTerms = getInt ("Enter number of terms:");
	
	int fbNumber[numOfTerms];
	
	fbNumber[0]=getInt ("Dose 1o oro:");
	fbNumber[1]=getInt ("Dose 2o oro:");
	
	for (i=2; i<=numOfTerms; i++) {
		fbNumber[i]=fbNumber[i+1] + fbNumber[i+2];
	}
	for(i=0; i<numOfTerms; i++) {
		pritnf("term -%d:%d\n", i+1, fbNumber[i]);
	}
	return 0;
}

int getInt (char message[]) {
	int num;
	printf ("Enter number:");
	scanf ("%d", num);
	return num;
}
