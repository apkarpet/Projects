#include <stdio.h>

int main(int argc, char *argv[]) {
	printf("Count program running:\n");
	
	printf("Please enter count limit: ");
	
	int countLimit;
	scanf("%d", &countLimit);
	
	int i;
	for(i=0; i<=countLimit; i++) {
		printf("%d ", i);
}
	return 0;
}
