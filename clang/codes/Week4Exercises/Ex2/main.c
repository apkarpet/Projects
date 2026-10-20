#include <stdio.h>
#include <string.h>

#define N 40

//V1

int main(){
char name[N]="NIKOY";

int len;
int i;


printf("Give name: ");

len=strlen(name);

for(i=0;i<=len;i++){
name[len-i] = '\0';
printf("%s\n",name);
}

return 0;

}

//V2 With getString
