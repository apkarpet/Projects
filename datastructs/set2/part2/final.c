#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define M 11

struct BSTNode {
    char date[20];
    long long cumulative;
    int height; //λογω AVL
    struct BSTNode *left, *right;
};

struct HashNode {
    char date[20];
    long long cumulative;
    struct HashNode *next;
};

// ΠΡΩΤΟΤΥΠΑ ΣΥΝΑΡΤΗΣΕΩΝ 
struct BSTNode* newBSTNode(char *date, long long cumulative);
struct BSTNode* insertBSTDate(struct BSTNode* node, char *date, long long cumulative);
struct BSTNode* insertBSTCumulative(struct BSTNode* node, char *date, long long cumulative);
void findMinMax(struct BSTNode* root);

struct BSTNode* searchBST(struct BSTNode* root, char *date);
struct BSTNode* deleteBSTNode(struct BSTNode* root, char *date);

void printInOrder(struct BSTNode* root);

int calculateHash(char *date);
void insertHash(struct HashNode *table[], char *date, long long cumulative);
struct HashNode* searchHash(struct HashNode *table[], char *date);
void deleteHash(struct HashNode *table[], char *date);

void loadData(char *filename, struct BSTNode **bstRoot, struct HashNode *table[], int mode);
int compareDates(char *d1, char *d2);

// Βοηθητικες συναρτησεις για τα AVL
int height(struct BSTNode *N);
int max(int a, int b);
struct BSTNode* rightRotate(struct BSTNode *y);
struct BSTNode* leftRotate(struct BSTNode *x);
int getBalance(struct BSTNode *N);

int main() {
    struct BSTNode *root = NULL;
    struct HashNode *hashTable[M] = {NULL};
    int typeChoice, bstChoice, action;
    char targetDate[20];
    long long newVal;
    char *filename = "effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv";

    do {
        printf("\nΜΕΝΟΥ\n");
        printf("1. Χρήση Δομής BST (Δυαδικό Δέντρο)\n");
        printf("2. Χρήση Δομής Hash Table (Κατακερματισμός)\n");
        printf("3. Έξοδος\n");
        printf("Επιλογή: ");
        if (scanf("%d", &typeChoice) != 1) break;

        if (typeChoice == 1) {
            printf("\n--- Ρυθμίσεις BST ---\n");
            printf("1. Φόρτωση βάσει Ημερομηνίας\n");
            printf("2. Φόρτωση βάσει Cumulative (Εύρεση Min/Max)\n");
            printf("3. Επιστροφή\n");
            printf("Επιλογή: ");
            scanf("%d", &bstChoice);

            if (bstChoice == 1 || bstChoice == 2) {
                root = NULL;
                loadData(filename, &root, NULL, bstChoice);

                if (bstChoice == 1) {
                    int bstAction;
                    char searchDate[20];
                    long long newCum;
                    do {
                        printf("\n--- Μενού BST (ταξινόμηση κατά Ημερομηνία) ---\n");
                        printf("1. Εμφάνιση όλων (In-order)\n");
                        printf("2. Αναζήτηση Cumulative βάσει Ημερομηνίας\n");
                        printf("3. Τροποποίηση Cumulative βάσει Ημερομηνίας\n");
                        printf("4. Διαγραφή εγγραφής βάσει Ημερομηνίας\n");
                        printf("5. Επιστροφή\n");
                        printf("Επιλογή: ");
                        scanf("%d", &bstAction);

                        if (bstAction >= 2 && bstAction <= 4) {
                            printf("Δώστε ημερομηνία (π.χ. 31/12/2020): ");
                            scanf("%s", searchDate);
                        }

                        if (bstAction == 1) {
                            printf("\n%-12s | %s\n", "Ημερομηνία", "Cumulative");
                            printf("-------------------------------------\n");
                            printInOrder(root);
                            printf("-------------------------------------\n");
                        } else if (bstAction == 2) {
                            struct BSTNode *res = searchBST(root, searchDate);
                            if (res) printf("Cumulative για %s: %lld\n", res->date, res->cumulative);
                            else printf("Δεν βρέθηκε.\n");
                        } else if (bstAction == 3) {
                            struct BSTNode *res = searchBST(root, searchDate);
                            if (res) {
                                printf("Νέα τιμή Cumulative: ");
                                scanf("%lld", &newCum);
                                res->cumulative = newCum;
                                printf("Ενημερώθηκε.\n");
                            } else printf("Δεν βρέθηκε.\n");
                        } else if (bstAction == 4) {
                            root = deleteBSTNode(root, searchDate);
                            printf("Διαγράφηκε (αν υπήρχε).\n");
                        }
                    } while (bstAction != 5);

                } else if (bstChoice == 2) {
                    findMinMax(root);
                }
            }

        } else if (typeChoice == 2) {
            loadData(filename, NULL, hashTable, 3);
            do {
                printf("\n--- Μενού Hashing (m=11) ---\n");
                printf("1. Αναζήτηση τιμής\n");
                printf("2. Τροποποίηση τιμής\n");
                printf("3. Διαγραφή εγγραφής\n");
                printf("4. Επιστροφή στο Κεντρικό Μενού\n");
                printf("Επιλογή: ");
                scanf("%d", &action);

                if (action >= 1 && action <= 3) {
                    printf("Δώστε ημερομηνία (π.χ. 31/12/2020): ");
                    scanf("%s", targetDate);
                }

                if (action == 1) {
                    struct HashNode *res = searchHash(hashTable, targetDate);
                    if (res) printf("Αποτέλεσμα: %lld\n", res->cumulative);
                    else printf("Δεν βρέθηκε.\n");
                } else if (action == 2) {
                    struct HashNode *res = searchHash(hashTable, targetDate);
                    if (res) {
                        printf("Νέα τιμή: ");
                        scanf("%lld", &newVal);
                        res->cumulative = newVal;
                        printf("Ενημερώθηκε.\n");
                    } else printf("Δεν βρέθηκε.\n");
                } else if (action == 3) {
                    deleteHash(hashTable, targetDate);
                }
            } while (action != 4);
        }

    } while (typeChoice != 3);

    printf("Τερματισμός εφαρμογής.\n");
    return 0;
}
//  ΥΛΟΠΟΙΗΣΗ ΣΥΝΑΡΤΗΣΕΩΝ 

struct BSTNode* newBSTNode(char *date, long long cumulative) {
    struct BSTNode* node = (struct BSTNode*)malloc(sizeof(struct BSTNode));
    if (node) {
        strcpy(node->date, date);
        node->cumulative = cumulative;
        node->height = 1; // Απαραίτητο για το AVL
        node->left = node->right = NULL;
    }
    return node;
}
struct BSTNode* insertBSTDate(struct BSTNode* node, char *date, long long cumulative) {
    // Κανονική εισαγωγή BST
    if (node == NULL) {
        struct BSTNode* newNode = newBSTNode(date, cumulative);
        newNode->height = 1;
        return newNode;
    }

    int cmp = compareDates(date, node->date);
    if (cmp < 0)
        node->left = insertBSTDate(node->left, date, cumulative);
    else if (cmp > 0)
        node->right = insertBSTDate(node->right, date, cumulative);
    else
        return node; // Δεν επιτρέπονται διπλότυπα κλειδιά

    // Ενημέρωση ύψους
    node->height = 1 + max(height(node->left), height(node->right));

    // Έλεγχος ισορροπίας
    int balance = getBalance(node);

    // Left, left case
    if (balance > 1 && compareDates(date, node->left->date) < 0)
        return rightRotate(node);

    // Right right case
    if (balance < -1 && compareDates(date, node->right->date) > 0)
        return leftRotate(node);

    // Left Right Case
    if (balance > 1 && compareDates(date, node->left->date) > 0) {
        node->left = leftRotate(node->left);
        return rightRotate(node);
    }

    // Right Left Case
    if (balance < -1 && compareDates(date, node->right->date) < 0) {
        node->right = rightRotate(node->right);
        return leftRotate(node);
    }

    return node;
}
struct BSTNode* insertBSTCumulative(struct BSTNode* node, char *date, long long cumulative) {
    if (node == NULL) {
        struct BSTNode* newNode = newBSTNode(date, cumulative);
        newNode->height = 1;
        return newNode;
    }

    if (cumulative < node->cumulative)
        node->left = insertBSTCumulative(node->left, date, cumulative);
    else
        node->right = insertBSTCumulative(node->right, date, cumulative);

    // Ενημέρωση ύψους και εξισορρόπηση
    node->height = 1 + max(height(node->left), height(node->right));
    int balance = getBalance(node);

    if (balance > 1 && cumulative < node->left->cumulative)
        return rightRotate(node);
    if (balance < -1 && cumulative > node->right->cumulative)
        return leftRotate(node);
    if (balance > 1 && cumulative > node->left->cumulative) {
        node->left = leftRotate(node->left);
        return rightRotate(node);
    }
    if (balance < -1 && cumulative < node->right->cumulative) {
        node->right = rightRotate(node->right);
        return leftRotate(node);
    }
    return node;
}
void findMinMax(struct BSTNode* root) {
    if (!root) return;
    struct BSTNode *minN = root, *maxN = root;
    while (minN->left) minN = minN->left;
    while (maxN->right) maxN = maxN->right;
    printf("\nMIN: %s | %lld\nMAX: %s | %lld\n", minN->date, minN->cumulative, maxN->date, maxN->cumulative);
}

int calculateHash(char *date) {
    int sum = 0;
    for (int i = 0; date[i] != '\0'; i++) sum += (int)date[i];
    return sum % M;
}

void insertHash(struct HashNode *table[], char *date, long long cumulative) {
    int idx = calculateHash(date);
    struct HashNode *newNode = (struct HashNode*)malloc(sizeof(struct HashNode));
    strcpy(newNode->date, date);
    newNode->cumulative = cumulative;
    newNode->next = table[idx];
    table[idx] = newNode;
}

struct HashNode* searchHash(struct HashNode *table[], char *date) {
    int idx = calculateHash(date);
    struct HashNode *curr = table[idx];
    while (curr) {
        if (strcmp(curr->date, date) == 0) return curr;
        curr = curr->next;
    }
    return NULL;
}

void deleteHash(struct HashNode *table[], char *date) {
    int idx = calculateHash(date);
    struct HashNode *curr = table[idx], *prev = NULL;
    while (curr && strcmp(curr->date, date) != 0) {
        prev = curr; curr = curr->next;
    }
    if (!curr) return;
    if (!prev) table[idx] = curr->next;
    else prev->next = curr->next;
    free(curr);
    printf("Διαγράφηκε.\n");
}

void loadData(char *filename, struct BSTNode **bstRoot, struct HashNode *table[], int mode) {
    FILE *f = fopen(filename, "r");
    if (!f) { printf("Αρχείο μη διαθέσιμο.\n"); return; }
    char line[1024];
    fgets(line, 1024, f);
    while (fgets(line, 1024, f)) {
        char *temp = strdup(line);
        char *date = NULL; long long cum = 0; int col = 0;
        char *tok = strtok(temp, ",");
        while (tok) {
            col++;
            if (col == 3) date = tok;
            if (col == 10) cum = atoll(tok);
            tok = strtok(NULL, ",");
        }
        if (date) {
            if (mode == 1) *bstRoot = insertBSTDate(*bstRoot, date, cum);
            else if (mode == 2) *bstRoot = insertBSTCumulative(*bstRoot, date, cum);
            else if (mode == 3) insertHash(table, date, cum);
        }
        free(temp);
    }
    fclose(f);
}

void printInOrder(struct BSTNode* root) {
    if (root != NULL) {
        printInOrder(root->left);
        printf("Ημερομηνία: %-12s | Cumulative: %lld\n", root->date, root->cumulative);
        printInOrder(root->right);
    }
}

int compareDates(char *d1, char *d2) {
    int day1, mon1, year1, day2, mon2, year2;
    sscanf(d1, "%d/%d/%d", &day1, &mon1, &year1);
    sscanf(d2, "%d/%d/%d", &day2, &mon2, &year2);
    if (year1 != year2) return year1 - year2;
    if (mon1 != mon2)   return mon1 - mon2;
    return day1 - day2;
}

struct BSTNode* searchBST(struct BSTNode* root, char *date) {
  if (root == NULL) return NULL;
  int cmp = compareDates(date, root->date);
  if (cmp == 0) return root;
  if (cmp < 0) return searchBST(root->left, date);
  return searchBST(root->right, date);
}

struct BSTNode* deleteBSTNode(struct BSTNode* root, char *date) {
    if (root == NULL) return root;

    int cmp = compareDates(date, root->date);
    if (cmp < 0)
        root->left = deleteBSTNode(root->left, date);
    else if (cmp > 0)
        root->right = deleteBSTNode(root->right, date);
    else {
        if ((root->left == NULL) || (root->right == NULL)) {
            struct BSTNode *temp = root->left ? root->left : root->right;
            if (temp == NULL) {
                temp = root;
                root = NULL;
            } else
                *root = *temp;
            free(temp);
        } else {
            struct BSTNode* temp = root->right;
            while (temp->left != NULL) temp = temp->left;
            strcpy(root->date, temp->date);
            root->cumulative = temp->cumulative;
            root->right = deleteBSTNode(root->right, temp->date);
        }
    }

    if (root == NULL) return root;

    root->height = 1 + max(height(root->left), height(root->right));
    int balance = getBalance(root);

    if (balance > 1 && getBalance(root->left) >= 0)
        return rightRotate(root);
    if (balance > 1 && getBalance(root->left) < 0) {
        root->left = leftRotate(root->left);
        return rightRotate(root);
    }
    if (balance < -1 && getBalance(root->right) <= 0)
        return leftRotate(root);
    if (balance < -1 && getBalance(root->right) > 0) {
        root->right = rightRotate(root->right);
        return leftRotate(root);
    }
    return root;
}
int height(struct BSTNode *N) {
    if (N == NULL) return 0;
    return N->height;
}

int max(int a, int b) {
    return (a > b) ? a : b;
}

struct BSTNode* rightRotate(struct BSTNode *y) {
    struct BSTNode *x = y->left;
    struct BSTNode *T2 = x->right;
    x->right = y;
    y->left = T2;
    y->height = max(height(y->left), height(y->right)) + 1;
    x->height = max(height(x->left), height(x->right)) + 1;
    return x;
}

struct BSTNode* leftRotate(struct BSTNode *x) {
    struct BSTNode *y = x->right;
    struct BSTNode *T2 = y->left;
    y->left = x;
    x->right = T2;
    x->height = max(height(x->left), height(x->right)) + 1;
    y->height = max(height(y->left), height(y->right)) + 1;
    return y;
}

int getBalance(struct BSTNode *N) {
    if (N == NULL) return 0;
    return height(N->left) - height(N->right);
}
