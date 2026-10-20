#include <stdio.h>
#include <stdlib.h>

float calcAverage();
int getInt(char message[]);

int main(int argc, char *argv[]) {
	printf("CalcAverage Version 2:\n");
	calcAverage();
 return 0; 
  
}

float calcAverage(){
	int i, sum;
	int numOfNumbers = getInt("Dose plithos arithmwn: ");
	
	for(i=0; i<numOfNumbers; i++); {
	int number = getInt("Dose arithmo: ");
	sum+=number;
		}	
		
 	float avg = (float)sum/numOfNumbers;
 	printf("Average=%f",avg);
}

int getInt(char message[]){
	int num;
	printf(message);
	scanf("%d", &num);
	return num;
}


