#include <stdio.h>
#include <stdlib.h>

//V1

int main(int argc, char *argv[]) {
    int n, num, max, min;

    printf("Enter the number of integers: ");
    scanf("%d", &n);


    printf("Eisagete 1o oro: ");
    scanf("%d", &num);
    max = min = num;

	int i;
    for (i=2; i <= n; i++) {
        printf("Eisagete %do oro: ", i);
        scanf("%d", &num);

        
        if (num > max) {
            max = num;
        }
        if (num < min) {
            min = num;
        }
    }

    printf("The largest number is: %d\n", max);
    printf("The smallest number is: %d\n", min);

    return 0;
}

