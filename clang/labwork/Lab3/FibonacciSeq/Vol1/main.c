#include <stdio.h>

int getInt(char message[]);

int main () {
int result, i;

int numOfTerms = getInt("Eisagete arithmo orwn:");

int a = getInt("Eisagete 1o oro:");
int b = getInt("Eisagete 2o oro:");

for(i=0; i<numOfTerms; i++) {
  printf("%d ", a);
  result = a + b;
  a = b;
  b = result;
	}
}

int getInt(char message[]){
	int num;
	printf(message);
	scanf("%d", &num);
	return num;
}
