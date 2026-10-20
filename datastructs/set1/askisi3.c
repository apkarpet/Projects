#include <stdio.h>
#include <stdlib.h>

// Δομή κόμβου του Δυαδικού Δέντρου
struct Node {
    int data;
    struct Node *left;
    struct Node *right;
};

// Δομή κόμβου για την Ουρά (Queue)
// Χρησιμοποιείται για την Κατά επίπεδα διαπέραση (levelOrder)
struct QueueNode {
    struct Node* treeNode;
    struct QueueNode* next;
};

// Δομή της Ουράς με δείκτες αρχής (first) και τέλους (last)  
struct Queue {
    struct QueueNode *first, *last;
};

// Συνάρτηση δημιουργίας νέου κόμβου δέντρου
struct Node* newNode(int data) {
    struct Node* node = (struct Node*)malloc(sizeof(struct Node));
    node->data = data;
    node->left = NULL;
    node->right = NULL;
    return node;
}

// Συνάρτηση αρχικοποίησης της ουράς 
struct Queue* createQueue() {
    struct Queue* q = (struct Queue*)malloc(sizeof(struct Queue));
    q->first = q->last = NULL;
    return q;
}

// Εισαγωγή στοιχείου στην ουρά (Enqueue)
void enqueue(struct Queue* q, struct Node* treeNode) {
    struct QueueNode* temp = (struct QueueNode*)malloc(sizeof(struct QueueNode));
    temp->treeNode = treeNode;
    temp->next = NULL;
    if (q->last == NULL) {
        q->first = q->last = temp;
        return;
    }
    q->last->next = temp;
    q->last = temp;
}

// Εξαγωγή στοιχείου από την ουρά (Dequeue)  
struct Node* dequeue(struct Queue* q) {
    if (q->first == NULL) return NULL;
    struct QueueNode* temp = q->first;
    struct Node* treeNode = temp->treeNode;
    q->first = q->first->next;
    if (q->first == NULL) q->last = NULL;
    free(temp);
    return treeNode;
}

// Έλεγχος αν η ουρά είναι άδεια
int isQueueEmpty(struct Queue* q) {
    return q->first == NULL;
}

// --- (i) Διαπέραση κατά επίπεδα (Level Order) --- 
void levelOrder(struct Node* root) {
    if (root == NULL) return;

    struct Queue* q = createQueue();
    enqueue(q, root); // 1. Εισαγωγή ρίζας στην ουρά

    while (!isQueueEmpty(q)) { // 2. Όσο υπάρχουν κόμβοι στην ουρά
        struct Node* current = dequeue(q); // Πάρε τον επόμενο κόμβο 
        printf("%d ", current->data);     // Εκτύπωσε την τιμή 

        // Εισαγωγή αριστερού παιδιού αν υπάρχει 
        if (current->left != NULL) 
            enqueue(q, current->left);

        // Εισαγωγή δεξιού παιδιού αν υπάρχει
        if (current->right != NULL) 
            enqueue(q, current->right);
    }
    free(q);
}

// --- (ii) Προδιατεταγμένη διαπέραση (Pre-order) ---
// Ρίζα -> Αριστερά -> Δεξιά 
void preOrder(struct Node* root) {
    if (root == NULL) return;
    printf("%d ", root->data);
    preOrder(root->left);
    preOrder(root->right);
}

// --- (ii) Μεταδιατεταγμένη διαπέραση (Post-order)  --- 
// Αριστερά -> Δεξιά -> Ρίζα 
void postOrder(struct Node* root) {
    if (root == NULL) return;
    postOrder(root->left);
    postOrder(root->right);
    printf("%d ", root->data);
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
    

    printf("--- Tree Traversals ---\n");

    printf("Level Order: ");
    levelOrder(root); 
    printf("\n");

    printf("Pre-order:   ");
    preOrder(root);  
    printf("\n");

    printf("Post-order:  ");
    postOrder(root); 
    printf("\n");

    printf("\nPress Enter to exit...");
    getchar();
    return 0;
}
