//HAILSTONE V1.2

#include<stdio.h>

int main(){
  int n;

  printf("Enter starting number: ");
  scanf("%d", &n);

  while(n > 1)
    if(n%2 == 0) {
      n = n / 2;
      printf("%d\n", n);}
    else{
      n = (3 * n)+ 1;
    printf("%d\n", n);}
}

//HAILSTONE V2

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

//VOL3

#include <stdio.h>

int i, sTerm;

int main () {
	
 int sTerm;
 
 
 printf("Hailstone | V1.2\n");
 printf("Enter starting number: ");
 scanf("%d", &sTerm);
 
 while (sTerm > 1) {
     sTerm = calcNextTerm(sTerm);
     printf ("%d\n", sTerm);
}
 
 
return 0;
}

int calcNextTerm (int n) {
	if(n%2==0) {
		return n/=2;
	}
	else {
		return 3*n + 1;
	}
	return n;
}





