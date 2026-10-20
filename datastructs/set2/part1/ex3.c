#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

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

    load_data(&data, &n);

    printf("Ταξινόμηση των δεδομένων βάσει της ημερομηνίας...\n");
    quickSortByDate(data, 0, n - 1); 

    char targetDate[15];
    printf("Εισάγετε ημερομηνία αναζήτησης (dd/mm/yyyy): ");
    scanf("%14s", targetDate);
    long long targetKey = dateToKey(targetDate);

    clock_t start, end;

    start = clock();
    int res1 = binarySearch(data, n, targetKey); 
    end = clock();
    printf("Binary Search: Χρόνος = %f δευτ. (Θέση: %d)\n", (double)(end - start)/CLOCKS_PER_SEC, res1);

    start = clock();
    int res2 = interpolationSearch(data, n, targetKey);
    end = clock();
    printf("Interpolation Search: Χρόνος = %f δευτ. (Θέση: %d)\n", (double)(end - start)/CLOCKS_PER_SEC, res2);

    if (res1 != -1) {
        printf("\nΣτοιχεία που βρέθηκαν:\n");
        printf("Date: %s, Value: %lld, Cumulative: %lld\n", data[res1].date, data[res1].value, data[res1].cumulative);
    } else {
        printf("\nΗ ημερομηνία δεν βρέθηκε.\n");
    }

    free(data);
    return 0;
}

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

int interpolationSearch(struct Record arr[], int n, long long target) {
    int low = 0, high = n - 1;
    while (low <= high && target >= dateToKey(arr[low].date) && target <= dateToKey(arr[high].date)) {
        if (low == high) {
            if (dateToKey(arr[low].date) == target) return low;
            break;
        }

        long long lowKey = dateToKey(arr[low].date);
        long long highKey = dateToKey(arr[high].date);

        int pos = low + (int)(((double)(high - low) / (highKey - lowKey)) * (target - lowKey));

        if (pos < low || pos > high) break; // Ασφάλεια ορίων

        long long posKey = dateToKey(arr[pos].date);
        if (posKey == target) return pos;
        if (posKey < target) low = pos + 1;
        else high = pos - 1;
    }
    return -1;
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
    if (low < high) {
        int pi = partitionByDate(arr, low, high);
        quickSortByDate(arr, low, pi - 1);
        quickSortByDate(arr, pi + 1, high);
    }
}

void load_data(struct Record **arr, int *n) {
    FILE *file = fopen("effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv", "r"); 
    if (!file) { printf("Error: file not found!\n"); exit(1); }
    char line[1024];
    fgets(line, 1024, file);
    *arr = malloc(111438 * sizeof(struct Record));
    int i = 0;
    while (fgets(line, 1024, file)) {
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
}