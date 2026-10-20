#include <stdio.h>
#include <stdlib.h>

int num1, num2;
int result;
int krat;
int dig1, dig2, dig3;

int main(int argc, char *argv[]) {
	
	printf("AddNumbers Program V1 Running:\n");

	printf("Enter 1st number: \n");
	scanf("%d", &num1);

	printf("Enter 2nd number: \n");
	scanf("%d", &num2);

	//monades
	int monades=num1%100+num2%100;
	if(monades<10){
		krat=0;
		dig1=monades;
	}
	else{
		krat=1;
		dig1=monades%10;
	}
	
	//dekades
	int dekades=(num1/10)%10+(num2/10)%10+krat;
	if(dekades<10){
		krat=0;
		dig2=dekades;
	}
	else{
		krat=1;
		dig2=dekades%10;
	}
	
	//ekatontades
	int ekatontades=num1/100+num2/100+krat;
	dig3=ekatontades;
	
	result=dig1+dig2*10+dig3*100;
	
	printf("Result = %d", result);
	return 0;
}

