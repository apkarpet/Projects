#include <stdio.h>
#include <stdlib.h>

void getStringV1(char message[],char str[]);
void getStringV2(char message[],char str[],int
numOfChars);

char fname[20];
char lname[20];
char odos[20];
int arithmos;

int main(int argc, char *argv[]) {
// V2

 getStringV2("Dose odo:",odos,20);
 getStringV2("Dose epitheto:",fname,20);
 getStringV2("Dose onoma:",lname,20);
 printf("onoma:%s\tEpitheto:%s\todos:%s",lname,fname,
odos);
 return 0;
 }

 void getStringV2(char message[],char str[],int numOfChars) {
  char ch;
  int i=0;
  printf(message);
  ch=getchar();
  if(ch=='\n'){
  str[0]='\0';
  return;
 }
 
 for(i=0;i<numOfChars&&ch!='\n';i++) {
  ch=getchar();
  str[i]=getchar();
  } 
  str[i]='\0';
  return;
  }
