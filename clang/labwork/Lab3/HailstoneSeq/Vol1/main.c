#include <stdio.h>
#include <stdlib.h>

//Vol 1.2


int main(void) {
	int n, result;
	
	printf("Hailstone Vol1 running: \n");
	printf("Enter starting number: ");
	scanf("%d", &n);
	while(n>1){
	if (n % 2 == 0) n /=2;	
	else n = 3*n + 1;
	printf("%d ", n);
	}
	
	return 0;

}	

