//EXERCISE 2

#include <stdio.h>
#include <math.h>

/*Για κάθε αριθμό μεταξύ του 100 και 999, κάνε εξαγωγή των ψηφίων του.
Αν το άθροισμα κάθε ψηφίου υψωμένο εις την τρίτη ισούται με τον αριθμό αυτό, εμφάνισε τον αριθμό.*/

int main(int argc, char *argv[]) {
	printf("Exercise2 program running: \n");
		for(int number=100;number<1000;number++){	
		
			int digit1=number%10;
			int digit2=(number/10)%10;
			int digit3=number/100;
			
			int sumOfDigits=pow(digit1,3)+pow(digit2,3)+pow(digit3,3);
			if(sumOfDigits==number){
				printf("The sum of %d's digits raised to the power of 3 is equal to %d. (%d^3+%d^3+%d^3=%d)\n", number, number, digit1, digit2, digit3, number);
			}
		}
	return 0;
}


