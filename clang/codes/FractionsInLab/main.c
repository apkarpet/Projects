#include <stdio.h>
#include <string.h>

#define N 5
#define M 31

typedef struct student{
    char lastname[M];
    char name[M];
    float degree;
}STUDENT;

void input(STUDENT x[], int size);
void output(STUDENT x[], int size);
void statistics(STUDENT x[], int size);
//void search(STUDENT x[], int size, char name[]);

int main(){
    //int X[N];
    char onoma[M];
    STUDENT etos[N];

    input(etos, N);
    output(etos, N);
    statistics(etos, N);

    printf("Give student: ");
    scanf("%s", onoma);
    //search(etos, N, onoma);

    return 0;
}

void input(STUDENT x[], int size){
    int i;
    for(i=0;i<size;i++){
        printf("Give student #%d: ",i);
        scanf("%s", x[i].lastname);
        scanf("%s", x[i].name);
        scanf("%f", &x[i].degree);
    }
}

void output(STUDENT x[], int size){
    int i;
    for(i=0;i<size;i++){
        printf("The student #%d is:",i);
        printf("%s", x[i].lastname);
        printf(" %s", x[i].name);
        printf("%.2f\n", x[i].degree);
        fflush(stdout);
    }
}

void statistics(STUDENT x[], int size){
    float min, max, average;
    int i;
    min=x[0].degree;
    max=x[0].degree;
    average=x[0].degree;

    for(i=1;i<size;i++){
        average=average+x[i].degree;
        if(x[i].degree<min) min=x[i].degree;
        if(x[i].degree>max) max=x[i].degree;
    }

printf("\nThe values are (min,max average): %.2f, %.2f, %.2f\n", min, max, average/N);
}