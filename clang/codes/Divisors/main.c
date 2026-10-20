#include <stdio.h>

int number;
int arr[100000000];

int isPrime();

void diairetes(void);

int main() {
    
    printf("Dose arithmo: ");
    scanf("%d", &number);
    
    if (isPrime(number)==1) {
        printf("O %d einai prwtos arithmos.\n", number);
    } else {
        printf("O %d den einai prwtos arithmos.\n", number);
        diairetes();
    }

    return 0;
}

int isPrime() {
    if (number<=1) return 0; 
    if (number==2) return 1;  
    if (number%2==0) return 0; 
    int i;
    for(i=3; i*i<=number;i+=2) {
        if(number%i==0) {
            return 0;
        }
    }
    return 1;
}
void diairetes(void){
	int i;	
	printf("Oi diairetes tou %d ektos apo to 1 kai ton eauto tou einai: \n", number);
	for(i=2;i<number;i++){
		if(number%i==0)
		arr[i]=i;
	}
	int j;
	for(j=2;j<number;j++){
		if(number%j==0)
		printf("%d\n", arr[j]);
	}
}

