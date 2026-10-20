#include <stdio.h>

void moveBubbleUp(void);
void moveBubbleDown(void);
void printArray(void);
void generateArray(void);
void numsToLetters(void);

int arr[12];
const size = 12;

int main() {
	generateArray();
	printf("Array before sorting: \n");
	printArray();
    bubbleSort();
    return 0;
}

void bubbleSort(void){
	moveBubbleUp();
	moveBubbleDown();
}

void moveBubbleUp(void) {
    for (int step = 0; step < 11; ++step) {
        for (int i = 0; i < 11 - step; ++i) {
            if (arr[i] > arr[i + 1]) {
                int temp = arr[i];
                arr[i] = arr[i + 1];
                arr[i + 1] = temp;
            }
        }
    }
    printf("Sorted array in ascending order: \n");
   	printArray();
}

void moveBubbleDown(void){
	for (int step = 0; step < 11; step++) {
        for (int i = 0; i < 11 - step; i++) {
            if (arr[i] < arr[i + 1]) {
                int temp = arr[i];
                arr[i] = arr[i + 1];
                arr[i + 1] = temp;
            }
        }
    }
    printf("Sorted array in descending order: \n");
   	printArray();
}

void generateArray(void){
	for(int i=0; i<12; i++){
		int num = rand();
		arr[i]=num;
	}
}

void printArray(void) {
    for (int i = 0; i < size; ++i) {
        printf("%d  ", arr[i]);
    }
    printf("\n");
}
