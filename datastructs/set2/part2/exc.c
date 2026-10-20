#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define M 11

struct Node {
    char date[20];
    long long cumulative;
    struct Node *next;
};

int calculate(char *date);
void insert(struct Node *table[], char *date, long long cumulative);
struct Node* search(struct Node *table[], char *date);
void update(struct Node *table[], char *date, long long newVal);
void deleteNode(struct Node *table[], char *date); 
void freeTable(struct Node *table[]);
void loadCSV(char *filename, struct Node *table[]);

int main() {
    struct Node *hashTable[M] = {NULL};

    char filename[] = "test.csv";

    loadCSV(filename, hashTable);

    int choice;
    char targetDate[20];
    long long newVal;

    do {
        printf("\n--- COVID-19 Hashing Menu (m=11) ---\n");
        printf("1. Αναζήτηση Cumulative βάσει Ημερομηνίας\n");
        printf("2. Τροποποίηση Cumulative βάσει Ημερομηνίας\n");
        printf("3. Διαγραφή εγγραφής βάσει Ημερομηνίας\n");
        printf("4. Έξοδος\n");
        printf("Επιλογή: ");
        
        if (scanf("%d", &choice) != 1) {
            while(getchar() != '\n');
            continue;
        }

        if (choice >= 1 && choice <= 3) {
            printf("Δώστε ημερομηνία (π.χ. 31/12/2020): ");
            scanf("%s", targetDate);
        }

        switch(choice) {
            case 1: {
                struct Node *res = search(hashTable, targetDate); 
                if (res) printf("Βρέθηκε: Cumulative = %lld\n", res->cumulative);
                else printf("Η ημερομηνία δεν βρέθηκε στον πίνακα.\n");
                break;
            }
            case 2:
                printf("Δώστε νέα τιμή Cumulative: ");
                scanf("%lld", &newVal);
                update(hashTable, targetDate, newVal);
                break;
            case 3:
                deleteNode(hashTable, targetDate);
                break;
            case 4:
                freeTable(hashTable);
                printf("Έξοδος και καθαρισμός μνήμης...\n");
                break;
            default:
                printf("Λάθος επιλογή.\n");
        }
    } while (choice != 4);

    return 0;
}

int calculate(char *date) {
    int sum = 0;
    for (int i = 0; date[i] != '\0'; i++) 
        sum += (int)date[i];
    return sum % M;
}

void insert(struct Node *table[], char *date, long long cumulative) {
    int index = calculate(date);
    struct Node *newNode = (struct Node*)malloc(sizeof(struct Node));
    strcpy(newNode->date, date);
    newNode->cumulative = cumulative;

    newNode->next = table[index];
    table[index] = newNode;
}

struct Node* search(struct Node *table[], char *date) {
    int index = calculate(date);
    struct Node *current = table[index];
    while (current != NULL) {
        if (strcmp(current->date, date) == 0) return current;
        current = current->next;
    }
    return NULL;
}

void update(struct Node *table[], char *date, long long newVal) {
    struct Node *node = search(table, date);
    if (node) {
        node->cumulative = newVal;
        printf("Η εγγραφή ενημερώθηκε σε %lld.\n", newVal);
    } else printf("Δεν βρέθηκε ημερομηνία για τροποποίηση.\n");
}

void deleteNode(struct Node *table[], char *date) {
    int index = calculate(date);
    struct Node *current = table[index];
    struct Node *previous = NULL;

    while (current != NULL && strcmp(current->date, date) != 0) { 
        current = current->next;
    }
    
    if (current == NULL) {
        printf("Η εγγραφή δεν βρέθηκε για διαγραφή.\n");
        return;
    }
    
    if (previous == NULL) table[index] = current->next;
    else previous->next = current->next;

    free(current);
    printf("Η εγγραφή %s διαγράφηκε.\n", date);
}

void loadCSV(char *filename, struct Node *table[]) {
    FILE *stream = fopen(filename, "r");
    if (!stream) {
        printf("Σφάλμα στο άνοιγμα του αρχείου %s.\n", filename);
        return;
    }
    char line[1024];
    fgets(line, 1024, stream); 
    
    while (fgets(line, 1024, stream)) {
        char *temp = strdup(line);
        char *date = NULL;
        long long cumulative = 0;
        int col = 0;

        char *token = strtok(temp, ",");
        while (token != NULL) {
            col++;
            if (col == 3) date = token;
            if (col == 10) cumulative = atoll(token);
            token = strtok(NULL, ",");
        }
        if (date != NULL) insert(table, date, cumulative);
        free(temp);
    }
    fclose(stream);
    printf("Το αρχείο φορτώθηκε με επιτυχία (m=%d).\n", M);
}

void freeTable(struct Node *table[]) {
    for (int i = 0; i < M; i++) {
        struct Node *current = table[i];
        while (current != NULL) { 
            struct Node *temp = current;
            current = current->next; 
            free(temp);
        }
        table[i] = NULL;
    }
}