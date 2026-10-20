#include <stdio.h>

#define TERMINATE 0
#define INSERT_NUMBERS 1
#define ADD 2
#define SUB 3
#define MUL 4

int menu(void);
void insertNumbers(void);
void add(void);
void sub(void);
void mul(void);
	
int num, num1, num2, result;
	
void main(){
	int selectedOp;
	
	printf("Menu V1 - SkeletonCode\n\n");
	selectedOp=menu();
		while(selectedOp!= TERMINATE){
			switch(selectedOp){
				case INSERT_NUMBERS :
					insertNumbers();
				break;
				case ADD :
					result=num1+num2;
					printf("%d + %d = %d\n", num1, num2, result);
					add();
				break;
				case SUB :
					result=num1-num2;
					printf("%d - %d = %d\n", num1, num2, result);
					sub();
				break;
				case MUL :
					result=num1*num2;
					printf("%d * %d = %d\n", num1, num2, result);
					mul();
				break;
				default :
					printf("Operation is not supported\n");
				break;
			}
		selectedOp=menu();
		}
	printf("Menu V1 terminated\n");
	}
	
int menu(void){
	int choice;
	printf("\n\n-----------MENU---------------\n");
	printf("0 - TERMINATE\n");
	printf("1 - INSERT NUMBERS\n");
	printf("2 - ADD\n");
	printf("3 - SUB\n");
	printf("4 - MUL \n------------------------------\n");
	printf("Select operation:"); //use getInt()
	scanf("%d",&choice);
	return (choice);
	}
	
void insertNumbers(void){
	printf("insertNumbers executed\n");
	num1=getInt();
	num2=getInt();
	}

void add(void){
	printf("add executed\n");
	}

void sub(void){
	printf("sub executed\n");
	}

void mul(void){
	printf("mul executed\n");
	}
int getInt(){
	printf("Enter integer: \n");
	scanf("%d", &num);
	return num;
}
