#include <stdio.h>
#include <stdlib.h>
#include <string.h>
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

void swap(struct Record* a, struct Record* b);
int partition(struct Record arr[], int low, int high);
void quickSort(struct Record arr[], int low, int high);

void heapify(struct Record arr[], int n, int i);
void heapSort(struct Record arr[], int n);

int main() {
    struct Record *data_heap, *data_quick;
    int n;

    load_data(&data_heap, &n);
    
    data_quick = malloc(n * sizeof(struct Record));
    for(int i=0; i<n; i++) data_quick[i] = data_heap[i];

    clock_t start, end;

    printf("Εκκίνηση ταξονόμησης για %d εγγραφές:\n", n);
    start = clock();
    heapSort(data_heap, n);
    end = clock();
    printf("Heap Sort: %f δευτερόλεπτα\n", (double)(end - start) / CLOCKS_PER_SEC);

    start = clock();
    quickSort(data_quick, 0, n - 1);
    end = clock();
    printf("Quick Sort: %f δευτερόλεπτα\n", (double)(end - start) / CLOCKS_PER_SEC);
    
    free(data_heap); 
    free(data_quick);
    return 0;
}
void swap(struct Record* a, struct Record* b){
    struct Record t = *a;
    *a = *b;
    *b = t;
}
int partition(struct Record arr[], int low, int high){
    long long pivot = arr[high].value;
    int i = (low-1);

    for (int j = low; j<=high-1; j++){
        if (arr[j].value < pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i+1], &arr[high]);
    return (i+1);
}
void quickSort(struct Record arr[], int low, int high){
    if (low < high) {
        int x = partition(arr, low, high);
        quickSort(arr, low, x-1);
        quickSort(arr, x+1, high);
    }
}
void heapify(struct Record arr[], int n, int i){
    int max = i;
    int l = 2 * i + 1; //aristero paidi
    int r = 2 * i + 2; //deji paidi

    if (l < n && arr[l].value > arr[max].value)
        max = l;

    if (r < n && arr[r].value > arr[max].value)
        max = r;

    if (max != i){
        swap(&arr[i], &arr[max]);
        heapify(arr, n, max);
    }
}
void heapSort(struct Record arr[], int n){
    for (int i = n / 2 - 1; i>=0; i--)
    heapify(arr, n, i);

    for (int i = n-1; i>0; i--){
        swap(&arr[0], &arr[i]);
        heapify(arr, i, 0);
    }
}

void load_data(struct Record **arr, int *n) {
    FILE *file = fopen("test_data.csv", "r");
    if (!file) { printf("Error opening file!\n"); exit(1); }

    char line[1024];
    fgets(line, 1024, file); 

    *arr = malloc(111438 * sizeof(struct Record));
    int i = 0;
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
}