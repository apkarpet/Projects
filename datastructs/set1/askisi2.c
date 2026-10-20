#include <stdio.h>
#include <stdlib.h>

// Ορισμός δομής κόμβου
struct Node {
    int data;
    struct Node *left, *right;
};

// Συνάρτηση δημιουργίας νέου κόμβου
struct Node* newNode(int item) {
    struct Node* temp = (struct Node*)malloc(sizeof(struct Node));
    temp->data = item;
    temp->left = temp->right = NULL;
    return temp;
}

// ΑΝΑΖΗΤΗΣΗ (binaryTreeSearch)
struct Node* binaryTreeSearch(struct Node* root, int key) {
    if (root == NULL || root->data == key)
        return root;
    
    if (root->data < key)
        return binaryTreeSearch(root->right, key);
        
    return binaryTreeSearch(root->left, key);
}

// ΕΝΘΕΣΗ (insert)
struct Node* insert(struct Node* node, int key) {
    if (node == NULL) return newNode(key);

    if (key < node->data)
	    node->left = insert(node->left, key);
	else if (key > node->data)
	    node->right = insert(node->right, key);

    return node;
}

// Βοηθητική συνάρτηση για την εύρεση του μικρότερου κόμβου (για τη διαγραφή)
struct Node* minValueNode(struct Node* node) {
    struct Node* current = node;
    while (current && current->left != NULL)
        current = current->left;
    return current;
}

// ΔΙΑΓΡΑΦΗ (delete)
struct Node* deleteNode(struct Node* root, int key) {
    if (root == NULL) return root;

    if (key < root->data)
        root->left = deleteNode(root->left, key);
    else if (key > root->data)
        root->right = deleteNode(root->right, key);
    else {
        // Κόμβος με ένα ή κανένα παιδί
        if (root->left == NULL) {
            struct Node* temp = root->right;
            free(root);
            return temp;
        } else if (root->right == NULL) {
            struct Node* temp = root->left;
            free(root);
            return temp;
        }
        // Κόμβος με δύο παιδιά: εύρεση διαδόχου (inorder successor)
        struct Node* temp = minValueNode(root->right);
        root->data = temp->data;
        root->right = deleteNode(root->right, temp->data);
    }
    return root;
}

// Κύριο Πρόγραμμα
int main() {
    struct Node* root = NULL;
    int choice, value;

    printf("--- Binary Search Tree ---\n");
	
	root = insert(root, 50);
    root = insert(root, 30);
    root = insert(root, 70);
    root = insert(root, 20);
    root = insert(root, 40);
    root = insert(root, 60);
    root = insert(root, 80);
    
    while (1) {
        printf("\nOptions:\n");
        printf("1. Insert a value\n");
        printf("2. Delete a value\n");
        printf("3. Search for a value\n");
        printf("4. Exit\n");
        printf("Choice: ");
        scanf("%d", &choice);

        switch (choice) {
            case 1: {
			    printf("Enter value to insert: ");
			    scanf("%d", &value);
			
			    struct Node* exists = binaryTreeSearch(root, value);
			
			    if (exists != NULL) {
			        printf("Error: Value %d already exists. Cannot insert duplicates.\n", value);
			    } else {
			        root = insert(root, value);
			        printf("Value %d inserted successfully.\n", value);
			    }
			    break;
			}

            case 2: {
                printf("Enter value to delete: ");
                scanf("%d", &value);
                
                // ΕΛΕΓΧΟΣ: Υπάρχει η τιμή πριν τη διαγραφή;
                struct Node* exists = binaryTreeSearch(root, value);
                
                if (exists != NULL) {
                    root = deleteNode(root, value);
                    printf("Value %d found and deleted successfully.\n", value);
                } else {
                    printf("Error: Value %d does not exist in the tree. Deletion aborted.\n", value);
                }
                break;
			}

            case 3: {
                printf("Enter value to search: ");
                scanf("%d", &value);
                struct Node* found = binaryTreeSearch(root, value);
                if (found) 
                    printf("Value %d found in the tree!\n", found->data);
                else 
                    printf("Value %d NOT found.\n", value);
				break;
			}

            case 4: 
                printf("Exiting program...\n");
                return 0;

            default:
                printf("Invalid choice. Please try again.\n");
        }
    }
    return 0;
}
