#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Δομή για την αποθήκευση των εγγραφών του CSV
struct Record {
    char direction[15];
    int year;
    char date[15];
    char weekday[15];
    char country[50];
    char commodity[100];
    char transport_mode[20];
    char measure[20];
    long long value;
    long long cumulative;
};

// Μετατρέπει το string DD/MM/YYYY σε αριθμό YYYYMMDD για εύκολη σύγκριση
long long dateToKey(char* dateStr) {
    int day, month, year;
    if (sscanf(dateStr, "%d/%d/%d", &day, &month, &year) == 3) {
        return (long long)year * 10000 + (long long)month * 100 + day;
    }
    return 0;
}

void load_data(struct Record **arr, int *n);
void quickSortByDate(struct Record arr[], int low, int high);
int binarySearch(struct Record arr[], int n, long long target);
int interpolationSearch(struct Record arr[], int n, long long target);

int main() {
    struct Record *data;
    int n = 0;

    load_data(&data, &n); // Φόρτωση των δεδομένων από το αρχείο

    printf("Sorting data by Date for searching...\n\n");
    quickSortByDate(data, 0, n - 1); // Ταξινόμηση πριν την αναζήτηση

    char targetDate[15];
    printf("Enter search date (DD/MM/YYYY): ");
    scanf("%14s", targetDate);
    long long targetKey = dateToKey(targetDate);

    clock_t start, end;

    // Εκτέλεση και χρονομέτρηση της Δυαδικής Αναζήτησης (Binary Search)
    start = clock();
    int res1 = binarySearch(data, n, targetKey);
    end = clock();
    printf("Binary Search: Time = %f sec (Index: %d)\n", (double)(end - start)/CLOCKS_PER_SEC, res1);

    // Εκτέλεση και χρονομέτρηση της Αναζήτησης Παρεμβολής (Interpolation Search)
    start = clock();
    int res2 = interpolationSearch(data, n, targetKey);
    end = clock();
    printf("Interpolation Search: Time = %f sec (Index: %d)\n", (double)(end - start)/CLOCKS_PER_SEC, res2);

    // Εμφάνιση αποτελεσμάτων αν βρεθεί η ημερομηνία
    if (res1 != -1) {
        printf("\nResult Found:\n");
        printf("Date: %s | Value: %lld | Cumulative: %lld\n", data[res1].date, data[res1].value, data[res1].cumulative);
    } else {
        printf("\nDate not found.\n");
    }

    printf("\n----------------------------------------\n");

    free(data); // Αποδέσμευση της μνήμης
    return 0;
}

// Αλγόριθμος Κλασικής Δυαδικής Αναζήτησης
int binarySearch(struct Record arr[], int n, long long target) {
    int low = 0, high = n - 1;
    while (low <= high) {
        int mid = low + (high - low) / 2;
        long long midKey = dateToKey(arr[mid].date);
        if (midKey == target) return mid;
        if (midKey < target) low = mid + 1;
        else high = mid - 1;
    }
    return -1;
}

// Αλγόριθμος Αναζήτησης Παρεμβολής
int interpolationSearch(struct Record arr[], int n, long long target) {
    int low = 0, high = n - 1;
    while (low <= high && target >= dateToKey(arr[low].date) && target <= dateToKey(arr[high].date)) {
        if (low == high) {
            if (dateToKey(arr[low].date) == target) return low;
            break;
        }

        long long lowKey = dateToKey(arr[low].date);
        long long highKey = dateToKey(arr[high].date);

        // Τύπος υπολογισμού της πιθανής θέσης (εκτίμηση)
        int pos = low + (int)(((double)(high - low) / (highKey - lowKey)) * (target - lowKey));

        if (pos < low || pos > high) break; // Έλεγχος ορίων πίνακα

        long long posKey = dateToKey(arr[pos].date);
        if (posKey == target) return pos;
        if (posKey < target) low = pos + 1;
        else high = pos - 1;
    }
    return -1;
}

// Βοηθητική συνάρτηση εναλλαγής δύο εγγραφών
void swap(struct Record *a, struct Record *b) {
    struct Record t = *a; *a = *b; *b = t;
}

// Συνάρτηση διαμερισμού (Partition) για την QuickSort
int partitionByDate(struct Record arr[], int low, int high) {
    long long pivot = dateToKey(arr[high].date);
    int i = low - 1;
    for (int j = low; j <= high - 1; j++) {
        if (dateToKey(arr[j].date) < pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i + 1], &arr[high]);
    return (i + 1);
}

// Βελτιστοποιημένη QuickSort για την αποφυγή Stack Overflow σε μεγάλα datasets
void quickSortByDate(struct Record arr[], int low, int high) {
    while (low < high) {
        int pi = partitionByDate(arr, low, high);
        if (pi - low < high - pi) {
            quickSortByDate(arr, low, pi - 1);
            low = pi + 1;
        } else {
            quickSortByDate(arr, pi + 1, high);
            high = pi - 1;
        }
    }
}

// Ανάγνωση και επεξεργασία του αρχείου CSV
void load_data(struct Record **arr, int *n) {
    FILE *file = fopen("effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv", "r");
    if (!file) { printf("Error: file not found!\n"); exit(1); }
    
    char line[1024];
    fgets(line, 1024, file); // Προσπέραση της πρώτης γραμμής (επικεφαλίδες)
    
    *arr = malloc(111438 * sizeof(struct Record)); // Δέσμευση μνήμης
    int i = 0;
    
    // Ανάγνωση γραμμή προς γραμμή και κοπή σε tokens με βάση το κόμμα
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
    fclose(file);
    printf("Successfully loaded %d records.\n", i);
}
