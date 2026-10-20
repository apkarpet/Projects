#include <stdio.h>
#include <stdlib.h>
//V4

 void getArray();
 void initMinAndMax(int n);
 void updateMinAndMax(int n);
 void displayMinAndMax(void);

 int numOfItems=0;
 int ar[];

 int min,max;
 int i=0;
 int num;

 int main(int argc, char *argv[]) {
	getNumOfItems();
	getArray();
	initMinAndMax(ar[0]);

	for(i=1;i<numOfItems;i++)
	updateMinAndMax(ar[i]);
	displayMinAndMax();
	return 0;
	}
	
	int getNumOfItems(void){
    	printf("Enter number of items: ");
    	scanf("%d", &numOfItems);
    	return numOfItems;
	}

	void getArray(void){
		printf("Enter integers: \n");
		for(i=0;i<numOfItems;i++){
			scanf("%d", &num);
			ar[i]=num;
		}
	}

	void initMinAndMax(int i){
	min=ar[0];
	max=ar[0];
	}

	void updateMinAndMax(int i){
	for(i=0;i<numOfItems;i++){
		if(ar[i]<min)
		min=ar[i];
		if(ar[i]>max)
		max=ar[i];
		}
	}
  void displayMinAndMax(void){
  printf("Min=%d \tMax=%d\n",min,max);
    }

