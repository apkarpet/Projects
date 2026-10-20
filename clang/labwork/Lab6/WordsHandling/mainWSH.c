#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "i2p.h"

#define TERMINATE           0
#define ADD_WORD           1
#define DISPLAY_WORDS      2
#define INCR_SORT          3
#define DECR_SORT          4
#define WORD_STATS         5
#define CHAR_STATS         6
#define SEARCH_WORD        7
#define MAX_WORDS          6
#define MAX_WORD_LEN       10

int menu(void);
void addWord(void);
void displayWords(void);
void incSort(void);
void decSort(void);
void wordStats(void);
void charStats(char ch);
void searchWord(void);
void initializeWordStats(char str[]);
void updateWordStats(char str[]);
void displayWordStats(void);
char getCharacter(char message[]);
int charAp(char word[], char ch);

char words[MAX_WORDS][MAX_WORD_LEN];
int freeEntry = 0;
int curWord_len;
int max_len, min_len;
int total_len = 0;

int main(int argc, char *argv[]) {
    int selectedOp;
    char ch;
    
    printf("WordsHandling V1 - SkeletonCode\n\n");
    selectedOp = menu();
    
    while(selectedOp != TERMINATE) {
        switch(selectedOp) {
            case ADD_WORD:
                addWord();
                break;
            case DISPLAY_WORDS:
                displayWords();
                break;
            case INCR_SORT:
                incSort();
                break;
            case DECR_SORT:
                decSort();
                break;
            case WORD_STATS:
                wordStats();
                break;
            case CHAR_STATS:
                ch = getCharacter("Dose xaraktira gia statistika: \n");
                charStats(ch);
                break;
            case SEARCH_WORD:
                searchWord();
                break;
            default:
                printf("Operation is not supported\n");
                break;
        }
        selectedOp = menu();
    }
    printf("WordsHandling V1 terminated\n");
    return 0;
}

int menu(void) {
    int choice;
    printf("\n\n-----------MENU---------------\n");
    printf("0 - TERMINATE\n");
    printf("1 - ADD WORD\n");
    printf("2 - DISPLAY WORDS\n");
    printf("3 - INCREMENTAL SORT\n");
    printf("4 - DECREMENTAL SORT\n");
    printf("5 - WORD STATISTICS\n");
    printf("6 - CHARACTER STATISTICS\n");
    printf("7 - SEARCH WORD \n");
    printf("Select operation: ");
    scanf("%d", &choice);
    while(getchar() != '\n');
    return choice;
}

void addWord(void) {
    printf("add word\n");
    if(freeEntry < MAX_WORDS) {
        getStringV2("Dose lexeis: \n", words[freeEntry], MAX_WORD_LEN-1);
        freeEntry++;
    } else {
        printf("Array is full!\n");
    }
    printf("addWord executed\n");
}

void displayWords(void) {
    int i;
    printf("display words: \n");
    for(i = 0; i < freeEntry; i++) {
        printf("%s\n", words[i]);
    }
    printf("displayWords executed\n");
}

void incSort(void) {
	int i;
    sortStringArrayInc(words, freeEntry, MAX_WORD_LEN);
    for(i=0; i< freeEntry; i++) {
        printf("incremental sort: %s\n", words[i]);	
	}
    printf("incSort executed\n");
}

void decSort(void) {
    int i;
    sortStringArrayDec(words, freeEntry, MAX_WORD_LEN);
    for(i=0; i< freeEntry; i++) {
        printf("decremental sort: %s\n", words[i]);	
	}
    printf("decSort executed\n");
}

void wordStats(void) {
	int i;
    printf("word statistics\n");
    if(freeEntry > 0) {
        initializeWordStats(words[0]);
        for(i = 1; i < freeEntry; i++) {
            updateWordStats(words[i]);
        }
        displayWordStats();
    }
    printf("wordStats executed\n");
}

void initializeWordStats(char str[]) {
    curWord_len = strlen(str);
    max_len = min_len = curWord_len;
    total_len = curWord_len;
}

void updateWordStats(char str[]) {
    curWord_len = strlen(str);
    total_len += curWord_len;
    if(max_len < curWord_len)
        max_len = curWord_len;
    if(min_len > curWord_len)
        min_len = curWord_len;
}

void displayWordStats(void) {
    printf("max len = %d\n", max_len);
    printf("min len = %d\n", min_len);
    printf("average len = %.2f\n", freeEntry == 0 ? 0 : (float)total_len/freeEntry);
}

char getCharacter(char message[]) {
    char ch;
    printf("%s", message);
    scanf(" %c", &ch);
    while(getchar() != '\n');
    return ch;
}

void charStats(char ch) {
    int i, totalCount = 0;
    printf("character statistics for '%c':\n", ch);
    for(i = 0; i < freeEntry; i++) {
        int count = charAp(words[i], ch);
        if(count > 0) {
            printf("'%c' appears %d times in word '%s'\n", ch, count, words[i]);
            totalCount += count;
        }
    }
    printf("Total appearances: %d\n", totalCount);
}

int charAp(char word[], char ch) {
    int i = 0, count = 0;
    while(word[i] != '\0') {
        if(word[i] == ch) count++;
        i++;
    }
    return count;
}

void searchWord(void) {
	int i;
    char searchStr[MAX_WORD_LEN];
    int found = 0;
    getStringV2("Dose lexi gia anazitisi: ", searchStr, MAX_WORD_LEN-1);
    
    for(i = 0; i < freeEntry; i++) {
        if(strcmp(searchStr, words[i]) == 0) {
            printf("Word '%s' found at position %d\n", searchStr, i);
            found = 1;
            break;
        }
    }
    if(!found) {
        printf("Word '%s' not found\n", searchStr);
    }
}
