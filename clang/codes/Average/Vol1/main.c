#include <stdio.h>
#include <stdlib.h>

int numOfNumbers , count, num, sum;
float avg;

int main(int argc, char *argv[]) {
	int count=0;
	printf("CalcAverage Version 2:\n");
	printf("Dose plithos arithmwn:");
	scanf("%d", &numOfNumbers);
	
	for(count=0; count<numOfNumbers; count++); {
	printf("Dose arithmo:");
	scanf("%d", &num);
	sum += num;
	}
 avg=(float)sum/numOfNumbers;
 printf("Average=%f", avg);
 return 0;  

}


