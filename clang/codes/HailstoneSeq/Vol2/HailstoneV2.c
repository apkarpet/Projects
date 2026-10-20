#include <stdio.h>

int i, sTerm;

int main () {
	
 int sTerm;
 
 
 printf("Hailstone | V1.2\n");
 printf("Enter starting number: ");
 scanf("%d", &sTerm);
 
 while (sTerm > 1) {
     sTerm = hailstone(sTerm);
     printf ("%d\n", sTerm);
}
 
 
return 0;
}

int hailstone (int n) {
	if(n%2==0) {
		return n/=2;
	}
	else {
		return 3*n + 1;
	}
	return n;
}



