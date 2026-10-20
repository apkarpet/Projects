#include <stdio.h>
#include <string.h>

#define MAX 100

/*
--- 3 COMPLEX CORRECT EXPRESSIONS (50-80 chars) ---
1: (([{[5+8]/4}+[5+9]]+({7/8}+1)+[7+9])*(({3-5}+4)-[1])*{[7-4]-4}+1)
Length: 65

2: ({([(9+8)+9]+[5/1]/4)-({6-7}-8)+{4*2}}-([(3/3)*1]*{8+4})*({8-8}-8))
Length: 67

3: {[[([4+8]/6)*(3*1)+6]+[(9)/8]-(3)-1]+{{{6+8}}*{5+1}}/({4}/6)}
Length: 61

--- 3 RANDOM INVALID EXPRESSIONS ---
1: (052)60+2-57)[454[})874{+6838{(2[+8/{6-258][+-[}{28]059)-*+//59346490-)
Length: 71

2: 2[09+3}9)/{/-988/0)7733[72131764+7194--325[}5)[3(8786(2{[4-{{]{0}1]]-
Length: 69

3: {23+3{2-{80+15-9*1)7/){{]2428[3{]+(87(3]203835/01)16]9
Length: 54
*/

// Δομή Στοίβας 
struct Stack {
    int first;
    char elements[MAX];
};

// Αρχικοποίησης στοίβας
void initStack(struct Stack *s) {
    s->first = -1;
}

// Έλεγχος αν η στοίβα είναι γεμάτη
int isFull(struct Stack *s) {
    return s->first == MAX - 1;
}

// Έλεγχος αν η στοίβα είναι άδεια
int isEmpty(struct Stack *s) {
    return s->first == -1;
}

// Εισαγωγή στοιχείου στη στοίβα (Push)
void push(struct Stack *s, char c) {
    if (!isFull(s)) {
        s->elements[++(s->first)] = c;
    }
}

// Εξαγωγή στοιχείου από τη στοίβα (Pop)
char pop(struct Stack *s) {
    if (!isEmpty(s)) {
        return s->elements[(s->first)--];
    }
    return '\0';
}

// Συνάρτηση για το αν ταιριάζουν
int checkPair(char char1, char char2) {
    if (char1 == '(' && char2 == ')') return 1;
    if (char1 == '{' && char2 == '}') return 1;
    if (char1 == '[' && char2 == ']') return 1;
    return 0;
}

// Η κύρια συνάρτηση ελέγχου της έκφρασης
int checkExpression(char exp[]) {
    struct Stack s;
    initStack(&s);
    
    for (int i = 0; i < strlen(exp); i++) {
        // Αν είναι χαρακτήρας ανοίγματος, push στη στοίβα
        if (exp[i] == '(' || exp[i] == '{' || exp[i] == '[') {
            push(&s, exp[i]);
        }
        // Αν είναι χαρακτήρας κλεισίματος
        else if (exp[i] == '}' || exp[i] == ']' || exp[i] == ')') {
            // Αν βρούμε κλείσιμο αλλά η στοίβα είναι άδεια, τότε είναι λάθος
            if (isEmpty(&s)) return 0;
            
            // Βγάζουμε το στοιχείο από την κορυφή και ελέγχουμε αν ταιριάζει
            if (!checkPair(pop(&s), exp[i])) {
                return 0;
            }
        }
    }
    
    // Αν στο τέλος η στοίβα είναι άδεια, η έκφραση είναι σωστή 
    return isEmpty(&s);
}

int main() {
    char exp[MAX];
    
    printf("--- EXPRESSION CHECKER WITH STACK ---\n");
    
    while (1) {
        printf("\nGIVE THE EXPRESSION (type 'EXIT' to quit): ");
        scanf("%s", exp);
        
        if (strcmp(exp, "EXIT") == 0) {
            printf("EXITING ...\n");
            break;
        }
        
        if (checkExpression(exp)) {
            printf("Result: 1 (The expression is CORRECT)\n");
        } else {
            printf("Result: 0 (The expression is WRONG)\n");
        }
    }

    return 0;
}
