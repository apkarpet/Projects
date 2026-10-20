#include <stdio.h>
#include <stdlib.h>

//V3

int getInt(char message[]);
void minAndMax(void);

int main(int argc, char *argv[]) {
	minAndMax();
    return 0;
}

int getInt(char message[]){
	int num;
	printf(message);
	scanf("%d", &num);
	return num;
}

void minAndMax(void){
	int n, num, max, min;

    printf("Enter the number of integers: ");
    scanf("%d", &n);
    int numbers[n];
    
    int first = getInt("Eisagete 1o oro: ");
    numbers[0]=first;
    min = max = first;
	int i;
    for (i=1; i<n; i++) {
        printf("Eisagete %do oro: ", i+1);
        
        scanf("%d", &numbers[i]);
        
        if (&numbers[i] > max) {
            max = numbers[i];
        }
        if (&numbers[i] < min) {
            min = numbers[i];
        }
    }

    printf("The largest number is: %d\n", max);
    printf("The smallest number is: %d\n", min);


}
