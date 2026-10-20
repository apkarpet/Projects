#include <stdio.h>
#include <stdlib.h>

//V1

int getInt(char message[]);
float getFloat(char message[]);


int num, sum;
float avg;

int main(int argc, char *argv[]) {
	printf("CalcAverage Version 2:\n");
	int numOfNumbers = getInt("Dose plithos arithmwn: ");
	
	int count=0;
	for(count=0; count<numOfNumbers; count++) {
	float number=getFloat("Dose arithmo: ");
	sum += number;
	}
 avg=(float)sum/numOfNumbers;
 printf("Average=%.3f", avg);
 return 0;  

}

float getFloat(char message[]){
	float num;
	printf(message);
	scanf("%f", &num);
	return num;
}
int getInt(char message[]){
	int num;
	printf(message);
	scanf("%d", &num);
	return num;
}


