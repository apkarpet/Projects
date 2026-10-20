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

void merge(struct Record arr[], int x, int y, int z);
void mergeSort(struct Record arr[], int x, int y);
void countingSort(struct Record arr[], int n);

int main(){
    struct Record *data_merge, *data_counting;
    int n;

    load_data(&data_merge, &n);

    data_counting = malloc(n * sizeof(struct Record));
    for (int i=0; i<n; i++) data_counting[i] = data_merge[i];

    clock_t start, end;

    printf("Ταξινόμηση για %d εγγραφές.\n", n);

    start = clock();
    mergeSort(data_merge, 0, n-1);
    end = clock();
    printf("Merge Sort: %f δευτερόλεπτα.\n", (double)(end-start) / CLOCKS_PER_SEC);

    start = clock();
    countingSort(data_merge, n);
    end = clock();
    printf("Counting Sort: %f δευτερόλεπτα.\n", (double)(end-start) / CLOCKS_PER_SEC);

    free(data_merge);
    free(data_counting);

    return 0;
}

void merge(struct Record arr[], int x, int y, int z){
    int i, j, k;
    int n1 = y - x + 1;
    int n2 = z - y;

    struct Record *R1 = malloc(n1 * sizeof(struct Record));
    struct Record *R2 = malloc(n2 * sizeof(struct Record));

    for(i = 0; i < n1; i++) R1[i] = arr[x + i];
    for(j = 0; j < n2; j++) R2[j] = arr[y + 1 + j];

    i = 0;
    j = 0;
    k = x;

    while(i < n1 && j < n2) {
        if (R1[i].cumulative <= R2[j].cumulative) {
            arr[k] = R1[i];
            i++;
        } else {
            arr[k] = R2[j];
            j++;
        }
        k++;
    }

    while (i < n1) arr[k++] = R1[i++];

    while (j < n2) arr[k++] = R2[j++];

    free(R1);
    free(R2);
}
void mergeSort(struct Record arr[], int x, int y){
    if (x < y) {
        int m = x + (y - x) / 2;

        mergeSort(arr, x, m);
        mergeSort(arr, m+1, y);

        merge(arr, x, m, y);
    }
}
void countingSort(struct Record arr[], int n){
    if (n<=0) return;

    long long max = arr[0].cumulative;
    for (int i=1; i<n; i++){
        if (arr[i].cumulative > max) max = arr[i].cumulative;
    }

    if (max > 100000000) {
        printf("Counting Sort: Το εύρος τιμών είναι υπερβολικά μεγάλο για δέσμευση μνήμης.\n");
        return;
    }

    int* count = (int*)calloc(max + 1, sizeof(int));
    if (!count) {
        printf("Counting Sort: Αποτυχία δέσμευσης μνημης.\n");
        return;
    }
    struct Record* output = (struct Record*)malloc(n*sizeof(struct Record));

    for (int i=0; i<n; i++){
        count[arr[i].cumulative]++;
    }
    for (int i=1; i<=max; i++){
        count[i] += count[i-1];
    }
    for (int i=n-1; i>=0; i--){
        output[count[arr[i].cumulative]-1] = arr[i];
        count[arr[i].cumulative]--;
    }
    for (int i=0; i<n; i++){
        arr[i] = output[i];
    }
    free(count);
    free(output);
}

 void load_data(struct Record **arr, int *n) {
    FILE *file = fopen("effects-of-covid-19-on-trade-at-15-december-2021-provisional.csv", "r");
    if (!file) { 
        printf("Error opening file!\n"); 
        exit(1); }

    char line[1024];
    fgets(line, 1024, file);
    
    *arr = malloc(111438 * sizeof(struct Record));
    int i = 0;
    while (fgets(line, 1024, file) && i < 111438) {
        char *token;

        token = strtok(line, ",");
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

        token = strtok(NULL, ","); // Measure
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