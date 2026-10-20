#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Δομή κόμβου για το AVL Δέντρο
struct Node {
    char date[20];
    long long cumulative;
    struct Node *left;
    struct Node *right;
    int height; // Ύψος του κόμβου για τον έλεγχο εξισορρόπησης
};

// Δηλώσεις συναρτήσεων
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
    // Φόρτωση των δεδομένων από το αρχείο CSV κατά την εκκίνηση
    root = loadCSV("effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv", root);
    int choice;
    char targetDate[20];
    long long cumulative;
    
    do {
        choice = userSelection(); // Εμφάνιση μενού και λήψη επιλογής χρήστη

        switch(choice) {
            case 1: // Ενδοδιατεταγμένη διάσχιση (In-order)
                printf("\n%-15s | %-15s\n", "Date", "Cumulative");
                printf("-------------------------------\n");
                inorder(root); 
                break;
            case 2: // Αναζήτηση βάσει ημερομηνίας
                printf("Give a date (DD/MM/YYYY): ");
                scanf("%s", targetDate);
                struct Node* found = searchDate(root, targetDate);
                if (found) printf("Found: %lld\n", found->cumulative);
                else printf("Not Found.\n");
                break;
            case 3: // Τροποποίηση τιμής
                printf("Give a date (DD/MM/YYYY): ");
                scanf("%s", targetDate);
                printf("New Value: ");
                scanf("%lld", &cumulative);
                root = update(root, targetDate, cumulative);
                break;
            case 4: // Διαγραφή εγγραφής
                printf("Give a date for deletion (DD/MM/YYYY): ");
                scanf("%s", targetDate);
                root = deleteNode(root, targetDate);
                break;
            case 5: // Έξοδος και καθαρισμός μνήμης
                printf("EXITING...\n");
                freeTree(root);
                root = NULL;
                break;
            default:
                printf("WRONG CHOICE.\n");
        } 
    } while (choice != 5);
    return 0;
}

// Επιστρέφει το ύψος του κόμβου (0 αν είναι NULL)
int height(struct Node *N){
    if (N == NULL) return 0;
    return N -> height;
}

// Δημιουργία ενός νέου κόμβου
struct Node* newNode(char *date, long long cumulative){
    struct Node* node = (struct Node*)malloc(sizeof(struct Node));
    strcpy(node -> date, date);
    node -> cumulative = cumulative;
    node -> left = node -> right = NULL;
    node -> height = 1; // Ο νέος κόμβος αρχικά μπαίνει ως φύλλο
    return node;
}

// Δεξιά στροφή υποδέντρου (εξισορρόπηση AVL)
struct Node* rightRotate(struct Node *y){
    struct Node *x = y -> left;
    struct Node *t = x -> right;
    x -> right = y;
    y -> left = t;
    // Ενημέρωση υψών
    y -> height = 1 + (height(y -> left) > height(y -> right) ? height(y -> left) : height(y -> right));
    x -> height = 1 + (height(x -> left) > height(x -> right) ? height(x -> left) : height(x -> right));
    return x;
}

// Αριστερή στροφή υποδέντρου (εξισορρόπηση AVL)
struct Node* leftRotate(struct Node *x){
    struct Node *y = x -> right;
    struct Node *t = y -> left;
    y -> left = x;
    x -> right = t;
    // Ενημέρωση υψών
    x -> height = 1 + (height(x -> left) > height(x -> right) ? height(x -> left) : height(x -> right));
    y -> height = 1 + (height(y -> left) > height(y -> right) ? height(y -> left) : height(y -> right));
    return y;
}

// Εμφάνιση του μενού επιλογών
int userSelection(){
    int x;
    printf("\n--- COVID-19 Trade Data Menu ---\n");
    printf("1. Tree Representation (In-order Traversal)\n");
    printf("2. Search based on Date\n");
    printf("3. Modify Cumulative\n");
    printf("4. Delete Registration\n");
    printf("5. EXIT\n");
    printf("Select : ");  

    if(scanf("%d", &x) != 1) {
        while(getchar() != '\n'); // Καθαρισμός buffer σε περίπτωση λάθος εισαγωγής
        return -1;
    }
    return x;
}

// Ανάγνωση δεδομένων από το αρχείο CSV και εισαγωγή στο δέντρο
struct Node* loadCSV(char* filename, struct Node* root){
    FILE* stream = fopen(filename, "r");
    if(!stream) {
        printf("Error - File %s Not Found\n", filename);
        return root;
    }

    char line[1024];
    fgets(line, 1024, stream); // Προσπέραση της γραμμής επικεφαλίδων

    while (fgets(line, 1024, stream)){
        char *temp = strdup(line);
        char *date = NULL;
        long long cumulative = 0;
        int col = 0;

        // Tokenization της γραμμής με βάση το κόμμα
        char* token = strtok(temp, ",");
        while (token != NULL){
            col++;
            if (col == 3)  date = token;              // 3η στήλη: Ημερομηνία
            if (col == 10) cumulative = atoll(token); // 10η στήλη: Cumulative τιμή
            token = strtok(NULL, ",");
        }
        if (date != NULL){
            root = insert(root, date, cumulative); // Εισαγωγή στο AVL δέντρο
        }
        free(temp);
    }
    fclose(stream);
    printf("File %s uploaded successfully\n", filename);
    return root;
}

// Αναδρομική εισαγωγή κόμβου με αυτόματη εξισορρόπηση (AVL)
struct Node* insert(struct Node* node, char* date, long long cumulative){
    if (node == NULL)
        return newNode(date, cumulative);

    // Σύγκριση αλφαριθμητικών (date) για την κατεύθυνση εισαγωγής
    if (strcmp(date, node -> date) < 0)
        node -> left = insert(node -> left, date, cumulative);
    else if(strcmp(date, node -> date) > 0)
        node -> right = insert(node -> right, date, cumulative);
    else return node; // Δεν επιτρέπονται διπλότυπα κλειδιά

    // Ενημέρωση ύψους τρέχοντος κόμβου
    node -> height = 1 + (height(node -> left) > height(node -> right) ? height(node -> left) : height(node -> right));

    // Έλεγχος συντελεστή ισορροπίας (Balance Factor)
    int balance = height(node -> left) - height(node -> right);

    // Περίπτωση Left-Left
    if (balance > 1 && strcmp(date, node -> left -> date) < 0)
        return rightRotate(node);

    // Περίπτωση Right-Right
    if(balance < -1 && strcmp(date, node -> right -> date) > 0)
        return leftRotate(node);
    
    // Περίπτωση Left-Right
    if (balance > 1 && strcmp(date, node -> left -> date) > 0){
        node -> left = leftRotate(node -> left);
        return rightRotate(node);
    }
    // Περίπτωση Right-Left
    if (balance < -1 && strcmp(date, node -> right -> date) < 0){
        node -> right = rightRotate(node -> right);
        return leftRotate(node);
    }
    return node;
}

// Αναζήτηση κόμβου βάσει ημερομηνίας (κλασική δυαδική αναζήτηση)
struct Node* searchDate(struct Node* root, char* target){
    if (root == NULL || strcmp(root -> date, target) == 0)
        return root;
    if (strcmp(target, root -> date) < 0){
        return searchDate(root -> left, target);
    }
    return searchDate(root -> right, target);
}

// Ενημέρωση της τιμής cumulative σε συγκεκριμένη ημερομηνία
struct Node* update(struct Node* root, char* target, long long newVal){
    if (root == NULL){
        printf("Error - Date %s not found.\n", target);
        return  NULL;
    }

    if (strcmp(target, root -> date) < 0){
        root -> left = update(root -> left, target, newVal);
    }
    else if (strcmp(target, root -> date) > 0){
        root -> right = update(root -> right, target, newVal);
    }
    else {
        root -> cumulative = newVal; // Εύρεση και αντικατάσταση τιμής
        printf("Cumulative value for date %s updated - New Value : %lld.\n", target, newVal);
    }
    return root;
}

// Διαγραφή κόμβου από το AVL δέντρο με επαναφορά της ισορροπίας
struct Node* deleteNode(struct Node* root, char* date){
    if (root == NULL) return root;

    if (strcmp(date, root -> date) < 0)
        root -> left = deleteNode(root->left, date);
    else if (strcmp(date, root -> date) > 0)
        root -> right = deleteNode(root -> right, date);
    else {
        // Κόμβος με έναν ή κανέναν υποκόμβο
        if((root -> left == NULL) || (root -> right == NULL)){
            struct Node *temp = root -> left ? root -> left : root -> right;

            if(temp == NULL) {
                temp = root;
                root = NULL;
            } else 
                *root = *temp; // Αντιγραφή περιεχομένων του μη-κενικού παιδιού
            free(temp);
        } else {
            // Κόμβος με δύο παιδιά: Εύρεση του μικρότερου στο δεξί υποδέντρο
            struct Node* temp = minimumNode(root -> right);
            strcpy(root -> date, temp -> date);
            root -> cumulative = temp -> cumulative;
            root -> right = deleteNode(root -> right, temp -> date); // Διαγραφή του διαδόχου
        }
    }
    if (root == NULL) return root;

    // Επαναϋπολογισμός ύψους και ισορροπίας μετά τη διαγραφή
    int leftH = height(root -> left);
    int rightH = height(root -> right);
    root -> height = 1 + (leftH > rightH ? leftH : rightH);
    int balance = leftH - rightH;

    // Έλεγχος και στροφές εξισορρόπησης για τις 4 περιπτώσεις (LL, LR, RR, RL)
    if (balance > 1 && height(root->left->left) >= height(root->left->right))
        return rightRotate(root);

    if (balance > 1 && height(root->left->left) < height(root->left->right)){
        root->left = leftRotate(root->left);
        return rightRotate(root);
    }

    if (balance < -1 && height(root->right->right) >= height(root->right->left))
        return leftRotate(root);

    if (balance < -1 && height(root->right->right) < height(root->right->left)) {
        root->right = rightRotate(root->right);
        return leftRotate(root);
     }
    return root;   
}

// Επιστρέφει τον κόμβο με την ελάχιστη τιμή (πιο αριστερό φύλλο)
struct Node* minimumNode(struct Node* node){
    struct Node* current = node;
    while (current -> left != NULL)
        current = current -> left;
    return current;
}

// Ενδοδιατεταγμένη εκτύπωση του δέντρου (παράγει ταξινομημένο αποτέλεσμα)
void inorder(struct Node *root){
    if (root != NULL){
        inorder(root -> left);
        printf("%-15s | %-15lld\n", root -> date, root -> cumulative);
        }
}

// Αποδέσμευση όλης της δυναμικής μνήμης του δέντρου (Post-order διάσχιση)
void freeTree(struct Node* node){
    if (node != NULL){
        freeTree(node->left);
        freeTree(node->right);
        free(node);
    }
}
