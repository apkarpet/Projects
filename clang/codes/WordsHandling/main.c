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

#define MAX_WORDS 30
#define MAX_WORD_LEN 31

int menu(void);
int wordsLength;
int numOfWords;

void addWord(void);
void displayWords(void);
void incSort(void);
void decSort(void);
void wordStats(void);
void charStats(void);
void searchWord(void);
void getStringV1(char message[], char str[]);

void sortStringArrayInc(word, numOfWords, MAX_WORD_LEN);
void sortStringArrayDec(word, numOfWords, MAX_WORD_LEN);

char word[MAX_WORDS][MAX_WORD_LEN];

void main(){
int selectedOp;

printf("WordsHandling\n\n");
	selectedOp=menu();
		while(selectedOp!= TERMINATE){
			switch(selectedOp){
				case ADD_WORD :
					getNumOfWords("Enter number of words: ");
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
printf("WordsHandling terminated\n");
return;
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
printf("7 - SEARCH WORD \n------------------------------\n");
printf("Select operation:");
scanf("%d",&choice);
return (choice);
}

void addWord(void){
	int i;
	for(i=0;i<numOfWords;i++){
		printf("Add word: \n");
		scanf("%s", word[i]);
	}
}

void displayWords(void){
	printf("Display words: \n");
	int j;
	for(j=0;j<numOfWords;j++)
		printf("%s\n", word[j]);

}

void incSort(void){
	int o=0;
	sortStringArrayInc(word, numOfWords, MAX_WORD_LEN);
	for(o=0;o<numOfWords;o++){
		printf("%s\n",word[o]);
	}

}

void decSort(void){
	sortStringArrayDec(word, numOfWords, MAX_WORD_LEN);
	int u=0;
	for(u=0;u<numOfWords;u++){
		printf("%s\n", word[u]);
	}

}

void wordStats(void){
	int u, o, max, min, overallLength;
	float avg;
	overallLength=strlen(word[0]);
	max=strlen(word[0]);
	min=strlen(word[0]);
	for(u=1;u<numOfWords;u++){
		if(strlen(word[u])>max){
			max=strlen(word[u]);
			}
		if(strlen(word[u])<min){
			min=strlen(word[u]);
			}
	}
	for(o=1;o<numOfWords;o++){
		overallLength+=strlen(word[o]);
	}
	avg=(float)overallLength/numOfWords;
	printf("Max word length = %d \nMin word length = %d \nAverage word length = %f",max,min,avg);	
 }
 
 void charstats(void) {
    char schar;
    int totalCount = 0;  
    int maxCount = 0;        
    int minCount = 0;        
    int wordCounts[30];     
    char maxWordchar[maxwordlen];
    char minWordchar[maxwordlen];
    float averageCount = 0;

  
    printf("Enter character to search: ");
    scanf("%c", &schar); 


   
    minCount = strlen(word[0]);
    

    
    for (i = 0; i < numOfWords; i++) {
        int currentCount = 0;

       	
		int j;
        for (j = 0; j < strlen(word[i]); j++) {
            if (word[i][j] == schar) {
                currentCount++;
            }
        }

      
        wordCounts[i] = currentCount;
        totalCount += currentCount;

        if (currentCount > maxCount) {
            maxCount = currentCount;
            strcpy(maxWordchar, word[i]); 
        }
        if (currentCount < minCount) {
            minCount = currentCount;
            strcpy(minWordchar, word[i]); 
        }
    }

    if (numOfWords > 0) {
        averageCount = (float)totalCount / numOfWords;
    }

    printf("Total character results'%c':\n", schar);
    printf("Total character occurencies: %d\n", totalCount);
    printf("Average number of occurencies per word: %.2f\n", averageCount);
    if (numberofWords > 0) {
        printf("Max number of occurencies in one word: %d (Word: '%s')\n", maxCount, maxWordchar);
        printf("Min number of occurencies in one word: leksi: %d (Word: '%s')\n", minCount, minWordchar);
    } else {
        printf("No words have been added to the list.\n");
    }
}

 void searchWord(void) {
    char sword[MAX_WORD_LEN];
    int foundcount = 0;
    int theseis[30]; 
    
    getStringV1("Enter word to search: ", sword);
	int i;
    for (i = 0; i < numOfWords; i++) {
        if (strcmp(word[i], sword) == 0) {
            theseis[foundcount] = i + 1; 
            foundcount++;
        }
    }

    if (foundcount > 0) {
        printf("Word '%s' found %d times on list.\n", sword, foundcount);
        printf("Found in positions below: ");
        for (i = 0; i < foundcount; i++){
            printf("%d ", theseis[i]);
        }
        printf("\n");
    } else {
        char choice;
        printf("Word '%s' not found.\n", sword);
        printf("Add word to list? (y/n)\n(y stands for yes and n stands for no,choose and type the corresponding letter,only lowercase characters): ");
        scanf(" %c", &choice);

        if (choice == 'y'){
            if (numOfWords < 30) {
                strcpy(word[numOfWords], sword);
                numOfWords++;
                printf("Word '%s' added to list.\n", sword);
            } else {
                printf("Word not added, list is full.\n");
            }
        } else {
            printf("Word not added.\n");
        }
    }
}

int getNumOfWords(char message[]) {
	printf(message);
	scanf("%d", &numOfWords);
	return numOfWords;
}
int getInt(char message[]){
	printf(message);
	int num;
	scanf("%d", &num);
	return num;
}
