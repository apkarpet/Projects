#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Ορισμός της δομής για την αναπαράσταση κάθε εγγραφής (γραμμής) του αρχείου CSV
struct Record {
    char direction[20];
    int year;
    char date[20];
    char weekday[20];
    char country[100];
    char commodity[256];
    char transport_mode[20];
    char measure[20];
    long long value;
    long long cumulative; // Το πεδίο με βάση το οποίο θα γίνει η ταξινόμηση
};

// Πρωτότυπα συναρτήσεων
void load_data(struct Record **arr, int *n);
void merge(struct Record arr[], int x, int y, int z);
void mergeSort(struct Record arr[], int x, int y);
void countingSort(struct Record arr[], int n);

int main() {
    struct Record *data_merge = NULL;    // Πίνακας για τον Merge Sort
    struct Record *data_counting = NULL; // Πίνακας για τον Counting Sort
    int n = 0;                           // Πλήθος εγγραφών που θα φορτωθούν
    clock_t start, end;

    // Φόρτωση δεδομένων από το αρχείο CSV
    load_data(&data_merge, &n);

    if (n == 0) {
        printf("No records loaded. Check if the CSV file exists.\n");
        return 1;
    }

    // Δημιουργία πιστού αντιγράφου του πίνακα για τον Counting Sort
    // έτσι ώστε και οι δύο αλγόριθμοι να δοκιμαστούν με τα ίδια ακριβώς δεδομένα
    data_counting = malloc(n * sizeof(struct Record));
    if (data_counting == NULL) {
        printf("Memory allocation failed for second array.\n");
        free(data_merge);
        return 1;
    }
    for (int i = 0; i < n; i++) {
        data_counting[i] = data_merge[i];
    }

    printf("--- Experimental Comparison for %d Records ---\n", n);

    // --- 1. Μέτρηση Χρόνου για Merge Sort ---
    start = clock();
    mergeSort(data_merge, 0, n - 1);
    end = clock();
    printf("Merge Sort time: %f seconds\n", (double)(end - start) / CLOCKS_PER_SEC);

    // --- 2. Μέτρηση Χρόνου για Counting Sort ---
    start = clock();
    countingSort(data_counting, n);
    end = clock();
    printf("Counting Sort time: %f seconds\n", (double)(end - start) / CLOCKS_PER_SEC);

    // Αποδέσμευση της δυναμικής μνήμης και των δύο πινάκων
    free(data_merge);
    free(data_counting);

    return 0;
}

// --- ΦΟΡΤΩΣΗ ΔΕΔΟΜΕΝΩΝ ΑΠΟ CSV ---
// Συναρτήση ασφαλούς ανάγνωσης που διαχειρίζεται σωστά τα κόμματα
// ακόμα και όταν αυτά βρίσκονται μέσα σε εισαγωγικά (π.χ. "Text, with, commas")
void load_data(struct Record **arr, int *n) {
    FILE *file = fopen("effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv", "r");
    if (!file) {
        printf("Error: Could not open file 'effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv'\n");
        return;
    }

    char line[4096];
    fgets(line, sizeof(line), file); // Προσπέραση της 1ης γραμμής (επικεφαλίδες / header)

    // Δέσμευση μνήμης για το μέγεθος του dataset (111.438 εγγραφές)
    *arr = malloc(111438 * sizeof(struct Record));
    if (*arr == NULL) {
        printf("Memory allocation failed!\n");
        fclose(file);
        return;
    }

    int i = 0;
    // Ανάγνωση του αρχείου γραμμή προς γραμμή
    while (fgets(line, sizeof(line), file) && i < 111438) {
        char *ptr = line;
        int col = 0;

        // Επεξεργασία όλων των στηλών της τρέχουσας γραμμής
        while (*ptr && *ptr != '\n' && *ptr != '\r') {
            char field[512] = {0};
            int f_ptr = 0;

            // Περίπτωση Α: Το πεδίο ξεκινάει με εισαγωγικά
            if (*ptr == '"') { 
                ptr++; // Προσπέραση του αρχικού εισαγωγικού
                while (*ptr && *ptr != '"') {
                    field[f_ptr++] = *ptr++; // Ανάγνωση χαρακτήρων (αγνοεί τα κόμματα εδώ)
                }
                if (*ptr == '"') ptr++; // Προσπέραση του τελικού εισαγωγικού
            } 
            // Περίπτωση Β: Κανονικό πεδίο διαχωρισμένο με κόμμα
            else { 
                while (*ptr && *ptr != ',' && *ptr != '\n' && *ptr != '\r') {
                    field[f_ptr++] = *ptr++;
                }
            }

            // Τοποθέτηση του κειμένου στο κατάλληλο πεδίο της δομής βάσει του αριθμού στήλης (col)
            switch(col) {
                case 0: strcpy((*arr)[i].direction, field); break;
                case 1: (*arr)[i].year = atoi(field); break;
                case 2: strcpy((*arr)[i].date, field); break;
                case 3: strcpy((*arr)[i].weekday, field); break;
                case 4: strcpy((*arr)[i].country, field); break;
                case 5: strcpy((*arr)[i].commodity, field); break;
                case 6: strcpy((*arr)[i].transport_mode, field); break;
                case 7: strcpy((*arr)[i].measure, field); break;
                case 8: (*arr)[i].value = atoll(field); break;
                case 9: (*arr)[i].cumulative = atoll(field); break;
            }

            if (*ptr == ',') ptr++; // Μετακίνηση μετά το κόμμα για την επόμενη στήλη
            col++;
        }
        i++; // Επόμενη εγγραφή
    }
    *n = i; // Επιστροφή του τελικού πλήθους των εγγραφών που διαβάστηκαν
    fclose(file);
    printf("Successfully loaded %d records.\n", i);
}

// --- ΑΛΓΟΡΙΘΜΟΣ MERGE SORT (Διαίρει και Βασίλευε) ---

// Η συνάρτηση merge συγχωνεύει δύο ταξινομημένα υποτμήματα του πίνακα arr[]:
// Το 1ο υπό-τμήμα είναι από το arr[x] έως το arr[y]
// Το 2ο υπό-τμήμα είναι από το arr[y+1] έως το arr[z]
void merge(struct Record arr[], int x, int y, int z) {
    int n1 = y - x + 1; // Μέγεθος του αριστερού προσωρινού πίνακα
    int n2 = z - y;     // Μέγεθος του δεξιού προσωρινού πίνακα

    // Δυναμική δέσμευση μνήμης για τους δύο προσωρινούς πίνακες L (Left) και R (Right)
    struct Record *L = malloc(n1 * sizeof(struct Record));
    struct Record *R = malloc(n2 * sizeof(struct Record));

    // Αντιγραφή των δεδομένων στους προσωρινούς πίνακες L[] και R[]
    for (int i = 0; i < n1; i++) L[i] = arr[x + i];
    for (int j = 0; j < n2; j++) R[j] = arr[y + 1 + j];

    // Συγχώνευση των πινάκων L[] και R[] πίσω στον αρχικό πίνακα arr[x...z]
    int i = 0, j = 0, k = x;
    while (i < n1 && j < n2) {
        // Ταξινόμηση σε αύξουσα σειρά με βάση το πεδίο cumulative
        if (L[i].cumulative <= R[j].cumulative) {
            arr[k] = L[i++];
        } else {
            arr[k] = R[j++];
        }
        k++;
    }

    // Αντιγραφή των στοιχείων που τυχόν περίσρεψαν στον L[]
    while (i < n1) arr[k++] = L[i++];

    // Αντιγραφή των στοιχείων που τυχόν περίσρεψαν στον R[]
    while (j < n2) arr[k++] = R[j++];

    // Αποδέσμευση της μνήμης των βοηθητικών πινάκων
    free(L);
    free(R);
}

// Η κύρια αναδρομική συνάρτηση του Merge Sort
void mergeSort(struct Record arr[], int x, int y) {
    if (x < y) {
        // Εύρεση του μέσου για τον διαχωρισμό του πίνακα σε δύο κομμάτια
        int m = x + (y - x) / 2;

        // Αναδρομική ταξινόμηση του πρώτου (αριστερού) μισού
        mergeSort(arr, x, m);
        
        // Αναδρομική ταξινόμηση του δεύτερου (δεξιού) μισού
        mergeSort(arr, m + 1, y);

        // Συγχώνευση των δύο ταξινομημένων κομματιών
        merge(arr, x, m, y);
    }
}

// --- ΑΛΓΟΡΙΘΜΟΣ COUNTING SORT (Μη-συγκριτικός Αλγόριθμος) ---
void countingSort(struct Record arr[], int n) {
    if (n <= 0) return;

    // Βήμα 1: Εύρεση της μέγιστης τιμής (max) στο πεδίο cumulative
    // προκειμένου να καθοριστεί το μέγεθος του πίνακα συχνοτήτων (count)
    long long max = arr[0].cumulative;
    for (int i = 1; i < n; i++) {
        if (arr[i].cumulative > max) max = arr[i].cumulative;
    }

    // Δικλείδα Ασφαλείας: Επειδή ο Counting Sort δεσμεύει μνήμη ίση με τη μέγιστη τιμή στοιχείου (max),
    // αν το max είναι υπερβολικά μεγάλο (π.χ. > 100.000.000), το πρόγραμμα θα κρασάρει λόγω έλλειψης RAM.
    if (max > 100000000) { 
        printf("Counting Sort: Range too large (max: %lld). Skipping for safety.\n", max);
        return;
    }

    // Βήμα 2: Δέσμευση και μηδενισμός του πίνακα count μεγέθους (max + 1)
    int *count = calloc(max + 1, sizeof(int));
    if (!count) return;

    // Δέσμευση μνήμης για τον προσωρινό πίνακα εξόδου (output)
    struct Record *output = malloc(n * sizeof(struct Record));
    if (!output) { free(count); return; }

    // Βήμα 3: Καταμέτρηση των εμφανίσεων (συχνότητας) κάθε τιμής cumulative
    for (int i = 0; i < n; i++) count[arr[i].cumulative]++;

    // Βήμα 4: Μετατροπή του count έτσι ώστε κάθε θέση να δείχνει την πραγματική 
    // τελική θέση του στοιχείου στον πίνακα εξόδου (αθροιστικός πίνακας)
    for (int i = 1; i <= max; i++) count[i] += count[i - 1];

    // Βήμα 5: Κατασκευή του τελικού πίνακα εξόδου διαβάζοντας ανάποδα τον αρχικό
    // (Η ανάποδη ανάγνωση εξασφαλίζει ότι ο αλγόριθμος παραμένει σταθερός / stable)
    for (int i = n - 1; i >= 0; i--) {
        output[count[arr[i].cumulative] - 1] = arr[i];
        count[arr[i].cumulative]--; // Μείωση του μετρητή για διαχείριση διπλότυπων τιμών
    }

    // Βήμα 6: Αντιγραφή των ταξινομημένων δεδομένων από τον output πίσω στον αρχικό arr
    for (int i = 0; i < n; i++) arr[i] = output[i];

    // Αποδέσμευση της βοηθητικής μνήμης
    free(count);
    free(output);
}
