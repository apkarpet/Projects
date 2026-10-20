#include <stdio.h>

int getInt(char message[]);

int main() {
    int numOfTerms=getInt("Enter number of terms: ");
    if (numOfTerms <= 0) {
        printf("Invalid input.\n");
    }

    int currentNum, previousNum;
    int currentCount = 1, maxCount = 1;
    int maxNum;

    printf("Enter the integers:\n");
    scanf("%d", &previousNum);
    maxNum=previousNum;
    
    int i;
    for (i=1; i<numOfTerms; i++) {
        scanf("%d", &currentNum);

        if (currentNum == previousNum) {
            currentCount++;
        } else {
            currentCount = 1;
        }

        if (currentCount>maxCount) {
            maxCount=currentCount;
            maxNum=currentNum;
        }

        previousNum=currentNum;
    }

    printf("The number %d has the most occurrences in a row (%d).\n",maxNum,maxCount);

    return 0;
}

int getInt(char message[]){
	printf(message);
	int num;
	scanf("%d", &num);
	return num;
}

