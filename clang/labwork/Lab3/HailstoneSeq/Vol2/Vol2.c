#include <stdio.h>
#include <stdlib.h>

//Vol 2

int hailstone(int n);

int main(void) {
	int start, result;
	
	printf("Hailstone Vol1 running: \n");
	printf("Enter starting number: ");
	scanf("%d", &start);
	result = Hailstone(start);
	
	printf("%d\n", result);
	
	return 0;

}	

int hailstone(int n){
	if (n % 2 == 0) return n /=2;	
	else return n = 3  *n + 1;
	return n;
}
