#include <stdio.h>
#include <math.h>

int firstNum;
int secondNum;
char num1[3];
char num2[3];

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
	scanf("%d%d%d", &num1[0], &num1[1], &num1[2]);
	firstNum=num1[0]*100+num1[1]*10+num1[2];
	return firstNum;
}

int getNum2(){
	printf("Enter each digit of number 2:\n");
	scanf("%d%d%d", &num2[0], &num2[1], &num2[2]);
	secondNum=num2[0]*100+num2[1]*10+num2[2];
	return secondNum;
}

