#include <stdio.h>
#include <stdlib.h>

//V1

int getInt(char message[]);

int sum;
float avg;

int main(int argc, char *argv[]) {
	printf("CalcAverage Version 2:\n");
	int numOfNumbers = getInt("Dose plithos arithmwn: ");
	
	int count=0;
	for(count=0; count<numOfNumbers; count++) {
	int number = getInt("Dose arithmo: ");
	sum += number;
	}
 avg=(float)sum/numOfNumbers;
 printf("Average=%.3f", avg);
 return 0;  

}

int getInt(char message[]){
	int num;
	printf(message);
	scanf("%d", &num);
	return num;
}


