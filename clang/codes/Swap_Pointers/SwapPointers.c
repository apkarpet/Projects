#include <stdio.h>

void swap(int *x, int *y);

int main(){
   int a=2, b=3;
   printf("a=%d, b=%d\n", a,b);

   swap(&a,&b);

   printf("a=%d, b=%d\n", a,b);

   return 0; 
}

//swap the pointer value
void swap(int *x, int *y){
    int temp;
    temp=*x;
    *x=*y;  //change a
    *y=temp;//change b
    printf("x=%d, y=%d\n", *x,*y);
}
