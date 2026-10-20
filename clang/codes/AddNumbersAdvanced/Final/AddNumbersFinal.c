#include <stdio.h>
#define NUM_OF_DIGITS 4
#define NUM_OF_NUMBERS 3

int digitAt(int n, int dOrder);
int num[];

int num1=7281, num2=4996;
int digitSum, realSum, sum=0;
int dOrder;

int main(int argc, char *argv[]){
    int carry=0;
    realSum=num1+num2;
    printf("%d + %d = %d\n", num1,num2,realSum);
    for(dOrder=1;dOrder<NUM_OF_DIGITS+1;dOrder++){
        // digitSum=digitAt(num1,dOrder)+digitAt(num2,dOrder)+carry;
        for(int nOrder=1;nOrder<NUM_OF_NUMBERS;nOrder++)
            digitSum+=digitAt(num[nOrder],dOrder);
        sum+=digitAt(digitSum,1);
        carry=digitAt(digitSum,2);
        printf("%d digitSum=%d\t carry=%d\t sum=%d\t",dOrder, digitSum, carry, sum);
    }
    sum+=carry*pow(10,dOrder-1);

    // digitSum=digitAt(num1,1)+digitAt(num2,2);
    // sum=digitAt(digitSum,1);
    // carry=digitAt(digitSum,2);

    // digitSum=digitAt(num1,2)+digitAt(num2,2);
    // digitSum+=carry;

    // sum=sum+digitSum*10;
    printf("Sum=%d", sum);

    return 0;

}

int digitAt(int n, int dOrder){
    int digit;
    int i;
    for(i=0;i<dOrder;i++){
        n=n/10;
    }
    digit=n%10;
    return digit;
}
