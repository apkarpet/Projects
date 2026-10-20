#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Δομή κόμβου για το Δυαδικό Δέντρο Αναζήτησης (BST)
struct Node {
    char date[20];
    long long cumulative;
    struct Node *left;
    struct Node *right;
};

// Δηλώσεις συναρτήσεων
struct Node* newNode(char *date, long long cumulative);
struct Node* loadCSV(char* filename, struct Node* root);
struct Node* insert(struct Node* node, char* date, long long cumulative);
void minimumNode(struct Node* node);
void maxNode(struct Node* node);
void freeTree(struct Node* node);
void inorder(struct Node* node);

int main () {
    struct Node *root = NULL;
    // Φόρτωση των δεδομένων από το CSV αρχείο στην εκκίνηση
    root = loadCSV("effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv", root);
    int choice;
    
    do {
        // Εμφάνιση μενού επιλογών
        printf("\n--- BST Menu (Ordered by Cumulative) ---\n");
        printf("1. View all (Ascending Order) \n");
        printf("2. Find Day(s) with MINIMUM Cumulative\n");
        printf("3. Find Day(s) with MAXIMUM Cumulative\n");
        printf("4. EXIT\n");
        printf("Select : ");
        if (scanf("%d", &choice) != 1) break;

        switch(choice) {
            case 1: // Εμφάνιση όλων σε αύξουσα σειρά τιμής
                printf("\n%-15s | %-15s\n", "Date", "Cumulative");
                inorder(root);
                break;
            case 2: // Εύρεση της ελάχιστης τιμής
                minimumNode(root);
                break;
            case 3: // Εύρεση της μέγιστης τιμής
                maxNode(root);
                break;
            case 4: // Έξοδος και αποδέσμευση μνήμης
                freeTree(root);
                printf("EXITING...\n");
                break;
            default:
                printf("WRONG CHOICE.\n");
        }
    } while (choice != 4);
    return 0;
}

// Δημιουργία και αρχικοποίηση ενός νέου κόμβου
struct Node* newNode(char *date, long long cumulative){
    struct Node* node = (struct Node*)malloc(sizeof(struct Node));
    strcpy(node->date, date);
    node -> cumulative = cumulative;
    node -> left = node -> right = NULL; // Τα παιδιά αρχικά είναι NULL
    return node;
}

// Ανάγνωση του αρχείου CSV και εισαγωγή των στοιχείων στο δέντρο
struct Node* loadCSV(char* filename, struct Node* root){
    FILE* stream = fopen(filename, "r");
    if(!stream) {
        printf("Error - File %s not found.\n", filename);
        return root;
    }

    char line[1024];
    fgets(line, 1024, stream); // Προσπέραση της γραμμής με τις επικεφαλίδες

    // Ανάγνωση γραμμή προς γραμμή
    while (fgets(line, 1024, stream)){
        char *temp = strdup(line);
        char *date = NULL;
        long long cumulative = 0;
        int col = 0;

        // Τεμαχισμός της γραμμής με βάση το κόμμα
        char* token = strtok(temp, ",");
        while (token != NULL){
            col++;
            if (col == 3)  date = token;              // 3η στήλη: Ημερομηνία
            if (col == 10) cumulative = atoll(token); // 10η στήλη: Cumulative
            token = strtok(NULL, ",");
        }
        if (date != NULL){
            root = insert(root, date, cumulative); // Εισαγωγή του κόμβου στο BST
        }
        free(temp);
    }
    fclose(stream);
    printf("File %s uploaded successfully.\n", filename);
    return root;
}

// Αναδρομική εισαγωγή κόμβου στο BST με βάση το πεδίο cumulative
struct Node* insert(struct Node* node, char *date, long long cumulative){
    if (node == NULL) return newNode(date, cumulative);

    // Αν η νέα τιμή είναι μικρότερη, πάει αριστερά, αλλιώς πάει δεξιά
    if (cumulative < node -> cumulative)
        node -> left = insert(node -> left, date, cumulative);
    else 
        node -> right = insert(node -> right, date, cumulative);
    
    return node;
}

// Εύρεση της ελάχιστης τιμής (βρίσκεται στο πιο αριστερό φύλλο του BST)
void minimumNode(struct Node* root){
    if (root == NULL) {
        printf("Tree is empty.\n");
        return;
    }
    struct Node* current = root;
    // Συνεχής μετακίνηση αριστερά
    while (current -> left != NULL)
        current = current -> left;
        
    printf("\nMinimum Value :\n");
    printf("Date: %s | Cumulative: %lld\n", current->date, current->cumulative);
}

// Εύρεση της μέγιστης τιμής (βρίσκεται στο πιο δεξί φύλλο του BST)
void maxNode(struct Node* root){
    if (root == NULL) {
        printf("Tree is empty.\n");
        return;
    }
    struct Node* current = root;
    // Συνεχής μετακίνηση δεξιά
    while (current -> right != NULL)
        current = current->right;
        
    printf("\nMaximum Value:\n");
    printf("Date: %s | Cumulative: %lld\n", current->date, current->cumulative);
}

// Αποδέσμευση όλης της δυναμικής μνήμης του δέντρου (Post-order διάσχιση)
void freeTree(struct Node* node){
    if (node != NULL){
        freeTree(node->left);
        freeTree(node->right);
        free(node); // Αποδέσμευση του ίδιου του κόμβου
    }
}

// Ενδοδιατεταγμένη διάσχιση (In-order): Εμφανίζει τα στοιχεία σε αύξουσα σειρά
void inorder(struct Node* root) {
    if (root != NULL) {
        inorder(root->left);  // 1. Επίσκεψη αριστερού υποδέντρου
        printf("%-15s | %-15lld\n", root->date, root->cumulative); // 2. Εκτύπωση ρίζας
        inorder(root->right); // 3. Επίσκεψη δεξιού υποδέντρου
    }
}
