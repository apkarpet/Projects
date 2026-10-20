#include <stdio.h>
#include <string.h>

#define N 10
#define M 31

typedef struct student{
    char lastname[M];
    char name[M];
    float degree;
}STUDENT;

void input(STUDENT x[], int size);
void output(STUDENT x[], int size);
void statistics(STUDENT x[], int size);
void search(STUDENT x[], int size, char name[]);

int main(){
    //int X[N];
    char onoma[M];
    STUDENT etos[N];
    
    input(etos, N);
    output(etos, N);
    statistics(etos, N);

    printf("Give student: ");
    scanf("%s", onoma);
    search(etos, N, onoma);

    return 0;
}