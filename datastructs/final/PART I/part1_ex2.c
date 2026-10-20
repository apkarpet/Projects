#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Δομή για την αποθήκευση των εγγραφών του CSV αρχείου
struct Record {
    char direction[15];
    int year;
    char date[15];
    char weekday[10];
    char country[50];
    char commodity[100];
    char transport_mode[20];
    char measure[20];
    long long value;
    long long cumulative;
};

// Δηλώσεις συναρτήσεων
void load_data(struct Record **arr, int *n);
void swap(struct Record* a, struct Record* b);
int partition(struct Record arr[], int low, int high);
void iterativeQuickSort(struct Record arr[], int low, int high);
void heapify(struct Record arr[], int n, int i);
void heapSort(struct Record arr[], int n);

int main() {
    struct Record *data_heap, *data_quick;
    int n;

    // Φόρτωση των δεδομένων
    load_data(&data_heap, &n);
   
    // Δημιουργία πιστού αντιγράφου του πίνακα για την Quick Sort
    data_quick = (struct Record*)malloc(n * sizeof(struct Record));
    for(int i = 0; i < n; i++) data_quick[i] = data_heap[i];

    clock_t start, end;

    printf("Starting sorting for %d records (Field: Value):\n", n);
   
    // Μέτρηση χρόνου για την Heap Sort
    start = clock();
    heapSort(data_heap, n);
    end = clock();
    printf("Heap Sort: %f seconds\n", (double)(end - start) / CLOCKS_PER_SEC);

    // Μέτρηση χρόνου για την Iterative Quick Sort (Lomuto)
    start = clock();
    iterativeQuickSort(data_quick, 0, n - 1);
    end = clock();
    printf("Quick Sort: %f seconds\n", (double)(end - start) / CLOCKS_PER_SEC);
   
    // Αποδέσμευση μνήμης
    free(data_heap);
    free(data_quick);
    return 0;
}

// Βοηθητική συνάρτηση εναλλαγής δύο εγγραφών
void swap(struct Record* a, struct Record* b){
    struct Record t = *a;
    *a = *b;
    *b = t;
}

// Διαμερισμός Lomuto με βάση το τελευταίο στοιχείο (pivot)
int partition(struct Record arr[], int low, int high){
    long long pivot = arr[high].value; // Επιλογή pivot
    int i = (low - 1);

    for (int j = low; j <= high - 1; j++){
        // Ταξινόμηση κατά αύξουσα σειρά του πεδίου Value
        if (arr[j].value < pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i + 1], &arr[high]);
    return (i + 1); // Επιστροφή της τελικής θέσης του pivot
}

// Επαναληπτική Quick Sort με χειροκίνητη στοίβα (Stack) για αποφυγή κρασαρίσματος
void iterativeQuickSort(struct Record arr[], int low, int high) {
    // Δέσμευση βοηθητικής στοίβας στη memory heap
    int* stack = (int*)malloc((high - low + 1) * sizeof(int));
    int top = -1;

    // Εισαγωγή των αρχικών ορίων στη στοίβα
    stack[++top] = low;
    stack[++top] = high;

    // Επανάληψη μέχρι να αδειάσει η στοίβα
    while (top >= 0) {
        // Εξαγωγή ορίων από τη στοίβα
        high = stack[top--];
        low = stack[top--];

        // Εύρεση της σωστής θέσης του pivot
        int p = partition(arr, low, high);

        // Αν υπάρχουν στοιχεία αριστερά του pivot, μπες στη στοίβα
        if (p - 1 > low) {
            stack[++top] = low;
            stack[++top] = p - 1;
        }

        // Αν υπάρχουν στοιχεία δεξιά του pivot, μπες στη στοίβα
        if (p + 1 < high) {
            stack[++top] = p + 1;
            stack[++top] = high;
        }
    }

    free(stack); // Αποδέσμευση της στοίβας
}

// Διόρθωση σωρού (Max-Heap) για τη Heap Sort
void heapify(struct Record arr[], int n, int i){
    int max = i;
    int l = 2 * i + 1; // Αριστερό παιδί
    int r = 2 * i + 2; // Δεξί παιδί

    if (l < n && arr[l].value > arr[max].value)
        max = l;

    if (r < n && arr[r].value > arr[max].value)
        max = r;

    // Αν το μεγαλύτερο στοιχείο δεν είναι η ρίζα
    if (max != i){
        swap(&arr[i], &arr[max]);
        heapify(arr, n, max); // Αναδρομική διόρθωση του υποδέντρου
    }
}

// Κύριος αλγόριθμος Heap Sort
void heapSort(struct Record arr[], int n){
    // Κατασκευή αρχικού Max-Heap
    for (int i = n / 2 - 1; i >= 0; i--)
        heapify(arr, n, i);

    // Απόσπαση στοιχείων από το σωρό ένα προς ένα
    for (int i = n - 1; i > 0; i--){
        swap(&arr[0], &arr[i]); // Μετακίνηση της ρίζας στο τέλος
        heapify(arr, i, 0);     // Αναδόμηση του εναπομείναντος σωρού
    }
}

// Συνάρτηση ανάγνωσης και parsing του αρχείου CSV
void load_data(struct Record **arr, int *n) {
    // Προσπάθεια ανοίγματος του αρχείου με ή χωρίς κατάληξη .csv
    FILE *file = fopen("effects-of-covid-19-on-trade-at-15-december-2021-provisional", "r");
    if (!file) {
        file = fopen("effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv", "r");
    }
    if (!file) { printf("Error opening file!\n"); exit(1); }

    char line[1024];
    fgets(line, 1024, file); // Προσπέραση της γραμμής επικεφαλίδων

    *arr = (struct Record*)malloc(111438 * sizeof(struct Record));
    int i = 0;
    
    // Ανάγνωση γραμμών και τεμαχισμός (tokenization) με βάση το κόμμα
    while (fgets(line, 1024, file) && i < 111438) {
        char *token = strtok(line, ",");

        if(token) strcpy((*arr)[i].direction, token);
        token = strtok(NULL, ",");
        if(token) (*arr)[i].year = atoi(token);
        token = strtok(NULL, ",");
        if(token) strcpy((*arr)[i].date, token);
        token = strtok(NULL, ",");
        if(token) strcpy((*arr)[i].weekday, token);
        token = strtok(NULL, ",");
        if(token) strcpy((*arr)[i].country, token);
        token = strtok(NULL, ",");
        if(token) strcpy((*arr)[i].commodity, token);
        token = strtok(NULL, ",");
        if(token) strcpy((*arr)[i].transport_mode, token);
        token = strtok(NULL, ",");
        if(token) strcpy((*arr)[i].measure, token);
        token = strtok(NULL, ",");
        if(token) (*arr)[i].value = atoll(token);
        token = strtok(NULL, ",");
        if(token) (*arr)[i].cumulative = atoll(token);
        i++;
    }
    *n = i;
    printf("Successfully loaded %d records.\n", *n);
    fclose(file);
}
