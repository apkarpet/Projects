#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define M 11 // Μέγεθος του Hash Table (m = 11)

// Δομή κόμβου για το Δυαδικό Δέντρο Αναζήτησης (BST)
struct BSTNode {
    char date[20];
    long long cumulative;
    struct BSTNode *left, *right;
};

// Δομή κόμβου για τον Πίνακα Κατακερματισμού (Hash Table με Chaining)
struct HashNode {
    char date[20];
    long long cumulative;
    struct HashNode *next;
};

// Δηλώσεις συναρτήσεων
struct BSTNode* newBSTNode(char *date, long long cumulative);
struct BSTNode* insertBSTDate(struct BSTNode* node, char *date, long long cumulative);
struct BSTNode* insertBSTCumulative(struct BSTNode* node, char *date, long long cumulative);
void findMinMax(struct BSTNode* root);
void printInOrder(struct BSTNode* root);
int calculateHash(char *date);
void insertHash(struct HashNode *table[], char *date, long long cumulative);
struct HashNode* searchHash(struct HashNode *table[], char *date);
void deleteHash(struct HashNode *table[], char *date);
void loadData(char *filename, struct BSTNode **bstRoot, struct HashNode *table[], int mode);

int main() {
    struct BSTNode *root = NULL; // Ρίζα του BST
    struct HashNode *hashTable[M] = {NULL}; // Πίνακας Κατακερματισμού
    int typeChoice, bstChoice, action;
    char targetDate[20];
    long long newVal;
    char *filename = "effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv";

    do {
        // Κεντρικό Μενού Επιλογών
        printf("\nMain Menu\n");
        printf("1. BST Structure (AVL Tree)\n");
        printf("2. Hash Table (Hashing)\n");
        printf("3. EXIT\n");
        printf("Select : ");
        if (scanf("%d", &typeChoice) != 1) break;

        if (typeChoice == 1) { // --- ΕΠΙΛΟΓΗ 1: ΔΥΑΔΙΚΟ ΔΕΝΤΡΟ ---
            printf("\n--- BST Settings ---\n");
            printf("1. Load based on Date\n");
            printf("2. Load based on Cumulative (Find Min/Max)\n");
            printf("3. <<< BACK \n");
            printf("Select : ");
            scanf("%d", &bstChoice);

            if (bstChoice == 1 || bstChoice == 2) {
                root = NULL; // Μηδενισμός προηγούμενου δέντρου
                loadData(filename, &root, NULL, bstChoice); // Φόρτωση δεδομένων στο BST
                
                if (bstChoice == 1) {
                    printf("\n--- Ordered Data (In-Order) ---\n");
                    printInOrder(root); // Εκτύπωση ταξινομημένων δεδομένων βάσει ημερομηνίας
                    printf("---------------------------------------\n");
                } else if (bstChoice == 2) {
                    findMinMax(root); // ’μεση εύρεση Min/Max λόγω της δομής του δέντρου
                }
            }
        }
        else if (typeChoice == 2) { // --- ΕΠΙΛΟΓΗ 2: ΠΙΝΑΚΑΣ ΚΑΤΑΚΕΡΜΑΤΙΣΜΟΥ ---
            loadData(filename, NULL, hashTable, 3); // Φόρτωση δεδομένων στο Hash Table
            do {
                printf("\n--- Hashing Menu (m = 11) ---\n");
                printf("1. Search Value \n");
                printf("2. Modify Value \n");
                printf("3. Delete Registration \n");
                printf("4. <<< BACK \n");
                printf("Select : ");
                scanf("%d", &action);
                
                if (action >= 1 && action <= 3) {
                    printf("Give a date (DD/MM/YYYY): ");
                    scanf("%s", targetDate);
                }

                if (action == 1) { // Αναζήτηση στο Hash Table
                    struct HashNode *res = searchHash(hashTable, targetDate);
                    if (res) printf("Result: %lld\n", res->cumulative);
                    else printf("Not Found\n");
                } else if (action == 2) { // Τροποποίηση στο Hash Table
                    struct HashNode *res = searchHash(hashTable, targetDate);
                    if (res) {
                        printf("New Value : ");
                        scanf("%lld", &newVal);
                        res->cumulative = newVal;
                        printf("Updated.\n");
                    } else printf("Not Found\n");
                } else if (action == 3) { // Διαγραφή από το Hash Table
                    deleteHash(hashTable, targetDate);
                }
            } while (action != 4);
        }
    } while (typeChoice != 3);

    printf("EXITING...\n");
    return 0;
}

// Δημιουργία και αρχικοποίηση νέου κόμβου BST
struct BSTNode* newBSTNode(char *date, long long cumulative) {
    struct BSTNode* node = (struct BSTNode*)malloc(sizeof(struct BSTNode));
    if (node) {
        strcpy(node->date, date);
        node->cumulative = cumulative;
        node->left = node->right = NULL;
    }
    return node;
}

// Εισαγωγή στο BST με βάση αλφαριθμητική σύγκριση της ημερομηνίας (strcmp)
struct BSTNode* insertBSTDate(struct BSTNode* node, char *date, long long cumulative) {
    if (node == NULL) return newBSTNode(date, cumulative);
    if (strcmp(date, node->date) < 0)
        node->left = insertBSTDate(node->left, date, cumulative);
    else if (strcmp(date, node->date) > 0)
        node->right = insertBSTDate(node->right, date, cumulative);
    return node;
}

// Εισαγωγή στο BST με βάση την αριθμητική τιμή του cumulative
struct BSTNode* insertBSTCumulative(struct BSTNode* node, char *date, long long cumulative) {
    if (node == NULL) return newBSTNode(date, cumulative);
    if (cumulative < node->cumulative)
        node->left = insertBSTCumulative(node->left, date, cumulative);
    else
        node->right = insertBSTCumulative(node->right, date, cumulative);
    return node;
}

// Εύρεση Min/Max στο BST (Min = τέρμα αριστερά, Max = τέρμα δεξιά)
void findMinMax(struct BSTNode* root) {
    if (!root) return;
    struct BSTNode *minN = root, *maxN = root;
    while (minN->left) minN = minN->left;   // Μετακίνηση στο μικρότερο στοιχείο
    while (maxN->right) maxN = maxN->right; // Μετακίνηση στο μεγαλύτερο στοιχείο
    printf("\nMIN: %s | %lld\nMAX: %s | %lld\n", minN->date, minN->cumulative, maxN->date, maxN->cumulative);
}

// Hash Function: ’θροισμα ASCII χαρακτήρων της ημερομηνίας mod M
int calculateHash(char *date) {
    int sum = 0;
    for (int i = 0; date[i] != '\0'; i++) sum += (int)date[i];
    return sum % M;
}

// Εισαγωγή στο Hash Table (Chaining στην αρχή της συνδεδεμένης λίστας)
void insertHash(struct HashNode *table[], char *date, long long cumulative) {
    int idx = calculateHash(date); // Εύρεση θέσης (bucket)
    struct HashNode *newNode = (struct HashNode*)malloc(sizeof(struct HashNode));
    strcpy(newNode->date, date);
    newNode->cumulative = cumulative;
    newNode->next = table[idx]; // Σύνδεση με το προηγούμενο πρώτο στοιχείο
    table[idx] = newNode;       // Ο νέος κόμβος γίνεται κεφαλή της λίστας
}

// Αναζήτηση στο Hash Table με γραμμική διάσχιση της αλυσίδας στη θέση idx
struct HashNode* searchHash(struct HashNode *table[], char *date) {
    int idx = calculateHash(date);
    struct HashNode *curr = table[idx];
    while (curr) {
        if (strcmp(curr->date, date) == 0) return curr; // Βρέθηκε
        curr = curr->next;
    }
    return NULL; // Δεν υπάρχει
}

// Διαγραφή κόμβου από το Hash Table με αναπροσαρμογή των δεικτών next
void deleteHash(struct HashNode *table[], char *date) {
    int idx = calculateHash(date);
    struct HashNode *curr = table[idx], *prev = NULL;
    
    // Αναζήτηση του κόμβου στην αλυσίδα
    while (curr && strcmp(curr->date, date) != 0) {
        prev = curr; curr = curr->next;
    }
    if (!curr) return; // Δεν βρέθηκε
    
    // Αφαίρεση του κόμβου από τη λίστα
    if (!prev) table[idx] = curr->next; // Ήταν το πρώτο στοιχείο
    else prev->next = curr->next;       // Ήταν ενδιάμεσο στοιχείο
    
    free(curr); // Αποδέσμευση μνήμης
    printf("Deleted.\n");
}

// Ανάγνωση του αρχείου CSV και επιλογή δομής εισαγωγής βάσει του mode
void loadData(char *filename, struct BSTNode **bstRoot, struct HashNode *table[], int mode) {
    FILE *f = fopen(filename, "r");
    if (!f) { printf("File not found.\n"); return; }
    char line[1024];
    fgets(line, 1024, f); // Προσπέραση επικεφαλίδας
    
    while (fgets(line, 1024, f)) {
        char *temp = strdup(line);
        char *date = NULL; long long cum = 0; int col = 0;
        char *tok = strtok(temp, ",");
        
        while (tok) {
            col++;
            if (col == 3) date = tok;              // 3η στήλη: Ημερομηνία
            if (col == 10) cum = atoll(tok);       // 10η στήλη: Cumulative
            tok = strtok(NULL, ",");
        }
        if (date) {
            if (mode == 1)       *bstRoot = insertBSTDate(*bstRoot, date, cum);       // BST με βάση Date
            else if (mode == 2)  *bstRoot = insertBSTCumulative(*bstRoot, date, cum); // BST με βάση Cumulative
            else if (mode == 3)  insertHash(table, date, cum);                        // Hash Table
        }
        free(temp);
    }
    fclose(f);
}

// Ενδοδιατεταγμένη (In-Order) εκτύπωση του BST (παράγει ταξινομημένο output)
void printInOrder(struct BSTNode* root) {
    if (root != NULL) {
        printInOrder(root->left);
        printf("Date: %-12s | Cumulative: %lld\n", root->date, root->cumulative);
        printInOrder(root->right);
    }
}
