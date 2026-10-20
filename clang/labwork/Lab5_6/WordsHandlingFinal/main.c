#include <stdio.h>
#include <string.h>
#include "i2p.h"

#define TERMINATE 0
#define ADD_WORD 1
#define DISPLAY_WORDS 2
#define INCR_SORT 3
#define DECR_SORT 4
#define WORD_STATS 5
#define CHAR_STATS 6
#define SEARCH_WORD 7
#define MAX_WORDS 6
#define MAX_WORD_LEN 10

int menu(void);
void addWord(void);
void displayWords(void);
void incSort(void);
void decSort(void);
void wordStats(void);
void charStats(void);
void searchWord(void);
void getString(char str[MAX_WORD_LEN]);
int getInt(char message[]);

char word[MAX_WORDS][MAX_WORD_LEN];
int freeEntry=0;
int strWidth=0;

int main(){
 int selectedOp;

 printf("WordsHandling:");
 selectedOp=menu();
	while(selectedOp!= TERMINATE){
		switch(selectedOp){
 		case ADD_WORD :
			 addWord();
			 break;
 		case DISPLAY_WORDS :
			displayWords();
			 break;
		case INCR_SORT :
			 incSort();
 			break;
 		case DECR_SORT :
 			decSort();
 			break;
 		case WORD_STATS :
			wordStats();
 			break;
 		case CHAR_STATS :
			charStats();
 			break;
 		case SEARCH_WORD :
			searchWord();
 			break;
 		default :
			 printf("Operation is not supported\n");
			 break;
 }	
	selectedOp=menu();
 }
	printf("WordsHandling V1 terminated\n");
 }

int menu(void){
	int choice;
	
	printf("\n\n-----------MENU---------------\n");
	printf("0 - TERMINATE\n");
	printf("1 - ADD WORD\n");
	printf("2 - DISPLAY WORDS\n");
	printf("3 - INCREMENTAL SORT\n");
	printf("4 - DECREMENTAL SORT\n");
	printf("5 - WORD STATISTICS\n");
	printf("6 - CHARACTER STATISTICS\n"); 
	printf("7 - SEARCH WORD\n");
	printf("Select operation:");
	scanf("%d",&choice);
	
	return (choice);
}

void addWord(void){
	printf("Add word: \n");
	scanf("%s", word[freeEntry]);
	freeEntry++;
	if(freeEntry>MAX_WORDS) printf("List is full.");
}

void displayWords(void){
	printf("Displaying words: \n");
	int i;
	for(i=0; i<freeEntry; i++){
	printf("%s\n", word[i]);
 }
}

void incSort(void){
	printf("Incremental sort: \n");
	sortStringArrayInc(word, freeEntry, MAX_WORD_LEN);
	displayWords();
}

void decSort(void){
	printf("Decremental sort: \n");
	sortStringArrayDec(word, freeEntry, MAX_WORD_LEN);
	displayWords();
}


void wordStats(void){
 printf("Word statistics: \n");
 int i;
 int minLength, maxLength, avgLength, sumOfLengths;
 minLength = maxLength = sumOfLengths = strlen(word[0]);
 for(i=1; i<freeEntry; i++){
 	if(strlen(word[i])>maxLength) maxLength = strlen(word[i]);
 	if(strlen(word[i])<minLength) minLength = strlen(word[i]);
 	sumOfLengths += strlen(word[i]);
 }
 avgLength = (float)sumOfLengths/freeEntry;
 printf("Max word length found: %d\nMin word length found: %d\nAverage word length found: %.2f\n", maxLength, minLength, avgLength);
}

void charStats(void) {
    printf("Character statistics: \n");
    printf("Enter a character: ");
    
    char character;
    scanf(" %c", &character);
    
    int totalOcc = 0;   
    int minOcc = MAX_WORD_LEN;  
    int maxOcc = 0;         
    float avgOcc = 0.0;
	
	int i,j;
    for(i = 0; i < freeEntry; i++) {
        int wordOcc = 0; 
        
        for(j = 0; j < MAX_WORD_LEN && word[i][j] != '\0'; j++) {
            if(word[i][j] == character) {
                wordOcc++;
            }
        }
        
        totalOcc += wordOcc;
        if(wordOcc < minOcc) minOcc = wordOcc;
        if(wordOcc > maxOcc) maxOcc = wordOcc;
    }
    
    avgOcc = freeEntry > 0 ? (float)totalOcc / freeEntry : 0;
    
    printf("This character appears %d times.\n", totalOcc);
    printf("Most occurrences in a word: %d\n", maxOcc);
    printf("Least occurrences in a word: %d\n", minOcc);
    printf("Average occurrences per word: %.2f\n", avgOcc);
}

void searchWord(void) {
    if(freeEntry >= MAX_WORDS) {
        printf("Warning: Word list is full!\n");
        return;
    }

    char toSearch[MAX_WORD_LEN];    
    printf("Search word: \nEnter word to search: ");
    scanf("%s", toSearch);
    getchar(); 
    int found = 0;
    int i;
    for(i = 0; i < freeEntry; i++) {
        if(strcmp(word[i], toSearch) == 0) {
            printf("The word %s exists in position %d\n", toSearch, i+1);
            found = 1;
            break;
        }
    }

    if(!found) {
        char addOrNot;
        printf("This word is not on the list.\nWould you like to add this word to the list? [y]/[n]: ");
        addOrNot = getchar();
        
        if(addOrNot == 'y' || addOrNot == 'Y') {  
            if(strlen(toSearch) < MAX_WORD_LEN) {
                strcpy(word[freeEntry], toSearch);
                freeEntry++;
                printf("Word added successfully.\n");
            } else {
                printf("Error: Word is too long to add.\n");
            }
        }
    }
}



