#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <time.h>

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

void load_data(struct Record **arr, int *n);

long long dateToKey(char* dateStr);
int partitionByDate(struct Record arr[], int low, int high);
void quickSortByDate(struct Record arr[], int low, int high);

void swap(struct Record *a, struct Record *b);
int bISearch(struct Record arr[], int n, long long target);
int bisStarSearch(struct Record arr[], int n, long long target);

int main() {
    struct Record *data;
    int n;
    load_data(&data, &n);
    quickSortByDate(data, 0, n - 1); 

    char targetDate[15];
    printf("Εισάγετε ημερομηνία για αναζήτηση BIS/BIS* (DD/MM/YYYY): ");
    scanf("%s", targetDate);
    long long targetKey = dateToKey(targetDate);

    clock_t start, end;

    start = clock();
    int res1 = bISearch(data, n, targetKey);
    end = clock();
    printf("BIS Αναζήτηση: %f δευτερόλεπτα. (Θέση: %d)\n", (double)(end-start)/CLOCKS_PER_SEC, res1);
    
    start = clock();
    int res2 = bisStarSearch(data, n, targetKey);
    end = clock();
    printf("BIS* Αναζήτηση: %f δευτερόλεπτα. (Θέση: %d)\n", (double)(end-start)/CLOCKS_PER_SEC, res2);

    free(data);
    return 0;
}

int partition(struct Record arr[], int low, int high){
    long long pivot = arr[high].value;
    int i = low-1;

    for (int j = low; j<high; j++){
        if (arr[j].value <= pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i+1], &arr[high]);
    return (i+1);
}
void swap(struct Record *a, struct Record *b){
    struct Record t = *a;
    *a = *b;
    *b = t;
}
int bISearch(struct Record arr[], int n, long long target){
    int low = 0, high = n -1 ;
    int next = (int)((double)(n - 1) * (target - dateToKey(arr[low].date)) / (dateToKey(arr[high].date) - dateToKey(arr[low].date)));

    while (target != dateToKey(arr[next].date)) {
        int i = 1;
        int size = high - low + 1;
        int m = (int)sqrt(size);

        if (target > dateToKey(arr[next].date)) {
            while (target > dateToKey(arr[(int)fmin(next + i *m, high)].date)) i*=2;
            low = next + (i/2)*m;
            high = (int)fmin(next + i*m, high);
        } else {
            while (target < dateToKey(arr[(int)fmax(next - i*m, low)].date)) i*=2;
            high = next - (i/2) * m;
            low = (int)fmax(next-i*m, low);
        }
        long long lowKey = dateToKey(arr[low].date);
        long long highKey = dateToKey(arr[high].date);
        if (highKey == lowKey) break;

        next = low + (int)((double)(high - low) * (target - lowKey) / (highKey - lowKey));
        if (next < low || next > high) break; 
    }
    if (target == dateToKey(arr[next].date)) return next;
    return -1;
}

void load_data(struct Record **arr, int *n) {
    FILE *file = fopen("effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv", "r");
    if (!file) { 
        printf("Error opening file!\n"); 
        exit(1); 
    }

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

long long dateToKey(char* dateStr) {
    int day, month, year;
    if(sscanf(dateStr, "%d/%d/%d", &day, &month, &year) == 3) {
        return (long long)year * 10000 + (long long)month * 100 + day;
    }
    return 0;
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
        int x = partitionByDate(arr, low, high);
        quickSortByDate(arr, low, x - 1);
        quickSortByDate(arr, x + 1, high);
    }
}

int bisStarSearch(struct Record arr[], int n, long long target) {
    int low = 0, high = n - 1;

    while (low <= high && target >= dateToKey(arr[low].date) && target <= dateToKey(arr[high].date)) {
        long long lowKey = dateToKey(arr[low].date);
        long long highKey = dateToKey(arr[high].date);

        int next = low + (int)((double)(high - low) * (target - lowKey) / (highKey - lowKey));

        if (dateToKey(arr[next].date) == target) return next;

        if (target > dateToKey(arr[next].date)) low = next+1;
        else high = next - 1;
    }
    return -1;
}