#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Node {
    char date[20];
    long long cumulative;
    struct Node *left;
    struct Node *right;
};

struct Node* newNode(char *date, long long cumulative);

struct Node* loadCSV(char* filename, struct Node* root);
struct Node* insert(struct Node* node, char* date, long long cumulative);
void minimumNode(struct Node* node);
void maxNode(struct Node* node);
void freeTree(struct Node* node);
void inorder(struct Node* node);

int main () {
    struct Node *root = NULL;
    root = loadCSV("effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv", root);
    int choice;
    char targetDate[20];
    do {
        printf("\n--- BST Menu (Ordered by Cumulative) ---\n");
        printf("1. Προβολή όλων (In-order)\n");
        printf("2. Εύρεση Ημέρας/Ημερών με ΕΛΑΧΙΣΤΟ Cumulative\n");
        printf("3. Εύρεση Ημέρας/Ημερών με ΜΕΓΙΣΤΟ Cumulative\n");
        printf("4. Έξοδος\n");
        printf("Επιλογή: ");
        if (scanf("%d", &choice) != 1) break;

        switch(choice) {
            case 1:
                printf("\n%-15s | %-15s\n", "Date", "Cumulative");
                inorder(root);
                break;
            case 2:
                minimumNode(root);
                break;
            case 3:
                maxNode(root);
                break;
            case 4:
                freeTree(root);
                printf("Έξοδος...\n");
                break;
            default:
                printf("Λάθος επιλογή.\n");
        }
    } while (choice != 4);
    return 0;
}

struct Node* newNode(char *date, long long cumulative){
    struct Node* node = (struct Node*)malloc(sizeof(struct Node));
    strcpy(node->date, date);
    node -> cumulative = cumulative;
    node -> left = node -> right = NULL;
    return node;
}

struct Node* loadCSV(char* filename, struct Node* root){
    FILE* stream = fopen(filename, "r");
    if(!stream) {
        printf("Σφάλμα - Το αρχείο %s δεν βρέθηκε.\n", filename);
        return root;
    }

    char line[1024];
    fgets(line, 1024, stream);

    while (fgets(line, 1024, stream)){
        char *temp = strdup(line);

        char *date = NULL;
        long long cumulative = 0;
        int col = 0;

        char* token = strtok(temp, ",");
        while (token != NULL){
            col++;
            if (col == 3){
                date = token;
            }
            if (col == 10) {
                cumulative = atoll(token);
            }
            token = strtok(NULL, ",");
        }
        if (date != NULL){
            root = insert(root, date, cumulative);
        }
        free(temp);
    }
    fclose(stream);
    printf("Το αρχείο %s φορτώθηκε με επιτυχία.\n", filename);
    return root;
}
struct Node* insert(struct Node* node, char *date, long long cumulative){
    if (node == NULL) return newNode(date, cumulative);

    if (cumulative < node -> cumulative)
        node -> left = insert(node -> left, date, cumulative);
    else node -> right = insert(node -> right, date, cumulative);
    
    return node;
}

void minimumNode(struct Node* root){
    if (root == NULL) {
        printf("Το δέντρο είναι άδειο.\n");
        return;
    }
    struct Node* current = root;
    while (current -> left != NULL)
        current = current -> left;
    printf("\nΕλάχιστη τιμή:\n");
    printf("Ημερομηνία: %s | Cumulative: %lld\n", current->date, current->cumulative);
}

void maxNode(struct Node* root){
    if (root == NULL) {
        printf("Το δέντρο είναι άδειο.\n");
        return;
    }
    struct Node* current = root;
    while (current -> right != NULL)
        current = current->right;
    printf("\nΜέγιστη τιμή:\n");
    printf("Ημερομηνία: %s | Cumulative: %lld\n", current->date, current->cumulative);
}

void freeTree(struct Node* node){
    if (node != NULL){
        freeTree(node->left);
        freeTree(node->right);
        free(node);
    }
}
void inorder(struct Node* root) {
    if (root != NULL) {
        inorder(root->left);
        printf("%-15s | %-15lld\n", root->date, root->cumulative);
        inorder(root->right);
    }
}