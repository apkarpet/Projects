#include <stdio.h>
#include <stdlib.h>
#include "i2p.h"

void getArr(void);
void displayMinAndMax(void);
int getInt(char message[]);

int numOfNums;
int ar[100];

int main(int argc, char *argv[]) {

getArr();

sortIntArrayInc(ar, numOfNums);

displayMinAndMax();

return 0;
}

void displayMinAndMax(void){
printf("Min=%d  Max=%d", ar[0], ar[numOfNums-1]);
}

void getArr(void){
int i;

numOfNums = getInt("Give Number Of Items: ");

for(i=0;i<numOfNums;i++){
ar[i]=getInt("Give Number: ");
}
}

int getInt(char message[]){
int num;
printf(message);
scanf("%d", &num);
return num;
}
