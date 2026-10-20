#include <stdio.h>
#include <stdlib.h>

void getStringV1(char message[],char str[]);
int getInt(char message[]);
//void getStringV1(char *message,char *str);

char fname[20];
char lname[20];
char odos[20];
	
	
int main(int argc, char *argv[]) {
	
 int arithmos = getInt("Dose Aritmo:");
 getStringV1("Dose odo:",odos);
 getStringV1("Dose epitheto:",fname);
 getStringV1("Dose onoma:",lname);
 printf("onoma:%s\tEpitheto:%s\todos:%s",lname,fname,odos);

getStringV1("Dose odo:",odos);
getStringV1("Dose epitheto:",fname);
getStringV1("Dose onoma:",lname);
printf("onoma:%s\tEpitheto:%s\todos:%s",lname,fname, odos);
return 0;
}

void getStringV1(char message[],char str[]){
 printf(message);
 scanf("%s",str);
}

int getInt(char message[]){
	int num;
	scanf("%d", &num);
	return num;
}

