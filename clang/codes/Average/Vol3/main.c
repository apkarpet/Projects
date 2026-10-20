#include <stdio.h>
#include <stdlib.h>

int numOfNumbers, count, num, sum;
float avg;

int main(int argc, char *argv[]) {
	printf("CalcAverage Version 2:\n");
	printf("Dose plithos arithmwn:");
	scanf("%d",&numOfNumbers);
	
	if(numOfNumbers==0) {
		printf("No average for 0 numbers.");
		return 0;
	}
	for(count=0;count<numOfNumbers;count++); {
	printf("Dose arithmo:");
	scanf("%d" ,&num);
	sum=sum+num;
	}
 avg = (float)sum/numOfNumbers;
 printf("Average=%f",avg);
 return 0; 
  
}

