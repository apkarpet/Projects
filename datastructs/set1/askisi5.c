#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node *left, *right;
};

struct Node* newNode(int data) {
    struct Node* node = (struct Node*)malloc(sizeof(struct Node));
    node->data = data;
    node->left = node->right = NULL;
    return node;
}

// Εύρεση της θέσης μιας τιμής στην Ενδοδιατεταγμένη διαπέραση 
int findIndex(int arr[], int start, int end, int value) {
    for (int i = start; i <= end; i++) {
        if (arr[i] == value) return i;
    }
    return -1;
}

// Ανάπλαση από Προδιατεταγμένη διαπέραση (Pre) και Ενδοδιατεταγμένη διαπέραση (In) 
struct Node* buildTree(int in[], int pre[], int inStart, int inEnd, int* preIdx) {
    if (inStart > inEnd) return NULL;

    // Το τρέχον στοιχείο της Προδιατεταγμένης διαπέρασης είναι η ρίζα 
    struct Node* root = newNode(pre[(*preIdx)++]);

    if (inStart == inEnd) return root;

    // Βρίσκουμε τη ρίζα στην Ενδοδιατεταγμένη διαπέραση για να χωρίσουμε αριστερό/δεξί υποδέντρο 
    int inIdx = findIndex(in, inStart, inEnd, root->data);

    root->left = buildTree(in, pre, inStart, inIdx - 1, preIdx);
    root->right = buildTree(in, pre, inIdx + 1, inEnd, preIdx);

    return root;
}

// Συνάρτηση Επιβεβαίωσης από ’σκηση 4 (PPre-order) 
void confirmTraversal(struct Node* node) {
    if (node == NULL) return;
    printf("%d ", node->data);
    confirmTraversal(node->left);
    confirmTraversal(node->right);
}

int main() {
    // Δεδομένα Εισόδου (Αλληλουχίες τιμών) 
    int inOrder[] = {20, 100, 50, 10, 60, 30, 140, 70, 300, 150};
    int preOrder[] = {10, 20, 50, 100, 30, 60, 70, 140, 150, 300};
    int n = sizeof(inOrder) / sizeof(inOrder[0]);
    int preIdx = 0;

    printf("--- Tree Reconstruction ---\n");
    
    // Εκτέλεση Ανάπλασης 
    struct Node* root = buildTree(inOrder, preOrder, 0, n - 1, &preIdx);

    // Επιβεβαίωση 
    printf("Reconstructed Tree (Pre-order verification): ");
    confirmTraversal(root);
    
    // Έλεγχος αν η ρίζα είναι σωστή 
    printf("\nRoot of the new tree is: %d\n", root->data);

    printf("\nPress Enter to exit...");
    getchar();
    return 0;
}
