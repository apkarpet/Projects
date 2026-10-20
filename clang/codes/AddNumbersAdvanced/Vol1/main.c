#include <stdio.h>
#include <math.h>

int firstNum;
int secondNum;
char num1[2];
char num2[2];

int main(int argc, char *argv[]) {
	printf("AddNumbers Advanced running: \n");
	getNum1();
	getNum2();
	int addResult=firstNum+secondNum;
	printf("%d + %d = %d", firstNum, secondNum, addResult);
	return 0;
}

int getNum1(){
	printf("Enter each digit of number 1:\n");
	scanf("%d%d", &num1[0], &num1[1]);
	firstNum=num1[0]*10+num1[1];
	return firstNum;
}

int getNum2(){
	printf("Enter each digit of number 2:\n");
	scanf("%d%d", &num2[0], &num2[1]);
	secondNum=num2[0]*10+num2[1];
	return secondNum;
}

