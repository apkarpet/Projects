#include <stdio.h>
#include <stdlib.h>

int num1, num2;
int result;
int carry;

int main(int argc, char *argv[]) {
	
	printf("AddNumbers Program V1 Running:\n");

	printf("Enter 1st number: \n");
	scanf("%d", &num1);

	printf("Enter 2nd number: \n");
	scanf("%d", &num2);
	
	result=(num1%10+num2%10)%10;
	
	if(num1%10+num2%10<9){
		result=num1%10+num2%10;
		carry=0;
	}
	else{
		result=(num1%10+num2%10)%10;
		carry=1;
	}
	result+=((num1/10)*10+(num2/10)*10+carry*10);
	printf("Result = %d", result);
	return 0;
}

