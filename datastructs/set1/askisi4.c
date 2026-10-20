#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node *left, *right;
};

// Συνάρτηση για δημιουργία κόμβου 
struct Node* newNode(int data) {
    struct Node* node = (struct Node*)malloc(sizeof(struct Node));
    node->data = data;
    node->left = node->right = NULL;
    return node;
}

// --- Υπολογισμός Ύψους Δέντρου --- 
// Χρησιμοποιεί τη λογική της Post-order διέλευσης
int calculateHeight(struct Node* root) {
    if (root == NULL) {
        return -1; // Ένα κενό δέντρο έχει ύψος -1. Η ρίζα (μόνη της) έχει ύψος 0.
    }

    // Υπολογίζουμε αναδρομικά το ύψος του αριστερού και δεξιού υποδέντρου
    int leftHeight = calculateHeight(root->left);
    int rightHeight = calculateHeight(root->right);

    // Το ύψος του τρέχοντος κόμβου είναι το μέγιστο των παιδιών του + 1
    if (leftHeight > rightHeight)
        return leftHeight + 1;
    else
        return rightHeight + 1;
}

//--- Υπολογισμός και Εκτύπωση Βάθους Κόμβων --- 
// Χρησιμοποιεί τη λογική της Pre-order διέλευσης 
void calculateDepth(struct Node* root, int currentDepth) {
    if (root == NULL) return;

    // Εκτυπώνουμε την τιμή του κόμβου και το βάθος του
    printf("Node: %d | Depth: %d\n", root->data, currentDepth);

    // Καλούμε αναδρομικά για τα παιδιά, αυξάνοντας το βάθος κατά 1
    calculateDepth(root->left, currentDepth + 1);
    calculateDepth(root->right, currentDepth + 1);
}

int main() {
   // Δημιουργία ενός δέντρου
    struct Node* root = newNode(10);
    root->left = newNode(20);
    root->right = newNode(30);
    root->left->right = newNode(50);
    root->right->left = newNode(60);
    root->right->right = newNode(70);
    root->left->right->left = newNode(100);
    root->right->right->left = newNode(140);
    root->right->right->right = newNode(150);
    root->right->right->right->left = newNode(300);

    printf("--- Tree Statistics ---\n");

    // Εύρεση Ύψους
    int height = calculateHeight(root);
    printf("Total Tree Height: %d\n\n", height);

    // Εύρεση Βάθους 
    printf("Individual Nodes Depth:\n");
    calculateDepth(root, 0);

    printf("\nPress Enter to exit...");
    getchar();
    return 0;
}
