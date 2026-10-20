#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <pthread.h>

// Δομή δεδομένων

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
    long long cumulative;
};

typedef struct {
    double m;
    double b;
} LinearModel;

typedef struct {
    struct Record *arr;
    int n;
    long long target;
    int result;
    double time_taken;
    LinearModel *model;
} ThreadData;

// Βοηθητικές Συναρτήσεις

// Μετατροπή ημερομηνίας σε αριθμητικό κλειδί YYYYMMDD για αναζήτηση
long long dateToKey(char* dateStr) {
    int day, month, year;
    if(sscanf(dateStr, "%d/%d/%d", &day, &month, &year) == 3) {
        return (long long)year * 10000 + (long long)month * 100 + day;
    }
    return 0;
}

// Εκπαίδευση Μοντέλου Γραμμικής Παλινδρόμησης για LA-BIS(Bonus 2) 
void trainModel(struct Record *arr, int n, LinearModel *model) {
    double sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    for (int i = 0; i < n; i++) {
        long long x = dateToKey(arr[i].date);
        sumX += x;
        sumY += i;
        sumXY += (double)x * i;
        sumX2 += (double)x * x;
    }
    double avgX = sumX / n;
    double avgY = sumY / n;
    model->m = (sumXY - n * avgX * avgY) / (sumX2 - n * avgX * avgX);
    model->b = avgY - model->m * avgX;
}

int predictPos(LinearModel *model, long long key, int n) {
    int pos = (int)(model->m * key + model->b);
    if (pos < 0) return 0;
    if (pos >= n) return n - 1;
    return pos;
}

// Αλγόριθμοι Αναζήτησης 

// Αλγόριθμος Αναζήτησης Παρεμβολής(BIS) 
int bISearch_logic(struct Record arr[], int n, long long target) {
    int left = 0, right = n - 1;
    while (left <= right && target >= dateToKey(arr[left].date) && target <= dateToKey(arr[right].date)) {
        int size = right - left + 1;
        if (size <= 3) break;
        
        long long lK = dateToKey(arr[left].date), rK = dateToKey(arr[right].date);
        int next = left + (int)(((double)(right - left) * (target - lK)) / (rK - lK));
        
        if (next < left) next = left;
        if (next > right) next = right;
        
        if (dateToKey(arr[next].date) == target) return next;
        
        int m = (int)sqrt(size), i = 0;
        if (target > dateToKey(arr[next].date)) {
            while (next + (i + 1) * m <= right && target > dateToKey(arr[next + (i + 1) * m - 1].date)) i++;
            left = next + i * m;
            right = (next + (i + 1) * m < n) ? next + (i + 1) * m : n - 1;
        } else {
            while (next - (i + 1) * m >= left && target < dateToKey(arr[next - (i + 1) * m + 1].date)) i++;
            right = next - i * m;
            left = (next - (i + 1) * m >= 0) ? next - (i + 1) * m : 0;
        }
    }
    for (int k = left; k <= right; k++) if (dateToKey(arr[k].date) == target) return k;
    return -1;
}

// Παραλλαγή BIS* για βελτίωση χειρότερης περίπτωσης
int bisStarSearch_logic(struct Record arr[], int n, long long target) {
    int left = 0, right = n - 1;
    while (left <= right && target >= dateToKey(arr[left].date) && target <= dateToKey(arr[right].date)) {
        int size = right - left + 1;
        if (size <= 3) break;
        
        long long lK = dateToKey(arr[left].date), rK = dateToKey(arr[right].date);
        int next = left + (int)(((double)(right - left) * (target - lK)) / (rK - lK));
        
        if (dateToKey(arr[next].date) == target) return next;
        
        int m = (int)sqrt(size), j = 1;
        if (target > dateToKey(arr[next].date)) {
            while (next + (int)pow(2, j) * m <= right && target > dateToKey(arr[next + (int)pow(2, j) * m - 1].date)) j++;
            left = next + (int)pow(2, j-1) * m;
            right = (next + (int)pow(2, j) * m < n) ? next + (int)pow(2, j) * m : n - 1;
        } else {
            while (next - (int)pow(2, j) * m >= left && target < dateToKey(arr[next - (int)pow(2, j) * m + 1].date)) j++;
            right = next - (int)pow(2, j-1) * m;
            left = (next - (int)pow(2, j) * m >= 0) ? next - (int)pow(2, j) * m : 0;
        }
    }
    for (int k = left; k <= right; k++) if (dateToKey(arr[k].date) == target) return k;
    return -1;
}

// LA-BIS (Learned Augmented BIS) 
int laBISearch_logic(struct Record arr[], int n, long long target, LinearModel *model) {
    int predicted = predictPos(model, target, n);
    if (dateToKey(arr[predicted].date) == target) return predicted;
    
    int range = (int)sqrt(n);
    int left = (predicted - range < 0) ? 0 : predicted - range;
    int right = (predicted + range >= n) ? n - 1 : predicted + range;
    
    if (target < dateToKey(arr[left].date)) left = 0;
    if (target > dateToKey(arr[right].date)) right = n - 1;
    
    int search_res = bISearch_logic(arr + left, right - left + 1, target);
    return (search_res != -1) ? search_res + left : -1;
}

// Διαχείρηση Δεδομένων 

void load_data(struct Record **arr, int *n) {
    FILE *file = fopen("effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv", "r"); 
    if (!file) { printf("Error: file not found!\n"); exit(1); }

    char line[4096];
    fgets(line, sizeof(line), file); // Header

    *arr = malloc(111438 * sizeof(struct Record));
    int i = 0;
    while (fgets(line, sizeof(line), file) && i < 111438) {
        char *ptr = line;
        int col = 0;
        while (*ptr && *ptr != '\n' && *ptr != '\r') {
            char field[512] = {0};
            int f_ptr = 0;
            if (*ptr == '"') {
                ptr++;
                while (*ptr && *ptr != '"') field[f_ptr++] = *ptr++;
                if (*ptr == '"') ptr++;
            } else {
                while (*ptr && *ptr != ',' && *ptr != '\n' && *ptr != '\r') field[f_ptr++] = *ptr++;
            }
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
            if (*ptr == ',') ptr++;
            col++;
        }
        i++;
    }
    *n = i;
    fclose(file);
    printf("Successfully loaded %d records.\n", i);
}

void swap(struct Record *a, struct Record *b) {
    struct Record t = *a; *a = *b; *b = t;
}

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

// Thread Wrappers 

void* threadBIS(void* arg) {
    ThreadData *d = (ThreadData*)arg;
    clock_t s = clock();
    d->result = bISearch_logic(d->arr, d->n, d->target);
    d->time_taken = (double)(clock() - s) / CLOCKS_PER_SEC;
    pthread_exit(NULL);
}

void* threadBISStar(void* arg) {
    ThreadData *d = (ThreadData*)arg;
    clock_t s = clock();
    d->result = bisStarSearch_logic(d->arr, d->n, d->target);
    d->time_taken = (double)(clock() - s) / CLOCKS_PER_SEC;
    pthread_exit(NULL);
}

void* threadLABIS(void* arg) {
    ThreadData *d = (ThreadData*)arg;
    clock_t s = clock();
    d->result = laBISearch_logic(d->arr, d->n, d->target, d->model);
    d->time_taken = (double)(clock() - s) / CLOCKS_PER_SEC;
    pthread_exit(NULL);
}

// Main

int main() {
    struct Record *data; int n;
    load_data(&data, &n);
    printf("Sorting records by date...\n");
    quickSortByDate(data, 0, n - 1);

    char searchDate[] = "15/12/2021";
    long long target = dateToKey(searchDate);
    LinearModel model; trainModel(data, n, &model);

    pthread_t t1, t2;
    ThreadData d1 = {data, n, target, -1, 0, NULL};
    ThreadData d2 = {data, n, target, -1, 0, &model};

    // BONUS 1: Parallel BIS vs BIS*
    printf("\n--- BONUS 1: Parallel BIS vs BIS* ---\n");
    pthread_create(&t1, NULL, threadBIS, &d1);
    pthread_create(&t2, NULL, threadBISStar, &d2);
    pthread_join(t1, NULL); pthread_join(t2, NULL);
    printf("BIS Search: %f sec (Result: %d)\n", d1.time_taken, d1.result);
    printf("BIS* Search: %f sec (Result: %d)\n", d2.time_taken, d2.result);
    printf("Consulting the faster: %s\n", (d1.time_taken < d2.time_taken) ? "BIS" : "BIS*");

    // BONUS 2: Parallel BIS vs LA-BIS
    printf("\n--- BONUS 2: Parallel BIS vs LA-BIS ---\n");
    pthread_create(&t1, NULL, threadBIS, &d1);
    pthread_create(&t2, NULL, threadLABIS, &d2);
    pthread_join(t1, NULL); pthread_join(t2, NULL);
    printf("Standard BIS: %f sec\n", d1.time_taken);
    printf("Learned Augmented BIS (LA-BIS): %f sec\n", d2.time_taken);

    if (d1.result != -1) {
        printf("\nDetails for %s:\n", searchDate);
        printf("Value: %lld, Cumulative: %lld\n", data[d1.result].value, data[d1.result].cumulative);
    }

    free(data);
    return 0;
}
