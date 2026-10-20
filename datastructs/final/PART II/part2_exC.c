#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define M 11 // Το μέγεθος του πίνακα κατακερματισμού (m = 11)

// Δομή κόμβου για τη συνδεδεμένη λίστα (αλυσίδα) κάθε θέσης
struct Node {
    char date[20];
    long long cumulative;
    struct Node *next;
};

// Δηλώσεις συναρτήσεων
int calculate(char *date);
void insert(struct Node *table[], char *date, long long cumulative);
struct Node* search(struct Node *table[], char *date);
void update(struct Node *table[], char *date, long long newVal);
void deleteNode(struct Node *table[], char *date); 
void freeTable(struct Node *table[]);
void loadCSV(char *filename, struct Node *table[]);

int main() {
    // Αρχικοποίηση του Hash Table με NULL σε όλες τις θέσεις
    struct Node *hashTable[M] = {NULL};

    char filename[] = "effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv";

    // Φόρτωση των δεδομένων από το CSV αρχείο
    loadCSV(filename, hashTable);

    int choice;
    char targetDate[20];
    long long newVal;

    do {
        // Εμφάνιση μενού επιλογών
        printf("\n--- COVID-19 Hashing Menu (m = 11) ---\n");
        printf("1. Search Cumulative based on Date\n");
        printf("2. Modify Cumulative based on Date\n");
        printf("3. Delete Registration based on Date\n");
        printf("4. EXIT\n");
        printf("Select : ");
        
        if (scanf("%d", &choice) != 1) {
            while(getchar() != '\n'); // Καθαρισμός buffer εισόδου σε περίπτωση λάθους
            continue;
        }

        // Αν ο χρήστης επέλεξε αναζήτηση, τροποποίηση ή διαγραφή, ζήτα ημερομηνία
        if (choice >= 1 && choice <= 3) {
            printf("Give a Date (DD/MM/YYYY): ");
            scanf("%s", targetDate);
        }

        switch(choice) {
            case 1: { // Αναζήτηση βάσει ημερομηνίας
                struct Node *res = search(hashTable, targetDate); 
                if (res) printf("Found: Cumulative = %lld\n", res->cumulative);
                else printf("Date did not found in registrations.\n");
                break;
            }
            case 2: // Τροποποίηση τιμής
                printf("Give a new Cumulative value: ");
                scanf("%lld", &newVal);
                update(hashTable, targetDate, newVal);
                break;
            case 3: // Διαγραφή εγγραφής
                deleteNode(hashTable, targetDate);
                break;
            case 4: // Έξοδος και αποδέσμευση όλης της μνήμης
                freeTable(hashTable);
                printf("EXITING ...\n");
                break;
            default:
                printf("WRONG CHOICE.\n");
        }
    } while (choice != 4);

    return 0;
}

// Συνάρτηση Κατακερματισμού: Προσθέτει τα ASCII των χαρακτήρων και παίρνει το υπόλοιπο mod M
int calculate(char *date) {
    int sum = 0;
    for (int i = 0; date[i] != '\0'; i++) 
        sum += (int)date[i];
    return sum % M; // Επιστρέφει index από 0 έως M-1
}

// Εισαγωγή νέας εγγραφής στην αρχή της λίστας (Chaining) της κατάλληλης θέσης
void insert(struct Node *table[], char *date, long long cumulative) {
    int index = calculate(date); // Υπολογισμός της θέσης στον πίνακα
    struct Node *newNode = (struct Node*)malloc(sizeof(struct Node));
    strcpy(newNode->date, date);
    newNode->cumulative = cumulative;

    // Εισαγωγή του νέου κόμβου στην κεφαλή της συνδεδεμένης λίστας
    newNode->next = table[index];
    table[index] = newNode;
}

// Αναζήτηση εγγραφής στη συνδεδεμένη λίστα της συγκεκριμένης θέσης index
struct Node* search(struct Node *table[], char *date) {
    int index = calculate(date); // Βρες σε ποια λίστα ανήκει η ημερομηνία
    struct Node *current = table[index];
    
    // Γραμμική αναζήτηση μέσα στην αλυσίδα
    while (current != NULL) {
        if (strcmp(current->date, date) == 0) return current; // Βρέθηκε
        current = current->next;
    }
    return NULL; // Δεν βρέθηκε
}

// Ενημέρωση της τιμής cumulative μιας ημερομηνίας
void update(struct Node *table[], char *date, long long newVal) {
    struct Node *node = search(table, date); // Χρήση της search για εύρεση του κόμβου
    if (node) {
        node->cumulative = newVal;
        printf("Registration updated : %lld.\n", newVal);
    } else printf("Date not found to modify.\n");
}

// Διαγραφή κόμβου από τη λίστα κατακερματισμού
void deleteNode(struct Node *table[], char *date) {
    int index = calculate(date); 
    struct Node *current = table[index];
    struct Node *previous = NULL;

    // Αναζήτηση του κόμβου κρατώντας και τον προηγούμενο
    while (current != NULL && strcmp(current->date, date) != 0) { 
        previous = current;
        current = current->next;
    }
    
    if (current == NULL) {
        printf("Registration not found to delete.\n");
        return;
    }
    
    // Αφαίρεση του κόμβου από την αλυσίδα
    if (previous == NULL) table[index] = current->next; // Ήταν ο πρώτος κόμβος της λίστας
    else previous->next = current->next;               // Ήταν ενδιάμεσος ή τελευταίος

    free(current); // Αποδέσμευση μνήμης
    printf("Registration %s deleted.\n", date);
}

// Ανάγνωση δεδομένων από το αρχείο CSV και εισαγωγή στο Hash Table
void loadCSV(char *filename, struct Node *table[]) {
    FILE *stream = fopen(filename, "r");
    if (!stream) {
        printf("Error while file %s opening.\n", filename);
        return;
    }
    char line[1024];
    fgets(line, 1024, stream); // Προσπέραση της γραμμής επικεφαλίδων
    
    // Ανάγνωση γραμμή προς γραμμή
    while (fgets(line, 1024, stream)) {
        char *temp = strdup(line);
        char *date = NULL;
        long long cumulative = 0;
        int col = 0;

        // Τεμαχισμός της γραμμής (parsing) με βάση το κόμμα
        char *token = strtok(temp, ",");
        while (token != NULL) {
            col++;
            if (col == 3) date = token;              // 3η στήλη: Ημερομηνία
            if (col == 10) cumulative = atoll(token); // 10η στήλη: Cumulative
            token = strtok(NULL, ",");
        }
        if (date != NULL) insert(table, date, cumulative); // Εισαγωγή στο Hash Table
        free(temp);
    }
    fclose(stream);
    printf("File uploaded successfully (m = %d).\n", M);
}

// Αποδέσμευση όλης της δυναμικής μνήμης που δεσμεύτηκε για τις λίστες του Hash Table
void freeTable(struct Node *table[]) {
    for (int i = 0; i < M; i++) { // Διάσχιση όλων των θέσεων του πίνακα
        struct Node *current = table[i];
        while (current != NULL) { 
            struct Node *temp = current;
            current = current->next; 
            free(temp); // Αποδέσμευση κάθε κόμβου της αλυσίδας
        }
        table[i] = NULL; // Επαναφορά της θέσης σε NULL
    }
}
