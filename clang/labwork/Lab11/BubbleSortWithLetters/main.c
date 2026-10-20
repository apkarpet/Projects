#include <stdio.h>
#include <string.h>

#define NUM_STRINGS 7
#define STRING_LENGTH 6

void generateString(char *str);
void bubbleSortStrings(char str[][STRING_LENGTH], int n);
void swapStrings(char str1[], char str2[]);


int main(int argc, char *argv[]){
	char strings[NUM_STRINGS][STRING_LENGTH];
    
	int i;
    printf("Original strings:\n");
    for(i = 0; i < NUM_STRINGS; i++) {
        generateString(strings[i]);
        printf("%s\n", strings[i]);
    }
    
    bubbleSortStrings(strings, NUM_STRINGS);
    
	printf("\nSorted strings:\n");
	int j;
    for(j = 0; j< NUM_STRINGS; j++) {
        printf("%s\n", strings[j]);
    }
	
	return 0;
}

void generateString(char *str) {
    const char charset[] = "abcdefghijklmnopqrstuvwxyz";
    int i;
    for(i = 0; i < STRING_LENGTH - 1; i++) {
        int index = rand() % (sizeof(charset) - 1);
        str[i] = charset[index];
    }
    str[STRING_LENGTH - 1] = '\0';
}

void swapStrings(char str1[], char str2[]){
    char temp[STRING_LENGTH];
    strcpy(temp, str1);
    strcpy(str1, str2);
    strcpy(str2, temp);
}


void bubbleSortStrings(char str[][STRING_LENGTH], int n) {
	int i,j;
    for(i = 0; i < n - 1; i++) {
        for(j = 0; j < n - i - 1; j++) {
            if(strcmp(str[j], str[j + 1]) > 0) {
                swapStrings(str[j], str[j + 1]);
            }
        }
    }
}
