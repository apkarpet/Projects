#include <search.h>

typedef struct fraction{
	int ar;
	int par;
}Fraction;

typedef struct expression{
	char operator;
	Fraction op1;
	Fraction op2;
}Expression;

int getArrayOfInts(int ar[],int maxItems);
int getInt(char message[]);

void getStringV1(char message[], char str[]);
void getStringV2(char message[],char str[], int maxSize);

void sortStringArrayInc(char base[],int numOfElements, int strWidth);
void sortStringArrayDec(char base[],int numOfElements, int strWidth);

void sortIntArrayInc(int ar[],int numOfElements);
void sortIntArrayDec(int ar[],int numOfElements);

Expression readExpression(void); // reads an expression of the following form + 1/5 3/15

