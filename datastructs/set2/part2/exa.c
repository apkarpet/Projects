#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct Node {
    char date[20];
    long long cumulative;
    struct Node *left;
    struct Node *right;
    int height;
};

int height(struct Node *N);
struct Node* newNode(char *date, long long cumulative);

struct Node* rightRotate(struct Node *y);
struct Node* leftRotate(struct Node *y);

void inorder(struct Node *root);

int userSelection();

struct Node* loadCSV(char* filename, struct Node* root);
struct Node* insert(struct Node* node, char* date, long long cumulative);

struct Node* searchDate(struct Node* root, char* target);
struct Node* update(struct Node* root, char*target, long long newVal);
struct Node* deleteNode(struct Node* root, char* date);
struct Node* minimumNode(struct Node* node);

void freeTree(struct Node* node);

int main () {
    struct Node *root = NULL;
    root = loadCSV("effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv", root);
    int choice;
    char targetDate[20];
    long long cumulative;
    do {
        choice = userSelection();

        switch(choice) {
            case 1:
                printf("\n%-15s | %-15s\n", "Date", "Cumulative");
                printf("-------------------------------\n");
                inorder(root); 
                break;
            case 2:
                printf("Δώστε ημερομηνία (π.χ. 31/12/2020): ");
                scanf("%s", targetDate);
                struct Node* found = searchDate(root, targetDate);
                if (found) printf("Βρέθηκε: %lld\n", found->cumulative);
                else printf("Δεν βρέθηκε.\n");
                break;
            case 3:
                printf("Δώστε ημερομηνία: ");
                scanf("%s", targetDate);
                printf("Νέα τιμή: ");
                scanf("%lld", &cumulative);
                root = update(root, targetDate, cumulative);
                break;
            case 4:
                printf("Δώστε ημερομηνία για διαγραφή: ");
                scanf("%s", targetDate);
                root = deleteNode(root, targetDate);
                break;
            case 5:
                printf("Έξοδος...\n");
                freeTree(root);
                root = NULL;
                break;
            default:
                printf("Λάθος επιλογή.\n");
        } 
    }while (choice != 5);
    return 0;
}

int height(struct Node *N){
    if (N == NULL) return 0;
    return N -> height;
}

struct Node* newNode(char *date, long long cumulative){
    struct Node* node = (struct Node*)malloc(sizeof(struct Node));
    strcpy(node -> date, date);
    node -> cumulative = cumulative;
    node -> left = node -> right = NULL;
    node -> height = 1;
    return node;
}

struct Node* rightRotate(struct Node *y){
    struct Node *x = y -> left;
    struct Node *t = x -> right;
    x -> right = y;
    y -> left = t;
    y -> height = 1 + (height(y -> left) > height(y -> right) ? height(y -> left) : height(y -> right));
    x -> height = 1 + (height(x -> left) > height(x -> right) ? height(x -> left) : height(x -> right));
    return x;
}

struct Node* leftRotate(struct Node *x){
    struct Node *y = x -> right;
    struct Node *t = y -> left;
    y -> left = x;
    x -> right = t;
    x -> height = 1 + (height(x -> left) > height(x -> right) ? height(x -> left) : height(x -> right));
    y -> height = 1 + (height(y -> left) > height(y -> right) ? height(y -> left) : height(y -> right));
    return y;
}

int userSelection(){
    int x;
    printf("\n--- COVID-19 Trade Data Menu ---\n");
    printf("1. Προβολή Δέντρου (In-order)\n");
    printf("2. Αναζήτηση βάσει Ημερομηνίας\n");
    printf("3. Τροποποίηση Cumulative\n");
    printf("4. Διαγραφή Εγγραφής\n");
    printf("5. Έξοδος\n");
    printf("Επιλογή: ");  

    if(scanf("%d", &x) != 1) {
        while(getchar() != '\n');
        return -1;
    }
    return x;
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
struct Node* insert(struct Node* node, char* date, long long cumulative){
    if (node == NULL)
        return newNode(date, cumulative);

    if (strcmp(date, node -> date) < 0)
        node -> left = insert(node -> left, date, cumulative);
    else if(strcmp(date, node -> date) > 0)
        node -> right = insert(node -> right, date, cumulative);
    else return node;

    node -> height = 1 + (height(node -> left) > height(node -> right) ? height(node -> left) : height(node -> right));

    int balance = height(node -> left) - height(node -> right);

    if (balance > 1 && strcmp(date, node -> left -> date) < 0)
        return rightRotate(node);

    if(balance < -1 && strcmp(date, node -> right -> date) > 0)
        return leftRotate(node);
    
    if (balance > 1 && strcmp(date, node -> left -> date) > 0){
        node -> left = leftRotate(node -> left);
        return rightRotate(node);
    }
    if (balance < -1 && strcmp(date, node -> right -> date) < 0){
        node -> right = rightRotate(node -> right);
        return leftRotate(node);
    }
    return node;
}
struct Node* searchDate(struct Node* root, char* target){
    if (root == NULL || strcmp(root -> date, target) == 0)
        return root;
    if (strcmp(target, root -> date) < 0){
        return searchDate(root -> left, target);
    }
    return searchDate(root -> right, target);
}
struct Node* update(struct Node* root, char* target, long long newVal){
    if (root == NULL){
        printf("Σφάλμα - Η ημερομηνία %s δεν βρέθηκε.\n", target);
        return  NULL;
    }

    if (strcmp(target, root -> date) < 0){
        root -> left = update(root -> left, target, newVal);
    }
    else if (strcmp(target, root -> date) > 0){
        root -> right = update(root -> right, target, newVal);
    }
    else {
        root -> cumulative = newVal;
        printf("Η τιμή cumulative για την ημερομηνία %s ενημερώθηκε - νέα τιμή: %lld.\n", target, newVal);
    }
    return root;
}
struct Node* deleteNode(struct Node* root, char* date){
    if (root == NULL) return root;

    if (strcmp(date, root -> date) < 0)
        root -> left = deleteNode(root->left, date);
    else if (strcmp(date, root -> date) > 0)
        root -> right = deleteNode(root -> right, date);
    else {
        if((root -> left == NULL) || (root -> right == NULL)){
            struct Node *temp = root -> left ? root -> left : root -> right;

            if(temp == NULL) {
                temp = root;
                root = NULL;
            } else 
                *root = *temp;
            free(temp);
        }else {
            struct Node* temp = minimumNode(root -> right);
            strcpy(root -> date, temp -> date);
            root -> cumulative = temp -> cumulative;
            root -> right = deleteNode(root -> right, temp -> date);
        }
    }
    if (root == NULL) return root;

    int leftH = height(root -> left);
    int rightH = height(root -> right);

    root -> height = 1 + (leftH > rightH ? leftH : rightH);

    int balance = leftH - rightH;

    if (balance > 1 && height(root->left->left) >= height(root->left->right))
        return rightRotate(root);

    // Case 2: Left-Right
    if (balance > 1 && height(root->left->left) < height(root->left->right)){
        root->left = leftRotate(root->left);
        return rightRotate(root);
    }

    // Case 3: Right-Right
    if (balance < -1 && height(root->right->right) >= height(root->right->left))
        return leftRotate(root); // Εδώ ήταν το λάθος

    // Case 4: Right-Left
    if (balance < -1 && height(root->right->right) < height(root->right->left)) {
        root->right = rightRotate(root->right);
        return leftRotate(root);
     }
    return root;   
}
struct Node* minimumNode(struct Node* node){
    struct Node* current = node;
    while (current -> left != NULL)
    current = current -> left;
    return current;
}

void inorder(struct Node *root){
    if (root != NULL){
        inorder(root -> left);
        printf("%-15s | %-15lld\n", root -> date, root -> cumulative);
        inorder(root -> right);
    }
}

void freeTree(struct Node* node){
    if (node != NULL){
        freeTree(node->left);
        freeTree(node->right);
        free(node);
    }
}